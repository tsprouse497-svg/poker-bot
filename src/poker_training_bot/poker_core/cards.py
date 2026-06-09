from __future__ import annotations

from dataclasses import dataclass

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}
VALUE_RANK = {value: rank for rank, value in RANK_VALUE.items()}


@dataclass(frozen=True, order=True)
class Card:
    rank: str
    suit: str

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"invalid card rank: {self.rank!r}")
        if self.suit not in SUITS:
            raise ValueError(f"invalid card suit: {self.suit!r}")

    @property
    def value(self) -> int:
        return RANK_VALUE[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


def parse_card(text: str) -> Card:
    normalized = text.strip()
    if len(normalized) != 2:
        raise ValueError(f"card must use two-character notation: {text!r}")
    return Card(normalized[0].upper(), normalized[1].lower())


def parse_cards(texts: list[str] | tuple[str, ...]) -> tuple[Card, ...]:
    return tuple(parse_card(text) for text in texts)


def card_texts(cards: tuple[Card, ...] | list[Card]) -> list[str]:
    return [str(card) for card in cards]


def standard_deck() -> tuple[Card, ...]:
    return tuple(Card(rank, suit) for rank in RANKS for suit in SUITS)


def validate_unique_cards(cards: tuple[Card, ...] | list[Card]) -> None:
    seen: set[Card] = set()
    for card in cards:
        if card in seen:
            raise ValueError(f"duplicate card: {card}")
        seen.add(card)
