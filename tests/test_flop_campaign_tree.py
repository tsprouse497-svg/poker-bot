"""Phase 21, stage 4: the tree a line builds, what one solve closes, and the memory bar.

Authored from the contract before any implementation exists; see the head of
`tests/test_flop_campaign_threads.py` for how the missing modules are reached.

**Every figure is GTOpen's own tree rule, re-derived.** `crates/solver/src/tree.rs`
(`legal_actions`, `apply_action`, `street_end`, lines 432-760) builds the tree a flop solve holds,
and the arena it plans is `entries * 8` bytes at full precision, where `entries` is each seat's
action slots times that seat's live combos. The tree's shape depends on the pot, the stack and the
menu and never on the board; the board only removes combos. So one tree per line and a combo count
per flop is the whole walk over 22,100 flops, and none of it needs a solver.

**Two tree rules, one port (decision 17).** At the pin, `4aee435`, a street both players check
passes the last aggressor on to the next street, so out of position cannot lead it with the empty
`donk` list; the clone the campaign solves on carries upstream `85b0a692`'s fix, which clears the
initiative on a checked-through street. Every function here that builds a tree - from a line or
from a pot - takes the keyword-only `carry_aggressor_through_checks: bool = False`, named after
GTOpen's own `TreeConfig` field: `False`, the default, is the clone's tree and the campaign's;
`True` is the pin's. The figures a build returns carry the rule they were built under as
`figures.carry_aggressor_through_checks`, and every function that takes figures reads the rule off
them rather than taking it again. `line_tree_figures`, `build_tree_figures`, `planned_arena_for`,
`line_memory_bar`, `campaign_memory_bar` and `flops_planned_above` take the keyword. The new tree's
figures were measured on 2026-10-04 by a tree counter linked against the clone's solver crate,
building each spot unsolved under both rules; the old rule reproduced every figure this file pinned
before, to the byte (the ExecPlan's decision 17 slice has the commands).

**What closes is what is stored (decision 1, re-ruled 2026-10-04): the flop and the turn.**
`closure_counts(figures)` returns `{"flop": ..., "turn": ...}` and no river key. The river the solve
still builds is a tree figure, kept apart: `river_tree_points(figures)` is the reachable river, the
48 river cards under each of the 49 turn cards, and `unreachable_river_points(figures)` the river
`tree.rs` also builds under the turn card already dealt.

**The four planned arenas phase 16 recorded are the check the port has to pass to the byte, on the
pin's tree, which is the tree phase 16 solved.** Each object's `solve.arena_bytes` was written
through `arena_bytes` in `postflop_transport`, which reads the server's decimal `arena_mb` as
2^20-byte megabytes. That reading is decision 14's, and it is `runtime-reversible` only while no
frozen test pins it - so the test below re-applies the reading phase 16 used, in its own arithmetic,
to reproduce phase 16's records. It says nothing about which reading the driver uses from here on.
The `9c8c7c` figure is committed in `data/artifacts/postflop/deep_convergence_check.json`; the other
three are in the four objects under `~/poker-bot-solve-objects/postflop`, read on 2026-09-26, which
git does not hold. These checks are kept against the pin's rule as historical validations of the
port: they held on the tree phase 16 ran, and the clone's tree plans 6.2 to 6.3 percent more.
"""

from __future__ import annotations

import itertools
import json

import pytest

from poker_training_bot.solver_artifacts import postflop_isomorphism as isomorphism
from scripts.repo_paths import REPO_ROOT

POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
COMMITTED_LINE = "BTN:raise@2.5,BB:call"
SMALL_BLIND_LINE = "SB:raise@2.5,BB:call"
LATE_LINES = ("CO:raise@2.5,BB:call", "HJ:raise@2.5,BB:call", "LJ:raise@2.5,BB:call")
ALL_FLOPS = 22_100
PIN = {"carry_aggressor_through_checks": True}
"""The pin's tree rule, passed by name wherever a check is a record of the tree phase 16 solved."""

PHASE_16_RECORDED_ARENA_BYTES = {
    ("9c", "8c", "7c"): 12_041_331_798,
    ("Kh", "7d", "2c"): 11_978_042_234,
    ("8c", "8d", "3c"): 12_236_838_500,
    ("Ac", "8c", "3c"): 11_598_324_830,
}
"""Each object's `solve.arena_bytes`, as phase 16 wrote it through the 2^20 reading, on the pin's
tree."""

SERVER_ARENA_BYTES = {
    ("9c", "8c", "7c"): 11_483_508_872,
    ("Kh", "7d", "2c"): 11_423_151_240,
    ("8c", "8d", "3c"): 11_669_958_592,
    ("Ac", "8c", "3c"): 11_061_024_504,
}
"""The same four in the server's own unit, `entries * 8`, on the pin's tree: 346 and 447 live
combos on `9c8c7c`, 342 and 447 on `Kh7d2c`, 350 and 456 on `8c8d3c`, 331 and 433 on `Ac8c3c`."""

CLONE_ARENA_BYTES = {
    ("9c", "8c", "7c"): 12_200_524_304,
    ("Kh", "7d", "2c"): 12_136_939_728,
    ("8c", "8d", "3c"): 12_399_017_440,
    ("Ac", "8c", "3c"): 11_752_224_384,
}
"""The same four boards planned on the clone's tree, which the re-solve decision 17 requires runs
on: the live combos are the board's and unchanged, and every seat has more action slots."""


@pytest.fixture(scope="module")
def tree():
    """`solver_artifacts.postflop_tree_size`: GTOpen's tree rule, counted rather than built."""
    import poker_training_bot.solver_artifacts.postflop_tree_size as module

    return module


@pytest.fixture(scope="module")
def textures():
    """`solver_artifacts.postflop_textures`: the six texture groups over the 1,755 classes."""
    import poker_training_bot.solver_artifacts.postflop_textures as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def phase_16_reading(server_bytes: int) -> int:
    """How phase 16 recorded a server arena: `int(arena_mb * 1024 * 1024)` on `bytes / 1e6`."""
    return int(server_bytes / 1_000_000 * 1024 * 1024)


@pytest.fixture(scope="module")
def committed_tree(tree):
    return owed(tree, "line_tree_figures")(COMMITTED_LINE)


@pytest.fixture(scope="module")
def small_blind_tree(tree):
    return owed(tree, "line_tree_figures")(SMALL_BLIND_LINE)


@pytest.fixture(scope="module")
def pinned_committed_tree(tree):
    return owed(tree, "line_tree_figures")(COMMITTED_LINE, **PIN)


@pytest.fixture(scope="module")
def pinned_small_blind_tree(tree):
    return owed(tree, "line_tree_figures")(SMALL_BLIND_LINE, **PIN)


# --------------------------------------------------------------------------- #
# The tree a line builds
# --------------------------------------------------------------------------- #


class TestTheCommittedLineBuildsTheCloneSTree:
    """The committed line and menu, pot 5.5 and 97.5 behind, on the clone's tree: 4,144,704 nodes
    and 1,588,692 decision points, 14 on the flop (seven per seat), 131 on each of 49 turns and
    659 on each river GTOpen builds under them."""

    def test_the_node_and_decision_point_totals(self, committed_tree) -> None:
        assert committed_tree.nodes == 4_144_704
        assert sum(sum(pair) for pair in committed_tree.action_nodes.values()) == 1_588_692

    def test_the_decision_points_per_street_and_seat_as_built(self, committed_tree) -> None:
        """Out of position first in each pair. The river is as `tree.rs` builds it, with the
        subtree under the already-dealt turn card still in its slot."""
        assert tuple(committed_tree.action_nodes["flop"]) == (7, 7)
        assert tuple(committed_tree.action_nodes["turn"]) == (3_430, 2_989)
        assert tuple(committed_tree.action_nodes["river"]) == (847_553, 734_706)

    def test_the_action_slots_that_size_the_arena(self, committed_tree) -> None:
        assert tuple(committed_tree.slots) == (1_987_018, 1_873_730)

    def test_the_late_position_lines_build_the_same_tree(self, tree, committed_tree) -> None:
        """Cutoff, hijack and lojack opens reach the same 5.5 pot at the same depth, so only the
        ranges differ; a per-line figure that differs here is a port that reads the line."""
        for line in LATE_LINES:
            figures = owed(tree, "line_tree_figures")(line)
            assert figures.nodes == committed_tree.nodes, line
            assert tuple(figures.slots) == tuple(committed_tree.slots), line


class TestTheSmallBlindLineBuildsItsOwnTree:
    """Criterion: every per-line figure is re-derived for each admitted line, because a line
    with another pot builds another tree. The small blind's open is called into a 5.0 pot, not
    5.5, so every bet and every all-in snap moves."""

    def test_the_node_total(self, small_blind_tree) -> None:
        assert small_blind_tree.nodes == 4_339_626

    def test_the_decision_points_per_street_and_seat_as_built(self, small_blind_tree) -> None:
        assert tuple(small_blind_tree.action_nodes["flop"]) == (7, 7)
        assert tuple(small_blind_tree.action_nodes["turn"]) == (3_528, 3_038)
        assert tuple(small_blind_tree.action_nodes["river"]) == (881_167, 773_122)

    def test_the_action_slots(self, small_blind_tree) -> None:
        assert tuple(small_blind_tree.slots) == (2_078_501, 1_969_966)

    def test_the_pot_is_read_off_the_line_and_not_assumed(self, tree) -> None:
        build = owed(tree, "build_tree_figures")

        assert build(5.0, 97.5).nodes == 4_339_626
        assert build(5.5, 97.5).nodes == 4_144_704


class TestThePinSTreeIsKeptAsTheRuleItWas:
    """Decision 17. The port builds both rules: the clone's by default, which the campaign solves
    on, and the pin's by name, which every solve phase 16 committed ran on. The pin's figures are
    the ones this file pinned before the clone existed, kept to the byte as the record that the
    port is GTOpen's rule and not a fit to the new figures."""

    def test_the_default_is_the_clone_s_tree(self, tree, committed_tree) -> None:
        explicit = owed(tree, "line_tree_figures")(
            COMMITTED_LINE, carry_aggressor_through_checks=False
        )

        assert committed_tree.carry_aggressor_through_checks is False
        assert explicit.nodes == committed_tree.nodes == 4_144_704
        assert tuple(explicit.slots) == tuple(committed_tree.slots)
        assert owed(tree, "build_tree_figures")(5.5, 97.5).carry_aggressor_through_checks is False

    def test_the_pin_s_rule_builds_the_pin_s_committed_tree(self, pinned_committed_tree) -> None:
        assert pinned_committed_tree.carry_aggressor_through_checks is True
        assert pinned_committed_tree.nodes == 3_921_411
        assert sum(sum(pair) for pair in pinned_committed_tree.action_nodes.values()) == 1_514_261
        assert tuple(pinned_committed_tree.action_nodes["flop"]) == (7, 7)
        assert tuple(pinned_committed_tree.action_nodes["turn"]) == (3_430, 2_989)
        assert tuple(pinned_committed_tree.action_nodes["river"]) == (821_142, 686_686)
        assert tuple(pinned_committed_tree.slots) == (1_886_176, 1_751_279)

    def test_the_pin_s_rule_builds_the_pin_s_small_blind_tree(
        self, tree, pinned_small_blind_tree
    ) -> None:
        assert pinned_small_blind_tree.nodes == 4_109_130
        assert tuple(pinned_small_blind_tree.action_nodes["turn"]) == (3_528, 3_038)
        assert tuple(pinned_small_blind_tree.action_nodes["river"]) == (854_756, 722_701)
        assert tuple(pinned_small_blind_tree.slots) == (1_975_258, 1_842_713)
        build = owed(tree, "build_tree_figures")
        assert build(5.0, 97.5, **PIN).nodes == 4_109_130
        assert build(5.5, 97.5, **PIN).nodes == 3_921_411

    def test_the_pin_s_rule_closes_on_the_pin_s_counts(
        self, tree, pinned_committed_tree, pinned_small_blind_tree
    ) -> None:
        closure = owed(tree, "closure_counts")
        river = owed(tree, "river_tree_points")
        unreachable = owed(tree, "unreachable_river_points")

        assert dict(closure(pinned_committed_tree)) == {"flop": 14, "turn": 6_419}
        assert river(pinned_committed_tree) == 1_477_056 == 628 * 49 * 48
        assert unreachable(pinned_committed_tree) == 30_772 == 628 * 49
        assert dict(closure(pinned_small_blind_tree)) == {"flop": 14, "turn": 6_566}
        assert river(pinned_small_blind_tree) == 1_545_264
        assert unreachable(pinned_small_blind_tree) == 32_193

    @pytest.mark.parametrize("line", [SMALL_BLIND_LINE, COMMITTED_LINE])
    def test_the_rules_differ_only_on_the_river(self, tree, line) -> None:
        """A checked-through turn clearing the initiative gives out of position a lead on the
        river and nothing earlier: the flop and the turn are built the same under both rules,
        and the river grows for both seats - the seat that may now lead, and the seat that
        answers it."""
        build = owed(tree, "line_tree_figures")
        new, old = build(line), build(line, **PIN)
        closure = owed(tree, "closure_counts")
        river = owed(tree, "river_tree_points")

        assert tuple(new.action_nodes["flop"]) == tuple(old.action_nodes["flop"])
        assert tuple(new.action_nodes["turn"]) == tuple(old.action_nodes["turn"])
        assert all(
            n > o for n, o in zip(new.action_nodes["river"], old.action_nodes["river"], strict=True)
        )
        assert new.nodes > old.nodes
        assert closure(new)["flop"] == closure(old)["flop"] == 14
        assert closure(new)["turn"] == closure(old)["turn"]
        assert river(new) > river(old)

    def test_each_river_card_gains_the_same_count_on_every_card(self, tree) -> None:
        """628 a river card on the pin's committed tree, 659 on the clone's, 31 more; 657 and
        689 on the small blind's, 32 more."""
        river = owed(tree, "river_tree_points")
        build = owed(tree, "line_tree_figures")

        assert river(build(COMMITTED_LINE, **PIN)) == 628 * 49 * 48
        assert river(build(COMMITTED_LINE)) == 659 * 49 * 48
        assert river(build(SMALL_BLIND_LINE, **PIN)) == 657 * 49 * 48
        assert river(build(SMALL_BLIND_LINE)) == 689 * 49 * 48


# --------------------------------------------------------------------------- #
# What one solve closes
# --------------------------------------------------------------------------- #


class TestOneSolveClosesTheFlopAndTheTurnForBothSeats:
    """Criterion: a solved board closes, for both seats, on the flop and the turn: on the committed
    line one flop's solve holds 14 flop and 6,419 turn decision points, 131 for each of 49 turn
    cards. The river is not stored (decision 1, re-ruled 2026-10-04) but the solve still builds and
    holds it: 1,549,968 reachable river decision points, 659 for each of 49 turn and 48 river cards,
    and 32,291 more under the card the turn already dealt, which can never occur. Those stay pinned
    as tree figures. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`."""

    def test_the_committed_line_closes_on_these_counts(self, tree, committed_tree) -> None:
        counts = owed(tree, "closure_counts")(committed_tree)

        assert dict(counts) == {"flop": 14, "turn": 6_419}

    def test_the_closure_holds_no_river(self, tree, committed_tree, small_blind_tree) -> None:
        """What is stored is what closes; a closure with a river key is a river someone keeps."""
        for figures in (committed_tree, small_blind_tree):
            assert "river" not in owed(tree, "closure_counts")(figures)

    def test_the_counts_are_per_card_figures_times_the_cards(self, tree, committed_tree) -> None:
        counts = owed(tree, "closure_counts")(committed_tree)

        assert counts["turn"] == 131 * 49
        assert owed(tree, "river_tree_points")(committed_tree) == 1_549_968 == 659 * 49 * 48

    def test_the_river_under_the_dealt_turn_card_is_counted_apart(
        self, tree, committed_tree
    ) -> None:
        unreachable = owed(tree, "unreachable_river_points")(committed_tree)
        river = owed(tree, "river_tree_points")(committed_tree)

        assert unreachable == 32_291 == 659 * 49
        assert river + unreachable == sum(committed_tree.action_nodes["river"])

    def test_the_small_blind_line_closes_on_its_own_counts(self, tree, small_blind_tree) -> None:
        counts = owed(tree, "closure_counts")(small_blind_tree)

        assert dict(counts) == {"flop": 14, "turn": 6_566}
        assert counts["turn"] == 134 * 49
        assert owed(tree, "river_tree_points")(small_blind_tree) == 1_620_528 == 689 * 49 * 48
        assert owed(tree, "unreachable_river_points")(small_blind_tree) == 33_761 == 689 * 49


# --------------------------------------------------------------------------- #
# The planned arena, per flop
# --------------------------------------------------------------------------- #


class TestThePortReproducesEveryPlannedArenaOnRecord:
    """The validation `nodes.py` passed at stage 1, now a test: all four committed boards'
    planned arenas, to the byte, from the committed line's ranges and the pin's tree they were
    solved on - and the same four on the clone's tree, which their re-solve runs on."""

    @pytest.mark.parametrize("board", sorted(CLONE_ARENA_BYTES))
    def test_the_server_arena_of_each_committed_board_on_the_clone(self, tree, board) -> None:
        assert owed(tree, "planned_arena_for")(COMMITTED_LINE, board) == CLONE_ARENA_BYTES[board]

    @pytest.mark.parametrize("board", sorted(SERVER_ARENA_BYTES))
    def test_the_server_arena_of_each_committed_board_on_the_pin(self, tree, board) -> None:
        planned = owed(tree, "planned_arena_for")(COMMITTED_LINE, board, **PIN)

        assert planned == SERVER_ARENA_BYTES[board]

    @pytest.mark.parametrize("board", sorted(PHASE_16_RECORDED_ARENA_BYTES))
    def test_phase_16_s_recorded_arena_of_each_board_to_the_byte(self, tree, board) -> None:
        planned = owed(tree, "planned_arena_for")(COMMITTED_LINE, board, **PIN)

        assert phase_16_reading(planned) == PHASE_16_RECORDED_ARENA_BYTES[board]

    def test_the_one_record_git_holds_is_the_figure_above(self) -> None:
        """Ties the constant to a committed file: the deep run solved `9c8c7c` on the same
        configuration, on the pin's tree, and committed its planned arena."""
        deep = json.loads((POSTFLOP_DIR / "deep_convergence_check.json").read_text("utf-8"))

        assert deep["deep_run"]["arena_bytes"] == PHASE_16_RECORDED_ARENA_BYTES[("9c", "8c", "7c")]

    def test_live_combos_drop_every_combo_the_board_blocks(self, tree) -> None:
        live = owed(tree, "live_combos")

        assert live({"AA": 1.0}, ("Ah", "7d", "2c")) == 3
        # 72o: three sevens left times three deuces left is nine, less 7h2h and 7s2s, suited.
        assert live({"AKs": 1.0, "72o": 1.0}, ("Ah", "7d", "2c")) == 3 + 7
        assert live({"AA": 1.0, "KK": 1.0}, ()) == 12

    def test_the_arena_is_eight_bytes_a_slot_per_live_combo(
        self, tree, committed_tree, pinned_committed_tree
    ) -> None:
        arena = owed(tree, "planned_arena_bytes")

        assert arena(committed_tree, 346, 447) == (1_987_018 * 346 + 1_873_730 * 447) * 8
        assert arena(committed_tree, 346, 447) == CLONE_ARENA_BYTES[("9c", "8c", "7c")]
        assert arena(pinned_committed_tree, 346, 447) == (1_886_176 * 346 + 1_751_279 * 447) * 8

    def test_gtopen_s_card_memory_estimate(self, tree, committed_tree) -> None:
        """`vram_mb`: `nodes * (oop + ip + max) * 4 + entries * 8 + 512 MiB`."""
        vram = owed(tree, "vram_estimate_bytes")

        expected = 4_144_704 * (346 + 447 + 447) * 4 + 12_200_524_304 + 512 * 1024 * 1024
        assert vram(committed_tree, 346, 447) == expected == 33_295_127_056

    def test_gtopen_s_card_memory_estimate_on_the_pin_s_tree(
        self, tree, pinned_committed_tree
    ) -> None:
        vram = owed(tree, "vram_estimate_bytes")

        expected = 3_921_411 * (346 + 447 + 447) * 4 + 11_483_508_872 + 512 * 1024 * 1024
        assert vram(pinned_committed_tree, 346, 447) == expected


# --------------------------------------------------------------------------- #
# The memory bar: the largest planned arena over every flop of every admitted line
# --------------------------------------------------------------------------- #

ADMITTED_LINES = (SMALL_BLIND_LINE, COMMITTED_LINE, *LATE_LINES)


@pytest.fixture(scope="module")
def line_bars(tree):
    bar = owed(tree, "line_memory_bar")
    return {line: bar(line) for line in ADMITTED_LINES}


@pytest.fixture(scope="module")
def pinned_line_bars(tree):
    bar = owed(tree, "line_memory_bar")
    return {line: bar(line, **PIN) for line in ADMITTED_LINES}


DEUCE_TRIPS = ("2c", "2d", "2h")


class TestTheMemoryBar:
    """Criterion: the memory bar is the largest planned arena over every flop of every admitted
    line, computed before any candidate is ranked. For the committed line, over all 22,100 flops
    on the clone's tree, 13,042,185,280 bytes, 13.68 GB as the driver reads it, on `2d2h2s` - a
    dressing of the deuce-trips class, which is where both ranges lose the fewest combos - and
    35,645,460,288 bytes of card memory by GTOpen's estimate."""

    def test_the_committed_line_bar_is_on_deuce_trips(self, line_bars) -> None:
        bar = line_bars[COMMITTED_LINE]

        assert bar.board == isomorphism.canonical_board(("2d", "2h", "2s")) == DEUCE_TRIPS
        assert bar.arena_bytes == 13_042_185_280

    def test_the_committed_line_bar_is_the_contract_s_figure_as_the_driver_reads_it(
        self, line_bars
    ) -> None:
        assert round(phase_16_reading(line_bars[COMMITTED_LINE].arena_bytes) / 1e9, 2) == 13.68

    def test_the_committed_line_bar_needs_gtopen_s_estimate_of_card_memory(self, line_bars) -> None:
        assert line_bars[COMMITTED_LINE].vram_bytes == 35_645_460_288
        assert round(line_bars[COMMITTED_LINE].vram_bytes / 1e9, 1) == 35.6

    @pytest.mark.parametrize(
        ("line", "arena", "vram"),
        [
            (SMALL_BLIND_LINE, 18_710_513_792, 51_239_107_576),
            (COMMITTED_LINE, 13_042_185_280, 35_645_460_288),
            ("CO:raise@2.5,BB:call", 10_595_705_120, 28_225_335_328),
            ("HJ:raise@2.5,BB:call", 9_660_897_216, 26_163_167_936),
            ("LJ:raise@2.5,BB:call", 7_715_569_200, 20_835_761_456),
        ],
    )
    def test_each_admitted_line_has_its_own_bar(self, line_bars, line, arena, vram) -> None:
        """Re-derived per line from its own tree and its own chart ranges. Every line's largest
        flop is the deuce-trips class. The card memory is pinned to the byte because it is the
        hard limit a GPU must hold: a port that takes the node count from the button's tree for
        the small blind's line gives 49,802,142,592, under a 48 GiB card, and wrong. The small
        blind's own tree, 4,339,626 nodes, gives 51,239,107,576 (47.72 GiB), within 0.3 GB of a
        48 GiB card before CUDA's own use."""
        assert line_bars[line].arena_bytes == arena
        assert line_bars[line].vram_bytes == vram
        assert line_bars[line].board == DEUCE_TRIPS

    @pytest.mark.parametrize(
        ("line", "arena", "vram"),
        [
            (SMALL_BLIND_LINE, 17_674_107_736, 48_503_485_008),
            (COMMITTED_LINE, 12_274_575_976, 33_689_039_052),
            ("CO:raise@2.5,BB:call", 9_983_334_872, 26_692_104_748),
            ("HJ:raise@2.5,BB:call", 9_108_225_432, 24_750_371_516),
            ("LJ:raise@2.5,BB:call", 7_271_691_528, 19_713_966_236),
        ],
    )
    def test_each_line_s_bar_on_the_pin_s_tree(self, pinned_line_bars, line, arena, vram) -> None:
        """The bars this file pinned before decision 17, kept as the pin's record: on that tree
        the committed line's bar read 12.87 GB as phase 16 read it, and the small blind's card
        memory was 48,503,485,008, recomputed twice, independently, on 2026-09-26."""
        assert pinned_line_bars[line].arena_bytes == arena
        assert pinned_line_bars[line].vram_bytes == vram
        assert pinned_line_bars[line].board == DEUCE_TRIPS
        if line == COMMITTED_LINE:
            assert round(phase_16_reading(arena) / 1e9, 2) == 12.87

    def test_the_campaign_bar_is_the_largest_line_bar(self, tree, line_bars) -> None:
        bar = owed(tree, "campaign_memory_bar")()

        assert bar.line == SMALL_BLIND_LINE
        assert bar.arena_bytes == max(found.arena_bytes for found in line_bars.values())
        assert bar.arena_bytes == 18_710_513_792
        assert bar.vram_bytes == 51_239_107_576

    def test_the_campaign_bar_on_the_pin_s_tree(self, tree) -> None:
        bar = owed(tree, "campaign_memory_bar")(**PIN)

        assert bar.line == SMALL_BLIND_LINE
        assert bar.arena_bytes == 17_674_107_736
        assert bar.vram_bytes == 48_503_485_008

    def test_flops_planned_above_the_largest_committed_board(self, tree) -> None:
        """The contract counts flops at or above `8c8d3c`'s planned arena on the clone's tree:
        3,484 of 22,100, or 15.8 percent. Strictly above it is 3,444, or 15.6 percent, because
        40 flops plan exactly the arena `8c8d3c` does. Both are pinned so the function's edge is
        not a choice. The pin's tree, against the pin's arena for the same board, measured the
        same two counts on 2026-10-04, and that is kept as the pin's record."""
        above = owed(tree, "flops_planned_above")
        threshold = CLONE_ARENA_BYTES[("8c", "8d", "3c")]

        assert above(COMMITTED_LINE, threshold) == 3_444
        assert above(COMMITTED_LINE, threshold - 1) == 3_484
        assert round(3_484 / ALL_FLOPS * 100, 1) == 15.8
        pinned = SERVER_ARENA_BYTES[("8c", "8d", "3c")]
        assert above(COMMITTED_LINE, pinned, **PIN) == 3_444
        assert above(COMMITTED_LINE, pinned - 1, **PIN) == 3_484


# --------------------------------------------------------------------------- #
# Texture groups over the 1,755 classes
# --------------------------------------------------------------------------- #

GROUP_CLASSES = {
    "rainbow unpaired": 286,
    "two-tone unpaired": 858,
    "rainbow paired": 156,
    "two-tone paired": 156,
    "monotone": 286,
    "trips": 13,
}
GROUP_FLOPS = {
    "rainbow unpaired": 6_864,
    "two-tone unpaired": 10_296,
    "rainbow paired": 1_872,
    "two-tone paired": 1_872,
    "monotone": 1_144,
    "trips": 52,
}
"""Counted over `canonical_board` for every three-card flop, 2026-09-26."""


class TestTheSixTextureGroups:
    """Criterion: the chosen box solves one flop from each of six texture groups and the report
    projects one closed line's cost from those six, weighted by how many of the 1,755 classes each
    group holds. Two-tone unpaired is 858 classes and 46.6 percent of all flops.
    `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL`,
    `THE-COMMITTED-SAMPLE-MISSES-THE-MODAL-FLOP-FAMILY`."""

    def test_the_six_groups_in_the_contract_s_order(self, textures) -> None:
        assert tuple(owed(textures, "TEXTURE_GROUPS")) == tuple(GROUP_CLASSES)

    def test_the_classes_each_group_holds(self, textures) -> None:
        counts = owed(textures, "group_class_counts")()

        assert dict(counts) == GROUP_CLASSES
        assert sum(counts.values()) == isomorphism.CANONICAL_FLOP_CLASSES

    def test_the_flops_each_group_holds(self, textures) -> None:
        counts = owed(textures, "group_flop_counts")()

        assert dict(counts) == GROUP_FLOPS
        assert sum(counts.values()) == ALL_FLOPS
        assert round(counts["two-tone unpaired"] / ALL_FLOPS * 100, 1) == 46.6

    @pytest.mark.parametrize(
        ("board", "group", "flops"),
        [
            (("Kh", "7d", "2c"), "rainbow unpaired", 24),
            (("8c", "8d", "3c"), "two-tone paired", 12),
            (("9c", "8c", "7c"), "monotone", 4),
            (("Ac", "8c", "3c"), "monotone", 4),
            (("Jd", "6d", "3c"), "two-tone unpaired", 12),
            (("8c", "8d", "3h"), "rainbow paired", 12),
            (DEUCE_TRIPS, "trips", 4),
        ],
    )
    def test_each_board_s_group_and_the_flops_its_class_stands_for(
        self, textures, board, group, flops
    ) -> None:
        assert owed(textures, "texture_group")(board) == group
        assert owed(textures, "flops_in_class")(board) == flops

    def test_a_group_is_a_property_of_the_class_not_the_dressing(self, textures) -> None:
        group = owed(textures, "texture_group")
        deck = [rank + suit for rank in "23456789TJQKA" for suit in "cdhs"]
        for board in itertools.islice(itertools.combinations(deck, 3), 0, None, 97):
            assert group(board) == group(isomorphism.canonical_board(board)), board

    def test_the_projection_weights_each_group_by_its_classes(self, textures) -> None:
        project = owed(textures, "project_line_cost")

        assert project(dict.fromkeys(GROUP_CLASSES, 1.0)) == pytest.approx(1_755.0)
        costs = dict.fromkeys(GROUP_CLASSES, 0.0) | {"two-tone unpaired": 2.0, "trips": 10.0}
        assert project(costs) == pytest.approx(858 * 2.0 + 13 * 10.0)

    def test_a_projection_missing_a_group_is_refused(self, textures) -> None:
        """Five groups priced is not a line priced. The one most likely to be missing is the one
        no solve has ever timed."""
        costs = dict.fromkeys(GROUP_CLASSES, 1.0)
        del costs["two-tone unpaired"]

        with pytest.raises((KeyError, ValueError)):
            owed(textures, "project_line_cost")(costs)
