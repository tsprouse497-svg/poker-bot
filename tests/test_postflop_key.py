"""Phase 16, stage 4: the postflop spot key, the query shape it needs, and the one collapse.

Authored before any implementation exists, from
`docs/phase_contracts/PHASE_16_POSTFLOP_BETTING.md` alone. Nothing here reads the postflop key
module, the artifact, or the strategy, because none of them is written; what it does instead is
state each criterion as an assertion a wrong implementation fails.

**The import shape is deliberate and is the thing not to tidy.** A module stage 6 has not written
is reached through a fixture whose `import ... as module` sits in the function body, never at module
scope. `from pkg.sub import missing` raises `ImportError` rather than `ModuleNotFoundError`, which
`red_for_the_right_reason` in `scripts/loop_stage.py` refuses, and either form at module scope turns
this file into one collection error - which runs no assertion in any file and freezes a suite that
has never executed. `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` is the entry; the repo has paid
for it twice.

**The board map is checked jointly, which is stronger than the contract's own wording.**
`reports/phase_audits/reviews/PHASE_16_POSTFLOP_BETTING/stage-03-contract-foldin.md` round 2 says
the flush-draw check the contract names is necessary and not sufficient: it catches an identity hand
map on a two-tone board and misses a different non-identity map that happens to preserve draw
status. So `TestTheOnePermittedCollapse` asserts the canonicaliser applies **one** permutation to
board and hand together, over all 22,100 boards, and keeps the flush-draw check beside it as the
poker statement of why that matters. `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`.
"""

from __future__ import annotations

import dataclasses
import itertools
from collections import Counter

import pytest

from poker_training_bot.data_pipeline import self_play_reference
from poker_training_bot.poker_core import positions as positions_module
from poker_training_bot.strategy import contract as contract_module

RANKS = "23456789TJQKA"
SUITS = "cdhs"
ALL_CARDS = tuple(rank + suit for rank in RANKS for suit in SUITS)

THREE_CARD_BOARDS = 22100
CANONICAL_FLOPS = 1755

# Orbit sizes over the four suits, brute-forced by the stage-3 review and recomputed by
# `test_the_class_sizes_are_the_three_orbit_sizes_and_nothing_else` rather than trusted:
# 286 x 24 + 1,170 x 12 + 299 x 4 = 22,100.
ORBIT_HISTOGRAM = {24: 286, 12: 1170, 4: 299}

# The committed chart declares exactly two raise prices, so the band is concrete at both.
SOLVED_OPEN_BB = 2.5
SOLVED_THREE_BET_BB = 7.5
CORPUS_MEDIAN_OPEN_BB = 2.25
CORPUS_MEDIAN_THREE_BET_BB = 9.25

A_COVERED_PREFLOP_KEY = "t6/d100/BB/BTN:raise@2.5"
"""A key the committed preflop chart actually holds, so the postflop key built on it names a
real line rather than one invented here. Read off
`data/artifacts/preflop/six_max_100bb_rakefree.json`."""


@pytest.fixture(scope="module")
def key_module():
    """`solver_artifacts.postflop_key`, the one producer of a postflop spot key.

    Imported inside the fixture, not at module scope. See the module docstring: a top-level import
    of a module stage 6 has not written makes this file one collection error and runs nothing.
    """
    import poker_training_bot.solver_artifacts.postflop_key as module

    return module


def owed(module, name: str):
    """A name stage 6 owes, fetched rather than reached, so the red says which one is missing.

    A bare attribute access raises `AttributeError: module has no attribute 'x'`, which says
    nothing about the obligation. This says what the contract requires and why.
    """
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 16's contract requires it and no"
        " implementation has been written yet"
    )
    return found


BUTTON_SEAT, SB_SEAT, HERO_SEAT = 0, 1, 2
STARTING_STACK = 10_000

COMMITTED = {BUTTON_SEAT: 250, SB_SEAT: 50, HERO_SEAT: 250}
"""The covered `@2.5` line six-handed: the button opens, the small blind folds and keeps its own
dead 50, and hero - the big blind at seat 2, which is where `blind_seats` puts it - calls."""

SEAT_STATES = tuple(
    contract_module.SeatState(
        seat=seat,
        street_bet=0,
        committed_total=COMMITTED.get(seat, 0),
        folded=seat not in (BUTTON_SEAT, HERO_SEAT),
    )
    for seat in range(6)
)
"""Every seat listed and the folded ones marked, each having sat down with exactly 10,000.
`tests/test_postflop_betting.py::seated` carries why dropping one is a defect and not a shorthand:
`len(stacks)` is read as the table size, and a dead blind lent to a live seat is read as depth."""

PREFLOP_LINE = (
    *(contract_module.SeatAction(seat, "fold") for seat in (3, 4, 5)),
    contract_module.SeatAction(BUTTON_SEAT, "raise", 250),
    contract_module.SeatAction(SB_SEAT, "fold"),
    contract_module.SeatAction(HERO_SEAT, "call"),
)
"""`simulator/run.py` appends every preflop action a seat takes, folds included."""


def flop_query(**overrides):
    """A contract-valid flop query in the covered `@2.5` line, six-handed and flat at 100bb."""
    fields = {
        "hand_id": "h1",
        "street": "flop",
        "seat": HERO_SEAT,
        "button_seat": BUTTON_SEAT,
        "hole_cards": ("As", "Kd"),
        "board": ("Kc", "7d", "2h"),
        "legal_actions": ("check", "bet"),
        "to_call": 0,
        "current_bet": 0,
        "min_raise_target": 100,
        "pot": sum(state.committed_total for state in SEAT_STATES),
        "stacks": tuple((s.seat, STARTING_STACK - s.committed_total) for s in SEAT_STATES),
        "seat_states": SEAT_STATES,
        "blinds": (50, 100),
        "preflop_actions": PREFLOP_LINE,
    }
    fields.update(overrides)
    return contract_module.StrategyQuery(**fields)


def audit(query, outcome, schema_version: int | None = None):
    return contract_module.DecisionAuditRecord(
        schema_version=(
            contract_module.DECISION_AUDIT_SCHEMA_VERSION
            if schema_version is None
            else schema_version
        ),
        strategy_id="phase-16-fixture",
        strategy_version=1,
        query=query,
        outcome=outcome,
    )


# --------------------------------------------------------------------------- #
# The query and the audit record have to be able to say what happened on a flop
# --------------------------------------------------------------------------- #


class TestTheQueryCanExpressAFlopSpot:
    """Criterion: `StrategyQuery` gains a postflop action history and `SeatAction` gains `bet`.

    Flop-only still needs within-street history, because a flop is not one decision: hero acts,
    villain answers, hero faces a bet or a raise.
    """

    def test_a_recorded_bet_is_accepted_and_carries_the_amount_it_bet(self) -> None:
        entry = contract_module.SeatAction(0, "bet", 300)

        assert entry.action == "bet"
        assert entry.amount == 300

    def test_a_recorded_bet_without_its_size_is_rejected(self) -> None:
        """A sizeless bet is the defect decision 9 names: two cells that face different prices
        merge into one, and the lookup silently answers a 75% bet from a 33% cell."""
        with pytest.raises(ValueError):
            contract_module.SeatAction(0, "bet")

    def test_a_recorded_check_still_carries_no_amount(self) -> None:
        with pytest.raises(ValueError):
            contract_module.SeatAction(0, "check", 300)

    def test_the_query_carries_a_postflop_history_beside_the_preflop_one(self) -> None:
        names = {field.name for field in dataclasses.fields(contract_module.StrategyQuery)}

        assert "postflop_actions" in names, (
            "a flop spot needs within-street history; `preflop_actions` alone cannot say"
            " whether hero has already bet and been raised"
        )
        assert "preflop_actions" in names, "the preflop history is unchanged by this phase"

    def test_the_postflop_history_defaults_to_empty_so_a_preflop_producer_is_unchanged(
        self,
    ) -> None:
        assert flop_query().postflop_actions == ()

    def test_the_payload_carries_the_two_histories_separately(self) -> None:
        query = flop_query(
            postflop_actions=(contract_module.SeatAction(0, "bet", 180),),
            preflop_actions=(contract_module.SeatAction(0, "raise", 250),),
        )

        payload = query.to_payload()

        assert payload["postflop_actions"] == [{"seat": 0, "action": "bet", "amount": 180}]
        assert payload["preflop_actions"] == [{"seat": 0, "action": "raise", "amount": 250}]

    def test_two_flop_lines_at_one_price_do_not_serialize_alike(self) -> None:
        """The whole point of carrying the history: a check-check flop and a bet-call flop can
        reach hero at the same price, and a cell answering both is answering the wrong one."""
        checked = flop_query()
        bet_into = flop_query(postflop_actions=(contract_module.SeatAction(0, "bet", 180),))

        assert checked.to_payload() != bet_into.to_payload()


class TestTheAuditSchemaVersionMovedWithThePayload:
    """Criterion: `DECISION_AUDIT_SCHEMA_VERSION` rises from 3, and a committed audit at the old
    version is rejected rather than read as the new one.

    `DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS` is what happens when it does not: two
    payload shapes under one number, indistinguishable in the bytes.
    """

    def test_the_version_rose_from_three(self) -> None:
        assert contract_module.DECISION_AUDIT_SCHEMA_VERSION == 4

    def test_the_audit_line_carries_the_moved_version(self) -> None:
        record = audit(flop_query(), contract_module.StrategyDecision("check", None, "x"))
        line = record.to_json_line()

        assert '"schema_version":4' in line

    def test_a_record_at_the_previous_version_is_refused(self) -> None:
        with pytest.raises(ValueError, match="schema_version"):
            audit(
                flop_query(),
                contract_module.StrategyDecision("check", None, "x"),
                schema_version=3,
            )

    def test_a_bet_with_an_amount_passes_the_legality_proof(self) -> None:
        """`DecisionAuditRecord` is the legality proof every amount this phase returns must
        satisfy, and until now no `StrategyDecision` the repo built carried one postflop."""
        record = audit(flop_query(), contract_module.StrategyDecision("bet", 180, "x"))

        assert record.outcome.amount == 180

    def test_a_bet_above_the_acting_seat_s_all_in_maximum_is_refused(self) -> None:
        with pytest.raises(ValueError, match="all-in maximum"):
            audit(flop_query(), contract_module.StrategyDecision("bet", 99999, "x"))


# --------------------------------------------------------------------------- #
# Postflop action order
# --------------------------------------------------------------------------- #


class TestPostflopActionOrder:
    """Criterion: `postflop_action_order` is added to `poker_core/positions.py`; the blinds act
    first once the flop is out, and postflop order is never derived from the seating order."""

    def test_the_blinds_act_first_six_handed(self) -> None:
        order = owed(positions_module, "postflop_action_order")

        assert order(6) == ("SB", "BB", "LJ", "HJ", "CO", "BTN")

    def test_heads_up_the_big_blind_acts_first_and_the_button_last(self) -> None:
        """Preflop the button posts the small blind and acts first; postflop that inverts. A
        function that returned the seating order would get exactly this case backwards."""
        order = owed(positions_module, "postflop_action_order")

        assert order(2) == ("BB", "BTN")

    def test_postflop_order_is_not_the_seating_order_at_any_table_size(self) -> None:
        order = owed(positions_module, "postflop_action_order")

        for size in range(2, 10):
            assert order(size) != positions_module.table_positions(size), size

    def test_postflop_order_seats_exactly_the_positions_that_are_at_the_table(self) -> None:
        order = owed(positions_module, "postflop_action_order")

        for size in range(2, 10):
            assert sorted(order(size)) == sorted(positions_module.table_positions(size)), size

    def test_the_preflop_order_this_phase_does_not_touch_is_unchanged(self) -> None:
        assert positions_module.preflop_action_order(6) == (
            "LJ",
            "HJ",
            "CO",
            "BTN",
            "SB",
            "BB",
        )


# --------------------------------------------------------------------------- #
# The one permitted collapse
# --------------------------------------------------------------------------- #


def apply_suit_map(cards, suit_map) -> tuple[str, ...]:
    return tuple(card[0] + suit_map[card[1]] for card in cards)


class TestTheOnePermittedCollapse:
    """Criterion: the board in the key is the canonical representative of its suit-isomorphism
    class, computed rather than tabulated.

    Every count below is recomputed here from the 52-card deck. A test that imported 1,755 from
    the module it is checking would agree with the module whatever the module said.
    """

    @pytest.fixture(scope="class")
    def canonical(self, key_module):
        return owed(key_module, "canonical_board")

    def test_all_twenty_two_thousand_boards_map_into_exactly_one_class_each(
        self, canonical
    ) -> None:
        boards = list(itertools.combinations(ALL_CARDS, 3))
        assert len(boards) == THREE_CARD_BOARDS

        classes = {canonical(board) for board in boards}

        assert len(classes) == CANONICAL_FLOPS

    def test_the_representative_is_a_member_of_its_own_class_and_is_stable(
        self, canonical
    ) -> None:
        """Idempotence. A map that returns a label rather than a board is not a representative,
        and a representative that re-canonicalises to something else is not canonical."""
        for board in itertools.combinations(ALL_CARDS, 3):
            representative = canonical(board)
            assert canonical(representative) == representative, board

    def test_the_class_sizes_are_the_three_orbit_sizes_and_nothing_else(self, canonical) -> None:
        """A canonicaliser that over-collapses - merging two genuinely different textures - shows
        up here as a class of the wrong size long before any strategy is wrong.

        **Orbit size is not a property of the texture**, which is what an earlier draft of this
        docstring said. It is 24 over the stabiliser: suits the board does not use permute freely,
        and so do suits holding identical ranks. Brute-forced over all 22,100 boards under all 24
        suit permutations, the six (texture, rank pattern) families are

            rainbow unpaired   286 classes x 24 =  6,864 boards
            rainbow paired     156 classes x 12 =  1,872 boards
            rainbow trips       13 classes x  4 =     52 boards
            two-tone unpaired  858 classes x 12 = 10,296 boards
            two-tone paired    156 classes x 12 =  1,872 boards
            monotone unpaired  286 classes x  4 =  1,144 boards

        so 169 of the 455 rainbow classes are not orbit-24, and 13 of the 299 orbit-4 classes are
        rainbow trips rather than monotone. `ORBIT_HISTOGRAM` was right; only the sentence that
        explained it was wrong, and it was about to be frozen as this repo's reference.

        The poker cost of believing the old sentence is the rainbow cost scaling the contract asks
        for: rainbow covers 8,788 boards over 455 classes, 19.314 a class, so scaling 455 classes
        at 24 boards each gives 10,920 and overstates rainbow by 24.3%.
        """
        sizes = Counter(canonical(board) for board in itertools.combinations(ALL_CARDS, 3))

        assert Counter(sizes.values()) == ORBIT_HISTOGRAM

    def test_the_module_s_declared_class_count_matches_the_deck(self, key_module) -> None:
        assert owed(key_module, "CANONICAL_FLOP_CLASSES") == CANONICAL_FLOPS

    def test_a_rank_texture_neighbour_maps_to_a_different_class(self, canonical) -> None:
        """Decision 2 defers rank abstraction rather than taking it, so `K72r` and `Q72r` are two
        boards and not one. `POSTFLOP-BOARD-ABSTRACTION` owns the deferral."""
        assert canonical(("Kc", "7d", "2h")) != canonical(("Qc", "7d", "2h"))
        assert canonical(("9c", "8c", "7c")) != canonical(("9c", "8c", "6c"))

    def test_the_same_board_in_two_suit_dresses_is_one_class(self, canonical) -> None:
        assert canonical(("Kc", "7d", "2h")) == canonical(("Kh", "7s", "2c"))
        assert canonical(("9c", "8c", "7c")) == canonical(("9s", "8s", "7s"))

    def test_a_two_tone_board_is_not_collapsed_onto_its_rainbow_twin(self, canonical) -> None:
        """The collapse is over suits, not over texture. Two-tone `K72` has a flush draw in it
        and rainbow `K72` does not, and no permutation of four suits turns one into the other."""
        assert canonical(("Kc", "7c", "2h")) != canonical(("Kc", "7d", "2h"))


class TestTheHandIsPermutedByTheBoardSOwnMap:
    """The half the contract's board tests cannot see, and the stage-3 review's note to stage 4.

    Suit isomorphism is exact only if hero's two cards are permuted by the **same** map as the
    board. A hand permuted inconsistently passes every board-level check - the classes are still
    distinct, every board still maps into exactly one, the rank-texture neighbour still maps
    elsewhere - and returns a real strategy for a real hand. No exploitability figure and no shape
    check can see it. `AN-ISOMORPHISM-TEST-ON-BOARDS-DOES-NOT-COVER-HERO-HANDS`.

    Asserting the joint permutation is strictly stronger than the flush-draw check and no more
    expensive, which is what the review asked stage 4 to do rather than stopping at the contract's
    wording. The flush-draw check stays below as the poker statement of why it matters.
    """

    @pytest.fixture(scope="class")
    def canonical(self, key_module):
        return owed(key_module, "canonical_board")

    @pytest.fixture(scope="class")
    def suit_map(self, key_module):
        return owed(key_module, "board_suit_map")

    @pytest.fixture(scope="class")
    def canonical_hand(self, key_module):
        return owed(key_module, "canonical_hole_cards")

    def test_the_published_map_is_a_permutation_of_the_four_suits(self, suit_map) -> None:
        for board in itertools.combinations(ALL_CARDS, 3):
            mapping = suit_map(board)
            assert sorted(mapping) == sorted(SUITS), board
            assert sorted(mapping.values()) == sorted(SUITS), board

    def test_the_published_map_is_what_carries_the_board_to_its_representative(
        self, canonical, suit_map
    ) -> None:
        """If the map and the representative disagree, there is no single permutation at all and
        the hand has nothing consistent to be permuted by."""
        for board in itertools.combinations(ALL_CARDS, 3):
            moved = apply_suit_map(board, suit_map(board))
            assert tuple(sorted(moved)) == tuple(sorted(canonical(board))), board

    def test_hero_s_cards_move_under_that_same_map_and_no_other(
        self, suit_map, canonical_hand
    ) -> None:
        """The joint property, over every board and a hero holding for each. One permutation is
        applied to board and hand together, or the collapse is not exact."""
        for board in itertools.combinations(ALL_CARDS, 3):
            spare = [card for card in ALL_CARDS if card not in board][:2]
            hole = (spare[0], spare[1])
            expected = tuple(sorted(apply_suit_map(hole, suit_map(board))))

            assert tuple(sorted(canonical_hand(board, hole))) == expected, (board, hole)

    def test_every_hero_combo_on_a_two_tone_board_moves_under_the_board_s_map(
        self, suit_map, canonical_hand
    ) -> None:
        """Exhaustive over all 1,176 hero combos on the modal texture, where the defect lives:
        two-tone is 55.06% of flops and whether hero shares the board's flush suit is most of the
        strategy there."""
        board = ("8h", "8d", "3h")
        mapping = suit_map(board)
        rest = [card for card in ALL_CARDS if card not in board]
        assert len(rest) == 49

        combos = list(itertools.combinations(rest, 2))
        assert len(combos) == 1176

        for hole in combos:
            expected = tuple(sorted(apply_suit_map(hole, mapping)))
            assert tuple(sorted(canonical_hand(board, hole))) == expected, hole

    def test_a_flush_draw_and_the_same_ranks_without_one_are_two_hero_classes(
        self, canonical_hand
    ) -> None:
        """The contract's own named gate test, kept beside the stronger one.

        On a two-tone board `AhQh` holds the flush draw and `AsQd` does not. If they canonicalise
        alike, one of them is about to be served the other's strategy - which is the failure the
        joint property above rules out in general and this states in poker.
        """
        board = ("8h", "8d", "3h")

        with_draw = canonical_hand(board, ("Ah", "Qh"))
        without_draw = canonical_hand(board, ("As", "Qd"))

        assert with_draw != without_draw

    def test_a_hand_sharing_only_one_board_suit_is_its_own_class_too(self, canonical_hand) -> None:
        """Three readings of `AQ` on a two-tone board and no two of them are one class: both
        hearts, one heart, neither."""
        board = ("8h", "8d", "3h")

        classes = {
            canonical_hand(board, ("Ah", "Qh")),
            canonical_hand(board, ("Ah", "Qs")),
            canonical_hand(board, ("Ac", "Qs")),
        }

        assert len(classes) == 3


# --------------------------------------------------------------------------- #
# What the key says
# --------------------------------------------------------------------------- #


def build_key(key_module, **overrides) -> str:
    """One call site for the producer, so a signature change is one edit rather than twenty."""
    producer = owed(key_module, "postflop_spot_key")
    fields = {
        "preflop_spot_key": A_COVERED_PREFLOP_KEY,
        "board": ("Kc", "7d", "2h"),
        "flop_actions": (),
        "pot_bb": 5.5,
        "effective_stack_bb": 97.5,
    }
    fields.update(overrides)
    return producer(**fields)


class TestWhatTheKeyCarries:
    """Criterion: the key carries the board, the preflop line verbatim with its sizes, the flop
    action so far with every bet size named, and the pot and effective stack."""

    def test_the_preflop_line_appears_verbatim_with_its_sizes(self, key_module) -> None:
        """Decision 8, ruled verbatim: a postflop spot names exactly the preflop spot whose ranges
        it was solved from, so no compression is invented."""
        assert A_COVERED_PREFLOP_KEY in build_key(key_module)

    def test_the_key_does_not_begin_with_t(self, key_module) -> None:
        """Criterion: no existing reader may mistake a postflop key for a preflop one, and
        `self_play_reference.py` claims any token starting with `t` that holds three slashes."""
        assert not build_key(key_module).startswith("t")

    def test_the_key_names_the_canonical_board_rather_than_the_board_asked_about(
        self, key_module
    ) -> None:
        dressed = build_key(key_module, board=("Kh", "7s", "2c"))
        assert build_key(key_module, board=("Kc", "7d", "2h")) == dressed

    def test_two_board_classes_are_two_keys(self, key_module) -> None:
        neighbour = build_key(key_module, board=("Qc", "7d", "2h"))
        assert build_key(key_module, board=("Kc", "7d", "2h")) != neighbour

    def test_two_preflop_lines_are_two_keys(self, key_module) -> None:
        elsewhere = build_key(key_module, preflop_spot_key="t6/d100/BB/CO:raise@2.5")
        assert build_key(key_module) != elsewhere

    def test_the_flop_bet_size_is_named_so_a_menu_change_fails_closed(self, key_module) -> None:
        """Decision 9. Against a 33% bet a caller needs 19.9% equity and against 75% he needs
        30.0%; a key that merged them would overfold to small bets and overcall large ones, and
        an opponent farms that by choosing his size."""
        action = owed(key_module, "FlopAction")
        small = build_key(key_module, flop_actions=(action("BTN", "bet", 33),))
        large = build_key(key_module, flop_actions=(action("BTN", "bet", 75),))

        assert small != large
        assert "33" in small
        assert "75" in large

    def test_a_checked_flop_and_a_bet_flop_are_two_keys(self, key_module) -> None:
        action = owed(key_module, "FlopAction")
        bet_into = build_key(key_module, flop_actions=(action("BTN", "bet", 33),))

        assert build_key(key_module) != bet_into

    def test_the_pot_is_in_the_key(self, key_module) -> None:
        assert build_key(key_module, pot_bb=5.5) != build_key(key_module, pot_bb=16.0)

    def test_the_effective_stack_is_in_the_key(self, key_module) -> None:
        """Decision 10, ruled against its own default. The geometric three-street size moves
        103.9%, 115.8% and 130.9% of pot at 77.5, 97.5 and 127.5bb effective, so a key that cannot
        say which depth it was solved at cannot refuse a spot it has no cell for."""
        shallower = build_key(key_module, effective_stack_bb=77.5)
        assert build_key(key_module, effective_stack_bb=97.5) != shallower

    def test_the_key_is_derived_and_the_module_publishes_no_parser(self, key_module) -> None:
        """Criterion: derived and compared, never parsed. Two derivations of "what spot is this"
        are two answers that can drift, and a parser is the second one."""
        parsers = sorted(
            name
            for name in dir(key_module)
            if not name.startswith("_")
            and ("parse" in name.lower() or name.lower().startswith("from_key"))
        )

        assert parsers == []

    def test_the_same_inputs_render_the_same_key_every_time(self, key_module) -> None:
        assert build_key(key_module) == build_key(key_module)


# --------------------------------------------------------------------------- #
# The price band
# --------------------------------------------------------------------------- #


class TestTheTwentyPercentPriceBand:
    """Criterion: the query refuses when the actual price is outside 20% of the price its cell was
    solved at, inclusive at both ends, and never substitutes a nearest value.

    The endpoints are pinned because the previous draft of this rule failed at a boundary nobody
    wrote down: the corpus's median 2.25bb open passed a "more than 0.5bb" pot test by exactly zero
    margin, so a stage-6 `>=` for a `>` would have flipped the commonest flop spot in the corpus to
    refused with nothing going red.
    """

    @pytest.fixture(scope="class")
    def within_band(self, key_module):
        return owed(key_module, "price_within_band")

    def test_the_band_is_a_fifth_of_the_cell_s_own_price(self, key_module) -> None:
        assert owed(key_module, "PRICE_BAND_FRACTION") == pytest.approx(0.20)

    def test_an_open_at_both_endpoints_is_accepted(self, within_band) -> None:
        assert within_band(SOLVED_OPEN_BB, 2.0) is True
        assert within_band(SOLVED_OPEN_BB, 3.0) is True

    def test_an_open_outside_either_endpoint_is_refused(self, within_band) -> None:
        assert within_band(SOLVED_OPEN_BB, 1.99) is False
        assert within_band(SOLVED_OPEN_BB, 3.01) is False

    def test_a_three_bet_at_both_endpoints_is_accepted(self, within_band) -> None:
        """The half the first draft of this ruling was silent about: a 3-bet pot cell carries the
        chart's second substituted price and the rule's antecedent did not describe it at all.
        Five of the seven converged rows are 3-bet pots."""
        assert within_band(SOLVED_THREE_BET_BB, 6.0) is True
        assert within_band(SOLVED_THREE_BET_BB, 9.0) is True

    def test_a_three_bet_outside_either_endpoint_is_refused(self, within_band) -> None:
        assert within_band(SOLVED_THREE_BET_BB, 5.99) is False
        assert within_band(SOLVED_THREE_BET_BB, 9.01) is False

    def test_the_band_scales_with_the_price_rather_than_being_a_chip_count(
        self, within_band
    ) -> None:
        """A fixed width that admits 2.0-3.0 against `@2.5` would admit only 7.0-8.0 against
        `@7.5`, and a 3-bet to 6.5 would fall through the rule the way it did in the first draft."""
        assert within_band(SOLVED_THREE_BET_BB, 6.5) is True
        assert within_band(SOLVED_OPEN_BB, 6.5) is False

    def test_the_corpus_median_open_is_inside_the_band(self, within_band) -> None:
        """99.0% of the corpus's 409 opens land in 2.0-3.0bb, which is what the band was chosen
        for. This pins the commonest real spot as answerable rather than refused."""
        assert within_band(SOLVED_OPEN_BB, CORPUS_MEDIAN_OPEN_BB) is True

    def test_the_corpus_median_three_bet_is_outside_it_and_the_phase_fails_closed(
        self, within_band
    ) -> None:
        """Ruled: keep the band and record the gap rather than widen it. The committed chart's
        single 3-bet price of 7.5bb sits below the corpus median of 9.25bb, so 47.1% of real 3-bet
        pots are servable and the rest refuse. `THE-COMMITTED-3BET-PRICE-IS-BELOW-THE-CORPUS-MEDIAN`
        owns that; this test is what stops a later session widening the band to make it go away."""
        assert within_band(SOLVED_THREE_BET_BB, CORPUS_MEDIAN_THREE_BET_BB) is False

    def test_a_price_outside_the_band_is_never_moved_to_the_nearest_one(self, key_module) -> None:
        """Deliberately the opposite of the preflop chart's nearest-price behaviour. Preflop
        0.25bb barely moves a range; postflop the same 0.25bb moves the pot, the SPR and both
        ranges at once."""
        within = owed(key_module, "price_within_band")

        assert within(SOLVED_OPEN_BB, 3.5) is False
        assert within(SOLVED_THREE_BET_BB, 3.5) is False


# --------------------------------------------------------------------------- #
# The reader nobody would think to look at
# --------------------------------------------------------------------------- #


class TestNoPreflopReaderClaimsAPostflopKey:
    """Criterion: a test asserts that `self_play_reference.py` returns no postflop key while still
    finding every preflop one and still raising on an empty inventory.

    The reader scrapes any token starting with `t` that holds at least three slashes and raises
    rather than returning empty, because an empty result is indistinguishable from a real answer.
    """

    def inventory(self, monkeypatch, tmp_path, text: str):
        path = tmp_path / "latest_refusal_inventory.txt"
        path.write_text(text, encoding="utf-8")
        monkeypatch.setattr(self_play_reference, "SELF_PLAY_INVENTORY", path)
        return path

    def test_a_postflop_key_in_the_inventory_is_not_returned_as_a_preflop_spot(
        self, monkeypatch, tmp_path, key_module
    ) -> None:
        postflop = build_key(key_module)
        self.inventory(monkeypatch, tmp_path, f"{A_COVERED_PREFLOP_KEY}: 12\n{postflop}: 4\n")

        found = self_play_reference.self_play_spots()

        assert postflop not in found

    def test_the_preflop_keys_beside_it_are_still_all_found(
        self, monkeypatch, tmp_path, key_module
    ) -> None:
        postflop = build_key(key_module)
        preflop = (A_COVERED_PREFLOP_KEY, "t6/d100/CO/rfi", "t6/d100/SB/BTN:raise@2.5")
        self.inventory(
            monkeypatch,
            tmp_path,
            "\n".join([*(f"{key}: 3" for key in preflop), f"{postflop}: 4"]) + "\n",
        )

        found = self_play_reference.self_play_spots()

        assert found == frozenset(preflop)

    def test_an_inventory_holding_only_postflop_keys_still_raises_rather_than_returning_empty(
        self, monkeypatch, tmp_path, key_module
    ) -> None:
        """The important half. A reader that quietly returned an empty set would mark every
        real-hand spot NEW, inverting the phase's most actionable claim under a passing gate."""
        self.inventory(monkeypatch, tmp_path, f"{build_key(key_module)}: 4\n")

        with pytest.raises(ValueError):
            self_play_reference.self_play_spots()
