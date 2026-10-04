"""Phase 21, stage 4: how a turn or river frequency is stored, and how an object is counted.

Authored before any implementation exists, from decision 15 of
`reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md` as Taylor re-ruled it on
2026-10-03: **every turn and river frequency is rounded to a tenth of a percent, which is the flop's
thousandths, with the flop's rule that the largest entry pays the rounding residue so a decision
still sums to one; storage stays two bytes a number.** Stage 6 writes the format and cannot write
its tests, because stage 5 takes `tests/**` out of scope, so the format is pinned here or nowhere.

**The rounding is the flop's own, not a second copy of it.** `postflop_harvest._rounded` already
makes a flop cell's row: thousandths, summed in integers, residue to the largest entry. A turn or
river row encoded and decoded must equal exactly what that function makes of the same solver row,
so one rule rounds every street and a later change to it cannot leave two streets disagreeing.

**Two bytes a number means a whole count, not a half-precision float.** Each stored number is the
row entry in thousandths, an unsigned integer from 0 to 1,000, little-endian - both x86 and
Graviton are little-endian, so a reader maps the words with no byte swap. IEEE half precision is
also two bytes and is the plausible wrong reading: near 1.0 it steps in about 0.0005, so its rows
are neither thousandths nor exactly one in sum, and 23 TB of river would be committed in a format
the ruling does not describe. A decoder refuses a word above 1,000 and a row whose words do not sum
to 1,000, which is what a half-precision row read as counts looks like.

**An object's decision-point count is read back from the object.** The manifest and the line index
claim 6,419 turn and 1,477,056 river decision points a board; the fetch checks a fetched flop
object by its keys (`tests/test_flop_campaign_raise_key.py`), and checks a turn or river object by
the count this module reads out of it. How an object lays out its rows, and whether it is
compressed - the trial flops measure that - is stage 6's; these tests pin the round trip, the
words and the count, not the layout.

`solver_artifacts.postflop_street_rows` is the module, named the way its siblings are: it is the
store of one street's rows, as `postflop_harvest` is the harvest and `postflop_fetch` the fetch.
"""

from __future__ import annotations

import json
import struct

import pytest

from poker_training_bot.solver_artifacts import postflop_harvest as harvest
from tests.test_flop_campaign_manifest import (
    CLOSED_COUNTS,
    INDEX_KEY,
    DictStore,
    published_line,
    sha256,
)


@pytest.fixture(scope="module")
def rows():
    """`solver_artifacts.postflop_street_rows`: the turn and river row format."""
    import poker_training_bot.solver_artifacts.postflop_street_rows as module

    return module


@pytest.fixture(scope="module")
def fetch():
    """`solver_artifacts.postflop_fetch`: the command a fresh machine runs, as a function."""
    import poker_training_bot.solver_artifacts.postflop_fetch as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; decision 15 as re-ruled requires it and no"
        " implementation has been written yet"
    )
    return found


SOLVER_ROWS = (
    (1 / 3, 1 / 3, 1 / 3),
    (0.33349, 0.66651),
    (0.0004, 0.9996),
    (0.12351, 0.23449, 0.64204),
    (0.49951, 0.50049),
    (0.3337, 0.3337, 0.3337),
    (0.0, 0.0, 1.0),
    (0.00049, 0.0012, 0.4971, 0.50121),
)
"""Rows as the solver answers them, tails and all: thirds that round to 999 and give the missing
thousandth to the first of the tied largest entries, entries astride a half thousandth, a row
summing to 1.0011 whose counts come to 1,002 and whose first largest entry pays the two back
(0.332, 0.334, 0.334), a pure row, and one whose smallest entry rounds to zero."""


class TestARowIsStoredInThousandths:
    @pytest.mark.parametrize("row", SOLVER_ROWS, ids=range(len(SOLVER_ROWS)))
    def test_a_row_round_trips_to_exactly_the_flop_s_rounding(self, rows, row) -> None:
        encoded = owed(rows, "encode_row")(row)

        assert owed(rows, "decode_row")(encoded) == harvest._rounded(row)

    def test_the_thirds_land_where_the_flop_rule_puts_the_residue(self, rows) -> None:
        """An anchor that does not lean on `_rounded`: 333 three times is 999, and the one
        thousandth left goes to the first of the tied largest entries."""
        decoded = owed(rows, "decode_row")(owed(rows, "encode_row")((1 / 3, 1 / 3, 1 / 3)))

        assert decoded == (0.334, 0.333, 0.333)

    @pytest.mark.parametrize("row", SOLVER_ROWS, ids=range(len(SOLVER_ROWS)))
    def test_each_stored_number_is_a_whole_count_of_thousandths_in_two_bytes(self, rows, row):
        encoded = owed(rows, "encode_row")(row)

        assert len(encoded) == 2 * len(row)
        counts = struct.unpack(f"<{len(row)}H", encoded)
        assert all(0 <= count <= 1000 for count in counts)
        assert sum(counts) == 1000
        assert tuple(count / 1000 for count in counts) == harvest._rounded(row)

    def test_the_words_are_little_endian_unsigned_counts(self, rows) -> None:
        assert owed(rows, "encode_row")((1 / 3, 1 / 3, 1 / 3)) == struct.pack("<3H", 334, 333, 333)

    def test_the_scale_is_the_flop_s(self, rows) -> None:
        assert owed(rows, "STORED_SCALE") == harvest.WEIGHT_SCALE == 1000
        assert owed(rows, "BYTES_PER_NUMBER") == 2


class TestARowThatIsNotThousandthsIsRefused:
    def test_a_half_precision_row_is_refused(self, rows) -> None:
        """0.25, 0.25 and 0.5 as IEEE half precision are the words 13312, 13312 and 14336."""
        with pytest.raises(ValueError):
            owed(rows, "decode_row")(struct.pack("<3e", 0.25, 0.25, 0.5))

    @pytest.mark.parametrize(
        "counts", [(500, 499), (500, 501), (1001, 0), (0, 0)], ids=["999", "1001", "over", "none"]
    )
    def test_a_row_whose_counts_do_not_sum_to_a_thousand_is_refused(self, rows, counts) -> None:
        with pytest.raises(ValueError):
            owed(rows, "decode_row")(struct.pack(f"<{len(counts)}H", *counts))

    def test_an_odd_number_of_bytes_is_refused(self, rows) -> None:
        with pytest.raises(ValueError):
            owed(rows, "decode_row")(struct.pack("<2H", 500, 500) + b"\x00")

    @pytest.mark.parametrize(
        "row", [(-0.01, 1.01), (0.4, 0.4, 0.4, 0.4), ()], ids=["negative", "sums to 1.6", "empty"]
    )
    def test_a_solver_row_the_flop_rule_cannot_round_is_refused(self, rows, row) -> None:
        """The rows `_rounded` itself refuses: a negative entry, and a residue larger than the
        largest entry can pay."""
        with pytest.raises(ValueError):
            owed(rows, "encode_row")(row)


def street_points(count: int, width: int = 2):
    """`count` decision points, each a few rows of `width` actions, as a solve answers them."""
    return [
        [tuple((index + hand + action + 1) / 7 for action in range(width)) for hand in range(3)]
        for index in range(count)
    ]


def normalised(points):
    return [[tuple(value / sum(row) for value in row) for row in point] for point in points]


class TestAStreetObjectIsCountedFromItsOwnBytes:
    def test_an_object_round_trips_every_row_through_the_flop_rule(self, rows) -> None:
        """Decision points of different widths in one object: three, two and four actions."""
        points = [
            *normalised(street_points(2, 3)),
            *normalised(street_points(3, 2)),
            *normalised(street_points(1, 4)),
        ]
        data = owed(rows, "encode_street_object")(points)

        decoded = owed(rows, "decode_street_object")(data)

        assert [list(point) for point in decoded] == [
            [harvest._rounded(row) for row in point] for point in points
        ]

    @pytest.mark.parametrize("count", [1, 14, CLOSED_COUNTS["turn"]])
    def test_the_decision_point_count_reads_back_from_the_object(self, rows, count) -> None:
        data = owed(rows, "encode_street_object")(normalised(street_points(count)))

        assert owed(rows, "street_object_decision_points")(data) == count

    def test_a_truncated_object_is_refused(self, rows) -> None:
        data = owed(rows, "encode_street_object")(normalised(street_points(5)))

        with pytest.raises(ValueError):
            owed(rows, "decode_street_object")(data[:-1])


def with_turn_objects(rows, counts):
    """The published line with each board's turn object replaced by an encoded one holding
    `counts[board]` decision points, digests and fingerprint updated to match, so only a count
    read out of the object itself can see a short one."""
    manifest, index, objects = published_line()
    objects = dict(objects)
    for board, count in zip(index["boards"], counts, strict=True):
        entry = board["objects"]["turn"]
        objects[entry["key"]] = owed(rows, "encode_street_object")(normalised(street_points(count)))
        entry["sha256"] = sha256(objects[entry["key"]])
    objects[INDEX_KEY] = json.dumps(index, sort_keys=True).encode()
    manifest["index"]["sha256"] = sha256(objects[INDEX_KEY])
    manifest["index"]["bytes"] = len(objects[INDEX_KEY])
    return manifest, objects


class TestTheFetchCountsATurnObject:
    """The contract's fetch checks every fetched object against the counts. A turn object that
    holds one decision point fewer than its board's 6,419, with every digest made to match, is
    refused on the count read out of it."""

    def test_a_turn_object_holding_the_board_s_count_fetches(self, rows, fetch, tmp_path):
        full = CLOSED_COUNTS["turn"]
        manifest, objects = with_turn_objects(rows, (full, full))

        owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("turn",))

        owed(fetch, "require_fetched")(manifest, tmp_path, street="turn")

    def test_a_turn_object_one_decision_point_short_is_refused(self, rows, fetch, tmp_path):
        full = CLOSED_COUNTS["turn"]
        manifest, objects = with_turn_objects(rows, (full, full - 1))

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("turn",))

        assert raised.value.code == owed(fetch, "DECISION_POINTS_MISMATCH")
