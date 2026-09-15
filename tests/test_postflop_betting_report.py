"""Phase 16, stage 4: the report, and the figures the generator has to re-derive.

Authored before any implementation exists. The generator is reached through a fixture whose import
sits in the function body; the head of `tests/test_postflop_key.py` says why.

**Every figure the contract names as an obligation is printed by the report and re-derived by the
generator, which exits non-zero when one does not hold.** A report renders whatever it is handed:
a byte count that disagrees with the bytes on disk, a coverage share that pools two loss causes, or
an exploitability figure printed without the menu qualification all exit 0 and publish as happily
as the right numbers would. This repo has twice shipped a validator that could not fail, so each
one here is fed a wrong input and made to refuse, with one positive control beside it - several
tests below read "it refused", which a generator that refuses everything satisfies.

**What no report may say.** No accuracy for the solve as a whole. No winrate and no EV figure over
this artifact, because the hands they would come from are the ones that ended at the turn refusal,
so the number does not exist. No scaled figure reported as measured, and no capped solve's wall
clock as a cost.
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_verify import COMMANDS  # noqa: E402

COMMAND_ID = "generate_postflop_betting_report"
SCRIPT = REPO_ROOT / "scripts" / f"{COMMAND_ID}.py"
REPORT = REPO_ROOT / "reports" / "active" / "latest_postflop_betting_report.txt"

REPORT_BYTE_CAP = 300 * 1024
"""`BYTE_LIMITS` in `scripts/check_file_sizes.py` for `reports/active/*.txt`."""


@pytest.fixture(scope="module")
def refusal(generator):
    """The error the generator raises when a figure it publishes does not re-derive.

    Named rather than `Exception`, because `pytest.raises(Exception)` also passes on a
    `TypeError` from a signature that moved, which is a test agreeing with a broken call.
    """
    return owed(generator, "ReportFigureError")


@pytest.fixture(scope="module")
def generator():
    """The script stage 6 writes, reached inside the fixture rather than imported at the top."""
    import scripts.generate_postflop_betting_report as module

    return module


@pytest.fixture(scope="module")
def refusal_codes():
    """The strategy's own closed refusal vocabulary, taken from the module that produces the
    codes rather than scraped out of the report, so a code the generator quietly left out of its
    breakdown is a red here rather than an absence nothing looks for."""
    import poker_training_bot.strategy.postflop_betting as module

    found = getattr(module, "REFUSAL_CODES", None)
    assert found, (
        "strategy.postflop_betting must publish a non-empty REFUSAL_CODES; the report's vacuity"
        " labels are checked against it rather than against the report's own list, and an empty"
        " vocabulary would make every check that reads it pass over nothing"
    )
    return tuple(found)


@pytest.fixture(scope="module")
def report() -> str:
    assert REPORT.is_file(), (
        f"{REPORT.relative_to(REPO_ROOT)} is missing, so `{COMMAND_ID}` has not run"
    )
    return REPORT.read_text(encoding="utf-8")


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"scripts/{COMMAND_ID}.py must publish {name}(), which phase 16's contract requires and"
        " which the generator does not implement yet"
    )
    return found


def says(report: str, *phrases: str) -> bool:
    lowered = report.lower()
    return all(phrase.lower() in lowered for phrase in phrases)


# --------------------------------------------------------------------------- #
# Three properties this file decides itself, beside the generator's own validator
# --------------------------------------------------------------------------- #
#
# Stage 4's mechanical review held the stage over these three. Each test was a bare
# `assert owed(generator, "<name>")(report) is True`, and each of those names occurs exactly once
# in the whole repo - at its own call site here - so the entire claim was "the code under test
# says the code under test is fine", and `def <name>(report): return True` passed all three, on
# three of the criteria a reader is least able to check by eye. The fix keeps the validator
# requirement and adds the property, decided here, against the report text, so a generator whose
# validator lies reds on the second assertion. Each predicate has a negative control in
# `TestThisFileSOwnPredicatesCanFail`: a predicate that cannot return False is the same defect.

EXPLOITABILITY_FIGURE = re.compile(r"exploitability[^\n]*?\d+(?:\.\d+)?\s*%", re.IGNORECASE)
TEXTURE = re.compile(r"\b(rainbow|two-tone|monotone)\b", re.IGNORECASE)
STANDALONE_INTEGER = re.compile(r"(?<!\S)(\d+)(?!\S)")


def exploitability_figure_lines(report: str) -> list[str]:
    """Every line that prints an exploitability figure, whole report, no block to point at."""
    return [line for line in report.splitlines() if EXPLOITABILITY_FIGURE.search(line)]


def every_exploitability_figure_names_the_menu(report: str) -> bool:
    """Criterion: the published exploitability is a bound only against an opponent confined to
    the same bet menu, and the report says so **wherever it prints the figure**. Line by line,
    because one footnote at the bottom of the page is not "wherever": the marker is the word
    `menu` on the line, and a line printing the number without it reads as an unconditional
    accuracy, which is the claim the contract bans."""
    lines = exploitability_figure_lines(report)
    return bool(lines) and all("menu" in line.lower() for line in lines)


def cost_rows(report: str) -> list[str]:
    """Every line that puts a number beside a board texture.

    Deliberately the whole report rather than a block the generator hands over. A generator that
    chose its own rows could publish an unlabelled figure by leaving it out of the list, which is
    the same unfalsifiable shape as returning True.
    """
    return [line for line in report.splitlines() if TEXTURE.search(line) and re.search(r"\d", line)]


def every_cost_row_declares_measured_or_scaled(report: str) -> bool:
    """Criterion: the cost model separates measured from scaled, and no scaled figure is reported
    as measured. Rainbow, 455 of the 1,755 classes, was never solved to target, so **every**
    rainbow figure is scaled from an orbit factor: a rainbow row carries `scaled` and must not
    carry `measured`. Every other texture row declares which of the two it is."""
    rows = cost_rows(report)
    if not rows:
        return False
    for line in rows:
        lowered = line.lower()
        if "rainbow" in lowered:
            if "scaled" not in lowered or "measured" in lowered:
                return False
        elif "measured" not in lowered and "scaled" not in lowered:
            return False
    return True


def code_rows(report: str, codes) -> dict[str, list[str]]:
    """The breakdown row for each refusal code: the line naming it that carries a bare count.

    The count has to be a whitespace-delimited token, which is what stops a digit inside a code
    name being read as a count.
    """
    rows: dict[str, list[str]] = {}
    for line in report.splitlines():
        if not STANDALONE_INTEGER.search(line):
            continue
        for code in codes:
            if code in line:
                rows.setdefault(code, []).append(line)
    return rows


def row_count(line: str) -> int:
    return int(STANDALONE_INTEGER.findall(line)[-1])


def vacuity_labels_match_the_counts(report: str, codes) -> bool:
    """Criterion: the refusal counts are broken out by code, with any vacuous one labelled.

    Both directions, because a report that labelled nothing and one that labelled everything both
    pass a naive search for the word. The codes come from the strategy's own closed vocabulary
    rather than from the report, so a code left out of the breakdown fails here.

    **An empty code list is refused here rather than by the fixture that fills it.** Over no codes
    every clause below is vacuously satisfied - `sorted({}) == sorted(())`, then an empty loop - so
    this returned `True` for any report at all, and what closed it was
    `test_the_refusal_vocabulary_is_a_closed_list` in another file. That is the shape this whole
    block exists to correct, one level down: a guard covered by a sibling is not a guard."""
    if not codes:
        return False
    rows = code_rows(report, codes)
    if sorted(rows) != sorted(codes):
        return False
    for found in rows.values():
        if len(found) != 1:
            return False
        line = found[0]
        if ("vacuous" in line.lower()) != (row_count(line) == 0):
            return False
    return True


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #


class TestTheCommandIsRegisteredAndRuns:
    def test_both_of_this_phase_s_command_ids_are_registered(self) -> None:
        assert "pytest_postflop_betting" in COMMANDS
        assert COMMAND_ID in COMMANDS

    def test_the_generator_script_exists_where_the_command_points(self) -> None:
        assert SCRIPT.is_file()

    def test_the_command_publishes_on_good_input(self) -> None:
        """The positive control for every refusal test below."""
        result = subprocess.run(
            COMMANDS[COMMAND_ID].command, cwd=REPO_ROOT, capture_output=True, text=True
        )

        assert result.returncode == 0, result.stderr

    def test_the_report_fits_the_reports_byte_cap(self, report) -> None:
        assert len(report.encode("utf-8")) <= REPORT_BYTE_CAP


# --------------------------------------------------------------------------- #
# The figures
# --------------------------------------------------------------------------- #


class TestTheCoverageFigures:
    """Criterion: the covered lines, their servable corpus ranks and which constraint bound the
    count; the flop-reaching count and the servable share of corpus flops by loss cause."""

    def test_the_covered_lines_are_listed(self, report) -> None:
        assert says(report, "covered preflop line")

    def test_the_ranking_sorts_on_servable_arrival_rather_than_arrival(self, report) -> None:
        """A 3-bet line serves 47.1% of its arrivals against a single-raised line's 99.0%, so the
        quantity the ranking sorts on is servable arrival frequency. Decision 10 drew that
        consequence for decision 3 and nobody had before."""
        assert says(report, "servable")

    def test_the_report_names_which_constraint_bound_the_line_count(self, report) -> None:
        """How many lines are covered is an output rather than a choice: as many as the campaign
        cost and the index each afford, whichever is smaller, and the report names which."""
        assert says(report, "bound by") and (says(report, "campaign") or says(report, "index"))

    def test_the_report_says_the_keys_are_post_substitution(self, report) -> None:
        """Every corpus-derived key reads `@2.5` against a corpus median open of 2.25bb. A reader
        taking the ranking at face value is reading a ranking of substituted keys."""
        assert says(report, "post-substitution") or says(report, "substituted")
        assert "2.25" in report

    def test_the_report_separates_reaching_a_decision_point_from_seeing_a_flop(
        self, report
    ) -> None:
        """The flop-reaching filter is a different query, which this phase computes and
        publishes; nothing in the repo computed it before."""
        assert says(report, "flop-reaching") or says(report, "reached a flop")

    def test_the_corpus_ranking_is_cross_checked_against_the_artifact_s_own_order(
        self, report
    ) -> None:
        assert says(report, "arrival_ppb")

    def test_the_report_prints_where_the_two_orders_disagree(self, report) -> None:
        assert says(report, "disagree")

    def test_the_share_of_corpus_flops_this_artifact_can_answer_is_printed(
        self, report
    ) -> None:
        assert says(report, "share of corpus flops")

    def test_the_loss_is_split_by_cause_and_multiway_is_named_structural(self, report) -> None:
        """A two-range solve cannot express a three-handed flop at any budget, machine or menu, so
        the multiway share is structural rather than fundable.
        `THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`."""
        assert says(report, "multiway", "structural")


class TestTheAccuracyFigures:
    """Criterion: per-spot achieved exploitability and iteration count with the 0.3%-to-1%
    distribution, and no report may state an accuracy for the solve as a whole."""

    def test_the_target_and_the_ceiling_are_both_printed(self, report) -> None:
        assert "0.3" in report
        assert "1%" in report or "1.0%" in report

    def test_the_distribution_between_target_and_ceiling_is_printed_by_board_and_line(
        self, report
    ) -> None:
        """1% is the worst a played cell may carry, not an accuracy anyone aimed at. How many
        cells sit between 0.3% and 1% of pot, on which boards and lines."""
        assert says(report, "between 0.3") or says(report, "0.3% to 1")

    def test_the_iteration_cap_is_printed(self, report) -> None:
        assert "1,200" in report or "1200" in report

    def test_no_line_states_an_accuracy_for_the_solve_as_a_whole(self, report) -> None:
        """The one sentence this phase must never publish. A per-cell figure is evidence; a
        single figure for the artifact is a claim nothing measured."""
        banned = re.compile(
            r"(the\s+)?solve\s+is\s+accurate\s+to|"
            r"overall\s+exploitability|"
            r"the\s+artifact\s+is\s+accurate\s+to",
            re.IGNORECASE,
        )

        assert banned.search(report) is None, banned.search(report).group(0)

    def test_the_menu_qualification_appears_wherever_the_figure_is_printed(
        self, generator, report
    ) -> None:
        """The published exploitability is a bound only against an opponent confined to the same
        bet menu. Checked line by line rather than once for the whole document, because a single
        footnote at the bottom is not "wherever it prints the figure".

        Two assertions, not one. The generator owes the validator - the contract requires it to
        exit non-zero on this - and the property is decided here as well, so a generator whose
        validator returns True over an unqualified report reds on the second line.
        """
        qualified = owed(generator, "exploitability_lines_are_qualified")

        assert qualified(report) is True
        assert exploitability_figure_lines(report), (
            "no line of the report prints an exploitability figure at all, so the qualification"
            " has nothing to qualify and the validator above passed vacuously"
        )
        unqualified = [
            line for line in exploitability_figure_lines(report) if "menu" not in line.lower()
        ]
        assert unqualified == [], unqualified

    def test_convergence_is_not_reported_as_settled(self, report) -> None:
        """A solve at the committed iteration count is not proven to have converged.
        Exploitability was targeted; frequencies on indifferent hands settle later and nothing
        here has diffed a deep solve against a shallow one."""
        unproven = says(report, "convergence", "unproven")
        assert says(report, "not proven to have converged") or unproven

    def test_the_count_of_cells_rejected_above_one_percent_is_printed(self, report) -> None:
        assert says(report, "rejected above 1")


class TestTheDeterminismRecord:
    """Criterion: the report records that the committed configuration was solved twice, the two
    strategies compared, and whether they were byte-identical.

    That is what gives the halt a surface: a report saying not-byte-identical beside a phase that
    did not halt is a visible contradiction. No tolerance is set here and no implementer may pick
    one.
    """

    def test_the_report_says_the_configuration_was_solved_twice(self, report) -> None:
        assert says(report, "solved twice")

    def test_the_report_says_whether_the_two_strategies_were_byte_identical(
        self, report
    ) -> None:
        assert says(report, "byte-identical")

    def test_the_report_does_not_publish_a_determinism_tolerance(self, report) -> None:
        """If they are not byte-identical the phase halts and Taylor is asked. A tolerance in the
        report is an implementer having picked one."""
        assert not says(report, "within tolerance")
        assert not says(report, "determinism tolerance")


class TestTheMenuAndTheCostModel:
    """Criterion: the report states that nothing in the record uses 66% or 125%, and that no line
    this menu offers gets all-in in a single-raised pot; and the cost model separates measured
    from scaled."""

    def test_the_committed_menu_is_printed(self, report) -> None:
        for size in ("33", "75", "66", "125", "2.5x"):
            assert size in report, size

    def test_the_report_says_nothing_in_the_record_uses_sixty_six_or_one_twenty_five(
        self, report
    ) -> None:
        """The turn and river half of the ruled menu is configured and never exercised, because
        the phase is flop-only. A reader seeing `66 125` in the config has to be told that, or
        the menu reads as evidence about streets nothing was solved for."""
        assert re.search(
            r"nothing in the record uses (66|66%) (and|or) (125|125%)", report, re.IGNORECASE
        ), "the report has to say in terms that no record uses the turn and river sizes"

    def test_the_report_says_no_line_this_menu_offers_gets_all_in_single_raised(
        self, report
    ) -> None:
        assert says(report, "all-in", "single-raised")

    def test_every_scaled_cost_figure_is_labelled_scaled(self, generator, report) -> None:
        """Rainbow, 455 of the 1,755 classes, was never solved to target, so every rainbow figure
        is scaled from an exact orbit factor. Do not report a scaled figure as measured.
        `POSTFLOP-COST-MODEL-HAS-NO-RAINBOW-CELL` stays open.

        The rows are found here, over the whole report, rather than taken from the generator: a
        generator that picked its own rows could publish an unlabelled figure by leaving it out
        of the list it hands over.
        """
        labelled = owed(generator, "cost_rows_declare_measured_or_scaled")

        assert labelled(report) is True
        rows = cost_rows(report)
        assert rows, "no line of the report puts a figure beside a texture, so there is no cost"
        undeclared = [
            line
            for line in rows
            if "measured" not in line.lower() and "scaled" not in line.lower()
        ]
        assert undeclared == [], undeclared
        rainbow_as_measured = [
            line
            for line in rows
            if "rainbow" in line.lower()
            and ("measured" in line.lower() or "scaled" not in line.lower())
        ]
        assert rainbow_as_measured == [], rainbow_as_measured

    def test_the_rainbow_class_count_is_printed_and_is_the_deck_s(self, report) -> None:
        assert "455" in report
        assert "1,755" in report or "1755" in report

    def test_no_capped_solve_s_wall_clock_is_printed_as_a_cost(self, report) -> None:
        assert not says(report, "cost: capped")


class TestTheBehaviourFigures:
    """Criterion: the bet and raise frequencies; the refusal counts by code and by the two table
    causes, with any vacuous one labelled; and the pot-odds firing rate."""

    def test_the_bet_and_raise_frequencies_are_printed(self, report) -> None:
        assert says(report, "bet frequency") or says(report, "bets")
        assert says(report, "raise frequency") or says(report, "raises")

    def test_the_refusal_counts_are_broken_out_by_code(self, report) -> None:
        assert says(report, "refusals by code")

    def test_the_two_table_causes_are_printed_and_never_pooled(self, report) -> None:
        """Two causes, not three. How many cells the campaign rejected above 1% of pot is a report
        figure, not a table cause, and the criterion pre-empts the mistake in terms."""
        assert says(report, "no cell for this board or line")
        assert says(report, "not fetched")

    def test_the_report_says_never_solved_and_solved_but_rejected_are_one_absence(
        self, report
    ) -> None:
        """Both are the same absence at query time, because neither is in the artifact and the
        query meets one absence. The report says so rather than letting a reader think the phase
        never looked."""
        assert says(report, "never solved") and says(report, "rejected")

    def test_a_vacuous_refusal_code_is_labelled_as_one(
        self, generator, report, refusal_codes
    ) -> None:
        """Conditional: the board-miss code is live on the ruled design, so the label appears only
        where a code really did fire zero times. A report that labelled nothing and a report that
        labelled everything both pass a naive text check.

        The codes come from `strategy.postflop_betting.REFUSAL_CODES`, so the breakdown has to
        carry every code the strategy can return. A code with no row is the cheapest way to make
        a vacuity check pass, and it is the one this catches.
        """
        labelled = owed(generator, "vacuous_codes_are_labelled")

        assert labelled(report) is True
        rows = code_rows(report, refusal_codes)
        missing = sorted(set(refusal_codes) - set(rows))
        assert missing == [], missing
        wrong = {
            code: found[0]
            for code, found in rows.items()
            if len(found) != 1
            or ("vacuous" in found[0].lower()) != (row_count(found[0]) == 0)
        }
        assert wrong == {}, wrong

    def test_the_pot_odds_firing_rate_is_printed(self, report) -> None:
        assert says(report, "pot-odds") and says(report, "fired")

    def test_the_report_states_that_a_uniform_unseen_deck_flatters_hero(self, report) -> None:
        """Decision 5 ships its default reporting the frequency it fires rather than claiming it
        is correct, and the report says this makes the bot over-call as the mirror of its current
        over-folding."""
        assert says(report, "over-call") and says(report, "unseen deck")

    def test_the_report_says_which_fallback_codes_are_now_unreachable(self, report) -> None:
        assert says(report, "unreachable")

    def test_the_report_states_the_seam_the_phase_accepted(self, report) -> None:
        """The bot bets a flop and then refuses every turn. Decision 1 accepted that explicitly
        and a reader should not have to discover it from a refusal count."""
        assert says(report, "refuses every turn") or says(report, "refuses the turn")


class TestTheByteFigures:
    """Criterion: the report prints the bytes used, the headroom left and the per-spot cost, and
    no figure is a per-weight rate that includes non-weight bytes."""

    def test_the_bytes_used_and_the_headroom_are_printed(self, report) -> None:
        assert says(report, "bytes used") and says(report, "headroom")

    def test_the_per_spot_cost_is_printed(self, report) -> None:
        assert says(report, "per spot") or says(report, "per-spot")

    def test_the_budget_says_it_covers_the_index_and_the_sample_not_the_object_storage(
        self, report
    ) -> None:
        """What the repo commits is an index plus a sample, not the artifact the bot plays, and a
        later phase measuring "the committed chart" has to be able to tell which."""
        assert says(report, "index") and says(report, "sample")
        assert says(report, "object storage")

    def test_the_published_ranges_carry_their_pair_weights_on_both_sides(self, report) -> None:
        """The floor is class-level, and `EXPORT-RANGES-NEED-CONDITIONING-BEFORE-POSTFLOP` owns
        the `44` asymmetry the floor exposes rather than causes."""
        assert says(report, "pair weights")


class TestTheForbiddenFigures:
    """Forbidden shortcuts, asserted rather than trusted to a reviewer's memory."""

    def test_no_winrate_is_reported_over_this_artifact(self, report) -> None:
        """The hands it would come from are the ones that ended at the turn refusal, so the number
        does not exist."""
        assert not re.search(r"\bbb\s*/\s*100\b", report, re.IGNORECASE)
        assert not re.search(r"\bwin\s*rate\b", report, re.IGNORECASE)

    def test_no_ev_figure_is_reported_over_this_artifact(self, report) -> None:
        assert not re.search(r"\bEV\b\s*[:=]", report)

    def test_no_line_claims_a_green_gate_means_good_poker(self, report) -> None:
        assert not says(report, "gate proves the strategy")


# --------------------------------------------------------------------------- #
# The generator refuses rather than publishing a figure that does not hold
# --------------------------------------------------------------------------- #


class TestTheGeneratorRefusesAWrongFigure:
    """Criterion: the generator exits non-zero when one of the figures it names does not hold.

    Each validator is fed a wrong input directly rather than through a subprocess, so the red says
    which figure failed to reconcile. The subprocess positive control is above.
    """

    def test_a_byte_count_that_disagrees_with_the_bytes_on_disk_is_refused(
        self, generator, refusal
    ) -> None:
        check = owed(generator, "check_bytes_reconcile")

        with pytest.raises(refusal):
            check(declared=1, on_disk=2)

    def test_the_byte_check_passes_when_they_agree(self, generator) -> None:
        check = owed(generator, "check_bytes_reconcile")

        assert check(declared=2, on_disk=2) in (None, True)

    def test_a_per_spot_rate_that_charges_non_weight_bytes_is_refused(
        self, generator, refusal
    ) -> None:
        """The error the stage-1 numbers review held this phase over: a rate computed as
        whole-file bytes over weight count charges the per-spot blocks against every weight, which
        is how 26.789 became 40.227 and two published figures ran high."""
        check = owed(generator, "check_rate_excludes_non_weight_bytes")

        with pytest.raises(refusal):
            check(rate_bytes_per_weight=40.227, weight_bytes=0, weight_count=1)

    def test_a_coverage_share_that_does_not_sum_over_its_causes_is_refused(
        self, generator, refusal
    ) -> None:
        check = owed(generator, "check_coverage_splits_by_cause")

        with pytest.raises(refusal):
            check(answerable=0.5, losses={"multiway": 0.1, "no-cell": 0.1})

    def test_a_coverage_split_that_does_sum_is_accepted(self, generator) -> None:
        check = owed(generator, "check_coverage_splits_by_cause")

        assert check(answerable=0.8, losses={"multiway": 0.1, "no-cell": 0.1}) in (None, True)

    def test_a_refusal_count_that_does_not_match_the_codes_it_broke_out_is_refused(
        self, generator, refusal
    ) -> None:
        check = owed(generator, "check_refusal_counts_reconcile")

        with pytest.raises(refusal):
            check(total=10, by_code={"a": 3, "b": 3})

    def test_a_committed_spot_count_that_disagrees_with_the_index_is_refused(
        self, generator, refusal
    ) -> None:
        check = owed(generator, "check_spot_count_matches_index")

        with pytest.raises(refusal):
            check(printed=5, in_index=6)


# --------------------------------------------------------------------------- #
# The negative controls for this file's own three predicates
# --------------------------------------------------------------------------- #


class TestThisFileSOwnPredicatesCanFail:
    """A predicate that cannot return False is the defect one level down from a validator that
    cannot return False, and swapping one for the other would have fixed nothing.

    Every case here is a report string built in the test, so none of them waits on stage 6.
    These run and assert today, which is also what makes them the control on the three tests
    above still being red for the right reason rather than for a broken regex.
    """

    QUALIFIED = "  Kc7d2h @2.5  exploitability 0.42% of pot, a bound against the same bet menu"
    UNQUALIFIED = "  Kc7d2h @2.5  exploitability 0.42% of pot"

    def test_an_exploitability_line_with_no_menu_clause_is_rejected(self) -> None:
        assert every_exploitability_figure_names_the_menu(self.UNQUALIFIED + "\n") is False

    def test_an_exploitability_line_carrying_the_clause_is_accepted(self) -> None:
        assert every_exploitability_figure_names_the_menu(self.QUALIFIED + "\n") is True

    def test_one_qualified_line_does_not_carry_an_unqualified_one(self) -> None:
        """The failure a whole-document search makes invisible: a footnote that qualifies the
        figure once while a per-cell table prints it bare underneath."""
        both = f"{self.QUALIFIED}\n{self.UNQUALIFIED}\n"

        assert every_exploitability_figure_names_the_menu(both) is False

    def test_a_report_printing_no_figure_at_all_is_rejected_rather_than_passed(self) -> None:
        """Vacuously true is the other way a line-by-line rule goes quiet."""
        assert every_exploitability_figure_names_the_menu("nothing to see here\n") is False

    def test_a_rainbow_cost_row_with_no_scaled_label_is_rejected(self) -> None:
        assert every_cost_row_declares_measured_or_scaled("  rainbow   455   38.2 h\n") is False

    def test_a_rainbow_cost_row_claiming_measured_is_rejected(self) -> None:
        """The forbidden shortcut in one line: rainbow was never solved to target, so a rainbow
        figure reported as measured is a claim nothing took."""
        row = "  rainbow   455   38.2 h   measured\n"

        assert every_cost_row_declares_measured_or_scaled(row) is False

    def test_cost_rows_declaring_their_provenance_are_accepted(self) -> None:
        good = "  rainbow    455   38.2 h  scaled\n  monotone   286   6.1 h  measured\n"

        assert every_cost_row_declares_measured_or_scaled(good) is True

    def test_a_texture_row_declaring_neither_is_rejected(self) -> None:
        assert every_cost_row_declares_measured_or_scaled("  monotone  286  6.1 h\n") is False

    CODES = ("postflop:no-cell-for-this-spot", "postflop:in-the-index-but-not-fetched")

    def test_a_code_that_fired_zero_times_and_is_not_labelled_is_rejected(self) -> None:
        report = f"  {self.CODES[0]}   12\n  {self.CODES[1]}   0\n"

        assert vacuity_labels_match_the_counts(report, self.CODES) is False

    def test_a_code_that_fired_and_is_labelled_vacuous_is_rejected(self) -> None:
        """The other direction, which is how a report passes a naive search by labelling
        everything."""
        report = f"  {self.CODES[0]}   12   vacuous\n  {self.CODES[1]}   0    vacuous\n"

        assert vacuity_labels_match_the_counts(report, self.CODES) is False

    def test_labels_that_match_the_counts_are_accepted(self) -> None:
        report = f"  {self.CODES[0]}   12\n  {self.CODES[1]}   0    vacuous\n"

        assert vacuity_labels_match_the_counts(report, self.CODES) is True

    def test_a_code_left_out_of_the_breakdown_is_rejected(self) -> None:
        """The cheapest way to pass a vacuity check is to print no row for the code that fired
        zero times."""
        report = f"  {self.CODES[0]}   12\n"

        assert vacuity_labels_match_the_counts(report, self.CODES) is False

    def test_an_empty_code_vocabulary_is_rejected_rather_than_passed_vacuously(self) -> None:
        """The negative control on the predicate's own emptiness: without the guard it returns
        `True` for a report with no refusal breakdown in it at all."""
        assert vacuity_labels_match_the_counts(f"  {self.CODES[0]}   12\n", ()) is False
        assert vacuity_labels_match_the_counts("", ()) is False

    def test_a_digit_inside_a_code_name_is_not_read_as_its_count(self) -> None:
        """`row_count` takes the last whitespace-delimited integer, so a code carrying a number
        in its own name does not turn a vacuous row into a fired one."""
        codes = ("postflop:cell-over-1-percent-of-pot",)
        report = f"  {codes[0]}   0   vacuous\n"

        assert row_count(f"  {codes[0]}   0   vacuous") == 0
        assert vacuity_labels_match_the_counts(report, codes) is True
