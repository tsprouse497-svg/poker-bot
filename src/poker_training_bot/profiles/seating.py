"""Named seats for a comparison, and no poker of any kind.

A profile is a strategy plus the label a report needs to talk about it. That is the whole
job, and keeping it that small is deliberate: the moment a profile could adjust what its
strategy does, a report comparing two profiles would be comparing two things nobody
wrote down, and the comparison would stop meaning anything. Two profiles differing only
in name play identically, and a test pins that.

Two seatings exist, because Phase 07's judgment call 2 says the comparison has two jobs.

`self-play` seats six copies of the Phase 06 composite. Six copies of one strategy have
zero expectation against each other by symmetry, so this measures no strategy quality at
all - which is exactly why it carries the mechanical criteria. Chip conservation, hand
termination, determinism, and the replay cross-check all have a known expected answer
here, and net chips across the table must come out at zero.

`floor` seats one composite against five copies of the Phase 03 reference check-fold
strategy. That strategy folds to any bet and checks whenever it can, so it is a floor
that is deliberately bad and already trusted. The number that falls out is closer to "how
often does the chart open" than to "how good are the chart's ranges", so it is reported as
a floor check: the chart-driven bot must beat a bot that folds everything, and if it does
not, something is broken. It is not a ranking against a real opponent, and nothing in this
repo can produce one of those until an opponent with a strategy exists.

The composite is built once and shared. It reads committed chart artifacts from disk, so
building six of them would do the same I/O six times to produce six equal objects; the
strategy is a frozen, field-equal dataclass holding no per-call state, so sharing one
instance across seats cannot let one seat's decision affect another's.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from poker_training_bot.strategy.composite import CompositeStrategy
from poker_training_bot.strategy.contract import StrategyProtocol
from poker_training_bot.strategy.reference import CheckFoldStrategy

SELF_PLAY = "self-play"
FLOOR = "floor"


@dataclass(frozen=True)
class Profile:
    """One named seat. The name is for reports; the strategy does all the work."""

    name: str
    strategy: StrategyProtocol


@cache
def _composite() -> CompositeStrategy:
    """One shared composite, because building it reads committed artifacts from disk."""
    return CompositeStrategy.from_repo()


def composite_profile(name: str = "composite") -> Profile:
    return Profile(name=name, strategy=_composite())


def reference_profile(name: str = "reference") -> Profile:
    return Profile(name=name, strategy=CheckFoldStrategy())


def seat_profiles(kind: str, seats: int) -> tuple[Profile, ...]:
    """The seating for one comparison.

    Every seat holding the same strategy carries the same name, deliberately. A report
    compares strategies rather than chairs, so five reference seats are one profile with
    five seats and their chips are summed, which is what `SimulationResult.profile_names`
    dedupes to and `chips_per_hand` sums over. Suffixing the names per seat would turn one
    profile into five, each measured over a sixth of the samples.

    A `seats` count the committed chart cannot answer is not rejected here.
    `SimulationConfig` rejects it, so that "this table is not one the chart covers" is
    reported once, by the thing that knows what a run needs, rather than by whichever
    helper happened to be called first.
    """
    if seats < 0:
        raise ValueError("a seating needs a non-negative number of seats")
    if kind == SELF_PLAY:
        return tuple(composite_profile(_COMPOSITE_LABEL) for _ in range(seats))
    if kind == FLOOR:
        return (composite_profile(_COMPOSITE_LABEL),) + tuple(
            reference_profile(_REFERENCE_LABEL) for _ in range(1, seats)
        )
    raise ValueError(f"unknown seating {kind!r}; expected {SELF_PLAY!r} or {FLOOR!r}")


# The labels match each strategy's own `strategy_id`, so a profile name in a report and a
# decision code prefix in an audit line refer to the same thing rather than to two
# vocabularies a reader has to reconcile.
_COMPOSITE_LABEL = CompositeStrategy.strategy_id
_REFERENCE_LABEL = CheckFoldStrategy.strategy_id
