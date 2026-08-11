"""Canonical 169-class preflop hand notation.

A hand class is the suit-independent, order-independent name for two hole cards:
a pair (`AA`), a suited holding (`AKs`), or an offsuit holding (`AKo`). The high
card always comes first in the label.
"""

from __future__ import annotations

from collections.abc import Sequence

from poker_training_bot.poker_core.cards import (
    RANK_VALUE,
    RANKS,
    parse_card,
    validate_unique_cards,
)

HIGH_TO_LOW_RANKS = RANKS[::-1]


def _build_hand_classes() -> tuple[str, ...]:
    classes: list[str] = []
    for row, row_rank in enumerate(HIGH_TO_LOW_RANKS):
        for column, column_rank in enumerate(HIGH_TO_LOW_RANKS):
            if row == column:
                classes.append(f"{row_rank}{row_rank}")
            elif row < column:
                classes.append(f"{row_rank}{column_rank}s")
            else:
                classes.append(f"{column_rank}{row_rank}o")
    return tuple(classes)


HAND_CLASSES: tuple[str, ...] = _build_hand_classes()
"""All 169 hand classes in grid order.

The order is the 13x13 rank grid walked row-major with both axes running high to
low (`A`, `K`, `Q`, ..., `2`). The diagonal holds the pairs, cells above it hold
the suited classes, and cells below it hold the offsuit classes. That makes
`HAND_CLASSES` a stable sort key for chart reports.
"""

_HAND_CLASS_INDEX: dict[str, int] = {text: index for index, text in enumerate(HAND_CLASSES)}


def hand_class(hole_cards: Sequence[str]) -> str:
    """Canonical class for exactly two hole cards such as `("As", "kd")`.

    Card text is normalized the way `poker_core.cards.parse_card` normalizes it,
    so case does not matter. The result is order-independent and depends on suits
    only through suitedness.
    """
    texts = tuple(hole_cards)
    if len(texts) != 2:
        raise ValueError(f"a hand class requires exactly two hole cards: {len(texts)}")
    cards = tuple(parse_card(text) for text in texts)
    validate_unique_cards(cards)
    high, low = sorted(cards, key=lambda card: RANK_VALUE[card.rank], reverse=True)
    if high.rank == low.rank:
        return f"{high.rank}{low.rank}"
    return f"{high.rank}{low.rank}{'s' if high.suit == low.suit else 'o'}"


def is_hand_class(text: str) -> bool:
    """True only for a member of `HAND_CLASSES`. Non-string input is False, not an error."""
    return isinstance(text, str) and text in _HAND_CLASS_INDEX


def hand_class_grid_index(hand_class_text: str) -> int:
    """Stable index of a hand class in `HAND_CLASSES`."""
    if not is_hand_class(hand_class_text):
        raise ValueError(f"unknown hand class: {hand_class_text!r}")
    return _HAND_CLASS_INDEX[hand_class_text]
