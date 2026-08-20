"""A dealer, and deliberately not a second poker engine.

Phase 06 left the repo with one strategy object that can play a hand from the first preflop
decision to showdown, and nothing that deals one. This module is the dealer. It shuffles,
posts blinds, walks the streets, asks each seat's strategy what to do, applies the answer,
and awards the pot.

Every poker rule it appears to know it is actually borrowing. Legality and betting arithmetic
come from `BettingRoundState`, turn order and round completion from `TurnState`, hand ranking
and pot splitting from `settle_showdown` and `settle_uncontested`. The one thing this module
decides is *when to ask*; the one thing it is forbidden to decide is *what the answer is*.
Every action it applies came out of a `StrategyDecision`, and a `StrategyRefusal` ends the
hand as a counted outcome rather than being stepped over with a substitute.

Three properties are load-bearing, and two of them are checked here rather than left to the
tests, because a simulator that quietly violates one still produces a plausible report.

Chips are conserved per hand. `_settle` refuses to return a hand whose books do not balance,
rather than letting the run net out at the end, because an aggregate that sums to zero hides
two errors that cancel.

A run is a pure function of `(seed, seating, profiles)`. Every hand derives its own `Random`
from the run seed and the hand index, and nothing here touches the `random` module's global
state, so interleaved use of `random` elsewhere in the process cannot move a single card. The
per-hand seed travels on the result and the hand identity is derived from it, so any one hand
regenerates on its own without replaying what came before it.

Every dealt hand is emitted as a Phase 02 `NormalizedHandHistory`, written as it is played
rather than reconstructed afterwards, and is expected to survive `replay_hand` - which
re-derives the whole hand from that record and checks its own settlement against the recorded
result. That is what stops this module and the replayer being two independent stories about
the same rules.

Stacks reset to the configured depth before every hand, by judgment call 1, and that is not a
bankroll preference. `PreflopChartStrategy` derives hero's depth exactly and refuses a table
that is not one flat stack depth, so if stacks carried over, whoever won the first hand would
put every later hand into the refusal path. The cost is that this models no session and no
stack dynamics, and the report says so wherever it prints a figure.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from random import Random

from poker_training_bot.hand_history.schema import (
    HistoryAction,
    HistoryActionKind,
    HistoryStreet,
    ShowdownEntry,
    StreetName,
)
from poker_training_bot.poker_core.cards import Card
from poker_training_bot.poker_core.engine import (
    Action,
    ActionKind,
    PlayerState,
    settle_showdown,
    settle_uncontested,
)
from poker_training_bot.poker_core.order import TurnState, blind_seats
from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.simulator.config import (
    REQUIRED_DEPTH_BB,
    REQUIRED_SEATS,
    SimulationConfig,
)
from poker_training_bot.simulator.measure import HandResult, SimulationResult
from poker_training_bot.simulator.outcomes import REFUSED, SHOWDOWN, UNCONTESTED
from poker_training_bot.simulator.record import (
    blinds_only,
    history_action,
    normalized_hand,
)
from poker_training_bot.simulator.table import (
    Dealt,
    build_query,
    deal,
    post_blind,
    seat_label,
    snapshot,
    street_state,
)
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    StrategyDecision,
    StrategyRefusal,
)

__all__ = [
    "REQUIRED_DEPTH_BB",
    "REQUIRED_SEATS",
    "SimulationConfig",
    "SimulationResult",
    "run_simulation",
]

# Judgment call 1. A module constant rather than a config field, because it is not a knob:
# the committed chart cannot answer a table that is not one flat depth, so a run with this
# off measures the refusal path. Named so a mutation canary can flip it.
STACKS_RESET_EVERY_HAND = True

# Judgment call 4. A refusal voids the hand: stacks are restored, nothing moves, and the hand
# is counted as refused. Turning it into a fold would convert a refusal into an action in the
# accounting even while the strategy layer refused, which is the same erasure the contract
# forbids one level up.
REFUSAL_VOIDS_THE_HAND = True

_POSTFLOP_STREETS = (StreetName.FLOP, StreetName.TURN, StreetName.RIVER)
_HISTORY_ACTIONS = frozenset({"fold", "check", "call", "raise"})


def _hand_random(hand_seed: int) -> Random:
    """The only source of randomness in the module.

    A fresh `Random` per hand, so a hand is reproducible on its own and the process-wide
    `random` module is never touched. A mutation canary perturbs this line, because a
    simulation that is not a pure function of its seed still produces a report that looks
    perfectly reasonable.
    """
    return Random(hand_seed)


def _filed_through(
    filed: list[HistoryStreet],
    street: StreetName,
    board: tuple[Card, ...],
    actions: list[HistoryAction],
) -> tuple[HistoryStreet, ...]:
    """The streets already filed, plus the one a refusal stopped in the middle of.

    A street is normally filed once its betting round completes, and a refusal returns before
    that, so without this the partial street is lost - and with it every action taken before
    the refusal, which is the only thing that identifies the spot that was refused. An earlier
    version of this module returned the filed streets alone, and threw away 565 actions across
    128 hands without a single test objecting.
    """
    return (*filed, HistoryStreet(name=street, board=board, actions=tuple(actions)))


@dataclass(frozen=True)
class _Played:
    """Everything one hand produced before the pot was awarded."""

    streets: tuple[HistoryStreet, ...]
    decisions: tuple[DecisionAuditRecord, ...]
    committed: dict[int, int]
    folded: set[int]
    refusal: StrategyRefusal | None
    refusing_seat: int | None


def _play(
    config: SimulationConfig,
    dealt: Dealt,
    hand_id: str,
    button_seat: int,
    stacks: dict[int, int],
) -> _Played:
    """Walk the streets, asking whoever is to act and applying what comes back."""
    small_blind, big_blind = config.blinds
    sb_seat, bb_seat = blind_seats(config.seats, button_seat)
    streets: list[HistoryStreet] = []
    decisions: list[DecisionAuditRecord] = []
    history: list[SeatAction] = []
    committed = {seat: 0 for seat in config.seats}
    folded: set[int] = set()
    all_in: set[int] = set()
    board: tuple[Card, ...] = ()

    for street in (StreetName.PREFLOP, *_POSTFLOP_STREETS):
        if len(set(config.seats) - folded) <= 1:
            break
        street_board = dealt.board_for(street)
        board = board + street_board
        state = street_state(config, stacks, committed, folded, all_in)
        actions: list[HistoryAction] = []
        if street is StreetName.PREFLOP:
            state = post_blind(state, sb_seat, small_blind)
            state = post_blind(state, bb_seat, big_blind)
            actions.append(HistoryAction(sb_seat, HistoryActionKind.POST_BLIND, small_blind))
            actions.append(HistoryAction(bb_seat, HistoryActionKind.POST_BLIND, big_blind))
            turn = TurnState.start_preflop(state, button_seat)
        else:
            turn = TurnState.start_postflop(state, button_seat)

        while not turn.round_complete:
            seat = turn.to_act
            if seat is None:
                break
            query = build_query(
                config, dealt, hand_id, button_seat, street, turn, seat, board, tuple(history)
            )
            outcome = config.profiles[seat].strategy.decide(query)
            if isinstance(outcome, StrategyRefusal):
                if REFUSAL_VOIDS_THE_HAND:
                    # File the street as far as it got. A refusal aborts the betting round,
                    # so the loop below never reaches the append at the bottom - and an
                    # earlier version returned here without this line, which threw away
                    # every action taken before the refusal and with it the only trace of
                    # which spot was refused.
                    return _Played(
                        streets=_filed_through(streets, street, street_board, actions),
                        decisions=tuple(decisions),
                        committed=committed,
                        folded=folded,
                        refusal=outcome,
                        refusing_seat=seat,
                    )
                outcome = StrategyDecision("fold", None, outcome.code)
            decisions.append(
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=config.profiles[seat].strategy.strategy_id,
                    strategy_version=config.profiles[seat].strategy.strategy_version,
                    query=query,
                    outcome=outcome,
                )
            )
            before = turn.round.player(seat).street_bet
            turn = turn.apply(Action(seat, ActionKind(outcome.action), outcome.amount))
            added = turn.round.player(seat).street_bet - before
            actions.append(history_action(outcome, seat, added))
            if street is StreetName.PREFLOP and outcome.action in _HISTORY_ACTIONS:
                # `outcome.amount` is the raise-to target for a raise and None for
                # every other action, which is exactly what a recorded action carries.
                history.append(SeatAction(seat, outcome.action, outcome.amount))

        streets.append(HistoryStreet(name=street, board=street_board, actions=tuple(actions)))
        committed, folded, all_in = snapshot(turn.round)

    return _Played(
        streets=tuple(streets),
        decisions=tuple(decisions),
        committed=committed,
        folded=folded,
        refusal=None,
        refusing_seat=None,
    )


def _voided(
    config: SimulationConfig,
    hand_id: str,
    hand_seed: int,
    button_seat: int,
    starting: dict[int, int],
    played: _Played,
) -> HandResult:
    """A refused hand: counted, named, carrying its action, and moving nothing.

    Judgment call 4. Chip conservation holds trivially rather than by an accounting fix, and
    the refusal reaches the report with its own reason code and the detail naming what the
    strategy could not find - which is what lets the inventory key an entry to a chart cell.

    No completed normalized record, deliberately. The hand stops inside a betting round, so
    it is not a hand the Phase 02 replayer can re-derive, and handing one over would be a
    category error dressed as convenience. What it carries instead is the transcript as far
    as it got, which is where the refused spot is legible.
    """
    refusal = played.refusal
    assert refusal is not None
    return HandResult(
        hand_id=hand_id,
        seed=hand_seed,
        button_seat=button_seat,
        outcome=REFUSED,
        refusal_code=refusal.code,
        refusing_seat=played.refusing_seat,
        refusal_detail=refusal.detail,
        starting_stacks=dict(starting),
        stack_deltas={seat: 0 for seat in config.seats},
        pot_collected=0,
        pot_awarded=0,
        decisions=played.decisions,
        streets=played.streets or blinds_only(config, button_seat),
        normalized=None,
    )


def _settle(
    config: SimulationConfig,
    dealt: Dealt,
    hand_id: str,
    hand_seed: int,
    button_seat: int,
    starting: dict[int, int],
    stacks: dict[int, int],
    played: _Played,
) -> HandResult:
    """Award the pot through Phase 01, then check this one hand's books."""
    active = set(config.seats) - played.folded
    players = tuple(
        PlayerState(
            seat=seat,
            name=seat_label(seat),
            stack=stacks[seat] - played.committed[seat],
            hole_cards=dealt.hole_cards[seat] if seat in active else (),
            committed_total=played.committed[seat],
            folded=seat in played.folded,
            all_in=stacks[seat] - played.committed[seat] == 0,
        )
        for seat in config.seats
    )
    if len(active) == 1:
        settlement = settle_uncontested(players)
        outcome = UNCONTESTED
        showdown: tuple[ShowdownEntry, ...] = ()
    else:
        settlement = settle_showdown(players, dealt.board)
        outcome = SHOWDOWN
        showdown = tuple(
            ShowdownEntry(seat=seat, hole_cards=dealt.hole_cards[seat]) for seat in sorted(active)
        )

    deltas = {seat: settlement.payouts[seat] - played.committed[seat] for seat in config.seats}
    pot_collected = sum(played.committed.values())
    if sum(deltas.values()) != 0:
        raise ValueError(
            f"{hand_id} does not conserve chips: stack changes sum to {sum(deltas.values())}"
        )
    if settlement.total_pot != pot_collected:
        raise ValueError(f"{hand_id} awarded {settlement.total_pot} of a {pot_collected} pot")

    return HandResult(
        hand_id=hand_id,
        seed=hand_seed,
        button_seat=button_seat,
        outcome=outcome,
        refusal_code=None,
        refusing_seat=None,
        refusal_detail=(),
        starting_stacks=dict(starting),
        stack_deltas=deltas,
        pot_collected=pot_collected,
        pot_awarded=settlement.total_pot,
        decisions=played.decisions,
        streets=played.streets,
        normalized=normalized_hand(
            config,
            hand_id,
            button_seat,
            stacks,
            played.streets,
            showdown,
            settlement.payouts,
            pot_collected,
        ),
    )


def _run_hand(config: SimulationConfig, index: int, stacks: dict[int, int]) -> HandResult:
    """One hand, identified by its own seed rather than by its place in the run.

    The seed is `run seed + index` and the button is derived from the seed rather than from
    the index, so a single-hand run seeded with a hand's own seed reproduces that hand
    exactly - same cards, same button, same play. Deriving the button from the index instead
    would make a hand reproducible only in the position it originally occupied, which is not
    reproducible in any useful sense.
    """
    hand_seed = config.seed + index
    hand_id = f"sim-{hand_seed}"
    button_seat = hand_seed % len(config.seats)
    dealt = deal(config, _hand_random(hand_seed))
    played = _play(config, dealt, hand_id, button_seat, stacks)
    starting = dict(stacks)
    if played.refusal is not None:
        return _voided(config, hand_id, hand_seed, button_seat, starting, played)
    return _settle(
        config, dealt, hand_id, hand_seed, button_seat, starting, stacks, played
    )


def run_simulation(config: SimulationConfig) -> SimulationResult:
    """Deal `config.hands` hands and report what happened.

    The button advances one seat per hand and profiles stay in their seats, by judgment call
    6, so over any multiple of the table size every profile has played every position an
    equal number of times.
    """
    stacks = {seat: config.starting_stack for seat in config.seats}
    hands: list[HandResult] = []
    for index in range(config.hands):
        if STACKS_RESET_EVERY_HAND:
            stacks = {seat: config.starting_stack for seat in config.seats}
        hand = _run_hand(config, index, stacks)
        hands.append(hand)
        stacks = {seat: stacks[seat] + hand.stack_deltas[seat] for seat in config.seats}
    counts: dict[int, Counter] = {seat: Counter() for seat in config.seats}
    for hand in hands:
        for seat in config.seats:
            counts[seat][position_for_seat(config.seats, hand.button_seat, seat)] += 1
    return SimulationResult(
        seed=config.seed,
        seat_names=tuple(profile.name for profile in config.profiles),
        hands=tuple(hands),
        position_counts=counts,
    )
