"""Phase 10: the three expectations checks, and the report a human reaches a verdict from.

`data/artifacts/preflop/expectations/six_max_nl25_100bb.json` holds the only numbers in
this repo that this repo did not produce, which makes it the one thing that can catch an
extraction that is uniformly wrong rather than merely self-consistent. Against a rake-free
solve it is a gross-error check and not an equality check, so what it supports is two
orderings, a one-sided bound, and a separate parity solve at a matched rake basis.

Every threshold here was ruled in
`reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md` before any solve
ran, and this file is frozen before the solve stage begins. A tolerance authored once the
numbers are visible is a tolerance fitted to them, so one test below reads the ruled record
and fails when a constant drifts away from what the human answered.
"""

from __future__ import annotations

import re
import sys

import pytest
from poker_training_bot.solver_artifacts.gtopen_expectations import (
    DEFENCE_ORDER,
    DIRECTIONAL_SLACK_PCT,
    EXPECTATIONS_PATH,
    MAX_NUMBERS_BELOW_EXPECTATION,
    OPENING_ORDER,
    OPENING_ORDER_EXCLUSIONS,
    PARITY_GATED_KEYS,
    PARITY_REPORTED_KEYS,
    PARITY_TOLERANCE_PCT,
    Aggregates,
    aggregate_frequencies,
    directional_bound_errors,
    load_expectations,
    ordering_errors,
    parity_rows,
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
    "add_allin": True,
    "allin_threshold": 0.67,
    "rake_pct": 0.0,
    "rake_cap": 0.0,
    "no_flop_no_drop": True,
    "realization": "calibrated",
}

# Indicative of the ruled config as the probe measured it, and comfortably passing every
# check below. Each test moves one number to show what the check is actually holding.
PASSING_OPENS = {"LJ": 19.08, "HJ": 22.4, "CO": 28.5, "BTN": 40.9, "SB": 54.09}
PASSING_DEFENCE = {"LJ": 27.28, "HJ": 30.1, "CO": 34.0, "BTN": 40.2, "SB": 49.0}


def aggregates(open_pct: dict, defence_pct: dict, limp_pct: float = 0.0) -> Aggregates:
    return Aggregates(
        opening_pct=dict(open_pct), defence_pct=dict(defence_pct), limp_pct={"SB": limp_pct}
    )


def passing() -> Aggregates:
    return aggregates(PASSING_OPENS, PASSING_DEFENCE)


def ruled_answer(decision_number: int) -> str:
    """The bracketed answer the human ruled for one numbered decision."""
    text = DECISIONS_PATH.read_text(encoding="utf-8")
    section = re.split(rf"^## {decision_number}\.", text, flags=re.M)
    assert len(section) == 2, f"decision {decision_number} is not in the ruled record"
    match = re.search(r"^Answer: \[([^\]]+)\]", section[1], flags=re.M)
    assert match, f"decision {decision_number} carries no bracketed answer"
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
# The reference file, and the orderings: decision 4
# --------------------------------------------------------------------------- #


def test_the_reference_file_is_the_one_this_repo_did_not_produce() -> None:
    expectations = load_expectations(EXPECTATIONS_PATH)

    assert expectations.opening_pct["BTN"] == 40.56
    assert expectations.defence_pct["SB"] == 42.88
    assert expectations.limp_pct["SB"] == 13.73


def test_the_ruled_orderings_pass() -> None:
    assert ordering_errors(passing(), load_expectations(EXPECTATIONS_PATH)) == []


def test_the_defence_order_admits_no_tolerance_at_all() -> None:
    """The tight check, and the one a transposed hand index breaks immediately."""
    expectations = load_expectations(EXPECTATIONS_PATH)
    swapped = dict(PASSING_DEFENCE)
    swapped["SB"], swapped["BTN"] = swapped["BTN"], swapped["SB"]
    assert ordering_errors(aggregates(PASSING_OPENS, swapped), expectations)

    barely = dict(PASSING_DEFENCE)
    barely["CO"] = barely["HJ"] - 0.01
    assert ordering_errors(aggregates(PASSING_OPENS, barely), expectations)


def test_the_opening_order_covers_four_positions_and_names_its_exclusion() -> None:
    """Decision 4. The small blind leaves the order because rake decides its
    limp-versus-raise mix, and the exclusion carries its reason rather than being silent."""
    assert OPENING_ORDER == ("LJ", "HJ", "CO", "BTN")
    assert DEFENCE_ORDER == ("LJ", "HJ", "CO", "BTN", "SB")
    assert len(OPENING_ORDER_EXCLUSIONS["SB"]) > 40

    expectations = load_expectations(EXPECTATIONS_PATH)
    out_of_place = dict(PASSING_OPENS) | {"SB": 60.0}
    assert ordering_errors(aggregates(out_of_place, PASSING_DEFENCE), expectations) == []

    swapped = dict(PASSING_OPENS)
    swapped["CO"], swapped["HJ"] = swapped["HJ"], swapped["CO"]
    assert ordering_errors(aggregates(swapped, PASSING_DEFENCE), expectations)


def test_the_small_blind_is_bounded_below_by_raise_plus_limp() -> None:
    """What replaces the ordering check for the widest-ranged position.

    Removing rake may reallocate between raising and limping but should not leave the
    position playing tighter overall. The bound is read off the reference file rather than
    written down, so it moves when the reference does instead of describing an older one.
    """
    expectations = load_expectations(EXPECTATIONS_PATH)
    bound = expectations.opening_pct["SB"] + expectations.limp_pct["SB"]
    assert bound == pytest.approx(48.14)

    below = dict(PASSING_OPENS) | {"SB": bound - 0.01}
    assert ordering_errors(aggregates(below, PASSING_DEFENCE), expectations)

    above = dict(PASSING_OPENS) | {"SB": bound + 0.01}
    assert ordering_errors(aggregates(above, PASSING_DEFENCE), expectations) == []


# --------------------------------------------------------------------------- #
# The directional bound: decision 5
# --------------------------------------------------------------------------- #


def test_the_directional_bound_allows_three_points_and_no_more() -> None:
    """The slack exists because a 2.55-point miss on one number, between a full solver and
    a preflop-only equity-realization model, is solver difference rather than a defect."""
    expectations = load_expectations(EXPECTATIONS_PATH)

    inside = dict(PASSING_DEFENCE)
    inside["BTN"] = expectations.defence_pct["BTN"] - DIRECTIONAL_SLACK_PCT + 0.01
    assert directional_bound_errors(aggregates(PASSING_OPENS, inside), expectations) == []

    outside = dict(PASSING_DEFENCE)
    outside["BTN"] = expectations.defence_pct["BTN"] - DIRECTIONAL_SLACK_PCT - 0.01
    assert directional_bound_errors(aggregates(PASSING_OPENS, outside), expectations)


def test_at_most_one_number_may_sit_below_its_expectation() -> None:
    """The clause that stops the slack degrading into a blanket three-point tolerance."""
    expectations = load_expectations(EXPECTATIONS_PATH)
    defence = dict(PASSING_DEFENCE)
    defence["BTN"] = expectations.defence_pct["BTN"] - 1.0
    assert directional_bound_errors(aggregates(PASSING_OPENS, defence), expectations) == []

    opens = dict(PASSING_OPENS)
    opens["CO"] = expectations.opening_pct["CO"] - 1.0
    errors = directional_bound_errors(aggregates(opens, defence), expectations)

    assert errors
    assert any(str(MAX_NUMBERS_BELOW_EXPECTATION) in error for error in errors)


def test_a_uniformly_tighter_extraction_still_fails_on_nine_counts() -> None:
    """The failure the bound is actually for, and the slack does not admit it."""
    expectations = load_expectations(EXPECTATIONS_PATH)
    opens = {key: value - 4.0 for key, value in expectations.opening_pct.items()}
    defence = {key: value - 4.0 for key, value in expectations.defence_pct.items()}

    assert len(directional_bound_errors(aggregates(opens, defence), expectations)) >= 9


def test_the_small_blind_limp_is_excluded_from_the_bound_by_name() -> None:
    """Rake's effect on how often the small blind limps rather than raises is not obviously
    signed, and a directional check must not be extended to a guess. Under the ruled config
    the number is zero by construction, and that alone must not fail the bound."""
    expectations = load_expectations(EXPECTATIONS_PATH)

    assert directional_bound_errors(passing(), expectations) == []


# --------------------------------------------------------------------------- #
# The parity comparison: decision 6
# --------------------------------------------------------------------------- #


def test_parity_gates_eight_numbers_and_reports_three() -> None:
    """Gating the small blind would mean fitting the tolerance to the one thing already
    measured to disagree, so it is reported instead - reported, not dropped."""
    assert len(PARITY_GATED_KEYS) == 8
    assert set(PARITY_REPORTED_KEYS) == {"open:SB", "defence:SB", "limp:SB"}

    expectations = load_expectations(EXPECTATIONS_PATH)
    parity = aggregates(
        dict(expectations.opening_pct), dict(expectations.defence_pct), limp_pct=1.38
    )
    parity.opening_pct["SB"] = 12.0

    rows = parity_rows(parity, expectations)

    assert {row.key for row in rows} == set(PARITY_GATED_KEYS) | set(PARITY_REPORTED_KEYS)
    assert [row.key for row in rows if row.failed] == []
    assert {row.label for row in rows if row.key in PARITY_REPORTED_KEYS} == {"reported"}


def test_parity_fails_a_gated_number_outside_the_tolerance() -> None:
    """Absolute rather than relative, because the failure this exists to catch - transposed
    suited and offsuit, an unnormalised row - moves a number by tens of points."""
    expectations = load_expectations(EXPECTATIONS_PATH)
    parity = aggregates(dict(expectations.opening_pct), dict(expectations.defence_pct))
    parity.opening_pct["BTN"] += PARITY_TOLERANCE_PCT + 0.01

    assert [row.key for row in parity_rows(parity, expectations) if row.failed] == ["open:BTN"]


# --------------------------------------------------------------------------- #
# The thresholds are the ruled ones, and the check reads the export
# --------------------------------------------------------------------------- #


def test_every_threshold_matches_what_was_ruled() -> None:
    """A tolerance may not be widened after the numbers are visible.

    The loop enforces the ordering mechanically by freezing this file before the solve
    runs. This closes the other half: a constant edited without a matching re-ruling in
    the decision record fails here, so code and record cannot drift apart quietly.
    """
    slack = re.search(r"minus-(\d+)-points", ruled_answer(5))
    assert slack and DIRECTIONAL_SLACK_PCT == float(slack.group(1))
    assert "at-most-one-below" in ruled_answer(5)
    assert MAX_NUMBERS_BELOW_EXPECTATION == 1

    parity = re.match(r"(\d+)-points-on-eight", ruled_answer(6))
    assert parity and PARITY_TOLERANCE_PCT == float(parity.group(1))

    scale = re.search(r"basis-points-0-(\d+)", ruled_answer(8))
    assert scale and QUANTISATION_SCALE == int(scale.group(1))

    gap = re.search(r"gap-([\d.]+)-cap-(\d+)", ruled_answer(3))
    assert gap and SOLVE_TARGET_GAP_BB == float(gap.group(1))
    assert SOLVE_ITERATION_CAP == int(gap.group(2))


def test_the_byte_limit_is_the_ruled_twenty_megabytes() -> None:
    """Decision 9. `data/artifacts/**` is covered by no size check at all today, so a
    12 MB artifact and a 40 MB one commit with nothing objecting."""
    limit = re.match(r"(\d+)MB-total", ruled_answer(9))
    assert limit

    assert dict(DIRECTORY_BYTE_LIMITS)["data/artifacts"] == int(limit.group(1)) * 1024 * 1024
    assert "data/samples" in dict(DIRECTORY_BYTE_LIMITS)


def test_the_gate_command_exits_nonzero_when_a_check_fails(tmp_path) -> None:
    """The library functions returning errors is not the same as the gate failing.

    `check_solver_export_expectations` is what the gate runs, and a script that collects
    errors and returns zero anyway passes every other test in this file.
    """
    from check_solver_export_expectations import main as check_expectations
    from poker_training_bot.solver_artifacts.gtopen_export import write_solver_export

    broken = tmp_path / "broken.json.gz"
    write_solver_export(broken, one_node_export((9990, 10, 0)))

    assert check_expectations(["--export", str(broken)]) == 1


def test_the_aggregates_are_recomputed_from_the_export_rather_than_recalled() -> None:
    """A gate check that reads a number an earlier run wrote is a mirror, which is the
    defect Phase 09 found in this repo's own settlement oracle. Perturbing the export has
    to move the answer."""
    before = aggregate_frequencies(one_node_export((8000, 2000, 0)))
    after = aggregate_frequencies(one_node_export((5000, 5000, 0)))

    assert before.opening_pct["LJ"] == pytest.approx(20.0)
    assert after.opening_pct["LJ"] == pytest.approx(50.0)


# --------------------------------------------------------------------------- #
# The report a human reaches a verdict from: decision 11
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


def test_every_comparison_in_the_report_carries_one_of_the_four_labels() -> None:
    """A reader must be able to tell which numbers are held to equality, which are only
    bounded, and which are gated by nothing at all."""
    assert REPORT_PATH.exists(), "the report has not been generated yet"
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert set(COMPARISON_LABELS) == {"ordering", "directional", "tolerance", "reported"}
    for label in COMPARISON_LABELS:
        assert label in text


def test_the_renderer_labels_a_reported_number_as_gated_by_nothing() -> None:
    """Checked against a rendering rather than only the committed file, so the label is a
    property of the code and not of one lucky run."""
    measured = passing()

    text = render_solver_export_report(
        export=one_node_export((8000, 2000, 0)),
        measured=measured,
        parity=measured,
        expectations=load_expectations(EXPECTATIONS_PATH),
    )

    reported_lines = [line for line in text.splitlines() if "limp" in line.lower() and "SB" in line]
    assert reported_lines
    for line in reported_lines:
        assert "reported" in line
