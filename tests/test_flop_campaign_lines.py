"""Phase 21, stage 4: part 3's lines - which ones, in what order, and whose range is whose.

Authored from the contract before any implementation exists; see the head of
`tests/test_flop_campaign_threads.py` for how the missing modules are reached.

**Every range here comes out of the committed chart**,
`data/artifacts/preflop/six_max_100bb_rakefree.json`, and the expected values are derived in this
file from that chart's own `action_weights` and `arrival_ppb`, floored class-level at
`RANGE_WEIGHT_FLOOR` the way phase 16 floored the committed ranges. The one oracle outside the
chart is the committed `solve_config.json`, which is what the driver solved the button's line on:
the new function has to give back exactly those two ranges for that line.

**The seat rule is the point.** GTOpen has two seats, out of position and in position, and the
driver hardcodes the big blind out of position because every flop phase 16 solved was a button
open. Against the small blind that is backwards: the small blind raises and then acts first on
every street after the flop, so the raiser is out of position.
"""

from __future__ import annotations

import inspect
import json

import pytest

from poker_training_bot.solver_artifacts import postflop_artifact as artifact
from poker_training_bot.solver_artifacts import postflop_key as key
from poker_training_bot.solver_artifacts import postflop_solve_driver as driver
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy import postflop_betting as betting
from scripts.repo_paths import REPO_ROOT
from tests.test_postflop_betting import BUTTON_SEAT
from tests.test_postflop_betting import HERO_SEAT as BIG_BLIND_SEAT
from tests.test_postflop_betting import query as button_line_query

CHART_PATH = REPO_ROOT / "data" / "artifacts" / "preflop" / "six_max_100bb_rakefree.json"
SOLVE_CONFIG_PATH = REPO_ROOT / "data" / "artifacts" / "postflop" / "solve_config.json"

ADMITTED = (
    "SB:raise@2.5,BB:call",
    "BTN:raise@2.5,BB:call",
    "CO:raise@2.5,BB:call",
    "HJ:raise@2.5,BB:call",
    "LJ:raise@2.5,BB:call",
)
REACH_PERCENT = (5.53, 3.66, 2.75, 2.71, 2.42)
"""The contract's figures: how often each line reaches a flop, as a share of all hands."""


@pytest.fixture(scope="module")
def lines():
    """`solver_artifacts.postflop_lines`: the admitted lines, their order and their ranges."""
    import poker_training_bot.solver_artifacts.postflop_lines as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


@pytest.fixture(scope="module")
def chart():
    return json.loads(CHART_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def solve_config():
    return json.loads(SOLVE_CONFIG_PATH.read_text(encoding="utf-8"))


def combos(hand: str) -> int:
    return 6 if len(hand) == 2 else (4 if hand.endswith("s") else 12)


def chart_range(chart, spot: str, action: str) -> dict[str, float]:
    weights = chart["action_weights"][spot]
    return artifact.floor_range({hand: row[action] for hand, row in weights.items()})


SEATED = [
    (
        "SB:raise@2.5,BB:call",
        ("t6/d100/SB/rfi", "raise"),
        ("t6/d100/BB/SB:raise@2.5", "call"),
        5.0,
    ),
    *(
        (
            f"{opener}:raise@2.5,BB:call",
            (f"t6/d100/BB/{opener}:raise@2.5", "call"),
            (f"t6/d100/{opener}/rfi", "raise"),
            5.5,
        )
        for opener in ("BTN", "CO", "HJ", "LJ")
    ),
]
"""Per line: the chart spot and action of the out-of-position range, of the in-position range,
and the pot. Written out here from the seating rule - the small blind acts first after the flop,
every other opener acts last - rather than read back from the code under test."""


def gtopen_range_text(weights: dict[str, float]) -> str:
    """GTOpen's range syntax, class-level: `AKs` at full weight, `AKs:0.5` otherwise. The rule
    `scripts/solve_postflop_sample.py`'s `range_text` wrote every committed solve with."""
    parts = []
    for hand, weight in weights.items():
        parts.append(hand if weight >= 1.0 else f"{hand}:{weight:.4f}".rstrip("0").rstrip("."))
    return ",".join(parts)


# --------------------------------------------------------------------------- #
# Which lines, and in what order
# --------------------------------------------------------------------------- #


class TestTheAdmittedLinesAndTheirOrder:
    """Criterion: the lines are small blind, button, cutoff, hijack and lojack opening against the
    big blind, in that order, which is the chart's own: those lines reach a flop in 5.53, 3.66,
    2.75, 2.71 and 2.42 percent of hands, weighting each action by its chart probability.
    `LINE-RANKING-BY-CLOSING-DECISION-ARRIVAL-COUNTS-LINES-THE-CHART-NEVER-PLAYS`."""

    def test_the_admitted_lines_in_the_ruled_order(self, lines) -> None:
        assert tuple(owed(lines, "ADMITTED_LINES")) == ADMITTED

    @pytest.mark.parametrize(("line", "percent"), list(zip(ADMITTED, REACH_PERCENT, strict=True)))
    def test_each_line_s_reach_is_the_chart_s_figure(self, lines, line, percent) -> None:
        assert owed(lines, "line_reach")(line) * 100 == pytest.approx(percent, abs=0.005)

    def test_the_reach_is_the_arrival_times_the_big_blind_s_call_rate(self, lines, chart) -> None:
        """Re-derived here from the chart rather than quoted: the big blind arrives holding every
        combo, so its call rate is the combo-weighted mean of its call weights."""
        for line in ADMITTED:
            opener = line.split(":", 1)[0]
            spot = f"t6/d100/BB/{opener}:raise@2.5"
            weights = chart["action_weights"][spot]
            call_rate = sum(combos(h) * row["call"] for h, row in weights.items()) / 1326
            expected = chart["arrival_ppb"][spot] / 1e9 * call_rate
            assert owed(lines, "line_reach")(line) == pytest.approx(expected, rel=1e-9), line

    def test_the_ranking_is_the_admitted_order(self, lines) -> None:
        assert tuple(owed(lines, "ranked_lines")()) == ADMITTED

    def test_a_line_the_chart_never_plays_ranks_nowhere(self, lines) -> None:
        """The hijack flatting a lojack open is asked often - 185,689,291 parts per billion on
        arrival - and never happens, because the chart's hijack facing a lojack open offers only
        fold and raise; there is no call action to weight at all. The old ranking put it
        first."""
        never = "LJ:raise@2.5,HJ:call"

        assert owed(lines, "line_reach")(never) == 0.0
        assert never not in owed(lines, "ranked_lines")()

    def test_a_limped_line_is_excluded_by_name_with_its_reason(self, lines) -> None:
        """The corpus's fourth most common flop line is the small blind completing and the big
        blind checking. The chart's small blind only folds or raises, so it has no range to
        solve with."""
        excluded = owed(lines, "EXCLUDED_LINES")

        assert "SB:call" in excluded
        assert "limp" in excluded["SB:call"].lower()
        assert "SB:call" not in owed(lines, "ranked_lines")()

    def test_a_line_with_no_chart_range_is_refused_rather_than_given_one(self, lines) -> None:
        with pytest.raises(owed(lines, "LineRangeError")) as raised:
            owed(lines, "line_ranges")("SB:call")

        assert "SB:call" in str(raised.value)


# --------------------------------------------------------------------------- #
# Whose range is whose: seat position after the flop, not who raised
# --------------------------------------------------------------------------- #


class TestRangesAreAssignedBySeatPositionAfterTheFlop:
    """Criterion: the ranges for any heads-up line are derived from the committed chart by one
    tested function that assigns them by seat position after the flop, not by who raised: in
    `SB:raise@2.5,BB:call` the raiser is out of position."""

    def test_the_committed_button_line_is_what_the_driver_solved(self, lines, solve_config) -> None:
        found = owed(lines, "line_ranges")("BTN:raise@2.5,BB:call")

        assert (found.oop_position, found.ip_position) == ("BB", "BTN")
        assert found.range_oop == solve_config["ranges"]["oop_bb_call"]
        assert found.range_ip == solve_config["ranges"]["ip_btn_open"]
        assert list(found.range_oop) == list(solve_config["ranges"]["oop_bb_call"])
        assert list(found.range_ip) == list(solve_config["ranges"]["ip_btn_open"])

    def test_the_small_blind_raiser_is_out_of_position(self, lines, chart) -> None:
        found = owed(lines, "line_ranges")("SB:raise@2.5,BB:call")

        assert (found.oop_position, found.ip_position) == ("SB", "BB")
        assert found.range_oop == chart_range(chart, "t6/d100/SB/rfi", "raise")
        assert found.range_ip == chart_range(chart, "t6/d100/BB/SB:raise@2.5", "call")

    def test_the_small_blind_line_s_ranges_hold_the_combos_the_chart_gives(self, lines) -> None:
        """730 combos open from the small blind and 470 defend from the big blind after the
        floor; swapping the seats puts the wider range in position."""
        found = owed(lines, "line_ranges")("SB:raise@2.5,BB:call")

        assert sum(combos(hand) for hand in found.range_oop) == 730
        assert sum(combos(hand) for hand in found.range_ip) == 470

    @pytest.mark.parametrize("opener", ["CO", "HJ", "LJ"])
    def test_every_other_opener_is_in_position_against_the_big_blind(
        self, lines, chart, opener
    ) -> None:
        found = owed(lines, "line_ranges")(f"{opener}:raise@2.5,BB:call")

        assert (found.oop_position, found.ip_position) == ("BB", opener)
        assert found.range_oop == chart_range(chart, f"t6/d100/BB/{opener}:raise@2.5", "call")
        assert found.range_ip == chart_range(chart, f"t6/d100/{opener}/rfi", "raise")

    @pytest.mark.parametrize(
        ("line", "pot"),
        [(ADMITTED[0], 5.0), *((line, 5.5) for line in ADMITTED[1:])],
    )
    def test_the_pot_and_stack_follow_from_the_line(self, lines, line, pot) -> None:
        """2.5 from each live seat, plus the small blind's dead 0.5 when it folded."""
        found = owed(lines, "line_ranges")(line)

        assert found.starting_pot == pytest.approx(pot)
        assert found.effective_stack == pytest.approx(97.5)

    def test_every_weight_is_floored_class_level(self, lines) -> None:
        for line in ADMITTED:
            found = owed(lines, "line_ranges")(line)
            for weights in (found.range_oop, found.range_ip):
                assert min(weights.values()) >= artifact.RANGE_WEIGHT_FLOOR, line
                assert all(len(hand) in (2, 3) for hand in weights), line


# --------------------------------------------------------------------------- #
# The plan the driver posts, for any admitted line
# --------------------------------------------------------------------------- #


class TestThePlanForAnyLineIsTheRuledConfiguration:
    """Decision 10, ruled by Taylor: the same bet sizes and settings as `solve_config.json` for
    every single-raised line, the empty `donk` setting included."""

    def test_the_button_line_s_body_is_the_one_the_committed_cells_were_solved_on(
        self, lines, solve_config
    ) -> None:
        plan = owed(lines, "plan_for")("BTN:raise@2.5,BB:call", ("Kh", "7d", "2c"))
        body = driver.spot_body(plan)

        assert body["range_oop"] == gtopen_range_text(solve_config["ranges"]["oop_bb_call"])
        assert body["range_ip"] == gtopen_range_text(solve_config["ranges"]["ip_btn_open"])
        assert body["board"] == "Kh7d2c"

    @pytest.mark.parametrize(("line", "oop", "ip", "pot"), SEATED)
    def test_each_line_posts_the_chart_s_range_for_each_seat(
        self, lines, chart, line, oop, ip, pot
    ) -> None:
        """Both ranges, the pot and the stack, per line, against the chart directly rather than
        through `line_ranges`. The likeliest wrong `plan_for` swaps the seats for the small blind
        and otherwise posts `solve_config.json`'s button ranges: the cutoff's line would then be
        solved with the button's 498-combo open, where the chart's cutoff opens 350."""
        plan = owed(lines, "plan_for")(line, ("Kh", "7d", "2c"))
        body = driver.spot_body(plan)

        assert body["range_oop"] == gtopen_range_text(chart_range(chart, *oop)), line
        assert body["range_ip"] == gtopen_range_text(chart_range(chart, *ip)), line
        assert body["starting_pot"] == pytest.approx(pot), line
        assert body["effective_stack"] == pytest.approx(97.5), line

    def test_every_line_is_planned_on_the_ruled_configuration(self, lines) -> None:
        for line in ADMITTED:
            plan = owed(lines, "plan_for")(line, ("Kh", "7d", "2c"))
            assert driver.solve_config_errors(plan.config) == [], line
            assert driver.plan_refusals(plan) == [], line
            body = driver.spot_body(plan)
            assert body["oop"] == body["ip"], line
            assert [street["bet"] for street in body["oop"]] == ["33 75", "66 125", "66 125"]
            assert {street["donk"] for street in body["oop"]} == {""}, line

    def test_the_plan_names_the_line_it_was_built_for(self, lines) -> None:
        plan = owed(lines, "plan_for")("SB:raise@2.5,BB:call", ("2c", "2d", "2h"))

        assert "SB:raise@2.5,BB:call" in plan.preflop_line


# --------------------------------------------------------------------------- #
# A board refusal names the line and the seat it was scoped to
# --------------------------------------------------------------------------- #

BOARD_LEVEL = {betting.REFUSE_NO_CELL_FOR_THIS_BOARD, betting.REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED}


class TestABoardRefusalSaysWhichLineAndSeat:
    """Criterion: a board refusal says which line and seat it was scoped to.
    `A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`: today `9c8c7c` refuses
    for the big blind under `no-cell-for-this-board` although the artifact holds it - for the
    button, on the other side of the same betting sequence - and nothing in the refusal says so.

    Either board-level code may fire, because a campaign board this machine has not fetched
    refuses as not fetched rather than as absent; both are scoped per line and seat.

    **The strategy is built over an explicitly empty fetched folder.** A machine that has fetched
    the campaign must answer every closed board, so a strategy reading whatever this machine
    happens to hold would make the verdict depend on the disk rather than the tree. `from_repo`
    takes the folder fetched objects live in as `fetched_root`; an empty one is a fresh clone."""

    @pytest.fixture
    def strategy(self, tmp_path):
        signature = inspect.signature(betting.PostflopBettingStrategy.from_repo)
        assert "fetched_root" in signature.parameters, (
            "PostflopBettingStrategy.from_repo must take fetched_root, the folder fetched"
            " objects are read from, so a test can say this machine has fetched nothing"
        )
        empty = tmp_path / "fetched"
        empty.mkdir()
        return betting.PostflopBettingStrategy.from_repo(fetched_root=empty)

    @pytest.mark.parametrize("board", [("9c", "8c", "7c"), ("Jd", "6s", "3c")])
    def test_the_big_blind_s_refusal_names_the_line_and_the_seat(self, strategy, board) -> None:
        outcome = strategy.decide(button_line_query(board=board))

        assert isinstance(outcome, contract_module.StrategyRefusal)
        assert outcome.code in BOARD_LEVEL, outcome.code
        assert outcome.named("hero_position") == "BB", outcome.detail
        assert "BTN:raise@2.5,BB:call" in (outcome.named("preflop_line") or ""), outcome.detail

    def test_the_button_s_refusal_names_the_button(self, strategy) -> None:
        """The same line from the other chair, facing the big blind's check. A refusal that
        writes the big blind as a constant passes the test above and fails this one."""
        query = button_line_query(
            seat=BUTTON_SEAT,
            board=("Jd", "6s", "3c"),
            postflop_actions=(contract_module.SeatAction(BIG_BLIND_SEAT, "check"),),
        )

        outcome = strategy.decide(query)

        assert isinstance(outcome, contract_module.StrategyRefusal)
        assert outcome.code in BOARD_LEVEL, outcome.code
        assert outcome.named("hero_position") == "BTN", outcome.detail
        assert "BTN:raise@2.5,BB:call" in (outcome.named("preflop_line") or ""), outcome.detail


# --------------------------------------------------------------------------- #
# A live small blind hand maps onto the small blind's out-of-position cell
# --------------------------------------------------------------------------- #


class TestASmallBlindHandFindsTheSmallBlindsCell:
    """Checked at stage 4 because the driver hardcodes the button's line: the spot key and the
    strategy already derive the small blind's line from the seats, with the small blind first to
    act after the flop and a 5.0 pot, so the lookup side needs nothing new. What does hardcode the
    button is the harvest's seat map - `seat_of_player` in `scripts/solve_postflop_sample.py`
    returns the big blind for GTOpen's out-of-position player on every line - so the map a
    harvest uses comes from the line, here."""

    def test_the_small_blind_first_to_act_keys_its_cell_on_its_own_line(self) -> None:
        line = key.completed_preflop_line(
            6,
            100,
            "SB",
            (PreflopAction("SB", "raise", 2.5), PreflopAction("BB", "call")),
            small_blind_bb=0.5,
            big_blind_bb=1.0,
            ante_bb=0.0,
        )

        spot = key.postflop_spot_key(line, ("Kh", "7d", "2c"), (), line.pot_bb, 97.5)

        assert spot == "f/b:Kh7d2c/t6/d100/SB/SB:raise@2.5,BB:call/f:none/p:5/e:97.5"

    def test_the_big_blind_cannot_act_first_on_the_small_blind_s_line(self) -> None:
        line = key.completed_preflop_line(
            6,
            100,
            "BB",
            (PreflopAction("SB", "raise", 2.5), PreflopAction("BB", "call")),
            small_blind_bb=0.5,
            big_blind_bb=1.0,
            ante_bb=0.0,
        )

        with pytest.raises(ValueError):
            key.postflop_spot_key(
                line, ("Kh", "7d", "2c"), (key.FlopAction("BB", "check"),), line.pot_bb, 97.5
            )

    @pytest.mark.parametrize(
        ("line", "seats"),
        [
            ("SB:raise@2.5,BB:call", {0: "SB", 1: "BB"}),
            ("BTN:raise@2.5,BB:call", {0: "BB", 1: "BTN"}),
            ("LJ:raise@2.5,BB:call", {0: "BB", 1: "LJ"}),
        ],
    )
    def test_the_harvest_seat_map_comes_from_the_line(self, lines, line, seats) -> None:
        """GTOpen's player 0 is out of position and player 1 in position; the map names them."""
        assert owed(lines, "seat_labels")(line) == seats
