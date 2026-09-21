"""Phase 14: the report a non-coding reviewer reads, over the committed 156.

The family owns the **rendered** report: every heading the contract's evidence sentence names is
there, the body under each makes the claim it promises, and each printed figure is re-derived from
the committed artifact, the export or the report's own columns. Four files, split at the 700-line
cap, and **this one holds the module-scope interface the other three reach as an attribute** - the
ruled numbers, the row patterns, the section reader, the loaders behind the fixtures and the walks
over the committed keys. A count has one owner and is never copied.

- this file: how the 156 were selected and what each committed row carries - the census, the
  histogram and the prices, exposure per spot, one cell traced from export node to artifact row,
  and the arrival grain.
- `test_derived_chart_report_ranges.py`: the four relations, the ladders, both counterfactual
  arms, the equity relation, the accepted defects, the orderings, the big blind, the bands and the
  menus.
- `test_derived_chart_report_cutover.py`: the ledger, the refusal inventory, the corpus
  republication and the one recomputable number.
- `test_derived_chart_report_validators.py`: the generator's refusals, the three vacuous labels,
  hero's jam at the withheld spots and the source card's limitations.

**Re-cut at stage 4 on 2026-09-02, and again for MAINT-34.** Each earlier cut described a new set -
86 spots, then 143 nodes, then six - under three `derivation:*-four-bet-*` refusal codes that no
longer exist. All superseded by decisions 46, 48, 49 and 53.

Sibling lanes own the rules and no file here re-implements one: `test_chart_derivation.py` the
selection and the census, `test_chart_conversion.py` and `test_derived_chart.py` the artifact's
shape, `test_chart_arrival_probability.py` reach and arrival, `test_chart_cutover_evidence.py` the
relations and the arms. What is checked here is that the report **prints** those figures and that
the printed ones hold against the files a reader can open.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter

import pytest
import test_chart_derivation as derivation_tests

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from scripts.repo_paths import REPO_ROOT

COMMAND_ID = "generate_derived_chart_report"
ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
SOURCE_CARD = ARTIFACT_DIR / "exports" / "gtopen_six_max_100bb_rakefree.source.json"
RETIRED_SIZINGS = "data/artifacts/preflop/sizings/six_max_100bb_rakefree.json"
"""The sizing table of the **86-spot chart this phase retires**, read out of git at the pin the
ledger names. Not `sizings/six_max_nl25_100bb.json`, which belongs to the GTO Wizard chart deleted
before this phase restarted and which the sibling files name `GTO_WIZARD_SIZINGS`."""
DECISIONS = (
    REPO_ROOT / "reports" / "phase_audits" / "decisions" / "PHASE_14_CHART_CUTOVER_DECISIONS.md"
)

# --- the numbers, and where each is ruled --------------------------------------------------- #
#
# Nothing here is invented. The census figures come from `test_chart_derivation.py`, which is
# where the walk that derives them lives, and which this file reaches as a **module** so a
# constant that lane has not written yet is an AttributeError inside one test rather than a
# collection error that silences every assertion in the file. The rest carry the ruling.

PRICES = (2.5, 7.5, 13.5)
"""Every raise price a committed **key** names - what the seats before hero were offered, not what
hero is. MAINT-34 splits the three-bet by seat, so a key spells 7.5 where an in-position seat
re-raised and 13.5 where a blind did. `100.0` is still not among them: hero is never asked to
answer a jam, which is the half of the old claim that survives a committed spot being able to
offer one. The jam canary in the sibling file runs against the export for the other half."""

BIG_BLIND_OPEN_FACING_SPOTS = 5
MERGED_SPOTS = 11
THREE_BET_FACING_SPOTS = 135
MERGED_CELLS = 72
"""Decision 45: of the 16 facing-an-open spots, 5 are the big blind and keep fold/call/raise, and
at the other 11 the bot may not cold-call, so each cell's call weight is added to its raise. 72
cells move. The three families are 5 + 11 + 135 and they publish three different menus."""

PURE_AT_99_PCT_SOLVED = 90.79
MIXED_BELOW_90_PCT_SOLVED = 5.68
PURE_AT_99_PCT_PUBLISHED = 91.04
MIXED_BELOW_90_PCT_PUBLISHED = 5.55
"""Decisions 49 and 53, and **each pair says which grid it is measured over**, because the two
differ and this phase has already shipped one figure under two meanings. Both run over the same
14,586 cells at non-zero reach.

`_SOLVED` is the solve's own grid, before decision 45 folds the cold call into the raise, and it is
the pair the argument rests on: the chart barely mixes, which is why decision 45's hole was large
rather than marginal - "the solver was near-indifferent, take the other action" was never
available to the merge. `_PUBLISHED` is the artifact this phase writes, where the merge has turned
36 mixed cells pure. A generator computing purity off the file it just wrote reads 91.04, so both
are printed and each is labelled."""

ARRIVAL_ROUNDING_TO_ZERO = 53
ARRIVAL_EXACTLY_ZERO = 47
"""Decision 53: 53 of the 156 round to zero in parts per billion and 47 are exactly zero, so the
grain is published with the count rather than the zeroes read as unreachable spots. These were
44 and 2 at a 7.5bb blind three-bet, went to 181 and 175 at 13.5, and came back here when
decision 7's clause five refused the 128 spots whose exposure could not be measured - every one
of them at zero arrival."""

ROW_LADDER_COMPARISONS = 132
"""The kicker relation's comparison count over a full grid - adjacent kickers only, suited and
offsuit taken apart. The contract's figure."""

HERO_CLOSES_SPOTS = 89
"""Decision 49's correction: the spots where hero closes the action, which is where the equity
relation is defined at all. It was published as 93 over a set that has since moved, and 120 over
the 7.5bb committed 249."""

OPENERS_NARROWER_THAN_RAKED = 3
OPENERS_NARROWER_WORST_SEAT = "BTN"
BB_DEFENCE_NARROWER_THAN_RAKED = 1
"""The fifth accepted defect, ruled 2026-09-06 after a post-completion review of this phase.

Both families this repo can read against an outside number go the wrong way at at least one seat,
and the report asserted the opposite until this date. The reference is a RAKED NL25 game and this
is a rake-free solve, so rake-free is supposed to open and defend WIDER; a seat reading narrower is
the one direction that argument cannot explain. Opens read narrower at HJ, CO and BTN, worst at
BTN with 37.363 against 40.560, and the big blind's defence at BTN alone with 37.326 against
39.430 - the same seat both times, and the seat where a rake-free solve should stretch furthest.

**These are counts of seats and not a tolerance.** Nothing gates on the comparison (decision 6) and
this phase does not re-price a range; what changed is what the phase SAYS about what it shipped.
The counts are pinned here so a generator printing a hand-typed one goes red
(HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES), and the report re-derives both columns from
the artifact and the expectations file on every run.

**The small blind's opening row is deliberately excluded from the narrower count and is not
evidence of width.** The reference both raises and limps from that seat and this chart has no limp
branch, so its raise-only column is not the same quantity. Read entry to entry it is +5.70 rather
than +19.43, and the report prints that row and says so."""

PAIR_INVERSIONS = 87
KICKER_INVERSIONS = 197
KICKER_WHEEL_ACE = 60
KICKER_NO_STORY_WIDE = 15
KICKER_NO_STORY_NARROW = 122
RAISE_ACTION_INVERSIONS = 73
RAISE_ACTION_INVERSIONS_INVISIBLE = 27
"""Decisions 49 and 50, the raise-action pair corrected by decision 55 on 2026-09-03 and
re-measured whole for MAINT-34. The wheel-ace cases are correct poker and are separated out;
60 + 15 + 122 is the 197.

Run as this phase defines the relation - adjacent pair ladder, twelve comparisons, one-point
tolerance, strict, reach floor zero, every committed spot - the fourth relation reads **73**
inversions on the merged raise weight the bot plays, **27** of them invisible to play-not-fold,
against 81 and 35 on the solve's raw raise row. Both are re-derived from the export by
`test_chart_cutover_evidence.py`, which reaches them here, so a generator that prints a
hand-typed count goes red on the walk rather than on a substring.

**`PAIR_INVERSIONS` was the figure the two walks disagreed on, and decision 6 repaired the cause
rather than picking a side.** The report read 150 and `test_chart_cutover_evidence.py` 149, over
an identical 2,824 comparisons. 149 is right: at `t6/d100/HJ/HJ:raise@2.5,BTN:call,BB:raise@13.5`
the pair `99` and `88` play 0.84 and 1.84 percent, a gap of **exactly** the one-point tolerance,
and the tolerance is strict. The report reached 1.0000000000000009 subtracting the chart's
four-decimal weights where the walk reached 1.0 from the export's basis points. Both now round to
six decimal places before comparing - finer than the data, which is whole basis points - so the
noise is gone and neither can flag it."""

EV_BAND = {0.65: (0.10, 0.70), 0.85: (8.76, 13.04)}
"""Decision 34's cost, in big blinds per 100 occurrences of the spot, at both ends of the
realization range it depends on. Two ends and never a midpoint: the band cannot be narrowed
without measuring realization in this game, which nothing here does.

**What it prices is the over-folding**, in decision 34's own words: the big blind defending too
tight at the fit's own realization number for a single-raised pot. The band's shape is that of a
one-sided fold-too-much cost - near zero at R = 0.65, where equity that is folded away could not
have been realized anyway, and up to 125 times that at R = 0.85, where it could. It does not price
the flat's near-invariance to who opened, which is a two-sided shape error and is carried by
`BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`.

Two separate measurements sit under this and must not be confused, which is why every printed
comparison names the reference it is read against. The chart does read **wider** than
`expectations/six_max_nl25_100bb.json` at four of the five openers, narrower only against the
button. That file is a **raked** game, so a rake-free solve reading wider than it is the floor
rather than evidence the level is sound, and nothing in this repo commits a rake-free reference to
read the level against (`REFERENCE-RANGES-HAVE-NO-CITED-SOURCE`,
`NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE`). The flat separately spans 16.37
points across those five openers, which is the fingerprint decision 34 names, not a second defect
wearing this band's price."""

RETIRED_SPOTS = 86
RETIRED_SIZING_ENTRIES = 36
"""Decision 53: the chart this phase retires holds 86 spots, 36 carrying a sizing entry, and all
36 of those priced at a jam the ruled config cannot produce. The ledger balances against them, so
the test reads them back out of git at the pin the report names."""

ARM_ROWS = {
    # partition: (suit solved, suit transposed, rank solved, rank permuted,
    #             spots the rank arm scored, comparisons skipped solved, skipped permuted)
    "the committed set": (8, 110, 197, 390, 123, 10123, 10522),
    "raises faced 0": (0, 5, 11, 56, 5, 0, 0),
    "raises faced 1": (0, 16, 26, 112, 16, 0, 0),
    "raises faced 2": (8, 89, 160, 222, 102, 10123, 10522),
    "hero=LJ": (0, 12, 3, 23, 20, 2052, 2166),
    "hero=HJ": (0, 9, 9, 23, 13, 1144, 1210),
    "hero=CO": (1, 10, 12, 28, 10, 1620, 1660),
    "hero=BTN": (3, 21, 101, 114, 22, 2343, 2455),
    "hero=SB": (4, 32, 44, 107, 32, 2964, 3031),
    "hero=BB": (0, 26, 28, 95, 26, 0, 0),
}
"""Decision 53's figures over all ten partitions, re-derived on 2026-09-03 by two independent
walks after decision 54 withdrew the closed-spot restriction. The suit arm scores **spots**
holding a suited-under-offsuit cell; the rank arm scores **cells** breaking the row ladder, over
**every spot in the partition**, skipping a comparison whose partner cell is absent.

The two skipped columns are the arm's own account of what it could not look at, published on each
side because they differ - the reversal carries a present cell onto a different row. They are two
numbers rather than one because the figure this correction replaced, "149 against 69", was built
by taking one side from each of two different comparison rules. Both self-consistent readings pass
on every partition; the closest is `hero=BTN` at 101 against 114. A lane that finds this red halts
and says so; it does not move the tolerance or which comparisons count.

**These figures and `PARTITIONS` in `test_chart_cutover_evidence.py` are now equal by
construction, which MAINT-34 had to repair.** They were not: this column read 18 over the
committed set against the walk's 17, one spot apart at `raises faced 1` and `hero=SB`, and the
pair ladder read 150 against 149. Neither was a different rule - both walks compare
`low - high > TOLERANCE_PCT`. They read the same cell off different sources, the report off the
chart's four-decimal weights and the walk off the export's basis points, and at a pair sitting on
**exactly** the one-point tolerance the two subtractions land either side of it. Both now round to
`CELL_PCT_DECIMALS` first, which removes representation noise and cannot remove a real difference,
because every honest value is a whole number of basis points. Decision 6."""

RANK_ARM_SPOT_FLOOR = 5
"""Below five scored spots a strict gate over one or two grids is a coin flip, so the partition
publishes rather than asserts. Over the 156 no partition falls below it: the smallest, `raises
faced 0`, scores exactly five, so every row is asserted."""

# --- the report's shape --------------------------------------------------------------------- #

HEADINGS = {
    "census": "## The node census, bucket by bucket",
    "exposure": "## Multiway exposure, per committed spot",
    "trace": "## One converted cell, traced",
    "arrival": "## The arrival grain, and the spots that round to zero",
    "relations": "## The four relations, measured and gating nothing",
    "ladders": "## The group-order ladders, published for a human",
    "arms": "## The two counterfactual arms, on every partition",
    "equity": "## The equity relation, published and gating nothing",
    "defects": "## The five accepted defects, and what each costs",
    "orderings": "## The two orderings",
    "big_blind": "## The big blind's defence and flat, per opener",
    "bands": "## Every published band, against its family's extremes",
    "menus": "## The menu each family publishes, and the merged flats",
    "expectations": "## The derived chart against the GTO Wizard expectations",
    "ledger": "## The cutover ledger",
    "vacuous": "## The three criteria with no instance in the committed set",
    "jams": "## Hero's own jam, at the spots this phase withholds",
    "limitations": "## What the source cannot price, in poker terms",
    "corpus": "## The corpus, before and after",
    "prediction": "## The pre-registered prediction",
    "price": "## The price the corpus was played at",
    "explanations": "## What this measurement can and cannot separate",
    "bounds": "## What this chart does not answer",
    "refusals": "## The refusal inventory, by reason",
    "old_versus_new": "## Where the retired chart and the derived chart disagree",
    "recomputable": "## One number a reader can recompute by hand",
}

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")
POPULATIONS = ("Pluribus", "humans")

EXPOSURE_ROW = re.compile(
    r"^\s*(t6/\S+)\s+exposure\s+(\d+\.\d+)\s+multiway\s+(\d+\.\d+)\s+heads-up\s+(\d+\.\d+)\s*$",
    re.MULTILINE,
)
ARM_ROW = re.compile(
    r"^\s*(.+?)\s+spots\s+(\d+)\s+suit swap\s+solved\s+(\d+)\s+transposed\s+(\d+)"
    r"\s+rank reversal\s+solved\s+(\d+)\s+permuted\s+(\d+)\s+over\s+(\d+)\s+scored"
    r"\s+skipped\s+(\d+)\s+permuted-skipped\s+(\d+)\s+(asserted|published)\s*$",
    re.MULTILINE,
)
LADDER_ROW = re.compile(r"^\s*group\s+(.+?)\s+solved\s+(\d+)\s+transposed\s+(\d+)\s*$", re.M)
RELATION_ROW = re.compile(
    r"^\s*relation\s+(.+?)\s+violations\s+(\d+)\s+of\s+(\d+)\s+comparisons\s+worst\s+(\S.*?)\s*$",
    re.MULTILINE,
)
BAND_ROW = re.compile(
    r"^\s*band\s+(.+?)\s+over\s+(\d+)\s+(\S+)\s+min\s+(-?\d+\.\d+)\s+max\s+(-?\d+\.\d+)\s*$",
    re.MULTILINE,
)
MENU_ROW = re.compile(r"^\s*family\s+(.+?)\s+spots\s+(\d+)\s+menu\s+(\S+)\s*$", re.MULTILINE)
MERGED_ROW = re.compile(
    r"^\s*(t6/\S+)\s+defence\s+(\d+\.\d+)\s+solve raise\+call\s+(\d+\.\d+)\s*$", re.MULTILINE
)
BIG_BLIND_ROW = re.compile(
    r"^\s*vs\s+(LJ|HJ|CO|BTN|SB)\s+defends\s+(\d+\.\d+)\s+flats\s+(\d+\.\d+)"
    r"\s+raked reference\s+(\d+\.\d+)\s+(wider|narrower)\s*$",
    re.MULTILINE,
)
REFUSAL_ROW = re.compile(r"^\s*(lookup:[a-z-]+)\s+(\d+)\s+(\d+)\s*$", re.MULTILINE)
RATE_ROW = re.compile(
    r"\s*([a-z][a-z -]*?),\s*(before|after)\s+(\d+) of (\d+) [a-z ]+\((\d+\.\d)%\)"
)


def load_generator():
    """Imported in a function body rather than at the top: a top-level import of a module stage 6
    has not written turns the whole file into one collection error, which is how a previous cut
    froze a completed phase's tests having never executed one of them.

    The three loaders are plain functions and the fixtures below are three-line wrappers, because a
    fixture does not cross a module import: the split files define their own wrappers over these
    rather than re-writing the bodies, so the assertions guarding them exist once."""
    import scripts.generate_derived_chart_report as module

    return module


def load_report_text(generator) -> str:
    output = generator.REPORT_OUTPUT
    assert output.exists(), f"{output} is missing, so `{COMMAND_ID}` has not run"
    return output.read_text(encoding="utf-8")


def load_artifact():
    """The one committed chart. Two would mean the report's figures are about a mixture."""
    found = import_preflop_artifacts(ARTIFACT_DIR)
    assert len(found) == 1, f"the report's figures are about {[a.source.name for a in found]}"
    return found[0]


@pytest.fixture(scope="module")
def generator():
    return load_generator()


@pytest.fixture(scope="module")
def report_text(generator) -> str:
    return load_report_text(generator)


@pytest.fixture(scope="module")
def artifact():
    return load_artifact()


def section(text: str, key: str) -> str:
    """The body under one heading, so a claim is read where it is made rather than swept for."""
    marker = f"\n{HEADINGS[key]}\n"
    assert text.count(marker) == 1, f"the report needs exactly one {HEADINGS[key]!r} section"
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True)


def hero_seat(spot_key_text: str) -> str:
    """The seat hero sits in, read off the key rather than off the artifact's declared field, so
    a spot whose key and whose declared seat disagree is visible from here."""
    return spot_key_text.split("/")[2]


def raises_faced(spot_key_text: str) -> int:
    """How many raises are already in the pot hero is being asked about. Everything after the
    seat is the action history, and `rfi` is first in."""
    history = spot_key_text.split("/", 3)[3]
    return 0 if history == "rfi" else history.count(":raise@")


def partitions(artifact) -> dict[str, tuple[str, ...]]:
    """The ten the arms are measured on - the whole set, one per hero seat, one per raises faced
    - derived from the committed keys by a walk written here and never taken from the report."""
    found: dict[str, list[str]] = {"the committed set": []}
    for spot in artifact.spots:
        key = spot.spot_id
        found["the committed set"].append(key)
        for label in (f"hero={hero_seat(key)}", f"raises faced {raises_faced(key)}"):
            found.setdefault(label, []).append(key)
    return {label: tuple(keys) for label, keys in found.items()}


def spot_menus(artifact) -> dict[str, frozenset[str]]:
    """Which actions each committed spot offers hero over any class."""
    return {
        spot_id: frozenset(action for _, weights in classes for action, _ in weights)
        for spot_id, classes in artifact.action_weights
    }


def rate_rows(body: str) -> list[tuple[str, str, str, int, int, float]]:
    """Every published rate with the population block that owns it; a rate outside a block pools
    two different sets of players into one number."""
    rows = []
    population: str | None = None
    for line in body.splitlines():
        if line.strip() in POPULATIONS:
            population = line.strip()
            continue
        match = RATE_ROW.match(line)
        if match is None:
            continue
        assert population is not None, f"a rate published outside any population block: {line!r}"
        label, when, agreed, over, percent = match.groups()
        rows.append((population, label, when, int(agreed), int(over), float(percent)))
    return rows


# --- what the report prints about the derivation ---------------------------------------------- #


def test_the_census_and_the_spot_count_are_published_against_the_export_and_the_walk(
    report_text, artifact
) -> None:
    """Seven buckets summing to the export's own node count, and the spot set checked key by key.

    Seven, not the six this docstring said and not the four the heading said until MAINT-34:
    committed, the five exclusion codes, and the inexpressibility code. The census prints and
    totals all seven rows. A bucket count typed into prose beside a partition that is derived is
    the same defect as any other hand-typed count
    (HAND-TYPED-COUNTS-GO-STALE-EVERY-TIME-THE-SET-MOVES).

    Two failures live here and arithmetic catches neither. A census that balances can still be a
    subset dressed as a census, which is why the total is checked against a figure on the export's
    source card rather than against itself. And a converter that dropped one node while inventing
    one key gives the identical count, which is why the report publishes the invented and dropped
    keys rather than only the totals - 156 nodes are not self-evidently 156 keys.

    The vocabulary is closed and the five codes stay apart because a reader has to be able to
    tell which nodes come back by which route: the multiway family when GTOpen can price a
    multiway pot, the nine big-blind squeeze spots when the flats are repaired, the 160 with no
    arriving class and the 128 whose split does not close when a solve stops driving those lines
    to zero, and the 30,002 beyond the committed depth when a later phase takes up the four-bet.
    A census folding two of them together balances exactly and is refused for saying nothing.
    """
    body = section(report_text, "census")
    committed = re.search(r"^\s*committed\s+(\d+)\s*$", body, re.MULTILINE)
    excluded = {
        code: int(count)
        for code, count in re.findall(
            r"^\s*excluded\s+(derivation:[a-z-]+)\s+(\d+)\s*$", body, re.MULTILINE
        )
    }
    unwritable = re.findall(r"^\s*inexpressible\s+(derivation:[a-z-]+)\s+(\d+)\s*$", body, re.M)
    total = re.search(r"^\s*total\s+(\d+)\s*$", body, re.MULTILINE)
    coverage = re.search(r"^\s*coverage\s+(\d+\.\d+)\s+percent\s*$", body, re.MULTILINE)
    keys = re.search(
        r"^\s*artifact keys\s+(\d+)\s+walked keys\s+(\d+)\s+invented\s+(\d+)"
        r"\s+dropped\s+(\d+)\s*$",
        body,
        re.MULTILINE,
    )

    assert committed is not None and total is not None and keys is not None, body
    assert coverage is not None, "the census publishes no coverage figure"
    assert int(committed.group(1)) == derivation_tests.COMMITTED_NODES == len(artifact.spots)
    assert excluded == {
        derivation_tests.EXPOSURE_CODE: derivation_tests.EXPOSURE_REFUSED_NODES,
        derivation_tests.SQUEEZE_CODE: derivation_tests.BB_SQUEEZE_REFUSED_NODES,
        derivation_tests.NO_ARRIVING_CODE: derivation_tests.NO_ARRIVING_REFUSED_NODES,
        derivation_tests.SPLIT_CODE: derivation_tests.SPLIT_REFUSED_NODES,
        derivation_tests.DEPTH_CODE: derivation_tests.BEYOND_DEPTH_NODES,
    }
    assert set(excluded) == set(lookup.DERIVATION_EXCLUSION_CODES)
    assert unwritable and all(int(count) == 0 for _, count in unwritable), unwritable
    assert {code for code, _ in unwritable} <= set(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert float(coverage.group(1)) == pytest.approx(derivation_tests.COVERAGE_PCT, abs=0.0001)

    counted = int(committed.group(1)) + sum(excluded.values()) + sum(int(c) for _, c in unwritable)
    card = json.loads(SOURCE_CARD.read_text(encoding="utf-8"))
    assert counted == int(total.group(1)) == card["node_counts"]["exported"]
    assert counted == derivation_tests.EXPORTED_NODES

    artifact_keys, walked_keys, invented, dropped = (int(value) for value in keys.groups())
    assert artifact_keys == walked_keys == len(artifact.spots)
    assert invented == dropped == 0, "the artifact and the walk disagree key by key"
    assert len({spot.spot_id for spot in artifact.spots}) == len(artifact.spots)


def test_the_committed_set_has_the_shape_the_rulings_selected(report_text, artifact) -> None:
    """The histogram, the seats and the prices, recomputed off the artifact's own keys.

    5 first-in, 16 facing an open, 135 facing a three-bet, and nothing deeper: three-bet-facing is
    the deepest the filters admit, so a fourth bucket here is a converter that committed something
    above the ruled depth. The prices are exactly the three the solve offers and `100.0` is not
    among them, which is what makes hero's own jam a property of the withheld family rather than
    of this chart.
    """
    body = section(report_text, "census")
    histogram = Counter(raises_faced(spot.spot_id) for spot in artifact.spots)
    printed = {
        int(faced): int(count)
        for faced, count in re.findall(r"^\s*raises faced\s+(\d+)\s+(\d+)\s*$", body, re.MULTILINE)
    }
    prices = {
        float(price)
        for spot in artifact.spots
        for price in re.findall(r"raise@([0-9.]+)", spot.spot_id)
    }

    assert dict(histogram) == derivation_tests.RAISES_FACED_WHEN_COMMITTED
    assert printed == dict(histogram), (printed, dict(histogram))
    assert max(histogram) == 2, "a committed spot sits above the ruled raise depth"
    assert prices <= set(PRICES), f"the committed keys carry a price outside {PRICES}: {prices}"
    assert 100.0 not in prices, "hero faces a jam at a committed spot, which the config forbids"
    assert {hero_seat(spot.spot_id) for spot in artifact.spots} <= set(SEATS)


def test_exposure_is_published_per_committed_spot_with_both_extremes(
    report_text, artifact
) -> None:
    """The filter's margin is sixteen hundredths of a point, so it is published, not described.

    Every committed spot gets a row with its terminal split, the widest admitted and the narrowest
    refused are named, and the threshold is stated. The split is what makes the row readable:
    exposure is the share of a spot's decision mass reaching a multiway flop terminal over the
    branches the bot can take, so multiway and heads-up are the two halves of that mass and have
    to add to a hundred. A row publishing exposure alone could be over any denominator at all.

    The section also has to state what the filter got wrong, because decision 48 found it: the ten
    big-blind squeeze spots passed **because** the big blind folds 93 percent there, so almost
    nothing reaches the three-way flop. The filter is blindest exactly where the mispricing has
    already turned a call into a fold.
    """
    body = section(report_text, "exposure")
    rows = EXPOSURE_ROW.findall(body)
    threshold = re.search(r"^\s*threshold\s+(\d+\.\d+)\s*$", body, re.MULTILINE)
    widest = re.search(r"^\s*widest admitted\s+(t6/\S+)\s+(\d+\.\d+)\s*$", body, re.MULTILINE)
    narrowest = re.search(r"^\s*narrowest refused\s+(t6/\S+)\s+(\d+\.\d+)\s*$", body, re.MULTILINE)

    assert len(rows) == len(artifact.spots) == derivation_tests.COMMITTED_NODES, len(rows)
    assert {key for key, *_ in rows} == {spot.spot_id for spot in artifact.spots}
    assert threshold is not None and widest is not None and narrowest is not None, body
    assert float(threshold.group(1)) == derivation_tests.EXPOSURE_THRESHOLD_PCT

    measured = {key: float(exposure) for key, exposure, _, _ in rows}
    for key, exposure, multiway, heads_up in rows:
        assert float(exposure) < float(threshold.group(1)), f"{key} is committed above the line"
        assert float(multiway) + float(heads_up) == pytest.approx(100.0, abs=0.05), key
        assert float(multiway) == pytest.approx(float(exposure), abs=0.0002), key

    assert widest.group(1) in measured, "the widest admitted spot is not one of the committed ones"
    assert float(widest.group(2)) == pytest.approx(max(measured.values()), abs=0.0002)
    assert float(widest.group(2)) == pytest.approx(
        derivation_tests.WIDEST_ADMITTED_EXPOSURE_PCT, abs=0.0002
    )
    assert narrowest.group(1) not in measured, "the narrowest refused spot is also committed"
    assert float(narrowest.group(2)) == pytest.approx(
        derivation_tests.NARROWEST_REFUSED_EXPOSURE_PCT, abs=0.0002
    )
    assert float(narrowest.group(2)) > float(threshold.group(1))
    assert "MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN" in body
    assert re.search(r"blindest|already turned a call into a fold", body), (
        "the section does not say the filter is blind where the mispricing produced the fold"
    )


def test_one_cell_is_traced_from_an_export_node_to_the_row_it_became(
    report_text, artifact
) -> None:
    """A printed trace proves nothing, so every figure on it is read back out of the artifact.

    Reach and arrival are both on the row because neither says what the other does. Reach is "can
    hero hold this hand here", a plain mean over the 169 classes with no floor selecting cells;
    arrival is "is this line played at all", one left-to-right product from the root in parts per
    billion. Over the 156 arrival spans many orders of magnitude and reach does not, which is why
    the grain section below has to exist at all.
    """
    body = section(report_text, "trace")
    row = re.search(
        r"^\s*artifact row\s+(t6/\S+)\s+([2-9TJQKA]{2}[so]?)\s+(.+?)\s+reach\s+(\d+) bp"
        r"\s+arrival\s+(\d+) ppb\s*$",
        body,
        re.MULTILINE,
    )

    assert re.search(r"^\s*export node\s+\S+", body, re.MULTILINE), "no export node on the trace"
    assert row is not None, "the trace does not print the artifact row in the pinned form"

    spot_key_text, hand_class, printed, reach, arrival = row.groups()
    weights = [classes for spot, classes in artifact.action_weights if spot == spot_key_text]
    assert weights, f"{spot_key_text} is not a committed spot"
    cells = {text: dict(actions) for classes in weights for text, actions in classes}
    assert hand_class in cells, f"{spot_key_text} carries no {hand_class}"
    published = dict(re.findall(r"([a-z]+)=([0-9.]+)", printed))
    assert published, f"the trace prints no action weights: {printed!r}"
    for action, weight in published.items():
        assert cells[hand_class].get(action) == pytest.approx(float(weight), abs=0.0001), action
    assert set(published) == set(cells[hand_class]), "the trace drops an action the cell holds"
    assert artifact.reach_bp_for(spot_key_text, hand_class) == int(reach)
    assert dict(artifact.arrival_ppb)[spot_key_text] == int(arrival)


def test_the_arrival_grain_is_published_with_the_count_of_spots_rounding_to_zero(
    report_text, artifact
) -> None:
    """Arrival is a probability at a scale where a third of the committed set rounds away.

    53 of the 156 round to zero in parts per billion and 47 are exactly zero, so a reader who
    saw the zeroes without the grain would read 53 unreachable spots where there are 47. The
    count is recomputed here off the artifact's own `arrival_ppb` rather than read back off the
    sentence that states it, and the zero case is asserted non-vacuous: if nothing rounded to
    zero, publishing the grain would be a fact about the format and a criterion that cannot fail.
    """
    body = section(report_text, "arrival")
    grain = re.search(r"^\s*grain\s+parts per billion\s*$", body, re.MULTILINE)
    rounding = re.search(r"^\s*rounding to zero\s+(\d+) of (\d+)\s*$", body, re.MULTILINE)
    exactly = re.search(r"^\s*exactly zero\s+(\d+)\s*$", body, re.MULTILINE)

    assert grain is not None, "the report does not state the unit arrival is published in"
    assert rounding is not None and exactly is not None, body

    arrivals = dict(artifact.arrival_ppb)
    zeroes = sum(1 for value in arrivals.values() if value == 0)
    assert len(arrivals) == len(artifact.spots), "a committed spot claims no arrival"
    assert int(rounding.group(2)) == len(artifact.spots)
    assert int(rounding.group(1)) == zeroes == ARRIVAL_ROUNDING_TO_ZERO
    assert int(exactly.group(1)) == ARRIVAL_EXACTLY_ZERO
    assert zeroes > 0, "nothing rounds to zero, so publishing the grain checks nothing here"
    assert int(exactly.group(1)) < zeroes, (
        "the report does not separate the spots that are never dealt from the ones that round"
    )
    assert max(arrivals.values()) <= 1_000_000_000, "an arrival above one is not a probability"
