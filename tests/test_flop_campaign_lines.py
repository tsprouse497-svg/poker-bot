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

import hashlib
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
from tests.test_postflop_betting import BUTTON_SEAT, SB_SEAT, seated
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
            ("CO:raise@2.5,BB:call", {0: "BB", 1: "CO"}),
            ("HJ:raise@2.5,BB:call", {0: "BB", 1: "HJ"}),
            ("LJ:raise@2.5,BB:call", {0: "BB", 1: "LJ"}),
        ],
    )
    def test_the_harvest_seat_map_comes_from_the_line(self, lines, line, seats) -> None:
        """GTOpen's player 0 is out of position and player 1 in position; the map names them."""
        assert owed(lines, "seat_labels")(line) == seats


# --------------------------------------------------------------------------- #
# A machine that has fetched a closed board answers it; one that has not refuses
# --------------------------------------------------------------------------- #

SAMPLE_DIR = REPO_ROOT / "data" / "artifacts" / "postflop" / "sample"
INDEX_PATH = REPO_ROOT / "data" / "artifacts" / "postflop" / "index.json"
FETCHED_INDEX_KEY = "postflop/btn-v-bb/index.json"
FETCHED_FLOP_KEY = "postflop/btn-v-bb/Kh7d2c.flop.json"
FACING_75_KEY = "f/b:Kh7d2c/t6/d100/BB/BTN:raise@2.5,BB:call/f:BB:check,BTN:bet@75/p:5.5/e:97.5"


def facing_a_three_quarter_bet_cell() -> dict:
    """The big blind facing the button's 75 percent c-bet on `Kh7d2c`: one of the board's 14
    flop decision points, and not one the sample holds. Built from the committed cell for the
    33 percent bet - same board, seat, line and ranges - with the bet, the key and the raise
    size moved to the 75 percent node (4.125bb, raised 2.5x to 10.3125bb). Its frequencies are
    the 33 percent node's, borrowed; this test proves where the strategy reads from, not what
    the node plays."""
    cell = json.loads((SAMPLE_DIR / "rainbow-dry-high-facing-a-bet.json").read_text("utf-8"))
    cell["spot_key"] = FACING_75_KEY
    cell["flop_actions"][1]["size_pct"] = 75.0
    cell["actions"][2]["size_bb"] = 4.125 * 2.5
    return cell


def write(path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


CHECK_RAISED_KEY = (
    "f/b:Kh7d2c/t6/d100/BTN/BTN:raise@2.5,BB:call/f:BB:check,BTN:bet@33,BB:raise@2.5x/p:5.5/e:97.5"
)
BET_33_BB = 0.33 * 5.5


def facing_a_check_raise_cell() -> dict:
    """The button facing the big blind's 2.5x check-raise over its 33 percent c-bet on `Kh7d2c`:
    one of the eight flop decision points that follow a raise, which decision 16 made nameable.
    Built from the committed 33 percent cell - same board, line and ranges - with the seat, the
    key and the menu moved to the node: the button has 1.815bb out, the big blind raised to
    4.5375bb, and the button's own re-raise goes 2.5x that, to 11.34375bb. The raise is recorded
    by its multiplier, the cell field decision 16 freezes. Its frequencies are borrowed; this
    proves the node is played, not what it plays."""
    cell = json.loads((SAMPLE_DIR / "rainbow-dry-high-facing-a-bet.json").read_text("utf-8"))
    cell["spot_key"] = CHECK_RAISED_KEY
    cell["preflop_line"] = "t6/d100/BTN/BTN:raise@2.5,BB:call"
    cell["hero_position"] = "BTN"
    cell["flop_actions"].append({"position": "BB", "action": "raise", "multiplier": 2.5})
    cell["hero_street_bet_bb"] = BET_33_BB
    cell["actions"][2]["size_bb"] = 2.5 * 2.5 * BET_33_BB
    return cell


def fetched_folders(tmp_path, cells) -> dict:
    """A manifest folder holding one closed board for the button's line, `Kh7d2c`, and a
    fetched folder holding that board's line index and flop object where `fetch_line` leaves
    them - each at its object key under the folder. The flop object is a JSON document
    `{"cells": [cell documents]}` in the committed cell schema, written uncompressed, holding
    `cells`. The turn and river objects are listed and not fetched, which is the flop-only
    machine. The object holds fewer than the board's fourteen cells: the fetch checks which
    decision points an object holds, and this folder is written as if it had passed."""
    fetched = tmp_path / "fetched"
    flop_digest = write(
        fetched / FETCHED_FLOP_KEY, json.dumps({"cells": list(cells)}, sort_keys=True).encode()
    )
    streets = {"flop": {"key": FETCHED_FLOP_KEY, "sha256": flop_digest}}
    for street in ("turn", "river"):
        streets[street] = {"key": f"postflop/btn-v-bb/Kh7d2c.{street}.bin", "sha256": "0" * 64}
    counts = {"flop": 14, "turn": 6_419, "river": 1_477_056}
    index = {
        "line_index_schema_version": 1,
        "preflop_line": "BTN:raise@2.5,BB:call",
        "boards": [{"board": ["Kh", "7d", "2c"], "decision_points": counts, "objects": streets}],
    }
    index_bytes = json.dumps(index, sort_keys=True).encode()
    index_digest = write(fetched / FETCHED_INDEX_KEY, index_bytes)
    committed = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    manifest = {
        "manifest_schema_version": 1,
        "preflop_line": "BTN:raise@2.5,BB:call",
        "index": {
            "object_key": FETCHED_INDEX_KEY,
            "sha256": index_digest,
            "bytes": len(index_bytes),
        },
        "flops_held": 24,
        "refused_boards": 0,
        "boards": [
            {
                "board": ["Kh", "7d", "2c"],
                "status": "closed",
                "decision_points": counts,
                "achieved_exploitability_pct_of_pot": 0.283013340119407,
                "iterations": 340,
                "machine": "invented machine for a test",
                "threads": 10,
                "strategy_digests": {
                    entry["spot_key"]: entry["strategy_digest"]
                    for entry in committed["entries"]
                    if entry["board"] == ["Kh", "7d", "2c"]
                },
            }
        ],
    }
    manifests = tmp_path / "manifests"
    write(manifests / "btn-raise-bb-call.json", json.dumps(manifest, indent=1).encode())
    empty = tmp_path / "nothing-fetched"
    empty.mkdir()
    return {"fetched": fetched, "empty": empty, "manifests": manifests}


@pytest.fixture
def fetched_machine(tmp_path):
    """The fetched folders holding the 75 percent node and nothing else."""
    return fetched_folders(tmp_path, [facing_a_three_quarter_bet_cell()])


def facing_a_three_quarter_bet():
    """The button bets 413 into 550, which the menu matches as 75 percent."""
    return button_line_query(
        legal_actions=("fold", "call", "raise"),
        to_call=413,
        current_bet=413,
        min_raise_target=826,
        **seated(
            {BUTTON_SEAT: 663, SB_SEAT: 50, BIG_BLIND_SEAT: 250},
            (BUTTON_SEAT, BIG_BLIND_SEAT),
            {BUTTON_SEAT: 413},
        ),
        postflop_actions=(
            contract_module.SeatAction(BIG_BLIND_SEAT, "check"),
            contract_module.SeatAction(BUTTON_SEAT, "bet", 413),
        ),
    )


def facing_a_check_raise():
    """The button c-bets 182 into 550, which the menu matches as 33 percent, and the big blind
    check-raises to 455, exactly 2.5 times 182, so matching it needs no ruling on how far a real
    raise may sit from the menu's 2.5x."""
    return button_line_query(
        seat=BUTTON_SEAT,
        legal_actions=("fold", "call", "raise"),
        to_call=273,
        current_bet=455,
        min_raise_target=728,
        **seated(
            {BUTTON_SEAT: 432, SB_SEAT: 50, BIG_BLIND_SEAT: 705},
            (BUTTON_SEAT, BIG_BLIND_SEAT),
            {BUTTON_SEAT: 182, BIG_BLIND_SEAT: 455},
        ),
        postflop_actions=(
            contract_module.SeatAction(BIG_BLIND_SEAT, "check"),
            contract_module.SeatAction(BUTTON_SEAT, "bet", 182),
            contract_module.SeatAction(BIG_BLIND_SEAT, "raise", 455),
        ),
    )


class TestAFetchedClosedBoardIsPlayed:
    """Criteria: the bot plays the flop objects a machine has fetched, and a machine that has not
    fetched refuses with the not-fetched code.
    `THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`.
    `from_repo` takes `fetched_root`, the folder the fetch wrote into, and `manifest_dir`, the
    folder of manifests - the committed one by default - so a strategy that ignores either
    argument fails one of the two tests below."""

    def build(self, fetched_root, manifest_dir):
        signature = inspect.signature(betting.PostflopBettingStrategy.from_repo)
        assert {"fetched_root", "manifest_dir"} <= set(signature.parameters), (
            "PostflopBettingStrategy.from_repo must take fetched_root and manifest_dir"
        )
        return betting.PostflopBettingStrategy.from_repo(
            fetched_root=fetched_root, manifest_dir=manifest_dir
        )

    def test_the_fixture_s_cell_is_not_one_the_sample_holds(self) -> None:
        held = {
            json.loads(path.read_text(encoding="utf-8"))["spot_key"]
            for path in SAMPLE_DIR.glob("*.json")
        }
        assert FACING_75_KEY not in held

    def test_a_machine_that_fetched_the_board_answers_the_node(self, fetched_machine) -> None:
        strategy = self.build(fetched_machine["fetched"], fetched_machine["manifests"])

        outcome = strategy.decide(facing_a_three_quarter_bet())

        assert isinstance(outcome, contract_module.StrategyDecision), outcome
        assert outcome.action in ("fold", "call", "raise")

    def test_an_object_on_disk_that_no_manifest_lists_is_not_played(self, fetched_machine) -> None:
        """The fetched folder is full and the manifest folder is empty. A strategy that reads the
        committed manifests whatever it is handed, and finds the index by looking in the fetched
        folder, answers here; the right one refuses, because nothing it was given lists the
        board."""
        empty_manifests = fetched_machine["empty"].parent / "no-manifests"
        empty_manifests.mkdir()
        strategy = self.build(fetched_machine["fetched"], empty_manifests)

        outcome = strategy.decide(facing_a_three_quarter_bet())

        assert isinstance(outcome, contract_module.StrategyRefusal), outcome

    def test_the_same_node_on_a_machine_that_fetched_nothing_refuses_as_not_fetched(
        self, fetched_machine
    ) -> None:
        strategy = self.build(fetched_machine["empty"], fetched_machine["manifests"])

        outcome = strategy.decide(facing_a_three_quarter_bet())

        assert isinstance(outcome, contract_module.StrategyRefusal), outcome
        assert outcome.code == betting.REFUSE_IN_THE_INDEX_BUT_NOT_FETCHED, outcome.code
        assert outcome.named("hero_position") == "BB", outcome.detail

    def test_a_machine_that_fetched_a_node_after_a_raise_plays_it(self, tmp_path) -> None:
        """Decision 16's purpose: the bot answers a node after a raise rather than missing it.
        A table walk that keys the faced raise as a percent of pot - 455 into 732 is 62.16
        percent, matched onto a raise fraction off some cell's menu - builds a key no cell holds,
        or one `FlopAction` refuses, and misses here while every key and fetch test passes."""
        folders = fetched_folders(tmp_path, [facing_a_check_raise_cell()])
        strategy = self.build(folders["fetched"], folders["manifests"])

        outcome = strategy.decide(facing_a_check_raise())

        assert isinstance(outcome, contract_module.StrategyDecision), outcome
        assert outcome.action in ("fold", "call", "raise")

    def test_a_fetched_object_altered_after_the_fetch_is_not_played(self, fetched_machine) -> None:
        """The fetch checked the object's digest; the strategy reads the disk later. One class's
        row is reordered in place, so the object is still valid JSON in the cell schema and its
        bytes are no longer the ones the line index lists. A strategy that reads whatever sits
        at the object key answers here."""
        path = fetched_machine["fetched"] / FETCHED_FLOP_KEY
        document = json.loads(path.read_bytes())
        row = document["cells"][0]["class_weights"][0]
        document["cells"][0]["class_weights"][0] = row[::-1]
        path.write_bytes(json.dumps(document, sort_keys=True).encode())
        strategy = self.build(fetched_machine["fetched"], fetched_machine["manifests"])

        outcome = strategy.decide(facing_a_three_quarter_bet())

        assert isinstance(outcome, contract_module.StrategyRefusal), outcome
