"""The corpus half of the spot vocabulary report: what the widened key changed in play.

Split from `vocabulary_report` at the 500-line cap, on the seam the report itself reads
along. That module renders what a spot key can say - the worked example, the enumeration of
expressible spots, the sizing file a reader can check by hand - all of which are properties
of the vocabulary and of the committed files. This one renders what happened when the key
was pointed at 499 real hands: the refusal inventory, the price-substitution census, and the
restatement of every headline figure a completed phase published.

Rendering only, like its sibling. Every figure is measured in `vocabulary_measures`, which
raises rather than returning a number it cannot stand behind.
"""

from __future__ import annotations

from poker_training_bot.data_pipeline.comparison import ComparisonResult
from poker_training_bot.poker_core.positions import preflop_action_order
from poker_training_bot.solver_artifacts.schema import render_size_bb
from poker_training_bot.solver_artifacts.vocabulary_measures import (
    TABLE_SIZE,
    Census,
    restated_numbers,
)


def inventory_lines(result: ComparisonResult) -> list[str]:
    """The refusal inventory, and the total it adds up to.

    The total is the one figure here the chart cutover moves, and it moves the opposite way
    from the phase this section was written for. The vocabulary widening added no coverage
    and the total held at 290; the cutover gives fifteen retired spots up, four of them
    opening ranges, so it rises. It is stated as measured with that cause named rather than
    carried over, because a refusal total that reads unchanged next to a chart replacement is
    the one number a reader would take as proof nothing was lost.
    """
    catch_all = [
        entry for entry in result.refusal_inventory if entry.spot_key == "(no expressible spot)"
    ]
    second_orbit = [
        entry
        for entry in result.refusal_inventory
        if any(
            entry.spot_key.count(f"{position}:") > 1
            for position in preflop_action_order(TABLE_SIZE)
        )
    ]
    refused = [row for row in result.rows if row.refusal is not None]
    unrepresentable = [
        row
        for row in refused
        if row.miss_code is not None and row.miss_code.endswith("unrepresentable-spot")
    ]
    lines = [
        "## The real-hand refusal inventory loses its catch-all row",
        "",
        "The largest single row of the real-hand inventory used to be 19 decision points",
        "filed under `(no expressible spot)`, and it was the one row nobody could act on:",
        "a refusal that names no spot names no cell anybody could fill. All 19 were a",
        "position acting twice.",
        "",
        f"  rows still reading '(no expressible spot)'          {len(catch_all)}",
        f"  decisions refusing as lookup:unrepresentable-spot   {len(unrepresentable)}",
        f"  decision points now naming a repeated-position key  "
        f"{sum(entry.count for entry in second_orbit)}",
        f"  total refusals over the committed sample            {len(refused)}",
        "",
        "The catch-all emptied because the vocabulary can now name those cells, not because",
        "anything filled them: the 19 arrive as `lookup:spot-not-covered` instead, which is",
        "a different and better miss. That was `CHART-COVERAGE-EXPANSION`, and the chart",
        "cutover is what answered it - in both directions. Four-bet and five-bet",
        "continuations are committed heads-up, so part of this family is now answered; and",
        "the ruled selection predicate gives up fifteen spots the retired chart held,",
        "including four of the five opening ranges, so the total above is higher than the",
        "290 the vocabulary phase measured rather than lower. A chart that answers a",
        "narrower set of questions correctly refuses more of them, and that trade is the",
        "cutover's own subject rather than this section's.",
        "",
        "The deepest sequence the committed sample reached, now expressible:",
        "",
    ]
    deepest = max(
        (entry for entry in second_orbit),
        key=lambda entry: entry.spot_key.count(":raise"),
        default=None,
    )
    if deepest is None:
        lines.append("    none: no refusal left in the inventory has a seat acting twice")
    else:
        lines.append(f"    {deepest.spot_key}")
    lines.append("")
    return lines


def census_lines(measured: Census) -> list[str]:
    lines = [
        "## What ruling 8 costs in play: the price-substitution census",
        "",
        "Ruling 8 says the solved tree carries one opening price and every other price is",
        "answered from it. Taylor extended it on 2026-08-20 to every raise in the",
        "sequence, because exact matching past the open would have refused most of the",
        "three-bet decisions this chart can answer at all.",
        "",
        "Until the key carried sizes nothing counted how often that abstraction was used,",
        "because a coarse key could not tell two prices apart and so could not tell that one",
        "had been moved. Over the committed sample:",
        "",
        f"  decisions the chart answered                         {measured.answered:>6}",
        f"  answered at the price they were asked at             {measured.exact:>6}",
        f"  answered at a price they were not asked at           {measured.substituted:>6}"
        f"   ({100.0 * measured.substituted / measured.answered:.1f}%)",
        "",
        "Two different things get counted below and adding the wrong column gives a",
        "number this heading contradicts, so each table says which it counts. One",
        "decision can face several raises and have more than one of them moved: there",
        f"are {measured.substituted:,} substituted decisions carrying"
        f" {measured.substitutions:,} substituted raises between them.",
        "",
        "Split by which raise was moved, counting DECISIONS. The first line is what",
        "ruling 8 itself costs; the second is what extending it past the open costs, and",
        "they are kept apart because they were ruled separately. The third is why the",
        "first two sum to more than the total above.",
        "",
        f"  the opener's price was moved                         {measured.open_substituted:>6}",
        f"  a later raise's price was moved                      {measured.later_substituted:>6}",
        f"  both, counted once in each line above                {measured.both_substituted:>6}",
        "",
        "Split by how far a price moved, counting SUBSTITUTED RAISES:",
        "",
    ]
    for label, count in measured.by_distance:
        lines.append(f"  {label:<52}{count:>6}")
    lines += [
        f"  {'all substituted raises':<52}{measured.substitutions:>6}",
        "",
        "And by direction, which the distance split above cannot show and which is the",
        "half with poker content. A smaller open gives the defender a better price, so",
        "the correct response to it is a wider continue than the correct response to a",
        "larger one. Where the answered price is the higher, the chart hands back the",
        "tighter range:",
        "",
        f"  {'answered above the price asked':<52}{measured.moved_up:>6}",
        f"  {'answered below the price asked':<52}{measured.moved_down:>6}",
        "",
        "The opening prices the sample actually came in at, and the cell each was",
        "answered from, counting DECISIONS.",
        "",
        "The answered column is aggregated across openers, so one asked price can appear",
        "against more than one answered cell wherever the tree prices the same open",
        "differently by seat. It does not here: the committed solve opens to a single price",
        "at every seat that opens at all, so an asked price maps to one answered cell and a",
        "row where the two agree is an open that needed no substitution. The chart this",
        "replaced opened the small blind to 3.5 and everyone else to 2.5, and a row there",
        "reading '2.5 -> 3.5' was a small-blind open answered from the small-blind cell",
        "rather than a solved price that moved.",
        "",
        f"  {'asked':>8}{'answered':>10}{'decisions':>12}",
    ]
    for asked, given, count in measured.by_asked_open:
        lines.append(
            f"  {render_size_bb(asked):>8}{render_size_bb(given):>10}{count:>12}"
        )
    lines += [
        "",
        "And the figure the three-bet extension was ruled on, re-measured here rather",
        "than quoted from the decision record:",
        "",
        f"  decisions facing a three-bet at a spot the chart holds   "
        f"{measured.three_bet_spots_covered:>4}",
        f"  of those, facing a price the tree does not hold          "
        f"{measured.three_bet_spots_substituted:>4}",
        f"  of those, facing a price it does                         "
        f"{measured.three_bet_spots_exact:>4}",
        "",
        f"So exact matching past the open would have refused"
        f" {measured.three_bet_spots_substituted} of the {measured.three_bet_spots_covered}",
        "three-bet decisions this chart can answer at all. That is the alternative",
        "decision 5 rejected, not an outcome of the ruling.",
        "",
        "What this does not buy is coverage. A squeeze is expressible today and uncovered",
        "today, and it stays uncovered at every price: the normaliser moves a price, it does",
        "not find a nearer spot. The chart cutover made that a ruling rather than a gap - a",
        "squeeze has two opponents already invested, which is the clause the selection",
        "predicate refuses on, so those spots are outside the chart by intent and not",
        "pending some later phase.",
        "",
    ]
    return lines


def restatement_lines(result: ComparisonResult) -> list[str]:
    """Every headline figure a completed phase published, re-measured with its cause.

    The row that matters most here is the one the cutover moves, and the version of this
    section written for the vocabulary phase published it as unchanged. Nothing was wrong
    with that then; both figures held. What made it a defect is that the table went on
    carrying 290 refusals through a chart replacement, in the report whose own inventory
    section counts them, so the two halves of the same document disagreed and the
    reassuring half was the one with a table around it.
    """
    lines = [
        "## Every number Phase 11 moved, and every number the two phases after it moved",
        "",
        "Phase 11 corrected the engine and the strategy query that every published figure",
        "in this repo was measured through, and ruled that a fix phase does not grade its",
        "own fixes. The spot vocabulary phase was the first to re-run those measurements, so",
        "it owed the restatement - and it owed it with the causes kept apart, because a",
        "number that moved for two reasons and is reported once teaches nothing.",
        "",
        "The packet column is what the phase published. The branch column is what the",
        "committed report said at the vocabulary phase's branch point, which already carried",
        "Phase 11's corrections. So packet-to-branch is Phase 11, branch-to-now is what has",
        "happened since, and the cause column names which. Nothing here is asserted: the",
        "`now` column is measured on this run.",
        "",
        f"  {'number':<44}{'packet':>13}{'branch':>13}{'now':>13}  cause",
    ]
    for entry in restated_numbers():
        now = entry.measure(result)
        lines.append(
            f"  {entry.label:<44}{entry.packet:>13}{entry.branch:>13}{now:>13}"
            f"  {entry.cause(now)}"
        )
    lines += [
        "",
        "The widened key moved none of the corpus figures, and that was the vocabulary",
        "phase's own result rather than an absence of one. A finer key would have moved them",
        "if it had changed which cell a decision reached; it did not, because a price the",
        "tree does not hold is normalised back to the one cell the coarse key would have hit.",
        "What changed is that the answer now says so, which is what the census above counts.",
        "",
        "The chart cutover moved them, and it moved them in the direction a replacement is",
        "least likely to be read as moving them. The refusal total rises and every agreement",
        "denominator falls, because the ruled selection predicate keeps only the spots the",
        "source prices every terminal below: four of the five opening ranges and ten of the",
        "eleven spots facing a single open are given up, so decisions the retired chart",
        "answered are now refused and sit outside every rate. A higher agreement rate over a",
        "smaller denominator is not an improvement, and the two columns have to be read",
        "together for that reason.",
        "",
        "The self-play figures in `reports/active/latest_profile_comparison_report.txt` also",
        "moved at the vocabulary phase: 128 refused hands became 126, and 472 measured became",
        "474. That was not a coverage change. `PreflopChartStrategy._seed` hashes the spot key",
        "into the seeded draw that collapses a mixed cell, so re-keying re-seeds every mixed",
        "decision and the run walks a different path through the same distributions. Recorded",
        "here because a reader comparing the two reports would otherwise read it as coverage;",
        "what the cutover does to those figures is the cutover's own report to state.",
        "",
        "No committed audit packet was edited. The Phase 07 and Phase 08 packets are the",
        "record of what those phases found and believed; rewriting them would destroy the",
        "only evidence that a number ever changed.",
        "",
    ]
    return lines
