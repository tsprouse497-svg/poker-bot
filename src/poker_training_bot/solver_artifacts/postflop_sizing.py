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

from collections.abc import Sequence

from poker_training_bot.solver_artifacts.postflop_key import (
    FLOP_BET_MENU,
    FlopAction,
    match_menu_fraction,
)

SIZED_ACTIONS = frozenset({"bet", "raise"})
"""The two actions that carry a size. `THE-SIZED-ACTION-SET-IS-DEFINED-FOUR-TIMES` owns the
copies; this module is where the size itself is priced, so it holds one of them."""


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


def committed_bet_fractions(
    actions: Sequence[str],
    sizes: Sequence[float],
    hero_street_bet_bb: float,
    pot_before_bb: float,
) -> tuple[float, ...]:
    """Each committed sized action as a fraction of the pot the cell decides into.

    Raises `ValueError` naming the offence, which the importer turns into its own refusal code so
    the file and the cause travel together. Three of them: a pot nothing can be a fraction of, a
    size that adds nothing over what hero already has out, and a bet that is on no menu entry."""
    if pot_before_bb <= 0:
        raise ValueError(f"the cell decides into a pot of {pot_before_bb}bb, which prices nothing")
    priced: list[float] = []
    sized = [name for name in actions if name in SIZED_ACTIONS]
    for name, size in zip(sized, sizes, strict=True):
        added = float(size) - float(hero_street_bet_bb)
        if added <= 0:
            raise ValueError(
                f"a committed {name} of {size}bb adds nothing over the"
                f" {hero_street_bet_bb}bb hero already has out on this street"
            )
        if name == "bet" and match_menu_fraction(added, pot_before_bb) is None:
            raise ValueError(
                f"a committed bet of {added}bb into a {pot_before_bb}bb pot is"
                f" {100 * added / pot_before_bb:.1f}% of it, which is no entry on the"
                f" {list(FLOP_BET_MENU)} menu the solve was configured with, so the bot would"
                " make a bet its own matcher refuses"
            )
        priced.append(added / pot_before_bb)
    return tuple(priced)
