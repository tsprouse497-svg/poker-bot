"""A preflop chart question: the shape a caller asks in, and the key it derives.

Split out of `lookup` because a question is a different subject from the library that
answers it - live game state is turned into a `ChartQuery` by callers that never touch a
chart - and because `lookup` was at the 500-line cap when decision 8's derivation codes
arrived. `lookup` re-exports the name, which is what the frozen tests and every caller in
the repo import, so nothing outside this package can tell the two files apart.

The spot key is derived here rather than spelled by a caller, with the same function the
importer stamps artifacts with. That is what makes a spot that imports reachable from a
query built out of a real hand.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from poker_training_bot.solver_artifacts.hand_classes import (
    hand_class as canonical_hand_class,
)
from poker_training_bot.solver_artifacts.hand_classes import (
    is_hand_class,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key


def _validate_int(value: object, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer, got {value!r}")


@dataclass(frozen=True)
class ChartQuery:
    """A preflop chart question: table, depth, hero position, action, hand class.

    Validation here is deliberately light. A caller builds a query out of live
    game state, so an unknown table size or a position that does not exist at
    that table is a lookup miss it can log, not an exception it has to catch.
    Only genuine programming errors raise: a hand class outside the canonical
    169, or an action sequence holding something that is not a `PreflopAction`.
    """

    table_size: int
    stack_depth_bb: int
    hero_position: str
    action_sequence: tuple[PreflopAction, ...]
    hand_class: str

    def __post_init__(self) -> None:
        _validate_int(self.table_size, "table_size")
        _validate_int(self.stack_depth_bb, "stack_depth_bb")
        if not isinstance(self.hero_position, str) or not self.hero_position:
            raise ValueError(
                f"hero_position must be a non-empty string, got {self.hero_position!r}"
            )
        if not isinstance(self.action_sequence, tuple):
            raise ValueError(
                f"action_sequence must be a tuple, got {type(self.action_sequence).__name__}"
            )
        for entry in self.action_sequence:
            if not isinstance(entry, PreflopAction):
                raise ValueError(f"action_sequence entries must be PreflopAction, got {entry!r}")
        if not is_hand_class(self.hand_class):
            raise ValueError(f"unknown hand class: {self.hand_class!r}")

    @classmethod
    def from_hole_cards(
        cls,
        table_size: int,
        stack_depth_bb: int,
        hero_position: str,
        action_sequence: tuple[PreflopAction, ...],
        hole_cards: Sequence[str],
    ) -> ChartQuery:
        """Build a query from two hole cards such as `("As", "kd")`.

        Canonicalization is `hand_classes.hand_class`, so card order and suits
        beyond suitedness cannot change which spot is asked about.
        """
        return cls(
            table_size=table_size,
            stack_depth_bb=stack_depth_bb,
            hero_position=hero_position,
            action_sequence=action_sequence,
            hand_class=canonical_hand_class(hole_cards),
        )

    @property
    def spot_key(self) -> str | None:
        """The derived spot key at the query's own prices, or None if there is none.

        None is not an error. It means no legal preflop situation produces this
        sequence at all - a seat acting out of turn, a re-raise that is not an
        increase, a raise nobody at the stated depth can pay - and the lookup misses
        rather than guesses. A position acting more than once is no longer one of
        those cases, which is what closed `SECOND-ORBIT-PREFLOP-SPOTS`.
        """
        try:
            return derive_spot_key(
                self.table_size, self.stack_depth_bb, self.hero_position, self.action_sequence
            )
        except ValueError:
            return None
