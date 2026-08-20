"""Turn the committed solver export into the artifact, sizings, and expectations.

The artifact is derived, never hand-edited. Everything this writes is reproducible
from `data/artifacts/preflop/sources/`, which is what makes `--check` meaningful: a
chart nobody can regenerate is a chart nobody can diff against its origin.

Three transformations happen here, and each one loses information on purpose.

Position names are renamed into this repo's vocabulary. The source calls the first
seat to act at six-handed `UTG`; `poker_core.positions` calls it `LJ`.

Hero's own raise offers collapse. At the spot hero is deciding, an all-in offer and a
named raise are both `raise` and their weights add, because the artifact holds what
hero does rather than at what price. The sizes themselves are not thrown away: they
are written to the sizing table, which is where the strategy reads them. The raises
*in front of* hero are a different thing entirely and they do carry their price, in
the spot key, which is what phase 12 added.

For a spot where hero has already acted, the source normalizes strategy within
hero's own range. Hands hero would never have opened carry a normalized strategy
for a holding hero cannot have, so they are dropped rather than committed: an
uncovered class is an explicit lookup miss, which is honest, where a fabricated
strategy is not.

Every size that enters a key comes from the source's own action label at the spot the
raise was made at, never from a constant here. Facing an `LJ` open is 2.5 because
`RFI_UTG` offers `Raise 2.5`; facing a three-bet from the button carries the button's
own label at `BTN_vs_UTG_open`. So a re-solve at different sizings re-keys the
artifact by itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.poker_core.positions import table_positions  # noqa: E402
from poker_training_bot.solver_artifacts.schema import (  # noqa: E402
    ARTIFACT_SCHEMA_VERSION,
    PREFLOP_ACTIONS,
    PreflopAction,
    action_entry_payload,
    spot_key,
)

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
SOURCE = PREFLOP_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
ARTIFACT = PREFLOP_DIR / "six_max_nl25_100bb.json"
SIZINGS = PREFLOP_DIR / "sizings" / "six_max_nl25_100bb.json"
EXPECTATIONS = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"

TABLE_SIZE = 6
DEPTH_BB = 100
# The date this file was re-derived, not the date the ranges were extracted. Re-keying
# writes a new file, and a file claiming to predate the vocabulary it is written in
# would be false about itself - and would tie with its own predecessor in
# `lookup._artifact_sort_key`, which breaks ties on exactly this field.
GENERATED_AT = "2026-08-20T00:00:00Z"
RANGES_EXTRACTED_AT = "2026-08-11"
RANGE_EPSILON = 0.0005

# The source's six-handed labels against this repo's vocabulary. Only the first
# seat to act differs, and it differs because `poker_core.positions` fills
# non-blind seats backwards from the button rather than forwards from under the gun.
POSITION_MAP = {"UTG": "LJ", "HJ": "HJ", "CO": "CO", "BTN": "BTN", "SB": "SB", "BB": "BB"}

SOURCE_NAME = "GTO Wizard 6-max 100bb NL25 rake"
SOURCE_NOTES = (
    "Solver export from GTO Wizard solution Cash6mGeneral_6mNL25R25, six-max cash,"
    " 100bb effective, NL25 rake, cold calls allowed. The ranges are the"
    f" {RANGES_EXTRACTED_AT} extraction re-keyed at the phase 12 spot vocabulary, not a"
    " new solve: every spot key now carries the raise-to size in big blinds of each"
    " raise in front of hero, and the per-hand per-action weights are unchanged."
    " Hero's own raise offers still collapse into the single raise action, and hero's"
    " own size is committed separately in sizings/six_max_nl25_100bb.json. Spots where"
    " hero has already acted cover only hands inside hero's own opening range, so a"
    " hand hero could not hold is an explicit lookup miss rather than a fabricated"
    " strategy."
)


def parse_range(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for item in filter(None, text.split(",")):
        hand, weight = item.split(":")
        out[hand] = float(weight)
    return out


def repo_action(label: str) -> str:
    """Map a source action label onto the four preflop action names."""
    head = label.split()[0].lower()
    if head in {"raise", "allin"}:
        return "raise"
    if head in {"fold", "call", "check"}:
        return head
    raise ValueError(f"unknown source action label: {label!r}")


def raise_size_bb(actions: list[dict]) -> float | None:
    """The named raise size at a spot, ignoring the all-in offer.

    All-in is a raise like any other for the artifact, but it is not a sizing a
    strategy should pick: it is the stack, not a solved bet size.
    """
    for action in actions:
        label = action["label"]
        if label.lower().startswith("raise "):
            return float(label.split()[1])
    return None


def size_at(spots: dict[str, dict], source_key: str) -> float:
    """The raise-to size the source's own action label declares at one of its spots.

    Fails loudly rather than defaulting. A missing size here would mean the export
    stopped describing the line a key depends on, and inventing one is exactly the
    hand-authored number this whole file exists to keep out.
    """
    spot = spots.get(source_key)
    if spot is None:
        raise ValueError(f"the export has no spot {source_key!r} to take a raise size from")
    size = raise_size_bb(spot["actions"])
    if size is None:
        raise ValueError(f"the export's spot {source_key!r} offers no named raise size")
    return size


def hero_and_sequence(
    key: str, hero_source: str, spots: dict[str, dict]
) -> tuple[str, tuple[PreflopAction, ...]]:
    """Hero's position and the sized action sequence in front of hero.

    Each size is read from the spot at which that raise was actually offered, so the
    key's provenance is the export rather than this script.
    """
    hero = POSITION_MAP[hero_source]
    if key.startswith("RFI_"):
        return hero, ()
    facing = key.split("_vs_")[1]
    if key.endswith("_open"):
        opener_source = facing.removesuffix("_open")
        opener = POSITION_MAP[opener_source]
        return hero, (PreflopAction(opener, "raise", size_at(spots, f"RFI_{opener_source}")),)
    if key.endswith("_limp"):
        limper = POSITION_MAP[facing.removesuffix("_limp")]
        return hero, (PreflopAction(limper, "call"),)
    if key.endswith("_3bet"):
        three_bettor_source = facing.removesuffix("_3bet")
        three_bettor = POSITION_MAP[three_bettor_source]
        return hero, (
            PreflopAction(hero, "raise", size_at(spots, f"RFI_{hero_source}")),
            PreflopAction(
                three_bettor,
                "raise",
                size_at(spots, f"{three_bettor_source}_vs_{hero_source}_open"),
            ),
        )
    raise ValueError(f"unrecognized spot key: {key!r}")


def hero_range(spot_key_name: str, spots: dict[str, dict]) -> dict[str, float] | None:
    """Hero's own range at a spot where hero has already acted.

    None means hero has not acted yet, so every hand is possible.
    """
    if not spot_key_name.endswith("_3bet"):
        return None
    opener = spot_key_name.split("_vs_")[0]
    rfi = spots[f"RFI_{opener}"]
    label = next(
        name for name in rfi["strategy"] if name.lower().startswith("raise")
    )
    return parse_range(rfi["strategy"][label])


def build_weights(source: dict) -> dict[str, dict[str, dict[str, float]]]:
    spots = {spot["key"]: spot for spot in source["spots"]}
    weights: dict[str, dict[str, dict[str, float]]] = {}
    for key, spot in spots.items():
        hero, sequence = hero_and_sequence(key, spot["hero"], spots)
        derived_key = spot_key(TABLE_SIZE, DEPTH_BB, hero, sequence)
        possible = hero_range(key, spots)
        per_hand: dict[str, dict[str, float]] = {}
        for label, encoded in spot["strategy"].items():
            action = repo_action(label)
            for hand, weight in parse_range(encoded).items():
                if possible is not None and possible.get(hand, 0.0) <= RANGE_EPSILON:
                    continue
                bucket = per_hand.setdefault(hand, {})
                bucket[action] = round(bucket.get(action, 0.0) + weight, 6)
        weights[derived_key] = {
            hand: normalize(actions) for hand, actions in sorted(per_hand.items())
        }
    return weights


def normalize(actions: dict[str, float]) -> dict[str, float]:
    """Scale one hand's weights to sum to exactly one, in the artifact's action order.

    The source publishes frequencies rounded to four decimals, so a hand can add up
    to 0.9999 and the importer rejects anything outside a millionth of one. The
    residue is rounding in the export, not a real strategy, so it is scaled out and
    the largest action absorbs the last ulp. Doing this in the converter keeps it
    visible and reproducible; doing it in the importer would mean loosening a
    validation to admit a file, which the contract forbids.
    """
    present = {
        action: actions[action]
        for action in PREFLOP_ACTIONS
        if actions.get(action, 0.0) > 0.0
    }
    total = sum(present.values())
    scaled = {action: round(weight / total, 6) for action, weight in present.items()}
    largest = max(scaled, key=lambda action: (scaled[action], action))
    scaled[largest] = round(scaled[largest] + (1.0 - sum(scaled.values())), 6)
    return scaled


def checksum(weights: dict) -> str:
    text = json.dumps(weights, sort_keys=True, separators=(",", ":"))
    return sha256(text.encode("utf-8")).hexdigest()


def build_artifact(source: dict) -> dict:
    weights = build_weights(source)
    spots = {spot["key"]: spot for spot in source["spots"]}
    definitions = []
    for key, spot in spots.items():
        hero, sequence = hero_and_sequence(key, spot["hero"], spots)
        definitions.append(
            {
                "spot_id": spot_key(TABLE_SIZE, DEPTH_BB, hero, sequence),
                "hero_position": hero,
                "action_sequence": [action_entry_payload(entry) for entry in sequence],
            }
        )
    definitions.sort(key=lambda item: item["spot_id"])
    hand_classes = {hand for spot in weights.values() for hand in spot}
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source": {
            "name": SOURCE_NAME,
            "kind": "solver-export",
            "reference": "data/artifacts/preflop/sources/gtowizard_6max_nl25_100bb_preflop.json",
        },
        "generated_at": GENERATED_AT,
        "table_size": TABLE_SIZE,
        "stack_depth_bb": DEPTH_BB,
        "positions": list(table_positions(TABLE_SIZE)),
        "spots": definitions,
        "action_weights": weights,
        "audit_fields": {
            "weights_sha256": checksum(weights),
            "spot_count": len(definitions),
            "hand_class_count": len(hand_classes),
            "notes": SOURCE_NOTES,
        },
    }


def build_sizings(source: dict) -> dict:
    spots = {spot["key"]: spot for spot in source["spots"]}
    sizes: dict[str, float] = {}
    for key, spot in spots.items():
        hero, sequence = hero_and_sequence(key, spot["hero"], spots)
        size = raise_size_bb(spot["actions"])
        if size is not None:
            sizes[spot_key(TABLE_SIZE, DEPTH_BB, hero, sequence)] = size
    return {
        "schema_version": 1,
        "source": {
            "name": SOURCE_NAME,
            "kind": "solver-export",
            "reference": "data/artifacts/preflop/sources/gtowizard_6max_nl25_100bb_preflop.json",
        },
        "notes": (
            "Raise size in big blinds for each covered spot, taken from the solution the"
            " ranges came from. The all-in offer is deliberately excluded: it is a stack,"
            " not a solved bet size. A spot absent here has no size, and the strategy"
            " refuses rather than inventing one."
        ),
        "raise_to_bb": dict(sorted(sizes.items())),
    }


def build_expectations(source: dict) -> dict:
    spots = {spot["key"]: spot for spot in source["spots"]}

    def pct(spot: dict, predicate) -> float:
        total = sum(action["combos"] for action in spot["actions"])
        chosen = sum(action["combos"] for action in spot["actions"] if predicate(action["label"]))
        return round(100.0 * chosen / total, 2)

    opens = {}
    limps = {}
    for source_position, repo_position in POSITION_MAP.items():
        key = f"RFI_{source_position}"
        if key in spots:
            # Raise only. A small-blind limp is entering the pot but it is not an
            # open, and folding the two together would hide a 14% strategy.
            opens[repo_position] = pct(spots[key], lambda label: repo_action(label) == "raise")
            limp = pct(spots[key], lambda label: repo_action(label) == "call")
            if limp > 0.0:
                limps[repo_position] = limp
    defence = {}
    for source_position, repo_position in POSITION_MAP.items():
        key = f"BB_vs_{source_position}_open"
        if key in spots:
            defence[repo_position] = pct(
                spots[key], lambda label: not label.startswith("Fold")
            )
    return {
        "schema_version": 1,
        "source": SOURCE_NAME,
        "notes": (
            "Aggregate frequencies as the source itself displayed them, in poker terms a"
            " reviewer can check without reading code. These are the only numbers in this"
            " phase that this repo did not produce, so they are what catches a range that"
            " is uniformly wrong rather than merely self-consistent."
        ),
        "open_frequency_pct": dict(sorted(opens.items())),
        "limp_frequency_pct": dict(sorted(limps.items())),
        "big_blind_defence_pct": dict(sorted(defence.items())),
    }


def render(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def outputs(source: dict) -> list[tuple[Path, str]]:
    return [
        (ARTIFACT, render(build_artifact(source))),
        (SIZINGS, render(build_sizings(source))),
        (EXPECTATIONS, render(build_expectations(source))),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed files match what this script produces",
    )
    args = parser.parse_args()
    source = json.loads(SOURCE.read_text(encoding="utf-8"))

    stale: list[str] = []
    for path, text in outputs(source):
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(path.relative_to(REPO_ROOT)))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    if args.check:
        if stale:
            for name in stale:
                print(f"{name} does not match its source export", file=sys.stderr)
            return 1
        print("committed preflop files reproduce from their source")
        return 0

    print(f"wrote {ARTIFACT.name}, {SIZINGS.name}, {EXPECTATIONS.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
