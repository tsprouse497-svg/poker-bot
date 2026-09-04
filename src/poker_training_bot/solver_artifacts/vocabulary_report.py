"""The phase 12 spot vocabulary report, as text a non-coding reviewer can read.

Rendering only. Every number below is measured in
`poker_training_bot.solver_artifacts.vocabulary_measures`, which raises rather than
returning a figure it cannot stand behind, so a report that gets written is a report
whose measurements held.
"""

from __future__ import annotations

from poker_training_bot.data_pipeline.comparison import compare_committed_sample
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.schema import (
    PreflopAction,
    PreflopArtifact,
    render_size_bb,
    spot_key,
)
from poker_training_bot.solver_artifacts.vocabulary_corpus_report import (
    census_lines,
    inventory_lines,
    restatement_lines,
)
from poker_training_bot.solver_artifacts.vocabulary_measures import (
    DEPTH_BB,
    ENUMERATION_ENTRIES,
    TABLE_SIZE,
    VocabularyReportError,
    census,
    expressible_spots,
    strip_sizes,
)
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR
from poker_training_bot.strategy.preflop_sizing import DEFAULT_PATH as SIZING_PATH
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

# The sizing file as a reader would type it, derived from the path the table actually loads
# so the "open this file" instruction cannot name a file the report did not read. It named
# the retired chart's sizing table until the cutover deleted it.
SIZING_DISPLAY_PATH = SIZING_PATH.relative_to(ARTIFACT_DIR.parents[2])

# The spot the worked example below is shown at: the big blind closing the action against a
# button open at the price the tree solved. Named rather than derived, because the example is
# a claim about one committed cell and the guard under it has to be able to fail: it read
# `t6/d100/BTN/CO:raise@2.5` until the chart cutover retired that spot, and the guard is what
# turned a report describing a cell that is not there into a command that exits non-zero.
EXAMPLE_KEY = "t6/d100/BB/BTN:raise@2.5"


def _key_examples(artifact: PreflopArtifact) -> list[str]:
    raised = EXAMPLE_KEY
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
        "That is the big blind closing the action against a button open, at the one price",
        "the committed tree opens to. Before, one cell answered every price. A 2.25bb open",
        "and a 4bb open were the same spot, so every agreement rate this repo has published",
        "was computed across prices the chart could not tell apart.",
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


def _retired_section_lines() -> list[str]:
    """What this report used to check about the artifact, and why it cannot any more.

    Removed rather than loosened. The section it replaces mapped every committed key back to
    its size-stripped v1 form and made two assertions over that mapping: that it was a
    bijection, and that recomputing the weights checksum under the old keys reproduced the
    one the artifact carried before the re-keying. Both were true of a chart derived from the
    GTO Wizard source and neither can be true of the rake-free solve the cutover committed,
    so the honest move is to retire the section with its premise. Widening the two checks
    until they passed would have left a reader a section that reads like evidence and cannot
    fail, which is worse than no section.
    """
    return [
        "## The re-derivation section, and why it is gone",
        "",
        "This report used to close by proving the committed artifact had been re-keyed and",
        "not re-solved: strip every `@size` back out of the keys, recompute the weights",
        "checksum, and reproduce the checksum the file carried before the spot vocabulary",
        "phase. It also required the old-to-new mapping to be one-to-one, so no old cell",
        "could be silently merged.",
        "",
        "The chart cutover retired both, because it retired what they were about. The",
        "committed chart is now derived from a rake-free GTOpen solve rather than from the",
        "raked GTO Wizard ranges, so its weights are different numbers by intent and no",
        "checksum computed here can reproduce the old one. The mapping is no longer",
        "one-to-one either: the committed keys strip to fewer distinct v1 keys than there",
        "are keys, because the tree carries several prices where the coarse key carried one,",
        "and that collision is the vocabulary working rather than a merge.",
        "",
        "So the section is removed instead of relaxed. A check rewritten until it passes",
        "reads as evidence and proves nothing, and the re-keying it established is history",
        "that the phase's own audit packet already holds. The claim that no weight moved is",
        "not restated here for the new chart: nothing in this report measures it, and the",
        "chart cutover's own evidence is where that belongs.",
        "",
    ]


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


def _hand_check_lines(artifact: PreflopArtifact, sizing: PreflopSizingTable) -> list[str]:
    """One thing a reader can check in the sizing file with no code at all.

    The number it used to offer was the two opening prices - four `/rfi` entries reading 2.5
    and the small blind's reading 3.5 - and the chart cutover made every part of that false
    at once: one `/rfi` key survives, it reads 2.5, and a sizing entry is no longer a float.
    What replaces it is the shape change decision 6 was re-cut for, which is the property of
    this file a reader is most likely to get wrong from the outside: the prices are per hand
    class, so one spot holds one list per class rather than one number.

    Every figure below is read out of the loaded table, so checking the report against the
    file is comparing the file with itself through one indirection rather than against a
    sentence somebody typed.

    The two-price half of that shape has no instance over the committed set, so the section
    publishes it labelled vacuous rather than refusing to render - a criterion that cannot
    fire did not pass, and a report that will not print is not a way of saying so. The label
    is earned by a premise asked of the whole table below, never of this spot alone.
    """
    named = sorted(sizing.raise_to_bb)
    priced = sorted(spot for spot, classes in sizing.raise_to_bb.items() if classes)
    prices = sorted(
        {
            float(entry["to_bb"])
            for classes in sizing.raise_to_bb.values()
            for entries in classes.values()
            for entry in entries
        }
    )
    if len(named) != artifact.audit_fields.spot_count:
        raise VocabularyReportError(
            f"the sizing table names {len(named)} spots and the artifact declares"
            f" {artifact.audit_fields.spot_count}; the section below says they are the same set"
        )
    classes = sizing.raise_to_bb.get(EXAMPLE_KEY)
    if not classes:
        raise VocabularyReportError(
            f"the sizing table prices nothing at {EXAMPLE_KEY}, so this section cannot show"
            " a class that raises to one price beside a class that raises to two"
        )
    one_price = sorted(name for name, entries in classes.items() if len(entries) == 1)
    two_prices = sorted(name for name, entries in classes.items() if len(entries) > 1)
    if not one_price:
        raise VocabularyReportError(
            f"{EXAMPLE_KEY} prices no class at a single price, so this section has no entry"
            " a reader can open the file and check"
        )
    # The premise, before the label below. "This spot happens to offer nobody two prices" is
    # not the same claim as "the two-price schema has no instance", and labelling on the first
    # would let a build that broke only this spot print `vacuous` instead of failing. So the
    # question is asked of the whole table, and a live criterion this spot cannot show is a
    # report that refuses rather than one that labels.
    offered_two = [
        (spot, name)
        for spot, spot_classes in sizing.raise_to_bb.items()
        for name, entries in spot_classes.items()
        if len(entries) > 1
    ]
    if not two_prices and offered_two:
        raise VocabularyReportError(
            f"{EXAMPLE_KEY} prices no class at more than one price, but {len(offered_two)}"
            f" (spot, class) pairs elsewhere do, the first being {offered_two[0]}; the worked"
            " example has to move to a spot that can show the schema rather than label it"
        )
    single = "AA" if "AA" in one_price else one_price[0]
    mixed = ("44" if "44" in two_prices else two_prices[0]) if two_prices else None
    absent = sorted(name for name in HAND_CLASSES if name not in classes)

    def rendered(hand_class_text: str) -> str:
        return "   ".join(
            f"{render_size_bb(price)} at {weight:.4f}"
            for price, weight in sizing.sizes_bb(EXAMPLE_KEY, hand_class_text) or ()
        )

    return [
        "## Check one number by hand",
        "",
        "**The number: a raise price belongs to a hand class, not to a spot.**",
        "",
        f"Open `{SIZING_DISPLAY_PATH}` and find `raise_to_bb` ->",
        f"`{EXAMPLE_KEY}`, the spot the worked example at the top of this report uses. Two",
        "of its 169 hand-class slots, an entry being a list of prices with hero's weight:",
        "",
        *_two_price_lines(single, mixed, rendered),
        *_one_price_lines(single, absent, len(classes), rendered),
        f"The same file names every one of the {artifact.audit_fields.spot_count} committed spots,",
        f"prices a hand class at {len(priced)} of them, and holds {len(prices)} distinct raise-to",
        f"sizes in all. The other {len(named) - len(priced)} name the spot with nothing under it:",
        "hero's menu there does offer him a raise, but he reaches every one of those spots by",
        "calling a raise and then facing a re-raise, and no hand he still holds by then takes",
        "it. Nothing under a spot is not a price of zero either:",
        "",
        f"    {', '.join(render_size_bb(size) for size in prices)}",
        "",
    ]


def _two_price_lines(single: str, mixed: str | None, rendered) -> list[str]:
    """The section as written, for a table that offers some class two prices."""
    if mixed is None:
        return []
    return [
        f"    {single:<5}{rendered(single)}",
        f"    {mixed:<5}{rendered(mixed)}",
        "",
        "No code required, and it settles the thing a single number per spot cannot say. One",
        "of those classes is offered one price and the other is offered two, so a table",
        "holding one float per spot would have to give both the same answer: it would either",
        "price the class that never takes the second price as though it sometimes did, or",
        "drop the second price from the class that mostly takes it. Which of two offered",
        "prices the bot picks is drawn from these weights with the same seed that draws",
        "between a cell's actions, so the amount it raises to is always one the solve chose.",
        "",
    ]


def _one_price_lines(single: str, absent: list[str], priced_classes: int, rendered) -> list[str]:
    """The section when no class anywhere is offered two prices, which is the case today.

    This is the first of the contract's three vacuous criteria, and it is published with its
    label rather than refused: a criterion with no instance did not pass, and it is kept
    because the multiway family returns with two-price menus. The premise that makes it
    vacuous is asserted by the caller before this runs, so a solve that reactivates the
    schema turns that check red rather than leaving this label standing over a real case.
    """
    if not absent:
        return []
    return [
        f"    {single:<5}{rendered(single)}",
        f"    {absent[0]:<5}(no entry)",
        "",
        "No code required, and it still settles what a single number per spot cannot say. The",
        f"entry is a list under a hand class: {priced_classes} of the 169 classes have one here,",
        "the rest have none at all, and a file holding one float per spot could not tell you",
        "which was which. Nothing under a class is not a price of zero.",
        "",
        "**vacuous  the two-price sizing schema.** The list under a class is a list because a",
        "class can be offered two prices, and over the committed set none is: `add_allin:",
        "false` takes hero's shove off every node that also names a raise, and the four-bet",
        "family that still shoves is withheld. So no worked example can show a second price,",
        "and this section says so rather than counting the schema as a check that passed. It",
        "is kept because the multiway family returns with two-price menus, and it is proved",
        "against a synthetic export instead of against the committed one.",
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
        "The spot vocabulary phase committed no new solve and no new chart. It widened what",
        "a spot key can say, re-derived the committed artifact under the new keys carrying",
        "the same ranges, and re-ran the measurements Phase 11 deliberately left open.",
        "",
        "This report is regenerated against whatever chart is committed, and the chart has",
        "since been replaced: the ranges above are a rake-free GTOpen solve rather than the",
        "raked GTO Wizard ranges the phase measured. Every figure below is measured on this",
        "run, so the corpus numbers are the new chart's and the section on re-derivation is",
        "retired rather than restated. Where a number moved, the restatement table names",
        "which of the two phases moved it.",
        "",
    ]
    sections = [
        _key_examples(artifact),
        _retired_section_lines(),
        _counts_lines(),
        inventory_lines(result),
        census_lines(measured),
        restatement_lines(result),
        _hand_check_lines(artifact, sizing),
    ]
    body: list[str] = []
    for section in sections:
        body.extend(section)
    footer = ["Generated by `scripts/generate_spot_vocabulary_report.py`.", ""]
    return "\n".join(header + body + footer)
