"""What the two declared blinds and the recorded actions predict about a preflop pot.

Pure prediction: seats, a button, the declared blinds and the recorded history in, numbers
out. Nothing here refuses anything, names a refusal code, or knows what a chart is. The
comparison against what the seats actually hold lives in the strategy that has to answer
for it, and the prediction lives here so a report can reconcile its own census against the
same arithmetic the detector used rather than against a second copy of it.

Two predictions, and neither follows from the other. Contributions catch money a seat never
chose to put in, which is every ante and every straddle whose poster has not yet acted, on
a folded seat as readily as on a live one. The minimum raise target catches the straddle
those cannot see at all: a straddler who has already called to the level holds exactly what
an ordinary caller holds, and the only trace the straddle leaves is that the first raise was
measured from it rather than from the big blind.

**The residual all three signals still miss, stated because a detection without one reads as
a proof.** The prediction below is the final level plus the last increment, and a straddle
perturbs only the FIRST increment, so past one recorded raise the prediction is a difference
of two recorded raise-to amounts and comes out identical whether the pot is straddled or
not. So the minimum-raise signal fires only on a single-raise pot. Neither of the others
covers what it then misses: a raiser's predicted contribution is its own raise-to amount,
which absorbs any forced money that seat posted earlier, and an unraised level cannot be
read once the straddler has acted. A straddled pot with two or more recorded raises is
therefore invisible to all three - and it is not merely refused under the wrong code. It
reaches the chart, hits a cell, and is answered with the UNSTRADDLED range for that spot,
which is the one place this phase's claim that an undescribable table is refused rather than
answered does not hold. Filed as `STRADDLE-INVISIBLE-AFTER-A-SECOND-RAISE`: recovering the
trace needs a declared blind structure on the query, which is the format change this phase
is scoped out of, and any guard written without one over-refuses ordinary tables.

A straddle equal to the big blind is invisible for a second and simpler reason. It moves no
level, predicts what a limp predicts, and shifts no minimum, so an unraised pot holding one
reads exactly as the limped pot it cannot be told from.

That is one instance of a wider shape, written out here because the report states it and the
code a reader arrives at should too: **once the straddler has acted and nothing has raised,
the level is the only signal still standing.** The straddler's own recorded call explains the
chips it posted, so contributions are blind; with no recorded raise there is no increment for
a minimum to disagree about, so the minimum-raise signal has nothing to compare. The level
then carries the whole detection by itself, which is why a big-blind-sized straddle escapes
there and a larger one does not. No legal preflop street reaches that position - the straddler
acts last and its call ends the round, so there is no decision left to ask about - but a query
can be written holding it, and this module answers the query it is handed rather than the
street it wishes it had.
"""

from __future__ import annotations

from collections.abc import Sequence

from poker_training_bot.poker_core.order import blind_seats
from poker_training_bot.strategy.contract import SeatAction

_PAYING_ACTIONS = frozenset({"call", "raise"})


def predicted_contributions(
    seats: Sequence[int],
    button_seat: int,
    blinds: tuple[int, int],
    actions: Sequence[SeatAction],
) -> dict[int, int]:
    """What each seat should hold if the only forced money is the two declared blinds.

    A recorded raise pays the amount it raised to, a recorded call pays the level standing
    in front of it, and a fold or a check pays nothing beyond whatever blind that seat
    posted. A seat holding more than this is carrying chips it never chose to put in.

    Folded seats are predicted too. Their chips stay in the pot whatever they did, so a
    reconstruction over the seats still playing would read a dead blind as an ordinary pot
    and answer it.

    The blind seats come from `poker_core.order.blind_seats` rather than from the position
    labels, because heads-up the button posts the small blind and its label is `BTN`: asking
    for the seat labelled `SB` would find nobody and read the button's blind as forced money.
    """
    small_blind, big_blind = blinds
    small_seat, big_seat = blind_seats(seats, button_seat)
    predicted = {seat: 0 for seat in seats}
    predicted[small_seat] = small_blind
    predicted[big_seat] = big_blind
    level = big_blind
    for entry in actions:
        if entry.action == "raise" and entry.amount is not None:
            level = entry.amount
        if entry.action in _PAYING_ACTIONS:
            predicted[entry.seat] = max(predicted.get(entry.seat, 0), level)
    return predicted


def unexplained_contributions(
    seats: Sequence[int],
    button_seat: int,
    blinds: tuple[int, int],
    actions: Sequence[SeatAction],
    held: dict[int, int],
) -> dict[int, int]:
    """Chips each seat holds beyond what the blinds and its own actions predict, if any.

    `held` is what each seat has actually put in over the hand. Only the positive direction
    is forced money, so a seat below its prediction drops out rather than reading as a
    negative: it has called all-in for less than the level, which is short money.
    """
    predicted = predicted_contributions(seats, button_seat, blinds, actions)
    return {
        seat: chips - predicted[seat]
        for seat, chips in held.items()
        if chips > predicted[seat]
    }


def predicted_min_raise_target(big_blind: int, actions: Sequence[SeatAction]) -> int | None:
    """The raise-to the declared blinds and the recorded raises say a re-raise starts at.

    `poker_core.engine`'s own walk, mirrored: the minimum raise starts at the big blind, and
    a recorded raise moves it only when its increment - its raise-to less the level standing
    before it - is at least the minimum already standing, which is exactly what
    `BettingRoundState.apply` does to `min_raise`. The prediction is the final level plus
    that minimum, which is what every producer in this repo passes as `min_raise_target`.
    The walk starts from the big blind, the only level the artifact format can declare, so
    over a 200 straddle a raise to 600 predicts 1,100 where the table itself offers 1,000.
    The gap is the straddle less the big blind, not the straddle: the opener's increment was
    measured from the 200 in front of it rather than from the declared 100.

    None when nothing has raised. An unraised pot's minimum comes from the blind alone and
    carries no increment to disagree about, and the level itself is the signal there.

    The floor is what keeps a short all-in out of the straddle signal, and it costs nothing.
    A history records a shove for less than a full raise as an ordinary raise: at 50/100 with
    an open to 250, a 300-chip stack all-in to 300 has an increment of 50, and an unfloored
    walk predicted 350 where the engine holds the minimum at 150 and offers 450 - so the
    strategy announced a straddle in a pot where a short stack simply shoved, which is a
    false statement about the game. The floor cannot hide a straddle in exchange, because a
    straddle perturbs only the first increment and that increment is a full raise measured
    from a level *above* the declared big blind, so it is never below the floor the walk
    starts at. Every straddle the unfloored rule caught, this one catches.
    """
    level = minimum = big_blind
    raised = False
    for entry in actions:
        if entry.action != "raise" or entry.amount is None:
            continue
        raised = True
        increment = entry.amount - level
        if increment >= minimum:
            minimum = increment
        level = entry.amount
    if not raised:
        return None
    return level + minimum
