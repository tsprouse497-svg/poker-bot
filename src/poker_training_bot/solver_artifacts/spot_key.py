"""The preflop spot vocabulary: what a spot key can say, and how it is derived.

A key is derived here and nowhere else. The importer stamps artifacts with it and the
chart lookup rebuilds it from live game state, so a spot that imports is reachable by a
lookup. Two derivations of "what spot is this" would be two answers that can drift, and
the drift would be invisible.

Folds never appear in a sequence. A folded position carries no information beyond its
absence, so an empty sequence means "folded to hero" (RFI) and every recorded entry is
live aggression or a call.

A raise entry carries the amount it raised *to*, in big blinds, rendered after an `@`.
Big blinds rather than chips, because chips do not survive a change of blind level; a
raise-to rather than a multiple of the previous bet, because a multiple depends on what
came before it and the same spot would key two ways. A call entry carries no size: it
pays the level the preceding raise already states, and in a limped pot it pays the big
blind the key's own prefix implies.

A position may act more than once. What bounds the vocabulary is the *order* - whether the
ring can still have each of these positions acting, and whether hero has a decision left -
together with whether the raises fit the stated depth, rather than a number of orbits
somebody imagined. That is why the size in the key is not only a finer index: it is what
lets the key reject a five-bet to 300bb in a 100bb game at all.

What the checks below do **not** verify, stated because a docstring stronger than its check
is how the next reader stops looking. They never ask whether a *price* is legal. A raise has
only to exceed the one before it, so an under-raise no betting round produces still has a
key; the depth test is table-wide rather than per-seat, so a raise no single seat could pay
is admitted whenever the stated depth could; and a call carries no all-in marker, so a short
all-in call and a full call are one spot. Phase 12 left all three deliberately, because the
key holds one table-wide depth and no per-seat stacks, and so cannot tell an under-raise
from a legal short all-in at all.

What still waits is the key space itself rather than the query. Since phase 13 a live query
carries what every seat put in, so an asymmetric table is refused before a key is built, and a
short all-in caller - which by definition has put in everything it sat down with - refuses as
a seat shorter than hero rather than reaching this module at all. Anything working from keys
instead of from a table still merges both pairs: an imported artifact, a self-play
enumeration, `decide_spot`. Closing that is a change to the key format - a marker on each
raise and call entry saying whether it was a full action or an all-in for less - and it is
deferred rather than done. The table-state report measures what it costs on committed data.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from poker_training_bot.poker_core.positions import (
    POSITION_LABELS,
    preflop_action_order,
    table_positions,
)

# A recorded sequence entry can only be a call or a raise. Preflop everyone faces the big
# blind, so the only seat that can check is the big blind, and its check ends the betting
# round. A check can therefore never precede hero's decision.
SEQUENCE_ACTIONS = ("call", "raise")

MIN_TABLE_SIZE = 2
MAX_TABLE_SIZE = 9


# Hundredths of a big blind. Fine enough for every size the committed solve and the
# committed corpus contain, and coarse enough that two renderings of one value cannot
# both exist as keys. A size finer than this is rejected rather than rounded, because
# rounding moves a spot into a neighbouring cell without saying so.
SIZE_QUANTUM = Decimal("0.01")


def render_size_bb(value: float) -> str:
    """Render a size in big blinds as it appears inside a spot key.

    Quantized to hundredths with trailing zeros stripped, so `2.5` and `2.50` cannot
    both exist as keys for one spot: `2.5` renders `2.5`, `8.0` renders `8`, `2.25`
    renders `2.25`. The stripping costs a ragged column in a refusal inventory and buys
    a string a person can scan, which is the whole reason the inventory is useful.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"a size in big blinds must be a number, got {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"a size in big blinds must be finite, got {value!r}")
    exact = Decimal(repr(float(value)))
    if exact != exact.quantize(SIZE_QUANTUM):
        raise ValueError(
            f"{value!r} big blinds is finer than a hundredth of a big blind;"
            " a size the key cannot represent exactly is rejected rather than rounded"
            " into a neighbouring cell"
        )
    return format(exact.normalize(), "f")


def _validate_int(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer, got {value!r}")
    return value


def _validate_table_size(table_size: int) -> tuple[str, ...]:
    _validate_int(table_size, "table_size")
    if table_size < MIN_TABLE_SIZE or table_size > MAX_TABLE_SIZE:
        raise ValueError(
            f"table_size must be between {MIN_TABLE_SIZE} and {MAX_TABLE_SIZE},"
            f" got {table_size}"
        )
    return table_positions(table_size)


def _validate_stack_depth(stack_depth_bb: int) -> int:
    _validate_int(stack_depth_bb, "stack_depth_bb")
    if stack_depth_bb <= 0:
        raise ValueError(f"stack_depth_bb must be positive, got {stack_depth_bb}")
    return stack_depth_bb


def _validate_preflop_order(
    hero_position: str,
    entries: Sequence[PreflopAction],
    order: Sequence[str],
) -> None:
    """Walk the ring the way a preflop betting round actually walks it.

    v1 asked a weaker question - are these positions a subsequence of one pass over
    the action order - and that question has no answer past the first orbit, which is
    why a four-bet had no key at all. The generalisation is to run the ring: a cursor
    starts at the first seat to act and moves forward, wrapping, and every position it
    passes without a recorded action has folded there.

    Two rules fall out of that walk rather than being bolted onto it. A position the
    action has already passed cannot reappear, because a seat that folded is gone. And
    hero can never be one of the positions the walk folds, because hero is by
    definition still in the hand and about to act. A position merely *ahead* of the
    cursor in the current orbit is absent for the ordinary reason that its turn has not
    come, and it is free to appear later; that is the distinction the fold rule is easy
    to get backwards.
    """
    size = len(order)
    folded: set[str] = set()
    cursor = 0

    def advance_to(target: str, context: str) -> int:
        nonlocal cursor
        for _ in range(size + 1):
            standing = order[cursor % size]
            if standing == target:
                cursor += 1
                return cursor
            if standing not in folded:
                if standing == hero_position:
                    raise ValueError(
                        f"{hero_position} would have to fold before {context}, so it is"
                        " not the player to act in this sequence"
                    )
                folded.add(standing)
            cursor += 1
        raise ValueError(f"the preflop order never reaches {context}")

    for index, entry in enumerate(entries):
        if entry.position in folded:
            raise ValueError(
                f"action_sequence entry {index} has {entry.position} acting after the"
                " action already passed it, so it had folded: absence means folded once"
                " the orbit has gone by"
            )
        advance_to(entry.position, f"action_sequence entry {index} by {entry.position}")

    if not entries and order.index(hero_position) == size - 1:
        raise ValueError(
            f"{hero_position} acts last preflop, so a folded-to-hero spot has no decision"
        )
    advance_to(hero_position, f"hero {hero_position}")

    own = [index for index, entry in enumerate(entries) if entry.position == hero_position]
    if own:
        # Generalised from hero's first entry to hero's last: at any orbit depth, a call
        # behind hero does not give hero another turn, so only a later raise reopens it.
        later = entries[own[-1] + 1 :]
        if not any(entry.action == "raise" for entry in later):
            raise ValueError(
                f"{hero_position} already acted and faces no later raise,"
                " so the betting round is closed"
            )


def _validate_sizes(
    entries: Sequence[PreflopAction], stack_depth_bb: int
) -> None:
    """Raises strictly increase along the sequence and fit the stated depth.

    Neither check could be made at all before the key carried sizes, and together they
    are what bounds an uncapped orbit count: a re-raise has to be a real raise, and no
    sequence of them can put more in than the players brought.
    """
    previous_size = 0.0
    for index, entry in enumerate(entries):
        if entry.action != "raise":
            continue
        size = float(entry.size_bb or 0.0)
        if size > stack_depth_bb:
            raise ValueError(
                f"action_sequence entry {index} raises to {render_size_bb(size)}bb at a"
                f" {stack_depth_bb}bb depth, which nobody at the table can pay"
            )
        if size <= previous_size:
            raise ValueError(
                f"action_sequence entry {index} raises to {render_size_bb(size)}bb, which"
                f" does not exceed the {render_size_bb(previous_size)}bb it faces;"
                " a re-raise that is not an increase is not a raise"
            )
        previous_size = size


@dataclass(frozen=True)
class PreflopAction:
    """One recorded preflop action in front of (or by) hero.

    Only calls and raises are recorded, so `action` is restricted to
    `SEQUENCE_ACTIONS`. A fold is implicit in the position's absence, and a check
    cannot precede hero's decision preflop.
    """

    position: str
    action: str
    size_bb: float | None = None

    def __post_init__(self) -> None:
        if self.position not in POSITION_LABELS:
            raise ValueError(f"unknown position: {self.position!r}")
        if self.action not in SEQUENCE_ACTIONS:
            raise ValueError(
                f"action_sequence action must be one of {list(SEQUENCE_ACTIONS)},"
                f" got {self.action!r} (a fold is implicit in the position's absence,"
                " and a preflop check ends the round)"
            )
        if self.action == "raise":
            if self.size_bb is None:
                raise ValueError(
                    f"a raise by {self.position} must carry the amount it raised to, in"
                    " big blinds; a sizeless raise is the v1 shape and reading it as"
                    " matching any price is how a lookup silently hits the wrong cell"
                )
            if isinstance(self.size_bb, bool) or not isinstance(self.size_bb, int | float):
                raise ValueError(f"size_bb must be a number, got {self.size_bb!r}")
            if not self.size_bb > 0:
                raise ValueError(f"size_bb must be positive, got {self.size_bb!r}")
            render_size_bb(self.size_bb)
        elif self.size_bb is not None:
            raise ValueError(
                f"a {self.action} carries no size of its own: it pays the level the"
                " preceding raise already states, and in a limped pot it pays the big"
                f" blind, got size_bb={self.size_bb!r}"
            )


def render_entry(entry: PreflopAction) -> str:
    """One sequence entry as it appears inside a spot key.

    The size is what makes a 2.25bb open and a 2.5bb open two spots instead of one.
    Dropping it here would leave every lookup in this repo still hitting a cell, and
    would make the committed artifact permanently single-price: the one outcome ruling
    8 asked this vocabulary to avoid.
    """
    if entry.action == "raise":
        return f"{entry.position}:{entry.action}@{render_size_bb(entry.size_bb)}"
    return f"{entry.position}:{entry.action}"


def action_entry_payload(entry: PreflopAction) -> dict[str, Any]:
    """One sequence entry as a committed artifact records it.

    `size_bb` appears exactly where the key carries one, so the file and the key say
    the same thing and a reader can check one against the other by eye.
    """
    payload: dict[str, Any] = {"position": entry.position, "action": entry.action}
    if entry.size_bb is not None:
        payload["size_bb"] = float(entry.size_bb)
    return payload


def spot_key(
    table_size: int,
    stack_depth_bb: int,
    hero_position: str,
    action_sequence: Sequence[PreflopAction],
) -> str:
    """Derive the canonical spot key.

    An empty sequence renders as `rfi` (folded to hero); otherwise the sequence
    renders as comma-separated entries in action order, a raise carrying the amount
    it raised to in big blinds after an `@` and a call carrying nothing. Hero may
    appear in the sequence more than once, which is how a four-bet is keyed.

    The sequence must describe a spot where hero is actually the player to act.
    A well-formed string is not enough: `t6/d100/CO/BTN:raise@2.5` reads fine but
    cannot happen, because the button acts after the cutoff. What is rejected is an
    order no ring produces and a raise the stated depth cannot pay; the prices
    themselves are only checked for increasing, so the key space is canonical in
    who acted and when, not in whether every price was legal. The module docstring
    says which prices get through.
    """
    positions = _validate_table_size(table_size)
    _validate_stack_depth(stack_depth_bb)
    if hero_position not in positions:
        raise ValueError(
            f"hero_position {hero_position!r} is not a {table_size}-handed position;"
            f" expected one of {list(positions)}"
        )
    entries = tuple(action_sequence)
    for entry in entries:
        if not isinstance(entry, PreflopAction):
            raise ValueError(f"action_sequence entries must be PreflopAction, got {entry!r}")
        if entry.position not in positions:
            raise ValueError(
                f"action_sequence position {entry.position!r} is not a"
                f" {table_size}-handed position"
            )
    order = preflop_action_order(table_size)
    _validate_sizes(entries, stack_depth_bb)
    _validate_preflop_order(hero_position, entries, order)
    prefix = f"t{table_size}/d{stack_depth_bb}/{hero_position}/"
    if not entries:
        return f"{prefix}rfi"
    return prefix + ",".join(render_entry(entry) for entry in entries)


