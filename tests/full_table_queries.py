"""The six-handed table these tests ask their questions at, and the queries they ask.

**A support module, not a test module, and the split is a line cap and nothing more.**
`test_full_table_preflop.py` owns every assertion; this is the table mechanics those assertions
are posed on - who sits where, what each seat has paid, and what a `StrategyQuery` looks like
part-way through an orbit. None of it touches the chart. MAINT-34 forced the split: pricing by
hero's seat as well as by what he faces did not fit under the 700-line cap in a file whose own
docstring already said it was hard against it, and the ruling was to split rather than compress.

The blind and depth constants are duplicated from the owner deliberately: this module is what
defines the table, and importing them back from a test module would make the direction of
definition circular.
"""

from __future__ import annotations

from poker_training_bot.poker_core.positions import position_for_seat
from poker_training_bot.strategy.contract import SeatAction, SeatState, StrategyQuery

BIG_BLIND = 100
SMALL_BLIND = 50
DEPTH_BB = 100
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3  # seats 0..5 with button at 3 puts LJ at seat 0


def seat_of(position: str) -> int:
    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise AssertionError(f"no seat holds {position}")


def stacks(committed: dict[int, int] | None = None, ante: int = 0,
           depth_bb: int = DEPTH_BB) -> tuple[tuple[int, int], ...]:
    paid = dict(committed or {})
    paid.setdefault(seat_of("SB"), SMALL_BLIND)
    paid.setdefault(seat_of("BB"), BIG_BLIND)
    full = depth_bb * BIG_BLIND
    return tuple((seat, full - paid.get(seat, 0) - ante) for seat in SEATS)


def query(hero_position: str, history: tuple[SeatAction, ...] = (),
          hole_cards: tuple[str, str] = ("As", "Ks"), forced: dict[int, int] | None = None,
          ante: int = 0, **overrides) -> StrategyQuery:
    """A query for hero, unopened by default. `forced` is a straddle's chips, `ante` dead money."""
    hero = seat_of(hero_position)
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND, **(forced or {})}
    # A straddle raises the level a voluntary action is measured against, so the ladder starts
    # there. The detector knows only the declared blinds, which is the disagreement.
    current_bet = max(BIG_BLIND, *committed.values())
    min_raise_target = 2 * current_bet
    for entry in history:
        if entry.action == "raise":
            # The level is what the raise says it is: the query's price and the key's are one.
            amount = entry.amount or current_bet
            min_raise_target = amount + max(amount - current_bet, BIG_BLIND)
            current_bet = amount
            committed[entry.seat] = current_bet
        elif entry.action == "call":
            committed[entry.seat] = current_bet
    # Capped at what hero can actually pay, per Taylor's ruling of 2026-08-20.
    hero_stack = DEPTH_BB * BIG_BLIND - committed.get(hero, 0) - ante
    to_call = min(max(current_bet - committed.get(hero, 0), 0), hero_stack)
    gone = tuple(entry.seat for entry in history if entry.action == "fold")
    fields = {
        "hand_id": "h1", "street": "preflop", "seat": hero, "button_seat": BUTTON,
        "hole_cards": hole_cards, "board": (), "to_call": to_call, "current_bet": current_bet,
        "min_raise_target": min_raise_target, "blinds": (SMALL_BLIND, BIG_BLIND),
        "legal_actions": ("fold", "call", "raise") if to_call else ("check", "raise"),
        "pot": sum(committed.values()) + len(SEATS) * ante, "preflop_actions": history,
        "stacks": stacks(committed, ante),
        # An ante buys no part of the level, so it sits in `committed_total` alone.
        "seat_states": tuple(SeatState(s, committed.get(s, 0), committed.get(s, 0) + ante,
                                       s in gone, False) for s in SEATS),
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def cards_for(hand: str) -> tuple[str, str] | None:
    ranks = "23456789TJQKA"
    if len(hand) == 2 and hand[0] == hand[1] and hand[0] in ranks:
        return (hand[0] + "s", hand[1] + "h")
    if len(hand) != 3 or hand[2] not in "so":
        return None
    high, low = hand[0], hand[1]
    if high not in ranks or low not in ranks or ranks.index(high) <= ranks.index(low):
        return None
    return (high + "s", low + ("s" if hand[2] == "s" else "h"))


def combos_of(hand: str) -> int:
    if len(hand) == 2:
        return 6
    return 4 if hand.endswith("s") else 12


def raised(position: str, amount: int) -> SeatAction:
    return SeatAction(seat_of(position), "raise", amount)


def folded(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


def called(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "call")
