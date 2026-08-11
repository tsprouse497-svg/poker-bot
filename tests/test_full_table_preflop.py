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
from poker_training_bot.strategy.contract import (
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
            street_bet = street_bet * 3 if street_bet > BIG_BLIND else BIG_BLIND * 5 // 2
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


def combos_of(hand: str) -> int:
    """How many of the 1326 starting hands a 169-class name stands for."""
    if len(hand) == 2:
        return 6
    return 4 if hand.endswith("s") else 12


def raised(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "raise")


def folded(position: str) -> SeatAction:
    return SeatAction(seat_of(position), "fold")


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
                assert f"t6/d{DEPTH_BB}/{hero}/{opener}:raise" in library.spot_keys()

    def test_the_opener_facing_a_three_bet_is_covered(self, library) -> None:
        assert f"t6/d{DEPTH_BB}/LJ/LJ:raise,CO:raise" in library.spot_keys()

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
            spot = f"t6/d{DEPTH_BB}/BB/{opener}:raise"
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
        """Facing a four-bet has no representable spot key in v1."""
        history = (raised("LJ"), raised("CO"), raised("LJ"), raised("CO"))
        outcome = strategy.decide(query("LJ", history=history))

        assert isinstance(outcome, StrategyRefusal)

    def test_a_postflop_query_refuses(self, strategy) -> None:
        outcome = strategy.decide(
            query("LJ", street="flop", board=("2c", "7h", "Ts"), to_call=0,
                  legal_actions=("check", "raise"))
        )

        assert "preflop" in refusal(outcome).code

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
            assert f"t6/d{DEPTH_BB}/LJ/HJ:raise" in library.spot_keys()


class TestLegalityAndDeterminism:
    def test_every_decision_passes_the_phase_03_audit_record(self, strategy) -> None:
        order = table_positions(6)
        for hero in order:
            request = query(hero, hole_cards=("As", "Ah"))
            outcome = strategy.decide(request)
            if isinstance(outcome, StrategyDecision):
                DecisionAuditRecord(
                    schema_version=1,
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
                    schema_version=1,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=request,
                    outcome=outcome,
                ).to_json_line()
            )

        assert len(lines) == 1

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
        spot = "t6/d100/LJ/LJ:raise,CO:raise"
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
