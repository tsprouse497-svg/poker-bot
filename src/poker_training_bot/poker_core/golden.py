from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from poker_training_bot.poker_core.cards import Card, parse_cards
from poker_training_bot.poker_core.engine import PlayerState, Settlement, settle_showdown


@dataclass(frozen=True)
class GoldenHand:
    hand_id: str
    description: str
    board: tuple[Card, ...]
    players: tuple[PlayerState, ...]


def load_golden_hands(path: Path) -> tuple[GoldenHand, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    hands: list[GoldenHand] = []
    for raw_hand in payload["hands"]:
        players = tuple(
            PlayerState(
                seat=int(raw_player["seat"]),
                name=str(raw_player["name"]),
                stack=0,
                hole_cards=parse_cards(raw_player["hole_cards"]),
                committed_total=int(raw_player["committed_total"]),
                folded=bool(raw_player.get("folded", False)),
                all_in=True,
            )
            for raw_player in raw_hand["players"]
        )
        hands.append(
            GoldenHand(
                hand_id=str(raw_hand["hand_id"]),
                description=str(raw_hand["description"]),
                board=parse_cards(raw_hand["board"]),
                players=players,
            )
        )
    return tuple(hands)


def replay_golden_hands(path: Path) -> tuple[tuple[GoldenHand, Settlement], ...]:
    return tuple(
        (hand, settle_showdown(hand.players, hand.board)) for hand in load_golden_hands(path)
    )
