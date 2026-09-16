"""The committed flop solve, written for a reviewer who does not read code.

A report renders whatever it is handed. A spot count that disagrees with the index, a coverage
share that pools two loss causes, a byte figure that disagrees with the bytes on disk and an
exploitability figure printed without its menu qualification all exit 0 and publish as happily as
the right numbers would. So every figure the contract names as an obligation is **re-derived
here** out of a committed file or out of the deck itself, and the command exits non-zero and
writes nothing when one does not hold.

Nothing below is quoted from a decision list, a backlog entry or another phase's report. The
class census is brute-forced over every three-card board; the corpus figures are counted off the
committed corpus; the solve figures are parsed out of the committed solve-cost record and the
committed index; the behaviour figures come from asking the strategy itself.

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

import json
import re
import statistics
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
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
    """The byte figure the index declares against the bytes actually on disk."""
    if float(declared) != float(on_disk):
        raise ReportFigureError(
            f"the committed index declares {declared} bytes and the artifact tree holds"
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


def check_coverage_splits_by_cause(*, answerable: float, losses: Mapping[str, float]) -> bool:
    """The answerable share plus every loss cause is the whole population, or a cause is
    missing and the report understates the loss by exactly the cause it forgot."""
    total = float(answerable) + sum(float(value) for value in losses.values())
    if abs(total - 1.0) > 1e-9:
        raise ReportFigureError(
            f"an answerable share of {answerable} and losses {dict(losses)} sum to {total}"
            " rather than the whole population, so at least one loss cause is unaccounted for"
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


@dataclass(frozen=True)
class DeterminismRecord:
    """The one repeated solve in the committed record, and what the two runs produced."""

    board: str
    starting_pot: float
    iterations: int
    identical: bool
    digest_a: str
    digest_b: str
    divergence: float
    differences: int


def determinism_record() -> DeterminismRecord | None:
    for row in solve_cost_rows():
        if row["group"] != "determinism":
            continue
        found = row["determinism"]
        return DeterminismRecord(
            board=str(row["config"]["board"]),
            starting_pot=float(row["config"]["starting_pot"]),
            iterations=int(found["iterations_a"]),
            identical=bool(found["identical"]),
            digest_a=str(found["sha_a"]),
            digest_b=str(found["sha_b"]),
            divergence=float(found["max_divergence"]),
            differences=int(found["shape_differences"]),
        )
    return None


def committed_ranges() -> tuple[tuple[str, str, dict[str, float]], ...]:
    """Each range the converged rows were solved against, as its pocket-pair weights.

    The floor decision 12 rules is class-level, so what a reader needs to see is which pairs
    survive it on each side. Read out of the solve record's own appendix rather than restated.
    """
    appendix: dict[str, Any] = {}
    for line in SOLVE_COST_REPORT.read_text(encoding="utf-8").splitlines():
        if line.startswith("Appendix data: "):
            entry = json.loads(line[len("Appendix data: ") :])
            appendix[str(entry["key"])] = entry["value"]
    wanted: list[tuple[str, str]] = []
    for row in solve_cost_rows():
        if row.get("outcome") != "converged-to-target" or not row.get("usable_for_mean"):
            continue
        config = row["config"]
        for side in ("range_oop", "range_ip"):
            reference = str(config[side]).removeprefix("ref:")
            if (side, reference) not in wanted:
                wanted.append((side, reference))
    built = []
    for side, reference in wanted:
        body = appendix.get(reference)
        if not isinstance(body, str):
            continue
        built.append((side, reference, _pair_weights(body)))
    return tuple(built)


def _pair_weights(body: str) -> dict[str, float]:
    """The pocket pairs out of one range string, with an unstated weight reading as one."""
    weights: dict[str, float] = {}
    for token in body.split(","):
        name, _, value = token.partition(":")
        name = name.strip()
        if len(name) == 2 and name[0] == name[1] and name[0] in DECK_RANKS:
            weights[name] = float(value) if value else 1.0
    return weights


# --------------------------------------------------------------------------- #
# The corpus: what a real table asks for
# --------------------------------------------------------------------------- #


CAUSE_MULTIWAY = "multiway, structural"
CAUSE_PRICE = "preflop price outside the band"
CAUSE_LINE = "no cell for this preflop line"
CAUSE_BOARD = "no cell for this board, or in the index and not fetched"


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


def measure_corpus(covered_lines: frozenset[str], fetched_boards: frozenset[tuple[str, ...]]):
    """Walk every committed corpus hand that saw a flop, and name the first thing in its way.

    Coarsest gap first, the way the strategy's own walk fails closed, so the causes partition
    the flops rather than overlapping: a three-handed flop is counted as structural and is not
    also counted as an uncovered line.
    """
    prices = chart_prices()
    measured = CorpusMeasurement()
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
        if canonical_board(flop) not in fetched_boards:
            measured.causes[CAUSE_BOARD] += 1
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


def weight_bytes_and_count() -> tuple[int, int]:
    """The bytes hero's class weights occupy, and how many weights there are.

    Counted off the committed JSON's own weight block rather than off the whole file, because a
    whole-file rate charges the per-spot provenance fields against every weight and those scale
    per spot rather than per weight.
    """
    total_bytes = 0
    total_weights = 0
    files = sorted(SAMPLE_DIR.glob("*.json")) if SAMPLE_DIR.is_dir() else []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("class_weights") or []
        total_bytes += len(json.dumps(rows, separators=(",", ":")).encode("utf-8"))
        total_weights += sum(len(row) for row in rows)
    return (total_bytes, total_weights)


# --------------------------------------------------------------------------- #
# Measurement
# --------------------------------------------------------------------------- #


@dataclass
class Measured:
    census: dict[str, TextureCensus]
    costs: dict[str, TextureCost]
    determinism: DeterminismRecord | None
    ranges: tuple[tuple[str, str, dict[str, float]], ...]
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
    corpus = measure_corpus(covered_set, fetched_boards)

    strategy = PostflopBettingStrategy(library=library)
    behaviour = measure_behaviour(strategy)
    check_refusal_counts_reconcile(
        total=sum(behaviour.refusals.values()), by_code=behaviour.refusals
    )

    on_disk = artifact_bytes()
    if index is not None:
        check_bytes_reconcile(declared=float(index["committed_bytes"]), on_disk=float(on_disk))
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
    )
    check_servable_never_exceeds_arrivals(
        arrivals=corpus.arrivals, servable=corpus.servable, answerable=corpus.answerable
    )

    return Measured(
        census=census,
        costs=costs,
        determinism=determinism_record(),
        ranges=committed_ranges(),
        index=index,
        cells=cells,
        printed_spot_count=printed_spot_count,
        indexed_total=len(indexed),
        corpus=corpus,
        arrivals=arrival_probabilities(),
        behaviour=behaviour,
        unreachable=unreachable_fallback_codes(strategy),
        artifact_bytes=on_disk,
        postflop_bytes=postflop_bytes(),
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
        f"{ALL_BOARDS:,} three-card boards; the solve figures come from",
        "reports/active/latest_postflop_solve_cost.txt and data/artifacts/postflop/index.json;",
        "the corpus figures are counted off data/samples/public_corpus; the behaviour figures",
        "come from asking the strategy about the spots this machine holds.",
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
    for cause in (CAUSE_MULTIWAY, CAUSE_PRICE, CAUSE_LINE, CAUSE_BOARD):
        count = corpus.causes.get(cause, 0)
        lines.append(f"  lost to {cause}: {count} ({pct(count / total)})")
    lines += [
        "",
        "The multiway share is structural rather than fundable. A two-range solve cannot express",
        "a three-handed flop at any budget, on any machine, under any menu, so no campaign closes",
        "that share and a report that pooled it with the others would read as though money would.",
    ]
    return lines


def accuracy_lines(measured: Measured) -> list[str]:
    lines = heading("Per-spot accuracy, and the spread across the committed set")
    target = EXPLOITABILITY_TARGET_PCT_OF_POT
    ceiling = EXPLOITABILITY_CEILING_PCT_OF_POT
    lines += [
        "",
        f"  target: exploitability {target}% of the starting pot, a bound against the same menu",
        f"  ceiling: exploitability {ceiling}% of pot, menu-bound in the same way, and the worst",
        "    a played cell may carry rather than a figure anyone aimed at",
        f"  iteration cap: {SOLVE_ITERATION_CAP:,}",
        f"  committed spots: {measured.printed_spot_count}",
        f"  spots the index lists, fetched here or not: {measured.indexed_total}",
        "",
        "  Each row is one committed hero decision node, keyed by board, preflop line, flop line,",
        "  pot and effective stack. The accuracy is that cell's own achieved figure.",
        "",
    ]
    between = 0
    for cell in measured.cells:
        value = cell.achieved_exploitability_pct_of_pot
        if target <= value <= ceiling:
            between += 1
        lines.append(f"  {cell.spot_key}")
        lines.append(
            f"      exploitability {value:.3f}% of pot, menu-bound, at {cell.iterations}"
            " iterations"
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
        "frequencies on hands the solver drove to indifference settle later, and nothing here has",
        "diffed a deep solve against a shallow one. The figures above are not proven to have",
        "converged and are not reported as settled accuracy. No single accuracy figure is",
        "published for the artifact as a whole - the per-cell figures are the evidence, and one",
        "number over the set would be a claim nothing measured.",
    ]
    return lines


def determinism_lines(measured: Measured) -> list[str]:
    lines = heading("Determinism: solved twice, and diffed rather than checksummed")
    record = measured.determinism
    if record is None:
        lines += ["", "  no repeated solve is recorded, so nothing here claims one"]
        return lines
    verdict = "byte-identical" if record.identical else "NOT byte-identical"
    lines += [
        "",
        f"  configuration solved twice: board {record.board}, starting pot {record.starting_pot}",
        f"  runs: two processes against a restarted server, {record.iterations} iterations each",
        f"  strategies compared: {verdict}",
        f"  strategy digests: {record.digest_a} and {record.digest_b}",
        f"  per-action divergence: {record.divergence}; shape differences: {record.differences}",
        "",
        "If two runs of the committed configuration were not byte-identical the phase halts and",
        "a human is asked. No figure is set here in place of that, because a number nobody has a",
        "basis for would become the accuracy the artifact claims.",
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
    per_spot = (
        measured.postflop_bytes / measured.printed_spot_count
        if measured.printed_spot_count
        else None
    )
    lines += [
        "",
        "The budget covers the committed index and the committed sample. It does not cover the",
        "object storage the index points at, which is outside git and outside this cap.",
        "",
        f"  bytes used, whole artifact tree: {measured.artifact_bytes:,}",
        f"  of which the postflop index and sample: {measured.postflop_bytes:,}",
        f"  cap: {ARTIFACT_BYTE_CAP:,}",
        f"  headroom left: {headroom:,}",
        f"  per spot: {'n/a' if per_spot is None else f'{per_spot:,.1f} bytes'}",
        f"  hero class weights: {measured.weight_count:,} weights in"
        f" {measured.weight_bytes:,} bytes",
        f"  per weight: {measured.rate_per_weight:.3f} bytes",
        "",
        "The per-weight rate is weight bytes over weight count and nothing else. A rate taken as",
        "whole-file bytes over weight count charges each spot's provenance block against every",
        "weight, and those scale per spot rather than per weight.",
    ]
    if measured.index is not None:
        lines.append(
            f"  the index declares {int(measured.index['committed_bytes']):,} bytes,"
            " reconciled against the bytes on disk above"
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
        lines.append("  (no converged row in the record names a range)")
        return lines
    for side, reference, weights in measured.ranges:
        dropped = sorted(name for name, value in weights.items() if value < RANGE_WEIGHT_FLOOR)
        lines.append(f"  {side} {reference}")
        lines.append(
            "    pair weights: "
            + ", ".join(f"{name} {value:g}" for name, value in sorted(weights.items()))
        )
        lines.append(f"    dropped by the floor: {', '.join(dropped) if dropped else 'none'}")
    lines += [
        "",
        "A pair sitting near zero on one side while its neighbours sit near one is an asymmetry",
        "the floor exposes rather than causes, and it belongs to the export that produced the",
        "range rather than to the floor that reads it.",
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
        determinism_lines(measured),
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
