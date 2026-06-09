from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import IntEnum
from itertools import combinations

from poker_training_bot.poker_core.cards import (
    VALUE_RANK,
    Card,
    card_texts,
    validate_unique_cards,
)


class HandCategory(IntEnum):
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9


CATEGORY_LABELS = {
    HandCategory.HIGH_CARD: "High card",
    HandCategory.PAIR: "Pair",
    HandCategory.TWO_PAIR: "Two pair",
    HandCategory.THREE_OF_A_KIND: "Three of a kind",
    HandCategory.STRAIGHT: "Straight",
    HandCategory.FLUSH: "Flush",
    HandCategory.FULL_HOUSE: "Full house",
    HandCategory.FOUR_OF_A_KIND: "Four of a kind",
    HandCategory.STRAIGHT_FLUSH: "Straight flush",
}


@dataclass(frozen=True)
class HandRank:
    category: HandCategory
    kickers: tuple[int, ...]
    cards: tuple[Card, ...]

    @property
    def sort_key(self) -> tuple[int, ...]:
        return (int(self.category), *self.kickers)

    @property
    def label(self) -> str:
        return CATEGORY_LABELS[self.category]

    def beats(self, other: HandRank) -> bool:
        return self.sort_key > other.sort_key

    def ties(self, other: HandRank) -> bool:
        return self.sort_key == other.sort_key

    def describe(self) -> str:
        ranks = " ".join(VALUE_RANK[value] for value in self.kickers)
        return f"{self.label} ({ranks}) with {' '.join(card_texts(self.cards))}"


def evaluate_five(cards: tuple[Card, ...]) -> HandRank:
    if len(cards) != 5:
        raise ValueError("exactly five cards are required")
    validate_unique_cards(cards)
    values = sorted((card.value for card in cards), reverse=True)
    counts = Counter(values)
    groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    flush = len({card.suit for card in cards}) == 1
    unique_values = sorted(set(values), reverse=True)
    straight_high = _straight_high(unique_values)

    if flush and straight_high is not None:
        return HandRank(HandCategory.STRAIGHT_FLUSH, (straight_high,), cards)
    if groups[0][1] == 4:
        quad = groups[0][0]
        kicker = max(value for value in values if value != quad)
        return HandRank(HandCategory.FOUR_OF_A_KIND, (quad, kicker), cards)
    if groups[0][1] == 3 and groups[1][1] == 2:
        return HandRank(HandCategory.FULL_HOUSE, (groups[0][0], groups[1][0]), cards)
    if flush:
        return HandRank(HandCategory.FLUSH, tuple(values), cards)
    if straight_high is not None:
        return HandRank(HandCategory.STRAIGHT, (straight_high,), cards)
    if groups[0][1] == 3:
        trip = groups[0][0]
        kickers = tuple(value for value in values if value != trip)
        return HandRank(HandCategory.THREE_OF_A_KIND, (trip, *kickers), cards)
    if groups[0][1] == 2 and groups[1][1] == 2:
        high_pair, low_pair = sorted((groups[0][0], groups[1][0]), reverse=True)
        kicker = max(value for value in values if value not in {high_pair, low_pair})
        return HandRank(HandCategory.TWO_PAIR, (high_pair, low_pair, kicker), cards)
    if groups[0][1] == 2:
        pair = groups[0][0]
        kickers = tuple(value for value in values if value != pair)
        return HandRank(HandCategory.PAIR, (pair, *kickers), cards)
    return HandRank(HandCategory.HIGH_CARD, tuple(values), cards)


def evaluate_best(cards: tuple[Card, ...] | list[Card]) -> HandRank:
    if len(cards) < 5 or len(cards) > 7:
        raise ValueError("best-hand evaluation requires five to seven cards")
    card_tuple = tuple(cards)
    validate_unique_cards(card_tuple)
    return max(
        (evaluate_five(combo) for combo in combinations(card_tuple, 5)),
        key=lambda rank: rank.sort_key,
    )


def _straight_high(unique_values: list[int]) -> int | None:
    values = set(unique_values)
    if 14 in values:
        values.add(1)
    for high in range(14, 4, -1):
        needed = set(range(high - 4, high + 1))
        if needed.issubset(values):
            return high
    return None
