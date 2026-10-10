"""How one stored street's rows are written: the turn's two-byte whole counts, and its objects.

Decision 15, as Taylor re-ruled it on 2026-10-03: every turn frequency is rounded to a tenth of a
percent, which is the flop's thousandths, with the flop's rule that the largest entry pays the
rounding residue so a decision still sums to one, and storage stays two bytes a number.

**The rounding is the flop's own, called rather than copied.** `postflop_harvest._rounded` makes
a flop cell's row; a turn row is that same row written as whole counts, so one rule rounds every
street and a later change to it cannot leave two streets disagreeing.

**Two bytes a number is a whole count of thousandths, not a half-precision float.** Each stored
number is an unsigned integer from 0 to 1,000, little-endian, since every candidate box (x86 and
Graviton) is little-endian and a reader then maps the words with no byte swap. A decoder refuses a
word above 1,000 and a row whose words do not sum to 1,000, which is what a half-precision row read
as counts looks like.

**An object is a header and its decision points, each carrying its own shape.** Little-endian
throughout:

    magic "PBTR" (4 bytes), format version (u16), decision points (u32)
    then per decision point: actions (u16), rows (u32), rows * actions counts (u16 each)

The count in the header is checked against the decision points the body actually holds, and a
body that ends early or runs on is refused, so a truncated or padded upload never reads as a
shorter or longer street. The decision points are in the order the harvest walks the line's tree;
the format holds rows only, and naming each point is for the phase that plays the turn.

**The river is never stored** (decision 1, re-ruled 2026-10-04): it is solved at the table, so
this format is the turn's alone and nothing here encodes, counts or reads a river object. Whether
standard compression earns its keep over these words is measured on the trial flops, not assumed.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

from poker_training_bot.solver_artifacts import postflop_harvest

STORED_SCALE = postflop_harvest.WEIGHT_SCALE
"""Thousandths, the flop's scale: a stored word is a frequency times this, as a whole number."""

BYTES_PER_NUMBER = 2
"""Decision 15: two bytes a number, a whole count from 0 to `STORED_SCALE`."""

OBJECT_MAGIC = b"PBTR"
OBJECT_FORMAT_VERSION = 1

_WORD = "H"
_HEADER = struct.Struct("<4sHI")
_POINT_HEADER = struct.Struct("<HI")
_MAX_ACTIONS = 0xFFFF
_MAX_ROWS = 0xFFFFFFFF


def _row_counts(row: Sequence[float]) -> tuple[int, ...]:
    """One solver row as whole thousandths by the flop's rule, or a refusal."""
    if len(row) == 0:
        raise ValueError("a row with no actions cannot be stored")
    rounded = postflop_harvest._rounded(row)
    counts = tuple(round(value * STORED_SCALE) for value in rounded)
    if sum(counts) != STORED_SCALE:
        raise ValueError(f"the flop's rounding did not sum to {STORED_SCALE}: {list(row)}")
    return counts


def _checked_counts(counts: Sequence[int]) -> tuple[float, ...]:
    """Stored counts as frequencies, refusing anything that is not a row of thousandths."""
    if not counts:
        raise ValueError("a stored row holds no counts")
    over = [count for count in counts if count > STORED_SCALE]
    if over:
        raise ValueError(f"a stored count above {STORED_SCALE} is not thousandths: {over}")
    if sum(counts) != STORED_SCALE:
        raise ValueError(
            f"a stored row must sum to {STORED_SCALE} thousandths, got {sum(counts)}: "
            f"{list(counts)}"
        )
    return tuple(count / STORED_SCALE for count in counts)


def encode_row(row: Sequence[float]) -> bytes:
    """One solver row as two-byte whole thousandths, residue on the largest entry.

    Refuses what the flop's rule refuses: a negative entry, or a row too far from one for its
    largest entry to pay the residue. `HarvestError` is a `ValueError`, so every refusal here is
    one."""
    counts = _row_counts(row)
    return struct.pack(f"<{len(counts)}{_WORD}", *counts)


def decode_row(data: bytes) -> tuple[float, ...]:
    """One stored row back as frequencies, exactly the tuple the flop's rule made of it."""
    if len(data) == 0 or len(data) % BYTES_PER_NUMBER:
        raise ValueError(
            f"a stored row is whole {BYTES_PER_NUMBER}-byte words, got {len(data)} bytes"
        )
    counts = struct.unpack(f"<{len(data) // BYTES_PER_NUMBER}{_WORD}", data)
    return _checked_counts(counts)


def encode_street_object(points: Sequence[Sequence[Sequence[float]]]) -> bytes:
    """Every decision point of one board's street, in walk order, as one object.

    A decision point is its rows, one per hand, each a solver row over the point's actions; every
    row of one point must have the same width, because a point offers one menu."""
    parts = [_HEADER.pack(OBJECT_MAGIC, OBJECT_FORMAT_VERSION, len(points))]
    for index, point in enumerate(points):
        if len(point) == 0:
            raise ValueError(f"decision point {index} holds no rows")
        widths = {len(row) for row in point}
        if len(widths) != 1:
            raise ValueError(f"decision point {index} mixes rows of widths {sorted(widths)}")
        actions = widths.pop()
        if not 0 < actions <= _MAX_ACTIONS or len(point) > _MAX_ROWS:
            raise ValueError(f"decision point {index} has a shape the format cannot hold")
        parts.append(_POINT_HEADER.pack(actions, len(point)))
        counts = [count for row in point for count in _row_counts(row)]
        parts.append(struct.pack(f"<{len(counts)}{_WORD}", *counts))
    return b"".join(parts)


def _walk(data: bytes):
    """Yield each decision point's (actions, rows, offset of its first count), refusing an object
    whose header, body or length does not hold together."""
    if len(data) < _HEADER.size:
        raise ValueError(f"a street object is at least {_HEADER.size} bytes, got {len(data)}")
    magic, version, declared = _HEADER.unpack_from(data, 0)
    if magic != OBJECT_MAGIC:
        raise ValueError(f"not a stored street object: magic {magic!r}")
    if version != OBJECT_FORMAT_VERSION:
        raise ValueError(f"street object format {version} is unsupported")
    offset = _HEADER.size
    for index in range(declared):
        if offset + _POINT_HEADER.size > len(data):
            raise ValueError(f"the object ends inside decision point {index} of {declared}")
        actions, rows = _POINT_HEADER.unpack_from(data, offset)
        if actions == 0 or rows == 0:
            raise ValueError(f"decision point {index} declares {actions} actions, {rows} rows")
        offset += _POINT_HEADER.size
        end = offset + actions * rows * BYTES_PER_NUMBER
        if end > len(data):
            raise ValueError(f"the object ends inside decision point {index} of {declared}")
        yield actions, rows, offset
        offset = end
    if offset != len(data):
        raise ValueError(
            f"the object runs {len(data) - offset} bytes past its {declared} decision points"
        )


def decode_street_object(data: bytes) -> list[tuple[tuple[float, ...], ...]]:
    """Every decision point of a stored street object, each a tuple of its rows as frequencies."""
    points = []
    for actions, rows, offset in _walk(data):
        counts = struct.unpack_from(f"<{actions * rows}{_WORD}", data, offset)
        points.append(
            tuple(
                _checked_counts(counts[start : start + actions])
                for start in range(0, actions * rows, actions)
            )
        )
    return points


def street_object_decision_points(data: bytes) -> int:
    """How many decision points a stored street object holds, read from its own bytes.

    The header's count alone is a claim; this walks every point's shape to the last byte, so an
    object whose body does not hold what its header says is refused rather than counted. It does
    not decode the rows: that is `decode_street_object`'s, and a count is what the fetch needs."""
    return sum(1 for _ in _walk(data))
