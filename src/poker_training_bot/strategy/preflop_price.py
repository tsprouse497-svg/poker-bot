"""Raise prices in big blinds: reading one off a chart key's units, and drawing among them.

Split out of `preflop_chart.py` rather than added to it, and the split is the price subject
whole: a raise-to in chips becomes a raise-to in big blinds here, and a hand class offered
more than one big-blind price picks one here too. The file it came out of is at the repo's
500-line cap, and compressing the reasoning in either place to make room would delete the
part of this that is hard - which of two prices the bot puts in front of a villain is a
strategy question, not a formatting one.

**Ruled by Taylor, 2026-08-26.** Decision 6's sizing table holds every price a spot offers a
hand class, with the weight hero gives each, so a class can arrive here with two: at 21 of the
86 committed spots hero has both a named raise and a shove, and the one committed opening
range is one of them. The strategy chooses between them with the same deterministic seeded
draw it already uses to collapse a mixed action cell, which is why `collapse` is handed in
below rather than reimplemented - a second weighted walk in this file would be a second
mechanism, and the ruling is that there is one.

Rejected, and each for a reason measured rather than argued:

- **Failing closed on a class with two prices.** `t6/d100/SB/rfi` is the only opening range
  the cutover commits and it offers two, so refusing here stops the bot opening a pot at all,
  from any seat.
- **Taking the highest-weight price.** That is the heuristic pick the `lookup-tie-picks-an-action`
  canary forbids for actions, it has no answer at a tie, and at the small blind's open it would
  commit the bot to a 100bb shove branch the solve plays about once in ninety-seven thousand.
- **Taking the smallest price.** Never shoves, which throws away the 15 jam-only spots and
  teaches a 7.5 three-bet where the solve stacks off nearly nine times in ten.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import Decimal

from poker_training_bot.solver_artifacts.schema import SIZE_QUANTUM

# The draw the caller already owns: action weights and a seed in, one action out. Typed as
# what is used rather than as `PreflopChartStrategy.collapse`, so this module does not import
# the strategy that imports it.
Collapse = Callable[[tuple[tuple[str, float], ...], str], str | None]


def size_bb(amount: int | None, big_blind: int) -> float | None:
    """A raise-to in chips as a raise-to in big blinds, or None if it is not exact.

    Exact arithmetic rather than float division, so the answer depends on the numbers and
    not on how a binary fraction happened to land. At the 50/100 blinds of every committed
    sample and every simulator profile it is always exact; a blind level that makes it
    inexact refuses, which is the fail-closed direction.
    """
    if amount is None or big_blind <= 0:
        return None
    value = Decimal(amount) / Decimal(big_blind)
    quantized = value.quantize(SIZE_QUANTUM)
    if quantized != value:
        return None
    return float(quantized)


def draw_price_bb(
    offered: Sequence[tuple[float, float]] | None,
    seed: str,
    collapse: Collapse,
) -> float | None:
    """One raise-to price in big blinds out of what a hand class is offered, or None.

    `offered` is `PreflopSizingTable.sizes_bb`'s answer: `(to_bb, weight)` pairs in ascending
    price order, or None where the table prices neither the spot nor the class. None and empty
    are the same answer here and both come back None, which upstream is the refusal naming a
    missing size - a spot the chart answers but nothing can price is still a spot the bot must
    not raise in.

    One price needs no draw and is returned whatever weight it carries, because the weight of
    a sole price is a statement about hero's aggressive volume rather than about which price
    to use. Two or more go to `collapse`, in the price order the table wrote them in, so the
    cumulative walk is as stable as the artifact's action order makes the action draw.

    The seed is tagged rather than passed through, and that is the one part of this worth
    arguing about. `collapse` returns the LAST entry for a high roll, so a price draw sharing
    the action draw's roll would only ever see the rolls that chose to raise in the first
    place - at a cell weighted half fold and half raise, every raise would take the top price,
    which is the highest-weight heuristic arriving by the back door. The tag decorrelates the
    two draws while keeping both a pure function of the same inputs, so a twin strategy built
    from the same library and sizing still draws the identical sequence.

    Prices go through `repr` on the way in and `float` on the way back, because `collapse`
    speaks in action labels. `repr` of a float round-trips exactly, so the price returned is
    the price the table holds and not a re-parsed approximation of it.
    """
    if not offered:
        return None
    if len(offered) == 1:
        return offered[0][0]
    labelled = tuple((repr(to_bb), weight) for to_bb, weight in offered)
    drawn = collapse(labelled, f"price|{seed}")
    return None if drawn is None else float(drawn)
