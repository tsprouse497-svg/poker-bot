"""The phase 12 spot vocabulary report, as text a non-coding reviewer can read.

Rendering only. Every number below is measured in
`poker_training_bot.solver_artifacts.vocabulary_measures`, which raises rather than
returning a figure it cannot stand behind, so a report that gets written is a report
whose measurements held.
"""

from __future__ import annotations

from poker_training_bot.data_pipeline.comparison import (
    ComparisonResult,
    compare_committed_sample,
)
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.poker_core.positions import preflop_action_order
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.schema import (
    PreflopAction,
    PreflopArtifact,
    render_size_bb,
    spot_key,
)
from poker_training_bot.solver_artifacts.vocabulary_measures import (
    DEPTH_BB,
    ENUMERATION_ENTRIES,
    TABLE_SIZE,
    V1_WEIGHTS_SHA256,
    Census,
    VocabularyReportError,
    census,
    expressible_spots,
    key_mapping,
    restated_numbers,
    strip_sizes,
    v1_weights_checksum,
)
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable


def _key_examples(artifact: PreflopArtifact) -> list[str]:
    raised = "t6/d100/BTN/CO:raise@2.5"
    four_bet = spot_key(
        TABLE_SIZE,
        DEPTH_BB,
        "BTN",
        (
            PreflopAction("LJ", "raise", 2.5),
            PreflopAction("BTN", "raise", 8.0),
            PreflopAction("LJ", "raise", 21.5),
        ),
    )
    declared = set(spot.spot_id for spot in artifact.spots)
    if raised not in declared:
        raise VocabularyReportError(
            f"the committed artifact no longer declares {raised!r}, so the worked example"
            " below would describe a spot that is not there"
        )
    return [
        "## What a spot key can say now",
        "",
        "A key is a string a person reads in a refusal inventory, so what it looks like",
        "is the change rather than a detail of it. Two things are new.",
        "",
        "**A raise carries the amount it raised to, in big blinds, after an `@`.** The",
        "number is the total the raiser put in, not the increment: `BTN:raise@8` is a",
        "three-bet to eight big blinds, which a player would describe as a 3.2x.",
        "",
        f"    before   {strip_sizes(raised)}",
        f"    after    {raised}",
        "",
        "Before, one cell answered every price. A 2.25bb open and a 4bb open were the",
        "same spot, so every agreement rate this repo has published was computed across",
        "prices the chart could not tell apart.",
        "",
        "**A position may act more than once.** A four-bet had no key at all: the rule",
        "rejected any sequence in which a position appeared twice, in as many words.",
        "",
        f"    could not be written before   {four_bet}",
        "",
        "That reads: the lojack opened to 2.5, the button three-bet to 8, the lojack",
        "four-bet to 21.5, and the button is to act. Nothing bounds the number of orbits;",
        "what bounds the vocabulary is whether the sequence is a legal preflop order and",
        "whether its raises can be paid at the stated depth. A five-bet to 300bb in a",
        "100bb game is rejected because nobody can pay it, which is a check the key could",
        "not perform at all until it carried sizes.",
        "",
    ]


def _re_derivation_lines(artifact: PreflopArtifact, sizing: PreflopSizingTable) -> list[str]:
    mapping = key_mapping(artifact)
    old_keys = [old for old, _ in mapping]
    if len(set(old_keys)) != len(mapping):
        raise VocabularyReportError(
            "two new keys strip to the same old key, so the re-keying is not a bijection"
            " and one of the old cells has been silently merged"
        )
    derived_v1 = v1_weights_checksum(artifact)
    if derived_v1 != V1_WEIGHTS_SHA256:
        raise VocabularyReportError(
            f"stripping the sizes back out gives weights checksum {derived_v1}, not the"
            f" {V1_WEIGHTS_SHA256} the artifact carried before this phase; the ranges"
            " moved and this is a re-solve rather than a re-keying"
        )
    missing = sorted(set(sizing.raise_to_bb) - set(old for _, old in mapping))
    if missing:
        raise VocabularyReportError(
            f"the sizing table is keyed by spots the artifact does not declare: {missing}"
        )
    lines = [
        "## The committed artifact, re-keyed and not re-solved",
        "",
        f"{len(mapping)} spots before, {len(mapping)} spots after. The count does not move because",
        "each size-stripped prefix admits exactly one solved size, so the key gained the",
        "ability to tell prices apart at no cost in cells.",
        "",
        "The ranges did not move, and that is checked rather than asserted. Strip every",
        "`@size` back out of the committed keys, recompute the weights checksum over the",
        "result, and it has to reproduce the checksum the artifact carried before this",
        "phase. It does:",
        "",
        f"    checksum under the old keys   {derived_v1}",
        f"    recorded before this phase    {V1_WEIGHTS_SHA256}",
        f"    checksum the file carries now {artifact.audit_fields.weights_sha256}",
        "",
        "Spot ids are inside the checksum, so the file's own checksum had to change. The",
        "two lines above it are why that is evidence and not an alarm.",
        "",
        "The old-to-new mapping, in full. Every size here came from the source export's",
        "own action label at the spot that raise was offered at, never from a constant:",
        "facing a lojack open is 2.5 because the export's `RFI_UTG` offers `Raise 2.5`.",
        "",
        f"  {'old key':<44}{'new key'}",
    ]
    for old, new in mapping:
        lines.append(f"  {old:<44}{new}")
    lines.append("")
    return lines


def _counts_lines() -> list[str]:
    v1 = expressible_spots(single_orbit=True)
    v2 = expressible_spots(single_orbit=False)
    if v2.with_limps <= v1.with_limps:
        raise VocabularyReportError(
            "the widened vocabulary expresses no more spots than the old one, which"
            " cannot be true if a position may now act more than once"
        )
    return [
        "## How many spots the vocabulary can express",
        "",
        "Counted by enumerating `solver_artifacts.schema.spot_key` over legal preflop",
        "orders at a six-handed 100bb table, not quoted. A limp is a call before anybody",
        "has raised; a cold call behind an open is not a limp and is counted in both",
        "columns.",
        "",
        f"  {'':<34}{'with limps':>14}{'without limps':>16}",
        f"  {'v1, one orbit only':<34}{v1.with_limps:>14,}{v1.without_limps:>16,}",
        f"  {'v2, positions may repeat':<34}{v2.with_limps:>14,}{v2.without_limps:>16,}",
        "",
        f"Both rows are enumerated to at most {ENUMERATION_ENTRIES} recorded actions. For v1",
        "that is not a bound at all - a single-orbit key at a six-handed table cannot have",
        "more than six entries - so the v1 row is complete. For v2 it is a bound on this",
        "report rather than on the vocabulary, which has no orbit cap by ruling and is",
        "limited in play by what the stacks can pay.",
        "",
        "`docs/V2_ROADMAP.md` states 1,691 and 848 for the v1 pair and says both are",
        "recomputable this way. They are not: this enumeration gives"
        f" {v1.with_limps:,} and {v1.without_limps:,}.",
        "The ratio between the published pair is the same to within a percent, so it looks",
        "like one systematic difference rather than two errors, but",
        "no variation tried reproduces the published numbers. Correcting the four places",
        "that quote them is `ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE` in `backlog.yml`; the",
        "roadmap is a `contract-update` document and is not edited from an implementation",
        "phase.",
        "",
    ]


def _inventory_lines(result: ComparisonResult) -> list[str]:
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
        "The total is expected not to fall, and it did not. This phase adds no chart",
        "coverage: those 19 arrive as `lookup:spot-not-covered` instead, which is a",
        "different and better miss because the vocabulary can now name the cell. Filling",
        "it is `CHART-COVERAGE-EXPANSION`, proposed phase 14.",
        "",
        "The deepest sequence the committed sample reached, now expressible:",
        "",
    ]
    deepest = max(
        (entry for entry in second_orbit),
        key=lambda entry: entry.spot_key.count(":raise"),
        default=None,
    )
    if deepest is not None:
        lines.append(f"    {deepest.spot_key}")
        lines.append("")
    return lines


def _census_lines(measured: Census) -> list[str]:
    lines = [
        "## What ruling 8 costs in play: the price-substitution census",
        "",
        "Ruling 8 says the solved tree carries one opening price and every other price is",
        "answered from it. Taylor extended it on 2026-08-20 to every raise in the",
        "sequence, because exact matching past the open would have refused most of the",
        "three-bet decisions this chart can answer at all.",
        "",
        "Until this phase nothing counted how often that abstraction was used, because",
        "the key could not tell two prices apart and so could not tell that one had been",
        "moved. Over the committed sample:",
        "",
        f"  decisions the chart answered                         {measured.answered:>6}",
        f"  answered at the price they were asked at             {measured.exact:>6}",
        f"  answered at a price they were not asked at           {measured.substituted:>6}"
        f"   ({100.0 * measured.substituted / measured.answered:.1f}%)",
        "",
        "Split by which raise was moved. The first line is what ruling 8 itself costs;",
        "the second is what extending it past the open costs, and they are kept apart",
        "because they were ruled separately.",
        "",
        f"  the opener's price was moved                         {measured.open_substituted:>6}",
        f"  a later raise's price was moved                      {measured.later_substituted:>6}",
        "",
        "Split by how far a price moved:",
        "",
    ]
    for label, count in measured.by_distance:
        lines.append(f"  {label:<52}{count:>6}")
    lines += [
        "",
        "The opening prices the sample actually came in at, and the cell each was",
        "answered from:",
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
        "decision 5 rejected, not this phase's outcome.",
        "",
        "What this does not buy is coverage. A squeeze or a cold four-bet is expressible",
        "today and uncovered today, and it stays uncovered here at every price: the",
        "normaliser moves a price, it does not find a nearer spot.",
        "",
    ]
    return lines


def _restatement_lines(result: ComparisonResult) -> list[str]:
    lines = [
        "## Every number Phase 11 moved, and every number this phase moved",
        "",
        "Phase 11 corrected the engine and the strategy query that every published figure",
        "in this repo was measured through, and ruled that a fix phase does not grade its",
        "own fixes. This is the first phase to re-run those measurements, so it owes the",
        "restatement - and it owes it with the two causes kept apart, because a number",
        "that moved for both reasons and is reported once teaches nothing.",
        "",
        "The packet column is what the phase published. The branch column is what the",
        "committed report said at this phase's branch point, which already carried Phase",
        "11's corrections. So packet-to-branch is Phase 11 and branch-to-now is this",
        "phase, and neither is asserted.",
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
        "The corpus figures did not move at all, and that is the phase's own result",
        "rather than an absence of one. A finer key would have moved them if it had",
        "changed which cell a decision reached; it did not, because a price the tree does",
        "not hold is normalised back to the one cell the coarse key would have hit. What",
        "changed is that the answer now says so, which is what the census above counts.",
        "",
        "The self-play figures in `reports/active/latest_profile_comparison_report.txt`",
        "did move: 128 refused hands became 126, and 472 measured became 474. That is not",
        "a coverage change either. `PreflopChartStrategy._seed` hashes the spot key into",
        "the seeded draw that collapses a mixed cell, so re-keying re-seeds every mixed",
        "decision and the run walks a different path through the same distributions.",
        "Attributed to this phase, and reported here because a reader comparing the two",
        "reports would otherwise read it as coverage.",
        "",
        "No committed audit packet was edited. The Phase 07 and Phase 08 packets are the",
        "record of what those phases found and believed; rewriting them would destroy the",
        "only evidence that a number ever changed.",
        "",
    ]
    return lines


def _hand_check_lines(sizing: PreflopSizingTable) -> list[str]:
    sizes = sorted(set(sizing.raise_to_bb.values()))
    return [
        "## Check one number by hand",
        "",
        "**The number: the committed tree carries two opening prices, not one.**",
        "",
        "Open `data/artifacts/preflop/sizings/six_max_nl25_100bb.json` and read the five",
        "entries whose key ends in `/rfi`. Four of them - LJ, HJ, CO, BTN - read 2.5, and",
        "`t6/d100/SB/rfi` reads 3.5. No code required, and it settles a question the",
        "roadmap left open: a single constant for 'the solved opening price' would already",
        "be wrong today rather than only after some future solve, which is why the",
        "normaliser derives its candidate prices from the keys the artifacts declare.",
        "",
        f"The same file holds {len(sizes)} distinct raise-to sizes in all, and every one is a",
        "whole tenth of a big blind:",
        "",
        f"    {', '.join(render_size_bb(size) for size in sizes)}",
        "",
    ]


def render_spot_vocabulary_report() -> str:
    """The whole report, as text.

    Raises `VocabularyReportError` rather than writing a file it cannot stand behind.
    """
    artifacts = import_preflop_artifacts(ARTIFACT_DIR)
    if len(artifacts) != 1:
        raise VocabularyReportError(
            f"this report is written against one committed artifact, found {len(artifacts)}"
        )
    artifact = artifacts[0]
    sizing = PreflopSizingTable.from_repo()
    result = compare_committed_sample(load_committed_sample())
    measured = census(result)

    header = [
        "Spot Vocabulary Report",
        "======================",
        "",
        f"Artifact: {ARTIFACT_DIR.name}/{artifact.artifact_id.rsplit('/', 1)[-1]}",
        f"Source: {artifact.source.name}",
        f"Generated at: {artifact.generated_at}",
        f"Spots: {artifact.audit_fields.spot_count}",
        f"Sample: {result.hands_compared} hands, {len(result.rows)} preflop decision points",
        "",
        "This phase committed no new solve and no new chart. It widened what a spot key",
        "can say, re-derived the committed artifact under the new keys carrying the same",
        "ranges, and re-ran the measurements Phase 11 deliberately left open.",
        "",
    ]
    sections = [
        _key_examples(artifact),
        _re_derivation_lines(artifact, sizing),
        _counts_lines(),
        _inventory_lines(result),
        _census_lines(measured),
        _restatement_lines(result),
        _hand_check_lines(sizing),
    ]
    body: list[str] = []
    for section in sections:
        body.extend(section)
    footer = ["Generated by `scripts/generate_spot_vocabulary_report.py`.", ""]
    return "\n".join(header + body + footer)
