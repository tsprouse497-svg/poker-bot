"""The flop campaign report's measured records, each re-derived before a line of it is printed.

`scripts/generate_flop_campaign_report.py` prints these; this module reads them. Every record
lives under `data/artifacts/postflop/campaign/` (the M4's own determinism record beside the index)
and every one is checked against what the repo's own modules compute from its raw fields: a thread
choice against `postflop_threads.sweep_verdict` over its runs, a candidate ranking against
`postflop_campaign_costs.rank_candidates` over its candidates, a spend total against
`SpendLedger.from_document`, a projection against `postflop_textures.project_line_cost`, and a
determinism verdict against `postflop_determinism.rerun_verdict` read cell by cell. A record that
disagrees with its own fields raises `ReportFigureError`, because a report prints whatever it is
handed and the record is what the phase's spending and halts rest on.

**A record that does not exist is a figure not yet measured.** Each reader is called only when its
file is present; the generator prints `NOT_YET_MEASURED` in its place otherwise, never a zero, a
blank or an estimate.

Phase 16's table figures are the one thing here not re-derived: twenty thousand hands at seed 777
are a table run, not a file, so they are carried as phase 16's audit packet published them and
printed under that name.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from poker_training_bot.solver_artifacts import postflop_campaign_costs as costs
from poker_training_bot.solver_artifacts import postflop_determinism as determinism
from poker_training_bot.solver_artifacts import postflop_lines as lines
from poker_training_bot.solver_artifacts import postflop_textures as textures
from poker_training_bot.solver_artifacts import postflop_threads as threads
from poker_training_bot.solver_artifacts.postflop_machine import MachineRecord

NOT_YET_MEASURED = "not yet measured"

BOX_REPEATED = "the box repeated itself"
BOX_DID_NOT_REPEAT = "the box did not repeat itself"
M4_MATCH = "same digests as the M4's committed solve"
M4_MISMATCH = "other digests than the M4's committed solve"
"""The four determinism findings, worded so no one is a substring of its opposite."""

SWEEP_RECORD = "thread_sweep.json"
MAC_RESOLVE_RECORD = "mac_resolve_at_thread_count.json"
CANDIDATES_RECORD = "candidates.json"
BOX_DETERMINISM_RECORD = "box_determinism.json"
TEXTURE_TRIAL_RECORD = "texture_trial.json"
TABLE_RESULT_RECORD = "table_result.json"
SPEND_LEDGER_RECORD = "spend_ledger.json"
CAMPAIGN_RECORDS = (
    SWEEP_RECORD,
    MAC_RESOLVE_RECORD,
    CANDIDATES_RECORD,
    BOX_DETERMINISM_RECORD,
    TEXTURE_TRIAL_RECORD,
    TABLE_RESULT_RECORD,
    SPEND_LEDGER_RECORD,
)
"""Every record the report reads from `campaign/`. Any other file there is refused: it is a
measurement the report would neither print nor check."""

TABLE_HANDS = 20_000
TABLE_SEED = 777
VOID_STREETS = ("preflop", "flop", "turn", "river")
PHASE_16_TABLE = {
    "hands": 20_000,
    "seed": 777,
    "postflop_decisions": 2,
    "bets": 0,
    "showdowns": 0,
    "voided_hands": 5_365,
}
"""Phase 16's table result as `reports/phase_audits/PHASE_16_POSTFLOP_BETTING.md` published it:
two postflop decisions, both checks. A table run, not a committed file, so not re-derived here."""

_RELATIVE = 1e-9


class ReportFigureError(RuntimeError):
    """A figure the report was about to print does not re-derive from the files it came from.

    Raised before anything is written: a wrong report beside a non-zero exit is worse than no
    report, because the file is what a reviewer reads."""


def refuse(record: str, message: str) -> ReportFigureError:
    return ReportFigureError(f"{record}: {message}")


def same(one: float, two: float) -> bool:
    """Two figures that are one number, allowing only the last bits a JSON round trip may move."""
    return math.isclose(float(one), float(two), rel_tol=_RELATIVE, abs_tol=_RELATIVE)


def money(value: float) -> str:
    return f"${value:,.2f}"


def machine_record(record: str, document: Any) -> MachineRecord:
    """A machine as a record stated it, refusing one whose description is not its own fields'."""
    if not isinstance(document, Mapping):
        raise refuse(record, f"names no measured machine: {document!r}")
    fields = {key: value for key, value in document.items() if key != "description"}
    try:
        found = MachineRecord(**fields)
    except TypeError as error:
        raise refuse(record, f"the machine carries fields a machine has not: {error}") from error
    if not isinstance(found.logical_processors, int) or found.logical_processors < 1:
        raise refuse(record, f"{found.logical_processors!r} logical processors is no machine")
    if "description" in document and document["description"] != found.describe():
        raise refuse(
            record,
            f"the machine is described as {document['description']!r}, but its own fields"
            f" describe {found.describe()!r}",
        )
    return found


# --- The thread sweep


def _sweep_machine_rows(machine: Mapping[str, Any]) -> list[str]:
    found = machine_record(SWEEP_RECORD, machine.get("machine"))
    counts = list(threads.thread_counts_to_time(found.logical_processors))
    if machine.get("counts") != counts:
        raise refuse(
            SWEEP_RECORD,
            f"{found.describe()} times {counts} threads, the record says {machine.get('counts')}",
        )
    default = threads.gtopen_default_threads(found.logical_processors)
    if machine.get("gtopen_default_threads") != default:
        raise refuse(SWEEP_RECORD, f"GTOpen's default on {found.describe()} is {default}")
    if machine.get("iterations_per_stretch") != threads.ITERATIONS_PER_STRETCH:
        raise refuse(SWEEP_RECORD, f"a stretch is {threads.ITERATIONS_PER_STRETCH} iterations")
    if machine.get("repeats_per_count") != threads.REPEATS_PER_COUNT:
        raise refuse(SWEEP_RECORD, f"every count is timed {threads.REPEATS_PER_COUNT} times")
    runs = machine["runs"]
    for position, run in enumerate(runs):
        if run.get("valid", True) is not True:
            raise refuse(SWEEP_RECORD, f"run {position + 1} is marked invalid and still counted")
        if "iterations" in run and run["iterations"] != threads.ITERATIONS_PER_STRETCH:
            raise refuse(SWEEP_RECORD, f"run {position + 1} ran {run['iterations']} iterations")
        if "server_elapsed_seconds" in run and not same(
            run["seconds_per_iteration"], run["server_elapsed_seconds"] / run["iterations"]
        ):
            raise refuse(
                SWEEP_RECORD,
                f"run {position + 1}: {run['seconds_per_iteration']} seconds per iteration is not"
                f" its {run['server_elapsed_seconds']} seconds over {run['iterations']}",
            )
    pairs = [(run["threads"], run["seconds_per_iteration"]) for run in runs]
    if sorted({count for count, _ in pairs}) != counts:
        raise refuse(SWEEP_RECORD, f"the runs time {sorted({c for c, _ in pairs})}, not {counts}")
    try:
        verdict = threads.sweep_verdict(pairs)
    except ValueError as error:
        raise refuse(SWEEP_RECORD, str(error)) from error
    if machine.get("chosen_threads") != verdict.chosen_threads:
        raise refuse(
            SWEEP_RECORD,
            f"the record chose {machine.get('chosen_threads')} threads; the fastest median of its"
            f" own runs is {verdict.chosen_threads}",
        )
    stated = {row["threads"]: row for row in machine["per_count"]}
    if sorted(stated) != counts:
        raise refuse(SWEEP_RECORD, f"per_count covers {sorted(stated)}, not {counts}")
    for count in counts:
        row = stated[count]
        if not same(row["median_seconds_per_iteration"], verdict.medians[count]) or not same(
            row["spread_seconds_per_iteration"], verdict.spreads[count]
        ):
            raise refuse(SWEEP_RECORD, f"the median or spread at {count} threads is not its runs'")
    rows = [
        f"  machine: {found.describe()}",
        f"  counts timed: {', '.join(map(str, counts))} (GTOpen's default is {default}), each"
        f" {threads.REPEATS_PER_COUNT} times interleaved over {threads.ITERATIONS_PER_STRETCH}"
        " iterations",
    ]
    if "board" in machine:
        rows.append(f"  board and line timed: {machine['board']} on {machine.get('preflop_line')}")
    rows.append("  every run, in the order taken, seconds per iteration:")
    for position, (count, seconds) in enumerate(pairs):
        rows.append(f"    run {position + 1:>2}: {count:>3} threads, {seconds:.3f}")
    rows.append("  per count, median of three and spread (slowest less fastest):")
    for count in counts:
        times = ", ".join(f"{seconds:.3f}" for c, seconds in pairs if c == count)
        rows.append(
            f"    {count:>3} threads: median {verdict.medians[count]:.3f}, spread"
            f" {verdict.spreads[count]:.2f} (runs {times})"
        )
    rows.append(f"  chosen: {verdict.chosen_threads} threads, the fastest median")
    return rows


def sweep_rows(document: Mapping[str, Any]) -> list[str]:
    """Every machine's sweep, its runs, medians and spreads, and the count it chose."""
    machines = document.get("machines")
    if not isinstance(machines, list) or not machines:
        raise refuse(SWEEP_RECORD, "holds no machine's sweep")
    rows: list[str] = []
    for machine in machines:
        rows += _sweep_machine_rows(machine)
    return rows


# --- The Mac re-solve at the chosen thread count


def mac_resolve_rows(document: Mapping[str, Any], index: Mapping[str, Any]) -> list[str]:
    """Phase 16's four boards re-solved at another thread count, re-judged cell by cell."""
    found = machine_record(MAC_RESOLVE_RECORD, document.get("machine_record"))
    if document.get("machine") != found.describe():
        raise refuse(MAC_RESOLVE_RECORD, "the machine named is not the machine recorded")
    count = document.get("threads")
    if not isinstance(count, int) or count == threads.gtopen_default_threads(
        found.logical_processors
    ):
        raise refuse(
            MAC_RESOLVE_RECORD,
            f"re-solved at {count!r} threads; GTOpen's default is what the committed runs used,"
            " so a re-solve there proves nothing about thread count",
        )
    indexed = {entry["spot_key"] for entry in index["entries"]}
    cells = document.get("cells") or []
    if {cell["spot_key"] for cell in cells} != indexed:
        raise refuse(MAC_RESOLVE_RECORD, "the cells re-solved are not the index's spots")
    failures = []
    rows = [
        f"  machine: {found.describe()}, re-solved at {count} threads",
        "  phase 16's cells on the pin's tree, before decision 17's re-solve: that decision",
        "  changes the tree, never the fixed order the solver sums in, so this is not repeated",
    ]
    for cell in cells:
        name = cell["cell"]
        if cell["threads"][1] != count:
            failures.append(f"{name} ran at {cell['threads'][1]} threads")
        for field in ("iterations", "achieved_exploitability_pct_of_pot"):
            if cell[field][0] != cell[field][1]:
                failures.append(f"{name}: {field} {cell[field]}")
        if not determinism.per_combo_identical(cell["per_combo"]):
            failures.append(f"{name}: per-combo strategies differ {cell['per_combo']}")
        if cell["wall_seconds"][0] == cell["wall_seconds"][1]:
            failures.append(f"{name}: one wall clock twice, so a copy rather than a solve")
        rows.append(
            f"    {name}: {cell['iterations'][1]} iterations,"
            f" {cell['achieved_exploitability_pct_of_pot'][1]:.4f}% of pot, wall clock"
            f" {cell['wall_seconds'][0]:,.1f} s then {cell['wall_seconds'][1]:,.1f} s, peak"
            f" {cell['peak_resident_bytes'][1]:,} bytes"
        )
    reproduced = not failures and not document.get("errors")
    if document.get("reproduced") is not reproduced:
        raise refuse(
            MAC_RESOLVE_RECORD,
            f"says reproduced is {document.get('reproduced')!r}; its cells say {reproduced}"
            f" {failures}",
        )
    verdict = "reproduced exactly" if reproduced else "did not reproduce; the phase halts"
    rows.append(f"  verdict, read from every cell: {verdict} at {count} threads")
    return rows


# --- Determinism: the M4's committed record and the rented box's


def _rerun(record: str, document: Mapping[str, Any]) -> bool:
    try:
        verdict = determinism.rerun_verdict(document)
    except (ValueError, KeyError, TypeError) as error:
        raise refuse(record, str(error)) from error
    if document.get("identical") is not verdict:
        raise refuse(
            record,
            f"says identical is {document.get('identical')!r}, but its cells read {verdict}",
        )
    return verdict


def m4_determinism_rows(document: Mapping[str, Any], index: Mapping[str, Any]) -> list[str]:
    """The committed two-run record: identical or not, read from its cells, and whether its
    digests are the index's."""
    verdict = _rerun("determinism.json", document)
    if document.get("cells_compared") != len(document["cells"]):
        raise refuse("determinism.json", "cells_compared is not the cells it carries")
    held = determinism.matches_committed(document, index)
    return [
        f"  cells compared: {len(document['cells'])}, two processes against a restarted server",
        f"  both runs identical, read cell by cell: {'yes' if verdict else 'no'}",
        f"  the committed index's strategy digests are this record's: {'yes' if held else 'no'}",
    ]


def box_determinism_rows(document: Mapping[str, Any], index: Mapping[str, Any]) -> list[str]:
    """The rented box's re-run, and the separate finding of whether it matched the M4."""
    found = machine_record(BOX_DETERMINISM_RECORD, document.get("machine"))
    verdict = _rerun(BOX_DETERMINISM_RECORD, document)
    count = document.get("threads")
    at = f"at {count} threads" if count is not None else "thread count not in this record"
    if verdict:
        rows = [f"  {found.describe()}, {at}: {BOX_REPEATED} on every cell"]
    else:
        rows = [
            f"  {found.describe()}, {at}: {BOX_DID_NOT_REPEAT}; this is a halt, and Taylor is"
            " asked before anything else runs"
        ]
    m4 = M4_MATCH if determinism.matches_committed(document, index) else M4_MISMATCH
    rows.append(f"  separate finding, not a pass condition: {m4}")
    return rows


# --- The candidate machines


def candidate_rows(document: Mapping[str, Any], campaign_bar_bytes: int) -> list[str]:
    """The candidates re-ranked from their own fields against the record's bar, which may not sit
    below the largest arena the tree walk found over every admitted line."""
    bar = document["memory_bar_bytes"]
    if not isinstance(bar, int) or bar < campaign_bar_bytes:
        raise refuse(
            CANDIDATES_RECORD,
            f"ranks against a memory bar of {bar!r} bytes, below the campaign's largest planned"
            f" arena of {campaign_bar_bytes:,} bytes",
        )
    offered = [costs.Candidate.from_document(entry) for entry in document["candidates"]]
    try:
        ranking = costs.rank_candidates(
            offered,
            memory_bar_bytes=bar,
            ceiling_fraction=document["ceiling_fraction"],
            concurrent_solves=document["concurrent_solves"],
        )
    except ValueError as error:
        raise refuse(CANDIDATES_RECORD, str(error)) from error
    ranked = [candidate.name for candidate in ranking.ranked]
    if list(document["ranked"]) != ranked:
        raise refuse(CANDIDATES_RECORD, f"ranks {document['ranked']}; its candidates rank {ranked}")
    if set(document["excluded"]) != set(ranking.excluded):
        raise refuse(
            CANDIDATES_RECORD,
            f"excludes {sorted(document['excluded'])}; the bar excludes {sorted(ranking.excluded)}",
        )
    stated = document["cost_per_solved_flop_usd"]
    if set(stated) != set(ranked):
        raise refuse(CANDIDATES_RECORD, f"prices {sorted(stated)}, ranks {ranked}")
    for name, cost in ranking.cost_per_solved_flop_usd.items():
        if not same(stated[name], cost):
            raise refuse(
                CANDIDATES_RECORD,
                f"{name} costs {stated[name]} a solved flop; price times its billed stretch is"
                f" {cost}",
            )
    rows = [
        f"  memory bar ranked against: {bar:,} bytes at the {ranking.ceiling_fraction:.2f}"
        f" ceiling, {ranking.concurrent_solves} solve at a time",
    ]
    for position, candidate in enumerate(ranking.ranked, start=1):
        rows.append(
            f"  cost per solved flop: {money(ranking.cost_per_solved_flop_usd[candidate.name])} on"
            f" {candidate.name}, rank {position}, {money(candidate.price_per_hour_usd)} an hour"
            f" for {costs.billed_seconds_per_flop(candidate):,.0f} billed seconds"
        )
    for name, reason in ranking.excluded.items():
        rows.append(f"  excluded, never ranked: {name}, {reason}")
    return rows


# --- The spend ledgers


def ledger_rows(document: Mapping[str, Any]) -> list[str]:
    """Every ledger's total re-added from its entries, beside the cap it counts against."""
    ledgers = document.get("ledgers")
    if not isinstance(ledgers, Mapping) or not ledgers:
        raise refuse(SPEND_LEDGER_RECORD, "holds no ledger")
    rows: list[str] = []
    for name, entry in ledgers.items():
        try:
            ledger = costs.SpendLedger.from_document(entry)
        except (ValueError, KeyError, TypeError) as error:
            raise refuse(SPEND_LEDGER_RECORD, f"{name}: {error}") from error
        if name == "benchmark" and ledger.cap_usd != costs.BENCHMARK_CAP_USD:
            raise refuse(
                SPEND_LEDGER_RECORD,
                f"the benchmark ledger counts against {money(ledger.cap_usd)}, not the"
                f" {money(costs.BENCHMARK_CAP_USD)} Taylor ruled",
            )
        if ledger.past_cap:
            raise refuse(
                SPEND_LEDGER_RECORD,
                f"{name}: {ledger.summary()}; work halts at a cap, so a ledger past it records the"
                " rule broken and is not published as a total",
            )
        rows.append(f"  {name}: {ledger.summary()}")
        for item in ledger.entries:
            rows.append(
                f"    {item['machine']}: {item['hours']:g} hours at"
                f" {money(item['price_per_hour_usd'])} an hour, {item['what']}"
            )
    return rows


# --- The six texture solves


def texture_rows(document: Mapping[str, Any]) -> list[str]:
    """One closed line's cost projected from six group solves, re-weighted by class counts."""
    first = lines.ADMITTED_LINES[0]
    if document.get("line") != first:
        raise refuse(
            TEXTURE_TRIAL_RECORD,
            f"the trial boards are on {document.get('line')}; they belong on the first admitted"
            f" line, {first}",
        )
    found = machine_record(TEXTURE_TRIAL_RECORD, document.get("machine"))
    count = document.get("threads")
    if not isinstance(count, int) or count < 1:
        raise refuse(TEXTURE_TRIAL_RECORD, f"names no thread count: {count!r}")
    groups = document["groups"]
    if set(groups) != set(textures.TEXTURE_GROUPS):
        raise refuse(
            TEXTURE_TRIAL_RECORD,
            f"prices {sorted(groups)}; a line's projection needs all of {textures.TEXTURE_GROUPS}",
        )
    for group, entry in groups.items():
        actual = textures.texture_group(entry["board"])
        if actual != group:
            raise refuse(TEXTURE_TRIAL_RECORD, f"{entry['board']} is {actual}, filed as {group}")
    projected = textures.project_line_cost({g: groups[g]["cost_usd"] for g in groups})
    if not same(document["projected_line_cost_usd"], projected):
        raise refuse(
            TEXTURE_TRIAL_RECORD,
            f"projects {document['projected_line_cost_usd']}; weighted by class it is {projected}",
        )
    classes = textures.group_class_counts()
    rows = [f"  {found.describe()}, at {count} threads, on {first}"]
    for group in textures.TEXTURE_GROUPS:
        entry = groups[group]
        rows.append(
            f"    {group}: {''.join(entry['board'])}, {money(entry['cost_usd'])} a class,"
            f" times {classes[group]:,} classes"
        )
    rows.append(f"  projected cost of one closed line: {money(projected)}")
    return rows


# --- The table re-run


def table_rows(document: Mapping[str, Any]) -> list[str]:
    """The table re-run on phase 16's terms, its voids split by street, beside phase 16's."""
    found = machine_record(TABLE_RESULT_RECORD, document.get("machine"))
    if document.get("hands") != TABLE_HANDS or document.get("seed") != TABLE_SEED:
        raise refuse(
            TABLE_RESULT_RECORD,
            f"{document.get('hands')!r} hands at seed {document.get('seed')!r}; phase 16's terms"
            f" are {TABLE_HANDS:,} hands at seed {TABLE_SEED}",
        )
    split = document["voided_by_street"]
    if list(split) != list(VOID_STREETS):
        raise refuse(TABLE_RESULT_RECORD, f"splits voids over {list(split)}, not {VOID_STREETS}")
    if any(not isinstance(split[street], int) or split[street] < 0 for street in VOID_STREETS):
        raise refuse(TABLE_RESULT_RECORD, f"a void count is not a count: {split}")
    if sum(split.values()) != document["voided_hands"]:
        raise refuse(
            TABLE_RESULT_RECORD,
            f"{document['voided_hands']:,} voided hands; its streets add to {sum(split.values())}",
        )
    if split["river"]:
        raise refuse(
            TABLE_RESULT_RECORD,
            f"{split['river']:,} hands voided on the river; every turn decision refuses this"
            " phase, so a hand reaches the river only all-in, as a showdown",
        )
    by_street = ", ".join(f"{street} {split[street]:,}" for street in VOID_STREETS)
    old = PHASE_16_TABLE
    return [
        f"  {found.describe()}: {TABLE_HANDS:,} hands, seed {TABLE_SEED}",
        f"  postflop decisions: {document['postflop_decisions']:,} (phase 16:"
        f" {old['postflop_decisions']}, both checks)",
        f"  bets: {document['bets']:,} (phase 16: {old['bets']})",
        f"  showdowns: {document['showdowns']:,} (phase 16: {old['showdowns']})",
        f"  voided hands: {document['voided_hands']:,}, by street {by_street} (phase 16:"
        f" {old['voided_hands']:,})",
        "  the bot does not play the turn or river in this phase, so a hand that reaches a turn"
        " still voids; this measures flop coverage and closure, never a win rate",
    ]


def unread_records(present: Sequence[str]) -> list[str]:
    """Files under `campaign/` this report neither prints nor checks."""
    return sorted(name for name in present if name not in CAMPAIGN_RECORDS)
