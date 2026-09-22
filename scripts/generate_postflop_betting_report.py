"""The committed flop solve, written for a reviewer who does not read code.

A report renders whatever it is handed. A spot count that disagrees with the index, a coverage
share that pools two loss causes, a byte figure that disagrees with the bytes on disk and an
exploitability figure printed without its menu qualification all exit 0 and publish as happily as
the right numbers would. So every figure the contract names as an obligation is **re-derived
here** out of a committed file or out of the deck itself, and the command exits non-zero and
writes nothing when one does not hold.

Nothing below is quoted from a decision list, a backlog entry or another phase's report. The
class census is brute-forced over every three-card board; the corpus figures are counted off the
committed corpus; every figure about the committed cells is read out of `data/artifacts/postflop/`
and nothing else, the cost model alone coming from the separate solve-cost record; the behaviour
figures come from asking the strategy itself.

**What this report may never say**, and each is asserted by a frozen test rather than left to a
reviewer's memory: no single accuracy figure for the artifact as a whole, no figure of chips won
and no expected-value figure over this artifact - the hands they would come from are the ones
that ended at the turn refusal - no scaled figure reported as a measured one, no capped solve's
wall clock reported as a cost, and no determinism tolerance, because if the two solves are not
byte-identical the phase halts and a human is asked.

**Measured and scaled are separated on every row that carries a cost**, not once in a footnote.
Rainbow was never solved to target, so no rainbow row may read as a measurement.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_file_sizes  # noqa: E402

from poker_training_bot.data_pipeline.sample import load_committed_sample  # noqa: E402
from poker_training_bot.hand_history.schema import HistoryActionKind  # noqa: E402
from poker_training_bot.poker_core.cards import parse_cards  # noqa: E402
from poker_training_bot.poker_core.hand_eval import evaluate_best  # noqa: E402
from poker_training_bot.poker_core.positions import seat_positions  # noqa: E402
from poker_training_bot.solver_artifacts.postflop_artifact import (  # noqa: E402
    EXPLOITABILITY_CEILING_PCT_OF_POT,
    EXPLOITABILITY_TARGET_PCT_OF_POT,
    INDEX_PATH,
    POSTFLOP_DIR,
    RANGE_WEIGHT_FLOOR,
    SAMPLE_DIR,
    SOLVE_ITERATION_CAP,
    PostflopCell,
    import_postflop_index,
    indexed_spot_keys,
)
from poker_training_bot.solver_artifacts.postflop_key import (  # noqa: E402
    CANONICAL_FLOP_CLASSES,
    FLOP_BET_MENU,
    PRICE_BAND_FRACTION,
    canonical_board,
    canonical_hole_cards,
    price_within_band,
)
from poker_training_bot.solver_artifacts.spot_key import (  # noqa: E402
    PreflopAction,
    render_entry,
)
from poker_training_bot.strategy import postflop_fallback  # noqa: E402
from poker_training_bot.strategy.contract import (  # noqa: E402
    StrategyDecision,
    StrategyRefusal,
)
from poker_training_bot.strategy.postflop_betting import (  # noqa: E402
    REFUSAL_CODES,
    PostflopBettingStrategy,
)
from poker_training_bot.strategy.postflop_committed import load_library  # noqa: E402
from poker_training_bot.strategy.postflop_spot_queries import (  # noqa: E402
    committed_spot_queries,
)

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_postflop_betting_report.txt"
SOLVE_COST_REPORT = REPO_ROOT / "reports" / "active" / "latest_postflop_solve_cost.txt"
PREFLOP_CHART = REPO_ROOT / "data" / "artifacts" / "preflop" / "six_max_100bb_rakefree.json"
ARTIFACT_ROOT = REPO_ROOT / "data" / "artifacts"

DETERMINISM_PATH = POSTFLOP_DIR / "determinism.json"
DEEP_CHECK_PATH = POSTFLOP_DIR / "deep_convergence_check.json"
SOLVE_CONFIG_PATH = POSTFLOP_DIR / "solve_config.json"
OBJECTS_PATH = POSTFLOP_DIR / "objects.json"
"""The four committed files that describe the campaign this repo actually ran.

Before these were read, the determinism block and the range block were both parsed out of
`latest_postflop_solve_cost.txt`, which is August's cost measurement: another board, another
starting pot, another iteration count, and quantized arenas rather than the full precision the
committed campaign was ruled to. A block sourced from the nearest file that happens to have a
column of the right shape is a block about somebody else's run.
"""

ARTIFACT_BYTE_CAP = dict(
    (str(name), int(limit)) for name, limit in check_file_sizes.DIRECTORY_BYTE_LIMITS
)["data/artifacts"]
"""The cap `check_file_sizes` actually enforces, read out of it rather than restated here. A
headroom figure computed against a second copy of the number is a figure that goes stale the
moment the checker moves and says nothing went wrong."""

DECK_RANKS = "23456789TJQKA"
DECK_SUITS = "cdhs"
BOARD_CARDS = 3
ALL_BOARDS = 22100
"""C(52,3). Asserted against the enumeration rather than trusted."""

NAIVE_ORBIT = 24
"""The orbit an unpaired board really has, and the one a reader reaches for as though every
class had it. Carried as a named constant so the overstatement below is the comparison rather
than a figure typed twice."""

TEXTURES = ("rainbow", "two-tone", "monotone")
MEASURED = "measured"
SCALED = "scaled"
VACUOUS = "vacuous"

COMPARABLE_STARTING_POT = 16.0
"""The one starting pot in the committed solve record that carries converged rows and capped
rows on the same menu on both seats, which is what makes a texture comparison a comparison."""

TURN_RIVER_MENU = ("66", "125")
FLOP_RAISE = "2.5x"

_EXPLOITABILITY_FIGURE = re.compile(r"exploitability[^\n]*?\d+(?:\.\d+)?\s*%", re.IGNORECASE)
_TEXTURE = re.compile(r"\b(rainbow|two-tone|monotone)\b", re.IGNORECASE)
_STANDALONE_INTEGER = re.compile(r"(?<!\S)(\d+)(?!\S)")
_ROW_DATA = "Row data: "
_POOLED_LABEL = re.compile(r"\b(?:or|either)\b", re.IGNORECASE)
"""What a pooled cause label looks like: one row offering the reader a choice of reasons.

A lexical test rather than a structural one because the defect is lexical. The counts behind a
pooled row are correct arithmetic over the branch that produced them; what is wrong is that one
branch stands for two causes, and the only place that is visible is the label.
"""


class ReportFigureError(RuntimeError):
    """A figure this report was about to print does not re-derive.

    Raised rather than logged, and raised before anything is written: a wrong report on disk
    beside a non-zero exit code is worse than no report at all, because the file is what a
    reviewer reads.
    """


# --------------------------------------------------------------------------- #
# The validators the contract makes the generator own
# --------------------------------------------------------------------------- #


def check_bytes_reconcile(*, declared: float, on_disk: float) -> bool:
    """The byte figure the index declares against the bytes actually on disk.

    What the index declares is the whole `data/artifacts/postflop` directory - the index and the
    sample plus the campaign's own records beside them - so `on_disk` is that directory. Handing
    this the whole artifact tree compares a postflop figure against a number that is mostly
    preflop chart, and reds on a difference that is not a defect.

    This is not the figure the per-spot cost divides. The contract draws its budget around the
    index and the sample, which is a smaller number;
    `check_per_spot_cost_excludes_non_sample_bytes` owns that one, and the two are separate
    checks because they answer separate questions.
    """
    if float(declared) != float(on_disk):
        raise ReportFigureError(
            f"the committed index declares {declared} bytes and the postflop tree holds"
            f" {on_disk}; a byte budget checked against itself is not a byte budget"
        )
    return True


def check_rate_excludes_non_weight_bytes(
    *, rate_bytes_per_weight: float, weight_bytes: float, weight_count: int
) -> bool:
    """A per-weight rate must be weight bytes over weight count and nothing else.

    The error the stage-1 numbers review held this phase over: a rate computed as whole-file
    bytes over weight count charges the per-spot provenance blocks against every weight, and
    those scale per spot rather than per weight.
    """
    if weight_count < 0 or weight_bytes < 0:
        raise ReportFigureError(
            f"a per-weight rate cannot be built from {weight_bytes} bytes over"
            f" {weight_count} weights"
        )
    expected = 0.0 if weight_count == 0 else float(weight_bytes) / float(weight_count)
    if abs(float(rate_bytes_per_weight) - expected) > 1e-9:
        raise ReportFigureError(
            f"a rate of {rate_bytes_per_weight} bytes a weight does not come from"
            f" {weight_bytes} weight bytes over {weight_count} weights, which is {expected};"
            " the difference is non-weight bytes charged against every weight"
        )
    return True


def check_coverage_splits_by_cause(
    *, answerable: float, losses: Mapping[str, float], required: Sequence[str] = ()
) -> bool:
    """The answerable share plus every loss cause is the whole population, and no one label
    carries two causes.

    The sum alone is arithmetic over whatever causes the loop chose, and a row that pools two
    causes satisfies it exactly as well as two honest rows do - which is how the report came to
    print one figure for "no cell for this board, or in the index and not fetched" while its own
    refusal section asserted the two are never pooled. So two further properties:

    - no label names a disjunction. A cause label carrying `or` is a row that answers two
      questions with one number, whichever causes happen to be behind it.
    - every cause in `required` appears, at zero if that is its count. A cause dropped because it
      measured nothing is the same pooling defect arriving as an absence: the reader sees the
      remaining rows and has no way to know a second cause was ever asked about.

    `required` is empty by default because the property it enforces belongs to this report's own
    cause vocabulary rather than to the arithmetic, and a caller checking an arbitrary split has
    no vocabulary to declare.
    """
    for name in losses:
        if _POOLED_LABEL.search(str(name)):
            raise ReportFigureError(
                f"the loss cause {name!r} names more than one cause and carries one count;"
                " a share that answers two questions with one number is the pooling this split"
                " exists to refuse"
            )
    missing = [name for name in required if name not in losses]
    if missing:
        raise ReportFigureError(
            f"the loss causes {sorted(losses)} leave {missing} uncounted; a cause that prints no"
            " row is a cause the reader cannot tell was measured at zero rather than pooled"
        )
    total = float(answerable) + sum(float(value) for value in losses.values())
    if abs(total - 1.0) > 1e-9:
        raise ReportFigureError(
            f"an answerable share of {answerable} and losses {dict(losses)} sum to {total}"
            " rather than the whole population, so at least one loss cause is unaccounted for"
        )
    return True


def check_per_spot_cost_excludes_non_sample_bytes(
    *,
    cost_bytes_per_spot: float,
    index_and_sample_bytes: float,
    tree_bytes: float,
    tree_files_outside: int,
    spots: int,
) -> bool:
    """A per-spot cost must be the index and the sample over the spot count and nothing else.

    The same error as `check_rate_excludes_non_weight_bytes` on the other axis, and the one that
    shipped: the cost was the whole `data/artifacts/postflop` tree over the spot count, so the
    deep-convergence record, the determinism record, the solve config and the objects manifest
    were charged to every spot. The contract draws the byte budget around the index and the
    sample, and those four files are evidence about one campaign rather than a cost that grows
    with the next spot - the deep-convergence record is a single measurement of one cell and does
    not scale at all. A per-spot figure carrying them decides the wrong way on the question the
    criterion asks it, which is whether the index or the campaign cost is the binding bound on how
    many preflop lines the phase can cover.

    Unlike the per-weight check, this one is told where its numerator came from rather than only
    the division: `tree_files_outside` is how many files the postflop tree holds that are neither
    the index nor the sample. A numerator as large as the tree while that count is positive is the
    whole tree wearing the budget's label, which is the defect itself and not a rounding of it.
    """
    if spots < 0 or index_and_sample_bytes < 0 or tree_files_outside < 0:
        raise ReportFigureError(
            f"a per-spot cost cannot be built from {index_and_sample_bytes} bytes over"
            f" {spots} spots beside {tree_files_outside} files"
        )
    if index_and_sample_bytes > tree_bytes:
        raise ReportFigureError(
            f"the index and sample measure {index_and_sample_bytes} bytes inside a postflop tree"
            f" of {tree_bytes}; a part cannot be larger than what it was cut out of"
        )
    if tree_files_outside > 0 and index_and_sample_bytes >= tree_bytes:
        raise ReportFigureError(
            f"the per-spot numerator is {index_and_sample_bytes} bytes and the whole postflop"
            f" tree is {tree_bytes}, while {tree_files_outside} file(s) in it are neither the"
            " index nor the sample; that numerator is the tree under the budget's name, and the"
            " records it carries do not grow with the next spot"
        )
    expected = 0.0 if spots == 0 else float(index_and_sample_bytes) / float(spots)
    if abs(float(cost_bytes_per_spot) - expected) > 1e-9:
        raise ReportFigureError(
            f"a cost of {cost_bytes_per_spot} bytes a spot does not come from"
            f" {index_and_sample_bytes} index and sample bytes over {spots} spots, which is"
            f" {expected}; the difference is tree bytes that are neither index nor sample charged"
            " against every spot"
        )
    return True


def check_servable_never_exceeds_arrivals(
    *, arrivals: Mapping[str, int], servable: Mapping[str, int], answerable: int
) -> bool:
    """A line's servable count is a subset of its arrivals, and the subsets sum to answerable.

    The defect this refuses shipped: `servable` was counted beside `arrivals` and before the two
    gates that decide the question, so the column equalled arrivals for every input and the prose
    claiming the two orders differ could not have been true of anything.
    """
    for line, count in servable.items():
        reached = int(arrivals.get(line, 0))
        if int(count) > reached:
            raise ReportFigureError(
                f"{line} is servable {count} times out of {reached} arrivals; a line cannot be"
                " answered more often than it is reached"
            )
    summed = sum(int(value) for value in servable.values())
    if summed != int(answerable):
        raise ReportFigureError(
            f"the servable column sums to {summed} and {answerable} flops are answerable; the"
            " column is not counting the answers it says it counts"
        )
    return True


def check_refusal_counts_reconcile(*, total: int, by_code: Mapping[str, int]) -> bool:
    """Every refusal is broken out under exactly one code, or the breakdown is not one."""
    summed = sum(int(value) for value in by_code.values())
    if int(total) != summed:
        raise ReportFigureError(
            f"{total} refusals were counted and the per-code breakdown holds {summed};"
            " a refusal missing from the breakdown is a code nobody is looking at"
        )
    return True


def check_spot_count_matches_index(*, printed: int, in_index: int) -> bool:
    """The committed spot count the report is about to print against the index it came from."""
    if int(printed) != int(in_index):
        raise ReportFigureError(
            f"the report is about to print {printed} committed spots and the index accounts for"
            f" {in_index}; one node's difference stays plausible on the page and is exactly the"
            " drift this check exists to refuse"
        )
    return True


# --------------------------------------------------------------------------- #
# The three properties the report text has to hold, decided over the text
# --------------------------------------------------------------------------- #


def exploitability_lines_are_qualified(report: str) -> bool:
    """Every line printing an exploitability figure names the bet menu it is bound against.

    Line by line rather than once for the document: one footnote at the bottom of the page is
    not "wherever it prints the figure", and a line carrying the number without the clause reads
    as an unconditional accuracy, which is the claim the contract bans.
    """
    lines = [line for line in report.splitlines() if _EXPLOITABILITY_FIGURE.search(line)]
    if not lines:
        return False
    return all("menu" in line.lower() for line in lines)


def cost_rows(report: str) -> list[str]:
    """Every line that puts a figure beside a board texture, over the whole report.

    Deliberately not a list this module hands over: a generator choosing its own rows could
    publish an unlabelled figure by leaving it out.
    """
    return [
        line
        for line in report.splitlines()
        if _TEXTURE.search(line) and re.search(r"\d", line)
    ]


def cost_rows_declare_measured_or_scaled(report: str) -> bool:
    """Rainbow never reached the target, so a rainbow row carries `scaled` and never `measured`;
    every other texture row declares which of the two it is."""
    rows = cost_rows(report)
    if not rows:
        return False
    for line in rows:
        lowered = line.lower()
        if "rainbow" in lowered:
            if SCALED not in lowered or MEASURED in lowered:
                return False
        elif MEASURED not in lowered and SCALED not in lowered:
            return False
    return True


def code_rows(report: str, codes: Sequence[str]) -> dict[str, list[str]]:
    """The breakdown row for each refusal code: the line naming it that carries a bare count."""
    rows: dict[str, list[str]] = {}
    for line in report.splitlines():
        if not _STANDALONE_INTEGER.search(line):
            continue
        for code in codes:
            if code in line:
                rows.setdefault(code, []).append(line)
    return rows


def row_count(line: str) -> int:
    return int(_STANDALONE_INTEGER.findall(line)[-1])


def vacuous_codes_are_labelled(report: str, codes: Sequence[str] = REFUSAL_CODES) -> bool:
    """Both directions, because a report labelling nothing and one labelling everything both
    pass a naive search for the word. The vocabulary is the strategy's own closed list, so a
    code left out of the breakdown fails here rather than going unnoticed.

    An empty vocabulary is refused here rather than by whatever filled it: over no codes every
    clause below is vacuously satisfied, which is the shape this check exists to stop.
    """
    if not codes:
        return False
    rows = code_rows(report, codes)
    if sorted(rows) != sorted(codes):
        return False
    for found in rows.values():
        if len(found) != 1:
            return False
        line = found[0]
        if (VACUOUS in line.lower()) != (row_count(line) == 0):
            return False
    return True


# --------------------------------------------------------------------------- #
# The deck: the class census, brute-forced
# --------------------------------------------------------------------------- #


def texture_of(board: Sequence[str]) -> str:
    """Three distinct suits, two, or one."""
    return {3: "rainbow", 2: "two-tone", 1: "monotone"}[len({card[1] for card in board})]


@dataclass(frozen=True)
class TextureCensus:
    """One suit texture's share of the deck, counted rather than argued."""

    texture: str
    classes: int
    boards: int

    @property
    def mean_orbit(self) -> float:
        return self.boards / self.classes

    @property
    def board_share(self) -> float:
        return self.boards / ALL_BOARDS


def flop_class_census() -> dict[str, TextureCensus]:
    """Every three-card board mapped into its canonical class, then counted by texture.

    The orbit of a class is how many dealt boards land in it, and it is not one number: a
    paired board has fewer distinct suit dressings than an unpaired one and trips fewer again,
    so the naive "a rainbow class is twenty-four boards" overstates rainbow's share of the deck.
    The factor that matters is measured here, over the whole deck, using the same
    `canonical_board` the committed keys are derived with rather than a second canonicaliser.
    """
    deck = [rank + suit for rank in DECK_RANKS for suit in DECK_SUITS]
    orbit: Counter[tuple[str, ...]] = Counter()
    for board in combinations(deck, BOARD_CARDS):
        orbit[canonical_board(board)] += 1
    if len(orbit) != CANONICAL_FLOP_CLASSES or sum(orbit.values()) != ALL_BOARDS:
        raise ReportFigureError(
            f"the class census found {len(orbit)} classes over {sum(orbit.values())} boards,"
            f" against the {CANONICAL_FLOP_CLASSES} classes and {ALL_BOARDS} boards the deck has"
        )
    classes: Counter[str] = Counter()
    boards: Counter[str] = Counter()
    for board, size in orbit.items():
        name = texture_of(board)
        classes[name] += 1
        boards[name] += size
    return {
        name: TextureCensus(name, classes[name], boards[name])
        for name in TEXTURES
    }


# --------------------------------------------------------------------------- #
# The committed solve record: what was measured, and on what
# --------------------------------------------------------------------------- #


def solve_cost_rows() -> tuple[dict[str, Any], ...]:
    """The machine-readable rows of the committed solve-cost report."""
    if not SOLVE_COST_REPORT.is_file():
        raise ReportFigureError(f"{SOLVE_COST_REPORT} is missing, so no cost figure re-derives")
    rows = [
        json.loads(line[len(_ROW_DATA) :])
        for line in SOLVE_COST_REPORT.read_text(encoding="utf-8").splitlines()
        if line.startswith(_ROW_DATA)
    ]
    if not rows:
        raise ReportFigureError(f"{SOLVE_COST_REPORT} carries no machine-readable rows")
    return tuple(rows)


def _comparable(row: Mapping[str, Any]) -> bool:
    """One menu, one starting pot, one seat configuration - the only rows a texture comparison
    may put beside each other."""
    config = row["config"]
    return (
        row["group"] == "solve"
        and float(config["starting_pot"]) == COMPARABLE_STARTING_POT
        and _config_digest(config["ip"]) == _config_digest(config["oop"])
    )


def _config_digest(reference: str) -> str:
    """The body a `ref:config.ip@<digest>` names. The seat is in the field name and the digest
    is the config, so two seats carrying the same menu differ in the prefix and agree here."""
    return str(reference).rpartition("@")[2]


@dataclass(frozen=True)
class TextureCost:
    """What one texture cost, and whether the figure was taken or inferred."""

    census: TextureCensus
    converged_rows: int
    seconds_per_iteration: float | None
    seconds_to_target: float | None
    provenance: str
    basis: str


def texture_costs(census: dict[str, TextureCensus]) -> dict[str, TextureCost]:
    """Cost to target per canonical class, by texture, measured where it was measured.

    A row that stopped on the iteration cap reports a floor rather than a cost, so its wall
    clock is never a cost figure here - but its per-iteration fit is still a measurement of how
    heavy that texture's tree is, and that ratio is the only scaler the record supplies. Where a
    texture has a converged row its cost is that row's own wall clock. Where it has none - which
    is rainbow, on every row in the record - the cost is scaled from the converged texture by
    the per-iteration ratio, and the iteration count is borrowed rather than measured. Both
    halves of that are declared on the row.
    """
    rows = [row for row in solve_cost_rows() if _comparable(row)]
    per_iteration: dict[str, list[float]] = {name: [] for name in TEXTURES}
    to_target: dict[str, list[float]] = {name: [] for name in TEXTURES}
    for row in rows:
        name = texture_of(_board_cards(row["config"]["board"]))
        fit = row.get("fit") or {}
        seconds = fit.get("net_seconds_per_iteration")
        if row["outcome"] == "hit-iteration-cap" and isinstance(seconds, int | float):
            per_iteration[name].append(float(seconds))
        if row["outcome"] == "converged-to-target" and row.get("usable_for_mean"):
            to_target[name].append(float(row["solve"]["wall_seconds"]))
    reference = _reference_texture(to_target, per_iteration)
    costs: dict[str, TextureCost] = {}
    for name in TEXTURES:
        measured = statistics.median(to_target[name]) if to_target[name] else None
        rate = statistics.median(per_iteration[name]) if per_iteration[name] else None
        if measured is not None:
            costs[name] = TextureCost(
                census[name], len(to_target[name]), rate, measured, MEASURED,
                "its own converged rows in the committed record",
            )
            continue
        scaled = None
        basis = "no converged row and no comparable per-iteration row, so no cost is offered"
        if rate is not None and reference is not None:
            factor = rate / reference[1]
            scaled = reference[2] * factor
            basis = (
                f"{factor:.3f}x the {reference[0]} cost, from the per-iteration fits of capped"
                " rows on the same menu, at a borrowed iteration count"
            )
        costs[name] = TextureCost(census[name], 0, rate, scaled, SCALED, basis)
    return costs


def _reference_texture(
    to_target: Mapping[str, list[float]], per_iteration: Mapping[str, list[float]]
) -> tuple[str, float, float] | None:
    """The cheapest texture that both converged and has capped rows to scale from."""
    candidates = [
        (name, statistics.median(per_iteration[name]), statistics.median(to_target[name]))
        for name in TEXTURES
        if to_target[name] and per_iteration[name]
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda entry: entry[2])


def _board_cards(text: str) -> tuple[str, ...]:
    return tuple(text[index : index + 2] for index in range(0, len(text), 2))


def flop_line_of(spot_key: str) -> str:
    """The flop actions a committed spot key names, off the key itself.

    Two cells on one board differ only in this, so a table keyed on the board alone prints two
    rows a reader cannot tell apart.
    """
    for part in spot_key.split("/"):
        if part.startswith("f:"):
            return part[len("f:") :]
    raise ReportFigureError(f"{spot_key} names no flop line, so two cells on a board are one row")


def starting_pot_of(spot_key: str) -> float:
    """The starting pot a committed spot key names, off the key itself.

    The key is the only place the pot is written on the fifth cell, which the repo lists and
    does not hold, so a figure taken from the sample would silently skip it.
    """
    found = re.search(r"/p:([0-9.]+)/", spot_key)
    if not found:
        raise ReportFigureError(f"{spot_key} names no starting pot, so nothing can print one")
    return float(found.group(1))


@dataclass(frozen=True)
class DeterminismCell:
    """One cell solved twice, and what the two runs produced for it."""

    name: str
    spot_key: str
    board: str
    held: bool
    iterations: tuple[int, int]
    wall_seconds: tuple[float, float]
    digests: tuple[str, str]
    document_bytes: tuple[int, int]
    combos: int
    combos_in_only_one_run: int
    largest_gap: float
    documents_identical: bool
    arena_storage: tuple[str, ...]

    @property
    def starting_pot(self) -> float:
        return starting_pot_of(self.spot_key)


@dataclass(frozen=True)
class DeterminismRecord:
    """The committed determinism proof: every cell re-solved, and both comparisons per cell."""

    identical: bool
    configuration: str
    cells: tuple[DeterminismCell, ...]

    @property
    def iterations(self) -> tuple[int, int]:
        counts = [count for cell in self.cells for count in cell.iterations]
        return (min(counts), max(counts))

    @property
    def starting_pots(self) -> tuple[float, ...]:
        return tuple(sorted({cell.starting_pot for cell in self.cells}))


def determinism_record() -> DeterminismRecord | None:
    """The committed determinism proof, out of the file the campaign wrote.

    Not out of `latest_postflop_solve_cost.txt`. That record's repeated solve is a different
    board at a different pot and iteration count under a different arena, and printing it under
    this heading answers the contract's "on the configuration actually committed" with a
    measurement of something else.
    """
    if not DETERMINISM_PATH.is_file():
        return None
    payload = json.loads(DETERMINISM_PATH.read_text(encoding="utf-8"))
    cells = tuple(
        DeterminismCell(
            name=str(entry["cell"]),
            spot_key=str(entry["spot_key"]),
            board="".join(entry["board"]),
            held=bool(entry.get("held_in_the_repo", True)),
            iterations=(int(entry["iterations"][0]), int(entry["iterations"][1])),
            wall_seconds=(
                float(entry["wall_seconds"][0]), float(entry["wall_seconds"][1])
            ),
            digests=(str(entry["strategy_digest"][0]), str(entry["strategy_digest"][1])),
            document_bytes=(int(entry["committed_bytes"]), int(entry["second_run_bytes"])),
            combos=int(entry["per_combo"]["combos"]),
            combos_in_only_one_run=int(entry["per_combo"]["combos_in_only_one_run"]),
            largest_gap=float(entry["per_combo"]["largest_gap"]),
            documents_identical=bool(entry["cell_document_bytes_identical"]),
            arena_storage=tuple(str(value) for value in entry["arena_storage"]),
        )
        for entry in payload["cells"]
    )
    record = DeterminismRecord(
        identical=bool(payload["identical"]),
        configuration=str(payload["configuration"]),
        cells=cells,
    )
    if len(cells) != int(payload["cells_compared"]):
        raise ReportFigureError(
            f"{DETERMINISM_PATH.name} says {payload['cells_compared']} cells were compared and"
            f" carries {len(cells)}"
        )
    return record


def check_determinism_covers_what_is_committed(
    *, record: DeterminismRecord | None, index: Mapping[str, Any] | None
) -> bool:
    """The proof is about the cells the repo commits, and it agrees with them.

    Three clauses, each one a different way this block could end up describing another run.
    Every indexed spot key is in the proof, so a cell solved once cannot hide behind four that
    were solved twice. Every entry's digest and iteration count in the proof match the index's.
    And the byte count the proof compared matches the sample file on disk, which is what makes
    "byte-identical" a statement about the repo rather than about two temporary directories.
    """
    if record is None:
        if index is not None and index.get("entries"):
            raise ReportFigureError(
                f"{len(index['entries'])} cells are indexed and no determinism proof is"
                " committed, so the report would publish a solve nobody repeated"
            )
        return True
    proved = {cell.spot_key: cell for cell in record.cells}
    entries = list(index["entries"]) if index else []
    missing = [
        str(entry["spot_key"]) for entry in entries if str(entry["spot_key"]) not in proved
    ]
    if missing:
        raise ReportFigureError(
            f"{len(missing)} indexed spot keys are outside the determinism proof, the first"
            f" being {missing[0]}; the block would read as covering the campaign"
        )
    for entry in entries:
        found = proved[str(entry["spot_key"])]
        if set(found.digests) != {str(entry["strategy_digest"])}:
            raise ReportFigureError(
                f"{found.spot_key} is proved against digests {found.digests} and the index"
                f" carries {entry['strategy_digest']}"
            )
        if set(found.iterations) != {int(entry["iterations"])}:
            raise ReportFigureError(
                f"{found.spot_key} is proved at {found.iterations} iterations and the index"
                f" carries {entry['iterations']}"
            )
    for found in record.cells:
        if not found.held:
            continue
        document = SAMPLE_DIR / f"{found.name}.json"
        if not document.is_file():
            raise ReportFigureError(
                f"the determinism proof calls {found.name} held and {document} does not exist"
            )
        on_disk = document.stat().st_size
        if found.document_bytes[0] != on_disk:
            raise ReportFigureError(
                f"{document.name} is {on_disk} bytes on disk and the determinism proof"
                f" compared {found.document_bytes[0]}"
            )
    return True


def check_the_two_runs_are_distinct(*, record: DeterminismRecord | None) -> bool:
    """Two runs that report the same wall clock are one run compared with itself.

    The file makes this claim in its own prose. Deciding it here rather than reading the
    sentence is the difference between a proof and a description of one.
    """
    if record is None:
        return True
    same = [cell.name for cell in record.cells if cell.wall_seconds[0] == cell.wall_seconds[1]]
    if same:
        raise ReportFigureError(
            f"{len(same)} cells report the same wall clock in both runs, the first being"
            f" {same[0]}; that is a copy of one run and would pass whatever the solver did"
        )
    return True


@dataclass(frozen=True)
class CommittedRange:
    """One of the two ranges the committed cells were actually solved against."""

    name: str
    describes: str
    weights: dict[str, float]

    @property
    def pairs(self) -> dict[str, float]:
        return {
            name: weight
            for name, weight in self.weights.items()
            if len(name) == 2 and name[0] == name[1] and name[0] in DECK_RANKS
        }

    @property
    def combos(self) -> int:
        return sum(_combos_of(name) for name in self.weights)

    @property
    def weighted_combos(self) -> float:
        return sum(_combos_of(name) * weight for name, weight in self.weights.items())

    @property
    def smallest_weight(self) -> float:
        return min(self.weights.values()) if self.weights else 0.0


def _combos_of(name: str) -> int:
    """How many two-card combinations one range class stands for, off the class name."""
    if len(name) == 2 and name[0] == name[1]:
        return 6
    return 4 if name.endswith("s") else 12


def committed_ranges() -> tuple[CommittedRange, ...]:
    """The two ranges in `solve_config.json`, which is what the committed cells were solved
    against.

    Not the ranges in the cost record's appendix. Those belong to August's campaign and hold
    pairs from TT to AA out of position that the committed range does not hold at all, so a
    reader checking the caller's strength against the printed block was checking it against a
    stronger range than any committed cell ever faced.
    """
    if not SOLVE_CONFIG_PATH.is_file():
        return ()
    payload = json.loads(SOLVE_CONFIG_PATH.read_text(encoding="utf-8"))
    source = payload.get("range_source") or {}
    describes = {
        "oop_bb_call": str(source.get("oop", "")),
        "ip_btn_open": str(source.get("ip", "")),
    }
    return tuple(
        CommittedRange(
            name=str(name),
            describes=describes.get(str(name), ""),
            weights={str(key): float(value) for key, value in weights.items()},
        )
        for name, weights in payload["ranges"].items()
    )


def range_export() -> str:
    """Where the committed ranges came from, in the config's own words."""
    if not SOLVE_CONFIG_PATH.is_file():
        return ""
    payload = json.loads(SOLVE_CONFIG_PATH.read_text(encoding="utf-8"))
    return str((payload.get("range_source") or {}).get("export", ""))


def check_every_committed_weight_clears_the_floor(*, ranges: Sequence[CommittedRange]) -> bool:
    """The committed ranges are stored after the floor ran, so nothing under it may survive.

    Which is also why the report cannot print a dropped list: a class the floor removed is not
    in the file to be named. Printing "dropped by the floor: none" off a post-floor file was a
    statement that could not have come out any other way.
    """
    for found in ranges:
        under = sorted(
            name for name, weight in found.weights.items() if weight < RANGE_WEIGHT_FLOOR
        )
        if under:
            raise ReportFigureError(
                f"{found.name} carries {len(under)} classes under the {RANGE_WEIGHT_FLOOR}"
                f" floor, the first being {under[0]}, so the committed range is not the"
                " floored one the cells were solved against"
            )
    return True


# --------------------------------------------------------------------------- #
# The deep solve, diffed against the shallow one
# --------------------------------------------------------------------------- #


def action_label(entry: Mapping[str, Any], pot_bb: float) -> str:
    """One menu entry as a reader recognises it: a name, and a size as a share of the pot."""
    name = str(entry["action"])
    size = entry.get("size_bb")
    if size is None:
        return name
    return f"{name} {round(100 * float(size) / pot_bb)}% of pot"


@dataclass(frozen=True)
class DeepCheck:
    """Decision 15's deep solve, and how far the committed strategy is from it."""

    cell: str
    board: str
    spot_key: str
    iterations: tuple[int, int]
    exploitability: tuple[float, float]
    labels: tuple[str, ...]
    committed_frequencies: tuple[float, ...]
    deep_frequencies: tuple[float, ...]
    moved: tuple[float, ...]
    shapes: tuple[str, ...]
    top_action_changed: tuple[str, ...]
    largest_in_class_divergence: float

    @property
    def classes(self) -> int:
        return len(self.moved)

    @property
    def unmoved(self) -> int:
        return sum(1 for value in self.moved if value == 0.0)

    def moving_past(self, threshold: float) -> int:
        return sum(1 for value in self.moved if value > threshold)

    @property
    def median_moved(self) -> float:
        """The nearest-rank median, which is a movement some class actually exhibits.

        `statistics.median` interpolates between the two middle values of an even-sized set and
        would publish 0.0535 where no hand class moved by 0.0535. The file this reads chose
        nearest rank for that reason and says so beside its own `quantile` helper; recomputing it
        here under the other convention would make the report and the artifact disagree about a
        figure neither of them needed to derive twice."""
        ordered = sorted(self.moved)
        return ordered[(len(ordered) + 1) // 2 - 1]

    def shape_mean(self, shape: str) -> tuple[int, float]:
        found = [
            value
            for value, kind in zip(self.moved, self.shapes, strict=True)
            if kind == shape
        ]
        return (len(found), statistics.fmean(found) if found else 0.0)


def deep_check() -> DeepCheck | None:
    """The committed deep convergence check, re-derived from its own per-class arrays.

    The file publishes both the summary and the arrays it was computed from, so the summary is
    recomputed here and the stored one is used as the thing to disagree with rather than as the
    thing to print.
    """
    if not DEEP_CHECK_PATH.is_file():
        return None
    payload = json.loads(DEEP_CHECK_PATH.read_text(encoding="utf-8"))
    pot = starting_pot_of(str(payload["spot_key"]))
    per_class = payload["per_class"]
    committed = [tuple(float(value) for value in row) for row in per_class["committed_weights"]]
    deep = [tuple(float(value) for value in row) for row in per_class["deep_weights"]]
    moved = tuple(
        max(abs(one - two) for one, two in zip(first, second, strict=True))
        for first, second in zip(committed, deep, strict=True)
    )
    changed = tuple(
        str(name)
        for name, first, second in zip(per_class["hand_classes"], committed, deep, strict=True)
        if first.index(max(first)) != second.index(max(second))
    )
    reach = [float(value) for value in per_class["reach_share"]]
    total = sum(reach)
    actions = len(payload["actions"])
    return DeepCheck(
        cell=str(payload["cell"]),
        board="".join(payload["board"]),
        spot_key=str(payload["spot_key"]),
        iterations=(
            int(payload["committed_run"]["iterations"]), int(payload["deep_run"]["iterations"])
        ),
        exploitability=(
            float(payload["committed_run"]["achieved_exploitability_pct_of_pot"]),
            float(payload["deep_run"]["achieved_exploitability_pct_of_pot"]),
        ),
        labels=tuple(action_label(entry, pot) for entry in payload["actions"]),
        committed_frequencies=tuple(
            sum(weight * row[index] for weight, row in zip(reach, committed, strict=True)) / total
            for index in range(actions)
        ),
        deep_frequencies=tuple(
            sum(weight * row[index] for weight, row in zip(reach, deep, strict=True)) / total
            for index in range(actions)
        ),
        moved=moved,
        shapes=tuple(str(value) for value in per_class["committed_shape"]),
        top_action_changed=changed,
        largest_in_class_divergence=float(payload["deep_run"]["largest_in_class_divergence"]),
    )


def check_the_deep_check_reconciles(*, check: DeepCheck | None) -> bool:
    """The summary this report prints is recomputed, and agrees with the one the file stores.

    Two independent recomputations against two stored summaries. The per-class movement comes
    out of the two weight arrays and is compared against the stored `moved`; the aggregate
    frequencies come out of the same arrays weighted by reach and are compared against the
    stored `aggregate_frequencies`. Either could disagree, which is what makes this a check
    rather than a restatement: the arrays and the summaries were written by separate code.
    """
    if check is None:
        return True
    payload = json.loads(DEEP_CHECK_PATH.read_text(encoding="utf-8"))
    stored = [float(value) for value in payload["per_class"]["moved"]]
    if len(stored) != check.classes:
        raise ReportFigureError(
            f"the deep check stores {len(stored)} movements over {check.classes} classes"
        )
    worst = max(abs(one - two) for one, two in zip(stored, check.moved, strict=True))
    if worst > 5e-4:
        raise ReportFigureError(
            f"the deep check's stored movement disagrees with the movement its own weight"
            f" arrays give by {worst}, so one of the two describes a different pair of solves"
        )
    for index, entry in enumerate(payload["aggregate_frequencies"]):
        for stored_value, ours in (
            (float(entry["committed_frequency"]), check.committed_frequencies[index]),
            (float(entry["deep_frequency"]), check.deep_frequencies[index]),
        ):
            if abs(stored_value - ours) > 5e-4:
                raise ReportFigureError(
                    f"the deep check publishes {stored_value} for {entry['action']} and its own"
                    f" per-class rows weighted by reach give {ours:.4f}"
                )
    return True


# --------------------------------------------------------------------------- #
# What the caller did before hero's turn came round
# --------------------------------------------------------------------------- #

IN_POSITION = "BTN"
"""The seat that acts last on the flop in the one pot type this artifact covers. Heads up on a
flop the button is in position by definition, so which committed range a cell's hero was solved
with follows from `hero_position` rather than from a table anybody keeps in step by hand."""

COMBO_SUITEDNESS = ("s", "o")


def range_for(position: str, ranges: Sequence[CommittedRange]) -> CommittedRange:
    """The committed range one seat was solved with, off the config's own names."""
    prefix = "ip_" if position == IN_POSITION else "oop_"
    found = [entry for entry in ranges if entry.name.startswith(prefix)]
    if len(found) != 1:
        raise ReportFigureError(
            f"{len(found)} committed ranges are named {prefix}*, so which one {position} was"
            " solved with is a guess rather than a reading"
        )
    return found[0]


def range_class_of(first: str, second: str) -> str:
    """The range class two dealt cards belong to: `AA`, `AKs` or `AKo`."""
    high, low = sorted((first, second), key=lambda card: DECK_RANKS.index(card[0]), reverse=True)
    if high[0] == low[0]:
        return high[0] + low[0]
    return high[0] + low[0] + (COMBO_SUITEDNESS[0] if high[1] == low[1] else COMBO_SUITEDNESS[1])


def dealt_combos(board: Sequence[str], found: CommittedRange) -> dict[tuple[str, str], float]:
    """Every two-card combination the board leaves in one committed range, with its weight."""
    blocked = set(board)
    deck = [rank + suit for rank in DECK_RANKS for suit in DECK_SUITS if rank + suit not in blocked]
    held: dict[tuple[str, str], float] = {}
    for first, second in combinations(deck, 2):
        weight = found.weights.get(range_class_of(first, second))
        if weight:
            held[(first, second)] = weight
    if not held:
        raise ReportFigureError(
            f"the {found.name} range leaves no combination on {''.join(board)}, so every share"
            " below would divide by zero"
        )
    return held


@dataclass(frozen=True)
class CellFrequencies:
    """One committed cell's action frequencies, under both weightings, so the choice shows."""

    name: str
    board: str
    flop_line: str
    seat: str
    labels: tuple[str, ...]
    classes: int
    class_mean: tuple[float, ...]
    range_weighted: tuple[float, ...]
    weighted_combos: float

    @property
    def acts(self) -> float:
        """How often this seat does anything other than check, range-weighted."""
        return 1.0 - self.range_weighted[0]

    @property
    def acts_by_class_mean(self) -> float:
        return 1.0 - self.class_mean[0]


def cell_frequencies(
    cell: PostflopCell, name: str, ranges: Sequence[CommittedRange]
) -> CellFrequencies:
    """A committed cell's frequencies, weighted two ways over its own class rows.

    **Range-weighted is the one to read** and is what every share in this section is: each
    two-card combination the board leaves is weighted by the seat's own committed weight for it,
    mapped to the class label the cell holds, and averaged. That is the frequency the other seat
    faces at the table, and it reproduces the artifact's own aggregate row.

    The **class mean** - every class row counted once - is printed beside it because the two are
    not the same number and a reader who is not told which is which cannot tell. They differ by
    seven points on the paired board, where one class stands for six dealt combinations and
    another for two.
    """
    rows = dict(zip(cell.hand_classes, cell.class_weights, strict=True))
    actions = len(cell.actions)
    found = range_for(cell.hero_position, ranges)
    weighted = [0.0] * actions
    total = 0.0
    for combo, weight in dealt_combos(cell.board, found).items():
        label = "".join(canonical_hole_cards(cell.board, combo))
        row = rows.get(label)
        if row is None:
            raise ReportFigureError(
                f"{cell.spot_key} holds no row for {label}, which {''.join(combo)} on"
                f" {''.join(cell.board)} collapses to, so a share over its range cannot be taken"
            )
        total += weight
        for index in range(actions):
            weighted[index] += weight * row[index]
    return CellFrequencies(
        name=name,
        board="".join(cell.board),
        flop_line=flop_line_of(cell.spot_key),
        seat=cell.hero_position,
        labels=tuple(
            action_label({"action": entry.name, "size_bb": entry.size_bb}, cell.pot_before_hero_bb)
            for entry in cell.actions
        ),
        classes=len(cell.hand_classes),
        class_mean=tuple(
            statistics.fmean(row[index] for row in cell.class_weights) for index in range(actions)
        ),
        range_weighted=tuple(value / total for value in weighted),
        weighted_combos=total,
    )


def check_frequencies_are_a_distribution(*, found: Sequence[CellFrequencies]) -> bool:
    """Every printed frequency block sums to one under both weightings.

    A share that does not sum to one is a share taken over a population the rows do not cover -
    a class the board leaves that the cell does not hold, or a row weighted twice - and it is
    the one arithmetic mistake that makes a bet frequency read low without looking wrong.
    """
    for entry in found:
        both = (("class mean", entry.class_mean), ("range-weighted", entry.range_weighted))
        for name, row in both:
            if abs(sum(row) - 1.0) > 1e-6:
                raise ReportFigureError(
                    f"{entry.name}'s {name} frequencies sum to {sum(row)} rather than to one,"
                    " so they are shares of something other than its range"
                )
    return True


@dataclass(frozen=True)
class CategoryShare:
    """One hand category on one board, before the seat acts and in what survives its action."""

    label: str
    combos_before: float
    combos_after: float
    share_before: float
    share_after: float
    otherwise: float
    """How often this category did something else and hero's node was never reached."""


@dataclass(frozen=True)
class OpponentLead:
    """What the other seat did before hero's turn came round, and with which hands.

    Recovered from the solved node object rather than from a committed cell, because the node
    where the other seat decides is not one of the five the campaign harvested. A player's
    `reach` at a node is the product of its own action probabilities down the path, so `reach`
    over that hand's preflop weight is the probability it played the line that leads here, and
    one less that is the probability it did something else and hero's node was never reached.
    """

    board: str
    seat: str
    line: str
    source: str
    digest: str
    weighted_combos: float
    takes_the_line: float
    categories: tuple[CategoryShare, ...]

    @property
    def otherwise(self) -> float:
        return 1.0 - self.takes_the_line


def object_for(spot_key: str) -> tuple[Mapping[str, Any], Path, str] | None:
    """The solved node object one committed spot key names, verified against its own digest.

    The objects live outside git - `objects.json` says so in its own words - so this answers
    `None` on a machine that does not hold them rather than inventing a figure. What it will not
    do is read one whose bytes have moved: an object that no longer hashes to the digest the
    index commits is a different solve, and a frequency out of it would be published under this
    campaign's name.
    """
    if not OBJECTS_PATH.is_file():
        return None
    manifest = json.loads(OBJECTS_PATH.read_text(encoding="utf-8"))
    entry = manifest.get("objects", {}).get(spot_key)
    if entry is None:
        return None
    path = Path(str(entry["object_path"]))
    if not path.is_file():
        return None
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != str(entry["object_digest"]):
        raise ReportFigureError(
            f"{path} hashes to {digest} and the committed index names"
            f" {entry['object_digest']}; that is a different solve under this campaign's name"
        )
    return (json.loads(gzip.open(path).read()), path, digest)


def sample_name_of(spot_key: str) -> str | None:
    """Which committed sample file holds one spot key, and so what the solved node is called."""
    for path in sorted(SAMPLE_DIR.glob("*.json")):
        if str(json.loads(path.read_text(encoding="utf-8"))["spot_key"]) == spot_key:
            return path.stem
    return None


def opponent_flop_line(cell: PostflopCell) -> str:
    """The other seat's own flop actions on the way to hero's node, in a reader's words."""
    theirs = [entry for entry in cell.flop_actions if entry.position != cell.hero_position]
    if not theirs:
        return ""
    return ", ".join(
        entry.action
        if entry.size_pct is None
        else f"{entry.action} {round(float(entry.size_pct))}% of pot"
        for entry in theirs
    )


def opponent_lead(cell: PostflopCell, ranges: Sequence[CommittedRange]) -> OpponentLead | None:
    """What the other seat did before hero's turn came round on this board.

    Answers `None` where there is nothing to measure - a cell hero decides first on, whose other
    seat has taken no flop action - and where the solved object this machine would read it out
    of is not held.
    """
    line = opponent_flop_line(cell)
    if not line:
        return None
    found = object_for(cell.spot_key)
    name = sample_name_of(cell.spot_key)
    if found is None or name is None:
        return None
    payload, path, digest = found
    node = payload["nodes"][name]
    seat = int(node["player"])
    hands = node["players"][1 - seat]["hands"]
    other = IN_POSITION if cell.hero_position != IN_POSITION else "BB"
    committed = range_for(other, ranges)
    before: Counter[str] = Counter()
    after: Counter[str] = Counter()
    for hand in hands:
        combo = str(hand["combo"])
        cards = (combo[:2], combo[2:])
        weight = float(hand["weight"])
        expected = committed.weights.get(range_class_of(*cards))
        if expected is None or abs(expected - weight) > 1e-9:
            raise ReportFigureError(
                f"{combo} carries weight {weight} in the solved object and {expected} in the"
                f" committed {committed.name} range, so the object is not this campaign's"
            )
        label = evaluate_best(parse_cards(list(cell.board) + list(cards))).label
        before[label] += weight
        after[label] += float(hand["reach"])
    total_before = sum(before.values())
    total_after = sum(after.values())
    if total_before <= 0:
        raise ReportFigureError(f"{cell.spot_key}: the other seat arrives with no range at all")
    categories = tuple(
        CategoryShare(
            label=label,
            combos_before=before[label],
            combos_after=after[label],
            share_before=before[label] / total_before,
            share_after=after[label] / total_after if total_after else 0.0,
            otherwise=1.0 - after[label] / before[label],
        )
        for label in sorted(before, key=lambda name: -before[name])
    )
    return OpponentLead(
        board="".join(cell.board),
        seat=other,
        line=line,
        source=path.name,
        digest=digest,
        weighted_combos=total_before,
        takes_the_line=total_after / total_before,
        categories=categories,
    )


# --------------------------------------------------------------------------- #
# The corpus: what a real table asks for
# --------------------------------------------------------------------------- #


CAUSE_MULTIWAY = "multiway, structural"
CAUSE_PRICE = "preflop price outside the band"
CAUSE_LINE = "no cell for this preflop line"
CAUSE_BOARD = "no cell for this board"
CAUSE_NOT_FETCHED = "in the index and not fetched on this machine"

LOSS_CAUSES = (CAUSE_MULTIWAY, CAUSE_PRICE, CAUSE_LINE, CAUSE_BOARD, CAUSE_NOT_FETCHED)
"""Every reason a corpus flop goes unanswered, one cause to a label.

The last two were one row until stage 8. A flop whose canonical class the index does not list at
all and a flop whose class the index lists but this clone has not fetched are different questions
with different answers - the first is bought with a bigger campaign, the second with a fetch - and
this block is the only place in the report that puts a number on either. Counting them under one
label left the report asserting in its refusal section that it never pools the two table causes
while the single row that counted them did exactly that.

Declared here as the closed vocabulary so that a cause whose count is zero still prints. A
`Counter` drops a key it never saw, so the honest split would have vanished the moment the
unfetched cause measured nothing, which is the pooling defect returning by the other door.
"""


@dataclass
class CorpusMeasurement:
    """What the committed corpus says about the spots this artifact would be asked for."""

    hands: int = 0
    flops: int = 0
    causes: Counter[str] = field(default_factory=Counter)
    answerable: int = 0
    arrivals: Counter[str] = field(default_factory=Counter)
    """Corpus arrivals on each substituted preflop line, answerable or not."""
    servable: Counter[str] = field(default_factory=Counter)
    """The arrivals the artifact could have answered: the line is covered and the flop's
    canonical board was fetched. Sums across every line to `answerable`."""
    opens: list[float] = field(default_factory=list)
    three_bets: list[float] = field(default_factory=list)


def chart_prices() -> tuple[float, ...]:
    """Every preflop price the committed chart declares, off its own keys."""
    payload = json.loads(PREFLOP_CHART.read_text(encoding="utf-8"))
    found = {
        float(size)
        for key in payload["arrival_ppb"]
        for size in re.findall(r"@([0-9.]+)", key)
    }
    if not found:
        raise ReportFigureError(f"{PREFLOP_CHART} declares no preflop price to substitute onto")
    return tuple(sorted(found))


def arrival_probabilities() -> dict[str, int]:
    payload = json.loads(PREFLOP_CHART.read_text(encoding="utf-8"))
    return {str(key): int(value) for key, value in payload["arrival_ppb"].items()}


def measure_corpus(
    covered_lines: frozenset[str],
    fetched_boards: frozenset[tuple[str, ...]],
    indexed_boards: frozenset[tuple[str, ...]],
):
    """Walk every committed corpus hand that saw a flop, and name the first thing in its way.

    Coarsest gap first, the way the strategy's own walk fails closed, so the causes partition
    the flops rather than overlapping: a three-handed flop is counted as structural and is not
    also counted as an uncovered line.

    `indexed_boards` is what separates the last two causes. A flop the index lists is one the
    campaign already paid for and this clone has not fetched; a flop it does not list was never
    solved. Both leave the artifact silent and they are not the same gap, so they are counted
    apart rather than added together under a label that names both.
    """
    prices = chart_prices()
    measured = CorpusMeasurement()
    measured.causes.update({cause: 0 for cause in LOSS_CAUSES})
    for record in load_committed_sample().records:
        history = record.normalized
        measured.hands += 1
        preflop = history.streets[0]
        big_blind = history.blinds.big_blind
        raises = [
            action.amount / big_blind
            for action in preflop.actions
            if action.kind in (HistoryActionKind.RAISE, HistoryActionKind.BET)
        ]
        if raises:
            measured.opens.append(raises[0])
        if len(raises) > 1:
            measured.three_bets.append(raises[1])
        if len(history.streets) < 2:
            continue
        measured.flops += 1
        folded = {
            action.seat for action in preflop.actions if action.kind is HistoryActionKind.FOLD
        }
        live = [seat for seat in range(history.max_seats) if seat not in folded]
        if len(live) != 2:
            measured.causes[CAUSE_MULTIWAY] += 1
            continue
        labels = seat_positions(tuple(range(history.max_seats)), history.button_seat)
        entries = _substituted_line(preflop.actions, labels, big_blind, prices)
        if entries is None:
            measured.causes[CAUSE_PRICE] += 1
            continue
        line = ",".join(render_entry(entry) for entry in entries)
        measured.arrivals[line] += 1
        if line not in covered_lines:
            measured.causes[CAUSE_LINE] += 1
            continue
        flop = tuple(f"{card.rank}{card.suit}" for card in history.streets[1].board)
        board_class = canonical_board(flop)
        if board_class not in fetched_boards:
            listed = board_class in indexed_boards
            measured.causes[CAUSE_NOT_FETCHED if listed else CAUSE_BOARD] += 1
            continue
        measured.servable[line] += 1
        measured.answerable += 1
    return measured


def _substituted_line(actions, labels, big_blind: int, prices: tuple[float, ...]):
    """The preflop street as the committed keys render it, with each price substituted onto the
    chart price whose band it falls in. A price in no band has no key and is not guessed at."""
    entries: list[PreflopAction] = []
    for action in actions:
        if action.kind in (HistoryActionKind.FOLD, HistoryActionKind.POST_BLIND):
            continue
        if action.kind is HistoryActionKind.CHECK:
            continue
        if action.kind is HistoryActionKind.CALL:
            entries.append(PreflopAction(labels[action.seat], "call"))
            continue
        if action.kind not in (HistoryActionKind.RAISE, HistoryActionKind.BET):
            return None
        actual = action.amount / big_blind
        inside = [price for price in prices if price_within_band(price, actual)]
        if not inside:
            return None
        entries.append(PreflopAction(labels[action.seat], "raise", size_bb=inside[0]))
    return entries or None


def arrival_key_for(line: str) -> str:
    """The preflop spot key of the decision that closed this line.

    A completed line names a flop; a preflop spot key names a decision about to be made. The
    decision that closed the street is the last entry, so the chart's arrival figure for this
    line is the one it publishes for that seat facing everything in front of it.
    """
    entries = line.split(",")
    position = entries[-1].split(":")[0]
    return f"t6/d100/{position}/" + ",".join(entries[:-1])


# --------------------------------------------------------------------------- #
# The committed artifact, and what the strategy does with it
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Behaviour:
    """What the strategy did when it was asked about every spot this machine holds."""

    asked: int
    decisions: Counter[str]
    refusals: Counter[str]
    pot_odds_asked: int
    pot_odds_fired: int


def measure_behaviour(strategy: PostflopBettingStrategy) -> Behaviour:
    decisions: Counter[str] = Counter()
    refusals: Counter[str] = Counter()
    asked = 0
    for query in committed_spot_queries():
        asked += 1
        answer = strategy.decide(query)
        if isinstance(answer, StrategyDecision):
            decisions[answer.action] += 1
        elif isinstance(answer, StrategyRefusal):
            refusals[answer.code] += 1
    return Behaviour(asked, decisions, refusals, *_pot_odds_rate())


def _pot_odds_rate() -> tuple[int, int]:
    """How often decision 5's river rule fires, over the repo's own river enumeration.

    The population is `generate_postflop_fallback_report`'s engine shapes rather than a set
    invented here, so the rate is over river spots this repo already describes. The flag is off
    at the table; this measures the rule, which is what the ruling asked to be reported.
    """
    try:
        import generate_postflop_fallback_report as fallback_report
    except ImportError:  # pragma: no cover - the sibling report is committed
        return (0, 0)
    firing = PostflopBettingStrategy(library=load_library(), pot_odds_river_call=True)
    asked = 0
    fired = 0
    for query in fallback_report.enumeration_queries(fallback_report.engine_shapes()):
        if query.street != "river" or query.to_call <= 0:
            continue
        asked += 1
        answer = firing.decide(query)
        if isinstance(answer, StrategyDecision):
            fired += 1
    return (asked, fired)


def unreachable_fallback_codes(strategy: PostflopBettingStrategy) -> tuple[str, ...]:
    """Which of the conservative fallback's codes this phase's flop answer takes over.

    The composite reaches the fallback only where the betting strategy refuses, and the betting
    strategy answers exactly the committed flop spots, so a fallback code that only ever fired
    on a flop is unreachable for those spots and for no others.
    """
    taken = tuple(
        sorted(
            {
                value
                for name, value in vars(postflop_fallback).items()
                if name.startswith("CODE_") and "FLOP" in name and isinstance(value, str)
            }
        )
    )
    if not taken and strategy.library.cells:
        raise ReportFigureError(
            "the fallback publishes no flop refusal code, so nothing this phase replaced can be"
            " named, and the report would have to claim a takeover it cannot show"
        )
    return taken


def artifact_bytes() -> int:
    return sum(path.stat().st_size for path in ARTIFACT_ROOT.rglob("*") if path.is_file())


def postflop_bytes() -> int:
    if not POSTFLOP_DIR.is_dir():
        return 0
    return sum(path.stat().st_size for path in POSTFLOP_DIR.rglob("*") if path.is_file())


def index_and_sample_bytes() -> tuple[int, int]:
    """The bytes the contract's byte budget is drawn around, and what else the tree holds.

    The budget is the index plus the committed sample, cut out of the postflop tree rather than
    measured as the tree. The tree also holds the deep-convergence record, the determinism
    record, the solve config and the objects manifest, which are evidence about the campaign that
    ran and are neither the index nor the sample.

    Returns the count and how many tree files were left out of it, because that second number is
    the only thing carrying the numerator's provenance downstream:
    `check_per_spot_cost_excludes_non_sample_bytes` cannot see a file list, and a rate handed a
    numerator it cannot place is a rate that will accept the tree total again.
    """
    if not POSTFLOP_DIR.is_dir():
        return (0, 0)
    inside = [INDEX_PATH] if INDEX_PATH.is_file() else []
    if SAMPLE_DIR.is_dir():
        inside += [path for path in sorted(SAMPLE_DIR.rglob("*")) if path.is_file()]
    held = set(inside)
    outside = [
        path for path in POSTFLOP_DIR.rglob("*") if path.is_file() and path not in held
    ]
    return (sum(path.stat().st_size for path in inside), len(outside))


def weight_bytes_and_count() -> tuple[int, int]:
    """The bytes hero's class weights occupy, and how many weights there are.

    Counted off the committed JSON's own weight block rather than off the whole file, because a
    whole-file rate charges the per-spot provenance fields against every weight and those scale
    per spot rather than per weight.

    The numerator is checked against the sample's bytes on disk here, where it is produced.
    `check_rate_excludes_non_weight_bytes` can only re-derive the division it is handed, so
    nothing downstream can tell a weight block from the file it was cut out of.
    """
    total_bytes = 0
    total_weights = 0
    file_bytes = 0
    files = sorted(SAMPLE_DIR.glob("*.json")) if SAMPLE_DIR.is_dir() else []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("class_weights") or []
        total_bytes += len(json.dumps(rows, separators=(",", ":")).encode("utf-8"))
        total_weights += sum(len(row) for row in rows)
        file_bytes += path.stat().st_size
    if files and total_bytes >= file_bytes:
        raise ReportFigureError(
            f"the committed sample's weight blocks measure {total_bytes} bytes against"
            f" {file_bytes} bytes of sample file on disk; a numerator at least as large as the"
            " files it was cut out of is the whole file charged against every weight"
        )
    return (total_bytes, total_weights)


# --------------------------------------------------------------------------- #
# Measurement
# --------------------------------------------------------------------------- #


@dataclass
class Measured:
    census: dict[str, TextureCensus]
    costs: dict[str, TextureCost]
    determinism: DeterminismRecord | None
    ranges: tuple[CommittedRange, ...]
    range_export: str
    deep: DeepCheck | None
    frequencies: tuple[CellFrequencies, ...]
    leads: tuple[OpponentLead, ...]
    index: dict[str, Any] | None
    cells: tuple[PostflopCell, ...]
    printed_spot_count: int
    indexed_total: int
    corpus: CorpusMeasurement
    arrivals: dict[str, int]
    behaviour: Behaviour
    unreachable: tuple[str, ...]
    artifact_bytes: int
    postflop_bytes: int
    index_and_sample_bytes: int
    per_spot_bytes: float | None
    solve_digests: dict[str, str]
    """Each committed spot key against the digest of the solved object it was read out of.

    Two spots sharing a digest are two nodes of one solve, which is what the accuracy table has to
    say rather than print one measurement on two rows as though it were two.
    """
    weight_bytes: int
    weight_count: int
    rate_per_weight: float
    covered_lines: tuple[str, ...]
    line_bound_by: str
    rejected_above_ceiling: int | None


def measure() -> Measured:
    """Everything the report prints, taken before a single line is rendered."""
    census = flop_class_census()
    costs = texture_costs(census)
    library = load_library()
    cells = library.cells

    index: dict[str, Any] | None = None
    indexed: frozenset[str] = frozenset()
    if INDEX_PATH.is_file():
        index = import_postflop_index(INDEX_PATH)
        indexed = indexed_spot_keys(index)

    printed_spot_count = len(cells)
    in_index = len([cell for cell in cells if cell.spot_key in indexed])
    check_spot_count_matches_index(printed=printed_spot_count, in_index=in_index)

    covered = tuple(index["covered_preflop_lines"]) if index else ()
    bound_by = str(index["line_count_bound_by"]) if index else ""
    rejected = (
        int(index["cells_solved_and_rejected_above_one_percent"]) if index else None
    )

    covered_set = frozenset(cell.preflop_line.rendered.split("/", 3)[3] for cell in cells)
    fetched_boards = frozenset(canonical_board(cell.board) for cell in cells)
    indexed_boards = (
        frozenset(canonical_board(tuple(entry["board"])) for entry in index["entries"])
        if index
        else fetched_boards
    )
    corpus = measure_corpus(covered_set, fetched_boards, indexed_boards)

    strategy = PostflopBettingStrategy(library=library)
    behaviour = measure_behaviour(strategy)
    # The total comes from the loop's own counter less the decisions, never from summing the
    # breakdown being checked: `sum(x) == sum(x)` is a check that cannot fail, and an answer that
    # is neither a decision nor a refusal would be dropped by a breakdown nobody could catch.
    check_refusal_counts_reconcile(
        total=behaviour.asked - sum(behaviour.decisions.values()), by_code=behaviour.refusals
    )

    on_disk = artifact_bytes()
    committed_on_disk = postflop_bytes()
    if index is not None:
        check_bytes_reconcile(
            declared=float(index["committed_bytes"]), on_disk=float(committed_on_disk)
        )
    budget_on_disk, tree_files_outside = index_and_sample_bytes()
    per_spot = budget_on_disk / printed_spot_count if printed_spot_count else None
    check_per_spot_cost_excludes_non_sample_bytes(
        cost_bytes_per_spot=per_spot if per_spot is not None else 0.0,
        index_and_sample_bytes=budget_on_disk,
        tree_bytes=committed_on_disk,
        tree_files_outside=tree_files_outside,
        spots=printed_spot_count,
    )
    weight_bytes, weight_count = weight_bytes_and_count()
    rate = 0.0 if weight_count == 0 else weight_bytes / weight_count
    check_rate_excludes_non_weight_bytes(
        rate_bytes_per_weight=rate, weight_bytes=weight_bytes, weight_count=weight_count
    )

    losses = {
        name: count / corpus.flops for name, count in corpus.causes.items()
    } if corpus.flops else {}
    check_coverage_splits_by_cause(
        answerable=(corpus.answerable / corpus.flops) if corpus.flops else 1.0,
        losses=losses,
        required=LOSS_CAUSES if corpus.flops else (),
    )
    check_servable_never_exceeds_arrivals(
        arrivals=corpus.arrivals, servable=corpus.servable, answerable=corpus.answerable
    )

    determinism = determinism_record()
    check_determinism_covers_what_is_committed(record=determinism, index=index)
    check_the_two_runs_are_distinct(record=determinism)

    ranges = committed_ranges()
    check_every_committed_weight_clears_the_floor(ranges=ranges)

    deep = deep_check()
    check_the_deep_check_reconciles(check=deep)

    named = {cell.spot_key: sample_name_of(cell.spot_key) or cell.spot_key for cell in cells}
    frequencies = tuple(
        cell_frequencies(cell, named[cell.spot_key], ranges)
        for cell in sorted(cells, key=lambda cell: cell.spot_key)
    ) if ranges else ()
    check_frequencies_are_a_distribution(found=frequencies)
    leads = tuple(
        found
        for cell in sorted(cells, key=lambda cell: cell.spot_key)
        if (found := opponent_lead(cell, ranges)) is not None
    ) if ranges else ()

    return Measured(
        census=census,
        costs=costs,
        determinism=determinism,
        ranges=ranges,
        range_export=range_export(),
        deep=deep,
        frequencies=frequencies,
        leads=leads,
        index=index,
        cells=cells,
        printed_spot_count=printed_spot_count,
        indexed_total=len(indexed),
        corpus=corpus,
        arrivals=arrival_probabilities(),
        behaviour=behaviour,
        unreachable=unreachable_fallback_codes(strategy),
        artifact_bytes=on_disk,
        postflop_bytes=committed_on_disk,
        index_and_sample_bytes=budget_on_disk,
        per_spot_bytes=per_spot,
        solve_digests={
            str(entry["spot_key"]): str(entry["object_digest"])
            for entry in (index["entries"] if index else ())
        },
        weight_bytes=weight_bytes,
        weight_count=weight_count,
        rate_per_weight=rate,
        covered_lines=covered,
        line_bound_by=bound_by,
        rejected_above_ceiling=rejected,
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def heading(title: str) -> list[str]:
    return ["", title, "-" * len(title)]


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def header_lines() -> list[str]:
    return [
        "Postflop Betting Report",
        "=======================",
        "",
        "What the repo commits is an index plus a committed sample of three flops, and the solve",
        "the bot plays lives in object storage outside git. A later phase measuring the committed",
        "chart has to say which of the two it means, so this report says it here first.",
        "",
        "Every figure below is re-derived when this report is generated, out of a committed file",
        "or out of the deck itself, and the command exits non-zero and writes nothing when one",
        "does not reconcile. Sources, once: the class census is brute-forced over all",
        f"{ALL_BOARDS:,} three-card boards; the cost model comes from",
        "reports/active/latest_postflop_solve_cost.txt, which is a separate campaign measured in",
        "August; everything about the cells this repo commits - their accuracy, the two runs that",
        "prove them, the ranges they were solved against and the deep solve one of them was",
        "diffed against - comes from data/artifacts/postflop/, out of index.json,",
        "solve_config.json, determinism.json and deep_convergence_check.json by those names;",
        "the corpus figures are counted off data/samples/public_corpus; the behaviour figures",
        "come from asking the strategy about the spots this machine holds; and the one block",
        "that needs what the other seat did first reads the solved node objects, each verified",
        "against the digest the index commits for it.",
        "",
        "Four qualifications, stated as qualifications rather than as caveats. Convergence at the",
        "committed iteration count is unproven. The published exploitability binds only against",
        "an opponent confined to the same bet menu. Rainbow, and three rank patterns with it,",
        "were never solved to target. And the repo holds an index plus a sample rather than the",
        "artifact the bot plays.",
    ]


def servable_ranking(corpus: CorpusMeasurement) -> list[str]:
    """Every arrived line, servable count first, arrivals then the key itself as tie-breaks.

    One ordering for both blocks below, so the cross-check ranks what the table above ranked.
    The tie-breaks are what stop a Counter's insertion order deciding the display when many
    lines carry the same servable count - which is every line while nothing is servable.
    """
    return sorted(
        corpus.arrivals,
        key=lambda line: (-corpus.servable[line], -corpus.arrivals[line], line),
    )


def ranking_basis_lines(corpus: CorpusMeasurement) -> list[str]:
    """What the ranking below is sorted on, said in the report rather than assumed by it."""
    if sum(corpus.servable.values()):
        return [
            "The ranking below sorts on servable arrival frequency rather than on arrival",
            "frequency. A line the artifact can only answer some of the time is worth less than",
            "one it can answer almost always, and the two orders are not the same order.",
        ]
    return [
        "The ranking below sorts on servable arrival frequency - how often the artifact could",
        "have answered a line it was reached on - and no committed cell answers any corpus",
        "arrival yet, so every servable count is zero and there is no servable order to read.",
        "What is printed is the arrival order, which is the column beside it; the two orders",
        "differ only once something is servable.",
    ]


def coverage_lines(measured: Measured) -> list[str]:
    corpus = measured.corpus
    lines = heading("Covered preflop lines, and the corpus rank of each")
    lines += [
        "",
        "How many lines are covered is an output rather than a choice: as many as the campaign",
        "cost and the index each afford, whichever is smaller. The committed index names which",
        "of the two decided it.",
        "",
        f"  covered preflop lines committed: {len(measured.covered_lines)}",
        f"  bound by: {measured.line_bound_by or 'campaign cost or index bytes, whichever is smaller - no index is committed yet'}",  # noqa: E501
    ]
    for line in measured.covered_lines:
        lines.append(f"    {line}")
    lines += [
        "",
        *ranking_basis_lines(corpus),
        "",
        f"  corpus hands: {corpus.hands}",
        f"  flop-reaching hands: {corpus.flops}",
        "",
        "  arrivals  servable  substituted preflop line",
    ]
    for line in servable_ranking(corpus)[:12]:
        lines.append(f"  {corpus.arrivals[line]:8d}  {corpus.servable[line]:8d}  {line}")
    lines += [
        "",
        "The keys above are post-substitution. Every price is moved onto the chart price whose",
        f"band it falls in - {int(100 * PRICE_BAND_FRACTION)}% either side of it, inclusive at both"
        " ends - so a line opened to the",
        "corpus median of 2.25bb reads @2.5 here. A reader taking the ranking at face value is",
        "reading substituted keys rather than played ones.",
    ]
    if corpus.opens:
        inside = sum(
            1 for value in corpus.opens if any(price_within_band(p, value) for p in chart_prices())
        )
        lines.append(
            f"  opens: {len(corpus.opens)}, median {statistics.median(corpus.opens):.2f}bb,"
            f" {inside} inside a declared band"
        )
    if corpus.three_bets:
        inside = sum(
            1
            for value in corpus.three_bets
            if any(price_within_band(p, value) for p in chart_prices())
        )
        lines.append(
            f"  3-bets: {len(corpus.three_bets)},"
            f" median {statistics.median(corpus.three_bets):.2f}bb,"
            f" {inside} inside a declared band"
        )
    return lines


def cross_check_lines(measured: Measured) -> list[str]:
    corpus = measured.corpus
    basis = (
        "The corpus order is the servable count above."
        if sum(corpus.servable.values())
        else "The corpus order is the arrival count above, no line being servable yet."
    )
    lines = heading("The corpus order against the artifact's own arrival_ppb order")
    lines += [
        "",
        "Two orders over the same lines, and nothing in the repo had compared them.",
        basis,
        "The arrival_ppb order is the committed chart's own figure for the decision that closed",
        "each line. Where they disagree, the rank a reader would take off one document is not",
        "the rank the other gives.",
        "",
        "  corpus  arrival_ppb  line",
    ]
    ranked = servable_ranking(corpus)[:10]
    scored = []
    for line in ranked:
        key = arrival_key_for(line)
        scored.append((line, measured.arrivals.get(key)))
    by_arrival = sorted(
        [entry for entry in scored if entry[1] is not None],
        key=lambda entry: entry[1],
        reverse=True,
    )
    arrival_rank = {line: index + 1 for index, (line, _) in enumerate(by_arrival)}
    disagreements = 0
    for index, (line, value) in enumerate(scored):
        rank = arrival_rank.get(line)
        shown = "not in the chart" if value is None else f"{rank}"
        if rank is not None and rank != index + 1:
            disagreements += 1
            shown = f"{rank} <- disagrees"
        lines.append(f"  {index + 1:6d}  {shown:>11}  {line}")
    lines += [
        "",
        f"  positions where the two orders disagree: {disagreements}",
    ]
    return lines


def answerable_lines(measured: Measured) -> list[str]:
    corpus = measured.corpus
    lines = heading("The share of corpus flops this artifact can answer, split by cause")
    lines += [
        "",
        "Reaching a decision point is not seeing a flop, and the flop-reaching filter is a",
        "different query from the arrival one above. This block is over flops only.",
        "",
    ]
    total = corpus.flops or 1
    lines.append(f"  flop-reaching hands: {corpus.flops}")
    lines.append(f"  answerable: {corpus.answerable} ({pct(corpus.answerable / total)})")
    for cause in LOSS_CAUSES:
        count = corpus.causes.get(cause, 0)
        lines.append(f"  lost to {cause}: {count} ({pct(count / total)})")
    lines += [
        "",
        "The multiway share is structural rather than fundable. A two-range solve cannot express",
        "a three-handed flop at any budget, on any machine, under any menu, so no campaign closes",
        "that share and a report that pooled it with the others would read as though money would.",
        "",
        "The last two rows are the two table causes, counted apart here because this is the only",
        "place either of them is counted at all. A flop whose class the index never listed is one",
        "no campaign has paid for yet; a flop whose class the index lists and this clone has not",
        "fetched is one already paid for and one fetch away. They cost different things to close,",
        "so a single row over both would name a gap and hide which gap it is.",
    ]
    return lines


def accuracy_lines(measured: Measured) -> list[str]:
    lines = heading("Per-spot accuracy, and the spread across the committed set")
    target = EXPLOITABILITY_TARGET_PCT_OF_POT
    ceiling = EXPLOITABILITY_CEILING_PCT_OF_POT
    # Which committed spots came out of the same solved tree, keyed off the object digest the
    # index commits rather than off the object file, which a clone need not hold.
    by_tree: dict[str, list[str]] = {}
    for cell in measured.cells:
        digest = measured.solve_digests.get(cell.spot_key)
        if digest is not None:
            by_tree.setdefault(digest, []).append(cell.spot_key)
    shares_with = {
        key: tuple(other for other in keys if other != key)
        for keys in by_tree.values()
        for key in keys
        if len(keys) > 1
    }
    trees = len(by_tree) if by_tree else measured.printed_spot_count
    lines += [
        "",
        f"  target: exploitability {target}% of the starting pot, a bound against the same menu",
        f"  ceiling: exploitability {ceiling}% of pot, menu-bound in the same way, and the worst",
        "    a played cell may carry rather than a figure anyone aimed at",
        f"  iteration cap: {SOLVE_ITERATION_CAP:,}",
        f"  committed spots: {measured.printed_spot_count}",
        f"  spots the index lists, fetched here or not: {measured.indexed_total}",
        f"  solved trees the committed spots come out of: {trees}",
        "",
        "  Each row is one committed hero decision node, keyed by board, preflop line, flop line,",
        "  pot and effective stack. The accuracy is not one measurement a row. Exploitability is a",
        "  property of a solved tree, so two hero nodes taken out of one solve carry one figure,",
        "  one iteration count and one wall clock between them. Rows that share a solve say so and",
        "  name the tree they share; a reader counting distinct measurements counts trees, not",
        "  rows.",
        "",
    ]
    between = 0
    for cell in measured.cells:
        value = cell.achieved_exploitability_pct_of_pot
        if target <= value <= ceiling:
            between += 1
        lines.append(f"  {cell.spot_key}")
        shared = shares_with.get(cell.spot_key, ())
        lines.append(
            f"      exploitability {value:.3f}% of pot, menu-bound, at {cell.iterations}"
            " iterations"
        )
        if shared:
            digest = measured.solve_digests.get(cell.spot_key, "")
            lines.append(
                f"      out of solved tree {digest[:16]}, shared with {len(shared)} other"
                f" committed spot{'' if len(shared) == 1 else 's'}:"
            )
            # Named by spot key rather than by sample file, because the sample names carry a
            # board texture and `cost_rows` reads any line pairing a texture with a digit as a
            # cost row owing a measured-or-scaled label.
            for other in sorted(shared):
                lines.append(f"        {other}")
            lines.append(
                "        the figure above is that tree's and is not a second measurement"
            )
    if not measured.cells:
        lines.append("  (no committed cell is fetched on this machine)")
    lines += [
        "",
        f"  cells between 0.3% and 1.0% of pot: {between}",
    ]
    for cell in measured.cells:
        value = cell.achieved_exploitability_pct_of_pot
        if target <= value <= ceiling:
            lines.append(
                f"    {''.join(cell.board)}  {cell.preflop_line.rendered}  {value:.3f}% of pot"
            )
    rejected = measured.rejected_above_ceiling
    lines += [
        "",
        f"  cells the campaign solved and rejected above 1.0% of pot:"
        f" {rejected if rejected is not None else 'not yet committed, the index carries it'}",
        "",
        "Convergence at the committed iteration count is unproven: exploitability was targeted,",
        "and frequencies on hands the solver drove to indifference settle later. The figures above",
        "are not proven to have converged and are not reported as settled accuracy. No single",
        "accuracy figure is published for the artifact as a whole - the per-cell figures are the",
        "evidence, and one number over the set would be a claim nothing measured.",
        "",
        "One of the committed cells has now been re-solved to the cap and diffed against the",
        "strategy the repo holds, which is the next section. It does not make the set settled: it",
        "measures how far one cell moved, and the answer is that the decision between betting and",
        "checking had settled and the split between the two bet sizes had not.",
    ]
    return lines


def deep_check_lines(measured: Measured) -> list[str]:
    lines = heading("The deep solve, diffed against the committed one")
    check = measured.deep
    if check is None:
        lines += [
            "",
            "  no deep solve is committed, so nothing here says how far the committed",
            "  frequencies would move under one",
        ]
        return lines
    shallow, deep = check.iterations
    lines += [
        "",
        "Exploitability says what a perfect opponent wins against a strategy. It does not say the",
        "strategy has stopped moving. So one cell was re-solved on the same tree, the same menu,",
        "the same ranges and the same arena, with the iteration cap as its only stopping rule, and",
        "its frequencies diffed against the committed ones hand class by hand class.",
        "",
        f"  cell: board {check.board}, {check.spot_key.split('/')[4]} to act",
        f"  committed run: {shallow} iterations, exploitability"
        f" {check.exploitability[0]:.4f}% of pot, menu-bound",
        f"  deep run: {deep:,} iterations, exploitability"
        f" {check.exploitability[1]:.4f}% of pot, menu-bound",
        "",
        "  what the whole range does, weighted by how often hero's own line brings it here:",
        "",
        "    action                committed      deep      moved",
    ]
    for index, label in enumerate(check.labels):
        first = check.committed_frequencies[index]
        second = check.deep_frequencies[index]
        lines.append(
            f"    {label:18s} {pct(first):>10}  {pct(second):>8}  {second - first:+9.4f}"
        )
    lines += [
        "",
        "  how far each hand class moved, as the largest change in any one of its frequencies:",
        "",
        f"    hand classes in the cell: {check.classes}",
        f"    classes that did not move at all: {check.unmoved}",
        f"    median: {check.median_moved:.4f}"
        f"    mean: {statistics.fmean(check.moved):.4f}"
        f"    worst: {max(check.moved):.4f}",
        f"    classes moving more than 0.05: {check.moving_past(0.05)}",
        f"    classes that changed which action they prefer: {len(check.top_action_changed)}",
        "",
        "  and split by how mixed the committed strategy already was:",
        "",
    ]
    for shape in ("pure", "lightly-mixed", "mixed"):
        count, mean = check.shape_mean(shape)
        if count:
            lines.append(f"    {shape:15s} {count:4d} classes   mean movement {mean:.4f}")
    lines += [
        "",
        "Read it this way. Whether to put money in had settled: the check goes from a frequency",
        "already near zero to zero, so both solves bet essentially the whole range here. Which",
        "size to bet had not: the two sizes trade range between them, as the table above shows,",
        "and the classes that moved are the ones the committed strategy already had mixing. The",
        "classes it had playing one action barely moved at all.",
        "",
        "So a reader may take the bet-or-check answer from this cell and may not take the size",
        "split from it. That is narrower than the contract's blanket qualification and it is what",
        "was measured; the qualification stands for every cell nothing was re-solved for.",
    ]
    return lines


def determinism_lines(measured: Measured) -> list[str]:
    lines = heading("Determinism: solved twice, and diffed rather than checksummed")
    record = measured.determinism
    if record is None:
        lines += ["", "  no repeated solve is recorded, so nothing here claims one"]
        return lines
    verdict = "byte-identical" if record.identical else "NOT byte-identical"
    low, high = record.iterations
    arenas = ", ".join(sorted({name for cell in record.cells for name in cell.arena_storage}))
    pots = ", ".join(f"{value:g}" for value in record.starting_pots)
    lines += [
        "",
        f"  configuration solved twice: {record.configuration}",
        f"  cells re-solved: {len(record.cells)}, at starting pot {pots}",
        f"  iterations: {low} to {high}, the same count in both runs of every cell",
        f"  arena precision: {arenas}, which is what the committed campaign was ruled to",
        "  runs: two processes against a restarted server, the second sharing the machine with",
        "    other work, so no cell reports the same wall clock twice",
        f"  strategies compared: {verdict}",
        "",
        "  Two comparisons a cell. The committed document byte for byte, which is what the repo",
        "  holds; and the solver's own per-combo strategies inside the two runs' objects, which is",
        "  the stronger of the two, because a committed row is rounded to a thousandth and two",
        "  runs could differ under that and still write the same bytes.",
        "",
        "    board   flop line so far      document   combos  in one run only"
        "  largest gap  wall clocks",
    ]
    for cell in record.cells:
        clocks = f"{cell.wall_seconds[0]:.1f}s / {cell.wall_seconds[1]:.1f}s"
        document = "same bytes" if cell.documents_identical else "DIFFERENT"
        lines.append(
            f"    {cell.board}  {flop_line_of(cell.spot_key):20s} {document:>9}"
            f"  {cell.combos:7d}  {cell.combos_in_only_one_run:15d}"
            f"  {cell.largest_gap:11g}  {clocks}"
        )
    repeated = sorted(
        {
            cell.wall_seconds
            for cell in record.cells
            if sum(1 for other in record.cells if other.wall_seconds == cell.wall_seconds) > 1
        }
    )
    if repeated:
        lines += [
            "",
            "  Two rows carrying the same wall clocks are two hero nodes of one solve rather than"
            " two",
            "  solves that took the same time. The clock is the tree's, and the accuracy table"
            " above",
            "  names which rows share one.",
        ]
    held = [cell for cell in record.cells if not cell.held]
    if held:
        lines.append("")
        for cell in held:
            lines.append(
                f"    {cell.board} is listed by the index and not held here, so its document was"
                " compared in object storage"
            )
    lines += [
        "",
        "  strategy digests, one a cell and the same in both runs: "
        + ", ".join(cell.digests[0][:16] for cell in record.cells),
        "",
        "If two runs of the committed configuration were not byte-identical the phase halts and",
        "a human is asked. No figure is set here in place of that, because a number nobody has a",
        "basis for would become the accuracy the artifact claims.",
        "",
        "This block is the campaign the repo commits and nothing else. An earlier draft read it",
        "out of the solve-cost record, whose repeated solve is another board at another starting",
        "pot and iteration count under quantized arenas rather than the full precision ruled",
        "here; the contract asks for determinism on the configuration actually committed, and the",
        "two are not the same measurement.",
    ]
    return lines


def menu_lines() -> list[str]:
    lines = heading("The bet menu the solve is configured with")
    flop = " ".join(str(int(100 * size)) for size in FLOP_BET_MENU)
    lines += [
        "",
        f"  flop bet sizes, percent of pot: {flop}",
        f"  turn and river bet sizes, percent of pot: {' '.join(TURN_RIVER_MENU)}",
        f"  raise: {FLOP_RAISE}    donk: empty",
        "  identical on both seats, and committed beside the data",
        "",
        "Nothing in the record uses 66% and 125%. The phase is flop only, so the turn and river",
        "half of the configured menu was never exercised, and a reader seeing it in the config",
        "would otherwise take it as evidence about streets nothing was solved for.",
        "",
        "No line this menu offers gets all-in in a single-raised pot. The deepest flop line at",
        "two raises reaches a little over a quarter of the stack behind, so a stack-off on the",
        "flop is not a branch of this tree in that pot type.",
    ]
    return lines


def cost_lines(measured: Measured) -> list[str]:
    lines = heading("The cost model: what was taken, and what was inferred")
    lines += [
        "",
        "The provenance column declares the cost figure on its own row. The class, board and",
        "orbit columns are brute-forced over the whole deck on every row and are the same kind of",
        "figure everywhere. A row that stopped on the iteration cap reports a floor rather than a",
        "cost, so no capped run's wall clock appears here as one.",
        "",
        "  texture   classes  boards  mean orbit  share of flops  at target  cost/class  source",
    ]
    for name in TEXTURES:
        cost = measured.costs[name]
        census = cost.census
        seconds = "-" if cost.seconds_to_target is None else f"{cost.seconds_to_target:9.1f}s"
        lines.append(
            f"  {name:9s} {census.classes:7,d} {census.boards:7,d}"
            f"  {census.mean_orbit:9.3f}  {pct(census.board_share):>13}"
            f"  {cost.converged_rows:9d}  {seconds:>10}  {cost.provenance}"
        )
    lines += ["", "  how each row's cost figure was arrived at:"]
    for name in TEXTURES:
        cost = measured.costs[name]
        lines.append(f"    {name} ({cost.provenance}): {cost.basis}")
    naive = measured.census["rainbow"].classes * NAIVE_ORBIT
    exact = measured.census["rainbow"].boards
    lines += [
        "",
        "The orbit factor is not one number, and taking it as one is the error this block was",
        "built to avoid. A class's orbit is how many dealt boards land in it; a paired board has",
        "fewer distinct suit dressings than an unpaired one, and trips fewer again.",
        "",
        f"  classes with three distinct suits: {measured.census['rainbow'].classes}",
        f"  boards they cover: {exact:,}, a mean of"
        f" {measured.census['rainbow'].mean_orbit:.3f} boards a class",
        f"  taking every one of them as {NAIVE_ORBIT} boards instead: {naive:,},"
        f" which overstates that exposure by {pct(naive / exact - 1)}",
        "",
        f"All {CANONICAL_FLOP_CLASSES:,} classes are in scope for the solve, and they are not one"
        " size. Any figure",
        "scaled by class count alone inherits that error.",
    ]
    return lines


def behaviour_lines(measured: Measured) -> list[str]:
    behaviour = measured.behaviour
    lines = heading("What the strategy does, over the spots this machine holds")
    lines += [
        "",
        f"  spots asked: {behaviour.asked}",
        f"  bet frequency: {behaviour.decisions.get('bet', 0)} of {behaviour.asked} asked",
        f"  raise frequency: {behaviour.decisions.get('raise', 0)} of {behaviour.asked} asked",
        f"  calls: {behaviour.decisions.get('call', 0)}"
        f"   checks: {behaviour.decisions.get('check', 0)}"
        f"   folds: {behaviour.decisions.get('fold', 0)}",
        "",
        "Neither the bet figure nor the raise figure is split into value and bluff, and their",
        "losses have opposite signs, so neither is a judgement about whether the play is good.",
        "",
        "Refusals by code. A code that fired zero times is labelled, because a report labelling",
        "nothing and a report labelling everything both read the same to a search for the word.",
        "",
    ]
    total = sum(behaviour.refusals.values())
    for code in REFUSAL_CODES:
        count = behaviour.refusals.get(code, 0)
        suffix = f"   {VACUOUS}" if count == 0 else ""
        lines.append(f"  {code:60s} {count}{suffix}")
    lines += [
        "",
        f"  refusals counted: {total}",
        "",
        "At a table a miss carries exactly two causes, and this report never pools them:",
        "",
        "  no cell for this board or line",
        "  in the index and not fetched on this machine",
        "",
        "The first of those is one absence at query time and two facts behind it. A board that",
        "was never solved and a board that was solved and rejected above the ceiling are both",
        "simply absent from the artifact, and the query meets one absence either way. The phase",
        "looked at the second kind and threw it away; it did not fail to look. How many cells",
        "were rejected that way is the header figure above, not a third cause here.",
        "",
        "The bot bets a flop and then refuses every turn. That seam was accepted in terms rather",
        "than discovered from a refusal count, and a refusal is not an action: the composite",
        "hands it back untouched and the simulator voids the hand.",
        "",
        "Fallback refusal codes now unreachable for a committed flop spot, because this phase",
        "answers that spot before the fallback is reached:",
    ]
    for code in measured.unreachable:
        lines.append(f"  {code}")
    if not measured.unreachable:
        lines.append("  (none)")
    asked, fired = behaviour.pot_odds_asked, behaviour.pot_odds_fired
    share = f"{100 * fired / asked:.1f}%" if asked else "n/a"
    lines += [
        "",
        f"  pot-odds river call: fired {fired} of {asked} river spots facing a bet ({share})",
        "",
        "Read that rate against the population it was taken over, which is this repo's own river",
        "enumeration from the fallback report rather than a table. That set was built to exercise",
        "the hand-cannot-lose branch, so it is heavy in hands that are ahead of the deck and light",
        "in the marginal spots where a calling rule is worth arguing about. A rate near the top of",
        "the scale is a fact about that set and not a claim about how often the bot would call.",
        "",
        "The rate is reported rather than defended in any case. Equity there is counted against a",
        "uniform unseen deck, which flatters hero, so the rule makes the bot over-call as the",
        "mirror of its current over-folding. The flag is off unless a caller turns it on.",
    ]
    return lines


def byte_lines(measured: Measured) -> list[str]:
    lines = heading("Bytes: what the repo commits, and what is left")
    headroom = ARTIFACT_BYTE_CAP - measured.artifact_bytes
    per_spot = measured.per_spot_bytes
    evidence = measured.postflop_bytes - measured.index_and_sample_bytes
    tree_per_spot = (
        measured.postflop_bytes / measured.printed_spot_count
        if measured.printed_spot_count
        else None
    )
    lines += [
        "",
        "Three figures, because three different questions are asked of them. The 20 MiB cap is on",
        "`data/artifacts` whole, so that is what the headroom is measured against. The budget the",
        "contract draws is around the committed index and the committed sample, so that is what",
        "the per-spot cost divides. And the postflop tree sits between the two: it is the index",
        "and the sample plus the records of the campaign that produced them, which is the figure",
        "the committed index declares. None of the three covers the object storage the index",
        "points at, which is outside git and outside this cap.",
        "",
        f"  bytes used, whole artifact tree: {measured.artifact_bytes:,}",
        f"  cap: {ARTIFACT_BYTE_CAP:,}",
        f"  headroom left: {headroom:,}",
        "",
        f"  of which data/artifacts/postflop, whole directory: {measured.postflop_bytes:,}",
        f"    the committed index and sample: {measured.index_and_sample_bytes:,}",
        f"    the campaign's own records beside them: {evidence:,}",
        "      the deep-convergence record, the determinism record, the solve config and the",
        "      objects manifest - evidence about the one campaign that ran, not the chart",
        "",
        f"  per spot, index and sample: "
        f"{'n/a' if per_spot is None else f'{per_spot:,.2f} bytes'}",
        f"  per spot, whole postflop directory: "
        f"{'n/a' if tree_per_spot is None else f'{tree_per_spot:,.2f} bytes'}",
        f"  hero class weights: {measured.weight_count:,} weights in"
        f" {measured.weight_bytes:,} bytes",
        f"  per weight: {measured.rate_per_weight:.3f} bytes",
        "",
        "The per-spot cost is index and sample bytes over the spot count and nothing else, and it",
        "is the one of the two that answers what a further spot costs. The directory figure below",
        "it is printed because the cap is on the tree, not because it is a per-spot price: the",
        "deep-convergence record is one measurement of one cell and does not grow with the next",
        "spot at all, so charging it to every spot overstates what the index bound affords.",
        "",
        "The per-weight rate is weight bytes over weight count and nothing else. A rate taken as",
        "whole-file bytes over weight count charges each spot's provenance block against every",
        "weight, and those scale per spot rather than per weight.",
    ]
    if measured.index is not None:
        lines.append(
            f"  the index declares {int(measured.index['committed_bytes']):,} bytes, reconciled"
            "\n  against the whole postflop directory above, not against the whole artifact tree,"
            "\n  which is mostly the preflop chart and is not what the index declares"
        )
    else:
        lines.append(
            "  no index is committed yet, so there is no declared figure to reconcile against"
        )
    return lines


def range_lines(measured: Measured) -> list[str]:
    lines = heading("The committed ranges, as pair weights on both sides")
    lines += [
        "",
        f"  the class-level floor is {RANGE_WEIGHT_FLOOR}: a class under it is dropped rather",
        "  than lifted, and the floor is class-level because one suit-specific weight collapses",
        "  the isomorphism group and forfeits the saving on every non-rainbow board",
        "",
    ]
    if not measured.ranges:
        lines.append("  (no solve configuration is committed, so no range is published)")
        return lines
    lines.append(f"  read out of {SOLVE_CONFIG_PATH.name}, beside the cells it produced")
    if measured.range_export:
        lines.append(f"  derived from {measured.range_export}")
    lines.append("")
    for found in measured.ranges:
        lines.append(f"  {found.name}: {found.describes}")
        lines.append(
            "    pair weights: "
            + ", ".join(
                f"{name} {value:g}"
                for name, value in sorted(
                    found.pairs.items(), key=lambda pair: DECK_RANKS.index(pair[0][0])
                )
            )
        )
        lines.append(
            f"    classes: {len(found.weights)}, standing for {found.combos} dealt combinations"
            f" at full weight and {found.weighted_combos:.1f} weighted"
        )
        lines.append(f"    smallest weight in the range: {found.smallest_weight:g}")
    lines += [
        "",
        "The two combination counts are both worth having and only one of them describes the",
        "range. A class kept at a weight of a tenth is one tenth of a hand in the solve and a",
        "whole one in the count at full weight, so on the out-of-position side the full-weight",
        "figure overstates the range the cells were solved against. Anything comparing one seat's",
        "range against the other's has to use the weighted figure or it is comparing a count of",
        "labels.",
        "",
        "There is no dropped-by-the-floor list here, and there cannot be one. The committed file",
        "stores the range after the floor ran, so a class the floor removed is not in it to be",
        "named; what is checkable, and is checked before this block prints, is that no surviving",
        f"weight sits under {RANGE_WEIGHT_FLOOR}. The smallest weight on each side is printed",
        "above as the evidence for that.",
        "",
        "A pair sitting near zero on one side while its neighbours sit near one is an asymmetry",
        "the floor exposes rather than causes, and it belongs to the export that produced the",
        "range rather than to the floor that reads it.",
    ]
    return lines


def conditioning_lines(measured: Measured) -> list[str]:
    lines = heading("Who bets first, and what hero's bet frequency is conditioned on")
    if not measured.frequencies:
        lines += ["", "  no committed cell is fetched here, so no frequency is published"]
        return lines
    lines += [
        "",
        "Ruled on 2026-09-21. The solve lets the out-of-position player bet the flop, that is",
        "legal poker, and the cells are a correct solution to the game as configured. They ship.",
        "What must never travel without them is this block: a continuation-bet frequency read",
        "on its own, with no statement of what the other seat already did, misleads whoever",
        "reads it, and the preflop re-solve that preceded this campaign did not produce that",
        "number and must not be read as having fixed it.",
        "",
        "Weighting, said once. Every share below is range-weighted: each two-card combination the",
        "board leaves is weighted by that seat's own committed weight for it, collapsed to the",
        "class label the cell holds, and averaged. That is the frequency the other seat actually",
        "faces. The unweighted class mean is printed beside it because the two differ by several",
        "points where one class stands for six dealt combinations and another for two, and a",
        "reader given one number cannot tell which convention produced it.",
        "",
        "  hero's own frequencies, by committed cell. The flop line is what happened before",
        "  hero's turn, so 'none' is a cell hero decides first on.",
        "",
        "    board   seat  flop line so far      classes   action"
        "              range-weighted   class mean",
    ]
    for found in measured.frequencies:
        for index, label in enumerate(found.labels):
            board = found.board if index == 0 else " " * len(found.board)
            seat = found.seat if index == 0 else ""
            line = found.flop_line if index == 0 else ""
            count = f"{found.classes}" if index == 0 else ""
            lines.append(
                f"    {board}  {seat:4s}  {line:20s} {count:>7}   {label:18s}"
                f" {pct(found.range_weighted[index]):>14}  {pct(found.class_mean[index]):>11}"
            )
    if not measured.leads:
        lines += [
            "",
            "  What the other seat did first cannot be re-derived on this machine. It lives in the",
            "  solved node objects, which are outside git by design and which this checkout does",
            f"  not hold; {OBJECTS_PATH.name} names where they belong. Until they are readable the",
            "  frequencies above are published without the thing that conditions them, which is",
            "  the state the ruling above is against, so read no continuation-bet number off this",
            "  report on a machine that prints this paragraph.",
        ]
        return lines
    lines += [
        "",
        "  what the other seat did before hero's turn came round",
        "",
        "  Recovered from the solved node objects, each verified against the digest the committed",
        "  index carries for it. A seat's reach at a node is the product of its own action",
        "  probabilities down the path, so reach over that hand's preflop weight is how often it",
        "  played the line that leads here, and one less that is how often hero's node was never",
        "  reached at all.",
    ]
    for lead in measured.leads:
        lines += [
            "",
            f"    board {lead.board}, the other seat is {lead.seat}, its committed line is"
            f" '{lead.line}'",
            f"    it arrives with {lead.weighted_combos:.2f} weighted combinations and plays that"
            f" line {pct(lead.takes_the_line)} of the time,",
            f"    so {pct(lead.otherwise)} of its range does something else and hero is"
            " never asked",
            f"    source: {lead.source}, digest {lead.digest[:16]}",
            "",
            "      holding            weighted combos   share before   share after"
            "   does otherwise",
        ]
        for category in lead.categories:
            lines.append(
                f"      {category.label:18s} {category.combos_before:9.2f}"
                f" {pct(category.share_before):>14} {pct(category.share_after):>13}"
                f" {pct(category.otherwise):>16}"
            )
    lines += [
        "",
        "Read the two blocks together and never apart. On the three-club board the button's own",
        "frequency says it bets nearly its whole range. The block under it says why that is not",
        "the sentence 'the raiser bets every flop': half the caller's range, and three quarters of",
        "its best hands, has already bet and is not in front of the button at all. What reaches",
        "the button is a range with the flushes and the sets thinned out of it, and against that",
        "range the button's answer is a reasonable one.",
        "",
        "A student drilled on the first number alone would learn to bet every flop in position.",
        "A student shown both would learn something narrower and true: against a caller who leads",
        "half its flops, what is left to bet into is weak. Whether a caller who leads half its",
        "flops is the opponent worth drilling against is the ruling above, not a measurement, and",
        "it is recorded here so nobody has to reconstruct it from the data.",
    ]
    return lines


def limitation_lines() -> list[str]:
    return heading("What this report is not") + [
        "",
        "No figure of chips won and no expected-value figure is published over this artifact. The",
        "hands such a figure would be computed from are the ones that ended at the turn refusal,",
        "so the number does not exist rather than being expensive to get.",
        "",
        "A green gate says the committed data is internally consistent and that the walk refuses",
        "where it says it refuses. It says nothing about whether the strategy is good poker: the",
        "repo has no postflop oracle, and every shape property checked here is satisfied by a",
        "uniformly wrong strategy.",
    ]


def render(measured: Measured) -> str:
    sections = [
        header_lines(),
        coverage_lines(measured),
        cross_check_lines(measured),
        answerable_lines(measured),
        accuracy_lines(measured),
        deep_check_lines(measured),
        determinism_lines(measured),
        conditioning_lines(measured),
        menu_lines(),
        cost_lines(measured),
        behaviour_lines(measured),
        byte_lines(measured),
        range_lines(measured),
        limitation_lines(),
    ]
    return "\n".join(line for block in sections for line in block) + "\n"


def check_the_report_text_holds(report: str) -> None:
    """The three properties a reader cannot check by eye, decided over the finished text.

    Run against the rendered report rather than against the data it came from, because what a
    reviewer reads is the text: a figure that reconciles and then prints without its
    qualification is still an unqualified figure on the page.
    """
    if not exploitability_lines_are_qualified(report):
        raise ReportFigureError(
            "a line printing an exploitability figure does not name the bet menu it is bound"
            " against, so it reads as an unconditional accuracy"
        )
    if not cost_rows_declare_measured_or_scaled(report):
        raise ReportFigureError(
            "a cost row does not declare whether its figure was measured or scaled, or a rainbow"
            " row reads as measured when rainbow never reached the target"
        )
    if not vacuous_codes_are_labelled(report):
        raise ReportFigureError(
            "the refusal breakdown does not carry exactly one row for every code the strategy can"
            " return, with the vacuous label matching the count on each"
        )


def main() -> int:
    try:
        measured = measure()
        text = render(measured)
        check_the_report_text_holds(text)
    except ReportFigureError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
