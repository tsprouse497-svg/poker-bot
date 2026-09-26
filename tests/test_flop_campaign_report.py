"""Phase 21, stage 4: the report, and the figures its generator has to re-derive.

Authored before the generator exists. `scripts/generate_flop_campaign_report.py` is reached through
a fixture that first asserts the file exists - so its absence is an assertion rather than a
`ModuleNotFoundError` naming `scripts` - and then imports it inside the function body.

**Every figure the contract names is re-derived by the generator from committed files, and one
that does not reconcile exits non-zero.** A report renders whatever it is handed, so each check
below feeds the generator a copy of the committed postflop tree with one field altered and
requires a `ReportFigureError`, with a positive control beside it.

**A figure not yet measured says so.** When the gate first goes green the rented-box figures do
not exist - the candidate costs, the box's determinism re-run, the six texture solves, the table
re-run - and the Mac's thread sweep may not either. The generator reads each from its committed
record under `data/artifacts/postflop/campaign/`, and where the record is absent it prints
`NOT_YET_MEASURED` on that figure's line rather than a number. A zero, a blank or an estimate in
that place is the made-up number the contract forbids.
"""

from __future__ import annotations

import json
import re
import shutil
import sys

import pytest

from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402

COMMAND_ID = "generate_flop_campaign_report"
SCRIPT = REPO_ROOT / "scripts" / f"{COMMAND_ID}.py"
POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "flop_campaign"
COMMITTED_LINE = "BTN:raise@2.5,BB:call"
ADMITTED = (
    "SB:raise@2.5,BB:call",
    "BTN:raise@2.5,BB:call",
    "CO:raise@2.5,BB:call",
    "HJ:raise@2.5,BB:call",
    "LJ:raise@2.5,BB:call",
)
REPORT_BYTE_CAP = 300 * 1024
"""`BYTE_LIMITS` in `scripts/check_file_sizes.py` for `reports/active/*.txt`."""


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
    """Named rather than `Exception`: `pytest.raises(Exception)` also passes on a `TypeError`
    from a signature that moved."""
    return owed(generator, "ReportFigureError")


@pytest.fixture(scope="module")
def committed_report(generator) -> str:
    return owed(generator, "render_report")(POSTFLOP_DIR)


@pytest.fixture
def tree_copy(tmp_path):
    """The committed postflop tree, copied, with every campaign record taken out: the state of
    the tree before any rented-box figure exists."""
    copied = tmp_path / "postflop"
    shutil.copytree(POSTFLOP_DIR, copied)
    shutil.rmtree(copied / "campaign", ignore_errors=True)
    return copied


def committed_manifest_path(copied):
    for path in sorted((copied / "manifests").glob("*.json")):
        if json.loads(path.read_text(encoding="utf-8")).get("preflop_line") == COMMITTED_LINE:
            return path
    raise AssertionError("no manifest for the committed line in the copied tree")


def rewrite(path, change) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    change(document)
    path.write_text(json.dumps(document, indent=1) + "\n", encoding="utf-8")


def committed_tree_without(copied):
    """A second copy of the tree beside `copied`, with no campaign records at all."""
    bare = copied.parent / "bare"
    if not bare.exists():
        shutil.copytree(POSTFLOP_DIR, bare)
        shutil.rmtree(bare / "campaign", ignore_errors=True)
    return bare


def cost_row(row: str) -> bool:
    """A row carrying the cost-per-solved-flop figure: its label, then a colon."""
    return row.strip().lower().startswith("cost per solved flop:")


TEN_THREAD_SPREAD = re.compile(r"(?<![\d.])7\.40?(?![\d])")
TEN_THREADS = re.compile(r"(?<![\d.])10(?![\d.])")


def write_record(copied, name: str, document) -> None:
    (copied / "campaign").mkdir(exist_ok=True)
    (copied / "campaign" / name).write_text(json.dumps(document, indent=1) + "\n", "utf-8")


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #


class TestTheCommandsAreRegistered:
    def test_both_command_ids_are_registered(self) -> None:
        assert COMMAND_ID in COMMANDS
        assert "pytest_flop_campaign" in COMMANDS

    def test_the_generator_command_runs_this_script(self) -> None:
        assert f"scripts/{COMMAND_ID}.py" in COMMANDS[COMMAND_ID].command

    def test_the_test_command_runs_every_flop_campaign_test_file(self) -> None:
        files = sorted(
            str(path.relative_to(REPO_ROOT))
            for path in (REPO_ROOT / "tests").glob("test_flop_campaign*.py")
        )
        command = COMMANDS["pytest_flop_campaign"].command

        assert files and all(name in command for name in files)
        assert "tests/test_postflop_solve_driver.py" in command


# --------------------------------------------------------------------------- #
# The committed report
# --------------------------------------------------------------------------- #


class TestTheReportPrintsWhatTheContractNames:
    """Criterion: the report prints every figure this contract names. Tokens are checked, not
    layout: the five lines in the ruled order, the excluded limp, the closure counts, the memory
    bar's board class, the flop count everything is a share of, and phase 16's ceiling."""

    def test_the_committed_tree_renders_without_a_refusal(self, committed_report) -> None:
        assert committed_report.strip()
        assert len(committed_report.encode("utf-8")) <= REPORT_BYTE_CAP

    def test_the_admitted_lines_appear_in_the_ruled_order(self, committed_report) -> None:
        positions = [committed_report.find(line) for line in ADMITTED]

        assert -1 not in positions, positions
        assert positions == sorted(positions)

    def test_the_excluded_limp_is_named_with_its_reason(self, committed_report) -> None:
        assert "SB:call" in committed_report
        assert "limp" in committed_report.lower()

    def test_the_closure_counts_are_printed(self, committed_report) -> None:
        for figure in ("6,419", "1,477,056", "30,772"):
            assert figure in committed_report, figure

    def test_the_small_blind_line_s_own_figures_are_printed(self, committed_report) -> None:
        """Every per-line figure is printed per line, so the small blind's 5.0-pot tree shows
        its own closure counts, its own bar and its own reach, not the button's repeated. The bar
        is printed in the server's unit, bytes, so the figure does not depend on decision 14's
        reading."""
        for figure in ("6,566", "1,545,264", "32,193", "17,674,107,736", "5.53"):
            assert figure in committed_report, figure

    def test_the_memory_bar_names_its_board_class(self, committed_report) -> None:
        assert "2c2d2h" in committed_report

    def test_coverage_is_a_share_of_every_flop_and_sits_beside_phase_16_s_ceiling(
        self, committed_report
    ) -> None:
        assert "22,100" in committed_report
        assert "74.9" in committed_report

    def test_the_river_under_the_dealt_turn_is_said_not_to_be_kept(self, committed_report):
        assert "not kept" in committed_report.lower()


# --------------------------------------------------------------------------- #
# A figure not yet measured says so
# --------------------------------------------------------------------------- #


class TestAFigureNotYetMeasuredSaysSo:
    def test_the_phrase_is_published(self, generator) -> None:
        assert owed(generator, "NOT_YET_MEASURED") == "not yet measured"

    def test_a_tree_with_no_campaign_records_renders_and_says_what_is_missing(
        self, generator, tree_copy
    ) -> None:
        text = owed(generator, "render_report")(tree_copy)

        assert owed(generator, "NOT_YET_MEASURED") in text

    def test_no_cost_per_solved_flop_is_printed_before_a_candidate_is_timed(
        self, generator, tree_copy
    ) -> None:
        """Checked on the figure's own rows - lines whose label is `cost per solved flop:` - so
        prose may use the contract's phrase freely."""
        text = owed(generator, "render_report")(tree_copy)
        rows = [row for row in text.splitlines() if cost_row(row)]

        assert rows, "the report must name the figure even when it has no value yet"
        assert all(owed(generator, "NOT_YET_MEASURED") in row for row in rows), rows


# --------------------------------------------------------------------------- #
# A committed record that disagrees with its re-derivation fails the generator
# --------------------------------------------------------------------------- #


class TestTheGeneratorRefusesAFigureThatDoesNotReconcile:
    def test_a_closed_board_short_of_one_river_decision_point_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        rewrite(
            committed_manifest_path(tree_copy),
            lambda m: m["boards"][0]["decision_points"].update(river=1_477_055),
        )

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)

    def test_a_flops_held_figure_that_disagrees_with_the_boards_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        rewrite(
            committed_manifest_path(tree_copy), lambda m: m.update(flops_held=m["flops_held"] + 1)
        )

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)

    def test_a_phase_16_board_whose_figures_differ_from_the_index_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        """The closed board and the committed cell came off one solve, so their iteration
        counts are one number; two numbers is two solves mixed."""

        def change(manifest):
            for entry in manifest["boards"]:
                if entry["board"] == ["Kh", "7d", "2c"]:
                    entry["iterations"] += 20

        rewrite(committed_manifest_path(tree_copy), change)

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)


# --------------------------------------------------------------------------- #
# The thread sweep and the spend ledger, re-derived from their records
# --------------------------------------------------------------------------- #

SWEEP_RUNS = [
    (count, seconds)
    for round_ in range(3)
    for count, seconds in (
        (3, (4.0, 4.1, 3.9)[round_]),
        (5, (2.6, 2.5, 2.7)[round_]),
        (8, (1.9, 2.0, 1.8)[round_]),
        (10, (1.7, 1.6, 9.0)[round_]),
    )
]


def m4_sweep_record():
    import poker_training_bot.solver_artifacts.postflop_machine as machine
    import poker_training_bot.solver_artifacts.postflop_threads as threads

    values = {}
    for line in (FIXTURES / "darwin_apple_m4.sysctl.txt").read_text("utf-8").splitlines():
        key, _, value = line.partition(": ")
        values[key] = value

    def no_proc(path: str) -> str:
        raise FileNotFoundError(path)

    m4 = machine.measure_machine(platform="Darwin", sysctl=values.__getitem__, read_text=no_proc)
    return {"record_schema_version": 1, "machines": [threads.sweep_record(m4, SWEEP_RUNS)]}


def a_ledger(entries):
    import poker_training_bot.solver_artifacts.postflop_campaign_costs as costs

    ledger = costs.SpendLedger(cap_usd=100.0)
    for machine, hours, price in entries:
        ledger.record(machine=machine, hours=hours, price_per_hour_usd=price, what="trial")
    return {"record_schema_version": 1, "ledgers": {"benchmark": ledger.to_document()}}


class TestTheCampaignRecordsAreReDerived:
    """Criteria: the report prints each thread-sweep run's seconds per iteration and the spread,
    and the money spent against the cap it counts against; the generator re-derives both."""

    def test_a_consistent_sweep_prints_its_choice_and_spread(self, generator, tree_copy) -> None:
        write_record(tree_copy, "thread_sweep.json", m4_sweep_record())

        text = owed(generator, "render_report")(tree_copy)

        assert "Apple M4" in text
        rows = [row for row in text.splitlines() if TEN_THREAD_SPREAD.search(row)]
        assert any(TEN_THREADS.search(row) for row in rows), (
            "ten threads' spread, 9.0 less 1.6, printed on ten threads' row"
        )
        baseline = owed(generator, "render_report")(committed_tree_without(tree_copy))
        assert not TEN_THREAD_SPREAD.search(baseline), "7.4 must come from the sweep record"

    def test_a_sweep_whose_choice_is_not_the_fastest_median_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        record = m4_sweep_record()
        record["machines"][0]["chosen_threads"] = 8
        write_record(tree_copy, "thread_sweep.json", record)

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)

    def test_a_sweep_whose_counts_are_another_machine_s_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        record = m4_sweep_record()
        record["machines"][0]["machine"]["logical_processors"] = 64
        write_record(tree_copy, "thread_sweep.json", record)

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)

    def test_a_consistent_ledger_prints_its_total_beside_the_cap(self, generator, tree_copy):
        write_record(tree_copy, "spend_ledger.json", a_ledger([("invented-a", 2.0, 2.0)]))

        text = owed(generator, "render_report")(tree_copy)

        assert any("$4.00" in row and "$100.00" in row for row in text.splitlines())
        baseline = owed(generator, "render_report")(committed_tree_without(tree_copy))
        assert "$4.00" not in baseline, "the total must come from the ledger record"

    def test_a_ledger_whose_total_is_not_its_entries_fails(
        self, generator, refusal, tree_copy
    ) -> None:
        record = a_ledger([("invented-a", 2.0, 2.0)])
        record["ledgers"]["benchmark"]["total_usd"] = 3.0
        write_record(tree_copy, "spend_ledger.json", record)

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)

    def test_a_ledger_past_its_cap_fails(self, generator, refusal, tree_copy) -> None:
        """Work halts at a cap rather than past it, so a committed ledger past its cap is a
        record of the rule being broken, and the report does not publish it as a total."""
        record = a_ledger([("invented-a", 30.0, 3.0)])
        entries = record["ledgers"]["benchmark"]["entries"]
        entries.append(
            {**entries[0], "machine": "invented-b", "hours": 10.0, "price_per_hour_usd": 1.5}
        )
        record["ledgers"]["benchmark"]["total_usd"] = 105.0
        write_record(tree_copy, "spend_ledger.json", record)

        with pytest.raises(refusal):
            owed(generator, "render_report")(tree_copy)


# --------------------------------------------------------------------------- #
# The command itself
# --------------------------------------------------------------------------- #


class TestTheCommandExitsOnTheVerdict:
    def test_the_command_writes_the_report_and_exits_zero_on_the_committed_tree(
        self, generator, tmp_path
    ) -> None:
        output = tmp_path / "report.txt"

        assert (
            owed(generator, "main")(["--postflop-dir", str(POSTFLOP_DIR), "--output", str(output)])
            == 0
        )
        assert output.read_text(encoding="utf-8").strip()

    def test_the_command_exits_non_zero_on_a_figure_that_does_not_reconcile(
        self, generator, tree_copy, tmp_path
    ) -> None:
        rewrite(committed_manifest_path(tree_copy), lambda m: m.update(refused_boards=7))
        output = tmp_path / "report.txt"

        assert (
            owed(generator, "main")(["--postflop-dir", str(tree_copy), "--output", str(output)])
            != 0
        )

    def test_the_default_output_is_the_contract_s_report_path(self, generator) -> None:
        expected = REPO_ROOT / "reports" / "active" / "latest_flop_campaign_report.txt"

        assert owed(generator, "REPORT_PATH") == expected
