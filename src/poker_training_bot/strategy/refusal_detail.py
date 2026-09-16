"""What a refusal says about who asked, in one place for every strategy that refuses.

A refusal's detail has two halves and they answer different questions. One half is the gap
itself - the spot key, the board, the preflop line, the size that was off the menu - and it
belongs to the strategy that hit the gap, because only that strategy knows which step of its own
walk failed. The other half is the query: how many seats were at the table and what hero was
holding. That half is identical wherever it appears, and it is what this module owns.

**Why it is shared rather than written twice.** `PreflopChartStrategy` and
`PostflopBettingStrategy` refuse into one `refusal_inventory`, and a reader walking that file
reads both kinds of row. Two private copies of "name the table and the hand" is two chances for
the key names to drift apart, and a drift there does not look like a bug: it looks like two rows
about different things. The chart got there first - `_miss_detail` is the shape this follows -
and the betting strategy shipped without it, which is how ten of eleven postflop rows came to
read `classes: ()` while every preflop row named its hand.

**Why neither field fragments the inventory.** `simulator.measure.refusal_inventory` pops
`hand_class` out of the grouping key before it groups and keeps it as a sub-count, so naming the
hand fills the `classes` column without splitting one work item into one row per holding.
`table_size` stays in the key and belongs there: the same spot uncovered six-handed and uncovered
heads-up are two cells somebody has to solve. What
`REFUSAL-INVENTORY-FRAGMENTS-ON-PER-SEAT-DETAIL` bars is a seat number or a chip count, which
take a distinct value per hand; neither of these does.

**Adopting this in `preflop_chart` is a later task and needs no second seam.** Its
`_miss_detail` emits `spot_key`, `table_size`, `stack_depth_bb` and `hand_class`, and its
`hand_class` is `hand_classes.hand_class(query.hole_cards)` - this function's own call on this
function's own argument, so the strings are the same one - which makes the pair below a drop-in
for two of its four fields. The chart's extra two wrap around the pair rather than changing it:
`stack_depth_bb` would arrive here as an optional third field, and `spot_key` stays on the caller
because it is the gap rather than the query and is reported only when the vocabulary can express
the spot at all. The four refusals at `preflop_chart.py:373, 377, 428, 431` that carry no detail
whatever are what adoption would fix; they are a completed phase's and are filed, not fixed here.
"""

from __future__ import annotations

from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.strategy.contract import StrategyQuery

__all__ = ["asked_by"]


def asked_by(query: StrategyQuery) -> tuple[tuple[str, str], ...]:
    """Who was asking, for the front of a refusal detail.

    The table size and hero's hand as one of the **169 preflop-style classes** - `AA`, `AKs`,
    `AKo` - which is the vocabulary `refusal_inventory`'s `classes` column already speaks. A
    postflop strategy also holds a 1,176-combo canonical label naming an exact strategy row;
    that one is a different vocabulary answering a different question and travels under its own
    key, because one column that sometimes holds 169 values and sometimes 1,176 cannot be
    counted. Decision 16b, `runtime-reversible`.

    `StrategyQuery` validates exactly two distinct, legal hole cards at construction, so
    `hand_class` cannot raise on a query that reached a strategy at all.
    """
    return (
        ("table_size", str(len(query.stacks))),
        ("hand_class", hand_class(query.hole_cards)),
    )
