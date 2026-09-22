"""The postflop spot vocabulary: what a flop spot key says, and the one collapse it makes.

A sibling of `spot_key`, not an extension of it. The preflop key answers "which preflop spot
is this"; this one answers "which flop spot is this", and carries the whole preflop line rather
than compressing it. What is borrowed is the *pattern*: a key is **derived here and nowhere
else, and compared rather than parsed**. This module publishes no reader that takes a key apart
and a test asserts that by name, because a parser would be a second answer to "what spot is
this" and two answers drift invisibly.

**A preflop spot *key* cannot name the raiser's flop, which is why `PreflopLine` exists.** A
preflop spot key names a decision hero is *about to make*, and every flop is reached with the
preflop betting closed, so the only seat such a key can name is the caller - the one whose last
preflop decision was facing a bet. Built on one, this vocabulary could never express a
continuation bet, about half of all flops. What a postflop key carries is therefore the
**completed** preflop line, verbatim and with its sizes, in the preflop key's own grammar but
validated by the opposite rule: the street must be closed rather than open. Decision 8's
amendment of 2026-09-15 is the authority; `spot_key`'s validator is right for its own question
and is not loosened to serve this one.

**A key can only name a node a dealer reaches.** `validate_flop_action_line` walks the flop
round against `postflop_action_order` before a key is built, so a line whose seats act out of
turn, act after folding, act after the betting closed, or stop at somebody else's decision has
no key at all. Without it the raiser's continuation bet keys as `f:none` at import and as
`f:BB:check` at a table, and every c-bet refuses while `committed_spot_queries` answers itself.

**The key does not begin with `t`.** `data_pipeline/self_play_reference.py` recovers preflop
keys by taking any whitespace token starting with `t` that holds three slashes, and a postflop
key carries a line in that grammar verbatim inside it. Beginning with `f` stops that reader
claiming a flop spot as a preflop one, and the whole key is one whitespace-free token so the
segment inside it is never a token of its own. Decision 8.

**What the key names.** The canonical board, the preflop line verbatim with its prices, every
flop action so far with its bet size, the pot and the effective stack. Naming the bet size is
decision 9: a caller needs 19.9% equity against a 33% bet and 30.0% against a 75% one, so a
merged key would overfold to small bets and overcall large ones. Naming the pot and stack is
decision 10: the geometric three-street size moves 103.9%, 115.8% and 130.9% of pot at 77.5,
97.5 and 127.5bb effective, so a key that cannot say which depth it holds cannot refuse one it
lacks.

**The pot and the stack in the key are nominal, not observed:** they come from the
*substituted* preflop line, which keeps a cell findable when a hand opened to 2.25bb looks up an
`@2.5` cell. `PRICE_BAND_FRACTION` carries the rest, and
`THE-QUERY-TIME-PRICE-SUBSTITUTION-IS-NOT-BOUNDED-POSTFLOP` what it still cannot see.

**The one collapse is over suits, and it lives in `postflop_isomorphism`.** A board becomes the
smallest member of its suit-isomorphism class and hero's hand becomes the smallest image of
itself over every relabelling that reaches that representative. Re-exported here, because the
key producer is where a caller looks for it, and implemented there, because minimising over the
board's stabiliser rather than mapping by one permutation is the whole of the correctness
argument and it owes its own file. Nothing else is collapsed: `K72r` and `Q72r` are two boards,
because decision 2 defers rank abstraction rather than taking it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from poker_training_bot.poker_core.positions import (
    POSITION_LABELS,
    postflop_action_order,
    preflop_action_order,
)

# Re-exported rather than restated. `postflop_isomorphism` owns the one collapse decision 2
# permits; this module is where every caller looks for it, because the key is what the collapse
# is for. `__all__` below is what makes the re-export deliberate rather than an unused import.
from poker_training_bot.solver_artifacts.postflop_isomorphism import (
    CANONICAL_FLOP_CLASSES,
    FLOP_CARDS,
    board_suit_map,
    board_suit_maps,
    canonical_board,
    canonical_hole_cards,
)

# The three underscored names are borrowed rather than restated: everything a preflop line must
# satisfy *whatever* question is asked of it - a table size the repo seats, a positive depth,
# raises that increase and that the depth can pay - is `spot_key`'s rule already, and a second
# copy would be a second rule that can drift. What differs here is only that the street is closed.
from poker_training_bot.solver_artifacts.spot_key import (
    PreflopAction,
    _validate_sizes,
    _validate_stack_depth,
    _validate_table_size,
    render_entry,
    render_size_bb,
)

# The re-exports, named so they are a published surface rather than an unused import. Everything
# else this module defines is public by being defined here.
__all__ = [
    "CANONICAL_FLOP_CLASSES", "FLOP_CARDS", "board_suit_map", "board_suit_maps",
    "canonical_board", "canonical_hole_cards",
]

# Decision 11's flop menu as a fraction of pot, which is the unit it was solved in.
FLOP_BET_MENU: tuple[float, ...] = (0.33, 0.75)

MENU_FRACTION_TOLERANCE = 0.05
"""How far, in pot fraction, a faced bet may sit from a menu entry and still be that entry.

Decision 14, ruled by Taylor 2026-09-15, compared **inclusively**. The menu is a percent of pot
and the table is in chips and the arithmetic does not come out even - 33% of a 550-chip pot is
181.5 - so strict equality would refuse every faced bet at a real table.

Bounded on both sides by arithmetic rather than taste: above the rounding a real table imposes,
`|180/550 - 0.33| = 0.002727`; under half the distance between two entries,
`(0.75 - 0.33)/2 = 0.21`; and under `|0.50 - 0.33| = 0.17`, because a 50% bet must refuse. The
cost is stated rather than hidden: a 28%-of-pot bet and a 38%-of-pot bet both get the strategy
solved for 33%. The fraction is always of the **real** pot the bet went into, never a nominal
one, on both sides of the conversion - `match_menu_fraction` and `menu_size_chips`."""

PRICE_BAND_FRACTION = 0.20
"""How far a real preflop price may sit from the price a cell was solved at.

Decision 10, ruled by Taylor 2026-09-10, a fraction of the cell's own price and inclusive at
both ends: an open of 2.0bb to 3.0bb against an `@2.5` cell, a 3-bet of 6.0bb to 9.0bb against
an `@7.5` one. A fraction rather than a chip width, because a fixed width admitting 2.0-3.0
against `@2.5` would admit only 7.0-8.0 against `@7.5` and a 3-bet to 6.5 would fall through the
rule entirely, and five of the seven converged rows are 3-bet pots.

A coverage rule, not a sensitivity-derived one: 99.0% of the corpus's 409 opens land inside it
and 47.1% of its 87 3-bets do, because the committed chart's single 3-bet price of 7.5bb sits
below the corpus median of 9.25bb. `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN` owns
that gap, recorded rather than tuned away."""

# Every action a seat can take on a flop. Unlike preflop, a check can precede hero's
# decision and a bet is the commonest entry there is.
_FLOP_ACTIONS = ("fold", "check", "call", "bet", "raise")
_SIZED_FLOP_ACTIONS = frozenset({"bet", "raise"})


_NO_FLOP_ACTION = "none"
"""What the flop segment reads when hero is first to act and nothing has happened yet. It
cannot collide with a rendered line: every `FlopAction` renders as `POSITION:action`, so every
non-empty flop segment holds a colon and this one does not."""


@dataclass(frozen=True)
class FlopAction:
    """One completed flop action, in the unit the solve was configured in.

    `size_pct` is a percent of the pot - decision 11's menu unit, and what the committed cells
    are indexed by; chips belong to the table and reach this menu through
    `match_menu_fraction`. A bet or a raise must carry one, because a sizeless aggressive
    action is decision 9's defect: two cells facing different prices merge into one and the
    lookup answers a 75% bet out of a 33% cell."""

    position: str
    action: str
    size_pct: float | None = None

    def __post_init__(self) -> None:
        if self.position not in POSITION_LABELS:
            raise ValueError(f"unknown position: {self.position!r}")
        if self.action not in _FLOP_ACTIONS:
            raise ValueError(
                f"flop action must be one of {list(_FLOP_ACTIONS)}, got {self.action!r}"
            )
        if self.action in _SIZED_FLOP_ACTIONS:
            if self.size_pct is None:
                raise ValueError(
                    f"a {self.action} by {self.position} must carry its size as a percent of"
                    " pot; a sizeless one reads as matching any price"
                )
            if isinstance(self.size_pct, bool) or not isinstance(self.size_pct, int | float):
                raise ValueError(f"size_pct must be a number, got {self.size_pct!r}")
            if not self.size_pct > 0:
                raise ValueError(f"size_pct must be positive, got {self.size_pct!r}")
            render_size_bb(self.size_pct)
        elif self.size_pct is not None:
            raise ValueError(
                f"a {self.action} carries no size of its own, got size_pct={self.size_pct!r}"
            )


def render_flop_action(entry: FlopAction) -> str:
    """One flop action as it appears inside a key, on the preflop key's own `@size` shape."""
    if entry.size_pct is None:
        return f"{entry.position}:{entry.action}"
    return f"{entry.position}:{entry.action}@{render_size_bb(entry.size_pct)}"


@dataclass(frozen=True)
class PreflopLine:
    """The preflop betting as it stood when the flop was dealt, and what it left behind.

    Not a preflop spot key and deliberately not interchangeable with one: `spot_key` refuses a
    sequence where hero has already acted and faces no later raise, which is every line the
    raiser reaches a flop by. This records the closed street instead - who is still in, what
    each put in, the level they all reached.

    `rendered` is that line in the preflop key's grammar, which is what decision 8 means by
    verbatim with its sizes. Hero's position is in it because one completed line is two spots:
    the raiser decides whether to continuation-bet and the caller whether to donk, out of two
    different ranges.
    """

    table_size: int
    stack_depth_bb: int
    hero_position: str
    actions: tuple[PreflopAction, ...]
    live_positions: tuple[str, ...]
    contributions: tuple[tuple[str, float], ...]
    closing_level_bb: float
    pot_bb: float
    effective_stack_bb: float
    rendered: str


_LIVE_SEATS_ON_A_FLOP = 2
_HEADS_UP = 2


def completed_preflop_line(
    table_size: int,
    stack_depth_bb: int,
    hero_position: str,
    action_sequence: Sequence[PreflopAction],
    small_blind_bb: float = 0.5,
    big_blind_bb: float = 1.0,
    ante_bb: float = 0.0,
) -> PreflopLine:
    """Validate a preflop line that a flop actually followed, and say what it left in the middle.

    The ring is walked the way `spot_key` walks it - a cursor over the action order, every live
    seat it passes without a recorded action having folded there, hero never among them - and
    then one further lap **closes** the street: a live seat that has not matched the standing
    level never acted, so it folded, and hero in that position means the betting was still open
    and no flop had been dealt. That lap is the whole difference from the preflop validator,
    which asserts the opposite. Pot and effective stack fall out of the same walk: every live
    seat sits at the closing level, so what is behind is the depth less it, and a seat that
    folded leaves what it had already put in."""
    positions = _validate_table_size(table_size)
    _validate_stack_depth(stack_depth_bb)
    entries = tuple(action_sequence)
    for entry in entries:
        if not isinstance(entry, PreflopAction):
            raise ValueError(f"action_sequence entries must be PreflopAction, got {entry!r}")
    for name in (hero_position, *(entry.position for entry in entries)):
        if name not in positions:
            raise ValueError(
                f"{name!r} is not a {table_size}-handed position; expected {list(positions)}"
            )
    _validate_sizes(entries, stack_depth_bb)
    put_in, folded, level = _closed_preflop_round(
        hero_position, entries, positions, small_blind_bb, big_blind_bb
    )
    live = tuple(name for name in positions if name not in folded)
    if len(live) < _LIVE_SEATS_ON_A_FLOP:
        raise ValueError(
            f"{len(live)} seat(s) reach the flop on this line, so no flop was dealt here and"
            " there is no postflop spot to name"
        )
    totals = {name: value + ante_bb for name, value in put_in.items()}
    return PreflopLine(
        table_size=table_size,
        stack_depth_bb=stack_depth_bb,
        hero_position=hero_position,
        actions=entries,
        live_positions=live,
        contributions=tuple(sorted(totals.items())),
        closing_level_bb=level,
        pot_bb=sum(totals.values()),
        effective_stack_bb=float(stack_depth_bb) - level,
        rendered=f"t{table_size}/d{stack_depth_bb}/{hero_position}/"
        + ",".join(render_entry(entry) for entry in entries),
    )


def _closed_preflop_round(
    hero_position: str,
    entries: Sequence[PreflopAction],
    positions: Sequence[str],
    small_blind_bb: float,
    big_blind_bb: float,
) -> tuple[dict[str, float], set[str], float]:
    """Run the round to its close: what each seat put in, who is out, and the closing level."""
    order = preflop_action_order(len(positions))
    size = len(order)
    folded: set[str] = set()
    put_in = dict.fromkeys(positions, 0.0)
    # Heads-up the button posts the small blind; at every larger table the small blind does.
    small = "BTN" if len(positions) == _HEADS_UP else "SB"
    for label, posted in ((small, small_blind_bb), ("BB", big_blind_bb)):
        if label in put_in:
            put_in[label] = posted
    level = big_blind_bb
    cursor = 0

    def passing(standing: str, context: str) -> None:
        if standing == hero_position:
            raise ValueError(
                f"{hero_position} would have to fold before {context}, so it is not in the hand"
                " on the flop this line leads to"
            )
        folded.add(standing)

    for index, entry in enumerate(entries):
        context = f"action_sequence entry {index} by {entry.position}"
        if entry.position in folded:
            raise ValueError(
                f"{context} acts after the action already passed it, so it had folded:"
                " absence means folded once the orbit has gone by"
            )
        for _ in range(size + 1):
            standing = order[cursor % size]
            cursor += 1
            if standing == entry.position:
                break
            if standing not in folded:
                passing(standing, context)
        else:
            raise ValueError(f"the preflop order never reaches {context}")
        if entry.action == "raise":
            level = float(entry.size_bb or 0.0)
        put_in[entry.position] = level

    for _ in range(size):
        standing = order[cursor % size]
        cursor += 1
        if standing in folded or put_in[standing] >= level:
            continue
        passing(
            standing,
            f"the flop, still owing {render_size_bb(level - put_in[standing])}bb of the"
            f" {render_size_bb(level)}bb the street closed at",
        )
    return put_in, folded, level


def validate_flop_action_line(
    preflop_line: PreflopLine, flop_actions: Sequence[FlopAction]
) -> None:
    """Refuse a flop line no dealer could have produced, ending at hero's own turn.

    **An unreachable node is a cell nothing ever asks for**, and the case that matters is exactly
    the continuation bet. A real table puts the out-of-position seat's check on the record, so the
    key it derives for the raiser's flop is `f:BB:check`; a cell written `f:none` there - the
    natural reading of "nothing has happened yet" - refuses every c-bet under `no-cell-for-this-
    spot` and turns the report's bet frequency into a donk-bet frequency. Nothing in the loop
    could see it, because `committed_spot_queries` rebuilds the table **from the cell**.

    The flop analogue of `_closed_preflop_round`, over `postflop_action_order` - which until now
    had no production caller at all. Four ways a line can be unreachable: a seat that is not live,
    a seat acting out of turn, an action that does not suit the price in front of it, and a line
    that stops before or after hero's own decision. A bet or a raise re-opens the round for
    everybody else and closes it on itself.

    Sizes are not walked: a flop size is a percent of the pot **as it stood**, so chip levels are
    not derivable here, and whether a seat faced a bet - which is all turn order needs - is.
    """
    live = set(preflop_line.live_positions)
    order = [
        name for name in postflop_action_order(preflop_line.table_size) if name in live
    ]
    if preflop_line.hero_position not in live:
        raise ValueError(f"{preflop_line.hero_position} is not live on this flop")
    pending = list(order)
    faced = dict.fromkeys(order, 0)
    level = 0
    for index, entry in enumerate(flop_actions):
        context = f"flop_actions entry {index} by {entry.position}"
        if entry.position not in live:
            raise ValueError(
                f"{context} folded before the flop, so it cannot act on one:"
                f" {sorted(live)} are the seats this line leaves in"
            )
        if not pending:
            raise ValueError(f"{context} acts after the flop betting had already closed")
        if pending[0] != entry.position:
            raise ValueError(
                f"{context} acts out of turn; it is {pending[0]}'s turn here, since postflop"
                f" order is {order} rather than the preflop one"
            )
        if faced[entry.position] < level:
            if entry.action not in ("fold", "call", "raise"):
                raise ValueError(
                    f"{context} {entry.action}s facing a bet, which no dealer offers; facing one"
                    " a seat folds, calls or raises"
                )
        elif entry.action not in ("check", "bet"):
            raise ValueError(
                f"{context} {entry.action}s with nothing in front of it; first in a round a seat"
                " checks or bets"
            )
        pending.pop(0)
        if entry.action == "fold":
            live.discard(entry.position)
            pending = [name for name in pending if name != entry.position]
            order = [name for name in order if name != entry.position]
        elif entry.action in _SIZED_FLOP_ACTIONS:
            level += 1
            faced[entry.position] = level
            pending = [name for name in order if name != entry.position]
        else:
            faced[entry.position] = level
    if len(live) < _LIVE_SEATS_ON_A_FLOP:
        raise ValueError("the flop line leaves one seat in, so the hand ended before hero acted")
    if not pending:
        raise ValueError(
            "the flop betting closes on this line, so there is no decision left for"
            f" {preflop_line.hero_position} to make and no spot to name"
        )
    if pending[0] != preflop_line.hero_position:
        raise ValueError(
            f"this line ends at {pending[0]}'s turn rather than"
            f" {preflop_line.hero_position}'s, so it names somebody else's decision"
        )


def postflop_spot_key(
    preflop_line: PreflopLine,
    board: Sequence[str],
    flop_actions: Sequence[FlopAction],
    pot_bb: float,
    effective_stack_bb: float,
) -> str:
    """Derive the canonical postflop spot key.

    `f/b:<board>/<preflop line>/f:<flop line>/p:<pot>/e:<stack>`, where the board is the
    canonical representative of its class, the preflop line is carried verbatim with its
    prices, and the flop line is comma-separated in action order or `none` when hero is first
    to act. Pot and effective stack are the nominal ones the cell was solved for, in big blinds,
    so a 100bb cell can never quietly answer a spot at another depth. The whole key is one
    whitespace-free token beginning with `f`, which keeps the preflop segment inside it
    invisible to `self_play_reference.py`.
    """
    if not isinstance(preflop_line, PreflopLine):
        raise ValueError(
            "preflop_line must be a PreflopLine from `completed_preflop_line`; a preflop spot"
            " key names a decision hero is about to make and cannot name a flop at all,"
            f" got {preflop_line!r}"
        )
    entries = tuple(flop_actions)
    for entry in entries:
        if not isinstance(entry, FlopAction):
            raise ValueError(f"flop_actions entries must be FlopAction, got {entry!r}")
    validate_flop_action_line(preflop_line, entries)
    line = ",".join(render_flop_action(entry) for entry in entries) or _NO_FLOP_ACTION
    cards = "".join(canonical_board(board))
    pot = render_size_bb(pot_bb)
    stack = render_size_bb(effective_stack_bb)
    return f"f/b:{cards}/{preflop_line.rendered}/f:{line}/p:{pot}/e:{stack}"


def price_within_band(solved_bb: float, actual_bb: float) -> bool:
    """Whether a real preflop price is close enough to the one a cell was solved at.

    Inclusive at both ends, because the endpoints are prices real hands land on - 2.0 is a
    min-open and 3.0 a standard 3x - and because the previous draft failed at a boundary nobody
    had written down. A price outside refuses and is never moved onto the nearest, deliberately
    the opposite of the preflop chart: preflop 0.25bb barely moves a range, postflop the same
    0.25bb moves the pot, the SPR and both ranges at once."""
    for value, field in ((solved_bb, "solved_bb"), (actual_bb, "actual_bb")):
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"{field} must be a number, got {value!r}")
    if not solved_bb > 0:
        raise ValueError(f"solved_bb must be positive, got {solved_bb!r}")
    return abs(actual_bb - solved_bb) <= solved_bb * PRICE_BAND_FRACTION


def _validated_pot(pot_chips: int) -> int:
    if isinstance(pot_chips, bool) or not isinstance(pot_chips, int | float):
        raise ValueError(f"pot_chips must be a number, got {pot_chips!r}")
    if not pot_chips > 0:
        raise ValueError(f"pot_chips must be positive, got {pot_chips!r}")
    return pot_chips


def match_menu_fraction(bet_chips: int, pot_chips: int) -> float | None:
    """Which menu entry a chip bet is, or None when it is none of them.

    Decision 14. The comparison is by pot fraction rather than chips, so it holds at any blind
    level, and `None` is the answer for anything outside every bucket rather than the nearer
    entry - snapping is the nearest-neighbour substitution the contract forbids by name, and a
    bet exactly halfway between two entries has no nearer entry anyway. The first matching entry
    wins and no bet can match two: at the ruled tolerance the buckets reach 38% and 70% of pot
    and do not touch.
    """
    if isinstance(bet_chips, bool) or not isinstance(bet_chips, int | float):
        raise ValueError(f"bet_chips must be a number, got {bet_chips!r}")
    fraction = bet_chips / _validated_pot(pot_chips)
    for entry in FLOP_BET_MENU:
        if abs(fraction - entry) <= MENU_FRACTION_TOLERANCE:
            return entry
    return None


def menu_size_chips(fraction: float, pot_chips: int) -> int:
    """A committed artifact size as chips, rounded to the nearest chip.

    The other direction of decision 14's rule, and why it needs stating: 33% of a 550-chip pot
    is 181.5 and the table can only push whole chips."""
    if isinstance(fraction, bool) or not isinstance(fraction, int | float):
        raise ValueError(f"fraction must be a number, got {fraction!r}")
    if not fraction > 0:
        raise ValueError(f"fraction must be positive, got {fraction!r}")
    return round(fraction * _validated_pot(pot_chips))
