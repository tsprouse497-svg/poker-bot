"""Phase 05 tests, written from the contract before any implementation existed.

`TestSourceFrequencies` moved to `tests/test_preflop_committed_charts.py`; this file is at its
line cap, which is why the prose is thin. **The cutover moved most of its seats:** over the 86 the
bot opens from one seat and faces a single open from one, so four opening ranges it answers today
are refused (Taylor, 2026-08-25). Prices are per hand class, ruled 2026-08-26; a class offering
two draws one with the action's seed; a checked price is checked against the key, not the table.
"""

from __future__ import annotations

import itertools
import subprocess
from collections import Counter

import pytest

from poker_training_bot.poker_core.positions import position_for_seat, table_positions
from poker_training_bot.solver_artifacts.gtopen_export import COMMITTED_EXPORT_PATH
from poker_training_bot.solver_artifacts.hand_classes import hand_class
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import ChartHit, PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    SeatState,
    StrategyDecision,
    StrategyQuery,
    StrategyRefusal,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
SOURCE = ARTIFACT_DIR / "sources" / "gtowizard_6max_nl25_100bb_preflop.json"

BIG_BLIND = 100
SMALL_BLIND = 50
DEPTH_BB = 100
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3  # seats 0..5 with button at 3 puts LJ at seat 0

COMMITTED_SPOTS = 86
"""At most one opponent invested beyond the blinds and at most two players live. Tree shape."""

SB_OPEN_KEY = f"t6/d{DEPTH_BB}/SB/rfi"
RETIRED_OPENS = ("LJ", "HJ", "CO", "BTN")

LADDER_BB = (2.5, 7.5, 22.5, 100.0)
"""Every raise price the solved tree holds; none of the retired chart's 3.5, 8, 11 or 13.5 does."""

FORCED_RAISE_CELLS, TWO_PRICE_CELLS = 117, 531
"""Of the 7,112 cells the 86 declare, walked over the export: 278 put at least 0.99 on raising once
the jam collapses in and 117 of those put exactly 1.0, and 531 offer their class two prices against
1,688 at one and 4,893 at none. Those 531 sit in exactly 21 spots, the spot-level count."""


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


def solved_line(lib: PreflopChartLibrary, hero: str, *raisers: str) -> tuple[PreflopAction, ...]:
    """`hero`'s line at each seat's solved price - the smaller one, since every point also jams."""
    sequence: list[PreflopAction] = []
    for raiser in raisers:
        prices = lib.solved_prices_bb(6, DEPTH_BB, hero, tuple(sequence), raiser)
        assert prices, (hero, raiser, tuple(sequence))
        sequence.append(PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


def solved_key(library: PreflopChartLibrary, hero: str, *raisers: str) -> str:
    return derive_spot_key(6, DEPTH_BB, hero, solved_line(library, hero, *raisers))


def raised_line(library: PreflopChartLibrary, hero: str, *raisers: str) -> tuple[SeatAction, ...]:
    return tuple(raised(entry.position, int(round(entry.size_bb * BIG_BLIND)))
                 for entry in solved_line(library, hero, *raisers))


def vs_open_key(library: PreflopChartLibrary, hero: str, opener: str) -> str:
    """`hero` facing an open, priced off the **big blind's** spots, the only vs-open ones kept."""
    price = min(library.solved_prices_bb(6, DEPTH_BB, "BB", (), opener))
    return derive_spot_key(6, DEPTH_BB, hero, (PreflopAction(opener, "raise", price),))


def open_to(library: PreflopChartLibrary) -> int:
    """The solved opening price in chips. An out-of-turn opener has no solved price anywhere."""
    prices = library.solved_prices_bb(6, DEPTH_BB, "BB", (), "LJ")
    return int(round(min(prices) * BIG_BLIND))


def sizes_bb(
    sizing: PreflopSizingTable, spot_key_text: str, hand_class_text: str
) -> tuple[tuple[float, float], ...]:
    """Ruled 2026-08-26: every price this **class** may raise to, weighted over its aggression."""
    assert hasattr(sizing, "sizes_bb"), "the table must offer sizes_bb(spot_key, hand_class)"
    return tuple(sizing.sizes_bb(spot_key_text, hand_class_text) or ())


def three_bet_spot(library: PreflopChartLibrary) -> str:
    """`t6/d100/LJ/LJ:raise@2.5,CO:raise@7.5`: hero opened, faces a re-raise, may four-bet."""
    return solved_key(library, "LJ", "LJ", "CO")


def four_bet_faced(library: PreflopChartLibrary) -> tuple[str, tuple[SeatAction, ...]]:
    """BB three-bet, BTN four-bet, hero to act. One of the 15 offering the stack and no raise."""
    line = ("BB", "BTN", "BB", "BTN")
    return solved_key(library, *line), raised_line(library, *line)


def sb_open(hole_cards: tuple[str, str] = ("As", "Ah"), **overrides) -> StrategyQuery:
    ahead = tuple(folded(seat) for seat in table_positions(6)[:4])
    return query("SB", history=ahead, hole_cards=hole_cards, **overrides)


def audit_record(strategy, request, outcome) -> DecisionAuditRecord:
    return DecisionAuditRecord(
        schema_version=DECISION_AUDIT_SCHEMA_VERSION, strategy_id=strategy.strategy_id,
        strategy_version=strategy.strategy_version, query=request, outcome=outcome,
    )


def _hand_cards() -> dict[str, tuple[str, str]]:
    ranks = "23456789TJQKA"
    names = (f"{high}{low}{kind}" for high in ranks for low in ranks for kind in ("s", "o", ""))
    found = ((name, cards_for(name)) for name in names)
    return {name: cards for name, cards in found if cards and hand_class(cards) == name}


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
        """The count, not a floor: "more than 36" assumed the retired chart was a subset."""
        assert len(library.artifacts) == 1
        assert len(library.spot_keys()) == COMMITTED_SPOTS

    def test_provenance_is_declared_as_a_solver_export(self, library) -> None:
        source = library.artifacts[0].source
        assert source.kind == "solver-export"
        assert (REPO_ROOT / source.reference) == COMMITTED_EXPORT_PATH

    def test_the_hand_authored_chart_is_retired(self) -> None:
        assert not (ARTIFACT_DIR / "six_max_100bb_core.json").exists()

    def test_the_gto_wizard_source_is_kept_even_though_its_chart_is_gone(self) -> None:
        assert SOURCE.exists()

    def test_the_converter_reproduces_the_artifact_byte_for_byte(self) -> None:
        converter = str(REPO_ROOT / "scripts" / "convert_preflop_export.py")
        result = subprocess.run(
            ["python", converter, "--check"], cwd=REPO_ROOT, capture_output=True, text=True
        )

        assert result.returncode == 0, result.stdout + result.stderr

    def test_the_small_blind_is_the_only_position_with_an_opening_spot(self, library) -> None:
        """Both halves: only the SB has one seat behind, and losing its open must fail here too."""
        assert SB_OPEN_KEY in library.spot_keys()
        for position in RETIRED_OPENS:
            assert f"t6/d{DEPTH_BB}/{position}/rfi" not in library.spot_keys()

    def test_only_the_big_blind_is_covered_facing_a_single_open(self, library) -> None:
        """Only the big blind closes the action, so only there is every terminal heads-up."""
        order = table_positions(6)
        covered = set()
        for opener_index, opener in enumerate(order[:-1]):
            for hero in order[opener_index + 1 :]:
                key = vs_open_key(library, hero, opener)
                assert (key in library.spot_keys()) is (hero == "BB"), key
                if hero == "BB":
                    covered.add(key)

        assert len(covered) == 5

    def test_the_opener_facing_a_three_bet_is_covered(self, library) -> None:
        assert three_bet_spot(library) in library.spot_keys()

    def test_the_big_blind_facing_a_limp_is_no_longer_covered(self, library) -> None:
        """`limp: false`, so it passes the predicate with no node: 22 of the retired 36 pass."""
        assert f"t6/d{DEPTH_BB}/BB/SB:call" not in library.spot_keys()


class TestPositionMapping:
    def test_the_first_seat_to_act_six_handed_is_the_lojack(self) -> None:
        assert table_positions(6) == ("LJ", "HJ", "CO", "BTN", "SB", "BB")

    def test_the_artifact_declares_the_whole_table(self, library) -> None:
        assert library.artifacts[0].positions == table_positions(6)


class TestDecisions:
    def test_the_one_committed_opening_range_opens_at_a_price_the_spot_offers(self, strategy):
        """A real hand rather than a bare key, so seat mapping, price rendering and depth run.
        The spot offers two prices and aces one of them: walked over the export, six of the 169
        classes weight the open-shove - AKs, AQs, 99 at a basis point, JJ, TT at two, AKo at
        three - so the amount is pinned and decision 6's retired per-spot weights fail here."""
        weights = strategy.weights_for(sb_open())
        aces = sizes_bb(strategy.sizing, SB_OPEN_KEY, "AA")
        outcome = decision(strategy.decide(sb_open()))

        assert not isinstance(weights, StrategyRefusal), weights
        assert dict(weights).get("raise") == pytest.approx(1.0)
        assert dict(weights).get("call", 0.0) == 0.0
        assert [price for price, _ in aces] == [pytest.approx(2.5)]
        assert len(sizes_bb(strategy.sizing, SB_OPEN_KEY, "AKo")) == 2
        assert outcome.action == "raise"
        assert outcome.amount == round(2.5 * BIG_BLIND)

    def test_the_price_is_drawn_from_the_classs_own_weights_with_the_actions_seed(self, strategy):
        """The seeded price draw, at the one cell where a draw can be seen. It ran at the small
        blind's open, where nothing could catch what it named: six classes there carry any jam
        weight and the jam is a hundred-thousandth of hero's aggressive volume, so a uniformly
        random picker returns one amount in eight draws 99.99 percent of the time. AKo at the big
        blind facing a button open is the subject instead: walked over the export it raises with
        weight 1.0, so no action draw intervenes, and splits that 3,359 basis points to 7.5
        against 6,641 to the stack, where eight ids tell a seed from an RNG at probability 0.99.
        Killed: taking the smallest price, which never jams; the highest-weight one, which always
        jams; refusing a class offering two; a per-instance RNG, which cannot reproduce the twin's
        sequence over 240 ids; and the retired per-**spot** weights, whose jam share is 0.0761.
        Not killed: any other stable seed, since every one draws this share and repeats."""
        key = vs_open_key(strategy.library, "BB", "BTN")
        history = raised_line(strategy.library, "BB", "BTN")
        twin = PreflopChartStrategy(library=strategy.library, sizing=strategy.sizing)
        offered = sizes_bb(strategy.sizing, key, "AKo")
        asked = [query("BB", history=history, hole_cards=("As", "Kd"), hand_id=f"h{index}")
                 for index in range(240)]
        drawn = [(decision(strategy.decide(ask)).amount, decision(twin.decide(ask)).amount)
                 for ask in asked]
        jams = [mine for mine, _ in drawn].count(round(100.0 * BIG_BLIND))

        assert [price for price, _ in offered] == pytest.approx([7.5, 100.0])
        assert [weight for _, weight in offered] == pytest.approx([0.3359, 0.6641])
        assert {mine for mine, _ in drawn} == {round(7.5 * BIG_BLIND), round(100.0 * BIG_BLIND)}
        assert all(mine == theirs for mine, theirs in drawn)
        assert jams / len(drawn) == pytest.approx(0.6641, abs=0.12)

    def test_a_hopeless_hand_folds_rather_than_refusing(self, strategy) -> None:
        outcome = decision(strategy.decide(sb_open(("7d", "2c"))))

        assert outcome.action == "fold"

    def test_the_raise_amount_comes_from_the_sizing_table(self, strategy) -> None:
        """Every raise is checked, and the expected amount is hero's whole stack rather than what
        the table holds - reading it back off `sizes_bb` compared the table against itself. Walked
        over the export, the 15 jam-only spots price 693 cells and every one is at the stack."""
        key, history = four_bet_faced(strategy.library)
        amounts, priced = set(), 0
        for hand, cards in HAND_CARDS.items():
            offered = sizes_bb(strategy.sizing, key, hand)
            priced += len(offered) == 1
            assert [price for price, _ in offered] in ([], [pytest.approx(DEPTH_BB)]), hand
            outcome = strategy.decide(query("BB", history=history, hole_cards=cards))
            if isinstance(outcome, StrategyDecision) and outcome.action == "raise":
                amounts.add(outcome.amount)

        assert priced
        assert amounts == {round(DEPTH_BB * BIG_BLIND)}

    def test_facing_an_open_uses_the_spot_for_that_opener(self, strategy) -> None:
        """The key rather than the action: the lookup is where "which opener" is decided anyway."""
        opened = raised_line(strategy.library, "BB", "CO")
        found = strategy.chart_lookup(query("BB", history=opened, hole_cards=("As", "Ah")))

        assert isinstance(found, ChartHit), found
        assert found.spot_key == vs_open_key(strategy.library, "BB", "CO")

    def test_folds_in_the_history_do_not_change_the_spot(self, strategy) -> None:
        opened = raised_line(strategy.library, "BB", "CO")
        padded = (folded("LJ"), folded("HJ"), *opened, folded("BTN"), folded("SB"))
        expected = vs_open_key(strategy.library, "BB", "CO")
        with_folds = strategy.chart_lookup(query("BB", history=padded, hole_cards=("As", "Ah")))
        without = strategy.chart_lookup(query("BB", history=opened, hole_cards=("As", "Ah")))

        assert isinstance(with_folds, ChartHit) and isinstance(without, ChartHit)
        assert with_folds.spot_key == without.spot_key == expected

    def test_the_decision_records_the_weights_it_came_from(self, strategy) -> None:
        opened = raised_line(strategy.library, "BB", "BTN")
        outcome = decision(strategy.decide(query("BB", history=opened, hole_cards=("7d", "2c"))))

        assert outcome.code.startswith(f"preflop-chart:weighted-draw:{outcome.action}[")
        assert outcome.code.count("=") > 1


class TestRefusals:
    """Each must refuse for the reason it names, and the ones reaching the chart moved seats."""

    def test_the_lojacks_own_open_is_refused_as_an_uncovered_spot(self, strategy) -> None:
        """The ruled cost where a human meets it: the lojack opens 19.1 percent, the bot none."""
        outcome = refusal(strategy.decide(query("LJ", hole_cards=("As", "Ah"))))

        assert outcome.code.endswith("spot-not-covered")
        assert ("spot_key", f"t6/d{DEPTH_BB}/LJ/rfi") in outcome.detail

    def test_an_uncovered_stack_depth_refuses(self, strategy) -> None:
        """A flat 40bb table at the one open a 100bb chart answers, so only depth is missing."""
        outcome = strategy.decide(sb_open(stacks=stacks(depth_bb=40)))

        assert "depth" in refusal(outcome).code

    def test_a_straddled_pot_refuses_rather_than_reading_as_ordinary(self, strategy) -> None:
        """Nobody has raised, so a level above the big blind is a straddle and nothing else."""
        outcome = strategy.decide(query("HJ", forced={seat_of("LJ"): 2 * BIG_BLIND}))

        assert refusal(outcome).code.endswith("pot-holds-a-straddle")

    def test_an_anted_pot_refuses(self, strategy) -> None:
        """An ante sits in a hand total, not a street total: the pot alone cannot describe it."""
        outcome = strategy.decide(query("LJ", ante=10))

        assert refusal(outcome).code.endswith("pot-holds-an-ante")

    def test_a_second_orbit_spot_is_now_decided_rather_than_refused(self, strategy) -> None:
        """Phase 12 gave it a key and the raked chart no cell; the solved tree runs to a
        four-bet and a shove, the predicate keeps that line, and hero may only fold or call."""
        history = raised_line(strategy.library, "LJ", "LJ", "CO", "LJ", "CO")
        assert len(history) == 4

        outcome = strategy.decide(
            query("LJ", history=history, hole_cards=("As", "Ah"), legal_actions=("fold", "call"))
        )

        assert isinstance(outcome, StrategyDecision), outcome

    def test_a_limped_pot_refuses_because_no_solved_node_holds_one(self, strategy) -> None:
        """The one miss a fixed GTOpen cannot recover: a limped pot has no node in the tree."""
        history = (folded("LJ"), folded("HJ"), folded("CO"), folded("BTN"), called("SB"))
        outcome = refusal(strategy.decide(query("BB", history=history, hole_cards=("As", "Ah"))))

        assert outcome.code.endswith("spot-not-covered")

    def test_a_postflop_query_refuses(self, strategy) -> None:
        flop = query("LJ", street="flop", board=("2c", "7h", "Ts"), to_call=0,
                     legal_actions=("check", "raise"))
        outcome = strategy.decide(flop)

        assert "preflop" in refusal(outcome).code

    def test_a_short_hero_refuses_even_behind_a_full_stack(self, strategy) -> None:
        """Depth is hero's: reading the deepest stack let a 12bb hero open a 100bb range."""
        hero = seat_of("LJ")
        short = tuple((s, 12 * BIG_BLIND if s == hero else v) for s, v in stacks())
        outcome = refusal(strategy.decide(query("LJ", stacks=short)))

        assert outcome.code.endswith("table-is-not-one-flat-stack-depth")

    def test_a_ragged_depth_refuses_with_its_own_code(self, strategy) -> None:
        odd = tuple((seat, 100 * BIG_BLIND + 37) for seat, _ in stacks())
        outcome = refusal(strategy.decide(query("LJ", stacks=odd)))

        assert outcome.code.endswith("stack-depth-not-a-whole-big-blind")

    def test_an_anted_pot_refuses_at_every_seat_not_just_the_first(self, strategy) -> None:
        """A folded seat's ante is still in the pot; a reconstruction from live seats misses it."""
        outcome = strategy.decide(query("HJ", history=(folded("LJ"),), ante=10))

        assert refusal(outcome).code.endswith("pot-holds-an-ante")

    def test_a_straddled_pot_refuses_after_someone_raises(self, strategy) -> None:
        """Raised over, a straddler's chips look like a caller's; the target gives it away."""
        history = (raised("HJ", 6 * BIG_BLIND), folded("CO"), folded("BTN"), folded("SB"))
        outcome = strategy.decide(
            query("BB", history=history, forced={seat_of("LJ"): 2 * BIG_BLIND})
        )

        assert refusal(outcome).code.endswith("pot-holds-a-straddle")

    def test_a_charted_action_that_is_not_legal_here_refuses(self, strategy) -> None:
        outcome = strategy.decide(sb_open(legal_actions=("fold", "call")))

        assert "not-legal-here" in refusal(outcome).code

    def test_a_raise_with_no_committed_size_refuses(self, strategy) -> None:
        """The table is emptied rather than thinned, so this refuses under any price rule."""
        bare = PreflopChartStrategy(library=strategy.library, sizing=PreflopSizingTable(
            source_name="empty", source_kind="solver-export", raise_to_bb={}
        ))
        outcome = bare.decide(sb_open())

        assert "no-committed-raise-size" in refusal(outcome).code

    def test_a_committed_size_below_the_minimum_raise_refuses(self, strategy) -> None:
        """A 2.5bb open cannot answer a pot raised to 6bb. The price is written here rather than
        read off the table - the only fixture that does - at the per-class shape ruled 2026-08-26,
        keyed on the aces `sb_open` holds so the one price leaves the draw nothing to pick. It is
        built rather than loaded because a payload written at the ruled version fails the loader's
        version check first, which is a fixture red rather than the refusal this test is about."""
        priced = PreflopChartStrategy(library=strategy.library, sizing=PreflopSizingTable(
            source_name="one-price", source_kind="solver-export",
            raise_to_bb={SB_OPEN_KEY: {"AA": [{"to_bb": 2.5, "weight": 1.0}]}},
        ))
        offered = sizes_bb(priced.sizing, SB_OPEN_KEY, "AA")
        outcome = priced.decide(sb_open(min_raise_target=12 * BIG_BLIND))

        assert [price for price, _ in offered] == [pytest.approx(2.5)]
        assert "below-minimum-raise" in refusal(outcome).code

    def test_every_refusal_names_the_coverage_that_was_missing(self, strategy) -> None:
        outcome = refusal(strategy.decide(sb_open(stacks=stacks(depth_bb=40))))

        assert outcome.code.startswith("preflop-chart:")


class TestTotality:

    def test_every_covered_cell_the_chart_can_price_answers(self, strategy, library) -> None:
        """Every cell of every covered spot, every price checked against the tree rather than
        against the table that produced it. `offered` was read from `sizes_bb`, which is where
        `decide_spot` reads it too, so `mispriced == []` said the implementation equalled itself.
        It comes off the **key** now: a key names the level hero faces, so his menu is the next
        rung of the ladder above it plus the stack, which reproduces all 86 menus exactly and
        fails a table pricing a three-bet spot at the open size. And the forced-cell claim is per
        cell - `drew >= forced` compared totals, so raising another set of the same size passed."""
        artifact = library.artifacts[0]
        undecided, mispriced, forced, drew, two_priced = [], [], [], set(), 0
        for spot_key in sorted(library.spot_keys()):
            faced = [float(part.split("@")[1])
                     for part in spot_key.rsplit("/", 1)[-1].split(",") if "@" in part]
            rungs = [rung for rung in LADDER_BB if rung > max(faced, default=0.0)]
            offered = {max(round(rung * 100), 1) for rung in rungs[:1] + rungs[-1:]}
            assert library.hand_classes_for(spot_key), spot_key
            for hand in library.hand_classes_for(spot_key):
                two_priced += len(sizes_bb(strategy.sizing, spot_key, hand)) == 2
                if dict(artifact.weights_for(spot_key, hand) or ()).get("raise", 0) >= 1.0 - 1e-9:
                    forced.append((spot_key, hand))
                outcome = strategy.decide_spot(spot_key, hand)
                if not isinstance(outcome, StrategyDecision):
                    undecided.append((spot_key, hand))
                elif outcome.action == "raise":
                    drew.add((spot_key, hand))
                    if outcome.amount not in offered:
                        mispriced.append((spot_key, hand, outcome.amount))

        assert undecided == []
        assert mispriced == []
        assert [cell for cell in forced if cell not in drew] == []
        assert len(forced) == FORCED_RAISE_CELLS
        assert two_priced == TWO_PRICE_CELLS

    def test_no_reachable_six_handed_spot_raises(self, strategy) -> None:
        order = table_positions(6)
        hands = [("As", "Ah"), ("7d", "2c"), ("Jc", "Td")]
        price = open_to(strategy.library)
        for hero in order:
            for opener in order:
                for cards in hands:
                    history = () if opener == hero else (raised(opener, price),)
                    outcome = strategy.decide(query(hero, history=history, hole_cards=cards))

                    assert isinstance(outcome, StrategyDecision | StrategyRefusal)

    def test_a_decision_is_never_returned_without_chart_backing(self, strategy, library) -> None:
        history = (raised("HJ", open_to(library)),)
        behind = strategy.decide(query("CO", history=history, hole_cards=("As", "Ah")))
        closing = strategy.decide(query("BB", history=history, hole_cards=("7d", "2c")))

        assert refusal(behind).code.endswith("spot-not-covered")
        assert vs_open_key(library, "CO", "HJ") not in library.spot_keys()
        assert isinstance(closing, StrategyDecision)
        assert vs_open_key(library, "BB", "HJ") in library.spot_keys()


class TestLegalityAndDeterminism:
    """The tests that decided twice and compared moved to the big blind facing a four-bet."""

    def test_every_decision_passes_the_phase_03_audit_record(self, strategy) -> None:
        """It counts what it recorded. AA and A5s reach a four-bet faced and jam and call."""
        _, four_bet = four_bet_faced(strategy.library)
        hands = (("As", "Ah"), ("Ac", "5c"))
        requests = [query("BB", history=four_bet, hole_cards=cards) for cards in hands]
        requests.append(sb_open(("7d", "2c")))
        recorded = 0
        for request in requests:
            outcome = strategy.decide(request)
            if isinstance(outcome, StrategyDecision):
                recorded += 1
                audit_record(strategy, request, outcome)

        assert recorded == len(requests)

    def test_suit_relabelling_does_not_change_the_decision(self, strategy) -> None:
        _, history = four_bet_faced(strategy.library)
        spades = strategy.decide(query("BB", history=history, hole_cards=("As", "Ks")))
        hearts = strategy.decide(query("BB", history=history, hole_cards=("Ah", "Kh")))

        assert decision(spades).action == decision(hearts).action

    def test_card_order_does_not_change_the_decision(self, strategy) -> None:
        _, history = four_bet_faced(strategy.library)
        forwards = strategy.decide(query("BB", history=history, hole_cards=("As", "Kd")))
        backwards = strategy.decide(query("BB", history=history, hole_cards=("Kd", "As")))

        assert decision(forwards).action == decision(backwards).action

    def test_canonicalization_agrees_with_the_hand_class_helper(self) -> None:
        assert hand_class(("As", "Kd")) == hand_class(("Kd", "As")) == "AKo"

    def test_the_same_query_serializes_to_the_same_audit_line(self, strategy) -> None:
        """A serialized refusal repeats as stably as a decision, so a refused seat proves little."""
        _, four_bet = four_bet_faced(strategy.library)
        request = query("BB", history=four_bet, hole_cards=("As", "Ah"))
        lines = set()
        for _ in range(3):
            outcome = strategy.decide(request)
            lines.add(audit_record(strategy, request, outcome).to_json_line())

        assert isinstance(strategy.decide(request), StrategyDecision)
        assert len(lines) == 1

    def test_the_draw_depends_on_the_hand_not_only_the_spot(self, strategy) -> None:
        """Spot-and-class seeding freezes every mixed cell, and frequency tests keep passing."""
        spot = three_bet_spot(strategy.library)
        mixed = next(h for h in strategy.library.hand_classes_for(spot)
                     if len(strategy.library.artifacts[0].weights_for(spot, h)) > 1)
        seeds = {strategy._seed(query("LJ", hole_cards=("As", "Ah"), hand_id=f"h{i}"), spot, mixed)
                 for i in range(5)}

        assert len(seeds) == 5

    def test_the_draw_ignores_suits_and_card_order(self, strategy) -> None:
        """At the lojack facing a three-bet, where AKo calls 96.3 percent and four-bets the rest."""
        spot = three_bet_spot(strategy.library)
        first = strategy._seed(query("LJ", hole_cards=("As", "Kd")), spot, "AKo")
        second = strategy._seed(query("LJ", hole_cards=("Kh", "Ac")), spot, "AKo")

        assert first == second

    def test_decide_reproduces_the_charts_frequencies_over_many_hands(self, strategy) -> None:
        """Through decide, not decide_spot, so the seed is under test too; folding needs no size."""
        spot = three_bet_spot(strategy.library)
        charted = strategy.library.action_frequency_pct(spot, "fold")
        history = raised_line(strategy.library, "LJ", "LJ", "CO")
        folds = total = 0.0
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
        """The blocker that halted this phase: a plurality rule folded 72.8% against 59.8%."""
        spot = three_bet_spot(strategy.library)
        charted = strategy.library.action_frequency_pct(spot, "fold")
        folds = total = 0
        for hand in strategy.library.hand_classes_for(spot):
            weight = combos_of(hand)
            total += weight
            for index in range(20):
                outcome = strategy.decide_spot(spot, hand, seed_suffix=str(index))
                if isinstance(outcome, StrategyDecision) and outcome.action == "fold":
                    folds += weight / 20

        assert 100.0 * folds / total == pytest.approx(charted, abs=2.0)


def test_no_two_covered_spots_share_a_hand_class_ordering(library) -> None:
    for spot_key in itertools.islice(sorted(library.spot_keys()), 5):
        first = library.hand_classes_for(spot_key)
        second = library.hand_classes_for(spot_key)

        assert first == second
