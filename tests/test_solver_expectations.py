"""Phase 10: the checks over the export, and the report a human reaches a verdict from.

Nothing here grades this solve's poker against another solver. Ruled on 2026-08-18: GTO
Wizard is a different program solving a different game, raked and with limps, so a
threshold over the gap between them measures the difference between two products rather
than anything about this extraction. `six_max_nl25_100bb.json` is still printed beside our
own numbers as context a reader can compare by eye, and nothing gates on it.

What gates instead is internal. Later position opens wider is a property of the game, and
big-blind defence tracking the opening order is a relation the export must satisfy against
itself - which means it holds at any rake basis, for any solver, at any stack depth, and
still breaks the moment a hand index is transposed or an actor mis-assigned.

The rest of the assurance is a human: decision 6c has the extractor save the solve, and a
person loads that save in GTOpen's own interface and reads range grids against the
committed report. No test can stand in for that, and these tests do not pretend to.
"""

from __future__ import annotations

import re
import sys

import pytest

from poker_training_bot.solver_artifacts.gtopen_expectations import (
    EXPECTATIONS_PATH,
    OPENING_ORDER,
    OPENING_ORDER_EXCLUSIONS,
    Aggregates,
    aggregate_frequencies,
    load_expectations,
    ordering_errors,
    reference_rows,
)
from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    SOLVE_ITERATION_CAP,
    SOLVE_TARGET_GAP_BB,
    SolverExport,
)
from poker_training_bot.solver_artifacts.gtopen_export_report import (
    COMPARISON_LABELS,
    REPORT_PATH,
    render_solver_export_report,
)
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_file_sizes import DIRECTORY_BYTE_LIMITS  # noqa: E402

DECISIONS_PATH = (
    REPO_ROOT / "reports" / "phase_audits" / "decisions"
    / "PHASE_10_SOLVER_EXTRACTION_DECISIONS.md"
)
RULED_CONFIG = {
    "positions": ["LJ", "HJ", "CO", "BTN", "SB", "BB"],
    "stack": 100.0,
    "posts": [0, 0, 0, 0, 0.5, 1.0],
    "ante": 0.0,
    "limp": False,
    "open_raises": [2.5],
    "raise_mults": [3.0],
    "max_raises": 4,
    "add_allin": False,
    "allin_threshold": 0.67,
    "rake_pct": 0.0,
    "rake_cap": 0.0,
    "no_flop_no_drop": True,
    "realization": "calibrated",
}
"""The ruled game these one-node fixtures post.

**Migrated on 2026-09-01 for decision 14's re-solve**, which flipped `add_allin` from True to
False. `one_node_export` builds a config `load_solver_export` then refused by name, so three
tests here raised before any assertion ran. The guard below stops the copy drifting again."""


def test_the_local_config_is_the_ruled_one() -> None:
    """A hand copy of a ruled constant needs one check that it is still the constant."""
    from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG as SHIPPED

    assert RULED_CONFIG == SHIPPED

# The ruled config as stage 4 measured it, for the four numbers that were captured. The
# rest are indicative and consistent with them. Each test moves one number to show what
# the check is holding.
MEASURED_OPENS = {"LJ": 19.08, "HJ": 21.64, "CO": 27.50, "BTN": 40.90, "SB": 54.09}
MEASURED_DEFENCE = {"LJ": 27.28, "HJ": 30.10, "CO": 34.00, "BTN": 40.20, "SB": 49.00}


def aggregates(open_pct: dict, defence_pct: dict, limp_pct: float = 0.0) -> Aggregates:
    return Aggregates(
        opening_pct=dict(open_pct), defence_pct=dict(defence_pct), limp_pct={"SB": limp_pct}
    )


def measured() -> Aggregates:
    return aggregates(MEASURED_OPENS, MEASURED_DEFENCE)


def ruled_answer(decision: str) -> str:
    """The bracketed answer the human ruled for one numbered decision."""
    text = DECISIONS_PATH.read_text(encoding="utf-8")
    section = re.split(rf"^## {re.escape(decision)}\.", text, flags=re.M)
    assert len(section) == 2, f"decision {decision} is not in the ruled record"
    match = re.search(r"^Answer: \[([^\]]+)\]", section[1], flags=re.M)
    assert match, f"decision {decision} carries no bracketed answer"
    return match.group(1)


def one_node_export(split: tuple[int, int, int]) -> SolverExport:
    """A root-only export whose every class plays the same mix. Enough to move an
    aggregate and see whether a check noticed."""
    return SolverExport.from_payload(
        {
            "export_schema_version": 1,
            "config": dict(RULED_CONFIG),
            "positions": list(RULED_CONFIG["positions"]),
            "quantisation_scale": QUANTISATION_SCALE,
            "nodes": [
                {
                    "path": [],
                    "actor_pos": "LJ",
                    "actions": [
                        {"label": "Fold", "kind": "fold", "to": 0.0, "terminal": True},
                        {"label": "Raise 2.5", "kind": "raise", "to": 2.5, "terminal": True},
                        {"label": "All-in 100", "kind": "jam", "to": 100.0, "terminal": True},
                    ],
                    "strategy_bp": [[weight] * 169 for weight in split],
                    "reach_bp": [QUANTISATION_SCALE] * 169,
                }
            ],
        }
    )


# --------------------------------------------------------------------------- #
# The orderings, which are internal: decision 4
# --------------------------------------------------------------------------- #


def test_the_measured_solve_passes_both_orderings() -> None:
    assert ordering_errors(measured()) == []


def test_later_position_opens_wider_holds_exactly() -> None:
    """No tolerance, because this is a property of the game rather than of a solution.

    It needs no external file to state, which is the whole point of restating it: the
    previous version asserted the same thing and also asserted something about GTO Wizard.
    """
    swapped = dict(MEASURED_OPENS)
    swapped["CO"], swapped["HJ"] = swapped["HJ"], swapped["CO"]
    assert ordering_errors(aggregates(swapped, MEASURED_DEFENCE))

    barely = dict(MEASURED_OPENS)
    barely["CO"] = barely["HJ"] - 0.01
    assert ordering_errors(aggregates(barely, MEASURED_DEFENCE))


def test_the_small_blind_is_out_of_the_opening_order_by_name_and_with_a_reason() -> None:
    """It acts with one opponent left and has the worst postflop position for the rest of
    the hand. Which of those wins is decided by rake, so its place is not structural."""
    assert OPENING_ORDER == ("LJ", "HJ", "CO", "BTN")
    assert "SB" not in OPENING_ORDER
    assert len(OPENING_ORDER_EXCLUSIONS["SB"]) > 40

    for value in (5.0, 54.09, 95.0):
        loose = dict(MEASURED_OPENS) | {"SB": value}
        assert ordering_errors(aggregates(loose, MEASURED_DEFENCE)) == []


def test_big_blind_defence_must_track_the_opening_order() -> None:
    """The tight check, and it compares the export against itself.

    Against a position that opens wider the big blind defends more, for every pair. A
    transposed hand index, a mis-assigned actor or an unnormalised row breaks this at once.
    """
    inverted = dict(MEASURED_DEFENCE)
    inverted["CO"], inverted["BTN"] = inverted["BTN"], inverted["CO"]

    errors = ordering_errors(aggregates(MEASURED_OPENS, inverted))

    assert errors
    assert any("CO" in error and "BTN" in error for error in errors)


def test_the_defence_relation_covers_the_small_blind_even_though_the_order_does_not() -> None:
    """SB leaves the opening order because rake decides where it sits. It stays in the
    defence relation, because wherever it sits the big blind must defend accordingly."""
    opens = dict(MEASURED_OPENS) | {"SB": 54.09}
    defence = dict(MEASURED_DEFENCE) | {"SB": 30.0}

    errors = ordering_errors(aggregates(opens, defence))

    assert any("SB" in error for error in errors)


def test_the_relation_is_not_a_hardcoded_position_list() -> None:
    """If the small blind opened tightest, the big blind should defend least against it.

    A check that pins a fixed order would fail this arrangement; a relation passes it,
    which is what makes it hold at any rake basis.
    """
    opens = dict(MEASURED_OPENS) | {"SB": 12.0}
    defence = dict(MEASURED_DEFENCE) | {"SB": 18.0}

    assert ordering_errors(aggregates(opens, defence)) == []


# --------------------------------------------------------------------------- #
# Nothing gates on the reference file
# --------------------------------------------------------------------------- #


def test_the_reference_file_still_holds_the_numbers_this_repo_did_not_produce() -> None:
    expectations = load_expectations(EXPECTATIONS_PATH)

    assert expectations.opening_pct["BTN"] == 40.56
    assert expectations.defence_pct["SB"] == 42.88
    assert expectations.limp_pct["SB"] == 13.73


def test_a_solve_nowhere_near_the_reference_still_passes_every_check() -> None:
    """The re-ruling, stated as a test rather than as prose in a decision record.

    These frequencies are half the reference's and internally consistent. Under the
    withdrawn directional bound that failed on ten counts. It now passes, because whether
    GTOpen agrees with GTO Wizard is not something this phase measures.
    """
    opens = {position: value / 2 for position, value in MEASURED_OPENS.items()}
    defence = {position: value / 2 for position, value in MEASURED_DEFENCE.items()}

    assert ordering_errors(aggregates(opens, defence)) == []


def test_every_reference_row_is_labelled_as_gated_by_nothing() -> None:
    """Printed for a reader to compare by eye, and labelled so nobody reads it as a check."""
    rows = reference_rows(measured(), load_expectations(EXPECTATIONS_PATH))

    assert len(rows) == 11
    assert {row.label for row in rows} == {"reported"}
    assert all(row.reference is not None and row.measured is not None for row in rows)


def test_the_expectations_module_exposes_no_tolerance_over_the_reference() -> None:
    """A withdrawn threshold that survives as a module constant is a threshold waiting to
    be wired back in by someone who did not read the ruling."""
    from poker_training_bot.solver_artifacts import gtopen_expectations

    leftovers = [
        name
        for name in dir(gtopen_expectations)
        if any(word in name.upper() for word in ("TOLERANCE", "SLACK", "PARITY", "DIRECTIONAL"))
    ]

    assert leftovers == []


# --------------------------------------------------------------------------- #
# The record and the code say the same thing
# --------------------------------------------------------------------------- #


def test_the_thresholds_that_remain_are_no_looser_than_what_was_ruled() -> None:
    """A threshold may not be widened once the numbers are visible. The loop enforces the
    ordering by freezing this file before the solve; this closes the other half, so a
    constant cannot drift from the decision record without failing here.

    Phase 14's decision 2 permits one re-solve of the ruled config at a *tighter* gap, to
    settle whether the lojack's 44 is unconverged or considered. Tightening is not
    widening, so the equality on the gap becomes a bound in the one direction the ruling
    allows and the iteration cap stays exact - a re-solve that raised either would be a
    new solve rather than the permitted one.
    """
    scale = re.search(r"basis-points-0-(\d+)", ruled_answer("8"))
    assert scale and QUANTISATION_SCALE == int(scale.group(1))

    gap = re.search(r"gap-([\d.]+)-cap-(\d+)", ruled_answer("3"))
    assert gap and 0.0 < SOLVE_TARGET_GAP_BB <= float(gap.group(1))
    assert SOLVE_ITERATION_CAP == int(gap.group(2))


def test_the_withdrawn_decisions_are_recorded_as_withdrawn() -> None:
    """Decisions 5, 6 and 6b were ruled once and then unruled. The record has to say so, or
    a later reader finds a specification for a check that does not exist and rebuilds it."""
    for decision in ("5", "6", "6b"):
        assert ruled_answer(decision) == "withdrawn"

    assert ruled_answer("4") == "internal-orderings-only"
    assert ruled_answer("6c") == "load-the-saved-solve"


def test_the_byte_limit_is_the_ruled_twenty_megabytes() -> None:
    """Decision 9. `data/artifacts/**` is covered by no size check at all today, so a
    12 MB artifact and a 40 MB one both commit with nothing objecting."""
    limit = re.match(r"(\d+)MB-total", ruled_answer("9"))
    assert limit

    assert dict(DIRECTORY_BYTE_LIMITS)["data/artifacts"] == int(limit.group(1)) * 1024 * 1024
    assert "data/samples" in dict(DIRECTORY_BYTE_LIMITS)


def test_the_gate_command_exits_nonzero_when_a_check_fails(tmp_path) -> None:
    """The library returning errors is not the same as the gate failing. A script that
    collects errors and returns zero anyway passes every other test in this file."""
    from check_solver_export_expectations import main as check_expectations

    from poker_training_bot.solver_artifacts.gtopen_export import write_solver_export

    broken = tmp_path / "broken.json.gz"
    write_solver_export(broken, one_node_export((9990, 10, 0)))

    assert check_expectations(["--export", str(broken)]) == 1


def test_the_aggregates_are_recomputed_from_the_export_rather_than_recalled() -> None:
    """A gate check that reads a number an earlier run wrote is a mirror, which is the
    defect Phase 09 found in this repo's own settlement oracle."""
    before = aggregate_frequencies(one_node_export((8000, 2000, 0)))
    after = aggregate_frequencies(one_node_export((5000, 5000, 0)))

    assert before.opening_pct["LJ"] == pytest.approx(20.0)
    assert after.opening_pct["LJ"] == pytest.approx(50.0)


# --------------------------------------------------------------------------- #
# The report a human reaches a verdict from: decisions 11 and 6c
# --------------------------------------------------------------------------- #


def test_the_report_shows_the_ruled_spots_and_says_what_it_omits() -> None:
    """The selection is stated, or the human verdict covers whatever happened to fit."""
    assert REPORT_PATH.exists(), "the report has not been generated yet"
    text = REPORT_PATH.read_text(encoding="utf-8")

    for position in ("LJ", "HJ", "CO", "BTN", "SB"):
        assert f"RFI {position}" in text
        assert f"BB vs {position}" in text
    assert "4-bet" in text
    assert re.search(r"omitted:? +\d+ spots", text)


def test_the_report_tells_a_reader_which_numbers_something_checks() -> None:
    assert REPORT_PATH.exists(), "the report has not been generated yet"
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert set(COMPARISON_LABELS) == {"gated", "reported"}
    for label in COMPARISON_LABELS:
        assert label in text


def test_the_report_names_the_saved_solve_a_human_has_to_load() -> None:
    """Decision 6c. The verification is loading that save in GTOpen and comparing grids, so
    the report has to say which file, or the comparison is against whatever is open."""
    assert REPORT_PATH.exists(), "the report has not been generated yet"
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "saved solve" in text.lower()
    assert re.search(r"[0-9a-f]{64}", text)


def test_the_renderer_labels_a_reference_number_as_gated_by_nothing() -> None:
    """Checked against a rendering rather than only the committed file, so the label is a
    property of the code and not of one lucky run."""
    text = render_solver_export_report(
        export=one_node_export((8000, 2000, 0)),
        measured=measured(),
        expectations=load_expectations(EXPECTATIONS_PATH),
    )

    reference_lines = [line for line in text.splitlines() if "40.56" in line]
    assert reference_lines
    for line in reference_lines:
        assert "reported" in line
