"""Phase 21, stage 4: part 3's storage - the manifest git holds, the fetch, and closure.

Authored from the contract before any implementation exists; see the head of
`tests/test_flop_campaign_threads.py` for how the missing modules are reached.

**The shape of a manifest is fixed here**, because the gate reads it offline and the report counts
coverage from it, so a field nobody pinned is a field the report can drift from. One JSON file per
admitted line under `data/artifacts/postflop/manifests/`:

    {"manifest_schema_version": 1,
     "preflop_line": "BTN:raise@2.5,BB:call",
     "index": {"object_key": "...", "sha256": "<64 hex>", "bytes": <int>},
     "flops_held": <flops the closed boards stand for, of 22,100>,
     "refused_boards": <how many boards below are refused>,
     "boards": [{"board": ["Kh", "7d", "2c"], "status": "closed" | "refused",
                 "decision_points": {"flop": 14, "turn": 6419, "river": 1477056},
                 "achieved_exploitability_pct_of_pot": 0.283, "iterations": 340,
                 "machine": "...", "threads": 10,
                 "strategy_digests": {"<spot key>": "<sha256>"}}]}

`strategy_digests` is carried by a board whose cells the committed `index.json` lists - phase 16's
four - and holds the strategy digest of each of those spots from the closing solve, which is what
ties the manifest to the committed sample offline rather than two numbers alone.

and the line's full index, in object storage, lists per board the same counts and one object per
street with its key and sha256. A board keeps every decision point of its line from its one solve,
or refuses all of them: a refused board carries zero on every street.

**The fetch is tested against an injected store**, because AWS is a hard external boundary. The
store is a dict of key to bytes with a `get` method; nothing here opens a socket or needs a
credential.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from poker_training_bot.solver_artifacts import postflop_artifact as artifact
from poker_training_bot.solver_artifacts import postflop_isomorphism as isomorphism
from scripts.repo_paths import REPO_ROOT

POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
SAMPLE_DIR = POSTFLOP_DIR / "sample"
COMMITTED_LINE = "BTN:raise@2.5,BB:call"
CLOSED_COUNTS = {"flop": 14, "turn": 6_419, "river": 1_477_056}
SMALL_BLIND_LINE = "SB:raise@2.5,BB:call"
SMALL_BLIND_COUNTS = {"flop": 14, "turn": 6_566, "river": 1_545_264}
"""The small blind's line closes on its own tree, pot 5.0: 134 decision points on each of 49
turns and 657 on each reachable river, with 32,193 under the dealt turn card not kept. Pinned in
`tests/test_flop_campaign_tree.py` and recomputed by two independent ports of `tree.rs`."""
PHASE_16_BOARDS = (("9c", "8c", "7c"), ("Kh", "7d", "2c"), ("8c", "8d", "3c"), ("Ac", "8c", "3c"))

SAMPLE_SHA256 = {
    "monotone-connected-cbet.json": (
        "5aa01d6802458b81effd579c506c889d3f778ae5dbb104215503dcbe351104ed"
    ),
    "rainbow-dry-high-donk.json": (
        "d8a6b8c44a71bffd7c5d4d71d7d212186a3a3029d8840674b083eca76b0432a6"
    ),
    "rainbow-dry-high-facing-a-bet.json": (
        "5dd593d95e47c4f6a3635a6182682fbdc03b76abd4eecd57a80175a66f3832d3"
    ),
    "two-tone-paired-donk.json": (
        "0d53acd682cbf5cd1710ff9b81ab09df59dc3ce678c62795d1e5d7349facba58"
    ),
}
"""The four cell documents phase 16 committed at `479aaf2`, hashed 2026-09-26."""


@pytest.fixture(scope="module")
def manifest_module():
    """`solver_artifacts.postflop_manifest`: the per-line manifest git holds, and coverage."""
    import poker_training_bot.solver_artifacts.postflop_manifest as module

    return module


@pytest.fixture(scope="module")
def fetch():
    """`solver_artifacts.postflop_fetch`: the command a fresh machine runs, as a function."""
    import poker_training_bot.solver_artifacts.postflop_fetch as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def manifests(manifest_module):
    return owed(manifest_module, "load_manifests")()


@pytest.fixture(scope="module")
def committed_index():
    return json.loads((POSTFLOP_DIR / "index.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Phase 16's cells and rules stay as they are
# --------------------------------------------------------------------------- #


class TestPhase16StaysByteIdentical:
    """Regression: every cell phase 16 committed stays byte-identical, the commit rule is phase
    16's constants as Taylor kept them (decision 8), and no git LFS is used or cap raised."""

    @pytest.mark.parametrize("name", sorted(SAMPLE_SHA256))
    def test_each_committed_cell_document_is_unchanged(self, name) -> None:
        assert sha256((SAMPLE_DIR / name).read_bytes()) == SAMPLE_SHA256[name]

    def test_the_sample_holds_exactly_those_four(self) -> None:
        assert sorted(path.name for path in SAMPLE_DIR.glob("*.json")) == sorted(SAMPLE_SHA256)

    def test_the_commit_rule_constants_are_phase_16_s(self) -> None:
        assert artifact.EXPLOITABILITY_TARGET_PCT_OF_POT == 0.3
        assert artifact.SOLVE_ITERATION_CAP == 1200
        assert artifact.EXPLOITABILITY_CEILING_PCT_OF_POT == 1.0

    def test_the_twenty_mebibyte_cap_on_data_artifacts_is_not_raised(self) -> None:
        text = (REPO_ROOT / "scripts" / "check_file_sizes.py").read_text(encoding="utf-8")

        assert '("data/artifacts", 20 * 1024 * 1024)' in text

    def test_no_git_lfs_filter_is_declared(self) -> None:
        attributes = REPO_ROOT / ".gitattributes"
        text = attributes.read_text(encoding="utf-8") if attributes.is_file() else ""

        assert "filter=lfs" not in text


# --------------------------------------------------------------------------- #
# The committed manifests
# --------------------------------------------------------------------------- #


class TestTheCommittedManifests:
    """Criterion: the full index lives in object storage, and git holds a manifest per line - the
    flops held and one fingerprint of that line's index file - which the gate checks offline
    against the committed sample, and from which the report counts coverage."""

    def test_the_manifests_live_under_the_capped_artifact_tree(self, manifest_module) -> None:
        """Inside `data/artifacts`, so `check_file_sizes` counts every manifest byte against the
        20 MiB cap, and beside the index, so a copy of the postflop tree carries them."""
        directory = owed(manifest_module, "MANIFEST_DIR")

        assert directory == POSTFLOP_DIR / "manifests"
        assert directory.is_dir()

    def test_there_is_a_manifest_for_the_committed_line(self, manifests) -> None:
        assert COMMITTED_LINE in manifests

    def test_every_manifest_is_for_an_admitted_line(self, manifests) -> None:
        import poker_training_bot.solver_artifacts.postflop_lines as lines

        assert set(manifests) <= set(lines.ADMITTED_LINES)

    def test_every_committed_manifest_passes_its_own_checks(self, manifest_module, manifests):
        errors = owed(manifest_module, "manifest_errors")

        for line, manifest in manifests.items():
            assert errors(manifest) == [], line

    def test_each_fingerprint_is_one_sha256(self, manifests) -> None:
        for line, manifest in manifests.items():
            assert re.fullmatch(r"[0-9a-f]{64}", manifest["index"]["sha256"]), line
            assert manifest["index"]["object_key"], line

    def test_phase_16_s_four_boards_are_closed_from_their_resolve(
        self, manifests, committed_index
    ) -> None:
        """Criterion: phase 16's four boards close from the part 1 re-solve, which must reproduce
        their committed cells - so the closed board carries the same exploitability and iteration
        count the committed index records, to the last bit, and all of its decision points."""
        boards = {tuple(entry["board"]): entry for entry in manifests[COMMITTED_LINE]["boards"]}
        recorded = {tuple(entry["board"]): entry for entry in committed_index["entries"]}

        for board in PHASE_16_BOARDS:
            assert board in boards, board
            entry = boards[board]
            assert entry["status"] == "closed", board
            assert entry["decision_points"] == CLOSED_COUNTS, board
            assert entry["iterations"] == recorded[board]["iterations"], board
            assert (
                entry["achieved_exploitability_pct_of_pot"]
                == recorded[board]["achieved_exploitability_pct_of_pot"]
            ), board
            committed_spots = {
                spot["spot_key"]: spot["strategy_digest"]
                for spot in committed_index["entries"]
                if tuple(spot["board"]) == board
            }
            assert entry["strategy_digests"] == committed_spots, board

    def test_every_board_names_the_machine_and_thread_count_it_was_solved_at(self, manifests):
        """Forbidden shortcut: reporting a campaign figure without its machine and thread count."""
        for line, manifest in manifests.items():
            for entry in manifest["boards"]:
                assert isinstance(entry["machine"], str) and entry["machine"], (line, entry)
                assert isinstance(entry["threads"], int) and entry["threads"] >= 1, (line, entry)


# --------------------------------------------------------------------------- #
# What the manifest checks refuse
# --------------------------------------------------------------------------- #


def closed_board(board, exploit=0.28, iterations=340, counts=None):
    return {
        "board": list(board),
        "status": "closed",
        "decision_points": dict(counts or CLOSED_COUNTS),
        "achieved_exploitability_pct_of_pot": exploit,
        "iterations": iterations,
        "machine": "invented machine for a test",
        "threads": 10,
    }


def refused_board(board):
    return {
        "board": list(board),
        "status": "refused",
        "decision_points": {"flop": 0, "turn": 0, "river": 0},
        "achieved_exploitability_pct_of_pot": 1.37,
        "iterations": 1200,
        "machine": "invented machine for a test",
        "threads": 10,
    }


def a_manifest(line=COMMITTED_LINE, counts=None):
    """Two closed boards (24 and 12 flops) and one refused: every field consistent."""
    return {
        "manifest_schema_version": 1,
        "preflop_line": line,
        "index": {"object_key": "postflop/btn-v-bb/index.json", "sha256": "a" * 64, "bytes": 1},
        "flops_held": 36,
        "refused_boards": 1,
        "boards": [
            closed_board(("Kh", "7d", "2c"), counts=counts),
            closed_board(("8c", "8d", "3c"), counts=counts),
            refused_board(("Jd", "6d", "3c")),
        ],
    }


def spoil(change):
    manifest = a_manifest()
    change(manifest)
    return manifest


class TestTheManifestChecksRefuseAnInconsistentManifest:
    """Criteria: a covered board keeps every decision point from its one solve, or refuses all of
    them because that solve missed the exploitability ceiling; the manifest carries each board's
    counts per street and a test asserts them offline; the refused count is in the header."""

    def test_a_consistent_manifest_passes(self, manifest_module) -> None:
        """The positive control for every refusal below."""
        assert owed(manifest_module, "manifest_errors")(a_manifest()) == []

    @pytest.mark.parametrize(
        ("why", "change"),
        [
            (
                "a river count one short",
                lambda m: m["boards"][0]["decision_points"].update(river=1_477_055),
            ),
            (
                "the unreachable river kept too",
                lambda m: m["boards"][0]["decision_points"].update(river=1_507_828),
            ),
            (
                "a closed board missing its turn",
                lambda m: m["boards"][1]["decision_points"].update(turn=0),
            ),
            (
                "a refused board keeping its flop",
                lambda m: m["boards"][2]["decision_points"].update(flop=14),
            ),
            (
                "a closed board above the one percent ceiling",
                lambda m: m["boards"][0].update(achieved_exploitability_pct_of_pot=1.2),
            ),
            (
                "a closed board past the iteration cap",
                lambda m: m["boards"][0].update(iterations=1220),
            ),
            (
                "a refused board inside the ceiling",
                lambda m: m["boards"][2].update(achieved_exploitability_pct_of_pot=0.5),
            ),
            ("a header refused count that disagrees", lambda m: m.update(refused_boards=0)),
            ("a flops-held figure that disagrees", lambda m: m.update(flops_held=37)),
            (
                "a board that is not its class's canonical dressing",
                lambda m: m["boards"][0].update(board=["Kc", "7d", "2h"]),
            ),
            (
                "the same board twice",
                lambda m: m["boards"].append(closed_board(("Kh", "7d", "2c"))),
            ),
            ("a line nobody admitted", lambda m: m.update(preflop_line="SB:call")),
            ("an unknown status", lambda m: m["boards"][0].update(status="partial")),
            ("a board with no thread count", lambda m: m["boards"][0].update(threads=None)),
        ],
    )
    def test_an_inconsistent_manifest_is_refused(self, manifest_module, why, change) -> None:
        assert owed(manifest_module, "manifest_errors")(spoil(change)), why

    def test_a_refused_board_does_not_count_toward_the_flops_held(self, manifest_module) -> None:
        """36 is `Kh7d2c`'s 24 and `8c8d3c`'s 12; `Jd6d3c`'s 12 flops are refused, not held."""
        assert a_manifest()["flops_held"] == 24 + 12
        assert owed(manifest_module, "manifest_errors")(a_manifest()) == []


class TestAClosedBoardIsClosedOnItsOwnLinesTree:
    """A board closes on the decision points of the line it was solved for, not the button's.
    The small blind's line goes first (decision 9), and a harvest that walked the 5.5 pot's tree
    for it would write 6,419 and 1,477,056 - which a checker hardwired to one line's counts
    accepts."""

    def test_the_small_blind_line_s_own_counts_are_accepted(self, manifest_module) -> None:
        manifest = a_manifest(SMALL_BLIND_LINE, SMALL_BLIND_COUNTS)

        assert owed(manifest_module, "manifest_errors")(manifest) == []

    @pytest.mark.parametrize(
        ("why", "line", "counts"),
        [
            ("the button's counts on the small blind's line", SMALL_BLIND_LINE, CLOSED_COUNTS),
            (
                "the small blind's river with the dealt turn's river kept",
                SMALL_BLIND_LINE,
                {**SMALL_BLIND_COUNTS, "river": 1_577_457},
            ),
            (
                "the small blind's turn with the button's river",
                SMALL_BLIND_LINE,
                {**SMALL_BLIND_COUNTS, "river": 1_477_056},
            ),
            (
                "the small blind's counts on the cutoff's line",
                "CO:raise@2.5,BB:call",
                SMALL_BLIND_COUNTS,
            ),
        ],
    )
    def test_another_line_s_counts_are_refused(self, manifest_module, why, line, counts) -> None:
        assert owed(manifest_module, "manifest_errors")(a_manifest(line, counts)), why


class TestTheCommitRuleIsPhase16s:
    """Decision 8 kept phase 16's rule: aim at 0.3 percent, stop at 1,200 iterations, commit a
    cap-bound board up to 1 percent and refuse it above. The solver stops only at the target or
    at the cap - it checks every 20 iterations - so a board above the target that stopped before
    the cap stopped on neither condition, and `commit_verdict` refuses that."""

    def with_first_board(self, **fields):
        manifest = a_manifest()
        manifest["boards"][0].update(fields)
        return manifest

    def test_a_cap_bound_board_between_the_target_and_the_ceiling_is_closed(
        self, manifest_module
    ) -> None:
        manifest = self.with_first_board(achieved_exploitability_pct_of_pot=0.8, iterations=1200)

        assert owed(manifest_module, "manifest_errors")(manifest) == []

    def test_a_cap_bound_board_at_exactly_the_ceiling_is_closed(self, manifest_module) -> None:
        """Refusal is above 1 percent, so 1.0 itself commits."""
        manifest = self.with_first_board(achieved_exploitability_pct_of_pot=1.0, iterations=1200)

        assert owed(manifest_module, "manifest_errors")(manifest) == []

    def test_a_board_above_the_target_that_stopped_before_the_cap_is_refused(
        self, manifest_module
    ) -> None:
        manifest = self.with_first_board(achieved_exploitability_pct_of_pot=0.8, iterations=600)

        assert owed(manifest_module, "manifest_errors")(manifest)


# --------------------------------------------------------------------------- #
# Coverage, counted from the manifests
# --------------------------------------------------------------------------- #


class TestCoverageIsCountedFromTheManifests:
    """Criteria: the report prints how many flop classes a fresh clone can answer beside how many
    a fetched machine can (`THE-BOT-PLAYS-DATA-THAT-IS-NOT-IN-THE-REPO-THAT-SHIPS-IT`), coverage by
    texture group, and counts lines and seats under different words
    (`A-BOARD-REFUSAL-READS-AS-BOARDWIDE-AND-IS-SCOPED-PER-LINE-AND-SEAT`)."""

    @pytest.fixture(scope="class")
    def found(self, manifest_module, manifests):
        return owed(manifest_module, "coverage")(manifests)

    def test_a_fresh_clone_answers_the_three_sample_boards(self, found) -> None:
        """`Kh7d2c`, `8c8d3c` and `9c8c7c` are in `sample/`: 24 + 12 + 4 flops. `Ac8c3c` is
        indexed and its cell is not in git."""
        assert found.fresh_clone_classes == 3
        assert found.fresh_clone_flops == 40

    def test_a_fetched_machine_answers_every_closed_board(self, found, manifests) -> None:
        for line, manifest in manifests.items():
            closed = [entry for entry in manifest["boards"] if entry["status"] == "closed"]
            assert found.classes_held[line] == len(closed), line
            assert found.flops_held[line] == manifest["flops_held"], line
        assert found.classes_held[COMMITTED_LINE] >= len(PHASE_16_BOARDS)

    def test_coverage_by_texture_group_adds_up_to_the_classes_held(self, found) -> None:
        for line, groups in found.by_texture.items():
            assert sum(groups.values()) == found.classes_held[line], line
        committed = found.by_texture[COMMITTED_LINE]
        assert committed["monotone"] >= 2 and committed["rainbow unpaired"] >= 1
        assert committed["two-tone paired"] >= 1

    def test_lines_and_seats_are_counted_apart(self, found, manifests) -> None:
        """A closed board is closed for both seats, so each line with a closed board is two
        seats. Phase 16's report called two seats "2 covered preflop lines"."""
        with_a_closed_board = [
            line
            for line, manifest in manifests.items()
            if any(entry["status"] == "closed" for entry in manifest["boards"])
        ]
        assert found.lines == len(with_a_closed_board)
        assert found.seats == 2 * found.lines


# --------------------------------------------------------------------------- #
# The fetch
# --------------------------------------------------------------------------- #


class DictStore:
    """An object store answered from memory: the S3 boundary, faked, and nothing else."""

    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = dict(objects)
        self.requested: list[str] = []

    def get(self, key: str) -> bytes:
        self.requested.append(key)
        return self.objects[key]


FETCH_BOARDS = (("Kh", "7d", "2c"), ("8c", "8d", "3c"))
INDEX_KEY = "postflop/btn-v-bb/index.json"
FLOP_DECISION_POINTS = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "flop_campaign" / "flop_decision_points.json").read_text(
        encoding="utf-8"
    )
)
"""Every flop decision point of each tree shape, derived from GTOpen's `tree.rs`; see its note."""


def flop_spot_keys(line: str, board) -> list[str]:
    """The spot key of every flop decision point one solve of `line` holds on `board`."""
    shape = FLOP_DECISION_POINTS["lines"][line]
    tail = f"/p:{shape['pot_bb']}/e:{shape['effective_stack_bb']}"
    return [
        f"f/b:{''.join(board)}/t6/d100/{point['hero']}/{line}/f:{point['flop']}{tail}"
        for point in shape["decision_points"]
    ]


def flop_object(keys) -> bytes:
    """A flop object as the fetch reads it, uncompressed JSON `{"cells": [...]}`, one cell a key.
    Every field but the key is borrowed from one committed cell: the fetch checks which decision
    points an object holds, by key, and whether each cell is sound is the importer's check when
    the strategy loads it."""
    borrowed = json.loads(
        (SAMPLE_DIR / "rainbow-dry-high-facing-a-bet.json").read_text(encoding="utf-8")
    )
    return json.dumps({"cells": [dict(borrowed, spot_key=key) for key in keys]}).encode()


def published_line():
    """A line index, its objects and its manifest, all consistent, as an upload would leave
    them. Each flop object holds the board's fourteen flop decision points; the turn and river
    bytes are stand-ins, since their format is stage 6's, and what the fetch checks of them is
    their digests."""
    objects: dict[str, bytes] = {}
    boards = []
    for board in FETCH_BOARDS:
        name = "".join(board)
        listed = {}
        for street in ("flop", "turn", "river"):
            if street == "flop":
                key = f"postflop/btn-v-bb/{name}.flop.json"
                objects[key] = flop_object(flop_spot_keys(COMMITTED_LINE, board))
            else:
                key = f"postflop/btn-v-bb/{name}.{street}.bin"
                objects[key] = f"{name} {street} decision points".encode()
            listed[street] = {"key": key, "sha256": sha256(objects[key])}
        boards.append(
            {"board": list(board), "decision_points": dict(CLOSED_COUNTS), "objects": listed}
        )
    index = {"line_index_schema_version": 1, "preflop_line": COMMITTED_LINE, "boards": boards}
    objects[INDEX_KEY] = json.dumps(index, sort_keys=True).encode()
    manifest = {
        "manifest_schema_version": 1,
        "preflop_line": COMMITTED_LINE,
        "index": {
            "object_key": INDEX_KEY,
            "sha256": sha256(objects[INDEX_KEY]),
            "bytes": len(objects[INDEX_KEY]),
        },
        "flops_held": 36,
        "refused_boards": 0,
        "boards": [closed_board(board) for board in FETCH_BOARDS],
    }
    return manifest, index, objects


def republish(index, objects):
    objects = dict(objects)
    objects[INDEX_KEY] = json.dumps(index, sort_keys=True).encode()
    return objects


class TestTheFetchChecksEverythingItFetches:
    """Criteria: every object is stored with its digest in the index, and a fetch command a fresh
    machine can run; a machine that has not fetched refuses with the not-fetched code; the fetch
    checks every fetched object against the counts, and the index against the manifest's
    fingerprint. With the river kept, a machine that plays only the flop fetches by street."""

    def test_the_failure_codes_are_four_distinct_names(self, fetch) -> None:
        codes = {
            owed(fetch, name)
            for name in (
                "NOT_FETCHED",
                "INDEX_FINGERPRINT_MISMATCH",
                "OBJECT_DIGEST_MISMATCH",
                "DECISION_POINTS_MISMATCH",
            )
        }
        assert len(codes) == 4
        assert "not-fetched" in owed(fetch, "NOT_FETCHED")

    def test_a_machine_that_has_fetched_nothing_refuses_as_not_fetched(self, fetch, tmp_path):
        manifest, _, _ = published_line()

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "require_fetched")(manifest, tmp_path, street="flop")

        assert raised.value.code == owed(fetch, "NOT_FETCHED")

    def test_a_consistent_line_fetches_and_then_reads_as_fetched(self, fetch, tmp_path) -> None:
        manifest, _, objects = published_line()

        owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        owed(fetch, "require_fetched")(manifest, tmp_path, street="flop")

    def test_a_flop_fetch_does_not_pull_the_turn_or_the_river(self, fetch, tmp_path) -> None:
        manifest, _, objects = published_line()
        store = DictStore(objects)

        owed(fetch, "fetch_line")(manifest, store, tmp_path, streets=("flop",))

        assert not [key for key in store.requested if key.endswith((".turn.bin", ".river.bin"))]
        assert sorted(key for key in store.requested if key.endswith(".flop.json")) == [
            "postflop/btn-v-bb/8c8d3c.flop.json",
            "postflop/btn-v-bb/Kh7d2c.flop.json",
        ]

    def test_a_street_that_was_not_fetched_still_refuses_as_not_fetched(self, fetch, tmp_path):
        """The index is on disk after a flop fetch, so this is the objects' own check."""
        manifest, _, objects = published_line()
        owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "require_fetched")(manifest, tmp_path, street="turn")

        assert raised.value.code == owed(fetch, "NOT_FETCHED")

    def test_an_index_that_is_not_the_one_the_manifest_fingerprints_is_rejected(
        self, fetch, tmp_path
    ) -> None:
        manifest, _, objects = published_line()
        objects[INDEX_KEY] = objects[INDEX_KEY] + b" "

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert raised.value.code == owed(fetch, "INDEX_FINGERPRINT_MISMATCH")

    def test_an_object_whose_digest_is_not_the_index_s_is_rejected(self, fetch, tmp_path) -> None:
        manifest, _, objects = published_line()
        objects["postflop/btn-v-bb/8c8d3c.flop.json"] = b"a different object"

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert raised.value.code == owed(fetch, "OBJECT_DIGEST_MISMATCH")

    def test_an_object_set_whose_counts_differ_from_the_manifest_is_rejected(
        self, fetch, tmp_path
    ) -> None:
        """The index is re-published with one board's river short by the 628 of one river card,
        and the manifest re-fingerprinted to match, so only the count comparison can see it."""
        manifest, index, objects = published_line()
        index = copy.deepcopy(index)
        index["boards"][1]["decision_points"]["river"] -= 628
        objects = republish(index, objects)
        manifest["index"]["sha256"] = sha256(objects[INDEX_KEY])
        manifest["index"]["bytes"] = len(objects[INDEX_KEY])

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert raised.value.code == owed(fetch, "DECISION_POINTS_MISMATCH")

    def test_a_manifest_and_index_that_agree_but_not_with_the_tree_are_rejected(
        self, fetch, tmp_path
    ) -> None:
        """Both short one river card, consistently: the fingerprint and the index-to-manifest
        comparison pass, and only a comparison against the line's own tree can see it."""
        manifest, index, objects = published_line()
        index = copy.deepcopy(index)
        index["boards"][1]["decision_points"]["river"] -= 628
        objects = republish(index, objects)
        manifest["index"]["sha256"] = sha256(objects[INDEX_KEY])
        manifest["index"]["bytes"] = len(objects[INDEX_KEY])
        manifest["boards"][1]["decision_points"]["river"] -= 628

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert raised.value.code == owed(fetch, "DECISION_POINTS_MISMATCH")

    def test_every_published_board_is_its_class_s_canonical_dressing(self) -> None:
        """A guard on this file's own fixture: the boards it publishes are ones the manifest
        checks above would accept."""
        for board in FETCH_BOARDS:
            assert isomorphism.canonical_board(board) == board
