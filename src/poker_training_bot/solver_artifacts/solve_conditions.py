"""What game the chart was solved in, and how much of it the numbers actually cover.

Three fields arrive with artifact schema 2 and they answer questions the chart could not
express before:

- `blind_structure`, decision 4. A chart solved at 0.5/1 was previously indistinguishable
  from one solved at 1/3, so the same hand at the same depth could be answered from a solve
  of a different game and nothing in the repo would say a word. That was phase 13's largest
  finding.
- `arriving_reach_bp`, decision 5. One value per cell, not per spot: a spot-level summary
  cannot tell a cell the solver trained from one it barely visited, and those are the same
  cells a later heuristic layer has to find.
- `arrival_ppb`, ruled 2026-08-27. Per spot, and orthogonal to reach: reach says whether
  hero can be holding that class here, arrival says whether anybody plays the line at all.
  Every class can be at full reach in a spot nobody ever reaches, which is exactly the case
  at `t6/d100/BB/BTN:raise@100`.

They live in their own module because `schema.py` and `importer.py` were both close to the
500-line cap when the bump landed, and because they are one subject: the conditions of the
solve rather than the strategy it produced. `schema` re-exports `BlindStructure`, which is
the name the frozen tests use. Both layers are here on purpose - the rule and the payload
reader for one field belong next to each other, and this module imports nothing from
`schema` or `importer`, so neither direction closes a cycle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from poker_training_bot.solver_artifacts.strict_json import (
    INVALID_VALUE,
    MISSING_FIELD,
    UNKNOWN_FIELD,
    _fail,
    _require_keys,
    _require_object,
    _require_unique_keys,
)

REACH_SCALE_BP = 10_000
"""Decision 8's basis-point scale, the artifact's own copy of it.

`gtopen_export.QUANTISATION_SCALE` is the same number on the export side, and it is not
imported here: the artifact schema must not depend on one source format's reader, or a
second export format would have to arrive through GTOpen's module to be validated.
"""

ARRIVAL_SCALE_PPB = 1_000_000_000
"""Parts per billion, and the grain is the point rather than the precision.

21 of the 86 committed spots sit at a nonzero arrival below one basis point, the smallest at
2.5e-08. In basis points every one of them would round to zero and become indistinguishable
from the eight spots the solve genuinely never reaches, which is the single distinction this
field exists to carry.
"""

# Spot key -> ordered (hand class, basis points). Ordered because two maps over the same
# keys in different orders serialise differently, which is the same reason `action_weights`
# is ordered rather than a mapping.
ArrivingReach = tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
# Spot key -> parts per billion. One value per spot, so no hand class appears.
ArrivalProbabilities = tuple[tuple[str, int], ...]

_BLIND_KEYS = {"small_blind_bb", "big_blind_bb", "ante_bb"}


@dataclass(frozen=True)
class BlindStructure:
    """The blinds and ante the solve posted, in big blinds.

    Validated on construction rather than merely stored. A field nothing validates is one a
    later artifact can fill with anything, and a lookup refusing a mismatched table would
    then be comparing against a number that never described a game. A zero ante is a real
    table and passes; blinds that are not both positive, or a small blind that is not
    smaller than the big blind, describe no game at all.
    """

    small_blind_bb: float
    big_blind_bb: float
    ante_bb: float

    def __post_init__(self) -> None:
        for field in _BLIND_KEYS:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"{field} must be a number, got {value!r}")
            if not math.isfinite(value):
                raise ValueError(f"{field} must be finite, got {value!r}")
        if self.small_blind_bb <= 0.0 or self.big_blind_bb <= 0.0:
            raise ValueError(
                "a blind structure needs both blinds posted, got"
                f" small_blind_bb={self.small_blind_bb!r}, big_blind_bb={self.big_blind_bb!r}"
            )
        if self.small_blind_bb >= self.big_blind_bb:
            raise ValueError(
                f"small_blind_bb {self.small_blind_bb!r} must be smaller than big_blind_bb"
                f" {self.big_blind_bb!r}"
            )
        if self.ante_bb < 0.0:
            raise ValueError(f"ante_bb cannot be negative, got {self.ante_bb!r}")


def _validate_scaled_int(value: Any, context: str, low: int, high: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{context} must be an integer, got {value!r}")
    if value < low or value > high:
        raise ValueError(f"{context} must be between {low} and {high}, got {value}")


def validate_arriving_reach(
    reach: ArrivingReach, declared: tuple[tuple[str, tuple[str, ...]], ...]
) -> None:
    """Every committed cell carries a reach, and nothing else does.

    `declared` is the artifact's own (spot key, hand classes) shape, so the reach map is
    checked against the cells the chart answers rather than against a count. A reach of zero
    is refused here: a cell hero cannot arrive at is a cell the solver never trained, and
    committing it would publish a strategy for a situation that does not occur.
    """
    keyed = [spot_id for spot_id, _ in reach]
    expected = [spot_id for spot_id, _ in declared]
    if keyed != expected:
        unknown = sorted(set(keyed) - set(expected))
        missing = sorted(set(expected) - set(keyed))
        if unknown:
            raise ValueError(f"arriving_reach_bp covers undeclared spots: {unknown}")
        if missing:
            raise ValueError(f"spots without an arriving reach: {missing}")
        raise ValueError("arriving_reach_bp must be ordered like spots")
    for (spot_id, cells), (_, classes) in zip(reach, declared, strict=True):
        named = [hand_class_text for hand_class_text, _ in cells]
        if named != list(classes):
            raise ValueError(
                f"arriving_reach_bp[{spot_id!r}] must carry exactly the hand classes"
                f" action_weights declares, in the same order: expected {list(classes)},"
                f" got {named}"
            )
        for hand_class_text, value in cells:
            _validate_scaled_int(
                value, f"arriving_reach_bp[{spot_id!r}][{hand_class_text!r}]", 1, REACH_SCALE_BP
            )


def validate_arrival_probabilities(
    arrival: ArrivalProbabilities, spot_ids: tuple[str, ...]
) -> None:
    """How often each recorded line is played, checked as a rule rather than stored.

    Zero is legal and load bearing: it marks the spots the solve never reaches, whose cells
    were ruled committed so a later heuristic layer can find them. Absent is not zero, so an
    empty map is refused - a spot missing from a map that has entries is a converter that did
    not compute the field there, and reading that as "never reached" would hand the heuristic
    layer every spot the converter failed on. A partial map is accepted, in spot order, for
    the same reason: what it says is true of the spots it names.
    """
    if not arrival:
        raise ValueError(
            "arrival_ppb records no spot at all; an empty map is a field that was never"
            " computed rather than a chart whose lines are never played"
        )
    remaining = list(spot_ids)
    for spot_id, value in arrival:
        if spot_id not in spot_ids:
            raise ValueError(f"arrival_ppb covers undeclared spot {spot_id!r}")
        if spot_id not in remaining:
            raise ValueError(
                f"arrival_ppb must follow spots order; {spot_id!r} arrives out of order"
            )
        del remaining[: remaining.index(spot_id) + 1]
        _validate_scaled_int(value, f"arrival_ppb[{spot_id!r}]", 0, ARRIVAL_SCALE_PPB)


def reach_payload(reach: ArrivingReach) -> dict[str, dict[str, int]]:
    return {spot_id: dict(cells) for spot_id, cells in reach}


def arrival_payload(arrival: ArrivalProbabilities) -> dict[str, int]:
    return dict(arrival)


def parse_blind_structure(payload: dict[str, Any], origin: str) -> BlindStructure:
    """Read `blind_structure` out of an artifact payload, or refuse the file."""
    path = "artifact.blind_structure"
    raw = _require_object(payload.get("blind_structure"), origin, path)
    _require_unique_keys(raw, origin, path, INVALID_VALUE)
    _require_keys(raw, origin, path, _BLIND_KEYS)
    for key in sorted(_BLIND_KEYS):
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise _fail(INVALID_VALUE, origin, f"{path}.{key} must be a number, got {value!r}")
    try:
        return BlindStructure(
            small_blind_bb=float(raw["small_blind_bb"]),
            big_blind_bb=float(raw["big_blind_bb"]),
            ante_bb=float(raw["ante_bb"]),
        )
    except ValueError as error:
        raise _fail(INVALID_VALUE, origin, f"{path}: {error}") from error


def parse_arriving_reach(
    payload: dict[str, Any],
    origin: str,
    declared: tuple[tuple[str, tuple[str, ...]], ...],
    duplicate_spot_code: str,
) -> ArrivingReach:
    """Read `arriving_reach_bp`, in the artifact's own spot and class order.

    Reordered onto the declared cells rather than required in order, exactly as
    `action_weights` is: a payload written in another order is a file the reader can trust,
    and the ordering rule is the schema's to enforce on the structure it builds. The spots a
    payload names that the artifact does not declare are the caller's own rejection, since
    the code for it belongs to the importer's poker-specific vocabulary.
    """
    path = "artifact.arriving_reach_bp"
    mapping = _require_object(payload.get("arriving_reach_bp"), origin, path)
    _require_unique_keys(mapping, origin, path, duplicate_spot_code)
    entries: list[tuple[str, tuple[tuple[str, int], ...]]] = []
    for spot_id, classes in declared:
        spot_path = f"{path}[{spot_id!r}]"
        if spot_id not in mapping:
            raise _fail(MISSING_FIELD, origin, f"{path} is missing a reach for spot {spot_id!r}")
        cells = _require_object(mapping[spot_id], origin, spot_path)
        _require_unique_keys(cells, origin, spot_path, INVALID_VALUE)
        unknown = sorted(set(cells) - set(classes))
        if unknown:
            raise _fail(
                UNKNOWN_FIELD,
                origin,
                f"{spot_path} carries a reach for hand classes the spot does not"
                f" declare: {unknown}",
            )
        for hand_class_text in classes:
            if hand_class_text not in cells:
                raise _fail(
                    MISSING_FIELD,
                    origin,
                    f"{spot_path} is missing a reach for {hand_class_text!r}",
                )
        row = tuple((hand_class_text, cells[hand_class_text]) for hand_class_text in classes)
        for hand_class_text, value in row:
            try:
                _validate_scaled_int(
                    value, f"{spot_path}[{hand_class_text!r}]", 1, REACH_SCALE_BP
                )
            except ValueError as error:
                raise _fail(INVALID_VALUE, origin, str(error)) from error
        entries.append((spot_id, row))
    return tuple(entries)


def parse_arrival_probabilities(
    payload: dict[str, Any], origin: str
) -> ArrivalProbabilities | None:
    """Read `arrival_ppb` if the payload carries it, in the order the payload wrote it.

    Order is preserved rather than normalised, because the schema's rule is that the map
    follows spot order and a reader that sorted it could not tell an unordered table from an
    ordered one. None means the key was absent, which is a v2 payload that predates the
    2026-08-27 ruling rather than a spot that is never reached.
    """
    if "arrival_ppb" not in payload:
        return None
    path = "artifact.arrival_ppb"
    mapping = _require_object(payload.get("arrival_ppb"), origin, path)
    _require_unique_keys(mapping, origin, path, INVALID_VALUE)
    for spot_id, value in mapping.items():
        if isinstance(value, bool) or not isinstance(value, int):
            raise _fail(
                INVALID_VALUE,
                origin,
                f"{path}[{spot_id!r}] must be an integer count of parts per billion,"
                f" got {value!r}",
            )
    return tuple(mapping.items())
