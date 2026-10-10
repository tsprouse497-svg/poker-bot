"""The flop campaign, written for a reviewer who does not read code.

Phase 21's contract names the figures this report must print: the lines covered and excluded with
their reasons, each line's tree, the boards and closed decision points per line, the cells refused
above the ceiling, the bytes used and the headroom left, the memory bar, the candidates' costs, the
money spent against its cap, the thread comparison, both determinism results, the fresh-clone and
fetched coverage, coverage by texture group, the share of the 22,100 flops and of the corpus's
flops the bot can answer, and the table result.

**Every one is re-derived here from committed files, and one that does not reconcile exits
non-zero and writes nothing.** The tree figures come from the port of GTOpen's tree rule, the
lines and their reach from the committed chart, the boards and coverage from the per-line
manifests, each checked against its line's own tree and phase 16's boards against the index they
were re-solved into. The measured records under `campaign/` are re-judged from their own raw
fields by `flop_campaign_report_records`.

**A figure not yet measured says so.** No rented machine has run, so the candidates' costs, the
box's determinism re-run, the six texture solves, the spend, settling and the table re-run have no
record; each prints `NOT_YET_MEASURED` on its own line, never a zero, a blank or an estimate.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_file_sizes  # noqa: E402
import generate_postflop_betting_report as betting_report  # noqa: E402

from poker_training_bot.solver_artifacts import (
    flop_campaign_report_records as records,  # noqa: E402
)
from poker_training_bot.solver_artifacts import postflop_lines as lines  # noqa: E402
from poker_training_bot.solver_artifacts import postflop_manifest as manifests_module  # noqa: E402
from poker_training_bot.solver_artifacts import postflop_textures as textures  # noqa: E402
from poker_training_bot.solver_artifacts import postflop_tree_size as tree_size  # noqa: E402
from poker_training_bot.solver_artifacts.flop_campaign_report_records import (  # noqa: E402
    BOX_DID_NOT_REPEAT,
    BOX_REPEATED,
    M4_MATCH,
    M4_MISMATCH,
    NOT_YET_MEASURED,
    ReportFigureError,
)
from poker_training_bot.solver_artifacts.postflop_artifact import (  # noqa: E402
    POSTFLOP_DIR,
    PostflopArtifactError,
    import_postflop_index,
    import_postflop_sample,
)
from poker_training_bot.solver_artifacts.postflop_campaign_costs import (  # noqa: E402
    BENCHMARK_CAP_USD,
)
from poker_training_bot.solver_artifacts.postflop_isomorphism import (  # noqa: E402
    CANONICAL_FLOP_CLASSES,
    canonical_board,
)
from poker_training_bot.solver_artifacts.postflop_solve_driver import (  # noqa: E402
    ARENA_READING_MARGIN,
    MEMORY_CEILING_FRACTION,
)
from poker_training_bot.solver_artifacts.postflop_textures import flops_in_class  # noqa: E402
from poker_training_bot.solver_artifacts.spot_key import render_entry  # noqa: E402

__all__ = [
    "BOX_DID_NOT_REPEAT",
    "BOX_REPEATED",
    "M4_MATCH",
    "M4_MISMATCH",
    "NOT_YET_MEASURED",
    "REPORT_PATH",
    "ReportFigureError",
    "main",
    "render_report",
]

REPORT_PATH = REPO_ROOT / "reports" / "active" / "latest_flop_campaign_report.txt"
REPORT_BYTE_CAP = dict(check_file_sizes.BYTE_LIMITS)["reports/active/*.txt"]
ARTIFACT_BYTE_CAP = dict(check_file_sizes.DIRECTORY_BYTE_LIMITS)["data/artifacts"]
ALL_FLOPS = sum(textures.group_flop_counts().values())

PHASE_16_CEILING = (194, 259)
"""Phase 16's coverage ceiling, corpus flops answerable of flop-reaching hands, from its stage 3
poker review (`THE-PHASE-CAN-ANSWER-AT-MOST-THREE-QUARTERS-OF-CORPUS-FLOPS`). Its numerator came
from a classification no committed code reproduces, so only its denominator and multiway share
are re-counted here, and a corpus that no longer gives them refuses the ceiling."""
PHASE_16_MULTIWAY = 20

MALFORMED = (KeyError, TypeError, ValueError, IndexError, AttributeError)
"""What a record with a missing or mistyped field raises on the way to a figure."""


def heading(title: str) -> list[str]:
    return ["", title, "-" * len(title)]


def pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.2f}%" if whole else "n/a"


def line_of(preflop_line: str) -> str:
    """`t6/d100/BB/BTN:raise@2.5,BB:call` as the line a manifest is filed under."""
    parts = preflop_line.split("/", 3)
    if len(parts) != 4:
        raise ReportFigureError(f"{preflop_line!r} is not a preflop line in the index's grammar")
    return parts[3]


# --------------------------------------------------------------------------- #
# The manifests, checked against the tree and the index
# --------------------------------------------------------------------------- #


def checked_manifests(postflop_dir: Path, index: Mapping[str, Any]) -> dict[str, dict]:
    """Every committed manifest, refused unless it holds together, closes on its line's own tree,
    and carries phase 16's boards exactly as the index records their re-solve."""
    try:
        found = manifests_module.load_manifests(postflop_dir / "manifests")
    except (OSError, ValueError) as error:
        raise ReportFigureError(f"the manifests cannot be read: {error}") from error
    for line, manifest in found.items():
        errors = manifests_module.manifest_errors(manifest)
        if errors:
            raise ReportFigureError(f"the manifest for {line} fails its checks: {errors}")
        closed_boards = [
            tuple(entry["board"])
            for entry in manifest["boards"]
            if entry["status"] == manifests_module.CLOSED
        ]
        derived_flops_held = sum(flops_in_class(board) for board in closed_boards)
        if derived_flops_held != manifest["flops_held"]:
            raise ReportFigureError(
                f"{line}: {len(closed_boards)} closed boards stand for {derived_flops_held:,}"
                f" flops; the manifest records {manifest['flops_held']:,}"
            )
    for spot in index["entries"]:
        line = line_of(spot["preflop_line"])
        boards = {tuple(entry["board"]): entry for entry in found.get(line, {}).get("boards", [])}
        entry = boards.get(tuple(spot["board"]))
        where = f"{''.join(spot['board'])} on {line}"
        if entry is None or entry["status"] != manifests_module.CLOSED:
            raise ReportFigureError(f"{where} is in the index and not closed in its manifest")
        for field in ("iterations", "achieved_exploitability_pct_of_pot"):
            if entry[field] != spot[field]:
                raise ReportFigureError(
                    f"{where}: the manifest's {field} is {entry[field]!r} and the index's"
                    f" {spot[field]!r}; one solve gives one figure, two is two solves mixed"
                )
        if entry.get("strategy_digests", {}).get(spot["spot_key"]) != spot["strategy_digest"]:
            raise ReportFigureError(f"{spot['spot_key']}: the manifest's digest is not the index's")
    return found


def closed_boards_of(manifest: Mapping[str, Any]) -> list[tuple[str, ...]]:
    return [
        tuple(entry["board"])
        for entry in manifest["boards"]
        if entry["status"] == manifests_module.CLOSED
    ]


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #


def header_lines() -> list[str]:
    return [
        "The flop campaign",
        "=================",
        "",
        "What the campaign has solved, what it would cost to solve more, and what the bot can",
        "answer now. Every figure is re-derived from committed files by the generator, which exits",
        "non-zero rather than print one that does not reconcile. Phase 16's table result and its",
        "coverage ceiling are its own published figures, and say so where they print. A figure",
        f"whose record does not exist yet reads '{NOT_YET_MEASURED}': no rented machine has run,",
        "so nothing measured on one is printed, and nothing is estimated in its place.",
    ]


def line_section(corpus: Any) -> list[str]:
    ranked = lines.ranked_lines()
    if ranked[: len(lines.ADMITTED_LINES)] != lines.ADMITTED_LINES:
        raise ReportFigureError(
            f"the chart ranks {ranked}; decision 9's order is {lines.ADMITTED_LINES}"
        )
    corpus_order = [line for line, _ in corpus.arrivals.most_common()]
    rows = heading("Lines: admitted in the chart's order, and excluded with reasons")
    rows.append("  rank, line, how often the chart reaches its flop, and the corpus's order beside")
    for position, line in enumerate(lines.ADMITTED_LINES, start=1):
        arrivals = corpus.arrivals[line]
        real = corpus_order.index(line) + 1 if line in corpus_order else None
        rows.append(
            f"  {position}. {line}: {100 * lines.line_reach(line):.2f}% of hands; in the corpus"
            f" {arrivals} flop arrivals, rank {real if real else 'none'}"
        )
    for line, reason in lines.EXCLUDED_LINES.items():
        try:
            lines.line_ranges(line)
        except lines.LineRangeError:
            pass
        else:
            raise ReportFigureError(f"{line} is excluded, yet the chart now supplies its ranges")
        rows.append(f"  excluded: {line}, {reason} ({corpus.arrivals[line]} corpus flop arrivals)")
    rows.append("  excluded: every three-bet pot; decision 9 admits only single-raised lines")
    return rows


def entry_bytes(postflop_dir: Path, index: Mapping[str, Any]) -> float | None:
    """Git bytes one more indexed decision point costs: its index entry plus its object-list
    entry, each measured as the committed file less the same file emptied, over its entries.
    The object list's cells listed and not held are left out: they are phase 16's record of a
    cell outside git, not the shape every held object takes."""
    if not index["entries"]:
        return None
    index_bytes = (postflop_dir / "index.json").stat().st_size
    emptied = len((json.dumps({**index, "entries": []}, indent=1) + "\n").encode("utf-8"))
    per_entry = (index_bytes - emptied) / len(index["entries"])
    objects_path = postflop_dir / "objects.json"
    if objects_path.is_file():
        objects = json.loads(objects_path.read_text(encoding="utf-8"))
        if objects.get("objects"):
            empty = json.dumps({**objects, "objects": {}}, indent=1) + "\n"
            per_entry += (objects_path.stat().st_size - len(empty.encode("utf-8"))) / len(
                objects["objects"]
            )
    return per_entry


def tree_section(per_entry: float | None) -> list[str]:
    rows = heading("Each admitted line's tree, on the clone's tree rule (decision 17)")
    rows += [
        "  A line with another pot builds another tree, so every figure is per line. A solved",
        "  board keeps its flop and turn decision points for both seats; the river is solved at",
        "  the table by a later phase, so its counts below are tree figures that nothing keeps.",
    ]
    for line in lines.ADMITTED_LINES:
        ranges = lines.line_ranges(line)
        figures = tree_size.line_tree_figures(line)
        closure = tree_size.closure_counts(figures)
        bar = tree_size.line_memory_bar(line)
        rows += [
            "",
            f"  {line}",
            f"    pot {ranges.starting_pot:.1f}bb behind {ranges.effective_stack:.1f}bb;"
            f" out of position {ranges.oop_position}, in position {ranges.ip_position}",
            f"    flop tree: {figures.nodes:,} nodes",
            f"    closed by one solve, both seats: {closure['flop']:,} flop and"
            f" {closure['turn']:,} turn decision points",
            f"    river decision points a hand can reach: {tree_size.river_tree_points(figures):,},"
            " a tree figure, not stored",
            "    river decision points built under the dealt turn card, never reached:"
            f" {tree_size.unreachable_river_points(figures):,}, not stored",
            f"    largest planned arena over all {ALL_FLOPS:,} flops: {bar.arena_bytes:,} bytes on"
            f" {''.join(bar.board)}, which {bar.flops_at_bar} flops plan; card memory"
            f" {bar.vram_bytes:,} bytes by GTOpen's estimate",
        ]
        if per_entry is None:
            rows.append(f"    index cost if git held this line's full index: {NOT_YET_MEASURED}")
        else:
            cost = closure["flop"] * CANONICAL_FLOP_CLASSES * per_entry
            rows.append(
                f"    index cost if git held this line's full index: {closure['flop']} x"
                f" {CANONICAL_FLOP_CLASSES:,} classes x {per_entry:,.1f} bytes = {cost:,.0f} bytes"
            )
    return rows


def memory_bar_section(found: Mapping[str, dict], index: Mapping[str, Any]) -> list[str]:
    bar = tree_size.campaign_memory_bar()
    read = bar.arena_bytes * (1 + ARENA_READING_MARGIN)
    rows = heading("The memory bar: the largest planned arena of every flop of every line")
    rows += [
        f"  {bar.line} on {''.join(bar.board)}: {bar.arena_bytes:,} bytes in the server's unit,"
        f" {read / 1e9:.2f} GB as the driver's guard reads it ({ARENA_READING_MARGIN:.2%} over)",
        f"  RAM that holds it at the {MEMORY_CEILING_FRACTION:.2f} ceiling:"
        f" {read / MEMORY_CEILING_FRACTION / 1e9:.1f} GB; card memory {bar.vram_bytes:,} bytes",
        "  a candidate that cannot hold this bar is excluded with that reason and never ranked",
    ]
    solved = {line_of(spot["preflop_line"]) for spot in index["entries"]}
    for line in sorted(solved):
        boards = closed_boards_of(found[line])
        largest = max(tree_size.planned_arena_for(line, board) for board in boards)
        rows.append(
            f"  {line}: largest committed board {largest:,} bytes;"
            f" {tree_size.flops_planned_above(line, largest - 1):,} of {ALL_FLOPS:,} flops plan"
            f" at or above it, {tree_size.flops_planned_above(line, largest):,} strictly above"
        )
    return rows


def board_section(found: Mapping[str, dict], index: Mapping[str, Any]) -> list[str]:
    rows = heading("Boards and closed decision points per line")
    for line in lines.ADMITTED_LINES:
        manifest = found.get(line)
        if manifest is None:
            rows.append(f"  {line}: no manifest, no board solved on this line")
            continue
        closure = tree_size.closure_counts(tree_size.line_tree_figures(line))
        closed = closed_boards_of(manifest)
        points = len(closed) * sum(closure.values())
        threads = sorted({entry["threads"] for entry in manifest["boards"]})
        machines = sorted({entry["machine"] for entry in manifest["boards"]})
        rows += [
            f"  {line}: {len(manifest['boards'])} boards, {len(closed)} closed, holding"
            f" {points:,} flop and turn decision points for both seats",
            f"    refused above the 1.0% ceiling: {manifest['refused_boards']}, scoped to this"
            " line and both its seats, not the board on other lines",
            f"    solved on {'; '.join(machines)} at {', '.join(map(str, threads))} threads",
        ]
    rows.append(
        "  the committed index's own count of cells solved and refused above the ceiling:"
        f" {index['cells_solved_and_rejected_above_one_percent']}"
    )
    return rows


def coverage_section(found: Mapping[str, dict], postflop_dir: Path) -> list[str]:
    try:
        covered = manifests_module.coverage(found, sample_dir=postflop_dir / "sample")
    except ValueError as error:
        raise ReportFigureError(str(error)) from error
    rows = heading(f"Coverage: classes held of {CANONICAL_FLOP_CLASSES:,}, flops of {ALL_FLOPS:,}")
    rows.append(
        f"  a fresh clone, from the cells in git: {covered.fresh_clone_classes} classes,"
        f" {covered.fresh_clone_flops} flops, {pct(covered.fresh_clone_flops, ALL_FLOPS)}"
    )
    for line in lines.ADMITTED_LINES:
        held = covered.flops_held.get(line, 0)
        rows.append(
            f"  a fetched machine, {line}: {covered.classes_held.get(line, 0)} classes,"
            f" {held:,} flops, {pct(held, ALL_FLOPS)} of every flop"
        )
    rows.append(
        f"  preflop lines with a closed board: {covered.lines}; seats those lines cover:"
        f" {covered.seats}, two a line, since a closed board is closed for both seats"
    )
    groups = textures.group_class_counts()
    rows.append("  by texture group, classes held of the classes in the group:")
    for line, by_group in covered.by_texture.items():
        held = ", ".join(f"{group} {by_group[group]} of {groups[group]}" for group in groups)
        rows.append(f"    {line}: {held}")
    return rows


def corpus_section(found: Mapping[str, dict], postflop_dir: Path, corpus: Any) -> list[str]:
    flops, ceiling_flops = corpus.flops, PHASE_16_CEILING[1]
    multiway = corpus.causes[betting_report.CAUSE_MULTIWAY]
    if flops != ceiling_flops or multiway != PHASE_16_MULTIWAY:
        raise ReportFigureError(
            f"the corpus gives {flops} flop-reaching hands and {multiway} multiway; phase 16's"
            f" ceiling was measured on {ceiling_flops} and {PHASE_16_MULTIWAY}"
        )
    fresh: dict[str, set[tuple[str, ...]]] = {}
    for cell in import_postflop_sample(postflop_dir / "sample"):
        line = ",".join(render_entry(action) for action in cell.preflop_actions)
        fresh.setdefault(line, set()).add(canonical_board(cell.board))
    fetched = {line: set(closed_boards_of(manifest)) for line, manifest in found.items()}

    def answerable(held: Mapping[str, set]) -> int:
        total = 0
        for line, boards in held.items():
            boards = frozenset(boards)
            walk = betting_report.measure_corpus(frozenset({line}), boards, boards)
            total += walk.servable[line]
        return total

    on_fresh, on_fetched = answerable(fresh), answerable(fetched)
    rows = heading("The share of corpus flops the bot can answer")
    rows += [
        f"  flop-reaching hands in the committed corpus: {flops}",
        f"  answerable on a fresh clone: {on_fresh} ({pct(on_fresh, flops)})",
        f"  answerable on a fetched machine: {on_fetched} ({pct(on_fetched, flops)})",
        f"  phase 16's ceiling: {PHASE_16_CEILING[0]} of {ceiling_flops},"
        f" {PHASE_16_CEILING[0] / ceiling_flops:.1%}, from its stage 3 review; the {ceiling_flops}"
        " and the multiway share below are re-counted here, its numerator is not",
        f"  multiway, structural: {multiway} ({pct(multiway, flops)}); a two-range solve cannot",
        "    express a three-handed flop at any budget, so no campaign closes this share",
    ]
    return rows


def byte_section(found: Mapping[str, dict], postflop_dir: Path, index: Mapping) -> list[str]:
    artifacts = REPO_ROOT / "data" / "artifacts"
    elsewhere = sum(
        path.stat().st_size
        for path in artifacts.rglob("*")
        if path.is_file() and POSTFLOP_DIR not in path.parents
    )
    postflop = sum(path.stat().st_size for path in postflop_dir.rglob("*") if path.is_file())
    used = elsewhere + postflop
    rows = heading("Bytes used and headroom left")
    rows += [
        f"  data/artifacts, whole tree: {used:,} bytes of the {ARTIFACT_BYTE_CAP:,} cap,"
        f" {ARTIFACT_BYTE_CAP - used:,} left",
        f"  of which the postflop folder: {postflop:,} bytes (the index declares"
        f" {index['committed_bytes']:,}; the betting report reconciles the two)",
    ]
    for line in lines.ADMITTED_LINES:
        if line in found:
            size = manifests_module.manifest_path(line, postflop_dir / "manifests").stat().st_size
            rows.append(f"  manifest for {line}: {size:,} bytes")
    rows.append("  object storage, where the full index and the objects live, is outside this cap")
    return rows


def read_record(path: Path) -> Any:
    try:
        return manifests_module.read_strict_json(path.read_bytes(), str(path))
    except ValueError as error:
        raise ReportFigureError(str(error)) from error


def record_section(title: str, path: Path, reader, *context) -> list[str]:
    """A measured record's rows, or the figure named as not yet measured when it is absent."""
    rows = heading(title)
    if not path.is_file():
        return [*rows, f"  {NOT_YET_MEASURED}: no {path.parent.name}/{path.name} is committed"]
    try:
        return rows + reader(read_record(path), *context)
    except ReportFigureError:
        raise
    except MALFORMED as error:
        raise ReportFigureError(f"{path.name}: malformed record: {error!r}") from error


def campaign_sections(postflop_dir: Path, index: Mapping[str, Any]) -> list[str]:
    campaign = postflop_dir / "campaign"
    present = (
        [p.name for p in campaign.iterdir() if not p.name.startswith(".")]
        if campaign.is_dir()
        else []
    )
    unread = records.unread_records(present)
    if unread:
        raise ReportFigureError(
            f"campaign/ holds {unread}, which this report neither prints nor re-derives"
        )
    bar = tree_size.campaign_memory_bar()

    def at(name: str) -> Path:
        return campaign / name

    rows = record_section("The thread comparison", at(records.SWEEP_RECORD), records.sweep_rows)
    rows += record_section(
        "A changed thread count does not change the answer: the Mac re-solve",
        at(records.MAC_RESOLVE_RECORD),
        records.mac_resolve_rows,
        index,
    )
    rows += record_section(
        "Determinism on the M4, re-solved on the clone's tree",
        postflop_dir / "determinism.json",
        records.m4_determinism_rows,
        index,
    )
    rows += record_section(
        "Determinism on the rented box",
        at(records.BOX_DETERMINISM_RECORD),
        records.box_determinism_rows,
        index,
    )
    rows += record_section(
        "Candidate machines and cost per solved flop",
        at(records.CANDIDATES_RECORD),
        records.candidate_rows,
        bar,
    )
    if not at(records.CANDIDATES_RECORD).is_file():
        rows.append(f"  cost per solved flop: {NOT_YET_MEASURED}")
    rows += record_section(
        "Money spent against the cap", at(records.SPEND_LEDGER_RECORD), records.ledger_rows
    )
    if not at(records.SPEND_LEDGER_RECORD).is_file():
        rows.append(f"  the trial cap it will count against: {records.money(BENCHMARK_CAP_USD)}")
    rows += record_section(
        "Six texture solves and one closed line's projected cost",
        at(records.TEXTURE_TRIAL_RECORD),
        records.texture_rows,
    )
    rows += record_section(
        "The table, re-run on phase 16's terms", at(records.TABLE_RESULT_RECORD), records.table_rows
    )
    rows += heading("Figures whose records no committed code writes yet")
    for figure in (
        "settling, one flop of each texture group solved on to the cap",
        "the GPU trial, one flop solved twice and compared exactly",
        "harvest time and stored size of one closed flop, on the six trial flops",
        "the campaign budget, with the measured turn size and its monthly storage bill",
        "which limit stopped the campaign, the budget or the fifth line",
    ):
        rows.append(f"  {figure}: {NOT_YET_MEASURED}")
    return rows


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #


def render_report(postflop_dir: Path = POSTFLOP_DIR) -> str:
    """The whole report for one postflop tree, or `ReportFigureError` on the first figure that
    does not reconcile."""
    postflop_dir = Path(postflop_dir)
    try:
        index = import_postflop_index(postflop_dir / "index.json")
    except PostflopArtifactError as error:
        raise ReportFigureError(f"the committed index cannot be read: {error}") from error
    found = checked_manifests(postflop_dir, index)
    corpus = betting_report.measure_corpus(frozenset(), frozenset(), frozenset())
    sections: Sequence[list[str]] = (
        header_lines(),
        line_section(corpus),
        tree_section(entry_bytes(postflop_dir, index)),
        memory_bar_section(found, index),
        board_section(found, index),
        coverage_section(found, postflop_dir),
        corpus_section(found, postflop_dir, corpus),
        byte_section(found, postflop_dir, index),
        campaign_sections(postflop_dir, index),
    )
    text = "\n".join(row for section in sections for row in section) + "\n"
    if len(text.encode("utf-8")) > REPORT_BYTE_CAP:
        raise ReportFigureError(f"the report is over the {REPORT_BYTE_CAP:,} byte cap")
    return text


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--postflop-dir", type=Path, default=POSTFLOP_DIR)
    parser.add_argument("--output", type=Path, default=REPORT_PATH)
    arguments = parser.parse_args(argv)
    try:
        text = render_report(arguments.postflop_dir)
    except ReportFigureError as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(text, encoding="utf-8")
    print(f"wrote {arguments.output} ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
