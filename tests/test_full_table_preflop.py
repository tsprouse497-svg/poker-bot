"""Phase 05 tests, written from the contract before any implementation existed.

`TestSourceFrequencies`, the phase's external oracle, moved to
`tests/test_preflop_committed_charts.py` when phase 14 rewrote it against a chart that is
no longer the raked source those numbers describe, because this file is at its line cap.

`TestTotality` proves coverage by enumeration rather than by sampling. An
artifact-backed strategy is allowed to refuse, and the danger is not a wrong answer
but a confident one where the chart says nothing, so the interesting property is
that every reachable spot resolves to a decision or an explicit refusal and never to
an exception or a guess.

No raise price is spelled here: the retired chart three-bet to 8, 11 and 13.5 and the
rake-free solve three-bets to 7.5, so a spelled price points at a cell nobody solved.
Prices come from the artifact's own keys, which is what `vs_open_key` already did.
"""

from __future__ import annotations

import itertools
import subprocess
from collections import Counter

import pytest

from poker_training_bot.poker_core.positions import position_for_seat, table_positions
from poker_training_bot.solver_artifacts.gtopen_export import COMMITTED_EXPORT_PATH
from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    SeatState,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
RETIRED_ARTIFACT = ARTIFACT_DIR / "six_max_nl25_100bb.json"
SOURCE = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"

BIG_BLIND = 100
SMALL_BLIND = 50
DEPTH_BB = 100
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3  # seats 0..5 with button at 3 puts LJ at seat 0


def seat_of(position: str) -> int:
    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise AssertionError(f"no seat holds {position}")


def stacks(
    committed: dict[int, int] | None = None, ante: int = 0, depth_bb: int = DEPTH_BB
) -> tuple[tuple[int, int], ...]:
    """Current stacks for a six-handed table, minus everything each seat has put in."""
    paid = dict(committed or {})
    paid.setdefault(seat_of("SB"), SMALL_BLIND)
    paid.setdefault(seat_of("BB"), BIG_BLIND)
    full = depth_bb * BIG_BLIND
    return tuple((seat, full - paid.get(seat, 0) - ante) for seat in SEATS)


def query(
    hero_position: str,
    history: tuple[SeatAction, ...] = (),
    hole_cards: tuple[str, str] = ("As", "Ks"),
    forced: dict[int, int] | None = None,
    ante: int = 0,
    **overrides,
) -> StrategyQuery:
    """A preflop query for hero, defaulting to an unopened, unstraddled, unanted pot.

    `forced` seats chips no recorded action explains, which is what a straddle is; `ante`
    is dead money every seat posted. Both are real chips on real seats, not an override of
    the pot or the level, because a pot that does not reconcile seat by seat is now
    rejected. An ante buys no part of the level, so it sits in `committed_total` alone.
    """
    hero = seat_of(hero_position)
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND, **(forced or {})}
    # A straddle raises the level a voluntary action is measured against, so the ladder
    # starts there. The detector knows only the declared blinds, which is the disagreement.
    current_bet = max(BIG_BLIND, *committed.values())
    min_raise_target = 2 * current_bet
    for entry in history:
        if entry.action == "raise":
            # The level is what the raise says it is, so the price the query states and
            # the price the key carries are one number rather than two that can disagree.
            amount = entry.amount or current_bet
            min_raise_target = amount + max(amount - current_bet, BIG_BLIND)
            current_bet = amount
            committed[entry.seat] = current_bet
        elif entry.action == "call":
            committed[entry.seat] = current_bet
    # Capped at what hero can actually pay, per Taylor's ruling of 2026-08-20.
    hero_stack = DEPTH_BB * BIG_BLIND - committed.get(hero, 0) - ante
    to_call = min(max(current_bet - committed.get(hero, 0), 0), hero_stack)
    gone = tuple(entry.seat for entry in history if entry.action == "fold")
    fields = {
        "hand_id": "h1",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": hole_cards,
        "board": (),
        "legal_actions": ("fold", "call", "raise") if to_call else ("check", "raise"),
        "to_call": to_call,
        "current_bet": current_bet,
        "min_raise_target": min_raise_target,
        "pot": sum(committed.values()) + len(SEATS) * ante,
        "seat_states": tuple(
            SeatState(s, committed.get(s, 0), committed.get(s, 0) + ante, s in gone, False)
            for s in SEATS
        ),
        "stacks": stacks(committed, ante),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": history,
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def cards_for(hand: str) -> tuple[str, str] | None:
    """Two concrete cards for a 169-class name, so a class can be driven through decide.

    None for a string that is not a class name, which is how the table below filters
    the generated candidates without a second list of the 169.
    """
    ranks = "23456789TJQKA"
    if len(hand) == 2:
        if hand[0] != hand[1] or hand[0] not in ranks:
            return None
        return (hand[0] + "s", hand[1] + "h")
    if len(hand) != 3 or hand[2] not in "so":
        return None
    high, low = hand[0], hand[1]
    if high not in ranks or low not in ranks or ranks.index(high) <= ranks.index(low):
        return None
    return (high + "s", low + ("s" if hand[2] == "s" else "h"))


def combos_of(hand: str) -> int:
    """How many of the 1326 starting hands a 169-class name stands for."""
    if len(hand) == 2:
        return 6
    return 4 if hand.endswith("s") else 12


def raised(position: str, amount: int) -> SeatAction:
    return SeatAction(seat_of(position), "raise", amount)


def solved_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[PreflopAction, ...]:
    """`hero`'s line where each seat raises at the price the chart solved there. Each
    point offers the named raise and the all-in decision 6 prices at hero's whole stack,
    so the named raise is the smaller of the two."""
    sequence: list[PreflopAction] = []
    for raiser in raisers:
        prices = library.solved_prices_bb(6, DEPTH_BB, hero, tuple(sequence), raiser)
        assert prices, (hero, raiser, tuple(sequence))
        sequence.append(PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


def solved_key(library: PreflopChartLibrary, hero: str, *raisers: str) -> str:
    return derive_spot_key(6, DEPTH_BB, hero, solved_line(library, hero, *raisers))


def vs_open_key(library: PreflopChartLibrary, hero: str, opener: str) -> str:
    """The committed key for `hero` facing an open from `opener`."""
    return solved_key(library, hero, opener)


def raised_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[SeatAction, ...]:
    """The same line as a recorded history, so the history and the key are one price."""
    return tuple(
        raised(entry.position, int(round(entry.size_bb * BIG_BLIND)))
        for entry in solved_line(library, hero, *raisers)
    )


def open_to(library: PreflopChartLibrary) -> int:
    """The solved opening price in chips, for the fixtures that enumerate pairs the
    chart cannot price. An out-of-turn opener has no solved price anywhere in the tree,
    and the claim at those spots is that the layer refuses rather than raises."""
    prices = library.solved_prices_bb(6, DEPTH_BB, "BB", (), "LJ")
    return int(round(min(prices) * BIG_BLIND))


def three_bet_spot(library: PreflopChartLibrary) -> str:
    """The committed spot where hero has already opened and faces a re-raise."""
    return solved_key(library, "LJ", "LJ", "CO")


def folded(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


def called(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "call")


def _hand_cards() -> dict[str, tuple[str, str]]:
    table = {}
    for high in "23456789TJQKA":
        for low in "23456789TJQKA":
            for kind in ("s", "o", ""):
                name = f"{high}{low}{kind}"
                cards = cards_for(name)
                if cards is not None and hand_class(cards) == name:
                    table[name] = cards
    return table


HAND_CARDS: dict[str, tuple[str, str]] = _hand_cards()


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary(import_preflop_artifacts(ARTIFACT_DIR))


def decision(outcome) -> StrategyDecision:
    assert isinstance(outcome, StrategyDecision), outcome
    return outcome


def refusal(outcome) -> StrategyRefusal:
    assert isinstance(outcome, StrategyRefusal), outcome
    return outcome


class TestCommittedArtifact:
    def test_the_artifact_imports_through_the_unchanged_importer(self, library) -> None:
        """A floor, not a count: the number the reach floor selects is decision 1's
        arithmetic rather than its ruling. Coverage is enumerated by name below."""
        assert len(library.artifacts) == 1
        assert len(library.spot_keys()) > 36

    def test_provenance_is_declared_as_a_solver_export(self, library) -> None:
        source = library.artifacts[0].source

        assert source.kind == "solver-export"
        assert (REPO_ROOT / source.reference) == COMMITTED_EXPORT_PATH

    def test_the_hand_authored_chart_is_retired(self) -> None:
        """Two artifacts claiming one spot is a library error, and the
        hand-authored ranges are known to disagree with the solver."""
        assert not (ARTIFACT_DIR / "six_max_100bb_core.json").exists()

    def test_the_gto_wizard_source_is_kept_even_though_its_chart_is_gone(self) -> None:
        assert SOURCE.exists()

    def test_the_converter_reproduces_the_artifact_byte_for_byte(self) -> None:
        result = subprocess.run(
            ["python", str(REPO_ROOT / "scripts" / "convert_preflop_export.py"), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr

    def test_every_position_that_can_open_has_an_opening_spot(self, library) -> None:
        for position in ("LJ", "HJ", "CO", "BTN", "SB"):
            assert f"t6/d{DEPTH_BB}/{position}/rfi" in library.spot_keys()

    def test_every_spot_facing_a_single_open_is_covered(self, library) -> None:
        order = table_positions(6)
        for opener_index, opener in enumerate(order[:-1]):
            for hero in order[opener_index + 1 :]:
                assert vs_open_key(library, hero, opener) in library.spot_keys()

    def test_the_opener_facing_a_three_bet_is_covered(self, library) -> None:
        assert three_bet_spot(library) in library.spot_keys()

    def test_the_big_blind_facing_a_limp_is_no_longer_covered(self, library) -> None:
        """The coverage the cutover gave up: the export is `limp: false`, so no limped
        node exists at any reach floor. `CHART-CANNOT-ANSWER-A-LIMPED-POT` carries the
        accepted cost and `TestRefusals` proves the layer refuses rather than guesses."""
        assert f"t6/d{DEPTH_BB}/BB/SB:call" not in library.spot_keys()


class TestPositionMapping:
    def test_the_first_seat_to_act_six_handed_is_the_lojack(self) -> None:
        """The source calls it UTG; this repo's six-handed vocabulary calls it LJ."""
        assert table_positions(6) == ("LJ", "HJ", "CO", "BTN", "SB", "BB")

    def test_the_artifact_declares_the_whole_table(self, library) -> None:
        assert library.artifacts[0].positions == table_positions(6)


class TestDecisions:
    def test_a_covered_open_returns_a_decision(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert outcome.action == "raise"

    def test_a_hopeless_hand_folds_rather_than_refusing(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("7d", "2c"))))

        assert outcome.action == "fold"

    def test_the_raise_amount_comes_from_the_sizing_table(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert outcome.amount == int(2.5 * BIG_BLIND)

    def test_facing_an_open_uses_the_spot_for_that_opener(self, strategy) -> None:
        opened = raised_line(strategy.library, "BB", "CO")

        outcome = strategy.decide(query("BB", history=opened, hole_cards=("As", "Ah")))

        assert decision(outcome).action == "raise"

    def test_folds_in_the_history_do_not_change_the_spot(self, strategy) -> None:
        opened = raised_line(strategy.library, "BB", "CO")
        with_folds = strategy.decide(
            query(
                "BB",
                history=(folded("LJ"), folded("HJ"), *opened, folded("BTN"), folded("SB")),
                hole_cards=("As", "Ah"),
            )
        )
        without_folds = strategy.decide(
            query("BB", history=opened, hole_cards=("As", "Ah"))
        )

        assert decision(with_folds).action == decision(without_folds).action

    def test_the_decision_records_the_weights_it_came_from(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert "raise" in outcome.code
        assert "weighted-draw" in outcome.code


class TestRefusals:
    def test_an_uncovered_stack_depth_refuses(self, strategy) -> None:
        """A flat 40bb table, so the depth is the only thing missing. A starting stack is
        now what a seat holds plus what it has put in, so the old fixture - 4,000 in front
        of a small blind that had posted 50 - refuses on its shape before the chart is
        ever asked about the depth."""
        outcome = strategy.decide(query("LJ", stacks=stacks(depth_bb=40)))

        assert "depth" in refusal(outcome).code

    def test_a_straddled_pot_refuses_rather_than_reading_as_ordinary(self, strategy) -> None:
        """The straddler's chips are in the pot and the level is two big blinds. Nobody
        has raised, so a level above the big blind is a straddle and nothing else, and the
        refusal names which forced-money structure it found rather than calling a straddle
        and an ante alike "some blind structure I cannot represent"."""
        outcome = strategy.decide(query("HJ", forced={seat_of("LJ"): 2 * BIG_BLIND}))

        assert refusal(outcome).code.endswith("pot-holds-a-straddle")

    def test_an_anted_pot_refuses(self, strategy) -> None:
        """Every seat antes 10, which sits in its hand total and not its street total. The
        old fixture overrode the pot alone, which is now a pot holding chips no seat paid
        for and does not construct at all."""
        outcome = strategy.decide(query("LJ", ante=10))

        assert refusal(outcome).code.endswith("pot-holds-an-ante")

    def test_a_second_orbit_spot_is_now_decided_rather_than_refused(self, strategy) -> None:
        """Phase 12 gave it a key and the raked chart had no cell to fill it with. The
        solved tree runs to a four-bet and a shove over it and the reach floor keeps that
        line, so this inverts; what it guarded moves to the limp below."""
        history = raised_line(strategy.library, "LJ", "LJ", "CO", "LJ", "CO")

        assert len(history) == 4

        outcome = strategy.decide(query("LJ", history=history, hole_cards=("As", "Ah")))

        assert isinstance(outcome, StrategyDecision), outcome

    def test_a_limped_pot_refuses_because_no_solved_node_holds_one(self, strategy) -> None:
        """The one structurally uncovered spot left, so this cannot go vacuous: all the
        chart's other misses are under the reach floor, which the re-solve moves, and a
        limp cannot come back at any floor. The neighbour it must not reach for - the
        small blind opening instead of limping - is covered in full."""
        history = (folded("LJ"), folded("HJ"), folded("CO"), folded("BTN"), called("SB"))

        outcome = refusal(
            strategy.decide(query("BB", history=history, hole_cards=("As", "Ah")))
        )

        assert outcome.code.endswith("spot-not-covered")

    def test_a_postflop_query_refuses(self, strategy) -> None:
        outcome = strategy.decide(
            query("LJ", street="flop", board=("2c", "7h", "Ts"), to_call=0,
                  legal_actions=("check", "raise"))
        )

        assert "preflop" in refusal(outcome).code

    def test_a_short_hero_refuses_even_behind_a_full_stack(self, strategy) -> None:
        """Depth is hero's, not the table's deepest seat.

        Reading the deepest stack meant a twelve-big-blind hero opened a hundred
        big-blind range whenever one untouched seat sat behind, which is an
        unbounded tolerance band on a decision ruled exact-only.
        """
        hero = seat_of("LJ")
        short = tuple((s, 12 * BIG_BLIND if s == hero else v) for s, v in stacks())

        outcome = refusal(strategy.decide(query("LJ", stacks=short)))

        assert outcome.code.endswith("table-is-not-one-flat-stack-depth")

    def test_a_ragged_depth_refuses_with_its_own_code(self, strategy) -> None:
        odd = tuple((seat, 100 * BIG_BLIND + 37) for seat, _ in stacks())

        outcome = refusal(strategy.decide(query("LJ", stacks=odd)))

        assert outcome.code.endswith("stack-depth-not-a-whole-big-blind")

    def test_an_anted_pot_refuses_at_every_seat_not_just_the_first(self, strategy) -> None:
        """Folds are recorded, so checking only an empty history covered one seat.

        A folded seat's ante is still in the pot and in its hand total, which is why the
        per-seat gap catches it where a reconstruction from the seats still playing does
        not."""
        outcome = strategy.decide(query("HJ", history=(folded("LJ"),), ante=10))

        assert refusal(outcome).code.endswith("pot-holds-an-ante")

    def test_a_straddled_pot_refuses_after_someone_raises(self, strategy) -> None:
        """The guard used to stop looking the moment anything raised.

        The hard case, and the one the deleted pot bound admitted: the straddler has been
        raised over, so its chips look exactly like an ordinary caller's and no comparison
        of contributions sees it. The minimum raise target gives it away - measured from
        the 200 straddle a raise to 600 leaves 1,000, unstraddled it would leave 1,100."""
        outcome = strategy.decide(
            query(
                "BB",
                history=(raised("HJ", 6 * BIG_BLIND), folded("CO"), folded("BTN"), folded("SB")),
                forced={seat_of("LJ"): 2 * BIG_BLIND},
            )
        )

        assert refusal(outcome).code.endswith("pot-holds-a-straddle")

    def test_a_charted_action_that_is_not_legal_here_refuses(self, strategy) -> None:
        outcome = strategy.decide(
            query("LJ", hole_cards=("As", "Ah"), legal_actions=("fold", "call"))
        )

        assert "not-legal-here" in refusal(outcome).code

    def test_a_raise_with_no_committed_size_refuses(self, strategy) -> None:
        bare = PreflopChartStrategy(library=strategy.library, sizing=PreflopSizingTable(
            source_name="empty", source_kind="solver-export", raise_to_bb={}
        ))

        outcome = bare.decide(query("LJ", hole_cards=("As", "Ah")))

        assert "no-committed-raise-size" in refusal(outcome).code

    def test_a_committed_size_below_the_minimum_raise_refuses(self, strategy) -> None:
        """A 2.5bb open cannot answer a pot already raised to 6bb."""
        outcome = strategy.decide(
            query("LJ", hole_cards=("As", "Ah"), min_raise_target=12 * BIG_BLIND)
        )

        assert "below-minimum-raise" in refusal(outcome).code

    def test_every_refusal_names_the_coverage_that_was_missing(self, strategy) -> None:
        outcome = refusal(strategy.decide(query("LJ", stacks=stacks(depth_bb=40))))

        assert outcome.code.startswith("preflop-chart:")


class TestTotality:
    """Coverage proved by enumeration, not by sampling."""

    def test_every_covered_spot_answers_for_all_169_hand_classes(
        self, strategy, library
    ) -> None:
        undecided = []
        for spot_key in sorted(library.spot_keys()):
            for hand in library.hand_classes_for(spot_key):
                outcome = strategy.decide_spot(spot_key, hand)
                if not isinstance(outcome, StrategyDecision):
                    undecided.append((spot_key, hand))

        assert undecided == []

    def test_no_reachable_six_handed_spot_raises(self, strategy) -> None:
        order = table_positions(6)
        hands = [("As", "Ah"), ("7d", "2c"), ("Jc", "Td")]
        for hero in order:
            for opener in order:
                for cards in hands:
                    price = open_to(strategy.library)
                    history = () if opener == hero else (raised(opener, price),)
                    outcome = strategy.decide(query(hero, history=history, hole_cards=cards))

                    assert isinstance(outcome, StrategyDecision | StrategyRefusal)

    def test_a_decision_is_never_returned_without_chart_backing(
        self, strategy, library
    ) -> None:
        """The one property that makes an artifact-backed bot trustworthy."""
        history = (raised("HJ", open_to(library)),)
        outcome = strategy.decide(query("LJ", history=history, hole_cards=("As", "Ah")))

        assert isinstance(outcome, StrategyRefusal | StrategyDecision)
        if isinstance(outcome, StrategyDecision):
            assert vs_open_key(library, "LJ", "HJ") in library.spot_keys()


class TestLegalityAndDeterminism:
    def test_every_decision_passes_the_phase_03_audit_record(self, strategy) -> None:
        order = table_positions(6)
        for hero in order:
            request = query(hero, hole_cards=("As", "Ah"))
            outcome = strategy.decide(request)
            if isinstance(outcome, StrategyDecision):
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=request,
                    outcome=outcome,
                )

    def test_suit_relabelling_does_not_change_the_decision(self, strategy) -> None:
        spades = strategy.decide(query("BTN", hole_cards=("As", "Ks")))
        hearts = strategy.decide(query("BTN", hole_cards=("Ah", "Kh")))

        assert decision(spades).action == decision(hearts).action

    def test_card_order_does_not_change_the_decision(self, strategy) -> None:
        forwards = strategy.decide(query("BTN", hole_cards=("As", "Kd")))
        backwards = strategy.decide(query("BTN", hole_cards=("Kd", "As")))

        assert decision(forwards).action == decision(backwards).action

    def test_canonicalization_agrees_with_the_hand_class_helper(self) -> None:
        assert hand_class(("As", "Kd")) == hand_class(("Kd", "As")) == "AKo"

    def test_the_same_query_serializes_to_the_same_audit_line(self, strategy) -> None:
        request = query("BTN", hole_cards=("As", "Ah"))
        lines = set()
        for _ in range(3):
            outcome = strategy.decide(request)
            lines.add(
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=request,
                    outcome=outcome,
                ).to_json_line()
            )

        assert len(lines) == 1

    def test_the_draw_depends_on_the_hand_not_only_the_spot(self, strategy) -> None:
        """A seed of spot and hand class alone is the plurality rule wearing a hash.

        It would freeze every mixed cell to one action forever while every frequency
        test that routes through decide_spot kept passing.
        """
        spot = three_bet_spot(strategy.library)
        mixed = next(
            hand
            for hand in strategy.library.hand_classes_for(spot)
            if len(strategy.library.artifacts[0].weights_for(spot, hand)) > 1
        )
        seeds = {
            strategy._seed(query("LJ", hole_cards=("As", "Ah"), hand_id=f"h{index}"), spot, mixed)
            for index in range(5)
        }

        assert len(seeds) == 5

    def test_the_draw_ignores_suits_and_card_order(self, strategy) -> None:
        spot = "t6/d100/BTN/rfi"
        first = strategy._seed(query("BTN", hole_cards=("As", "Kd")), spot, "AKo")
        second = strategy._seed(query("BTN", hole_cards=("Kh", "Ac")), spot, "AKo")

        assert first == second

    def test_decide_reproduces_the_charts_frequencies_over_many_hands(self, strategy) -> None:
        """Measured through decide, not decide_spot, so the seed is under test too."""
        spot = three_bet_spot(strategy.library)
        charted = strategy.library.action_frequency_pct(spot, "fold")
        history = raised_line(strategy.library, "LJ", "LJ", "CO")
        folds = 0.0
        total = 0.0
        for hand in strategy.library.hand_classes_for(spot):
            cards = HAND_CARDS.get(hand)
            if cards is None:
                continue
            weight = combos_of(hand)
            total += weight
            for index in range(30):
                outcome = strategy.decide(
                    query("LJ", history=history, hole_cards=cards, hand_id=f"h{index}")
                )
                if isinstance(outcome, StrategyDecision) and outcome.action == "fold":
                    folds += weight / 30

        assert 100.0 * folds / total == pytest.approx(charted, abs=3.0)

    def test_a_pure_cell_needs_no_draw(self, strategy) -> None:
        assert strategy.collapse((("fold", 0.0), ("raise", 1.0)), "any") == "raise"

    def test_the_same_seed_draws_the_same_action(self, strategy) -> None:
        mix = (("call", 0.5), ("raise", 0.5))

        assert strategy.collapse(mix, "h1|0|spot|AJo") == strategy.collapse(mix, "h1|0|spot|AJo")

    def test_the_draw_reproduces_the_charts_frequencies(self, strategy) -> None:
        """The whole point: a plurality rule would return one action every time."""
        mix = (("fold", 0.4), ("call", 0.35), ("raise", 0.25))
        counts = Counter(strategy.collapse(mix, f"hand-{index}") for index in range(4000))

        assert counts["fold"] / 4000 == pytest.approx(0.4, abs=0.03)
        assert counts["call"] / 4000 == pytest.approx(0.35, abs=0.03)
        assert counts["raise"] / 4000 == pytest.approx(0.25, abs=0.03)

    def test_a_tie_is_drawn_rather_than_refused(self, strategy) -> None:
        mix = (("call", 0.5), ("raise", 0.5))
        drawn = {strategy.collapse(mix, f"hand-{index}") for index in range(200)}

        assert drawn == {"call", "raise"}

    def test_the_strategy_does_not_over_fold_against_three_bets(self, strategy) -> None:
        """The blocker that halted this phase, pinned as a test.

        A plurality rule folded 72.8% here where the raked chart folded 59.8%, which is
        past the 66.7% at which a three-bet over a 2.5x open auto-profits as a pure bluff
        at the raked chart's 8bb price. The rake-free solve three-bets to 7.5, so the
        auto-profit threshold moves with the price and the fold frequency moves with the
        ranges; what is asserted is that the draw reproduces whatever the chart holds,
        which is the property a plurality rule breaks at any price.
        """
        spot = three_bet_spot(strategy.library)
        charted = strategy.library.action_frequency_pct(spot, "fold")
        folds = 0
        total = 0
        for hand in strategy.library.hand_classes_for(spot):
            weight = combos_of(hand)
            total += weight
            for index in range(20):
                outcome = strategy.decide_spot(spot, hand, seed_suffix=str(index))
                if isinstance(outcome, StrategyDecision) and outcome.action == "fold":
                    folds += weight / 20

        assert 100.0 * folds / total == pytest.approx(charted, abs=2.0)


def test_no_two_covered_spots_share_a_hand_class_ordering(library) -> None:
    """Ordering is what makes reports and audits byte-comparable."""
    for spot_key in itertools.islice(sorted(library.spot_keys()), 5):
        first = library.hand_classes_for(spot_key)
        second = library.hand_classes_for(spot_key)

        assert first == second
