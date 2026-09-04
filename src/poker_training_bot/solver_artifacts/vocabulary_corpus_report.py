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


def _direction(measured: int, recorded: int) -> str:
    """How a live count compares to a recorded one, as a phrase a sentence can take.

    Exists so that no sentence in this module can claim a direction the number beside it
    contradicts. Every place a report in this repo argued which way a figure had moved and
    got it backwards, the argument was a hardcoded word standing next to a computed count.
    """
    if measured < recorded:
        return "lower than"
    if measured > recorded:
        return "higher than"
    return "unchanged from"


def inventory_lines(result: ComparisonResult) -> list[str]:
    """The refusal inventory, and the total it adds up to.

    The total is the one figure here the chart cutover moves. The vocabulary widening added
    no coverage and the total held at 290; the cutover took it down, because the chart it
    commits answers more of the sample rather than less.

    The direction is computed from the count rather than asserted beside it. An earlier
    version of this prose argued the total had risen while the table under it printed a total
    that had fallen, which is worse than a stale figure: a reader trusts the sentence and
    distrusts the number. Nothing here states a live figure it does not derive, and the two
    retired-chart counts named below are historical constants read off the artifact
    `data/artifacts/preflop/six_max_nl25_100bb.json` carried at this branch's merge base.
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
        "cutover is what answered it - and it answered it by adding coverage rather than by",
        "trading some away. The retired raked chart held 36 spots: five first-in ranges, 15",
        "facing a single raise, 15 facing a three-bet, and the big blind facing a small-blind",
        "limp. The chart committed now holds the count this report's header prints, it keeps",
        "all five of those first-in ranges, and it goes much further into the spots facing a",
        f"three-bet. So the total above is {_direction(len(refused), 290)}",
        "the 290 the vocabulary phase measured, and that is the whole of the direction this",
        "section claims.",
        "",
        "What it still does not hold is a spot where hero is answering a four-bet. Every",
        "committed key has hero facing at most two raises - it prices hero's own four-bet as",
        "an action, which is a different thing - so the four-bet-or-deeper chains in the",
        "sample refuse, and they are one of the families making up the total above. An",
        "earlier version of this section said four-bet and five-bet continuations were",
        "committed heads-up. They are not, and they were not.",
        "",
        "One situation the retired chart answered is gone at every price, and it is the only",
        "one: the big blind facing a small-blind limp. This solve was run with limping",
        "switched off, so the small blind's first-in range never limps and the tree has no",
        "such node to price. That is a ruling's consequence rather than a gap, and the limped",
        "pots the sample does contain are refused for it.",
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


def _way(measured: int, recorded: int) -> str:
    """Which way a value moved: up, down or flat, for a column showing both values."""
    if measured < recorded:
        return "down"
    if measured > recorded:
        return "up"
    return "flat"


def _as_rate(value: str) -> tuple[int, int] | None:
    """`"439 of 456"` as a pair, or None for a row that is a bare count."""
    parts = value.split(" of ")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return None


def _movement_lines(result: ComparisonResult) -> list[str]:
    """Which way each agreement row moved since the branch point, derived not asserted.

    The rows carrying a rate get both movements, because they move independently and the
    report was wrong about both: the denominator is how much of the sample the chart scored
    at all, and the rate is how often it agreed with what was played. A chart that scores
    more and agrees less moves them in opposite directions, which is the case here and is
    the thing a single hardcoded sentence kept getting backwards.
    """
    refused = sum(1 for row in result.rows if row.refusal is not None)
    lines = [
        f"  {'row':<24}{'branch':>8}{'now':>8}{'':>6}{'branch':>9}{'now':>8}",
        f"  {'refusals':<24}{290:>8}{refused:>8}{_way(refused, 290):>6}",
    ]
    for entry in restated_numbers():
        branch = _as_rate(entry.branch)
        now = _as_rate(entry.measure(result))
        if branch is None or now is None:
            continue
        branch_num, branch_den = branch
        now_num, now_den = now
        branch_pct = 100.0 * branch_num / branch_den if branch_den else 0.0
        now_pct = 100.0 * now_num / now_den if now_den else 0.0
        # Cross-multiplied so the rate comparison is exact rather than a float tie-break.
        rate_way = _way(now_num * branch_den, branch_num * now_den)
        lines.append(
            f"  {entry.label:<24}{branch_den:>8}{now_den:>8}"
            f"{_way(now_den, branch_den):>6}{branch_pct:>8.1f}%{now_pct:>7.1f}%"
            f"{rate_way:>6}"
        )
    return lines


def restatement_lines(result: ComparisonResult) -> list[str]:
    """Every headline figure a completed phase published, re-measured with its cause.

    The row that matters most here is the one the cutover moves, and the version of this
    section written for the vocabulary phase published it as unchanged. Nothing was wrong
    with that then; both figures held. What made it a defect is that the table went on
    carrying 290 refusals through a chart replacement, in the report whose own inventory
    section counts them, so the two halves of the same document disagreed and the
    reassuring half was the one with a table around it.

    The table itself was then fixed and the paragraph under it was not, which is how the
    same defect came back with the signs reversed: a correct measured column arguing, in
    prose, that the figures had moved the other way. So the paragraph no longer contains a
    figure at all. It calls `_movement_lines`, which reads the same rows the table renders.
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
        "The chart cutover moved them, and not in the direction a replacement that gave up",
        "coverage would move them. The lines below are read off the same two columns the table",
        "above prints, so this paragraph cannot disagree with it. Each agreement row gets both",
        "of its movements, because they move independently: how many decisions the chart",
        "scored at all, and how often it agreed with what was actually played.",
        "",
    ]
    lines += _movement_lines(result)
    lines += [
        "",
        "Read the two together, because they point opposite ways. This is a wider chart that",
        "agrees with the corpus less often - not a narrower one that bought a higher rate by",
        "refusing the decisions it was going to get wrong. Which of those two a reader is",
        "looking at is the whole question, and a single sentence asserting a direction is how",
        "this report got it backwards twice.",
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
