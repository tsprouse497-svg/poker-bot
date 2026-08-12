"""What a run produced, and what it is allowed to conclude from it.

`HandResult` and `SimulationResult` are deliberately plain data: no `SimulationConfig`, no
strategy objects, nothing whose equality depends on how a chart library compares. Two runs
of the same seed, seating and profiles being equal is this phase's central property, and it
is only well defined over values, so the seating survives here as names.

The statistics live beside the data rather than in the report generator because two of them
are judgments rather than arithmetic. `standard_error` decides what "the run's own
variation" means, and `separated_profiles` decides when a difference is allowed to be called
a finding. Those belong where a test can pin them, not inside a report where they would read
as formatting.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from poker_training_bot.hand_history.schema import NormalizedHandHistory
from poker_training_bot.simulator.outcomes import REFUSED
from poker_training_bot.strategy.contract import DecisionAuditRecord


@dataclass(frozen=True)
class HandResult:
    """One dealt hand, its books, and the record that lets anyone re-derive it."""

    hand_id: str
    seed: int
    button_seat: int
    outcome: str
    refusal_code: str | None
    refusing_seat: int | None
    starting_stacks: dict[int, int]
    stack_deltas: dict[int, int]
    pot_collected: int
    pot_awarded: int
    decisions: tuple[DecisionAuditRecord, ...]
    normalized: NormalizedHandHistory


@dataclass(frozen=True)
class SimulationResult:
    seed: int
    seat_names: tuple[str, ...]
    hands: tuple[HandResult, ...]
    position_counts: dict[int, Counter]

    def profile_names(self) -> tuple[str, ...]:
        """One entry per strategy, not per chair.

        Several seats holding the same strategy are one profile, because a comparison is
        between strategies. Their chips are summed rather than averaged separately, which
        would measure each over a fraction of the samples.
        """
        return tuple(dict.fromkeys(self.seat_names))

    def hands_dealt(self) -> int:
        return len(self.hands)

    def hands_counted(self) -> int:
        """Hands that moved chips. A refused hand is voided, so it is not in here."""
        return sum(1 for hand in self.hands if hand.outcome != REFUSED)

    def seats_for(self, name: str) -> tuple[int, ...]:
        return tuple(seat for seat, seated in enumerate(self.seat_names) if seated == name)

    def _per_hand_chips(self, name: str) -> tuple[int, ...]:
        seats = self.seats_for(name)
        return tuple(
            sum(hand.stack_deltas[seat] for seat in seats)
            for hand in self.hands
            if hand.outcome != REFUSED
        )

    def chips_per_hand(self, name: str) -> float:
        samples = self._per_hand_chips(name)
        if not samples:
            return 0.0
        return sum(samples) / len(samples)

    def chips_per_hand_by_profile(self) -> dict[str, float]:
        return {name: self.chips_per_hand(name) for name in self.profile_names()}

    def standard_error(self, name: str) -> float:
        """The run's own variation in the figure above, so a reader can judge it.

        Population standard deviation over the per-hand samples, divided by the root of the
        sample count. One sample has no separable variation, so this reports zero rather
        than inventing a number.
        """
        samples = self._per_hand_chips(name)
        if len(samples) < 2:
            return 0.0
        mean = sum(samples) / len(samples)
        variance = sum((sample - mean) ** 2 for sample in samples) / len(samples)
        return (variance / len(samples)) ** 0.5

    def separated_profiles(self) -> tuple[str, ...]:
        """Profiles whose figure clears its own noise, best first.

        Judgment call 3: a chip difference smaller than the run's own variation is not a
        finding. Two standard errors is the bar, and identical profiles never clear it,
        which is what makes a self-play run report no winner.
        """
        cleared = [
            name
            for name in self.profile_names()
            if abs(self.chips_per_hand(name)) > 2 * self.standard_error(name)
        ]
        return tuple(sorted(cleared, key=self.chips_per_hand, reverse=True))

    def refusal_counts(self) -> dict[str, int]:
        counts = {name: 0 for name in self.profile_names()}
        for hand in self.hands:
            if hand.refusing_seat is None:
                continue
            counts[self.seat_names[hand.refusing_seat]] += 1
        return counts

    def refusal_codes(self) -> Counter:
        return Counter(hand.refusal_code for hand in self.hands if hand.refusal_code)
