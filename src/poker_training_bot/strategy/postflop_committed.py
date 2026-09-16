"""What this machine holds of the committed flop solve, and how a table's chips address it.

The fetched cells, the preflop lines they cover with the prices they were solved at, the keys
the index lists but this clone has not fetched, and the one conversion that turns a real bet in
chips into the menu entry a committed key names. Everything here is about the *committed side*
of a lookup; `postflop_betting` owns the walk that uses it and the refusals it produces.

**Absence and corruption are different.** A missing sample directory or index is an empty
library, because a clone that has not fetched the artifact genuinely holds nothing and the
strategy's answer there is a refusal naming that. A file that is present and disagrees with
itself still raises out of the importer, against a file nobody has played yet.

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
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from poker_training_bot.poker_core.positions import seat_positions
from poker_training_bot.solver_artifacts.postflop_artifact import (
    INDEX_PATH,
    SAMPLE_DIR,
    PostflopCell,
    import_postflop_index,
    import_postflop_sample,
    indexed_spot_keys,
)
from poker_training_bot.solver_artifacts.postflop_key import (
    MENU_FRACTION_TOLERANCE,
    FlopAction,
    PreflopLine,
    canonical_board,
    match_menu_fraction,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.solve_conditions import (
    BlindStructure,
    parse_blind_structure,
)
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
        cell = cells[str(payload["spot_key"])]
        built.append(
            CommittedTable(
                cell=cell,
                table_size=int(payload["table_size"]),
                stack_depth_bb=int(payload["stack_depth_bb"]),
                blinds=parse_blind_structure(payload, str(path)),
            )
        )
    return tuple(sorted(built, key=lambda table: table.cell.spot_key))


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
    """The fetched cells, the lines they cover, the keys the index lists, and the flop raise
    sizes the fetched cells declare. Frozen and built of tuples, so a strategy holding one stays
    field-equal and two built from the same repo answer identically."""

    cells: tuple[PostflopCell, ...] = ()
    lines: tuple[CoveredLine, ...] = ()
    listed: frozenset[str] = frozenset()
    raise_fractions: tuple[float, ...] = ()

    def cell_for(self, spot_key_text: str) -> PostflopCell | None:
        """The fetched cell for one derived key, or None. A linear walk over three cells rather
        than an index: a dict field would make this record unhashable for the sake of a lookup
        that is already shorter than the hash."""
        for cell in self.cells:
            if cell.spot_key == spot_key_text:
                return cell
        return None


@cache
def load_library() -> PostflopLibrary:
    """Read the committed sample and index once per process.

    Cached because a simulation asks thousands of questions of the same three files and the
    answer cannot change inside a run: nothing here writes and the library is frozen.
    """
    tables = committed_tables(SAMPLE_DIR)
    if not tables:
        return PostflopLibrary()
    cells = tuple(table.cell for table in tables)
    grouped: dict[PreflopLine, list[PostflopCell]] = {}
    for cell in cells:
        grouped.setdefault(cell.preflop_line, []).append(cell)
    lines = tuple(
        CoveredLine(
            preflop_line=line,
            boards=frozenset(canonical_board(cell.board) for cell in held),
        )
        for line, held in sorted(grouped.items(), key=lambda pair: pair[0].rendered)
    )
    fractions = sorted(
        {
            float(entry.size_pct or 0.0) / 100.0
            for cell in cells
            for entry in cell.flop_actions
            if entry.action == "raise"
        }
    )
    listed = frozenset()
    if INDEX_PATH.is_file():
        listed = indexed_spot_keys(import_postflop_index(INDEX_PATH))
    return PostflopLibrary(cells, lines, listed, tuple(fractions))


# --------------------------------------------------------------------------- #
# From a table's chips to the menu a committed key names
# --------------------------------------------------------------------------- #


def flop_action_line(
    query: StrategyQuery, raise_fractions: tuple[float, ...]
) -> tuple[tuple[FlopAction, ...] | None, tuple[tuple[str, str], ...]]:
    """The flop so far as committed actions, or `None` and the detail naming what did not match.

    **The unit trap, carried in two places at once.** A key renders a size as a percent - `@33` -
    and the menu speaks fractions - `0.33` - so the conversion is `fraction * 100` and neither
    unit can be normalised away.

    A chip bet is matched by pot fraction against the pot **as it stood when the bet went in**,
    which is decision 14's rule and why a 550-chip pot answers a 180 bet at all: 33% of 550 is
    181.5 and no dealer pushes half a chip. A size matching no entry inside the tolerance is a
    miss; it is never snapped to the nearer one, and a bet exactly halfway between two entries
    has no nearer one to snap to.

    A **raise** is matched against the sizes the committed cells declare rather than against the
    bet menu, because decision 11 configures the solve's raise as `2.5x` and decision 14 ruled
    only the bet menu. An unmatched raise misses. That reading is this module's own.

    The refusal itself belongs to the caller: this returns the numbers and the strategy names
    the code, so the vocabulary stays in one place.
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
        if entry.action in SIZED_ACTIONS:
            added = (entry.amount or 0) - standing
            fraction = _menu_fraction(entry.action, added, pot, raise_fractions)
            if fraction is None:
                return None, (
                    ("action", entry.action),
                    ("pct_of_pot", str(round(100 * added / pot))),
                )
            built.append(FlopAction(labels[entry.seat], entry.action, fraction * 100))
            pot += added
            level = entry.amount or 0
            street_bet[entry.seat] = level
        else:
            if entry.action == "call":
                pot += level - standing
                street_bet[entry.seat] = level
            built.append(FlopAction(labels[entry.seat], entry.action))
    return tuple(built), ()


def _menu_fraction(
    action: str, added: int, pot: int, raise_fractions: tuple[float, ...]
) -> float | None:
    if action == "bet":
        return match_menu_fraction(added, pot)
    fraction = added / pot
    for entry in raise_fractions:
        if abs(fraction - entry) <= MENU_FRACTION_TOLERANCE:
            return entry
    return None
