"""What a committed flop size means, and the one unit that survives the trip to a table.

Split out of `postflop_artifact` at the 500-line cap, and it is a real seam rather than a place
to put spare lines: the importer's subject is whether a file says what it claims, and this one's
is whether a number means the same thing on both sides of the wire.

**The trip, and where it used to break.** A cell stores its sized actions in big blinds. Those
big blinds are a *nominal* size against the *nominal* pot the key names - decision 10's band
admits a real preflop price 20% either side of the one the cell was solved at, so the `@2.5`
cell's 5.5bb pot is really anywhere from 4.5bb to 6.5bb at the table. Played as a flat chip
count the cell's 33% continuation bet is 40.44% of the pot after a 2.0bb open and 28.00% after a
3.0bb one, and decision 14 matches a faced bet by **real** pot fraction inside 0.05 - so the bot
put in a bet its own matcher then refused under `flop-size-off-the-committed-menu`, blaming the
other seat, on 46 of the corpus's 174 heads-up single-raised flops. Eighteen more survived only
because `abs(182/650 - 0.33)` happens to evaluate to `0.04999999999999999`.

So the unit that travels is the **fraction of the pot the cell itself decides into**, priced
once at import and converted back at the table through `menu_size_chips`, which is decision 14's
own rounding. Both ends of the trip then use one rule and cannot drift.

**And a committed bet is checked against the menu it claims to come from.** Decision 11
configures the flop at `33 75`; nothing checked that a cell's own size was one of those, so a
cell offering 3.0bb into its own 5.5bb pot - 54.5%, on neither entry - imported clean, and the
bot would have bet it and refused it. A **raise** is not checked, and that is a boundary rather
than an omission: decision 11 configures the raise as `2.5x` the bet it answers, which is not a
pot fraction at all, and decision 14 ruled the bet menu only.
`THE-FLOP-RAISE-TOLERANCE-IS-BORROWED-FROM-THE-BET-MENU-RULING`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from poker_training_bot.solver_artifacts.postflop_key import (
    FLOP_BET_MENU,
    FlopAction,
    match_menu_fraction,
)

SIZED_ACTIONS = frozenset({"bet", "raise"})
"""The two actions that carry a size. `THE-SIZED-ACTION-SET-IS-DEFINED-FOUR-TIMES` owns the
copies; this module is where the size itself is priced, so it holds one of them."""


@dataclass(frozen=True)
class CellAction:
    """One entry on a committed cell's action menu, welded to the size it is played at.

    **A name is not an identity, and until 2026-09-16 the schema assumed it was.** Decision 11's
    flop menu is `33 75`, so a cell offers two actions both called `bet` - 1.815bb and 4.125bb
    into a 5.5bb pot - and they were stored as one positional list of names beside a parallel
    array of sizes. Every lookup by name took the first: over every committed spot the bot bet
    33% of pot on all ten of its bets, while 29 of that cell's 160 hand classes weighted the 75%
    bet above 0.8 and one weighted it 0.969. Half the ruled menu was unreachable and no field on
    the cell could express the difference.

    Three units meet on this record and no two are the same number, so each has its own field.
    `size_bb` is the level hero's street contribution goes **to**, the solver's own unit and the
    one `check_size_is_playable` compares. `fraction` is that size as a share of the pot the cell
    decides into, filled in by `price_menu` at import; it is what travels to a table, because the
    nominal pot a key names and the real pot in front of hero differ by decision 10's band. The
    **percent** a spot key renders - `@33` - is neither, and lives on `FlopAction`.
    """

    name: str
    size_bb: float | None = None
    fraction: float | None = None

    @property
    def sized(self) -> bool:
        """Whether this entry carries a size at all, which is a fact about its name."""
        return self.name in SIZED_ACTIONS

    @property
    def label(self) -> str:
        """This entry as an audit line names it, so two bets on one menu read as two actions.

        The size is written in the cell's own big blinds rather than converted, because a decision
        record is evidence about the cell and a second conversion here is a second place to drift.
        """
        return self.name if self.size_bb is None else f"{self.name}({self.size_bb:g}bb)"

    @property
    def menu_entry(self) -> float | None:
        """Which ruled menu entry a table would read this size back as, or `None` when unsized.

        Taken against a pot of one, because `fraction` is already the ratio
        `match_menu_fraction` compares. An entry that matches nothing answers with its own
        fraction rather than with `None`, so it stays distinct from every other such entry: a
        **raise** is on no menu at all, decision 14 having ruled the bet menu only, and
        `FLOP_BET_MENU` is the flop's, which the turn and river's `66 125` is not.
        """
        if self.fraction is None or self.name != "bet":
            return self.fraction
        return match_menu_fraction(self.fraction, 1.0) or self.fraction


def pot_before_hero_bb(pot_bb: float, flop_actions: Sequence[FlopAction]) -> float:
    """The pot hero decides into, in big blinds, carried through the committed flop line.

    A flop size is a percent of the pot **as it stood when it went in**, so the pot is carried
    forward rather than taken once at the start. The same walk `postflop_spot_queries._flop_street`
    runs in chips and `postflop_committed.flop_action_line` runs against a table's own history;
    `ONE-FLOP-LINE-WALK-IS-WRITTEN-IN-BOTH-DIRECTIONS` owns the duplication."""
    pot = float(pot_bb)
    level = 0.0
    street: dict[str, float] = {}
    for entry in flop_actions:
        standing = street.get(entry.position, 0.0)
        if entry.action in SIZED_ACTIONS:
            added = pot * float(entry.size_pct or 0.0) / 100.0
            pot += added
            level = standing + added
            street[entry.position] = level
        elif entry.action == "call":
            pot += level - standing
            street[entry.position] = level
    return pot


def price_menu(
    entries: Sequence[Mapping[str, Any]],
    hero_street_bet_bb: float,
    pot_before_bb: float,
) -> tuple[CellAction, ...]:
    """One committed action menu as records, each sized entry priced against the cell's own pot.

    Takes the shape-checked entries the importer's own reader produces - `path`, `action` and
    `size` - rather than two sequences to be lined up, because lining two sequences up by
    position is the defect `CellAction` exists to remove and doing it here would reintroduce it
    one layer down.

    Raises `ValueError` naming the offence, which the importer turns into its own refusal code so
    the file and the cause travel together. Four of them: a pot nothing can be a fraction of, an
    action whose size does not follow from what it is, a size that adds nothing over what hero
    already has out, and a bet that is on no menu entry. A fifth - two entries a table could not
    tell apart - belongs to the importer, which holds the refusal codes.
    """
    if pot_before_bb <= 0:
        raise ValueError(f"the cell decides into a pot of {pot_before_bb}bb, which prices nothing")
    priced: list[CellAction] = []
    for entry in entries:
        action = CellAction(str(entry["action"]), entry["size"])
        if action.sized != (action.size_bb is not None):
            carries = "carries no size of its own" if action.sized else "carries a size"
            raise ValueError(f"{entry['path']} is a {action.name!r} and {carries}")
        if action.size_bb is None:
            priced.append(action)
            continue
        added = float(action.size_bb) - float(hero_street_bet_bb)
        if added <= 0:
            raise ValueError(
                f"a committed {action.name} of {action.size_bb}bb adds nothing over the"
                f" {hero_street_bet_bb}bb hero already has out on this street"
            )
        if action.name == "bet" and match_menu_fraction(added, pot_before_bb) is None:
            raise ValueError(
                f"a committed bet of {added}bb into a {pot_before_bb}bb pot is"
                f" {100 * added / pot_before_bb:.1f}% of it, which is no entry on the"
                f" {list(FLOP_BET_MENU)} menu the solve was configured with, so the bot would"
                " make a bet its own matcher refuses"
            )
        priced.append(CellAction(action.name, action.size_bb, added / pot_before_bb))
    return tuple(priced)
