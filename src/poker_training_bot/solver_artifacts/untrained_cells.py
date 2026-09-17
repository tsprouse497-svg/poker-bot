"""Whether a published cell is strategy the solve trained, or the row it never touched.

**Its own module because it is its own subject.** "This row was never trained" is a claim with a
measured argument behind it - three candidate detectors were tried and two rejected on numbers -
and that argument belongs beside the thing it justifies rather than as a long aside inside a
module about how a lookup answers or one about how an export is written. MAINT-34's decision 5
ruled that such a cell refuses rather than being dropped or answered; this is what decides which
cells those are, and `lookup.py` owns the refusal code and the refusal itself.

`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`.
"""

from __future__ import annotations

from poker_training_bot.solver_artifacts.gtopen_export import (
    QUANTISATION_SCALE,
    _quantise_row,
)
from poker_training_bot.solver_artifacts.schema import ActionWeights


def quantised_uniform_row(width: int) -> tuple[float, ...]:
    """The strategy row regret matching starts from, at this export's quantisation.

    A cell the solve never visits keeps its initialisation, and that initialisation is uniform.
    Quantising it is deterministic and is **not** a row of equal numbers: at width three the
    largest-remainder step above produces `3333, 3333, 3334`, so a check written as "all the
    weights are equal" misses it, and one written as "within a tolerance of 1/n" needs a
    threshold nobody has ruled. Reproducing the row through `_quantise_row` gives an exact value
    to compare against instead, and it cannot drift from the exporter because it *is* the
    exporter. MAINT-34's decision 5, and `UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`.

    Measured on the committed 13.5bb chart: all 167 untrained cells publish exactly this row and
    no trained cell does, the nearest trained row sitting 70 basis points away on its largest leg.
    Every count in this module is that chart's and moves whenever the committed set does, with no
    line of this code changing: decision 7 took them from 187 cells across 17 spots to 167 at one.
    """
    if width < 1:
        raise ValueError(f"a strategy row needs at least one action, got {width}")
    return tuple(value / QUANTISATION_SCALE for value in _quantise_row([1.0 / width] * width))


def is_untrained_cell(action_weights: ActionWeights, arrival_ppb: int | None) -> bool:
    """Whether a published cell is the solver's untouched initialisation rather than strategy.

    **The condition is "this row was never trained"; uniformity is only its symptom, and neither
    half identifies it alone.** Three readings were measured on the committed 13.5bb chart:

    - *arriving reach* does not separate at all. Untrained cells arrive at 3 to 62 basis points
      while 615 trained cells arrive at a single basis point, so any reach floor cuts trained
      cells first and keeps every untrained one. Rejected on measurement.
    - *spot arrival alone* is necessary and nowhere near sufficient. The one spot carrying an
      untrained cell arrives at exactly zero - but so do 53 of the 156, and that spot still has
      2 trained cells among its 169. Refusing on arrival would refuse 52 spots of trained cells
      and those 2, which is what the 2026-08-27 ruling exists to prevent: arrival is
      measured under the solve's own play, a human takes lines the solver never does, and a
      *trained* cell at a never-played spot is worth having.
    - *the row alone* is exact on this chart and unsafe in general. Regret matching starts uniform
      and a row it never updates stays there, so an untrained cell publishes precisely
      `quantised_uniform_row(width)` - `0.3333, 0.3333, 0.3334` at width three, never three equal
      numbers. That catches all 167 and nothing else here, the nearest trained row sitting 70
      basis points away on its largest leg. But at **width two the uniform row is `0.5, 0.5`**,
      which is ordinary poker rather than a signature - that nearest row is a width-two
      `0.493, 0.507` - and a sibling fixture in `test_preflop_lookup.py` is exactly that. Shape
      alone would refuse a genuine coin-flip mix.

    So both: the line is one the solve never plays **and** the row is the initialisation it would
    have kept if so. Neither over-refuses the other's cases, and together they select exactly the
    167 cells that MAINT-34's decision 5 rules must refuse: 167 of the 169 published at
    `t6/d100/SB/LJ:raise@2.5,HJ:call,CO:call,BTN:call,SB:call,BB:raise@13.5` and none anywhere
    else, decision 7 having stopped committing the other sixteen spots that carried them. A
    trained row cannot be caught, and it is the SHAPE half that guarantees it rather than the
    arrival half. `arrival_ppb` is rounded, so a spot the solve genuinely reaches can still
    store 0: 53 committed spots store it and only 47 are at exactly zero, leaving 6 that are
    played and indistinguishable here from never-played (`test_chart_arrival_probability.py`
    pins both counts). All 6 publish a three-action menu, which the exact-shape test below
    cannot mistake for the uniform initialisation - the dangerous case would be a width-two
    menu, as the next paragraph explains.

    The shape half is an exact equality against a value the exporter computes, not a threshold -
    a tolerance would also swallow the 4 cells that sit within 200 basis points of uniform while
    being trained. It is compared as a sorted multiset because which leg carries the extra basis
    point is an artefact of action order rather than of the strategy.

    `arrival_ppb` is None when the artifact publishes no arrival map, which is "not known here"
    rather than "zero"; an unknown never refuses.
    """
    if arrival_ppb != 0 or len(action_weights) < 2:
        return False
    published = sorted(weight for _, weight in action_weights)
    return published == sorted(quantised_uniform_row(len(action_weights)))
