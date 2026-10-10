"""What this machine holds of the committed flop solve, and how a table's chips address it.

The fetched cells, the preflop lines they cover with the prices they were solved at, the keys
the index lists but this clone has not fetched, and the one conversion that turns a real bet in
chips into the menu entry a committed key names. Everything here is about the *committed side*
of a lookup; `postflop_betting` owns the walk that uses it and the refusals it produces.

**Absence and corruption are different.** A missing sample directory or index is an empty
library, because a clone that has not fetched the artifact genuinely holds nothing and the
strategy's answer there is a refusal naming that. A file that is present and disagrees with
itself still raises out of the importer, against a file nobody has played yet.

**What a machine has fetched is read from the folder it was fetched into, and only as far as a
committed manifest lists it.** Each manifest names a line's closed boards, and every flop decision
point of those boards, for both seats, is a key this machine either holds or refuses as not
fetched. `require_fetched` decides which, so an object altered on disk since the fetch reads as
not fetched rather than being played, and an object no manifest lists is never read at all. The
fetched folder is an argument and defaults to none, a fresh clone: a library built from whatever
the disk happens to hold would make the gate's verdict a fact about the machine.

Chips are the table's unit and big blinds are the cell's, so `BIG_BLIND_CHIPS` fixes the scale
and each cell's own `blind_structure` supplies every ratio under it.

**What this module reads out of the committed JSON rather than off `PostflopCell`.**
`PostflopCell` does not carry `table_size`, `stack_depth_bb` or `blind_structure`, and without
those three there is no table to rebuild: nothing says how many seats there are, how deep they
sat, or how many chips a big blind is. They are read back out of the same file the importer
read, and everything poker-bearing still comes off the imported cell. That split is a gap in
the cell record rather than a preference here.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from poker_training_bot.poker_core.positions import seat_positions
from poker_training_bot.solver_artifacts.postflop_artifact import (
    INDEX_PATH,
    INVALID_VALUE_CODE,
    SAMPLE_DIR,
    PostflopArtifactError,
    PostflopCell,
    _build_cell,
    import_postflop_index,
    import_postflop_sample,
    indexed_spot_keys,
)
from poker_training_bot.solver_artifacts.postflop_fetch import FetchError, require_fetched
from poker_training_bot.solver_artifacts.postflop_key import (
    FLOP_RAISE_MENU,
    MENU_FRACTION_TOLERANCE,
    FlopAction,
    PreflopLine,
    canonical_board,
    match_menu_fraction,
)
from poker_training_bot.solver_artifacts.postflop_lines import (
    flop_spot_keys,
    heads_up_seats,
    preflop_line_for,
)
from poker_training_bot.solver_artifacts.postflop_manifest import (
    CLOSED,
    MANIFEST_DIR,
    load_manifests,
    manifest_errors,
    read_strict_json,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.solve_conditions import (
    BlindStructure,
    parse_blind_structure,
)
from poker_training_bot.solver_artifacts.strict_json import ArtifactImportError
from poker_training_bot.strategy.contract import StrategyQuery

BIG_BLIND_CHIPS = 100
"""Chips in one big blind. 100 is what every committed fixture and every simulator profile in
this repo uses, and it is the scale that makes the cell's 0.5bb small blind a whole 50 chips."""

SIZED_ACTIONS = frozenset({"bet", "raise"})
"""The two actions that carry a size, named once so the table side and the cell side agree."""


@dataclass(frozen=True)
class CommittedTable:
    """One committed cell plus the three table facts the cell record does not carry."""

    cell: PostflopCell
    table_size: int
    stack_depth_bb: int
    blinds: BlindStructure


def _chips(value_bb: float) -> int:
    return round(value_bb * BIG_BLIND_CHIPS)


def committed_tables(directory: Path | str = SAMPLE_DIR) -> tuple[CommittedTable, ...]:
    """Every committed sample cell, paired with the table shape its own file declares.

    An absent directory is an empty result rather than an error: a clone that has not fetched
    the artifact holds no committed spots, which is a fact about the machine. A directory that
    is present and unreadable still raises, through the importer.
    """
    root = Path(directory)
    if not root.is_dir():
        return ()
    cells = {cell.spot_key: cell for cell in import_postflop_sample(root)}
    built: list[CommittedTable] = []
    for path in sorted(item for item in root.glob("*.json") if item.is_file()):
        payload = json.loads(path.read_text(encoding="utf-8"))
        built.append(_table(cells[str(payload["spot_key"])], payload, str(path)))
    return tuple(sorted(built, key=lambda table: table.cell.spot_key))


def _table(cell: PostflopCell, payload: Mapping[str, Any], origin: str) -> CommittedTable:
    return CommittedTable(
        cell=cell,
        table_size=int(payload["table_size"]),
        stack_depth_bb=int(payload["stack_depth_bb"]),
        blinds=parse_blind_structure(payload, origin),
    )


def fetched_tables(path: Path) -> tuple[CommittedTable, ...]:
    """Every cell of one fetched flop object, `{"cells": [...]}`, through the importer's own
    re-derivation. The fetch checked which decision points the object holds and its digest;
    whether each cell is sound is the importer's question, and an unsound one raises here."""
    origin = str(path)
    document = read_strict_json(path.read_bytes(), origin)
    if not isinstance(document, dict) or set(document) != {"cells"}:
        raise PostflopArtifactError(INVALID_VALUE_CODE, f"{origin}: a flop object is {{cells: []}}")
    built: list[CommittedTable] = []
    for index, payload in enumerate(document["cells"]):
        where = f"{origin}#cells[{index}]"
        try:
            cell = _build_cell(payload, where)
        except ArtifactImportError as error:
            raise PostflopArtifactError(error.code, error.message) from error
        built.append(_table(cell, payload, where))
    return tuple(built)


# --------------------------------------------------------------------------- #
# The library: what is held here, and what is only listed
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CoveredLine:
    """One completed preflop line the committed solve covers, with the prices it was solved at.

    The line is carried as the `PreflopLine` the cell was built from rather than read back out
    of the key, because the key is compared and never parsed: `postflop_key` publishes no reader
    that takes one apart and a parser here would be a second answer to "what spot is this". Its
    pot and effective stack are the line's own nominal ones, which keeps a cell findable when a
    hand that opened to 2.25bb looks up a cell solved at 2.5bb.
    """

    preflop_line: PreflopLine
    boards: frozenset[tuple[str, ...]]

    @property
    def pot_bb(self) -> float:
        return self.preflop_line.pot_bb

    @property
    def effective_stack_bb(self) -> float:
        return self.preflop_line.effective_stack_bb

    @property
    def preflop_actions(self) -> tuple[PreflopAction, ...]:
        return self.preflop_line.actions


@dataclass(frozen=True)
class PostflopLibrary:
    """The cells held here - committed and fetched - the lines and boards they cover per seat, and
    the keys an index or manifest lists that this machine does not hold. Frozen and built of
    tuples, so a strategy holding one stays field-equal and two built alike answer identically."""

    cells: tuple[PostflopCell, ...] = ()
    lines: tuple[CoveredLine, ...] = ()
    listed: frozenset[str] = frozenset()

    def cell_for(self, spot_key_text: str) -> PostflopCell | None:
        """The fetched cell for one derived key, or None. A linear walk over three cells rather
        than an index: a dict field would make this record unhashable for the sake of a lookup
        that is already shorter than the hash."""
        for cell in self.cells:
            if cell.spot_key == spot_key_text:
                return cell
        return None


@cache
def load_library(
    fetched_root: Path | None = None, manifest_dir: Path = MANIFEST_DIR
) -> PostflopLibrary:
    """Read the committed sample and index, the manifests, and what `fetched_root` holds of the
    boards they list, once per process and argument pair.

    Cached because a simulation asks thousands of questions of the same files and nothing here
    writes. `fetched_root` is the folder a fetch wrote into, `None` for a clone that fetched
    nothing; `manifest_dir` is the committed manifests by default. A line's covered boards, per
    seat, are its sample cells' boards and its manifest's closed boards, so a board refusal is
    scoped to the line and seat that asked."""
    tables = list(committed_tables(SAMPLE_DIR))
    listed: set[str] = set()
    if INDEX_PATH.is_file():
        listed |= indexed_spot_keys(import_postflop_index(INDEX_PATH))
    boards: dict[PreflopLine, set[tuple[str, ...]]] = {}
    for line, manifest in _manifests(manifest_dir).items():
        closed = [
            tuple(entry["board"]) for entry in manifest["boards"] if entry["status"] == CLOSED
        ]
        for seat in heads_up_seats(line):
            boards.setdefault(preflop_line_for(line, seat), set()).update(closed)
        held = _fetched(manifest, fetched_root)
        if held is None:
            listed.update(key for board in closed for key in flop_spot_keys(line, board))
            continue
        for path in held.values():
            tables.extend(fetched_tables(path))
    cells = tuple(table.cell for table in sorted(tables, key=lambda table: table.cell.spot_key))
    held_keys = {cell.spot_key for cell in cells}
    for cell in cells:
        boards.setdefault(cell.preflop_line, set()).add(canonical_board(cell.board))
    lines = tuple(
        CoveredLine(preflop_line=line, boards=frozenset(held))
        for line, held in sorted(boards.items(), key=lambda pair: pair[0].rendered)
    )
    return PostflopLibrary(cells, lines, frozenset(listed - held_keys))


def _manifests(manifest_dir: Path) -> dict[str, dict[str, Any]]:
    """Every manifest in the folder, each refused unless it holds together. An absent folder is
    no manifest, the library's rule for every absent artifact; a malformed one raises."""
    if not Path(manifest_dir).is_dir():
        return {}
    found = load_manifests(Path(manifest_dir))
    for line, manifest in found.items():
        errors = manifest_errors(manifest)
        if errors:
            raise ValueError(f"the manifest for {line} fails its own checks: {errors}")
    return found


def _fetched(
    manifest: Mapping[str, Any], fetched_root: Path | None
) -> dict[tuple[str, ...], Path] | None:
    """Where each closed board's flop object sits on this machine, or `None` when the line is not
    fetched here: nothing on disk, an index that is not the manifest's, or an object changed since
    the fetch checked it. Every one of those is a board the bot must refuse rather than play."""
    if fetched_root is None:
        return None
    try:
        return require_fetched(manifest, Path(fetched_root), street="flop")
    except FetchError:
        return None


# --------------------------------------------------------------------------- #
# From a table's chips to the menu a committed key names
# --------------------------------------------------------------------------- #


def flop_action_line(
    query: StrategyQuery,
) -> tuple[tuple[FlopAction, ...] | None, tuple[tuple[str, str], ...]]:
    """The flop so far as committed actions, or `None` and the detail naming what did not match.

    **A bet is matched by pot fraction** against the pot as it stood when it went in, decision 14's
    rule: 33% of a 550-chip pot is 181.5 and no dealer pushes half a chip. A size matching no entry
    inside the tolerance is a miss, never snapped to the nearer one. The key renders the percent -
    `@33` - and the menu speaks fractions - `0.33` - so the conversion is `fraction * 100`.

    **A raise is named by its multiplier** (decision 16): the entry of `FLOP_RAISE_MENU` whose
    raise-to, that multiple of the level faced, is within `MENU_FRACTION_TOLERANCE` of the real
    raise-to as a share of the pot. The width is decision 14's, borrowed, since no ruling gives a
    raise its own: `THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`. The menu is the
    configured one rather than read off whichever cells happen to be committed, so the bot can name
    its own raise whatever this machine holds.

    The refusal itself belongs to the caller: this returns the numbers and the strategy names the
    code, so the vocabulary stays in one place.
    """
    seats = tuple(seat for seat, _ in query.stacks)
    labels = seat_positions(seats, query.button_seat)
    pot = query.pot - sum(state.street_bet for state in query.seat_states)
    if pot <= 0:
        # A flop whose pot is entirely this street's own bets describes no preflop line, so
        # there is nothing for a fraction to be a fraction of. Miss rather than divide.
        return None, (("pot_before_the_flop", "0"),)
    street_bet: dict[int, int] = {}
    level = 0
    built: list[FlopAction] = []
    for entry in query.postflop_actions:
        standing = street_bet.get(entry.seat, 0)
        amount = entry.amount or 0
        if entry.action in SIZED_ACTIONS:
            if entry.action == "bet":
                fraction = match_menu_fraction(amount - standing, pot)
                step = (
                    None
                    if fraction is None
                    else FlopAction(labels[entry.seat], "bet", fraction * 100)
                )
            else:
                multiple = _menu_multiplier(amount, level, pot)
                step = (
                    None
                    if multiple is None
                    else FlopAction(labels[entry.seat], "raise", multiplier=multiple)
                )
            if step is None:
                return None, (
                    ("action", entry.action),
                    ("pct_of_pot", str(round(100 * (amount - standing) / pot))),
                )
            built.append(step)
            pot += amount - standing
            level = amount
            street_bet[entry.seat] = level
        else:
            if entry.action == "call":
                pot += level - standing
                street_bet[entry.seat] = level
            built.append(FlopAction(labels[entry.seat], entry.action))
    return tuple(built), ()


def _menu_multiplier(raise_to: int, faced: int, pot: int) -> float | None:
    """The menu multiplier a chip raise-to is, or `None`: judged in pot fraction against the raise
    that multiplier would make, so one width governs bets and raises alike."""
    if faced <= 0:
        return None
    for entry in FLOP_RAISE_MENU:
        if abs(raise_to - entry * faced) / pot <= MENU_FRACTION_TOLERANCE:
            return entry
    return None
