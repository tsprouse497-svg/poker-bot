"""Reading a committed spot key, and building a line out of the prices the chart solved.

**A support module, not a test module, and the split is a line cap and nothing more.**
`test_preflop_committed_charts.py` owns every count and every assertion about the committed
chart; this is the grammar those assertions are written in, and `test_preflop_committed_lookup.py`
was already reaching six of these names through that file. MAINT-34 forced the split: the branched
price ladder did not fit under the 700-line cap, and the ruling was to split rather than to
compress a phase's reasoning to make room.

Both files reach these through `test_preflop_committed_charts`, which re-exports them and owns
which of them are part of the phase's vocabulary.
"""

from __future__ import annotations

from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

DEPTH_BB = 100


def rfi_key(seat: str) -> str:
    return f"t6/d{DEPTH_BB}/{seat}/rfi"


def hero_seat(spot_key_text: str) -> str:
    return spot_key_text.split("/")[2]


def raises_faced(spot_key_text: str) -> int:
    return spot_key_text.count(":raise@")


def cold_callers(spot_key_text: str) -> int:
    return spot_key_text.count(":call")


def prices_in(spot_key_text: str) -> list[float]:
    return [
        float(part.split(":raise@")[1])
        for part in spot_key_text.split("/", 3)[3].split(",")
        if ":raise@" in part
    ]


def solved_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[PreflopAction, ...]:
    """`hero`'s line where each named seat raises at the price the chart solved there.

    "There" is the spot **that seat** is acting at, not hero's. `solved_prices_bb` is addressed by
    the spot's own hero, so hero's own raise is priced only by keys deeper than it - and for hero's
    three-bet that key is the four-bet-facing one the depth clause withholds, which is why reading
    it there worked on the retired chart and stopped working here. The sizing table prices each
    committed spot directly, so each step reads the key its own raiser faces; `min` is the entry.

    The line the refusal tests want is then built entirely out of committed spots even though the
    spot it arrives at is not - `CO/rfi`, `BB/CO:raise@2.5` and `CO/CO:raise@2.5,BB:raise@13.5`
    price 2.5, 13.5 and 40.5 - and each step asserts its own spot is committed as it goes.
    """
    sizing = PreflopSizingTable.from_repo()
    declared = set(library.spot_keys())
    sequence: list[PreflopAction] = []
    for raiser in raisers:
        key = derive_spot_key(6, DEPTH_BB, raiser, tuple(sequence))
        prices = {size for name in HAND_CLASSES for size, _ in (sizing.sizes_bb(key, name) or ())}
        assert key in declared and prices, (hero, raiser, key)
        sequence.append(PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


def solved_key(library: PreflopChartLibrary, hero: str, *raisers: str) -> str:
    return derive_spot_key(6, DEPTH_BB, hero, solved_line(library, hero, *raisers))
