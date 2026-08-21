"""Phase 05 tests, written from the contract before any implementation existed.

Two things here are not ordinary unit tests and are worth naming.

`TestSourceFrequencies` is the phase's external oracle. Every other assertion in
this repo compares something this repo produced against something else this repo
produced. Those numbers came from GTO Wizard's own displayed output, so this class
is the only place a wrong range can be caught rather than merely reproduced.

`TestTotality` proves coverage by enumeration rather than by sampling. An
artifact-backed strategy is allowed to refuse, and the danger is not a wrong answer
but a confident one where the chart says nothing, so the interesting property is
that every reachable spot resolves to a decision or an explicit refusal and never to
an exception or a guess.
"""

from __future__ import annotations

import itertools
import json
import subprocess
from collections import Counter

import pytest

from poker_training_bot.poker_core.positions import position_for_seat, table_positions
from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
ARTIFACT = ARTIFACT_DIR / "six_max_nl25_100bb.json"
SOURCE = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"
EXPECTATIONS = ARTIFACT_DIR / "expectations" / "six_max_nl25_100bb.json"
SIZINGS = ARTIFACT_DIR / "sizings" / "six_max_nl25_100bb.json"

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


def stacks(committed: dict[int, int] | None = None) -> tuple[tuple[int, int], ...]:
    """Current stacks for a six-handed 100bb table, minus what each seat put in."""
    paid = dict(committed or {})
    paid.setdefault(seat_of("SB"), SMALL_BLIND)
    paid.setdefault(seat_of("BB"), BIG_BLIND)
    full = DEPTH_BB * BIG_BLIND
    return tuple((seat, full - paid.get(seat, 0)) for seat in SEATS)


def query(
    hero_position: str,
    history: tuple[SeatAction, ...] = (),
    hole_cards: tuple[str, str] = ("As", "Ks"),
    **overrides,
) -> StrategyQuery:
    """A preflop query for hero, defaulting to an unopened pot."""
    hero = seat_of(hero_position)
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND}
    street_bet = BIG_BLIND
    for entry in history:
        if entry.action == "raise":
            # The level is what the raise says it is, rather than a ladder this helper
            # invents, so the price the query states and the price the key carries are one
            # number instead of two that can disagree.
            street_bet = entry.amount or street_bet
            committed[entry.seat] = street_bet
        elif entry.action == "call":
            committed[entry.seat] = street_bet
    to_call = max(street_bet - committed.get(hero, 0), 0)
    fields = {
        "hand_id": "h1",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": hole_cards,
        "board": (),
        "legal_actions": ("fold", "call", "raise") if to_call else ("check", "raise"),
        "to_call": to_call,
        "street_bet": street_bet,
        "min_raise_target": street_bet * 2,
        "pot": sum(committed.values()),
        "stacks": stacks(committed),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": history,
    }
    fields.update(overrides)
    return StrategyQuery(**fields)


def cards_for(hand: str) -> tuple[str, str] | None:
    """Two concrete cards for a 169-class name, so a class can be driven through decide.

    None for a string that is not a class name, which is how the table below filters
    the generated candidates without a second list of the 169.
    """
    ranks = "23456789TJQKA"
    if len(hand) == 2:
        if hand[0] != hand[1] or hand[0] not in ranks:
            return None
        return (hand[0] + "s", hand[1] + "h")
    if len(hand) != 3 or hand[2] not in "so":
        return None
    high, low = hand[0], hand[1]
    if high not in ranks or low not in ranks or ranks.index(high) <= ranks.index(low):
        return None
    return (high + "s", low + ("s" if hand[2] == "s" else "h"))


def combos_of(hand: str) -> int:
    """How many of the 1326 starting hands a 169-class name stands for."""
    if len(hand) == 2:
        return 6
    return 4 if hand.endswith("s") else 12


# The prices this table actually plays at, in chips, matching the committed solve. They
# are named rather than derived inside `raised` because since phase 12 the amount is what
# the spot key is built from, and a helper that invented it would be inventing the price
# the chart is then asked about.
OPEN_TO = int(2.5 * BIG_BLIND)
THREE_BET_TO = int(8.0 * BIG_BLIND)
FOUR_BET_TO = int(21.5 * BIG_BLIND)
FIVE_BET_TO = int(50.0 * BIG_BLIND)

# The one committed spot where hero has already acted and faces a re-raise.
THREE_BET_SPOT = "t6/d100/LJ/LJ:raise@2.5,CO:raise@8"


def raised(position: str, amount: int = OPEN_TO) -> SeatAction:
    return SeatAction(seat_of(position), "raise", amount)


def vs_open_key(library: PreflopChartLibrary, hero: str, opener: str) -> str:
    """The committed key for `hero` facing an open from `opener`.

    The opener's price is read out of the keys the artifact declares rather than spelled
    here, which is the same rule the lookup normaliser follows and matters for the same
    reason: this solve opens the small blind to 3.5 and everyone else to 2.5, so one
    constant would already be wrong.
    """
    prices = library.solved_prices_bb(6, DEPTH_BB, hero, (), opener)
    assert len(prices) == 1, (hero, opener, prices)
    return derive_spot_key(6, DEPTH_BB, hero, (PreflopAction(opener, "raise", prices[0]),))


def folded(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


def _hand_cards() -> dict[str, tuple[str, str]]:
    table = {}
    for high in "23456789TJQKA":
        for low in "23456789TJQKA":
            for kind in ("s", "o", ""):
                name = f"{high}{low}{kind}"
                cards = cards_for(name)
                if cards is not None and hand_class(cards) == name:
                    table[name] = cards
    return table


HAND_CARDS: dict[str, tuple[str, str]] = _hand_cards()


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary(import_preflop_artifacts(ARTIFACT_DIR))


def decision(outcome) -> StrategyDecision:
    assert isinstance(outcome, StrategyDecision), outcome
    return outcome


def refusal(outcome) -> StrategyRefusal:
    assert isinstance(outcome, StrategyRefusal), outcome
    return outcome


class TestCommittedArtifact:
    def test_the_artifact_imports_through_the_unchanged_importer(self, library) -> None:
        assert len(library.spot_keys()) >= 36

    def test_provenance_is_declared_as_a_solver_export(self) -> None:
        source = json.loads(ARTIFACT.read_text(encoding="utf-8"))["source"]

        assert source["kind"] == "solver-export"
        assert "rake" in json.dumps(source).lower()

    def test_the_hand_authored_chart_is_retired(self) -> None:
        """Two artifacts claiming one spot is a library error, and the
        hand-authored ranges are known to disagree with the solver."""
        assert not (ARTIFACT_DIR / "six_max_100bb_core.json").exists()

    def test_the_source_export_is_committed_alongside_the_artifact(self) -> None:
        assert SOURCE.exists()

    def test_the_converter_reproduces_the_artifact_byte_for_byte(self) -> None:
        result = subprocess.run(
            ["python", str(REPO_ROOT / "scripts" / "convert_preflop_export.py"), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr

    def test_every_position_that_can_open_has_an_opening_spot(self, library) -> None:
        for position in ("LJ", "HJ", "CO", "BTN", "SB"):
            assert f"t6/d{DEPTH_BB}/{position}/rfi" in library.spot_keys()

    def test_every_spot_facing_a_single_open_is_covered(self, library) -> None:
        order = table_positions(6)
        for opener_index, opener in enumerate(order[:-1]):
            for hero in order[opener_index + 1 :]:
                assert vs_open_key(library, hero, opener) in library.spot_keys()

    def test_the_opener_facing_a_three_bet_is_covered(self, library) -> None:
        assert THREE_BET_SPOT in library.spot_keys()

    def test_the_big_blind_facing_a_limp_is_covered(self, library) -> None:
        assert f"t6/d{DEPTH_BB}/BB/SB:call" in library.spot_keys()


class TestSourceFrequencies:
    """The phase's external oracle: numbers this repo did not produce."""

    def test_expectations_are_committed_in_reviewable_poker_terms(self) -> None:
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))

        assert set(expectations["open_frequency_pct"]) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert set(expectations["big_blind_defence_pct"]) == {"LJ", "HJ", "CO", "BTN", "SB"}

    def test_opening_frequencies_match_the_source(self, library) -> None:
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))

        for position, expected in expectations["open_frequency_pct"].items():
            actual = library.action_frequency_pct(f"t6/d{DEPTH_BB}/{position}/rfi", "raise")

            assert actual == pytest.approx(expected, abs=0.5), position

    def test_big_blind_defence_matches_the_source(self, library) -> None:
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))

        for opener, expected in expectations["big_blind_defence_pct"].items():
            spot = vs_open_key(library, "BB", opener)
            folded_pct = library.action_frequency_pct(spot, "fold")

            assert 100.0 - folded_pct == pytest.approx(expected, abs=0.5), opener

    def test_the_button_opens_much_wider_than_the_lojack(self) -> None:
        """A sanity check a poker player can confirm without reading code."""
        expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
        opens = expectations["open_frequency_pct"]

        assert opens["BTN"] > opens["CO"] > opens["HJ"] > opens["LJ"]


class TestPositionMapping:
    def test_the_first_seat_to_act_six_handed_is_the_lojack(self) -> None:
        """The source calls it UTG; this repo's six-handed vocabulary calls it LJ."""
        assert table_positions(6) == ("LJ", "HJ", "CO", "BTN", "SB", "BB")

    def test_the_artifact_declares_the_whole_table(self) -> None:
        positions = json.loads(ARTIFACT.read_text(encoding="utf-8"))["positions"]

        assert positions == list(table_positions(6))


class TestSizingTable:
    def test_sizings_carry_their_own_provenance(self) -> None:
        table = json.loads(SIZINGS.read_text(encoding="utf-8"))

        assert table["source"]["kind"] == "solver-export"

    def test_every_covered_spot_that_allows_a_raise_has_a_size(self, library) -> None:
        sizing = PreflopSizingTable.from_repo()

        for spot_key in library.spot_keys():
            assert sizing.amount_bb(spot_key) is not None, spot_key

    def test_the_lojack_opens_to_the_size_the_solution_used(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.amount_bb(f"t6/d{DEPTH_BB}/LJ/rfi") == pytest.approx(2.5)

    def test_an_uncovered_spot_has_no_size_rather_than_a_default(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.amount_bb("t6/d40/CO/rfi") is None


class TestDecisions:
    def test_a_covered_open_returns_a_decision(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert outcome.action == "raise"

    def test_a_hopeless_hand_folds_rather_than_refusing(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("7d", "2c"))))

        assert outcome.action == "fold"

    def test_the_raise_amount_comes_from_the_sizing_table(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert outcome.amount == int(2.5 * BIG_BLIND)

    def test_facing_an_open_uses_the_spot_for_that_opener(self, strategy) -> None:
        outcome = strategy.decide(
            query("BB", history=(raised("CO"),), hole_cards=("As", "Ah"))
        )

        assert decision(outcome).action == "raise"

    def test_folds_in_the_history_do_not_change_the_spot(self, strategy) -> None:
        with_folds = strategy.decide(
            query(
                "BB",
                history=(folded("LJ"), folded("HJ"), raised("CO"), folded("BTN"), folded("SB")),
                hole_cards=("As", "Ah"),
            )
        )
        without_folds = strategy.decide(
            query("BB", history=(raised("CO"),), hole_cards=("As", "Ah"))
        )

        assert decision(with_folds).action == decision(without_folds).action

    def test_the_decision_records_the_weights_it_came_from(self, strategy) -> None:
        outcome = decision(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert "raise" in outcome.code
        assert "weighted-draw" in outcome.code


class TestRefusals:
    def test_an_uncovered_stack_depth_refuses(self, strategy) -> None:
        shallow = tuple((seat, 40 * BIG_BLIND) for seat in SEATS)
        outcome = strategy.decide(query("LJ", stacks=shallow, pot=SMALL_BLIND + BIG_BLIND))

        assert "depth" in refusal(outcome).code

    def test_a_straddled_pot_refuses_rather_than_reading_as_ordinary(self, strategy) -> None:
        outcome = strategy.decide(query("LJ", street_bet=2 * BIG_BLIND, to_call=2 * BIG_BLIND))

        assert "blind-structure" in refusal(outcome).code

    def test_an_anted_pot_refuses(self, strategy) -> None:
        outcome = strategy.decide(query("LJ", pot=SMALL_BLIND + BIG_BLIND + 6 * 10))

        assert "blind-structure" in refusal(outcome).code

    def test_a_second_orbit_spot_refuses(self, strategy) -> None:
        """Phase 12 gave it a key; the committed chart still holds no cell for it.

        The refusal is the same answer for a better reason - `spot-not-covered` names a
        cell somebody could fill, where `unrepresentable-spot` named nothing at all.
        """
        history = (
            raised("LJ", OPEN_TO),
            raised("CO", THREE_BET_TO),
            raised("LJ", FOUR_BET_TO),
            raised("CO", FIVE_BET_TO),
        )
        outcome = strategy.decide(query("LJ", history=history))

        assert isinstance(outcome, StrategyRefusal)

    def test_a_postflop_query_refuses(self, strategy) -> None:
        outcome = strategy.decide(
            query("LJ", street="flop", board=("2c", "7h", "Ts"), to_call=0,
                  legal_actions=("check", "raise"))
        )

        assert "preflop" in refusal(outcome).code

    def test_a_short_hero_refuses_even_behind_a_full_stack(self, strategy) -> None:
        """Depth is hero's, not the table's deepest seat.

        Reading the deepest stack meant a twelve-big-blind hero opened a hundred
        big-blind range whenever one untouched seat sat behind, which is an
        unbounded tolerance band on a decision ruled exact-only.
        """
        hero = seat_of("LJ")
        short = tuple(
            (seat, 12 * BIG_BLIND if seat == hero else stack)
            for seat, stack in stacks()
        )

        outcome = refusal(strategy.decide(query("LJ", stacks=short)))

        assert outcome.code.endswith("table-is-not-one-flat-stack-depth")

    def test_a_ragged_depth_refuses_with_its_own_code(self, strategy) -> None:
        odd = tuple((seat, 100 * BIG_BLIND + 37) for seat, _ in stacks())

        outcome = refusal(strategy.decide(query("LJ", stacks=odd)))

        assert outcome.code.endswith("stack-depth-not-a-whole-big-blind")

    def test_an_anted_pot_refuses_at_every_seat_not_just_the_first(self, strategy) -> None:
        """Folds are recorded, so checking only an empty history covered one seat."""
        outcome = strategy.decide(
            query("HJ", history=(folded("LJ"),), pot=SMALL_BLIND + BIG_BLIND + 60)
        )

        assert "blind-structure" in refusal(outcome).code

    def test_a_straddled_pot_refuses_after_someone_raises(self, strategy) -> None:
        """The guard used to stop looking the moment anything raised."""
        outcome = strategy.decide(
            query(
                "BB",
                history=(raised("LJ"),),
                street_bet=6 * BIG_BLIND,
                to_call=5 * BIG_BLIND,
                min_raise_target=11 * BIG_BLIND,
                pot=SMALL_BLIND + BIG_BLIND + 2 * BIG_BLIND + 6 * BIG_BLIND,
            )
        )

        assert "blind-structure" in refusal(outcome).code

    def test_a_charted_action_that_is_not_legal_here_refuses(self, strategy) -> None:
        outcome = strategy.decide(
            query("LJ", hole_cards=("As", "Ah"), legal_actions=("fold", "call"))
        )

        assert "not-legal-here" in refusal(outcome).code

    def test_a_raise_with_no_committed_size_refuses(self, strategy) -> None:
        bare = PreflopChartStrategy(library=strategy.library, sizing=PreflopSizingTable(
            source_name="empty", source_kind="solver-export", raise_to_bb={}
        ))

        outcome = bare.decide(query("LJ", hole_cards=("As", "Ah")))

        assert "no-committed-raise-size" in refusal(outcome).code

    def test_a_committed_size_below_the_minimum_raise_refuses(self, strategy) -> None:
        """A 2.5bb open cannot answer a pot already raised to 6bb."""
        outcome = strategy.decide(
            query("LJ", hole_cards=("As", "Ah"), min_raise_target=12 * BIG_BLIND)
        )

        assert "below-minimum-raise" in refusal(outcome).code

    def test_every_refusal_names_the_coverage_that_was_missing(self, strategy) -> None:
        shallow = tuple((seat, 40 * BIG_BLIND) for seat in SEATS)
        outcome = refusal(strategy.decide(query("LJ", stacks=shallow, pot=SMALL_BLIND + BIG_BLIND)))

        assert outcome.code.startswith("preflop-chart:")


class TestTotality:
    """Coverage proved by enumeration, not by sampling."""

    def test_every_covered_spot_answers_for_all_169_hand_classes(
        self, strategy, library
    ) -> None:
        undecided = []
        for spot_key in sorted(library.spot_keys()):
            for hand in library.hand_classes_for(spot_key):
                outcome = strategy.decide_spot(spot_key, hand)
                if not isinstance(outcome, StrategyDecision):
                    undecided.append((spot_key, hand))

        assert undecided == []

    def test_no_reachable_six_handed_spot_raises(self, strategy) -> None:
        order = table_positions(6)
        hands = [("As", "Ah"), ("7d", "2c"), ("Jc", "Td")]
        for hero in order:
            for opener in order:
                for cards in hands:
                    history = () if opener == hero else (raised(opener),)
                    outcome = strategy.decide(query(hero, history=history, hole_cards=cards))

                    assert isinstance(outcome, StrategyDecision | StrategyRefusal)

    def test_a_decision_is_never_returned_without_chart_backing(
        self, strategy, library
    ) -> None:
        """The one property that makes an artifact-backed bot trustworthy."""
        outcome = strategy.decide(query("LJ", history=(raised("HJ"),), hole_cards=("As", "Ah")))

        assert isinstance(outcome, StrategyRefusal | StrategyDecision)
        if isinstance(outcome, StrategyDecision):
            assert vs_open_key(library, "LJ", "HJ") in library.spot_keys()


class TestLegalityAndDeterminism:
    def test_every_decision_passes_the_phase_03_audit_record(self, strategy) -> None:
        order = table_positions(6)
        for hero in order:
            request = query(hero, hole_cards=("As", "Ah"))
            outcome = strategy.decide(request)
            if isinstance(outcome, StrategyDecision):
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=request,
                    outcome=outcome,
                )

    def test_suit_relabelling_does_not_change_the_decision(self, strategy) -> None:
        spades = strategy.decide(query("BTN", hole_cards=("As", "Ks")))
        hearts = strategy.decide(query("BTN", hole_cards=("Ah", "Kh")))

        assert decision(spades).action == decision(hearts).action

    def test_card_order_does_not_change_the_decision(self, strategy) -> None:
        forwards = strategy.decide(query("BTN", hole_cards=("As", "Kd")))
        backwards = strategy.decide(query("BTN", hole_cards=("Kd", "As")))

        assert decision(forwards).action == decision(backwards).action

    def test_canonicalization_agrees_with_the_hand_class_helper(self) -> None:
        assert hand_class(("As", "Kd")) == hand_class(("Kd", "As")) == "AKo"

    def test_the_same_query_serializes_to_the_same_audit_line(self, strategy) -> None:
        request = query("BTN", hole_cards=("As", "Ah"))
        lines = set()
        for _ in range(3):
            outcome = strategy.decide(request)
            lines.add(
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=request,
                    outcome=outcome,
                ).to_json_line()
            )

        assert len(lines) == 1

    def test_the_draw_depends_on_the_hand_not_only_the_spot(self, strategy) -> None:
        """A seed of spot and hand class alone is the plurality rule wearing a hash.

        It would freeze every mixed cell to one action forever while every frequency
        test that routes through decide_spot kept passing.
        """
        spot = THREE_BET_SPOT
        mixed = next(
            hand
            for hand in strategy.library.hand_classes_for(spot)
            if len(strategy.library.artifacts[0].weights_for(spot, hand)) > 1
        )
        seeds = {
            strategy._seed(query("LJ", hole_cards=("As", "Ah"), hand_id=f"h{index}"), spot, mixed)
            for index in range(5)
        }

        assert len(seeds) == 5

    def test_the_draw_ignores_suits_and_card_order(self, strategy) -> None:
        spot = "t6/d100/BTN/rfi"
        first = strategy._seed(query("BTN", hole_cards=("As", "Kd")), spot, "AKo")
        second = strategy._seed(query("BTN", hole_cards=("Kh", "Ac")), spot, "AKo")

        assert first == second

    def test_decide_reproduces_the_charts_frequencies_over_many_hands(self, strategy) -> None:
        """Measured through decide, not decide_spot, so the seed is under test too."""
        spot = THREE_BET_SPOT
        charted = strategy.library.action_frequency_pct(spot, "fold")
        history = (raised("LJ", OPEN_TO), raised("CO", THREE_BET_TO))
        folds = 0.0
        total = 0.0
        for hand in strategy.library.hand_classes_for(spot):
            cards = HAND_CARDS.get(hand)
            if cards is None:
                continue
            weight = combos_of(hand)
            total += weight
            for index in range(30):
                outcome = strategy.decide(
                    query("LJ", history=history, hole_cards=cards, hand_id=f"h{index}")
                )
                if isinstance(outcome, StrategyDecision) and outcome.action == "fold":
                    folds += weight / 30

        assert 100.0 * folds / total == pytest.approx(charted, abs=3.0)

    def test_a_pure_cell_needs_no_draw(self, strategy) -> None:
        assert strategy.collapse((("fold", 0.0), ("raise", 1.0)), "any") == "raise"

    def test_the_same_seed_draws_the_same_action(self, strategy) -> None:
        mix = (("call", 0.5), ("raise", 0.5))

        assert strategy.collapse(mix, "h1|0|spot|AJo") == strategy.collapse(mix, "h1|0|spot|AJo")

    def test_the_draw_reproduces_the_charts_frequencies(self, strategy) -> None:
        """The whole point: a plurality rule would return one action every time."""
        mix = (("fold", 0.4), ("call", 0.35), ("raise", 0.25))
        counts = Counter(strategy.collapse(mix, f"hand-{index}") for index in range(4000))

        assert counts["fold"] / 4000 == pytest.approx(0.4, abs=0.03)
        assert counts["call"] / 4000 == pytest.approx(0.35, abs=0.03)
        assert counts["raise"] / 4000 == pytest.approx(0.25, abs=0.03)

    def test_a_tie_is_drawn_rather_than_refused(self, strategy) -> None:
        mix = (("call", 0.5), ("raise", 0.5))
        drawn = {strategy.collapse(mix, f"hand-{index}") for index in range(200)}

        assert drawn == {"call", "raise"}

    def test_the_strategy_does_not_over_fold_against_three_bets(self, strategy) -> None:
        """The blocker that halted this phase, pinned as a test.

        A plurality rule folded 72.8% here where the chart folds 59.8%, which is past
        the 66.7% at which an 8bb three-bet over a 2.5x open auto-profits as a pure
        bluff.
        """
        spot = THREE_BET_SPOT
        charted = strategy.library.action_frequency_pct(spot, "fold")
        folds = 0
        total = 0
        for hand in strategy.library.hand_classes_for(spot):
            weight = combos_of(hand)
            total += weight
            for index in range(20):
                outcome = strategy.decide_spot(spot, hand, seed_suffix=str(index))
                if isinstance(outcome, StrategyDecision) and outcome.action == "fold":
                    folds += weight / 20

        assert 100.0 * folds / total == pytest.approx(charted, abs=2.0)


def test_no_two_covered_spots_share_a_hand_class_ordering(library) -> None:
    """Ordering is what makes reports and audits byte-comparable."""
    for spot_key in itertools.islice(sorted(library.spot_keys()), 5):
        first = library.hand_classes_for(spot_key)
        second = library.hand_classes_for(spot_key)

        assert first == second
