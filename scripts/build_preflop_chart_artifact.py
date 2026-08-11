"""Expand the reviewable range spec below into the committed preflop artifact.

The spec is hand-authored reference strategy, not solver output. It is written as
range shorthand a poker player can check by eye, and this script is the only
thing that turns it into artifact JSON, so the committed chart always has a
reproducible origin. Re-run it after editing the spec:

    uv run python scripts/build_preflop_chart_artifact.py
"""

from __future__ import annotations

import json
import sys

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.poker_core.cards import RANKS
from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.hand_classes import (
    HAND_CLASSES,
    hand_class_grid_index,
)
from poker_training_bot.solver_artifacts.schema import (
    HandClassWeights,
    PreflopAction,
    SpotActionWeights,
    spot_key,
    weights_checksum,
)

OUTPUT = REPO_ROOT / "data" / "artifacts" / "preflop" / "six_max_100bb_core.json"
GENERATED_AT = "2026-08-11T00:00:00Z"
HIGH_TO_LOW = tuple(reversed(RANKS))


def _rank_index(rank: str) -> int:
    """Index of a rank, accepting either "T" or the pair spelling "TT"."""
    if len(rank) == 2 and rank[0] == rank[1]:
        rank = rank[0]
    return HIGH_TO_LOW.index(rank)


def pairs(min_rank: str, max_rank: str = "A") -> list[str]:
    """Pocket pairs from `min_rank` up to `max_rank`, e.g. pairs("TT") -> AA..TT."""
    start, stop = _rank_index(max_rank), _rank_index(min_rank)
    return [f"{rank}{rank}" for rank in HIGH_TO_LOW[start : stop + 1]]


def _low_cards(high: str, min_low: str, max_low: str | None) -> tuple[str, ...]:
    start = _rank_index(high) + 1 if max_low is None else _rank_index(max_low)
    if start <= _rank_index(high):
        raise ValueError(f"{max_low} is not below {high}")
    return HIGH_TO_LOW[start : _rank_index(min_low) + 1]


def suited(high: str, min_low: str, max_low: str | None = None) -> list[str]:
    """Suited hands with `high` on top, low card from `min_low` up to `max_low`."""
    return [f"{high}{low}s" for low in _low_cards(high, min_low, max_low)]


def offsuit(high: str, min_low: str, max_low: str | None = None) -> list[str]:
    """Offsuit hands with `high` on top, low card from `min_low` up to `max_low`."""
    return [f"{high}{low}o" for low in _low_cards(high, min_low, max_low)]


def combine(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for entry in group:
            if entry in merged:
                raise ValueError(f"range spec lists {entry} twice")
            merged.append(entry)
    return merged


def every_suited() -> list[str]:
    """All 78 suited classes, for ranges a player would describe as "any suited"."""
    return [entry for entry in HAND_CLASSES if entry.endswith("s")]


# Cutoff open-raise, 100bb, 6-max: ~25% of combos. Suited hands are preferred
# over their offsuit counterparts, which is why the offsuit tail stops at ATo.
CO_RAISE = combine(
    pairs("22"),
    suited("A", "2"),
    suited("K", "5"),
    suited("Q", "8"),
    suited("J", "8"),
    suited("T", "7"),
    suited("9", "7"),
    suited("8", "6"),
    suited("7", "5"),
    ["65s", "54s"],
    offsuit("A", "T"),
    offsuit("K", "T"),
    ["QJo", "JTo"],
)

# Button open-raise, 100bb, 6-max: ~45% of combos. A strict superset of the
# cutoff range, as a later position must be.
BTN_RAISE = combine(
    pairs("22"),
    suited("A", "2"),
    suited("K", "2"),
    suited("Q", "2"),
    suited("J", "4"),
    suited("T", "4"),
    suited("9", "4"),
    suited("8", "4"),
    suited("7", "4"),
    suited("6", "3"),
    suited("5", "3"),
    ["43s"],
    offsuit("A", "2"),
    offsuit("K", "9"),
    offsuit("Q", "9"),
    offsuit("J", "9"),
    ["T9o"],
)

# Big blind defending a cutoff open, 100bb, 6-max: ~7% 3bet and ~39% call, so
# about 46% total defense. The big blind closes the action getting roughly 27%
# pot odds, so folding much more than half is a leak.
BB_VS_CO_RAISE = combine(
    pairs("TT"),
    suited("A", "T"),
    ["A5s", "A4s", "A3s", "A2s"],
    suited("K", "J"),
    ["AKo", "AQo"],
)
BB_VS_CO_CALL = combine(
    pairs("22", "99"),
    [entry for entry in every_suited() if entry not in BB_VS_CO_RAISE],
    offsuit("A", "7", "J"),
    offsuit("K", "9", "Q"),
    offsuit("Q", "9", "J"),
    ["J9o", "JTo", "T9o", "98o"],
)

SPOT_SPECS = [
    {
        "hero_position": "CO",
        "action_sequence": [],
        "actions": {"raise": CO_RAISE},
    },
    {
        "hero_position": "BTN",
        "action_sequence": [],
        "actions": {"raise": BTN_RAISE},
    },
    {
        "hero_position": "BB",
        "action_sequence": [{"position": "CO", "action": "raise"}],
        "actions": {"raise": BB_VS_CO_RAISE, "call": BB_VS_CO_CALL},
    },
]

TABLE_SIZE = 6
STACK_DEPTH_BB = 100


def spot_id_for(hero_position: str, action_sequence: list[dict[str, str]]) -> str:
    """Derive the spot key with the schema, never by spelling the format here."""
    return spot_key(
        TABLE_SIZE,
        STACK_DEPTH_BB,
        hero_position,
        tuple(PreflopAction(entry["position"], entry["action"]) for entry in action_sequence),
    )


def spot_weights(actions: dict[str, list[str]]) -> HandClassWeights:
    """Every hand class gets an explicit weight; anything unlisted folds."""
    assigned: dict[str, str] = {}
    for action, classes in actions.items():
        for hand_class_text in classes:
            if hand_class_text not in HAND_CLASSES:
                raise ValueError(f"range spec contains unknown hand class {hand_class_text!r}")
            if hand_class_text in assigned:
                raise ValueError(
                    f"{hand_class_text} is assigned to both {assigned[hand_class_text]} "
                    f"and {action}"
                )
            assigned[hand_class_text] = action
    return tuple(
        (hand_class_text, ((assigned.get(hand_class_text, "fold"), 1.0),))
        for hand_class_text in sorted(HAND_CLASSES, key=hand_class_grid_index)
    )


def build_payload() -> dict:
    spots = []
    ordered_weights: list[tuple[str, HandClassWeights]] = []
    for spec in SPOT_SPECS:
        spot_id = spot_id_for(spec["hero_position"], spec["action_sequence"])
        spots.append(
            {
                "spot_id": spot_id,
                "hero_position": spec["hero_position"],
                "action_sequence": spec["action_sequence"],
            }
        )
        ordered_weights.append((spot_id, spot_weights(spec["actions"])))
    action_weights: SpotActionWeights = tuple(ordered_weights)
    hand_class_count = len({
        hand_class_text
        for _, hand_classes in action_weights
        for hand_class_text, _ in hand_classes
    })
    return {
        "artifact_schema_version": 1,
        "source": {
            "name": "Reference 6-max 100bb core",
            "kind": "hand-authored",
            "reference": "scripts/build_preflop_chart_artifact.py",
        },
        "generated_at": GENERATED_AT,
        "table_size": TABLE_SIZE,
        "stack_depth_bb": STACK_DEPTH_BB,
        "positions": list(table_positions(TABLE_SIZE)),
        "spots": spots,
        "action_weights": {
            spot_id: {
                hand_class_text: dict(actions) for hand_class_text, actions in hand_classes
            }
            for spot_id, hand_classes in action_weights
        },
        "audit_fields": {
            "weights_sha256": weights_checksum(action_weights),
            "spot_count": len(spots),
            "hand_class_count": hand_class_count,
            "notes": (
                "Hand-authored reference ranges, not solver output. Every spot covers all 169 "
                "hand classes with a single pure action so uncovered spots, not uncovered "
                "hands, are what fail closed."
            ),
        },
    }


def main() -> int:
    payload = build_payload()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # Insertion order matters: the importer requires action_weights ordered like
    # spots, and hand classes ordered by grid index, so sorting keys would fail.
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
