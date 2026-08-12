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

from poker_training_bot.hand_history.schema import HistoryStreet, NormalizedHandHistory
from poker_training_bot.simulator.outcomes import REFUSED
from poker_training_bot.strategy.contract import DecisionAuditRecord


@dataclass(frozen=True)
class RefusedSpot:
    """One spot the charts could not answer, and how much of it this run reached.

    `hands` is what orders the work list. `hand_classes` says which holdings actually turned
    up there, which is how a reader can tell a spot that came up once with one hand from a
    spot that came up sixty times across forty hands - the second is a real hole and the
    first might be noise.
    """

    detail: tuple[tuple[str, str], ...]
    code: str
    hands: int
    hand_classes: tuple[tuple[str, int], ...]

    @property
    def spot_key(self) -> str:
        return dict(self.detail).get("spot_key", "(no expressible spot)")


@dataclass(frozen=True)
class HandResult:
    """One dealt hand, its books, and the record that lets anyone re-derive it.

    `streets` is always the transcript as far as the hand actually got, including the
    partial street a refusal stopped in the middle of. `normalized` is a completed Phase 02
    hand history and exists only when the hand reached a settlement - a refused hand stops
    inside a betting round, so there is no completed hand for the replayer to re-derive and
    presenting one would be a category error rather than a convenience.

    The first version of this phase collapsed the two, which is how the actions identifying
    a refused spot were lost: the record was built from whole streets, and a refusal never
    completes one.

    `refusal_detail` carries what the strategy could not find, straight off the
    `StrategyRefusal`, which is what makes an inventory of refusals keyable to a chart cell.
    """

    hand_id: str
    seed: int
    button_seat: int
    outcome: str
    refusal_code: str | None
    refusing_seat: int | None
    refusal_detail: tuple[tuple[str, str], ...]
    starting_stacks: dict[int, int]
    stack_deltas: dict[int, int]
    pot_collected: int
    pot_awarded: int
    decisions: tuple[DecisionAuditRecord, ...]
    streets: tuple[HistoryStreet, ...]
    normalized: NormalizedHandHistory | None


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

    def settled_hands(self) -> tuple[HandResult, ...]:
        """The hands that reached a settlement, and therefore carry a replayable record."""
        return tuple(hand for hand in self.hands if hand.normalized is not None)

    def refusal_inventory(self) -> tuple[RefusedSpot, ...]:
        """Every distinct spot a strategy could not answer, most-reached first.

        Keyed by the spot rather than by the spot-and-hand pair, because a spot is the unit
        of chart work: committing `t6/d100/BB/BTN:raise,SB:raise` covers every hand class in
        it at once, and a list fragmented by hand class buries a spot reached sixty times
        under sixty rows of one. The hand classes are kept as counts underneath, since they
        say how much of the spot this run actually exercised.

        The key comes off the refusal's own detail with the hand class lifted out, so an
        entry still names the cell the lookup asked about rather than anything re-derived
        here. Ordered by hands reached, ties breaking on the code and then on the key, so
        the file is byte-stable between runs and its diff is a record of coverage improving.
        """
        hands: Counter = Counter()
        classes: dict[tuple[tuple[tuple[str, str], ...], str], Counter] = {}
        for hand in self.hands:
            if hand.refusal_code is None:
                continue
            named = dict(hand.refusal_detail)
            hand_class = named.pop("hand_class", None)
            key = (tuple(sorted(named.items())), hand.refusal_code)
            hands[key] += 1
            if hand_class is not None:
                classes.setdefault(key, Counter())[hand_class] += 1
        return tuple(
            RefusedSpot(
                detail=key[0],
                code=key[1],
                hands=count,
                hand_classes=tuple(sorted(classes.get(key, Counter()).items())),
            )
            for key, count in sorted(
                hands.items(), key=lambda item: (-item[1], item[0][1], item[0][0])
            )
        )

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
