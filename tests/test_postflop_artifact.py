"""Phase 16, stage 4: what the committed solve owes, and what gets committed.

Authored before any implementation exists, from
`docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` alone. Modules stage 6 has not written are
reached through fixtures whose import sits in the function body; see the note at the head of
`tests/test_postflop_key.py` for why, and `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` for what it
costs when that is tidied away.

**What the repo commits is an index plus a three-flop sample, not the artifact the bot plays.**
Decision 6 ruled that the solve output lives in object storage outside git, so every byte figure
here measures the index and the sample. Nothing in this file fetches anything: the gate must pass
with no GTOpen, no Rust toolchain, no network and no fetched solve object.

**The third sample board is this stage's one choice and it is `8h8d3h`.** Decision 6 item 4 freezes
the texture and rank splits and names `Kc7d2h` (rainbow, dry-high) and `9c8c7c` (monotone,
connected) outright, leaving stage 4 the two-tone paired cell and nothing else. `8h8d3h` is
two-tone - two hearts and one diamond - and paired. Paired-monotone is impossible, which
`test_the_ruled_three_by_three_assignment_has_exactly_one_forbidden_cell` recomputes rather than
quotes.

**No figure here is a per-weight rate that includes non-weight bytes.** That is the error the
stage-1 numbers review held this phase over: a rate computed as whole-file bytes over weight count
charges per-spot blocks against every weight. Where this file checks a published rate it checks it
against the bytes on disk.
"""

from __future__ import annotations

import itertools
import json
import re
from pathlib import Path

import pytest

from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from scripts.repo_paths import REPO_ROOT

ARTIFACT_ROOT = REPO_ROOT / "data" / "artifacts"
PREFLOP_DIR = ARTIFACT_ROOT / "preflop"
POSTFLOP_DIR = ARTIFACT_ROOT / "postflop"
INDEX_PATH = POSTFLOP_DIR / "index.json"
SAMPLE_DIR = POSTFLOP_DIR / "sample"
SOLVE_CONFIG_PATH = POSTFLOP_DIR / "solve_config.json"

ARTIFACT_BYTE_CAP = 20 * 1024 * 1024
"""`DIRECTORY_BYTE_LIMITS` in `scripts/check_file_sizes.py`, restated so a red here says which
budget moved. The contract forbids raising it and forbids slipping under it with git LFS, whose
pointer would pass the byte budget vacuously on an unfetched clone."""

EXPLOITABILITY_TARGET_PCT = 0.3
EXPLOITABILITY_CEILING_PCT = 1.0
ITERATION_CAP = 1200

RANGE_WEIGHT_FLOOR = 0.01

SAMPLE_BOARDS = {
    "rainbow-dry-high": ("Kh", "7d", "2c"),
    "two-tone-paired": ("8c", "8d", "3c"),
    "monotone-connected": ("9c", "8c", "7c"),
}
"""Two ruled by decision 6 item 4, one picked here inside the split it left open, all three in the
canonical dressing - Taylor 2026-09-15, whose amendment to item 4 carries why."""

RANKS = "23456789TJQKA"
SUITS = "cdhs"
ALL_CARDS = tuple(rank + suit for rank in RANKS for suit in SUITS)

HEX16 = re.compile(r"\A[0-9a-f]{16}\Z")
HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")

PLACEHOLDERS = {"", "TBD", "tbd", "TODO", "todo", "none", "None", "n/a", "N/A", "0" * 16}


@pytest.fixture(scope="module")
def artifact_module():
    """`solver_artifacts.postflop_artifact`: the schema, the strict importer and the library."""
    import poker_training_bot.solver_artifacts.postflop_artifact as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 16's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def load(path: Path):
    assert path.is_file(), (
        f"{path.relative_to(REPO_ROOT)} is missing, so the committed solve owes everything this"
        " file checks and has delivered none of it"
    )
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def index():
    return load(INDEX_PATH)


@pytest.fixture(scope="module")
def entries(index):
    found = index.get("entries")
    assert found, "the committed index must list one entry per solved spot"
    return found


def texture(board) -> str:
    suits = {card[1] for card in board}
    return {1: "monotone", 2: "two-tone", 3: "rainbow"}[len(suits)]


def rank_structure(board) -> str:
    ranks = [card[0] for card in board]
    if len(set(ranks)) == 1:
        return "trips"
    if len(set(ranks)) == 2:
        return "paired"
    order = sorted(RANKS.index(rank) for rank in ranks)
    if order[2] - order[0] <= 4:
        return "connected"
    return "unpaired-spread"


# --------------------------------------------------------------------------- #
# The index
# --------------------------------------------------------------------------- #


class TestEveryIndexEntryCarriesItsEvidence:
    """Criterion: every entry records the achieved exploitability as a percent of the starting
    pot, the iteration count, the strategy digest and the digest of the stored object, and a test
    fails on absence or a placeholder."""

    REQUIRED = (
        "spot_key",
        "achieved_exploitability_pct_of_pot",
        "iterations",
        "strategy_digest",
        "object_digest",
    )

    def test_every_entry_carries_all_four_figures_plus_its_key(self, entries) -> None:
        for entry in entries:
            missing = [name for name in self.REQUIRED if name not in entry]
            assert missing == [], (entry.get("spot_key"), missing)

    def test_no_figure_is_absent_or_a_placeholder(self, entries) -> None:
        """An entry whose digest reads TBD is an entry that authenticates nothing, and it passes
        a presence check."""
        for entry in entries:
            for name in self.REQUIRED:
                value = entry[name]
                assert value is not None, (entry.get("spot_key"), name)
                if isinstance(value, str):
                    assert value.strip() not in PLACEHOLDERS, (entry.get("spot_key"), name)

    def test_the_exploitability_is_a_percent_of_pot_and_not_a_big_blind_figure(
        self, entries
    ) -> None:
        """Phase 10's 0.01bb is preflop and in the wrong unit, and a big-blind criterion will not
        reproduce the measured 220-to-260 iteration counts. The field name says percent of pot and
        the values have to be readable as one."""
        for entry in entries:
            value = entry["achieved_exploitability_pct_of_pot"]
            assert isinstance(value, int | float) and not isinstance(value, bool)
            assert 0.0 <= value <= EXPLOITABILITY_CEILING_PCT, entry["spot_key"]

    def test_no_committed_cell_sits_above_one_percent_of_pot(self, entries) -> None:
        """1% is the worst a played cell may carry. A cap-bound cell above it is refused, not
        committed."""
        over = [
            entry["spot_key"]
            for entry in entries
            if entry["achieved_exploitability_pct_of_pot"] > EXPLOITABILITY_CEILING_PCT
        ]

        assert over == []

    def test_no_committed_cell_ran_past_the_iteration_cap(self, entries) -> None:
        for entry in entries:
            assert 0 < entry["iterations"] <= ITERATION_CAP, entry["spot_key"]

    def test_the_digest_width_is_declared_rather_than_assumed(self, index, entries) -> None:
        """Not a byte decision. The repo's 16-hex precedent is a determinism digest compared
        against a rerun; this one authenticates an object fetched from storage the repo does not
        control. 64 bits is ample against accident and about 2^32 work against substitution, which
        is not a security margin - so either take the full sha256 or say in the file that it
        authenticates against accident only."""
        widths = {len(entry["object_digest"]) for entry in entries}
        assert len(widths) == 1, f"one digest width, got {sorted(widths)}"
        width = widths.pop()

        if width == 16:
            assert index.get("digest_authenticates") == "accident-only", (
                "a 16-hex digest is about 2^32 work to forge, so the index has to say in terms"
                " that it authenticates against accident only"
            )
        else:
            assert width == 64, (
                f"a digest is either the repo's 16-hex precedent or a sha256, got {width}"
            )

    def test_every_digest_is_lower_case_hex_of_its_declared_width(self, entries) -> None:
        for entry in entries:
            for name in ("strategy_digest", "object_digest"):
                value = entry[name]
                assert HEX16.match(value) or HEX64.match(value), (entry["spot_key"], name, value)

    def test_the_target_and_the_cap_are_published_by_the_module_not_by_this_test(
        self, artifact_module
    ) -> None:
        assert owed(artifact_module, "EXPLOITABILITY_TARGET_PCT_OF_POT") == pytest.approx(
            EXPLOITABILITY_TARGET_PCT
        )
        assert owed(artifact_module, "EXPLOITABILITY_CEILING_PCT_OF_POT") == pytest.approx(
            EXPLOITABILITY_CEILING_PCT
        )
        assert owed(artifact_module, "SOLVE_ITERATION_CAP") == ITERATION_CAP


class TestTheIndexHeader:
    """Criterion: the covered set of preflop lines is committed explicitly, so a refusal names a
    line that was excluded rather than one that was forgotten; and the count of cells the campaign
    solved and rejected above 1% of pot is carried in the committed index's header."""

    def test_the_covered_preflop_lines_are_listed_explicitly(self, index) -> None:
        covered = index.get("covered_preflop_lines")

        assert covered, (
            "the covered set is committed rather than inferred from which keys happen to be"
            " present; a refusal has to name a line that was excluded, not one that was forgotten"
        )
        assert len(set(covered)) == len(covered)

    def test_every_entry_s_line_is_one_of_the_declared_covered_lines(self, index, entries) -> None:
        covered = set(index["covered_preflop_lines"])
        stray = sorted(
            {
                entry["preflop_line"]
                for entry in entries
                if entry.get("preflop_line") not in covered
            }
        )

        assert stray == []

    def test_the_header_says_which_constraint_bound_the_line_count(self, index) -> None:
        """How many lines are covered is an output rather than a choice: as many as the campaign
        cost and the index each afford, whichever is smaller. Both bind, and an earlier draft of
        decision 6 item 7 said only one did."""
        bound = index.get("line_count_bound_by")

        assert bound in {"campaign-cost", "index-bytes"}, (
            "the index has to name which of the two constraints decided the covered line count"
        )

    def test_the_header_carries_the_count_of_cells_rejected_above_one_percent(self, index) -> None:
        """The phase's headline cost result. Knowable at report time and not at query time, which
        is why it is a header figure rather than a third refusal cause."""
        rejected = index.get("cells_solved_and_rejected_above_one_percent")

        assert isinstance(rejected, int) and not isinstance(rejected, bool)
        assert rejected >= 0

    def test_the_header_declares_the_object_storage_the_index_points_at(self, index) -> None:
        """No git LFS, and the bytes live outside git. A reader has to be able to tell an index
        entry from a committed sample cell without opening both."""
        assert index.get("object_storage"), (
            "the index points at objects the repo does not hold, and it has to say where"
        )


# --------------------------------------------------------------------------- #
# The strict importer
# --------------------------------------------------------------------------- #


def sample_cell(sample_dir: Path) -> tuple[Path, dict]:
    files = sorted(sample_dir.glob("*.json"))
    assert files, f"{sample_dir.relative_to(REPO_ROOT)} holds no committed sample flop"
    return files[0], json.loads(files[0].read_text(encoding="utf-8"))


def a_different_dressing(board: tuple[str, ...]) -> tuple[str, ...]:
    """A different board in the same isomorphism class: relabel the suits.

    A suit permutation never leaves the class and never duplicates a card, so all this needs is
    one that moves the board, which exists for every board. Derived from the cell's own board
    because which texture `sample_cell` returns depends on a glob order stage 6 fixes; the first
    moving permutation is taken, so it is one answer on every run and every committed texture.
    """
    original = tuple(sorted(board))
    for permutation in itertools.permutations(SUITS):
        mapping = dict(zip(SUITS, permutation, strict=True))
        moved = tuple(card[0] + mapping[card[1]] for card in board)
        if tuple(sorted(moved)) != original:
            return moved
    raise AssertionError(f"no suit permutation moves {board}, which no three-card board manages")


class TestTheImporterRefusesRatherThanRenders:
    """Criterion: the key is re-derived at import and at lookup, with a mismatch against the
    stored id refused; a committed size that cannot be played is refused at import rather than at
    the table; and a cell over 1% of pot is refused.

    Each test writes a deliberately wrong file and requires the importer to refuse it. A test that
    only imported the good file would pass against an importer that validates nothing.
    """

    def written(self, tmp_path: Path, payload) -> Path:
        path = tmp_path / "cell.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_the_good_committed_sample_imports(self, artifact_module) -> None:
        """The positive control. Four refusal tests below read "it raised", which an importer that
        refuses everything satisfies."""
        importer = owed(artifact_module, "import_postflop_cell")
        path, _ = sample_cell(SAMPLE_DIR)

        assert importer(path) is not None

    def test_a_stored_id_that_disagrees_with_the_re_derived_key_is_refused(
        self, artifact_module, tmp_path
    ) -> None:
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        payload["spot_key"] = payload["spot_key"] + "x"

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_cell_whose_board_is_not_its_canonical_representative_is_refused(
        self, artifact_module, tmp_path
    ) -> None:
        """The collapse is the only one permitted, so a cell keyed on a non-representative board
        is a second cell for a class that already has one.

        The wrong dressing is a different dress of the **same** class. An earlier draft rewrote
        every card to spades, which changes the texture, so the importer refused on the stored-key
        mismatch the test above proves - and on a monotone cell it could refuse a correct
        implementation. Inside the class the stored `spot_key` still re-derives equal, so the
        non-representative-board check is the only thing here that can refuse.
        """
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        moved = a_different_dressing(tuple(payload["board"]))
        assert sorted(moved) != sorted(payload["board"])
        assert len(set(moved)) == 3, moved
        payload["board"] = list(moved)

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_weight_outside_zero_to_one_is_refused_rather_than_rendered(
        self, artifact_module, tmp_path
    ) -> None:
        """Canary `postflop-weight-bounds-not-enforced` aims at exactly this line. A committed
        weight outside 0 to 1 is not a strategy, and a library that renders one hands the bot a
        frequency no dealer can deal.

        **The witness row sums to exactly 1.0, which is the whole point.** An earlier draft set
        one entry of a summing row to 1.7, breaking bound and sum together, so with this check
        disabled the sum check below still refused the cell and the canary survived the command it
        names - invisible until stage 7, after stage 5 froze file and mutation alike. `1.5 - 0.5`
        is 1.0 with no floating-point residue, unlike `1.7 - 0.7`.
        """
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        row = payload["class_weights"][0]
        assert len(row) >= 2, "a class with one action cannot hold a mixture to break"
        out_of_bounds = [1.5, -0.5, *([0.0] * (len(row) - 2))]
        assert sum(out_of_bounds) == 1.0
        payload["class_weights"][0] = out_of_bounds

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_class_whose_weights_do_not_sum_to_one_is_refused(
        self, artifact_module, tmp_path
    ) -> None:
        """The mirror of the test above, isolating the other check: every entry is inside 0 to 1
        and the row sums to its own length. An earlier draft used a row of `0.5`, which sums to
        exactly 1.0 whenever the cell holds two actions and is then refused by nothing at all.
        """
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        row = payload["class_weights"][0]
        assert len(row) >= 2, "a class with one action cannot hold a mixture to break"
        payload["class_weights"][0] = [1.0] * len(row)

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_committed_size_that_cannot_be_played_is_refused_at_import(
        self, artifact_module, tmp_path
    ) -> None:
        """Criterion, and the second required canary. A size above what the acting seat can put in
        is a legality failure `DecisionAuditRecord` would raise on at the table, in the middle of a
        hand, once. Refused at import it is one red on a file nobody has played yet.

        Inflate a **raise**, never a bet. Decision 14 put the menu check on bets only, because a
        flop raise answers a bet at 2.5x rather than as a fraction of the pot - so an inflated
        bet is refused by the menu one line on and this canary survives the command it names.
        """
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        cells = [json.loads(path.read_text("utf-8")) for path in sorted(SAMPLE_DIR.glob("*.json"))]
        raises = [(c, act) for c in cells for act in c["actions"] if act["action"] == "raise"]
        assert raises, "no committed cell offers a raise, and only a raise reaches this check"
        payload, inflated = raises[0]
        inflated["size_bb"] = payload["effective_stack_bb"] * 10

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_cell_over_one_percent_of_pot_is_refused_at_import(
        self, artifact_module, tmp_path
    ) -> None:
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        payload["achieved_exploitability_pct_of_pot"] = 1.4

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_cell_past_the_iteration_cap_is_refused_at_import(
        self, artifact_module, tmp_path
    ) -> None:
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        payload["iterations"] = ITERATION_CAP + 1

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_a_pot_that_does_not_follow_from_the_substituted_line_is_refused(
        self, artifact_module, tmp_path
    ) -> None:
        """Pot and stack are derived from the substituted preflop line, not from the table being
        asked about, and the substitution is recorded on the committed spot. A cell whose pot does
        not follow from its own line is refused rather than played."""
        importer = owed(artifact_module, "import_postflop_cell")
        error = owed(artifact_module, "PostflopArtifactError")
        _, payload = sample_cell(SAMPLE_DIR)
        payload["pot_bb"] = payload["pot_bb"] + 3.0

        with pytest.raises(error):
            importer(self.written(tmp_path, payload))

    def test_every_committed_cell_records_its_own_price_substitution(self) -> None:
        """Decision 8: the substitution is a fact about which ranges the spot was solved against,
        settled when the solve is committed rather than when a hand is played.

        Counted first, because an empty sample directory satisfies a per-file loop perfectly.
        """
        paths = sorted(SAMPLE_DIR.glob("*.json"))

        # `>= 3` on Taylor's 2026-09-15 amendment to decision 6 item 4; decision 18a. Not `== 3`.
        assert len(paths) >= 3, [path.name for path in paths]
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert "price_substitutions" in payload, path.name


# --------------------------------------------------------------------------- #
# The committed sample
# --------------------------------------------------------------------------- #


class TestTheCommittedSample:
    """Criterion: the committed sample is three flops and its texture and rank splits are frozen.

    `Kc7d2h` and `9c8c7c` are named by decision 6 item 4. `8h8d3h` is stage 4's one pick, inside
    the two-tone paired cell that item leaves and nothing else.
    """

    def test_the_three_boards_are_the_ruled_three(self) -> None:
        """Three flops, counted as boards rather than as files - Taylor allowed a fourth file
        2026-09-15, on a board already here, so item 4's splits are untouched. Absorbs the
        separate file-count test, which this assertion already implies."""
        files = sorted(SAMPLE_DIR.glob("*.json"))
        committed = {
            tuple(json.loads(path.read_text(encoding="utf-8"))["board"]) for path in files
        }

        assert committed == set(SAMPLE_BOARDS.values())
        assert len(files) >= 3, [path.name for path in files]

    def test_each_board_sits_in_the_texture_and_rank_cell_it_was_chosen_for(self) -> None:
        """Checked rather than taken. The stage-3 review found an earlier draft naming two rainbow
        boards among three while its own suit split said otherwise.

        The spread half is folded in here: a frequency-weighted three would be two two-tones and
        reproduce the blind spot the sample exists to remove. Both halves read the same literal
        table, so as two tests they were two names over one assertion.
        """
        for name, wanted in (
            ("rainbow-dry-high", ("rainbow", "unpaired-spread")),
            ("two-tone-paired", ("two-tone", "paired")),
            ("monotone-connected", ("monotone", "connected")),
        ):
            board = SAMPLE_BOARDS[name]
            assert (texture(board), rank_structure(board)) == wanted, name
        assert len({texture(board) for board in SAMPLE_BOARDS.values()}) == 3
        assert len({rank_structure(board) for board in SAMPLE_BOARDS.values()}) == 3

    def test_the_ruled_three_by_three_assignment_has_exactly_one_forbidden_cell(self) -> None:
        """Brute-forced over all 22,100 boards rather than quoted: paired-monotone is impossible,
        because two cards of one rank cannot share a suit. That is the arithmetic that forces the
        monotone slot to be unpaired and leaves stage 4 the two-tone paired cell."""
        cells = {
            (texture(board), rank_structure(board))
            for board in itertools.combinations(ALL_CARDS, 3)
        }

        assert ("monotone", "paired") not in cells
        assert ("monotone", "trips") not in cells
        assert ("two-tone", "paired") in cells
        assert ("rainbow", "paired") in cells

    def test_the_sample_is_not_all_monotone(self) -> None:
        """It cannot be two, and the reason is poker: the phase's entire converged evidence is six
        monotone rows and one two-tone, and monotone generalises worst.
        `POSTFLOP-EVIDENCE-IS-ALL-MONOTONE-AND-MONOTONE-GENERALISES-WORST`."""
        textures = [texture(board) for board in SAMPLE_BOARDS.values()]

        assert textures.count("monotone") == 1


# --------------------------------------------------------------------------- #
# Where it lands, and what it costs
# --------------------------------------------------------------------------- #


class TestWhereTheArtifactLands:
    """Criterion: the artifact does not land in `data/artifacts/preflop/`, because
    `import_preflop_artifacts` globs `*.json` directly under it and would read a postflop file as
    a preflop chart."""

    def test_the_preflop_library_still_imports_and_holds_only_preflop_charts(self) -> None:
        """The pin the contract asks for: the preflop library ignores the postflop tree.

        A sibling asserting `POSTFLOP_DIR` is not under `PREFLOP_DIR` was dropped: both are
        module constants built two lines apart, so it was true whatever any implementation did.
        """
        charts = import_preflop_artifacts(PREFLOP_DIR)

        assert charts
        for chart in charts:
            for spot in chart.spots:
                assert spot.spot_id.startswith("t"), spot.spot_id

    def test_the_postflop_tree_exists_under_its_own_directory(self) -> None:
        assert POSTFLOP_DIR.is_dir()
        assert INDEX_PATH.is_file()
        assert SAMPLE_DIR.is_dir()


class TestTheByteBudget:
    """Criterion: the committed index and the three-flop sample stay inside the 20 MiB
    `data/artifacts` cap, and the report prints the bytes used, the headroom left and the
    per-spot cost. The budget covers the index and the sample, not the object storage."""

    def measured(self) -> int:
        return sum(path.stat().st_size for path in ARTIFACT_ROOT.rglob("*") if path.is_file())

    def test_the_whole_artifact_tree_is_inside_the_cap(self) -> None:
        assert self.measured() <= ARTIFACT_BYTE_CAP

    def test_the_postflop_tree_holds_no_git_lfs_pointer(self) -> None:
        """A pointer passes the byte budget vacuously on an unfetched clone, which is the
        shortcut the contract forbids by name.

        The count is asserted first because this test is itself the vacuity risk: an empty tree
        satisfies "no file is a pointer" perfectly.
        """
        files = [path for path in POSTFLOP_DIR.rglob("*") if path.is_file()]

        assert files, "the postflop tree holds no files, so this check proves nothing"
        for path in files:
            assert b"git-lfs" not in path.read_bytes()[:64], path.name

    def test_the_index_declares_the_bytes_it_believes_it_costs_and_they_reconcile(
        self, index
    ) -> None:
        """No figure is a per-weight rate that includes non-weight bytes. The declared cost is
        checked against the bytes on disk rather than against another declared rate."""
        declared = index.get("committed_bytes")
        assert isinstance(declared, int) and not isinstance(declared, bool)

        on_disk = sum(
            path.stat().st_size for path in POSTFLOP_DIR.rglob("*") if path.is_file()
        )

        assert declared == on_disk, (
            f"the index says it costs {declared} bytes and the postflop tree holds {on_disk}"
        )

    def test_the_headroom_the_index_states_is_the_cap_less_the_whole_tree(self, index) -> None:
        declared = index.get("headroom_bytes")
        assert isinstance(declared, int) and not isinstance(declared, bool)

        assert declared == ARTIFACT_BYTE_CAP - self.measured()


# --------------------------------------------------------------------------- #
# The input ranges
# --------------------------------------------------------------------------- #


class TestTheInputRangesAreFlooredAtTheClassLevel:
    """Criterion: the input ranges are floored at a weight of 0.01, and the floor is class-level.

    One suit-specific weight in either range collapses the isomorphism group and forfeits the suit
    saving on every non-rainbow board - which is the whole of the only collapse this phase takes.
    """

    @pytest.fixture(scope="class")
    def config(self):
        return load(SOLVE_CONFIG_PATH)

    def test_the_floor_is_published_and_is_one_percent(self, artifact_module) -> None:
        assert owed(artifact_module, "RANGE_WEIGHT_FLOOR") == pytest.approx(RANGE_WEIGHT_FLOOR)

    def test_no_committed_range_weight_sits_below_the_floor(self, config) -> None:
        for name, weights in config["ranges"].items():
            for hand, weight in weights.items():
                assert weight >= RANGE_WEIGHT_FLOOR, (name, hand, weight)

    def test_every_committed_range_is_keyed_by_class_rather_than_by_suit_combo(
        self, config
    ) -> None:
        """A class key is `AKs`, `AKo` or `AA`, two or three characters. A suit-specific key such
        as `AhKh` is the thing that breaks the isomorphism group."""
        for name, weights in config["ranges"].items():
            for hand in weights:
                assert len(hand) in (2, 3), (name, hand)
                assert hand[0] in RANKS and hand[1] in RANKS, (name, hand)
                if len(hand) == 3:
                    assert hand[2] in ("s", "o"), (name, hand)

    def test_applying_the_floor_never_splits_a_class(self, artifact_module) -> None:
        """The class-level constraint, stated directly rather than as set equality.

        Corrected 2026-09-15. This assertion read `set(after) == set(before)`, which is a property
        only a lifting floor has, and between them these two tests required `floor_range` to raise
        every weight to 0.01 and keep every key. Decision 12 rules the other operation: "flooring
        means dropping every hand below a weight threshold out of the range before solving". What
        the class-level constraint actually forbids is a suit-specific key such as `AhKh`, because
        one of those anywhere in either range collapses the suit-isomorphism group and forfeits the
        saving on every non-rainbow board - `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP`. Set
        equality never checked that and a dropping floor satisfies it.
        """
        apply_floor = owed(artifact_module, "floor_range")
        before = {"AKs": 0.0, "AKo": 0.004, "AA": 1.0, "72o": 0.0}

        after = apply_floor(before)

        assert set(after) <= set(before)
        for hand in after:
            assert len(hand) in (2, 3), hand
            assert hand[0] in RANKS and hand[1] in RANKS, hand
            if len(hand) == 3:
                assert hand[2] in ("s", "o"), hand
        assert all(weight >= RANGE_WEIGHT_FLOOR for weight in after.values())
        assert after["AA"] == pytest.approx(1.0)

    def test_the_floor_drops_the_hand_rather_than_lifting_its_weight(self, artifact_module) -> None:
        """Decision 12's operation, and the one the phase's cost model rests on.

        Corrected 2026-09-15, from a test that required the opposite. Dropping is what takes the
        single-raised-pot arena from 21,663 MB to 10,881 MB with the action-node count identical at
        2,347,996: what shrinks is the number of hands, not the shape of the tree. Lifting shrinks
        nothing, so decision 4's campaign figures and decision 6's covered line count would both be
        derived from a saving that did not happen.
        The poker half is the reason it is not merely a units mistake. `72o` and `32o` sit in the
        committed out-of-position range at 0.0002 to 0.0005, which decision 12 measures as residue
        the preflop solve left a rounding of a percent in rather than hands a defender holds.
        Lifting them to 0.01 solves hero against a defender who holds them.
        """
        apply_floor = owed(artifact_module, "floor_range")

        assert "72o" not in apply_floor({"72o": 0.0, "AA": 1.0})
        assert "AKo" not in apply_floor({"AKo": 0.004, "AA": 1.0})
        assert apply_floor({"AA": 1.0, "KK": RANGE_WEIGHT_FLOOR}) == {
            "AA": pytest.approx(1.0),
            "KK": pytest.approx(RANGE_WEIGHT_FLOOR),
        }
