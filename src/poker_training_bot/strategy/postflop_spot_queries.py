"""Rebuild a playable table from a committed flop cell.

The strategy answers a `StrategyQuery`; the artifact stores a spot. Something has to turn one
into the other, and it is this module: given a committed cell it reconstructs the table that
cell describes - who posted, who folded, what is in the middle, what hero holds and what the
flop line put in - so the gate and the report can ask the strategy about a spot the repo
actually committed rather than about a spot a fixture invented.

The direction is what separates it from `postflop_betting`. That module walks from a table down
to a cell and **refuses** when it cannot, because a refusal is the answer a bot owes a spot it
was not given. This one walks the other way and **raises**, because a fixture that quietly
patches over a disagreement between the cell and the table it describes proves nothing.

Chips are the table's unit and big blinds are the cell's, so `BIG_BLIND_CHIPS` fixes the scale
and the cell's own `blind_structure` supplies every ratio under it.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

from poker_training_bot.poker_core.positions import preflop_action_order, seat_positions
from poker_training_bot.solver_artifacts.postflop_artifact import (
    INDEX_PATH,
    SAMPLE_DIR,
    PostflopCell,
    import_postflop_index,
    indexed_spot_keys,
)
from poker_training_bot.solver_artifacts.postflop_key import (
    canonical_board,
    menu_size_chips,
    postflop_spot_key,
)
from poker_training_bot.strategy.contract import SeatAction, SeatState, StrategyQuery
from poker_training_bot.strategy.postflop_committed import (
    BIG_BLIND_CHIPS,
    SIZED_ACTIONS,
    CommittedTable,
    committed_tables,
)

CLASSES_PER_ACTION = 3
"""How many hand classes are drawn per committed action when a cell is turned into queries.

The whole class list is thousands of combos and enumerating it would make the gate pay for a
table rebuild per combo. Taking the three classes that weigh an action highest keeps the set
small and keeps it *informative*: a cell that holds a raise is asked about by the hands most
likely to draw one, so `at_least_one_committed_spot_produces_a_raise` is not left to luck.
"""

MIXED_WEIGHT_FLOOR = 0.05
"""The weight at which an action counts towards a class being mixed rather than near-pure.
The same figure `tests/test_postflop_query_recording.py` uses to find a mixed cell."""

_TOLERANCE = 1e-9
_LIVE_SEATS = 2
_DECK_ORDER: tuple[str, ...] = tuple(rank + suit for rank in "AKQJT98765432" for suit in "cdhs")


def _chips(value_bb: float) -> int:
    return round(value_bb * BIG_BLIND_CHIPS)


def _seating(table: CommittedTable) -> tuple[tuple[int, ...], int, dict[str, int]]:
    """Seats, the button seat and the seat each position sits in.

    The button is seat 0 and the rest follows from `seat_positions`, which is the repo's one
    answer to where a label sits. Any button would do; a fixed one makes the fixture stable.
    """
    seats = tuple(range(table.table_size))
    labels = seat_positions(seats, 0)
    return seats, 0, {label: seat for seat, label in labels.items()}


def _flop_street(
    table: CommittedTable, seat_of: dict[str, int], pot_chips: int
) -> tuple[tuple[SeatAction, ...], dict[int, int], int, int]:
    """Replay the cell's flop line in chips: the history, each seat's street bet, the level
    standing in front of hero and the last raise increment.

    A committed size is a percent of the pot **at the moment it was put in**, so the pot is
    carried forward through the line rather than taken once at the start, and the chips come
    out of `menu_size_chips` - decision 14's rounding - rather than out of arithmetic invented
    here. A raise's percent is measured the same way, against what it added over its own
    standing bet, which is the convention `postflop_betting` matches a table's chips under.
    """
    street_bet: dict[int, int] = {}
    history: list[SeatAction] = []
    level = 0
    last_raise = 0
    for entry in table.cell.flop_actions:
        seat = seat_of[entry.position]
        standing = street_bet.get(seat, 0)
        if entry.action in SIZED_ACTIONS:
            added = menu_size_chips(float(entry.size_pct or 0.0) / 100.0, pot_chips)
            target = standing + added
            history.append(SeatAction(seat, entry.action, target))
            pot_chips += added
            last_raise = target - level
            level = target
            street_bet[seat] = target
        elif entry.action == "call":
            pot_chips += level - standing
            street_bet[seat] = level
            history.append(SeatAction(seat, "call"))
        else:
            history.append(SeatAction(seat, entry.action))
    return tuple(history), street_bet, level, last_raise


def _legal_actions(to_call: int, hero_stack: int, offered: tuple[str, ...]) -> tuple[str, ...]:
    """What the engine would put in front of hero here, widened to hold every committed action.

    Widened rather than replaced: an action the cell holds and this table cannot offer is a
    disagreement, and `_query_for` raises on it instead of dropping it, because a fixture that
    silently narrows the legal set is a fixture that never asks about half the cell.
    """
    if to_call == 0:
        available = ["check"] + (["bet"] if hero_stack > 0 else [])
    else:
        available = ["fold", "call"] + (["raise"] if hero_stack > to_call else [])
    return tuple(available + [name for name in offered if name not in available])


def _query_for(
    table: CommittedTable,
    board: tuple[str, ...],
    history: tuple[SeatAction, ...],
    street_bet: dict[int, int],
    level: int,
    last_raise: int,
    hole_cards: tuple[str, str],
    hand_id: str,
    offered: tuple[str, ...],
) -> StrategyQuery:
    """One contract-valid flop query for a rebuilt table, or a `ValueError` naming the gap."""
    cell = table.cell
    seats, button_seat, seat_of = _seating(table)
    line = cell.preflop_line
    contributions = dict(line.contributions)
    closing_level = line.closing_level_bb
    pot_bb = sum(contributions.values())
    if abs(pot_bb - cell.pot_bb) > _TOLERANCE:
        raise ValueError(f"{cell.spot_key}: rebuilt pot is {pot_bb}bb against {cell.pot_bb}bb")
    behind_bb = float(table.stack_depth_bb) - closing_level
    if abs(behind_bb - cell.effective_stack_bb) > _TOLERANCE:
        raise ValueError(f"{cell.spot_key}: rebuilt stack is {behind_bb}bb behind")
    live = set(line.live_positions)
    if len(live) != _LIVE_SEATS:
        raise ValueError(f"{cell.spot_key}: rebuilds {len(live)} live seats, not a two-seat flop")
    starting = _chips(float(table.stack_depth_bb))
    hero_seat = seat_of[cell.hero_position]
    states = []
    for label, seat in sorted(seat_of.items(), key=lambda pair: pair[1]):
        on_street = street_bet.get(seat, 0)
        states.append(
            SeatState(
                seat=seat,
                street_bet=on_street,
                committed_total=_chips(contributions[label]) + on_street,
                folded=label not in live,
            )
        )
    preflop = _preflop_history(table, seat_of)
    hero = states[hero_seat]
    if hero.street_bet != _chips(cell.hero_street_bet_bb):
        raise ValueError(f"{cell.spot_key}: rebuilt hero street bet is {hero.street_bet} chips")
    hero_stack = starting - hero.committed_total
    to_call = min(level - hero.street_bet, hero_stack)
    legal = _legal_actions(to_call, hero_stack, offered)
    missing = [name for name in offered if name not in legal]
    if missing:
        raise ValueError(f"{cell.spot_key}: committed actions {missing} are not legal here")
    return StrategyQuery(
        hand_id=hand_id,
        street="flop",
        seat=hero_seat,
        button_seat=button_seat,
        hole_cards=hole_cards,
        board=board,
        legal_actions=legal,
        to_call=to_call,
        current_bet=level,
        min_raise_target=level + max(last_raise, BIG_BLIND_CHIPS),
        pot=sum(state.committed_total for state in states),
        stacks=tuple((seat, starting - states[seat].committed_total) for seat in seats),
        seat_states=tuple(states),
        blinds=(_chips(table.blinds.small_blind_bb), _chips(table.blinds.big_blind_bb)),
        preflop_actions=preflop,
        postflop_actions=history,
    )


def _preflop_history(table: CommittedTable, seat_of: dict[str, int]) -> tuple[SeatAction, ...]:
    """The preflop street as the simulator would have recorded it, in chips.

    Every seat that took a preflop action is in it, folds included, because `simulator/run.py`
    appends every one of them and a fixture recorded from the raise onwards is not the line the
    producer emits. The order is the first orbit's, with each recorded entry taken at its own
    position and a fold standing in for every seat the line left out; anything the cell records
    beyond one orbit - a four-bet - follows in its own order.

    A **live** seat the line never names can only be the big blind checking its option in a
    limped pot, which the committed grammar has no entry for, so it is recorded as the check it
    was. Hero is no longer a special case: since decision 8's amendment the committed line is
    the completed street and hero's own closing action is in it like anybody else's.
    """
    entries = list(table.cell.preflop_line.actions)
    live = set(table.cell.preflop_line.live_positions)
    recorded: list[SeatAction] = []
    for label in preflop_action_order(table.table_size):
        if entries and entries[0].position == label:
            entry = entries.pop(0)
            recorded.append(
                SeatAction(seat_of[label], "raise", _chips(float(entry.size_bb or 0.0)))
                if entry.action == "raise"
                else SeatAction(seat_of[label], "call")
            )
        elif label not in live:
            recorded.append(SeatAction(seat_of[label], "fold"))
        elif all(entry.position != label for entry in table.cell.preflop_line.actions):
            recorded.append(SeatAction(seat_of[label], "check"))
    for entry in entries:
        recorded.append(
            SeatAction(seat_of[entry.position], "raise", _chips(float(entry.size_bb or 0.0)))
            if entry.action == "raise"
            else SeatAction(seat_of[entry.position], "call")
        )
    return tuple(recorded)


def _sample_classes(cell: PostflopCell) -> tuple[str, ...]:
    """Which hand classes a cell is asked about, chosen rather than taken at random.

    Three parts, in order and de-duplicated. The class that spreads its weight over the most
    actions comes first, so a mixed cell is reachable by the test that has to tell a weighted
    draw from an argmax. Then, for each committed action, the classes that weigh it highest, so
    every action the cell can produce has hands behind it that will actually draw it.
    """
    rows = list(zip(cell.hand_classes, cell.class_weights, strict=True))
    if not rows:
        return ()
    chosen: list[str] = [
        max(rows, key=lambda row: (sum(1 for w in row[1] if w >= MIXED_WEIGHT_FLOOR), row[0]))[0]
    ]
    for index in range(len(cell.actions)):
        ranked = sorted(rows, key=lambda row: (-row[1][index], row[0]))
        chosen.extend(name for name, _ in ranked[:CLASSES_PER_ACTION])
    return tuple(dict.fromkeys(chosen))


def committed_spot_queries(directory: Path | str = SAMPLE_DIR) -> tuple[StrategyQuery, ...]:
    """A flop query for every committed spot, one per sampled hand class.

    Empty when the artifact is not on this machine, which is the honest answer there: a clone
    that fetched nothing holds no committed spots to ask about.
    """
    built: list[StrategyQuery] = []
    for table in committed_tables(directory):
        cell = table.cell
        _, _, seat_of = _seating(table)
        history, street_bet, level, last_raise = _flop_street(
            table, seat_of, _chips(cell.pot_bb)
        )
        for hand in _sample_classes(cell):
            built.append(
                _query_for(
                    table, cell.board, history, street_bet, level, last_raise,
                    (hand[:2], hand[2:]), f"committed|{cell.spot_key}|{hand}",
                    # De-duplicated: decision 11's menu holds two entries called `bet` and
                    # `legal_actions` is a set of names, where a repeat would read as two.
                    tuple(dict.fromkeys(entry.name for entry in cell.actions)),
                )
            )
    return tuple(built)


def _unfetched_board(fetched: frozenset[tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    """Every canonical flop class this machine has not fetched, in deck order.

    Derived from the deck rather than tabulated, on `canonical_board`'s own cached
    minimisation, so this list and the key the lookup compares against cannot drift apart.
    """
    deck = _DECK_ORDER
    seen: list[tuple[str, ...]] = []
    known: set[tuple[str, ...]] = set(fetched)
    for cards in combinations(deck, 3):
        representative = canonical_board(cards)
        if representative not in known:
            known.add(representative)
            seen.append(representative)
    return tuple(seen)


def an_indexed_but_unfetched_query(index_path: Path | str = INDEX_PATH) -> StrategyQuery:
    """A query for a spot the committed index lists and this machine has not fetched.

    On a fresh clone that is the common case rather than the exotic one - the index names every
    class the campaign solved and the sample holds three of them - and it is a different miss
    from a spot nothing ever solved. Raises when the artifact is absent, because there is then
    no index to take a listed spot out of and inventing one would answer a question about this
    machine with a fixture.
    """
    tables = committed_tables()
    if not tables:
        raise LookupError("no committed sample is fetched here, so no spot is listed and unheld")
    listed = indexed_spot_keys(import_postflop_index(index_path))
    table = tables[0]
    cell = table.cell
    fetched = frozenset(item.cell.board for item in tables)
    for board in _unfetched_board(fetched):
        key = postflop_spot_key(
            cell.preflop_line, board, (), cell.pot_bb, cell.effective_stack_bb
        )
        if key not in listed:
            continue
        hole = tuple(card for card in _DECK_ORDER if card not in board)[:2]
        return _query_for(
            table, board, (), {}, 0, 0, (hole[0], hole[1]),
            f"indexed-unfetched|{key}", ("check",),
        )
    raise LookupError("the committed index lists no unfetched board on a covered line")


