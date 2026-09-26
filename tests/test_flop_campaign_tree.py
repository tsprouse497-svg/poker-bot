"""Phase 21, stage 4: the tree a line builds, what one solve closes, and the memory bar.

Authored from the contract before any implementation exists; see the head of
`tests/test_flop_campaign_threads.py` for how the missing modules are reached.

**Every figure is GTOpen's own tree rule, re-derived.** `crates/solver/src/tree.rs`
(`legal_actions`, `apply_action`, `street_end`, lines 432-760) builds the tree a flop solve holds,
and the arena it plans is `entries * 8` bytes at full precision, where `entries` is each seat's
action slots times that seat's live combos. The tree's shape depends on the pot, the stack and the
menu and never on the board; the board only removes combos. So one tree per line and a combo count
per flop is the whole walk over 22,100 flops, and none of it needs a solver.

**The four planned arenas phase 16 recorded are the check the port has to pass to the byte.** Each
object's `solve.arena_bytes` was written through `arena_bytes` in `postflop_transport`, which reads
the server's decimal `arena_mb` as 2^20-byte megabytes. That reading is decision 14's, and it is
`runtime-reversible` only while no frozen test pins it - so the test below re-applies the reading
phase 16 used, in its own arithmetic, to reproduce phase 16's records. It says nothing about which
reading the driver uses from here on. The `9c8c7c` figure is committed in
`data/artifacts/postflop/deep_convergence_check.json`; the other three are in the four objects
under `~/poker-bot-solve-objects/postflop`, read on 2026-09-26, which git does not hold.
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

PHASE_16_RECORDED_ARENA_BYTES = {
    ("9c", "8c", "7c"): 12_041_331_798,
    ("Kh", "7d", "2c"): 11_978_042_234,
    ("8c", "8d", "3c"): 12_236_838_500,
    ("Ac", "8c", "3c"): 11_598_324_830,
}
"""Each object's `solve.arena_bytes`, as phase 16 wrote it through the 2^20 reading."""

SERVER_ARENA_BYTES = {
    ("9c", "8c", "7c"): 11_483_508_872,
    ("Kh", "7d", "2c"): 11_423_151_240,
    ("8c", "8d", "3c"): 11_669_958_592,
    ("Ac", "8c", "3c"): 11_061_024_504,
}
"""The same four in the server's own unit, `entries * 8`: 346 and 447 live combos on `9c8c7c`,
342 and 447 on `Kh7d2c`, 350 and 456 on `8c8d3c`, 331 and 433 on `Ac8c3c`."""


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


# --------------------------------------------------------------------------- #
# The tree a line builds
# --------------------------------------------------------------------------- #


class TestTheCommittedLineBuildsTheTreeTheRecordMeasured:
    """The committed line and menu, pot 5.5 and 97.5 behind: 3,921,411 nodes and 1,514,261
    decision points, 14 on the flop (seven per seat), 131 on each of 49 turns and 628 on each
    river GTOpen builds under them."""

    def test_the_node_and_decision_point_totals(self, committed_tree) -> None:
        assert committed_tree.nodes == 3_921_411
        assert sum(sum(pair) for pair in committed_tree.action_nodes.values()) == 1_514_261

    def test_the_decision_points_per_street_and_seat_as_built(self, committed_tree) -> None:
        """Out of position first in each pair. The river is as `tree.rs` builds it, with the
        subtree under the already-dealt turn card still in its slot."""
        assert tuple(committed_tree.action_nodes["flop"]) == (7, 7)
        assert tuple(committed_tree.action_nodes["turn"]) == (3_430, 2_989)
        assert tuple(committed_tree.action_nodes["river"]) == (821_142, 686_686)

    def test_the_action_slots_that_size_the_arena(self, committed_tree) -> None:
        assert tuple(committed_tree.slots) == (1_886_176, 1_751_279)

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
        assert small_blind_tree.nodes == 4_109_130

    def test_the_decision_points_per_street_and_seat_as_built(self, small_blind_tree) -> None:
        assert tuple(small_blind_tree.action_nodes["flop"]) == (7, 7)
        assert tuple(small_blind_tree.action_nodes["turn"]) == (3_528, 3_038)
        assert tuple(small_blind_tree.action_nodes["river"]) == (854_756, 722_701)

    def test_the_action_slots(self, small_blind_tree) -> None:
        assert tuple(small_blind_tree.slots) == (1_975_258, 1_842_713)

    def test_the_pot_is_read_off_the_line_and_not_assumed(self, tree) -> None:
        build = owed(tree, "build_tree_figures")

        assert build(5.0, 97.5).nodes == 4_109_130
        assert build(5.5, 97.5).nodes == 3_921_411


# --------------------------------------------------------------------------- #
# What one solve closes
# --------------------------------------------------------------------------- #


class TestOneSolveClosesEveryStreetForBothSeats:
    """Criterion: on the committed line one flop's solve holds 14 flop, 6,419 turn and 1,477,056
    reachable river decision points, 628 for each of 49 turn and 48 river cards; `tree.rs` also
    builds a river under the card the turn already dealt, 30,772 more, which can never occur and
    are not kept. `A-SAMPLE-WHOSE-SITUATIONS-DO-NOT-CLOSE-VOIDS-THE-FLOP-NOT-THE-TURN`."""

    def test_the_committed_line_closes_on_these_counts(self, tree, committed_tree) -> None:
        counts = owed(tree, "closure_counts")(committed_tree)

        assert dict(counts) == {"flop": 14, "turn": 6_419, "river": 1_477_056}

    def test_the_counts_are_per_card_figures_times_the_cards(self, tree, committed_tree) -> None:
        counts = owed(tree, "closure_counts")(committed_tree)

        assert counts["turn"] == 131 * 49
        assert counts["river"] == 628 * 49 * 48

    def test_the_river_under_the_dealt_turn_card_is_counted_and_not_kept(
        self, tree, committed_tree
    ) -> None:
        unreachable = owed(tree, "unreachable_river_points")(committed_tree)
        counts = owed(tree, "closure_counts")(committed_tree)

        assert unreachable == 30_772 == 628 * 49
        assert counts["river"] + unreachable == sum(committed_tree.action_nodes["river"])

    def test_the_small_blind_line_closes_on_its_own_counts(self, tree, small_blind_tree) -> None:
        counts = owed(tree, "closure_counts")(small_blind_tree)

        assert dict(counts) == {"flop": 14, "turn": 6_566, "river": 1_545_264}
        assert owed(tree, "unreachable_river_points")(small_blind_tree) == 32_193


# --------------------------------------------------------------------------- #
# The planned arena, per flop
# --------------------------------------------------------------------------- #


class TestThePortReproducesEveryPlannedArenaOnRecord:
    """The validation `nodes.py` passed at stage 1, now a test: all four committed boards'
    planned arenas, to the byte, from the committed line's ranges and tree."""

    @pytest.mark.parametrize("board", sorted(SERVER_ARENA_BYTES))
    def test_the_server_arena_of_each_committed_board(self, tree, board) -> None:
        assert owed(tree, "planned_arena_for")(COMMITTED_LINE, board) == SERVER_ARENA_BYTES[board]

    @pytest.mark.parametrize("board", sorted(PHASE_16_RECORDED_ARENA_BYTES))
    def test_phase_16_s_recorded_arena_of_each_board_to_the_byte(self, tree, board) -> None:
        planned = owed(tree, "planned_arena_for")(COMMITTED_LINE, board)

        assert phase_16_reading(planned) == PHASE_16_RECORDED_ARENA_BYTES[board]

    def test_the_one_record_git_holds_is_the_figure_above(self) -> None:
        """Ties the constant to a committed file: the deep run solved `9c8c7c` on the same
        configuration and committed its planned arena."""
        deep = json.loads((POSTFLOP_DIR / "deep_convergence_check.json").read_text("utf-8"))

        assert deep["deep_run"]["arena_bytes"] == PHASE_16_RECORDED_ARENA_BYTES[("9c", "8c", "7c")]

    def test_live_combos_drop_every_combo_the_board_blocks(self, tree) -> None:
        live = owed(tree, "live_combos")

        assert live({"AA": 1.0}, ("Ah", "7d", "2c")) == 3
        # 72o: three sevens left times three deuces left is nine, less 7h2h and 7s2s, suited.
        assert live({"AKs": 1.0, "72o": 1.0}, ("Ah", "7d", "2c")) == 3 + 7
        assert live({"AA": 1.0, "KK": 1.0}, ()) == 12

    def test_the_arena_is_eight_bytes_a_slot_per_live_combo(self, tree, committed_tree) -> None:
        arena = owed(tree, "planned_arena_bytes")

        assert arena(committed_tree, 346, 447) == (1_886_176 * 346 + 1_751_279 * 447) * 8

    def test_gtopen_s_card_memory_estimate(self, tree, committed_tree) -> None:
        """`vram_mb`: `nodes * (oop + ip + max) * 4 + entries * 8 + 512 MiB`."""
        vram = owed(tree, "vram_estimate_bytes")

        expected = 3_921_411 * (346 + 447 + 447) * 4 + 11_483_508_872 + 512 * 1024 * 1024
        assert vram(committed_tree, 346, 447) == expected


# --------------------------------------------------------------------------- #
# The memory bar: the largest planned arena over every flop of every admitted line
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def line_bars(tree):
    bar = owed(tree, "line_memory_bar")
    return {line: bar(line) for line in (SMALL_BLIND_LINE, COMMITTED_LINE, *LATE_LINES)}


DEUCE_TRIPS = ("2c", "2d", "2h")


class TestTheMemoryBar:
    """Criterion: the memory bar is the largest planned arena over every flop of every admitted
    line, computed before any candidate is ranked. For the committed line, over all 22,100 flops,
    12.87 GB as the driver read it on `2d2h2s` - a dressing of the deuce-trips class, which is
    where both ranges lose the fewest combos - and 33.7 GB of card memory by GTOpen's estimate."""

    def test_the_committed_line_bar_is_on_deuce_trips(self, line_bars) -> None:
        bar = line_bars[COMMITTED_LINE]

        assert bar.board == isomorphism.canonical_board(("2d", "2h", "2s")) == DEUCE_TRIPS
        assert bar.arena_bytes == 12_274_575_976

    def test_the_committed_line_bar_is_the_contract_s_figure_as_phase_16_read_it(
        self, line_bars
    ) -> None:
        assert round(phase_16_reading(line_bars[COMMITTED_LINE].arena_bytes) / 1e9, 2) == 12.87

    def test_the_committed_line_bar_needs_gtopen_s_estimate_of_card_memory(self, line_bars) -> None:
        assert line_bars[COMMITTED_LINE].vram_bytes == 33_689_039_052
        assert round(line_bars[COMMITTED_LINE].vram_bytes / 1e9, 1) == 33.7

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
    def test_each_admitted_line_has_its_own_bar(self, line_bars, line, arena, vram) -> None:
        """Re-derived per line from its own tree and its own chart ranges. Every line's largest
        flop is the deuce-trips class. The card memory is pinned to the byte because it is the
        hard limit a GPU must hold: a port that takes the node count from the button's tree for
        the small blind's line gives 47,119,620,540, which is within a rounding of the
        contract's "about 47.2 GB" and wrong. The contract's 47.2 does not reproduce; the small
        blind's own tree, 4,109,130 nodes, gives 48,503,485,008 (45.17 GiB), recomputed twice,
        independently, on 2026-09-26."""
        assert line_bars[line].arena_bytes == arena
        assert line_bars[line].vram_bytes == vram
        assert line_bars[line].board == DEUCE_TRIPS

    def test_the_campaign_bar_is_the_largest_line_bar(self, tree, line_bars) -> None:
        bar = owed(tree, "campaign_memory_bar")()

        assert bar.line == SMALL_BLIND_LINE
        assert bar.arena_bytes == max(found.arena_bytes for found in line_bars.values())
        assert bar.vram_bytes == 48_503_485_008

    def test_flops_planned_above_the_largest_committed_board(self, tree) -> None:
        """15.8 percent in the contract counts flops at or above `8c8d3c`'s planned arena: 3,484
        of 22,100. Strictly above it is 3,444, or 15.6 percent, because 40 flops plan exactly
        the arena `8c8d3c` does. Both are pinned so the function's edge is not a choice."""
        above = owed(tree, "flops_planned_above")
        threshold = SERVER_ARENA_BYTES[("8c", "8d", "3c")]

        assert above(COMMITTED_LINE, threshold) == 3_444
        assert above(COMMITTED_LINE, threshold - 1) == 3_484
        assert round(3_484 / ALL_FLOPS * 100, 1) == 15.8


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
