"""Reading the public hand corpus this phase measures against.

The corpus is stored one hand per file in the poker hand history (PHH) format,
which is TOML. This module does nothing but read that format faithfully. It
deliberately computes nothing: the settlement this phase checks against has to be
the publisher's own integers, and the surest way to keep it that way is for the
reader to be incapable of deriving it.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass

DEAL_HOLE = "d dh"
DEAL_BOARD = "d db"
SHOWDOWN = "sm"

REQUIRED_KEYS = (
    "variant",
    "blinds_or_straddles",
    "min_bet",
    "starting_stacks",
    "actions",
    "players",
    "finishing_stacks",
)


class CorpusParseError(ValueError):
    """The corpus text is not a hand this phase can measure against."""


@dataclass(frozen=True)
class CorpusHand:
    """One hand exactly as the corpus records it.

    `finishing_stacks` is the whole point of the record. Everything else in this
    phase exists to be checked against it.
    """

    hand_id: str
    source_path: str
    variant: str
    players: tuple[str, ...]
    starting_stacks: tuple[int, ...]
    finishing_stacks: tuple[int, ...]
    blinds: tuple[int, int]
    min_bet: int
    hole_cards: tuple[tuple[str, str], ...]
    actions: tuple[str, ...]

    @property
    def seat_count(self) -> int:
        return len(self.players)


def hand_id_for(source_path: str) -> str:
    """A stable id from the path rather than the corpus's own hand number.

    Corpus hand numbers restart within each session directory, so they collide
    across a sample drawn from more than one session.
    """
    return source_path.removesuffix(".phh")


def _split_cards(text: str, context: str) -> tuple[str, ...]:
    if len(text) % 2 != 0:
        raise CorpusParseError(f"{context}: card text {text!r} is not whole cards")
    cards = tuple(text[index : index + 2] for index in range(0, len(text), 2))
    for card in cards:
        if "?" in card:
            raise CorpusParseError(
                f"{context}: card {card!r} is obfuscated;"
                " this phase compares decisions and needs the real holding"
            )
    return cards


def _require_int_list(payload: dict, key: str) -> tuple[int, ...]:
    values = payload[key]
    if not isinstance(values, list) or not values:
        raise CorpusParseError(f"{key} must be a non-empty list")
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise CorpusParseError(
                f"{key} must hold whole chips; {value!r} is not an integer."
                " Fractional-currency corpora are a different ingestion problem"
            )
        result.append(value)
    return tuple(result)


def parse_corpus_hand(text: str, *, source_path: str) -> CorpusHand:
    try:
        payload = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise CorpusParseError(f"{source_path}: unreadable corpus record ({error})") from error

    missing = [key for key in REQUIRED_KEYS if key not in payload]
    if missing:
        raise CorpusParseError(
            f"{source_path}: corpus record is missing {', '.join(missing)}."
            " A hand with no published settlement carries no oracle and proves nothing"
        )

    starting_stacks = _require_int_list(payload, "starting_stacks")
    finishing_stacks = _require_int_list(payload, "finishing_stacks")
    players = tuple(str(name) for name in payload["players"])
    if not (len(players) == len(starting_stacks) == len(finishing_stacks)):
        raise CorpusParseError(f"{source_path}: players and stacks disagree about the seat count")

    blinds_or_straddles = _require_int_list(payload, "blinds_or_straddles")
    if len(blinds_or_straddles) != len(players):
        raise CorpusParseError(f"{source_path}: blind list does not cover every seat")
    posted = [value for value in blinds_or_straddles if value > 0]
    if len(posted) != 2 or blinds_or_straddles[0] <= 0 or blinds_or_straddles[1] <= 0:
        raise CorpusParseError(
            f"{source_path}: expected exactly two posted blinds in the first two seats,"
            f" got {list(blinds_or_straddles)}"
        )

    actions = tuple(str(action) for action in payload["actions"])
    dealt: list[tuple[str, str]] = []
    for action in actions:
        if not action.startswith(DEAL_HOLE):
            continue
        parts = action.split()
        cards = _split_cards(parts[3], f"{source_path}: {action}")
        if len(cards) != 2:
            raise CorpusParseError(f"{source_path}: {action} does not deal exactly two cards")
        dealt.append((cards[0], cards[1]))
    if len(dealt) != len(players):
        raise CorpusParseError(
            f"{source_path}: {len(dealt)} hands dealt to {len(players)} players;"
            " every seat needs its holding for a decision comparison"
        )

    return CorpusHand(
        hand_id=hand_id_for(source_path),
        source_path=source_path,
        variant=str(payload["variant"]),
        players=players,
        starting_stacks=starting_stacks,
        finishing_stacks=finishing_stacks,
        blinds=(blinds_or_straddles[0], blinds_or_straddles[1]),
        min_bet=int(payload["min_bet"]),
        hole_cards=tuple(dealt),
        actions=actions,
    )
