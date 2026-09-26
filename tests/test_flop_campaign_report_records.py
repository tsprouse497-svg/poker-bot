"""Phase 21, stage 4: the rented-box records the report re-derives, one consistent and one
refusing variant each.

Split from `tests/test_flop_campaign_report.py` so each stays under the 700-line cap; the head
of that file says how the generator is reached and why a figure not yet measured says so.

**A record is read, checked and printed, never copied.** The candidate costs, the box's
determinism re-run, the six texture solves and the table result are the figures the phase's
spending and its halts rest on, so a generator that prints whatever a committed record holds -
or prints "not yet measured" whether or not a record exists - would publish the wrong number as
happily as the right one. Each record below lives under `campaign/` in a copy of the postflop
tree, in this shape:

    candidates.json       {record_schema_version, memory_bar_bytes, ceiling_fraction,
                           concurrent_solves, candidates: [{name, memory_bytes,
                           price_per_hour_usd, billed_seconds: {the five parts}}],
                           ranked: [names], excluded: {name: reason},
                           cost_per_solved_flop_usd: {name: dollars}}
    box_determinism.json  determinism.json's own shape, plus `machine`
    texture_trial.json    {record_schema_version, line, machine, threads,
                           groups: {group: {board, cost_usd}}, projected_line_cost_usd}
    table_result.json     {record_schema_version, machine, hands, seed, postflop_decisions,
                           bets, showdowns, voided_hands, voided_by_street: {street: hands}}

Every figure in these fixtures is invented, and named so; none is a measurement.
"""

from __future__ import annotations

import copy
import json
import shutil

import pytest

from scripts.repo_paths import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "generate_flop_campaign_report.py"
POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
GIB = 1024**3
INVENTED_BOX = {
    "platform": "Linux",
    "cpu_model": "invented box for a test",
    "logical_processors": 64,
    "memory_bytes": 128 * GIB,
}


@pytest.fixture(scope="module")
def generator():
    assert SCRIPT.is_file(), (
        f"{SCRIPT.relative_to(REPO_ROOT)} does not exist; phase 21's contract requires the"
        " generator and no implementation has been written yet"
    )
    import scripts.generate_flop_campaign_report as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


@pytest.fixture(scope="module")
def refusal(generator):
    return owed(generator, "ReportFigureError")


@pytest.fixture
def tree_copy(tmp_path):
    copied = tmp_path / "postflop"
    shutil.copytree(POSTFLOP_DIR, copied)
    shutil.rmtree(copied / "campaign", ignore_errors=True)
    (copied / "campaign").mkdir()
    return copied


def write_record(copied, name: str, document) -> None:
    (copied / "campaign" / name).write_text(json.dumps(document, indent=1) + "\n", "utf-8")


def render(generator, copied) -> str:
    return owed(generator, "render_report")(copied)


def rows_with(text: str, *tokens: str) -> list[str]:
    return [row for row in text.splitlines() if all(token in row for token in tokens)]


# --------------------------------------------------------------------------- #
# Candidates
# --------------------------------------------------------------------------- #

STRETCH = {
    "server_start": 30.0,
    "tree_build": 60.0,
    "solve": 1_200.0,
    "harvest": 1_800.0,
    "upload": 150.0,
}
"""3,240 seconds in all; at $3.60 an hour that is $3.24 a closed flop."""

BAR_BYTES = 18_600_000_000
"""At or above the small blind's line's largest planned arena under either reading of the
server's unit - 17,674,107,736 bytes as the server means it, 18,532,645,193 as the 2^20 reading
has it - so the fixture does not decide decision 14."""


def candidates_record():
    return {
        "record_schema_version": 1,
        "memory_bar_bytes": BAR_BYTES,
        "ceiling_fraction": 0.40,
        "concurrent_solves": 1,
        "candidates": [
            {
                "name": "invented-big",
                "memory_bytes": 128 * GIB,
                "price_per_hour_usd": 3.6,
                "billed_seconds": dict(STRETCH),
            },
            {
                "name": "invented-small",
                "memory_bytes": 32 * GIB,
                "price_per_hour_usd": 0.5,
                "billed_seconds": dict(STRETCH),
            },
        ],
        "ranked": ["invented-big"],
        "excluded": {"invented-small": "cannot hold the memory bar at the 0.40 ceiling"},
        "cost_per_solved_flop_usd": {"invented-big": 3.24},
    }


class TestTheCandidateRecordIsReDerived:
    """Criteria: a candidate that cannot hold the memory bar is excluded with that reason and
    never ranked, and the choice is made on cost per solved flop - price times the billed time
    for server start, tree build, solve, harvest and upload."""

    def test_a_consistent_record_prints_each_ranked_candidate_s_cost(self, generator, tree_copy):
        write_record(tree_copy, "candidates.json", candidates_record())

        text = render(generator, tree_copy)

        assert rows_with(text, "invented-big", "$3.24"), "the cost per solved flop, per candidate"
        assert rows_with(text, "invented-small"), "the excluded candidate is named with its reason"

    def test_ranking_a_candidate_the_bar_excludes_fails(self, generator, refusal, tree_copy):
        record = candidates_record()
        record["ranked"] = ["invented-small", "invented-big"]
        record["excluded"] = {}
        record["cost_per_solved_flop_usd"]["invented-small"] = 0.45
        write_record(tree_copy, "candidates.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_cost_that_is_not_price_times_the_stretch_fails(self, generator, refusal, tree_copy):
        record = candidates_record()
        record["cost_per_solved_flop_usd"]["invented-big"] = 2.00
        write_record(tree_copy, "candidates.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_bar_below_the_campaign_s_largest_arena_fails(self, generator, refusal, tree_copy):
        """Only the bar changes: the ranking, the exclusion and the costs stay as the tree's bar
        makes them, so a generator that never reads the record's own bar renders this and fails
        the test. The bar is the tree walk's, and a record that states a smaller one is wrong
        whatever else in it agrees."""
        record = candidates_record()
        record["memory_bar_bytes"] = 10_000_000_000
        write_record(tree_copy, "candidates.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)


# --------------------------------------------------------------------------- #
# The box's determinism re-run
# --------------------------------------------------------------------------- #


def box_record():
    record = json.loads((POSTFLOP_DIR / "determinism.json").read_text(encoding="utf-8"))
    record["machine"] = dict(INVENTED_BOX)
    return record


class TestTheBoxDeterminismRecordIsReDerived:
    """Criteria: determinism is re-proved on the chosen box, compared as `determinism.json`
    compares; whether the box matches the M4's committed digests is printed as a separate finding
    and is not a pass condition."""

    @pytest.fixture(scope="class")
    def words(self, generator):
        """The generator's own words for the four findings, published like `NOT_YET_MEASURED`
        so each can be looked for on a row rather than guessed at."""
        found = {
            name: owed(generator, name)
            for name in ("BOX_REPEATED", "BOX_DID_NOT_REPEAT", "M4_MATCH", "M4_MISMATCH")
        }
        for first, second in (("BOX_REPEATED", "BOX_DID_NOT_REPEAT"), ("M4_MATCH", "M4_MISMATCH")):
            assert found[first] and found[second]
            assert found[first] not in found[second] and found[second] not in found[first]
        return found

    def test_a_box_that_repeats_itself_and_the_m4_says_both(
        self, generator, tree_copy, words
    ) -> None:
        write_record(tree_copy, "box_determinism.json", box_record())

        text = render(generator, tree_copy)

        assert rows_with(text, "invented box for a test", words["BOX_REPEATED"])
        assert rows_with(text, words["M4_MATCH"])
        assert not rows_with(text, words["M4_MISMATCH"])

    def test_the_m4_match_is_its_own_finding_and_not_a_pass_condition(
        self, generator, tree_copy, words
    ) -> None:
        """Both runs on the box agree and differ from the M4: the box still repeated itself, and
        the M4 finding flips."""
        record = box_record()
        record["cells"][0]["strategy_digest"] = ["e" * 64, "e" * 64]
        write_record(tree_copy, "box_determinism.json", record)

        text = render(generator, tree_copy)

        assert rows_with(text, "invented box for a test", words["BOX_REPEATED"])
        assert rows_with(text, words["M4_MISMATCH"])
        assert not rows_with(text, words["M4_MATCH"])

    def test_a_flag_that_says_identical_over_cells_that_differ_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        record = box_record()
        record["cells"][2]["strategy_digest"][1] = "0" * 64
        assert record["identical"] is True
        write_record(tree_copy, "box_determinism.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_box_that_did_not_repeat_itself_says_so_and_that_the_phase_halts(
        self, generator, tree_copy, words
    ) -> None:
        """The contract: if the two runs on the box differ, the phase halts and Taylor is asked.
        The report's job is to say it, so an honest not-identical record renders, says the box
        did not repeat, and says on that row that this is a halt."""
        record = box_record()
        record["cells"][2]["strategy_digest"][1] = "0" * 64
        record["cells"][2]["cell_document_bytes_identical"] = False
        record["identical"] = False
        write_record(tree_copy, "box_determinism.json", record)

        text = render(generator, tree_copy)

        rows = rows_with(text, "invented box for a test", words["BOX_DID_NOT_REPEAT"])
        assert rows and any("halt" in row.lower() for row in rows), rows
        assert not rows_with(text, "invented box for a test", words["BOX_REPEATED"])


# --------------------------------------------------------------------------- #
# The six texture solves
# --------------------------------------------------------------------------- #

TEXTURE_BOARDS = {
    "rainbow unpaired": (["Kh", "7d", "2c"], 1.0),
    "two-tone unpaired": (["Jd", "6d", "3c"], 2.0),
    "rainbow paired": (["8d", "8h", "3c"], 1.5),
    "two-tone paired": (["8c", "8d", "3c"], 1.5),
    "monotone": (["9c", "8c", "7c"], 0.5),
    "trips": (["2c", "2d", "2h"], 1.0),
}
PROJECTION = 286 * 1.0 + 858 * 2.0 + 156 * 1.5 + 156 * 1.5 + 286 * 0.5 + 13 * 1.0
"""2,626.00: each group's invented cost times the classes it holds."""


def texture_record():
    return {
        "record_schema_version": 1,
        "line": "SB:raise@2.5,BB:call",
        "machine": dict(INVENTED_BOX),
        "threads": 32,
        "groups": {
            group: {"board": board, "cost_usd": cost}
            for group, (board, cost) in TEXTURE_BOARDS.items()
        },
        "projected_line_cost_usd": PROJECTION,
    }


class TestTheTextureRecordIsReDerived:
    """Criterion: the report projects one closed line's cost from the six texture solves,
    weighted by how many of the 1,755 classes each group holds."""

    def test_a_consistent_record_prints_its_projection(self, generator, tree_copy) -> None:
        write_record(tree_copy, "texture_trial.json", texture_record())

        assert "$2,626.00" in render(generator, tree_copy)

    def test_a_projection_that_is_not_the_class_weighted_sum_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        record = texture_record()
        record["projected_line_cost_usd"] = 2_000.0
        write_record(tree_copy, "texture_trial.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_record_missing_a_group_fails(self, generator, refusal, tree_copy) -> None:
        record = texture_record()
        del record["groups"]["two-tone unpaired"]
        write_record(tree_copy, "texture_trial.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_record_for_another_line_fails(self, generator, refusal, tree_copy) -> None:
        """The six trial boards are on the first admitted line, the small blind's; a projection
        from the cutoff's line prices the wrong tree."""
        record = texture_record()
        record["line"] = "CO:raise@2.5,BB:call"
        write_record(tree_copy, "texture_trial.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_board_filed_under_the_wrong_group_fails(self, generator, refusal, tree_copy):
        record = texture_record()
        record["groups"]["monotone"]["board"] = ["2c", "2d", "2h"]
        write_record(tree_copy, "texture_trial.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)


# --------------------------------------------------------------------------- #
# The table result
# --------------------------------------------------------------------------- #


def table_record():
    return {
        "record_schema_version": 1,
        "machine": dict(INVENTED_BOX),
        "hands": 20_000,
        "seed": 777,
        "postflop_decisions": 812,
        "bets": 240,
        "showdowns": 0,
        "voided_hands": 5_100,
        "voided_by_street": {"flop": 1_200, "turn": 3_900, "river": 0},
    }


class TestTheTableRecordIsReDerived:
    """Criterion: the table result is re-run on phase 16's own terms - 20,000 hands, seed 777 -
    printing voided hands split by the street the hand voided on, beside phase 16's 5,365."""

    def test_a_consistent_record_prints_its_voids_beside_phase_16_s(self, generator, tree_copy):
        write_record(tree_copy, "table_result.json", table_record())

        text = render(generator, tree_copy)

        assert "5,100" in text and "5,365" in text
        assert "3,900" in text, "the turn's share of the voids"

    def test_voids_by_street_that_do_not_sum_to_the_total_fail(
        self, generator, refusal, tree_copy
    ) -> None:
        record = copy.deepcopy(table_record())
        record["voided_by_street"]["turn"] = 3_400
        write_record(tree_copy, "table_result.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_run_of_another_length_fails(self, generator, refusal, tree_copy) -> None:
        record = table_record()
        record["hands"] = 19_999
        write_record(tree_copy, "table_result.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_hand_voided_on_the_river_fails(self, generator, refusal, tree_copy) -> None:
        """Every turn decision refuses this phase, so a hand reaches the river only all-in with
        no decision left, and that is a showdown, not a void. River voids above zero mean the bot
        played a turn, which the non-goals forbid."""
        record = table_record()
        record["voided_by_street"]["river"] = 400
        record["voided_hands"] = 5_500
        write_record(tree_copy, "table_result.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)

    def test_a_run_not_on_phase_16_s_terms_fails(self, generator, refusal, tree_copy) -> None:
        record = table_record()
        record["seed"] = 778
        write_record(tree_copy, "table_result.json", record)

        with pytest.raises(refusal):
            render(generator, tree_copy)


# --------------------------------------------------------------------------- #
# With no records, none of these numbers is printed
# --------------------------------------------------------------------------- #


def test_no_record_s_number_appears_before_the_record_exists(generator, tree_copy) -> None:
    """The not-yet-measured path, checked against the numbers above: a generator that printed a
    default or an estimate in their place would have to invent one of these to pass the tests
    above, and must not print it here."""
    text = render(generator, tree_copy)

    for figure in ("$3.24", "$2,626.00", "5,100", "invented box for a test"):
        assert figure not in text, figure
    assert owed(generator, "NOT_YET_MEASURED") in text
