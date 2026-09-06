"""Write the table-state report a human reads, and fail rather than publish a bad figure.

Rendering, plus the constructed tables the rendering is about. Every number below is
measured in `poker_training_bot.table_state.measures` and checked in
`poker_training_bot.table_state.checks`, which raises rather than returning a
figure it cannot stand behind, so a report that gets written is a report whose measurements
held. Two mutation canaries name this command in `must_fail`: one puts hero's depth back to
being taken from the price it is being offered, the other drops the minimum-raise signal
that is the only thing able to see an absorbed straddle. Both make this command exit
non-zero, which is the whole reason the checks are here rather than in the prose.

The tables in this file are constructions rather than data, and the report says so wherever
it prints one. The corpus is the only data in it, and the corpus cannot express a single
asymmetric, straddled or anted table, so the constructions carry the discovery and the
corpus carries a zero-delta regression proof.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from fractions import Fraction
from textwrap import fill

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.data_pipeline.comparison import _query_for  # noqa: E402
from poker_training_bot.hand_history import load_hand_history_file  # noqa: E402
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand  # noqa: E402
from poker_training_bot.poker_core.positions import position_for_seat  # noqa: E402
from poker_training_bot.solver_artifacts.lookup import ChartHit, ChartMiss  # noqa: E402
from poker_training_bot.strategy.contract import (  # noqa: E402
    SeatAction,
    SeatState,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import (  # noqa: E402
    REFUSE_BLIND_STRUCTURE,
    REFUSE_SHORT_LIVE_SEAT,
    PreflopChartStrategy,
)
from poker_training_bot.table_state import measures  # noqa: E402
from poker_training_bot.table_state.checks import validate  # noqa: E402
from poker_training_bot.table_state.forced_money import (  # noqa: E402
    unexplained_contributions,
)
from poker_training_bot.table_state.measures import (  # noqa: E402
    ANTED,
    CLEAN,
    INVISIBLE,
    RESIDUAL,
    STRADDLED,
    TABLE_SHAPE_CODES,
    CorpusCounts,
    DepthProbe,
    StraddleProbe,
    TableStateReportError,
)

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_table_state_report.txt"
WRAP = 88

# The constructed six-handed table every probe below is a variation of. Seats 0 to 5 with
# the button at 3 puts the lojack at seat 0, which is the seat order a reader sees printed.
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3
SMALL_BLIND = 50
BIG_BLIND = 100
FULL_STACK = 100 * BIG_BLIND
OPEN_TO = 250
THREE_BET_TO = 800
STRADDLE = 2 * BIG_BLIND


def wrapped(text: str, indent: str = "") -> list[str]:
    """Prose wrapped here rather than by a terminal, so the committed file reads the same."""
    return fill(
        " ".join(text.split()),
        width=WRAP,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    ).splitlines()


def seat_of(position: str) -> int:
    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise TableStateReportError(f"no seat holds {position}")


def table(
    hero: str,
    contributed: dict[str, int] | None = None,
    *,
    starting: dict[str, int] | None = None,
    ante: int = 0,
    current_bet: int = BIG_BLIND,
    min_raise_target: int | None = None,
    history: tuple[SeatAction, ...] = (),
    folded: tuple[str, ...] = (),
    hole_cards: tuple[str, str] = ("As", "Ah"),
) -> StrategyQuery:
    """One constructed six-handed preflop table, built from what each seat has put in.

    Every stack is derived from what that seat sat down with less what it has put in, so no
    fixture can state the two inconsistently. An ante is dead money: it leaves each stack
    and enters the pot without moving the level or the price, so it lands in the hand figure
    and not in the street figure, which is exactly what makes it visible as forced money.
    """
    hero_seat = seat_of(hero)
    folded_seats = {seat_of(name) for name in folded}
    paid = {seat_of(name): chips for name, chips in (contributed or {}).items()} or {
        seat_of("SB"): SMALL_BLIND,
        seat_of("BB"): BIG_BLIND,
    }
    sat_down = {seat: FULL_STACK for seat in SEATS}
    sat_down.update({seat_of(name): chips for name, chips in (starting or {}).items()})
    stacks = tuple((seat, sat_down[seat] - paid.get(seat, 0) - ante) for seat in SEATS)
    hero_stack = dict(stacks)[hero_seat]
    to_call = min(max(current_bet - paid.get(hero_seat, 0), 0), hero_stack)
    if to_call == 0:
        legal: tuple[str, ...] = ("check", "raise")
    elif to_call == hero_stack:
        # Hero is all-in for the call, so no raise is on offer and the query rejects one.
        legal = ("fold", "call")
    else:
        legal = ("fold", "call", "raise")
    return StrategyQuery(
        hand_id="constructed",
        street="preflop",
        seat=hero_seat,
        button_seat=BUTTON,
        hole_cards=hole_cards,
        board=(),
        legal_actions=legal,
        to_call=to_call,
        current_bet=current_bet,
        min_raise_target=min_raise_target or current_bet + BIG_BLIND,
        pot=sum(paid.values()) + ante * len(SEATS),
        stacks=stacks,
        seat_states=tuple(
            SeatState(
                seat=seat,
                street_bet=paid.get(seat, 0),
                committed_total=paid.get(seat, 0) + ante,
                folded=seat in folded_seats,
                all_in=sat_down[seat] - paid.get(seat, 0) - ante == 0,
            )
            for seat in SEATS
        ),
        blinds=(SMALL_BLIND, BIG_BLIND),
        preflop_actions=history,
    )


def raised(position: str, amount: int) -> SeatAction:
    return SeatAction(seat_of(position), "raise", amount)


def called(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "call")


def dropped(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


# --------------------------------------------------------------------------- #
# The constructed tables
# --------------------------------------------------------------------------- #


def three_bet_table() -> StrategyQuery:
    """Hero opened to 2.5bb, the cutoff three-bet to 8bb, and hero is deciding.

    Every seat sat down with 100bb, so the table is flat and the committed chart holds the
    cell. What it is not is flat in *held* chips: hero put in 250 and holds 97.5bb, the
    cutoff put in 800 and holds 92bb, and the blinds hold 99.5bb and 99bb. That difference
    is the whole of `ASYMMETRIC-EFFECTIVE-STACKS`, read from the answering side.
    """
    return table(
        "LJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": OPEN_TO, "CO": THREE_BET_TO},
        current_bet=THREE_BET_TO,
        min_raise_target=THREE_BET_TO + (THREE_BET_TO - OPEN_TO),
        history=(raised("LJ", OPEN_TO), raised("CO", THREE_BET_TO)),
        folded=("HJ", "BTN"),
    )


def absorbed_straddle_table() -> StrategyQuery:
    """50/100 with a 200 straddle, an open to 600, the straddler and the big blind calling.

    The pot is 1,850 where the deleted bound allowed 1,950, so it was admitted. The
    contributions are 50/600/600/600, which is exactly what an unstraddled pot at the same
    price produces, so nothing about the money gives it away. The minimum raise does: the
    first raise was measured from the straddle rather than from the big blind, so the table
    offers 1,000 where two declared blinds and a recorded raise to 600 predict 1,100.
    """
    return table(
        "BTN",
        {"SB": SMALL_BLIND, "BB": 600, "LJ": 600, "CO": 600},
        current_bet=600,
        min_raise_target=1000,
        history=(dropped("HJ"), raised("CO", 600), dropped("SB"), called("BB"), called("LJ")),
        folded=("HJ", "SB"),
    )


def unstraddled_control() -> StrategyQuery:
    """The same pot at the same price with nothing forced in it, so the census can be wrong.

    Identical to the absorbed straddle in every field but one: the minimum raise is 1,100,
    which is what 50/100 blinds and a recorded raise to 600 predict. Reporting a straddle
    here would make a poker claim out of a producer's arithmetic.
    """
    return table(
        "BTN",
        {"SB": SMALL_BLIND, "BB": 600, "LJ": 600, "CO": 600},
        current_bet=600,
        min_raise_target=1100,
        history=(dropped("HJ"), raised("CO", 600), dropped("SB"), called("BB"), called("LJ")),
        folded=("HJ", "SB"),
    )


def invisible_straddle_table() -> StrategyQuery:
    """The phase's headline exception, on a table an ordinary betting round produces.

    50/100 with the big blind straddling to 200. A straddler acts last in the first orbit, and
    the big blind already does, so nothing here acts out of turn: the lojack and the hijack
    fold, the cutoff opens to 500 - the smallest legal open over a 200 level is 400 - the
    button and the small blind fold, the big blind three-bets to 1,350, and the cutoff decides.

    Every price is legal at the straddled table's own minimums, and every seat holds exactly
    what its own actions explain, because the straddler's 200 is absorbed into the 1,350 it
    raised to. The table offers a minimum re-raise of 1,350 plus the 850 it was raised by, and
    the two declared blinds plus those same two raise-to amounts predict the same 2,200: past
    the first raise the prediction is a difference of two recorded raises, and the straddle
    perturbs only the first. So all three signals are silent and the pot reaches the chart.
    """
    return table(
        "CO",
        {"SB": SMALL_BLIND, "BB": 1350, "CO": 500},
        current_bet=1350,
        min_raise_target=2200,
        history=(
            dropped("LJ"),
            dropped("HJ"),
            raised("CO", 500),
            dropped("BTN"),
            dropped("SB"),
            raised("BB", 1350),
        ),
        folded=("LJ", "HJ", "BTN", "SB"),
    )


def worked_capped_hero() -> StrategyQuery:
    """The decision list's worked example: 150 held, 100 in, a level of 300, at 5/10.

    Three seats. Hero re-raised to 100 out of a 250 stack, the button shoved to 300, and the
    price is 150, which is every chip hero has. Hero started with 250, so hero is 25bb deep;
    the street's bet level is 300, which is 30bb, and that is the number the pre-phase
    derivation returned for exactly this hero.
    """
    seats = (0, 1, 2)
    paid = {0: 100, 1: 10, 2: 300}
    sat_down = {0: 250, 1: 250, 2: 300}
    stacks = tuple((seat, sat_down[seat] - paid[seat]) for seat in seats)
    return StrategyQuery(
        hand_id="worked-example",
        street="preflop",
        seat=0,
        button_seat=2,
        hole_cards=("As", "Ah"),
        board=(),
        legal_actions=("fold", "call"),
        to_call=min(300 - paid[0], dict(stacks)[0]),
        current_bet=300,
        min_raise_target=500,
        pot=sum(paid.values()),
        stacks=stacks,
        seat_states=tuple(
            SeatState(
                seat=seat,
                street_bet=paid[seat],
                committed_total=paid[seat],
                folded=seat == 1,
                all_in=sat_down[seat] - paid[seat] == 0,
            )
            for seat in seats
        ),
        blinds=(5, 10),
        preflop_actions=(
            SeatAction(2, "raise", 25),
            SeatAction(0, "raise", 100),
            SeatAction(1, "fold"),
            SeatAction(2, "raise", 300),
        ),
    )


def under_raise_table() -> StrategyQuery:
    """A recorded re-raise to 3bb over a 2.5bb open, which no legal full raise produces.

    The minimum legal re-raise is 4bb: the level plus the larger of the previous increment
    and one big blind. The spot key renders this sequence anyway, which is the first of the
    two findings Phase 12 handed on.

    The minimum stated here is the engine's own 450, not 400: an incomplete raise does not
    reset the increment, so with the level at 300 and the minimum raise still 150 the table
    offers 450. A table stating anything else is not one this repo's engine can produce, and
    the reading of this row turns on that number.
    """
    return table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO, "BTN": 300},
        current_bet=300,
        min_raise_target=450,
        history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO), raised("BTN", 300)),
        folded=("LJ", "HJ"),
    )


def short_all_in_raise_table() -> StrategyQuery:
    """The button was all-in for 300 over the same 250 open, which the history records as a raise.

    The other half of the under-raise pair, constructed rather than described. It carries the
    same recorded history as `under_raise_table` - a raise to 250 and a raise to 300 - so the
    vocabulary writes one string for both, and the only thing separating them is what the button
    sat down with. The engine's minimum is 450 here as it is there: an incomplete raise does not
    reset the increment.
    """
    return table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO, "BTN": 300},
        starting={"BTN": 300},
        current_bet=300,
        min_raise_target=450,
        history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO), raised("BTN", 300)),
        folded=("LJ", "HJ"),
    )


def full_call_table() -> StrategyQuery:
    """The button called the full 250 out of a 100bb stack."""
    return table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO, "BTN": OPEN_TO},
        current_bet=OPEN_TO,
        min_raise_target=400,
        history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO), called("BTN")),
        folded=("LJ", "HJ"),
    )


def short_all_in_call_table() -> StrategyQuery:
    """The button called all-in for 120 against the same 250 open."""
    return table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO, "BTN": 120},
        starting={"BTN": 120},
        current_bet=OPEN_TO,
        min_raise_target=400,
        history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO), called("BTN")),
        folded=("LJ", "HJ"),
    )


def moving_fixture_probes() -> tuple[DepthProbe, ...]:
    """Every preflop decision of the one committed fixture this phase moves.

    Built here rather than in `measures`, with every other probe in this report: the module
    next door measures and checks figures, and constructing the tables the figures are about
    is this file's job whether the table comes out of a fixture or out of a constructor.

    One legal holding is supplied for all three seats and nothing reads it: the claim is
    about the table's shape, settled before a hand class exists.
    """
    probes: list[DepthProbe] = []
    for hand in load_hand_history_file(measures.SAMPLE_FIXTURE):
        if hand.hand_id != measures.MOVING_FIXTURE_HAND:
            continue
        replayed: list[DecisionPoint] = []
        replay_hand(hand, on_decision=replayed.append)
        for point in replayed:
            query = _query_for(point, ("Ah", "Kh"))
            if query is not None:
                label = f"{measures.MOVING_FIXTURE_HAND}, seat {query.seat} to act"
                probes.append(DepthProbe(label, query, measures.BEFORE_MOVING_CODE))
    if not probes:
        raise TableStateReportError(
            f"{measures.MOVING_FIXTURE_HAND} has no preflop decision, so the only live evidence"
            " is gone"
        )
    return tuple(probes)


def depth_probes(strategy: PreflopChartStrategy) -> tuple[tuple[DepthProbe, str], ...]:
    """The constructed tables where hero's depth is the thing under the light."""
    short_buy_in = table(
        "LJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": OPEN_TO},
        starting={"LJ": 50 * BIG_BLIND},
        current_bet=OPEN_TO,
        min_raise_target=400,
        history=(raised("LJ", OPEN_TO),),
    )
    folded_short_seat = table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO},
        starting={"SB": 20 * BIG_BLIND},
        current_bet=OPEN_TO,
        min_raise_target=400,
        history=(
            dropped("LJ"),
            dropped("HJ"),
            raised("CO", OPEN_TO),
            dropped("BTN"),
            dropped("SB"),
        ),
        folded=("LJ", "HJ", "BTN", "SB"),
    )
    ragged_hero = table(
        "LJ",
        starting={"LJ": FULL_STACK + 50, "CO": 2 * FULL_STACK},
    )
    two_shorter_seats = table(
        "LJ",
        starting={"HJ": 90 * BIG_BLIND, "CO": 20 * BIG_BLIND},
    )
    return (
        (
            DepthProbe("a flat table, hero facing a three-bet", three_bet_table()),
            "Nobody is short. Hero holds 97.5bb and the three-bettor holds 92bb, and neither"
            " is a shallow seat: both sat down with 100bb and the difference is money already"
            " in the pot. This is the table the chart is allowed to answer.",
        ),
        (
            DepthProbe("the worked example: a capped hero at 5/10", worked_capped_hero()),
            "Hero holds 150, has 100 in, and the price is 150, which is everything hero has."
            " Hero started with 250 and is 25bb deep. The street's bet level is 300, which is"
            " 30bb, and that is what the pre-phase derivation returned here. The button is"
            " genuinely deeper, so this table refuses, and it refuses naming the button.",
        ),
        (
            DepthProbe("a hero who bought in short", short_buy_in),
            "Hero sat down with 50bb at a table of 100bb seats. It does not refuse because"
            " hero's own depth is odd - 50bb is a whole number of big blinds - but because a"
            " live seat is deeper by construction, so the table is not one flat depth. A hero"
            " who bought in short and a hero who is merely short on this street read as one"
            " sentence and are not. This row is a construction and not a reachable state:"
            " hero's own open stands in front of it with nobody having acted since, which no"
            " betting round produces. It is written that way so that the only thing separating"
            " it from the flat table above is what hero sat down with.",
        ),
        (
            DepthProbe("a folded seat holding 19.5bb", folded_short_seat),
            "The small blind bought in for 20bb, posted, and folded. Its chips stay in the pot"
            " and in the reconciliation, and it cannot change a chip of hero's decision,"
            " because effective stack is pairwise and against seats that can still act. This"
            " table is flat and gets answered.",
        ),
        (
            DepthProbe("two live seats shorter than hero, at 90bb and 20bb", two_shorter_seats),
            "Which of the two the refusal names is the whole of this row. The hijack is shorter"
            " than hero and comes first in seat order; the cutoff is shorter still. The seat"
            " reported is the cutoff, because the shortest live stack is the one that caps"
            " hero's effective stack and is the number a future tolerance would have to be set"
            " against: 90bb against 100bb is still 100bb poker, and 20bb is a different game."
            " Reporting the first offender in seat order instead would make the recorded depth"
            " depend on the seating - the same two stacks in swapped chairs would report 90bb"
            " here and 20bb from the other side of the table. This row is the one place in the"
            " report where the two rules give different answers, so it is what stops the check"
            " below from being a check that cannot fail.",
        ),
        (
            DepthProbe("a ragged hero hiding a 200bb seat", ragged_hero),
            "Hero sat down with 10,050 chips, which is 100.5 big blinds, and the cutoff sat"
            " down with 200bb. Only the raggedness is reported. This is what judgment call 7"
            " costs, and it is stated rather than fixed.",
        ),
    )


def straddle_probes() -> tuple[tuple[StraddleProbe, str], ...]:
    """Every pot the census classifies, with what is truly in it."""
    limped_straddle = table(
        "HJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": STRADDLE},
        current_bet=STRADDLE,
        min_raise_target=2 * STRADDLE,
    )
    raised_straddle = table(
        "HJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "BTN": STRADDLE, "LJ": 600},
        current_bet=600,
        min_raise_target=1000,
        history=(raised("LJ", 600),),
    )
    anted = table("LJ", ante=10)
    dead_blind = table(
        "HJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": BIG_BLIND},
        history=(dropped("LJ"),),
        folded=("LJ",),
    )
    # Two seats returning to the table post before the button reaches them and both fold: the
    # lojack owes the small blind, the hijack owes the big one. Two unexplained seats holding
    # DIFFERENT amounts, which is what makes the seat the refusal names a measurable claim
    # rather than a coincidence - `dead_blind` above has one such seat, so on it every rule for
    # choosing among them gives the same answer.
    two_dead_blinds = table(
        "CO",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": SMALL_BLIND, "HJ": BIG_BLIND},
        history=(dropped("LJ"), dropped("HJ")),
        folded=("LJ", "HJ"),
    )
    absorbed_big_blind_straddle = table(
        "HJ",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "LJ": BIG_BLIND},
        history=(called("LJ"),),
    )
    limper = table(
        "BB",
        {"SB": BIG_BLIND, "BB": BIG_BLIND},
        history=(
            dropped("LJ"),
            dropped("HJ"),
            dropped("CO"),
            dropped("BTN"),
            called("SB"),
        ),
        folded=("LJ", "HJ", "CO", "BTN"),
    )
    ordinary_open = table(
        "BB",
        {"SB": SMALL_BLIND, "BB": BIG_BLIND, "CO": OPEN_TO},
        current_bet=OPEN_TO,
        min_raise_target=400,
        history=(dropped("LJ"), dropped("HJ"), raised("CO", OPEN_TO)),
        folded=("LJ", "HJ"),
    )
    return (
        (
            StraddleProbe(
                "a 200 straddle already called to the level",
                STRADDLED,
                absorbed_straddle_table(),
                absorbed=True,
            ),
            "The pot the deleted bound admitted. Nothing about the chips gives it away and"
            " only the minimum raise does.",
        ),
        (
            StraddleProbe(
                "the same pot at the same price, unstraddled", CLEAN, unstraddled_control()
            ),
            "The negative control. One field differs from the row above, and the answer has to"
            " differ with it. It still refuses - two callers behind the raiser with the button"
            " yet to act is not a sequence the key space can write - but it is not refused as"
            " forced money, which is the claim being made here.",
        ),
        (
            StraddleProbe("a 200 straddle in an unraised pot", STRADDLED, limped_straddle),
            "Nothing has raised, so the level can only be the big blind, and it is 200.",
        ),
        (
            StraddleProbe("a 200 button straddle, raised to 600", STRADDLED, raised_straddle),
            "The straddler has not acted, so its 200 is unexplained money too. The order is"
            " ruled: the straddle signals fire first, so this is named a straddle rather than"
            " filed under the residual code.",
        ),
        (
            StraddleProbe("a 10-chip ante from every seat", ANTED, anted),
            "Dead money, uniform across the table. It is in each seat's hand figure and not"
            " in its street figure, so hero still owes the full big blind: an ante buys"
            " nothing off the price.",
        ),
        (
            StraddleProbe("a dead blind on a seat that has folded", RESIDUAL, dead_blind),
            "The lojack posted on sitting down and folded. Not a straddle, because the level"
            " is still the big blind; not an ante, because an ante is uniform. This is the"
            " residual the kept code exists for.",
        ),
        (
            StraddleProbe("two dead blinds of different sizes", RESIDUAL, two_dead_blinds),
            "The lojack owes 50 and the hijack owes 100, and both folded. Which of the two the"
            " refusal names is the whole of this row, and it is the only pot in this report"
            " where more than one seat holds unexplained money in different amounts - the ante"
            " row above has six such seats and they are all equal, which is what makes it an"
            " ante rather than this. The seat reported is the hijack, because it is the one"
            " holding the most, and the dead-blind row above cannot show that: with one"
            " unexplained seat, naming the most forced chips and naming the lowest chair are"
            " the same answer. Here they are seat 1 and seat 0, so the published detail says"
            " which rule produced it and the check below can fail.",
        ),
        (
            StraddleProbe(
                "a straddle equal to the big blind, already called",
                INVISIBLE,
                absorbed_big_blind_straddle,
            ),
            "The residual all three signals miss. It moves no level, predicts what a limp"
            " predicts, and shifts no minimum, so it is answered as the limped pot it is"
            " indistinguishable from. Reported rather than claimed as covered.",
        ),
        (
            StraddleProbe("a small blind completing to 100", CLEAN, limper),
            "The commonest pot in a home game. Reconstruction is against the blinds *and*"
            " each seat's own recorded actions, or this would read as an anted table.",
        ),
        (
            StraddleProbe("an ordinary 2.5bb cutoff open", CLEAN, ordinary_open),
            "The most ordinary spot the chart holds. A signal firing here would replace a"
            " bound that over-refused with a rule that over-refuses differently.",
        ),
    )


# --------------------------------------------------------------------------- #
# The deleted bound, reproduced only to print what it allowed
# --------------------------------------------------------------------------- #


def deleted_bound(query: StrategyQuery) -> int:
    """The largest pot the deleted rule could explain: two blinds plus one level per action.

    Reproduced here, in the report that prints its numbers, and consulted by nothing that
    decides anything. It was generous by construction, which is how a straddled pot with
    several callers slipped under it.
    """
    small_blind, big_blind = query.blinds
    voluntary = sum(1 for entry in query.preflop_actions if entry.action in ("call", "raise"))
    return small_blind + big_blind + voluntary * query.current_bet


def bound_verdict(query: StrategyQuery) -> str:
    """What the deleted rule made of a pot: it refused a pot too big, or a moved level."""
    _, big_blind = query.blinds
    raised_here = any(entry.action == "raise" for entry in query.preflop_actions)
    if not raised_here and query.current_bet != big_blind:
        return "refused (the level is not the big blind)"
    if query.pot > deleted_bound(query):
        return f"refused (pot {query.pot} over its bound of {deleted_bound(query)})"
    return f"admitted (pot {query.pot} at or under its bound of {deleted_bound(query)})"


def outcome_line(strategy: PreflopChartStrategy, query: StrategyQuery) -> str:
    """What the strategy did with a query, as one line a reader can take at face value."""
    outcome = strategy.decide(query)
    if isinstance(outcome, StrategyRefusal):
        detail = ", ".join(f"{name} {value}" for name, value in outcome.detail)
        return f"refused  {outcome.code}" + (f"  ({detail})" if detail else "")
    amount = "" if outcome.amount is None else f" to {outcome.amount}"
    return f"{outcome.action}{amount}  {outcome.code}"


# --------------------------------------------------------------------------- #
# The checks this file owns, beside the ones in `measures`
# --------------------------------------------------------------------------- #


def one_key_two_tables(
    strategy: PreflopChartStrategy, answered: StrategyQuery, refused: StrategyQuery
) -> str:
    """The one key a pair of tables renders, taken from the lookup that actually happened.

    What is checked is the pair, rather than the two English labels a caller writes beside it. A
    spot key is four things - table size, hero's depth, hero's position, and the sized action
    sequence in front of hero - and these two tables agree on every one of them, so the
    vocabulary has one string for both. The string itself is read off the lookup rather than
    composed here, because a second derivation of "what spot is this" can drift from the one the
    strategy used.

    Only one of the pair ever gets that far, and that asymmetry is the finding closing rather
    than a flaw in the demonstration: the other table holds a seat that put in everything it sat
    down with, which is a live seat shorter than hero, and it is refused at the depth check
    before any key is built. Both halves are asserted here, so a change that let the short table
    through, or that stopped the other one reaching the chart, fails this command rather than
    publishing a merged key that nothing renders.
    """
    if (
        answered.preflop_actions != refused.preflop_actions
        or answered.blinds != refused.blinds
        or tuple(seat for seat, _ in answered.stacks) != tuple(seat for seat, _ in refused.stacks)
        or answered.seat != refused.seat
        or answered.button_seat != refused.button_seat
        or measures.hero_start(answered) != measures.hero_start(refused)
    ):
        raise TableStateReportError(
            "the two tables this key is claimed to merge disagree on one of the four things a"
            " spot key is made of, so the vocabulary does not write one string for both of them"
        )
    found = strategy.chart_lookup(answered)
    if not isinstance(found, ChartHit | ChartMiss) or not found.spot_key:
        raise TableStateReportError(
            "the table this report says renders a key no longer reaches one, so there is no key"
            f" here to be merged: the lookup came back {found}"
        )
    reached = strategy.chart_lookup(refused)
    if reached is not None:
        raise TableStateReportError(
            "the short table this report says is refused before any key is built reached the"
            f" chart and asked about {reached}"
        )
    outcome = strategy.decide(refused)
    if not isinstance(outcome, StrategyRefusal) or outcome.code != REFUSE_SHORT_LIVE_SEAT:
        raise TableStateReportError(
            "the short table this report says is refused for holding a live seat shorter than"
            f" hero is answered {outcome_line(strategy, refused)} instead"
        )
    return found.spot_key


def validate_bound_coverage(
    strategy: PreflopChartStrategy, probes: Sequence[tuple[StraddleProbe, str]]
) -> None:
    """Every pot the deleted bound refused is still refused by something.

    The census prints the deleted bound's verdict beside the replacement's on every row, and two
    columns side by side read as a comparison whether or not anything compares them. This is the
    comparison. The contract deletes the bound only once its replacement refuses every pot the
    bound refused, and that rested on one frozen test covering two pots; the implication the two
    columns already carry is that a pot the bound refused cannot come out of the replacement as
    holding no forced money at all.

    It is not the whole of the criterion, which is about every pot rather than about these ones:
    what it adds is that a probe where the replacement loses coverage stops the report from
    publishing under a claim its own table contradicts. The antecedent has to be met somewhere
    or the implication is vacuous, so a census in which the bound refuses nothing fails too.

    Recorded rather than fixed, because a reader deserves to know how much this one is worth: on
    the probe table as it stands it is SHADOWED and cannot fail. `_validate_straddle_census` runs
    first, from `validate`, and pins every probe's verdict to the `truth` its own row declares, so
    `refused by the bound implies not CLEAN` follows from that check plus two hardcoded columns of
    the same static table - the bound's verdict and the declared truth are both data, and no row
    declares CLEAN under a bound that refuses it. Shadowed is not the same as tautological, and
    the difference was measured: with the census check disabled this one does fire. So it is
    falsifiable, by a probe-table data edit, and it is kept for exactly that - it is the check
    that survives if the census's declared truths are ever loosened, or if a row lands whose two
    columns disagree. Deliberately not strengthened into something that fails on today's table:
    the criterion it stands for is about every pot rather than about these ten, and a stronger
    rule here would only be a stronger claim about the ten.
    """
    refused_by_the_bound = 0
    for probe, _ in probes:
        if not bound_verdict(probe.query).startswith("refused"):
            continue
        refused_by_the_bound += 1
        verdict = measures.forced_money_verdict(strategy, probe.query)
        if verdict == CLEAN:
            raise TableStateReportError(
                f"{probe.label}: the deleted bound refused this pot and the replacement counts it"
                f" as {verdict!r}, so deleting the bound lost coverage rather than replacing it"
            )
    if not refused_by_the_bound:
        raise TableStateReportError(
            "the deleted bound refuses no pot in this census, so nothing here could show the"
            " replacement covering it"
        )


def validate_residual_seat(
    strategy: PreflopChartStrategy, probes: Sequence[tuple[StraddleProbe, str]]
) -> None:
    """Which seat a residual refusal names, recomputed here from the seat states.

    The refusal names the seat holding the MOST chips its own actions do not explain, ties to the
    lowest chair, because a figure the seating decides is not evidence. Nothing in `tests/**`
    can tell that rule from naming the lowest chair outright, and this phase has already been
    caught once by exactly that: a selection rule reverted with every test still green. So the
    expected seat is recomputed below from the contributions rather than asked of the rule, and
    a census with no row where the two answers differ fails as well, since on a pot with one
    unexplained seat every rule for choosing among them gives the same answer and the check
    could not fail.
    """
    distinguishing = 0
    named = 0
    for probe, _ in probes:
        query = probe.query
        outcome = strategy.decide(query)
        if not isinstance(outcome, StrategyRefusal) or outcome.code != REFUSE_BLIND_STRUCTURE:
            continue
        named += 1
        forced = unexplained_contributions(
            tuple(seat for seat, _ in query.stacks),
            query.button_seat,
            query.blinds,
            query.preflop_actions,
            {state.seat: state.committed_total for state in query.seat_states},
        )
        if not forced:
            raise TableStateReportError(
                f"{probe.label}: the strategy refused this pot for holding forced money of no"
                " named kind, and recomputing it from the seat states finds none"
            )
        seat, chips = max(forced.items(), key=lambda pair: (pair[1], -pair[0]))
        if outcome.named("seat") != str(seat) or outcome.named("forced_chips") != str(chips):
            raise TableStateReportError(
                f"{probe.label}: the seats holding chips their own actions do not explain are"
                f" {dict(sorted(forced.items()))}, so the one holding the most is seat {seat} with"
                f" {chips}, and the refusal names seat {outcome.named('seat')} with"
                f" {outcome.named('forced_chips')} chips"
            )
        distinguishing += seat != min(forced)
    if not named or not distinguishing:
        raise TableStateReportError(
            "the seat a residual refusal names is pinned only on a pot where a second seat holds"
            " a different amount of money its own actions do not explain, and of the"
            f" {named} pots refused as holding forced money of no named kind,"
            f" {distinguishing} are such a pot"
        )


# --------------------------------------------------------------------------- #
# The blind structure, which nothing anywhere checks
# --------------------------------------------------------------------------- #

# The structures this measurement runs over: the one the committed chart was solved at, and the
# three a live or home game is actually dealt at. Chips at a hundred to the dollar.
BLIND_STRUCTURES = (
    ("$0.50/$1", SMALL_BLIND, BIG_BLIND),
    ("$1/$3", 100, 300),
    ("$2/$5", 200, 500),
    ("$5/$5", 500, 500),
)
RANKS = "AKQJT98765432"


def canonical_holdings() -> tuple[tuple[str, str], ...]:
    """One holding per canonical preflop hand class: 13 pairs, 78 suited, 78 offsuit."""
    holdings: list[tuple[str, str]] = []
    for index, high in enumerate(RANKS):
        holdings.append((high + "s", high + "h"))
        for low in RANKS[index + 1 :]:
            holdings.append((high + "s", low + "s"))
            holdings.append((high + "s", low + "h"))
    return tuple(holdings)


def small_blind_with_the_pot_folded_to_it(
    small_blind: int, big_blind: int, hole_cards: tuple[str, str]
) -> StrategyQuery:
    """Hero in the small blind with the pot folded to it, at whatever blinds are handed in.

    Built here rather than through `table`, which is fixed at the 50/100 the rest of this report
    uses, and the whole of this measurement is what happens when that moves. Everything a spot
    key is made of is held still: six seats, every one of them a hundred big blinds deep, hero
    in the small blind, no recorded raise. Only the ratio between the two blinds changes, and
    with it the price hero is being offered.

    Authored as the small blind facing a 2.5bb button open, which the chart cutover retired -
    the ruled selection predicate keeps a spot only where the source prices every terminal
    below it, and `t6/d100/SB/BTN:raise@2.5` is one of the fourteen spots it gives up. The pot
    folded to the small blind replaces it, and it is a better probe rather than merely a
    surviving one. The blind ratio can only reach hero's price where the chips hero already has
    in the pot ARE the small blind, and that is true at exactly one committed spot: this one.
    Anywhere hero has raised, hero's contribution is the raise and the ratio has stopped
    mattering to the price, so the demonstration would have been measuring nothing.

    The price is derived rather than stated, and at equal blinds it is zero, which is why the
    legal actions are derived with it: a seat that owes nothing checks and does not call.
    """
    sat_down = 100 * big_blind
    hero_seat = seat_of("SB")
    paid = {hero_seat: small_blind, seat_of("BB"): big_blind}
    folded_seats = {seat_of(name) for name in ("LJ", "HJ", "CO", "BTN")}
    to_call = big_blind - small_blind
    return StrategyQuery(
        hand_id="blind-structure",
        street="preflop",
        seat=hero_seat,
        button_seat=BUTTON,
        hole_cards=hole_cards,
        board=(),
        legal_actions=("fold", "call", "raise") if to_call else ("check", "raise"),
        to_call=to_call,
        current_bet=big_blind,
        # Nothing has raised, so the standing minimum increment is one big blind.
        min_raise_target=2 * big_blind,
        pot=sum(paid.values()),
        stacks=tuple((seat, sat_down - paid.get(seat, 0)) for seat in SEATS),
        seat_states=tuple(
            SeatState(
                seat=seat,
                street_bet=paid.get(seat, 0),
                committed_total=paid.get(seat, 0),
                folded=seat in folded_seats,
                all_in=False,
            )
            for seat in SEATS
        ),
        blinds=(small_blind, big_blind),
        preflop_actions=(
            dropped("LJ"),
            dropped("HJ"),
            dropped("CO"),
            dropped("BTN"),
        ),
    )


def blind_structure_rows(
    strategy: PreflopChartStrategy,
) -> tuple[tuple[str, StrategyQuery, int, str], ...]:
    """One row per blind structure: the table, and how many of the 169 hand classes move.

    The claim being measured is that the committed artifact declares a table size and a stack
    depth and does NOT declare a blind structure, and that nothing anywhere compares the small
    blind against half the big one - so four games offering hero four different prices reach one
    cell and come back with one answer. Measured over every canonical hand class rather than a
    sample, because "no weight responds" is the whole claim and one hand that did would refute it.

    Refused rather than published if it stops holding, both ways round. Every structure has to
    still reach a chart cell, or the demonstration is about a refusal instead; the prices have to
    genuinely differ, or the rows prove nothing; and if any weight ever does respond, this
    section is describing a defect that has been fixed and has to be rewritten rather than
    reprinted.
    """
    holdings = canonical_holdings()
    if len(holdings) != 169:
        raise TableStateReportError(
            f"the canonical preflop hand classes number 169 and this enumeration holds"
            f" {len(holdings)}"
        )
    rows: list[tuple[str, StrategyQuery, int, str]] = []
    baseline: dict[tuple[str, str], object] | None = None
    for label, small_blind, big_blind in BLIND_STRUCTURES:
        answers = {
            cards: strategy.weights_for(
                small_blind_with_the_pot_folded_to_it(small_blind, big_blind, cards)
            )
            for cards in holdings
        }
        query = small_blind_with_the_pot_folded_to_it(small_blind, big_blind, holdings[0])
        found = strategy.chart_lookup(query)
        if not isinstance(found, ChartHit):
            raise TableStateReportError(
                f"{label} no longer reaches a chart cell at all, so this section is measuring a"
                f" refusal rather than an answer: the lookup came back {found}"
            )
        differing = 0 if baseline is None else sum(1 for c in holdings if answers[c] != baseline[c])
        if differing:
            raise TableStateReportError(
                f"{differing} of {len(holdings)} hand classes now answer differently at {label}"
                " than at the structure the chart was solved for, so the blind ratio is read"
                " somewhere and this section is describing a defect that is fixed"
            )
        baseline = answers if baseline is None else baseline
        rows.append((label, query, differing, found.spot_key))
    if len({row[3] for row in rows}) != 1:
        raise TableStateReportError(
            "the four blind structures no longer reach one spot key, so something distinguishes"
            f" them: {sorted({row[3] for row in rows})}"
        )
    if len({Fraction(row[1].to_call, row[1].blinds[1]) for row in rows}) != len(rows):
        raise TableStateReportError(
            "two of the blind structures offer hero the same price in big blinds, so the rows"
            " below do not show four different games reaching one cell"
        )
    return tuple(rows)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

SEAT_HEADER = (
    f"  {'seat':<6}{'position':<10}{'sat down with':>14}{'put in, street':>15}"
    f"{'put in, hand':>14}{'holds now':>11}{'status':>9}"
)


def seat_table(query: StrategyQuery) -> list[str]:
    """One table state written out seat by seat, so the pot reconciliation is legible."""
    seats = tuple(seat for seat, _ in query.stacks)
    stacks = dict(query.stacks)
    lines = [SEAT_HEADER, "  " + "-" * (len(SEAT_HEADER) - 2)]
    for state in query.seat_states:
        status = "folded" if state.folded else ("all-in" if state.all_in else "live")
        lines.append(
            f"  {state.seat:<6}"
            f"{position_for_seat(seats, query.button_seat, state.seat):<10}"
            f"{measures.seat_start(query, state.seat):>14}"
            f"{state.street_bet:>15}{state.committed_total:>14}"
            f"{stacks[state.seat]:>11}{status:>9}"
        )
    total = sum(state.committed_total for state in query.seat_states)
    lines.append("  " + "-" * (len(SEAT_HEADER) - 2))
    lines.append(f"  {'in the pot':<16}{'':>14}{'':>15}{total:>14}")
    lines.append("")
    lines.extend(
        wrapped(
            f"Chips in equal chips out: the seats put in {total} and the pot says {query.pot}."
            " A query whose stated pot is not the sum of the hand figures above is rejected"
            " rather than answered, folded seats included, because a folded seat's chips are"
            " in the pot and dropping them is how a pot stops reconciling.",
            "  ",
        )
    )
    return lines


def header_lines(strategy: PreflopChartStrategy) -> list[str]:
    return [
        "Table-state fidelity report",
        "===========================",
        "",
        f"Strategy: {strategy.strategy_id} v{strategy.strategy_version}",
        f"Charts: {strategy.library.artifacts[0].source.name}",
        "Command: generate_table_state_report",
        "",
        *wrapped(
            "What changed. The decision context handed to the strategy used to say what the pot"
            " was, what each seat held, and what hero had to pay - and not what any seat had"
            " put in. Nobody's own contribution was recoverable, hero's included, so hero's"
            " stack depth was worked back out of the price hero was being offered. That was"
            " exact until the price was capped at what hero can actually pay, and wrong"
            " afterwards for every hero whose whole stack is the price. The query now carries,"
            " for every seat, what it has put in on this street and over the hand, and whether"
            " it has folded or is all-in."
        ),
        "",
        *wrapped(
            "What that buys, in one sentence: a table whose STACK DEPTHS or whose FORCED MONEY"
            " this bot's charts cannot describe is now seen and refused for what it is, rather"
            " than answered as something else. It buys no new answers. A short opponent, a deep"
            " opponent, a straddle and an ante each get their own refusal, because they are"
            " different tables and a chart solved for six flat hundred-big-blind stacks is not"
            " solved for any of them."
        ),
        "",
        *wrapped(
            "That sentence names the two things this phase looks at rather than claiming the"
            " table as a whole, because two classes of table escape it and are still answered as"
            " something else. A straddled pot with two or more recorded raises is invisible to"
            " every signal here. And the ratio between the two blinds is compared with nothing at"
            " all: the committed artifact declares the structure it was solved at, and no code"
            " path reads it, so $1/$3 and $2/$5 - the structures this bot's own home games are"
            " dealt at - reach the same cells as 50/100 and come back with the same weights, at"
            " prices to call tens of points of pot odds apart. The closing section measures both,"
            " and this command re-measures each of them before it will print either."
        ),
        "",
        *wrapped(
            "What would make this command fail rather than print. Hero's depth is re-derived"
            " here from hero's own recorded contribution and compared against the depth the"
            " strategy acted on, and they have to agree on a table where taking the depth from"
            " the price would give a different answer. The straddle census is reconciled"
            " against the minimum raise the two declared blinds predict, and a pot whose"
            " minimum raise disagrees with that prediction has to be counted as straddled. Every"
            " pot the deleted arithmetic bound refused has to come out of the replacement as"
            " holding forced money of some kind, and a refusal that names a seat has to name the"
            " seat the seat states say it should - both recomputed here rather than asked of the"
            " rule that chose them. The corpus figures are checked against what they were before"
            " this phase. Any of those failing exits non-zero and writes nothing."
        ),
    ]


def before_and_after_lines(strategy: PreflopChartStrategy, query: StrategyQuery) -> list[str]:
    stacks = dict(query.stacks)
    hero = next(state for state in query.seat_states if state.seat == query.seat)
    return [
        "## One table state, before and after",
        "",
        *wrapped(
            "A six-handed 50/100 game. Everyone sat down with 10,000 chips, which is a hundred"
            " big blinds. Hero is the lojack and opened to 250; the hijack and the button"
            " folded; the cutoff three-bet to 800; hero is deciding. This is a construction,"
            " not a hand out of any file."
        ),
        "",
        "What the strategy used to be told about it:",
        "",
        f"    the pot                    {query.pot}",
        f"    the bet level              {query.current_bet}",
        f"    hero's price to call       {query.to_call}",
        "    what each seat holds       "
        + ", ".join(f"{seat}:{stack}" for seat, stack in query.stacks),
        "    what each seat put in      (nothing said)",
        "",
        *wrapped(
            "Hero's own 250 is not in that list. It had to be recovered from the price hero was"
            " being offered, and every other seat's contribution was simply unavailable. A seat"
            " holding 9,200 was indistinguishable from a seat that had bought in for 9,200, so"
            " the cutoff's three-bet and a genuinely short opponent looked the same."
        ),
        "",
        "What it is told now, seat by seat:",
        "",
        *seat_table(query),
        "",
        *wrapped(
            f"Hero's depth is now read rather than reconstructed: hero holds"
            f" {stacks[query.seat]} and its own record says it put in {hero.street_bet}, so hero"
            f" sat down with {measures.hero_start(query)}, which is"
            f" {measures.depth_text(measures.hero_start(query), BIG_BLIND)} big blinds. Every"
            " other seat is recomputed the same way, so the cutoff shows as a 100bb seat that"
            " has invested rather than as a 92bb seat."
        ),
        "",
        f"  the chart's answer:  {outcome_line(strategy, query)}",
        "",
        *wrapped(
            "The table is flat, hero's depth is a whole number of big blinds, the committed"
            " chart holds the cell, and the answer is capped at what hero can actually raise"
            " to: hero's own 250 plus the 9,750 behind it."
        ),
    ]


def depth_lines(
    strategy: PreflopChartStrategy, probes: Sequence[tuple[DepthProbe, str]]
) -> list[str]:
    lines = [
        "## The depth the chart derived against the depth that is true",
        "",
        *wrapped(
            "Hero's stack depth decides which chart is consulted, so a wrong depth is not a"
            " wrong label - it is an answer taken from a different game. The column marked"
            " 'true' is hero's own record: what hero holds plus what hero put in. The column"
            " marked 'from the price' is the number the pre-phase derivation returned for a"
            " hero whose whole stack is the price to call, which is the bet level itself. Where"
            " those two differ, everything the chart said rested on the wrong one."
        ),
        "",
    ]
    for probe, note in probes:
        query = probe.query
        _, big_blind = query.blinds
        true_depth = measures.depth_text(measures.hero_start(query), big_blind)
        from_price = (
            f"{measures.level_as_depth(query)}bb" if probe.diverges else f"{true_depth}bb, agreeing"
        )
        lines.append(f"  {probe.label}")
        lines.append(
            f"    hero sat down with {measures.hero_start(query)} at blinds of"
            f" {query.blinds[0]}/{big_blind}"
        )
        lines.append(f"    {'depth, true':<28}{true_depth}bb")
        lines.append(f"    {'depth, taken from the price':<28}{from_price}")
        lines.append(f"    {'the table shape':<28}{measures.independent_depth_verdict(query)}")
        lines.append(f"    {'the chart answered':<28}{outcome_line(strategy, query)}")
        lines.extend(wrapped(note, "    "))
        lines.append("")
    lines.extend(
        wrapped(
            "Every row above was checked before it was printed: the shape the contributions"
            " imply is the shape the strategy acted on, and no refusal names hero as deeper or"
            " shorter than hero. At least one row has to be a hero whose whole stack is the"
            " price and whose true depth is not the bet level, or the check could not fail and"
            " the report would be decoration. The seat each depth refusal names is checked too,"
            " against the extreme live seat recomputed from the seat states rather than taken"
            " from either copy of the selection rule - and because two copies that agree with"
            " each other prove nothing about which seat is right, a row where the extreme seat"
            " is not the first one in seat order has to exist in each direction, or that check"
            " could not fail either. The 90bb-and-20bb row above supplies the shorter"
            " direction; `phase02-three-way-side-pot`, further down, supplies the deeper one"
            " from its 50-chip chair."
        )
    )
    return lines


def straddle_lines(
    strategy: PreflopChartStrategy, query: StrategyQuery, control: StrategyQuery
) -> list[str]:
    offered = query.min_raise_target
    predicted = measures.StraddleProbe("", STRADDLED, query).min_raise_pair[1]
    return [
        "## The straddled pot that used to slip through the deleted bound",
        "",
        *wrapped(
            "50/100 with a 200 straddle. The cutoff opened to 600, the straddler and the big"
            " blind called, the small blind folded, and the button is deciding. This is the"
            " pot named in `PER-SEAT-CONTRIBUTIONS-IN-QUERY`, and it is common in the home"
            " games this bot is pointed at."
        ),
        "",
        *seat_table(query),
        "",
        *wrapped(
            "The rule this phase deleted worked out the largest pot two blinds and the recorded"
            " actions could explain, and refused anything bigger. Its number here:"
        ),
        "",
        f"    the deleted bound allowed   {deleted_bound(query)}",
        f"    this pot is                 {query.pot}",
        f"    so the old rule             {bound_verdict(query)}",
        "",
        *wrapped(
            "The money cannot give it away either. An unstraddled pot at the same price"
            " produces the same 50/600/600/600, so per-seat contributions do not help here and"
            " the straddler, having already called to the level, holds exactly what an ordinary"
            " caller holds. What differs is the price of a re-raise:"
        ),
        "",
        f"    the table offers a minimum raise to      {offered}",
        f"    two blinds and a raise to 600 predict    {predicted}",
        f"    the gap                                  {abs((predicted or 0) - offered)}",
        "",
        *wrapped(
            "The gap is the straddle less the big blind, because the opener's raise was measured"
            " from the 200 in front of it rather than from the 100 the format declares. That"
            " gap is the only trace the straddle leaves, and it is what this pot is now refused"
            " on:"
        ),
        "",
        f"  the chart's answer:  {outcome_line(strategy, query)}",
        "",
        "### The whole signal is one field a producer supplies, and that cuts both ways",
        "",
        *wrapped(
            "Because the trace is the minimum raise and nothing else, the answer here depends"
            " entirely on one number whoever built the query put in it. That is the sharpest"
            " false-positive channel this phase opens, so it is demonstrated rather than"
            " described. The two tables below are the same table - the same six seats, the same"
            " 50/600/600/600 contributions, the same 600 level, the same recorded history, the"
            " same everything - except for `min_raise_target`:"
        ),
        "",
        f"    min_raise_target {query.min_raise_target}   {outcome_line(strategy, query)}",
        f"    min_raise_target {control.min_raise_target}   {outcome_line(strategy, control)}",
        "",
        *wrapped(
            f"{control.min_raise_target} is what two declared blinds and a recorded raise to 600"
            f" predict; {query.min_raise_target} is what a table with a 200 straddle in it"
            " actually offers. One field moves and the strategy stops saying anything about"
            " forced money at all. So a producer that computes that field carelessly makes the"
            " strategy state something false about the game: wrong in one direction it announces"
            " a straddle in a pot that holds none, wrong in the other it misses the straddle"
            " that is there, and nothing downstream can tell either from the truth, because the"
            " field *is* the evidence. That is why `predicted_min_raise_target` mirrors the"
            " engine's own walk line for line rather than approximating it, and why the"
            " under-raise table further down states the 450 this repo's engine offers rather"
            " than the 400 an approximation gives: an earlier draft of the signal predicted 350"
            " against the engine's 450 and refused that pot as holding a straddle, which is a"
            " false statement about a pot where a short stack simply shoved."
        ),
    ]


def census_lines(
    strategy: PreflopChartStrategy, probes: Sequence[tuple[StraddleProbe, str]]
) -> list[str]:
    counts = measures.census_counts(strategy, [probe for probe, _ in probes])
    lines = [
        "## The straddle census, reconciled against the minimum raise",
        "",
        *wrapped(
            f"{len(probes)} constructed pots, each with what is truly in it stated first and what"
            " the three signals made of it second. The reconciliation is one rule: a pot whose"
            " minimum raise disagrees with what the declared blinds and the recorded raises"
            " predict is straddled, and has to be counted as straddled. It is checked in both"
            " directions, because a detector that called every pot straddled would satisfy half"
            " of it by itself."
        ),
        "",
        *wrapped(
            "The row marked `the old bound` is the arithmetic rule this phase deleted, run again"
            " on the same pot. It is printed beside the replacement's answer because a reader"
            " needs to see that the replacement did not lose what the bound covered, and it is"
            " compared rather than merely printed: every pot the bound refused has to come out"
            " of the replacement as holding forced money of some kind, or this command exits"
            " non-zero. That is narrower than the contract's criterion, which is about every pot"
            " and rests on a frozen test; what it adds is that these rows cannot quietly stop"
            " supporting the sentence they are printed under."
        ),
        "",
    ]
    for probe, note in probes:
        offered, predicted = probe.min_raise_pair
        prediction = "no raise yet, so no prediction" if predicted is None else str(predicted)
        lines.append(f"  {probe.label}")
        lines.append(f"    what is truly in it     {probe.truth}")
        verdict = measures.forced_money_verdict(strategy, probe.query)
        lines.append(f"    what the signals said   {verdict}")
        lines.append(f"    minimum raise offered   {offered}")
        lines.append(f"    minimum raise predicted {prediction}")
        lines.append(f"    the old bound           {bound_verdict(probe.query)}")
        lines.append(f"    the chart's answer      {outcome_line(strategy, probe.query)}")
        lines.extend(wrapped(note, "    "))
        lines.append("")
    lines.append("  the census")
    for name in (STRADDLED, ANTED, RESIDUAL, CLEAN):
        truly = sum(1 for probe, _ in probes if probe.truth == name)
        lines.append(f"    {name:<48}counted {counts[name]:>2}   truly {truly:>2}")
    invisible = sum(1 for probe, _ in probes if probe.truth == INVISIBLE)
    lines.append(f"    {INVISIBLE:<48}counted {counts[INVISIBLE]:>2}   truly {invisible:>2}")
    lines.append("")
    lines.extend(
        wrapped(
            f"The four counted classes account for all {len(probes)} pots, and the straddle count"
            " equals the number of pots holding a straddle the signals can see. The absorbed"
            " straddle is one of them, and it is counted through a minimum raise that disagrees"
            " with the prediction: that is the assertion this command exits non-zero on."
        )
    )
    lines.append("")
    lines.extend(
        wrapped(
            "One row deliberately does not match, and the difference is part of what is still"
            f" missed: {counts[CLEAN]} pots are counted as holding no forced money where only"
            f" {sum(1 for probe, _ in probes if probe.truth == CLEAN)} hold"
            " none. The odd one out is the big-blind-sized straddle, which is counted clean"
            " because"
            " nothing in the money, the level or the minimum raise distinguishes it from a limp."
            " It is printed as a straddle in the truth column so that the gap is a number rather"
            " than a sentence. Both figures on the last row are read off the same tally as every"
            " row above rather than written in: the detector has no such class to return, so its"
            " count is zero, and this command exits non-zero unless every pot in that row is"
            " counted as holding no forced money at all. The row is the smaller of the two"
            " residuals; the larger one is in the closing section and no probe here can carry it."
        )
    )
    lines.append("")
    lines.extend(
        wrapped(
            "One more thing above is checked rather than printed. Where a refusal names a seat -"
            " the two rows holding a dead blind - the seat it names is recomputed here from the"
            " contributions, not asked of the rule that chose it, and it has to be the seat"
            " holding the most chips its own actions do not explain, ties to the lowest chair."
            " A rule that simply named the lowest chair would agree on every pot with one such"
            " seat, so a row where the two answers differ has to exist or that check could not"
            " fail either. The two-dead-blinds row is it: the most forced chips are in seat 1 and"
            " the lowest chair holding any is seat 0."
        )
    )
    return lines


def corpus_lines(counts: CorpusCounts) -> list[str]:
    lines = [
        "## The corpus counts, as a checked regression proof",
        "",
        *wrapped(
            "All 499 committed corpus hands are six seats at 10,000 chips, with no ante and"
            " blinds of exactly 50 and 100. Not one unequal stack, not one straddle, not one"
            " ante. So every table-shape count below is zero before anything is measured, and"
            " it is printed rather than omitted for one reason: a number here that moves is a"
            " defect, not a discovery."
        ),
        "",
        f"  hands compared                     {counts.hands}",
        f"  preflop decision points            {counts.decisions}",
        f"  refusals                           {counts.refusals}",
        "",
    ]
    for code in TABLE_SHAPE_CODES:
        lines.append(f"  {code:<52}{counts.count(code):>5}")
    lines.append("")
    lines.extend(
        wrapped(
            "The refusals the corpus does produce are all about chart coverage rather than"
            " table shape, and they are unchanged by this phase:"
        )
    )
    lines.append("")
    for code, count in counts.by_code:
        lines.append(f"  {code:<52}{count:>5}")
    lines.append("")
    lines.extend(
        wrapped(
            f"One live corpus number is worth reading twice. {counts.capped} of"
            f" {counts.decisions} decisions price hero at its whole stack, which is the"
            " population the capped-price ruling is about and the population the deleted depth"
            f" derivation was wrong for. In {counts.capped_diverging} of them does the bet level"
            " differ from what hero sat down with - because every corpus seat starts with"
            " exactly 100bb, so a shove can never be for more than hero itself started with."
            " The corpus therefore has the population and cannot exercise the defect, which is"
            " why the divergence above is constructed."
        )
    )
    return lines


def moving_fixture_lines(
    strategy: PreflopChartStrategy, probes: Sequence[DepthProbe]
) -> list[str]:
    lines = [
        "## The one committed fixture that moves",
        "",
        *wrapped(
            "`data/samples/normalized_hands.json` holds `phase02-three-way-side-pot`: three"
            " seats with 50, 100 and 200 chips at blinds of 5 and 10. The button shoved 200,"
            " the 50-chip seat called all-in, the 100-chip seat called all-in. This is the only"
            " committed hand where the shorter-seat rule has anything to bite on, and it is the"
            " phase's only live evidence that the rule fires at all."
        ),
        "",
        *wrapped(
            "Before this phase all three of its preflop decisions refused with"
            f" `{measures.BEFORE_MOVING_CODE}`. Hero's depth came out as 20bb at every one of"
            " them, and the flat-table test compared what each seat *held* against that, so a"
            " seat holding less was invisible and the table read as flat. The refusal then came"
            " from there being no three-handed chart, which is true and is not what is wrong"
            " with the table."
        ),
        "",
    ]
    for probe in probes:
        query = probe.query
        _, big_blind = query.blinds
        lines.append(f"  {probe.label}")
        lines.append("")
        lines.extend(seat_table(query))
        lines.append("")
        lines.append(f"    hero's depth, true      "
                     f"{measures.depth_text(measures.hero_start(query), big_blind)}bb")
        lines.append(f"    before this phase       {probe.before_code}")
        lines.append(f"    now                     {outcome_line(strategy, query)}")
        lines.append("")
    lines.extend(
        wrapped(
            "All three decisions change code, and the deep seat takes the new shorter-live-seat"
            " code: from the button's chair two live seats are genuinely shorter, and from the"
            " two short chairs a live seat is genuinely deeper. This hand is also the committed"
            " evidence that a depth refusal names the extreme offending seat rather than the"
            " first one it meets. From the 50-chip chair two live seats are deeper, holding 100"
            " and 200, and the seat reported is the 200 - the deepest - so this row would read"
            " 10bb rather than 20bb under a rule that stopped at the first offender in seat"
            " order. It is the only row in COMMITTED DATA where the two rules differ, and it"
            " covers the deeper direction only; the shorter direction is pinned by the"
            " constructed 90bb-and-20bb probe in the depth section above, which is why the"
            " validator demands a distinguishing row in each direction rather than one. The"
            " committed"
            " postflop fallback report is regenerated with these codes rather than hand-edited,"
            " and the decision"
            " record's estimate that two of the three would move is corrected here to three."
        )
    )
    return lines


def recomputable_lines(query: StrategyQuery, addends: tuple[int, ...]) -> list[str]:
    return [
        "## A number in this report you can recompute by hand",
        "",
        *wrapped(
            f"The pot of {query.pot} printed above for seat {query.seat} of"
            f" `{measures.MOVING_FIXTURE_HAND}` comes out of the file itself, and the arithmetic"
            " is four numbers long."
        ),
        "",
        "  1. Open `data/samples/normalized_hands.json`.",
        f"  2. Find the hand whose `hand_id` is `{measures.MOVING_FIXTURE_HAND}`.",
        *wrapped(
            f"3. In its `preflop` street, read the `amount` of every action listed before seat"
            f" {query.seat}'s own `call`.",
            "  ",
        ),
        *wrapped(
            "4. A blind post and a raise record the total that seat then has in front of it; a"
            " call records what that seat added. Add them:",
            "  ",
        ),
        "",
        f"       {' + '.join(str(number) for number in addends)} = {sum(addends)}",
        "",
        *wrapped(
            "That is the pot this report prints for that decision, and this command checks the"
            " addition against the replayed query before writing anything: the file and the"
            " replay have to agree."
        ),
    ]


def handoff_lines(
    strategy: PreflopChartStrategy, counts: CorpusCounts
) -> list[str]:
    under_raise = under_raise_table()
    short_raise = short_all_in_raise_table()
    full_call = full_call_table()
    short_call = short_all_in_call_table()
    under_key = one_key_two_tables(strategy, under_raise, short_raise)
    call_key = one_key_two_tables(strategy, full_call, short_call)
    return [
        "## The two findings Phase 12 handed on, measured",
        "",
        "### A spot key admits a re-raise no legal action produces",
        "",
        *wrapped(
            "Over a 2.5bb open the smallest legal re-raise is 4bb: the level plus the larger of"
            " the previous increment and one big blind. A re-raise to 3bb is not a legal action"
            " and the key space writes it down anyway - and writes the same string for a button"
            " that was simply all-in for 300, which is legal and is a different table:"
        ),
        "",
        f"    the key the lookup asked about   {under_key}",
        "",
        *wrapped(
            "That string is read off the lookup the under-raise table actually reached rather"
            " than composed here, and only one of the two tables ever reaches one. The button"
            " all-in for 300 sat down with 300, which is three big blinds against hero's hundred,"
            " so that table is not one flat depth and it is refused before any key is built:"
        ),
        "",
        f"    the recorded under-raise   {outcome_line(strategy, under_raise)}",
        f"    the short all-in for 300   {outcome_line(strategy, short_raise)}",
        "",
        *wrapped(
            "So the merge lives in the key space and not in what this strategy does with these"
            " two tables, and the difference is worth stating rather than eliding: a claim that"
            " both tables render one key would be false of the second, which renders nothing."
            " This command refuses to publish that key unless the two tables still agree on every"
            " one of the four things a key is made of, the first still reaches the chart, and the"
            " second is still refused for holding a live seat shorter than hero."
        ),
        "",
        *wrapped(
            "Does the query's new state close the under-raise itself? Not in the key, and not in"
            " the query either. The recorded raise-to amounts and the two declared blinds do"
            " reconstruct what the minimum raise should be, and that reconstruction now mirrors"
            " the engine exactly: the minimum starts at the big blind and a recorded raise moves"
            " it only when its increment is at least the minimum already standing. An incomplete"
            " raise therefore predicts the same 450 the engine offers, so nothing about it"
            " disagrees and nothing about it is refused as forced money. Its refusal above is a"
            " chart-coverage miss and nothing more, which is what this table honestly is."
        ),
        "",
        *wrapped(
            "An earlier"
            " draft of the straddle signal walked the raises with no floor on the increment, so"
            " it predicted 350 against the engine's 450 and refused this pot as holding a"
            " straddle - a false statement about the game, in a pot where a short stack simply"
            " shoved. Flooring the walk removes that and hides no straddle, because a straddle"
            " perturbs only the first increment and that increment is always a full raise. What"
            " remains is that an under-raise is now fail-closed only by coverage: this cell"
            " happens to be unsolved, and nothing here refuses the price for being illegal."
        ),
        "",
        *wrapped(
            f"What it costs on committed data: {counts.under_raises} of the"
            f" {counts.facing_a_raise} corpus decisions that face a raise carry a recorded raise"
            " below the legal minimum, out of"
            f" {counts.decisions} decisions in all. Every raise in the corpus is a full legal"
            " raise, so the permissive key space costs nothing measurable today and stays"
            " structurally open."
        ),
        "",
        *wrapped(
            "What a key would have to carry to close it: a marker on each raise entry saying"
            " whether it was a legal full raise or an all-in for less. Without that, an"
            " under-raise and a short all-in render one string, and any cell filled from that"
            " string mixes two prices. That is a spot-key format change, which this phase is"
            " scoped out of, and it is filed rather than done."
        ),
        "",
        "### A call entry carries no record of being all-in for less",
        "",
        *wrapped(
            "Two different tables at the same price: on one the button called the full 250 out"
            " of a hundred big blinds, on the other it was all-in for 120. Their recorded"
            " histories are identical - fold, fold, a raise to 250, a call - and so is every"
            " other thing a spot key is made of, so the vocabulary has one string for both:"
        ),
        "",
        f"    the key the lookup asked about   {call_key}",
        "",
        *wrapped(
            "One of the two renders it, and that is this finding closing rather than the"
            " demonstration failing. The full call reaches the chart and the lookup asks about"
            " that key. The short all-in does not get that far: a seat all-in for less than the"
            " level has, by definition, put in everything it sat down with, so it is a shorter"
            " seat, and the table is no longer flat."
        ),
        "",
        f"    the full call        {outcome_line(strategy, full_call)}",
        f"    the short all-in     {outcome_line(strategy, short_call)}",
        "",
        *wrapped(
            "Those two lines are not two answers to one question, which is the whole of what the"
            " query bought here. The first is a chart-coverage refusal and names the cell nobody"
            " has solved. The second names a seat and the depth it holds, and is reached before"
            " any key exists at all. So a live query carrying a short all-in call never renders"
            " that key, and the two tables cannot be answered from one cell any more. What"
            " remains open is the key space itself: anything that works from keys rather than"
            " from a table - a committed artifact, a self-play enumeration, `decide_spot` -"
            " still merges them, and there the merge is total, because nothing in a key says how"
            " deep the caller was."
            f" On committed data that costs {counts.short_all_in_calls} of the"
            f" {counts.with_a_recorded_call} corpus decisions whose history holds a call."
        ),
        "",
        *wrapped(
            "That zero is weaker than it reads, and the weaker reading is the true one. It says"
            " no corpus call is tagged all-in at all - not that every corpus all-in is for the"
            " exact level, which is the claim this paragraph used to end on. The count asks two"
            " things of a recorded call, that the seat is marked all-in and that its street"
            " figure is below the level, and only the first is doing any work: measured over the"
            " corpus, none of the 183 recorded call entries comes from a seat the record marks"
            " all-in, and the whole corpus carries 10 all-in seat-states across 18,288."
            " Loosening the second test from below-the-level to at-or-below-the-level leaves the"
            " count at zero, which is what it is for a check to be insensitive to its own"
            " comparison. So the zero is a fact about how the converter tags a call rather than"
            " about the sizes of anything, and a corpus that began recording all-in calls could"
            " move it whatever the levels did. The regression is still worth keeping - same"
            " shape as the table-shape zeros above, a committed number a changed replay or"
            " converter can move - but it is not the statement about levels it was written up as."
        ),
        "",
        *wrapped(
            "What a key would have to carry: the same marker, on a call. What leaving it open"
            " costs is not a wrong answer today but a wrong denominator later - the first"
            " artifact built from real hands would fill one cell from two different tables and"
            " nothing would say so."
        ),
    ]


def blind_structure_lines(strategy: PreflopChartStrategy) -> list[str]:
    """The blind ratio nothing checks, measured over every canonical hand class.

    The second of the two exceptions the report's headline sentence names, and the one this
    phase closes least: the straddle residual at least ends in a refusal for most pots, while
    this ends in an answer every time and says nothing about itself.
    """
    rows = blind_structure_rows(strategy)
    odds = {
        label: Fraction(query.to_call, query.pot + query.to_call) for label, query, _, _ in rows
    }
    ordered = sorted(rows, key=lambda row: odds[row[0]])
    cheapest, dearest = ordered[0], ordered[-1]
    swing = (odds[dearest[0]] - odds[cheapest[0]]) * 100
    header = (
        f"  {'structure':<11}{'blinds':<11}{'hero pays':>10}{'in bb':>9}"
        f"{'the pot':>9}{'in bb':>9}{'pot odds':>10}{'classes moving':>15}"
    )
    lines = [
        *wrapped(
            "**The ratio between the two blinds is compared with nothing, so four different games"
            " reach one cell and come back with one answer.** The committed artifact declares a"
            " table size, a stack depth, and - since the chart cutover - the blind structure it"
            " was solved at. Nothing reads that last one: not the chart, not the lookup, not one"
            " of the checks this phase added, and nothing compares the small blind a query"
            " carries against the half a big blind the artifact says it was solved for. Below is"
            " hero in the small blind with the pot folded to it at four structures, with"
            " everything a spot key is made of held still: six seats, every one a hundred big"
            " blinds deep, no recorded raise. That is the one committed spot where the ratio can"
            " reach hero's price at all, because it is the one where the chips hero already has"
            " in the pot are the small blind itself. The whole canonical hand class list was"
            f" asked at each, all {len(canonical_holdings())} of them, and the last column counts"
            " the ones whose weights differ from the first row's."
        ),
        "",
        header,
        "  " + "-" * (len(header) - 2),
    ]
    for index, (label, query, differing, _) in enumerate(rows):
        small_blind, big_blind = query.blinds
        moved = "baseline" if index == 0 else f"{differing} of {len(canonical_holdings())}"
        lines.append(
            f"  {label:<11}{f'{small_blind}/{big_blind}':<11}{query.to_call:>10}"
            f"{float(Fraction(query.to_call, big_blind)):>9.4f}{query.pot:>9}"
            f"{float(Fraction(query.pot, big_blind)):>9.4f}"
            f"{float(odds[label]) * 100:>9.2f}%{moved:>15}"
        )
    lines.append("")
    lines.extend(
        wrapped(
            f"The price hero is offered swings {float(swing):.1f} points of pot odds across those"
            f" rows - {float(odds[cheapest[0]]) * 100:.2f}% at {cheapest[0]} against"
            f" {float(odds[dearest[0]]) * 100:.2f}% at {dearest[0]} - because the small blind is"
            " a different fraction of the big blind in each of them, and hero is the seat that"
            " posted it. Not one hand class responds. All four ask the chart about the same key,"
            f" `{rows[0][3]}`, because a key has nowhere to write the ratio down - and the"
            " artifact behind that key does now say what ratio it was solved at, which makes this"
            " a comparison nobody performs rather than one nobody could."
        )
    )
    lines.append("")
    lines.extend(
        wrapped(
            "What that costs is not a corner case. This bot is pointed at home games, and $1/$3"
            " and $2/$5 are what home and live games are dealt at; $1/$2, the structure whose"
            " ratio matches the chart's, is the exception rather than the rule. Whether the right"
            " ranges genuinely differ between those games is a solver question this repo cannot"
            " answer from here, and this report does not claim they do. What is measured is that"
            " they cannot differ, because nothing looks: the whole spread in the table above,"
            " which would turn a marginal call into a marginal fold at the table, changes nothing"
            " here."
        )
    )
    lines.append("")
    lines.extend(
        wrapped(
            "Not fixable in this phase, and filed as"
            " `BLIND-RATIO-NEVER-CHECKED-AGAINST-THE-SOLVED-STRUCTURE`. When this section was"
            " first written, refusing on the ratio would have meant hardcoding into the code a"
            " property the artifact did not declare - the"
            " reconstruction-from-an-undeclared-source defect this phase exists to end, in a new"
            " place. Half of that has since been removed: the chart cutover put a blind structure"
            " on the artifact, so the remaining half is a comparison at lookup time against a"
            " value the file already carries, and the entry is smaller than it was rather than"
            " closed. This command re-measures the four rows before printing them: each has to"
            " still reach a chart cell, the four prices have to still differ, and if any hand"
            " class ever does answer differently the command exits non-zero, because this section"
            " would then be describing a defect that is fixed."
        )
    )
    return lines


def limitations_lines(strategy: PreflopChartStrategy) -> list[str]:
    """The closing admissions, with the headline one measured on a reachable table.

    The exception is demonstrated rather than asserted, and refused rather than published if it
    stops holding: a table the report claims is answered has to still be answered, and a table
    the report claims no signal sees has to still be seen by none of them.
    """
    invisible = invisible_straddle_table()
    found = strategy.chart_lookup(invisible)
    if not isinstance(found, ChartHit):
        raise TableStateReportError(
            "the straddled pot this report admits is answered rather than refused no longer"
            f" reaches a chart cell: the lookup came back {found}"
        )
    verdict = measures.forced_money_verdict(strategy, invisible)
    if verdict != CLEAN:
        raise TableStateReportError(
            "the straddled pot this report admits no signal can see is now seen: the census"
            f" calls it {verdict!r}, so this section is describing a defect that is fixed"
        )
    offered, predicted = measures.StraddleProbe("", STRADDLED, invisible).min_raise_pair
    weights = ", ".join(f"{name}={weight:g}" for name, weight in found.action_weights)
    substitutions = (
        ", ".join(f"{name} {value}" for name, value in found.substitution_detail()) or "nothing"
    )
    return [
        "## What this still misses, and what it costs",
        "",
        *wrapped(
            "**A straddled pot with two or more recorded raises is invisible to all three"
            " signals, and it is answered rather than refused.** This is the largest thing this"
            " phase misses and the one place the claim at the top of this report does not hold,"
            " so it is stated first. The minimum-raise signal is the only one that can see a"
            " straddle whose poster has acted, and what it compares is the minimum the table"
            " offers against the final level plus the last increment. A straddle perturbs only"
            " the FIRST increment. From the second recorded raise onward the prediction is a"
            " difference of two recorded raise-to amounts, which comes out identical whether the"
            " pot is straddled or not, so the signal fires only on single-raise pots - which is"
            " what every probe in the census above happens to be. The other two signals cannot"
            " cover it: a raiser's predicted contribution is its own raise-to amount, which"
            " absorbs any forced money that seat posted earlier, and an unraised level cannot be"
            " read once the straddler has acted."
        ),
        "",
        *wrapped(
            "What that costs is worse than a refusal under the wrong code. Such a table reaches"
            " the chart, hits a cell, and is answered with the range solved for the UNSTRADDLED"
            " spot, which is answering a straddled pot by reaching for a neighbouring cell - the"
            " thing this phase set out to stop. Below is that table, built on this code with no"
            " mutation, and built so that an ordinary betting round produces it: 50/100 with the"
            " BIG BLIND straddling to 200, the lojack and hijack folding, the cutoff opening to"
            " 500, the button and small blind folding, the big blind three-betting to 1,350, and"
            " the cutoff deciding. A straddler has to act last in the first orbit, which is where"
            " the big blind already acts, so nothing here is out of turn and no seat is asked for"
            " a decision it would never be asked for."
        ),
        "",
        *seat_table(invisible),
        "",
        *wrapped(
            "Every price is legal at that table's own minimums, and every seat holds exactly what"
            " its own actions explain, because the straddler's 200 is absorbed into the 1,350 it"
            " raised to. So reconstruction is silent, the level is not readable behind two"
            " raises, and the one signal left agrees with the table exactly:"
        ),
        "",
        f"    the table offers a minimum raise to      {offered}",
        f"    two blinds and those two raises predict  {predicted}",
        f"    the key the lookup asked about           {found.spot_key}",
        f"    what it says it had to move to get there {substitutions}",
        f"    the weights it answered from             {weights}",
        f"    the chart's answer                       {outcome_line(strategy, invisible)}",
        "",
        *wrapped(
            "Those weights are the range solved for a 2.5bb cutoff open three-bet to 13.5bb at"
            " 50/100 with nothing forced in the pot, which is a different game from the one being"
            " played. The answer's only provenance field says a price was substituted; not one"
            " field on it says the pot holds forced money, because nothing in this phase can tell"
            " that it does. The report checks both halves of that before printing them: the pot"
            " has to still reach a chart cell, and the census has to still count it as holding no"
            " forced money at all, or this command exits non-zero and the admission is out of"
            " date. Filed as `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`, and not fixable in this"
            " phase's vocabulary: once the straddler raises, the straddle's trace is genuinely"
            " destroyed, the only thing that recovers it is a declared blind structure on the"
            " query - the format change this phase is scoped out of - and any guard written"
            " without one over-refuses ordinary unstraddled tables."
        ),
        "",
        "",
        *blind_structure_lines(strategy),
        "",
        *wrapped(
            "**A straddle equal to the big blind, once its poster has acted, is invisible for a"
            " second and simpler reason.** It moves no level, it predicts exactly what a limp"
            " predicts, and it shifts no minimum raise. The census above carries it as a row and"
            " counts it as undetected rather than leaving it out. A straddle in a pot where the"
            " straddler has acted and nothing has raised is the same blind spot; it cannot happen"
            " in a legal preflop street, where the straddler acts last and its call ends the"
            " round, but it can be written as a query."
        ),
        "",
        *wrapped(
            "**A ragged hero hides every table shape behind it.** The checks fire in a ruled"
            " order - hero's own depth first, then a live seat deeper, then a live seat shorter"
            " - and the first match wins. At a real table where no stack is a whole number of"
            " big blinds, hero's own raggedness is what gets reported, so the refusal inventory"
            " will under-count asymmetric tables in exactly the games where they are commonest."
            " That is judgment call 7's accepted cost, stated here rather than fixed: reporting"
            " all findings instead of the first would change the shape of a refusal, which"
            " carries one code."
        ),
        "",
        *wrapped(
            "**Refusing on any difference at all refuses almost every real table.** A live"
            " opponent whose starting stack differs from hero's by one chip is enough. That was"
            " ruled deliberately on 2026-08-21, on the reading that the alternatives need a"
            " tolerance nobody in this repo can derive yet, and the refusal names the seat and"
            " the depth it holds so that whoever re-rules it has data to do it with. Which seat"
            " is chosen is chosen for that reader: the shortest live seat when one is shorter,"
            " because the shortest live stack caps hero's effective one and is the number a"
            " tolerance would have to be set against - a 90bb opponent is still 100bb poker and"
            " a 20bb opponent is a different game. Reporting whichever offending seat came"
            " first in seat order instead made the recorded depth depend on the seating."
        ),
        "",
        *wrapped(
            "**Where a pot in this report is a construction rather than data.** Every table in"
            " this report except the `phase02-three-way-side-pot` section is constructed here to"
            " make one claim legible; none of them is read off a committed file. Separately, the"
            " postflop fallback report's enumeration now attributes its hundred otherwise"
            " unowned chips to villain's earlier street, so its pot is a claim about how the"
            " hand got here rather than a measurement - a reviewer reading it as data would be"
            " misled, and that report says so too."
        ),
    ]


def render() -> str:
    strategy = PreflopChartStrategy.from_repo()
    before_after = three_bet_table()
    depth = depth_probes(strategy)
    census = straddle_probes()
    moving = moving_fixture_probes()
    corpus = measures.measure_corpus(strategy)
    validate(
        strategy,
        [probe for probe, _ in depth] + list(moving),
        [probe for probe, _ in census],
        corpus,
    )
    # Two checks on the census that `checks` does not make: that the deleted bound's column
    # supports the sentence it is printed under, and that a residual refusal names the seat
    # holding the most unexplained chips rather than the lowest chair.
    validate_bound_coverage(strategy, census)
    validate_residual_seat(strategy, census)
    absorbed = absorbed_straddle_table()
    if absorbed.pot >= deleted_bound(absorbed):
        raise TableStateReportError(
            f"the absorbed straddle's pot of {absorbed.pot} is not under the deleted bound of"
            f" {deleted_bound(absorbed)}, so it is not the pot that slipped through it"
        )
    addends = measures.recomputed_pot(moving[-1].query)
    sections = [
        header_lines(strategy),
        before_and_after_lines(strategy, before_after),
        depth_lines(strategy, depth),
        straddle_lines(strategy, absorbed, unstraddled_control()),
        census_lines(strategy, census),
        corpus_lines(corpus),
        moving_fixture_lines(strategy, moving),
        recomputable_lines(moving[-1].query, addends),
        handoff_lines(strategy, corpus),
        limitations_lines(strategy),
    ]
    body = "\n\n".join("\n".join(section) for section in sections)
    return "\n".join(line.rstrip() for line in body.splitlines()) + "\n"


def main() -> int:
    try:
        text = render()
    except TableStateReportError as error:
        # The report is evidence, so a figure it cannot stand behind is a failed command
        # rather than a caveat inside a file that still gets written.
        print(f"table-state report refused to publish: {error}", file=sys.stderr)
        return 1
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
