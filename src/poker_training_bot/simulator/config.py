"""What a run is asked to do, and the shapes it refuses to be asked.

Its own module because `table` and `record` both need it while `run` owns the hand loop, so
putting it here is what keeps the imports a tree rather than a cycle.

The two rejections are judgment call 5, and they are refusals rather than adjustments on
purpose. The only committed chart artifact is six-handed at exactly 100 big blinds, so a
run at any other table size or depth would not be a worse measurement of the strategy - it
would be a measurement of the chart's refusal path. Better to say so at setup than to deal
six hundred hands of nothing.
"""

from __future__ import annotations

from dataclasses import dataclass

from poker_training_bot.profiles.seating import Profile

REQUIRED_SEATS = 6
REQUIRED_DEPTH_BB = 100


@dataclass(frozen=True)
class SimulationConfig:
    seed: int
    hands: int
    profiles: tuple[Profile, ...]
    starting_stack: int
    blinds: tuple[int, int]

    def __post_init__(self) -> None:
        if self.hands <= 0:
            raise ValueError("a simulation needs at least one hand")
        small_blind, big_blind = self.blinds
        if small_blind <= 0 or small_blind > big_blind:
            raise ValueError("blinds must be positive with the small blind no larger")
        if len(self.profiles) != REQUIRED_SEATS:
            raise ValueError(
                f"the committed preflop chart is {REQUIRED_SEATS}-handed only, got"
                f" {len(self.profiles)} profiles; another table size would measure the"
                " chart's refusal path rather than its ranges"
            )
        if self.starting_stack != REQUIRED_DEPTH_BB * big_blind:
            raise ValueError(
                f"the committed preflop chart holds {REQUIRED_DEPTH_BB}bb only, got"
                f" {self.starting_stack / big_blind:g}bb; another depth would measure the"
                " chart's refusal path rather than its ranges"
            )

    @property
    def seats(self) -> tuple[int, ...]:
        return tuple(range(len(self.profiles)))
