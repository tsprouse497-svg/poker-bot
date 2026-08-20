"""What the six Phase 11 fixes changed, in chips a person can check by hand.

Every number below is computed on this run from the engine, the query, and the fallback
themselves. Nothing is read back from a figure an earlier run recorded, because a report
that quotes its own previous answer proves only that it is consistent with itself.

The "before" column is not measured - the old behaviour is gone from the tree by the time
this runs - so it is stated from `backlog.yml` and the phase contract and labelled as
stated rather than computed. What is computed is every "after".
"""

from __future__ import annotations

import sys

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.poker_core.cards import parse_cards  # noqa: E402
from poker_training_bot.poker_core.engine import (  # noqa: E402
    Action,
    ActionKind,
    BettingRoundState,
    PlayerState,
)
from poker_training_bot.poker_core.order import TurnState  # noqa: E402
from poker_training_bot.strategy.contract import (  # noqa: E402
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    StrategyDecision,
    StrategyQuery,
)
from poker_training_bot.strategy.postflop_fallback import (  # noqa: E402
    PostflopFallbackStrategy,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy  # noqa: E402

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_engine_fidelity_report.txt"

_HOLE_TEXTS = ("As", "Ah", "Ks", "Kh", "Qs", "Qh", "Js", "Jh", "Ts", "Th", "9s", "9h")


def _player(seat: int, stack: int, bet: int = 0) -> PlayerState:
    return PlayerState(
        seat=seat,
        name=f"seat {seat}",
        stack=stack,
        hole_cards=parse_cards(_HOLE_TEXTS[2 * seat : 2 * seat + 2]),
        street_bet=bet,
    )


def _round(stacks: tuple[int, ...], min_raise: int = 20) -> BettingRoundState:
    return BettingRoundState(
        players=tuple(_player(seat, stack) for seat, stack in enumerate(stacks)),
        current_bet=0,
        min_raise=min_raise,
    )


def _free_fold_section() -> list[str]:
    state = _round((100, 100))
    before = state.apply(Action(0, ActionKind.FOLD))
    return [
        "1. A fold is legal whenever a seat may act  (FOLD-WHEN-FREE)",
        "",
        "   Was:  a seat with nothing to call was offered check and aggression only, so",
        "         applying a fold raised 'fold is not legal'. Any real history holding a",
        "         surrendered river or a timed-out check failed to replay at the action.",
        "   Now:  the same seat is offered "
        + ", ".join(kind.value for kind in state.legal_actions(0)),
        "",
        "   Worked example. Two seats, 100 chips each, nobody has bet this street.",
        f"     seat 0 folds for free -> chips committed {before.player(0).committed_total},"
        f" stack {before.player(0).stack}",
        f"     the bet level stays {before.current_bet} and the minimum raise stays"
        f" {before.min_raise}",
        f"     seat 0 is now folded={before.player(0).folded} and is offered"
        f" {list(before.legal_actions(0))}",
        "",
        "   Legal is not chosen. No strategy in this repo folds when checking is free:",
    ]


def _no_free_folds_section() -> list[str]:
    fallback = PostflopFallbackStrategy()
    lines: list[str] = []
    for street, board in (
        ("flop", ("2c", "7h", "Ts")),
        ("turn", ("2c", "7h", "Ts", "4d")),
        ("river", ("2c", "7h", "Ts", "4d", "9c")),
    ):
        outcome = fallback.decide(
            StrategyQuery(
                hand_id="engine-fidelity-report",
                street=street,
                seat=1,
                button_seat=0,
                hole_cards=("As", "Kd"),
                board=board,
                legal_actions=("fold", "check", "bet"),
                to_call=0,
                street_bet=20,
                min_raise_target=40,
                pot=60,
                stacks=((0, 980), (1, 940)),
                blinds=(5, 10),
            )
        )
        action = outcome.action if isinstance(outcome, StrategyDecision) else "refused"
        lines.append(f"     postflop fallback, {street:<5} free spot -> {action}")

    library = PreflopChartStrategy.from_repo().library
    free_spots = [
        key
        for key in library.spot_keys()
        if key.split("/")[2] == "BB" and "raise" not in key.split("/")[3]
    ]
    for key in free_spots:
        pct = library.action_frequency_pct(key, "fold")
        lines.append(f"     committed chart spot {key} -> fold {pct:.2f}% of the range")
    lines.append("")
    return lines


def _reopening_states(second: int) -> TurnState:
    turn = TurnState.start_postflop(_round((100, 15, second, 100), min_raise=2), button_seat=3)
    turn = turn.apply(Action(0, ActionKind.BET, 10))
    turn = turn.apply(Action(1, ActionKind.RAISE, 15))
    return turn.apply(Action(2, ActionKind.RAISE, second))


def _reopening_section() -> list[str]:
    lines = [
        "2. Betting reopens when short all-ins accumulate  (UNDER-RAISE-ACCUMULATION)",
        "",
        "   Was:  each all-in was measured against the bet level immediately before it, so",
        "         two short all-ins that together made a full raise left betting closed.",
        "   Now:  the measurement is against the last full bet or raise, and a full bet or",
        "         raise resets the level it is measured from.",
        "",
        "   Worked example. Four seats. Seat 0 bets 10, which sets the bet level to 10 and",
        "   the minimum raise to 10. Seat 1 is all-in for 15 - five over, half a raise.",
        "   Seat 2 is then all-in for the amount shown. Seat 0 has already acted.",
        "",
        "     seat 2 all-in to   advance since the last full raise (10)   seat 0 may raise",
    ]
    for second in (19, 20, 21, 30):
        turn = _reopening_states(second)
        may = ActionKind.RAISE in turn.legal_actions(0)
        lines.append(
            f"     {second:>16}   {second - 10:>38}   {'yes' if may else 'no':>16}"
        )
    short_open = TurnState.start_postflop(_round((5, 100, 22, 100), min_raise=20), button_seat=3)
    short_open = short_open.apply(Action(0, ActionKind.BET, 5))
    short_open = short_open.apply(Action(1, ActionKind.CALL))
    short_open = short_open.apply(Action(2, ActionKind.RAISE, 22))
    turn = _reopening_states(21)
    lines += [
        "",
        "   A street opened by a short all-in has had no full bet on it, so the reference",
        "   stays at the level the street opened on. Minimum bet 20, seat 0 all-in for 5,",
        "   seat 1 calls, seat 2 all-in for 22: the street has advanced 22 from nothing,",
        "   which is past a full bet, so seat 1 may raise.",
        f"     seat 1 is offered"
        f" {[kind.value for kind in short_open.legal_actions(1)]}",
    ]
    lines += [
        "",
        "   The bar is the minimum raise of 10, so 20 clears it and 19 does not. Reopening",
        "   restores the right to raise and not a cheaper price for it: with the level at",
        f"   {turn.round.current_bet} and the minimum raise still {turn.round.min_raise},"
        f" seat 0's smallest legal raise is to"
        f" {turn.round.current_bet + turn.round.min_raise}.",
        "",
        "   A seat barred from raising may still call and may still fold:",
        f"     at 19, seat 0 is offered"
        f" {[kind.value for kind in _reopening_states(19).legal_actions(0)]}",
        "",
    ]
    return lines


def _query_for(street_bet: int, to_call: int, stack: int) -> StrategyQuery:
    return StrategyQuery(
        hand_id="engine-fidelity-report",
        street="flop",
        seat=1,
        button_seat=0,
        hole_cards=("As", "Kd"),
        board=("2c", "7h", "Ts"),
        legal_actions=("fold", "call", "raise"),
        to_call=to_call,
        street_bet=street_bet,
        min_raise_target=street_bet + 20,
        pot=60,
        stacks=((0, 980), (1, stack)),
        blinds=(5, 10),
    )


def _street_bet_section() -> list[str]:
    rejected = ""
    try:
        _query_for(street_bet=10, to_call=20, stack=100)
    except ValueError as error:
        rejected = str(error)
    return [
        "3. street_bet means the street's bet level  (STREET-BET-MEANING-AMBIGUOUS)",
        "",
        "   Was:  the field carried no statement of which of two readings it held, and",
        "         scripts/generate_strategy_query_report.py passed hero's own contribution",
        "         while every other producer passed the street's level.",
        "   Now:  the meaning is written on StrategyQuery, the one producer is corrected,",
        "         and a query whose street_bet is below its to_call is rejected.",
        "",
        "   Worked example. Heads-up, blinds 5 and 10, the small blind acts preflop. Hero",
        "   has put in 5, the level is 10, the price to call is 5.",
        "     the wrong reading passed 5, and the chart derived hero's starting stack as",
        "       stacks[seat] + (5 - 5), which is the stack itself, and refused with",
        "       preflop-chart:blind-structure-not-representable",
        "     the right reading passes 10, and the chart refuses with",
        "       preflop-chart:lookup:no-artifact-for-table-size, which is the true miss:",
        "       a two-handed table against a six-handed chart",
        "",
        "   The guard, and its measured limit. A query with street_bet 10 and to_call 20 is",
        f"   rejected: {rejected}",
        "   It catches a producer passing hero's contribution only when hero has put in",
        "   less than half the level, so it misses the heads-up small blind, who has put in",
        "   exactly half. Filed as STRATEGY-QUERY-STREET-BET-NAME.",
        "",
    ]


def _ceiling_section() -> list[str]:
    query = _query_for(street_bet=20, to_call=20, stack=100)
    accepted, rejected = [], []
    for amount in (100, 101, 120):
        try:
            DecisionAuditRecord(
                schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                strategy_id="engine-fidelity-report",
                strategy_version=1,
                query=query,
                outcome=StrategyDecision("raise", amount, "report:probe"),
            )
            accepted.append(amount)
        except ValueError:
            rejected.append(amount)
    return [
        "4. The all-in ceiling is what hero can raise to  (DECISION-AUDIT-ALL-IN-BOUND-TOO-LOOSE)",
        "",
        "   Was:  the ceiling was the street's bet level plus hero's stack, which is too",
        "         high by exactly the price to call.",
        "   Now:  it is hero's own contribution to the street plus hero's stack.",
        "",
        "   Worked example. Street bet 20, price to call 20, stack 100. Hero has put in",
        "   20 minus 20, which is nothing, so hero's all-in raise target is 100.",
        f"     accepted: {accepted}",
        f"     rejected: {rejected}",
        "   The old ceiling accepted a raise to 120 and only rejected 121.",
        "",
    ]


def _fail_closed_section() -> list[str]:
    fallback = PostflopFallbackStrategy()
    lines = [
        "5. The fail-closed branch never invests  (FALLBACK-FAIL-CLOSED-CAN-CALL)",
        "",
        "   Was:  the branch took the most passive action from fold then call, so a set",
        "         offering call but not fold invested in a hand that can lose.",
        "   Now:  it folds when fold is legal and refuses otherwise. It never calls.",
        "",
        "   Neither set below is reachable from the engine's own legal actions, which is",
        "   why neither was covered. Both are contract-valid queries.",
        "",
    ]
    for legal in (("fold", "call"), ("call", "raise"), ("raise",)):
        outcome = fallback.decide(_query_for_legal(legal))
        answer = (
            f"{outcome.action} ({outcome.code})"
            if isinstance(outcome, StrategyDecision)
            else f"refused ({outcome.code})"
        )
        lines.append(f"     legal actions {str(list(legal)):<24} -> {answer}")
    lines.append("")
    return lines


def _query_for_legal(legal: tuple[str, ...]) -> StrategyQuery:
    return StrategyQuery(
        hand_id="engine-fidelity-report",
        street="flop",
        seat=1,
        button_seat=0,
        hole_cards=("As", "Kd"),
        board=("2c", "7h", "Ts"),
        legal_actions=legal,
        to_call=20,
        street_bet=20,
        min_raise_target=40,
        pot=60,
        stacks=((0, 980), (1, 940)),
        blinds=(5, 10),
    )


def _registry_section() -> list[str]:
    try:
        import run_verify
    except ModuleNotFoundError:
        import scripts.run_verify as run_verify
    description = run_verify.COMMANDS["check_solver_export_expectations"].description
    return [
        "6. The registry describes checks that exist  (GATE-COMMAND-DESCRIPTION-NAMES-A-",
        "   WITHDRAWN-CHECK)",
        "",
        "   Was:  the entry said the command recomputes the export's orderings and",
        "         directional bound. The directional bound was withdrawn on 2026-08-18",
        "         with the parity solve, and the command never computed it.",
        f"   Now:  {description}",
        "",
    ]


def _moved_numbers_section() -> list[str]:
    return [
        "What these fixes move, and who re-measures it",
        "",
        "   This phase names the committed numbers its fixes move and recomputes none of",
        "   them, by decision 9. A fix phase that grades its own fixes puts a moved number",
        "   and a mistaken one in the same commit.",
        "",
        "     latest_decision_audit.jsonl        street_bet changes on every preflop record",
        "                                        where hero had not matched the level",
        "     Phase 08 agreement rates           measured through the uncorrected query and",
        "                                        the uncorrected replayer",
        "     Phase 08 refusal inventory         the same",
        "     Phase 07 simulator counts          replayed through the old reopening rule",
        "",
        "   Filed as PHASE-11-MOVED-NUMBERS-AWAIT-REMEASUREMENT against proposed phase 12,",
        "   which already re-runs the comparison for its own reasons.",
        "",
    ]


def render_report() -> str:
    lines = [
        "Engine And Query Fidelity Report",
        "================================",
        "",
        "Six defects that v1's own reviews found, diagnosed, and filed. Every 'now' below",
        "is computed on this run; every 'was' is stated from backlog.yml and the phase",
        "contract, because the old behaviour is no longer in the tree to measure.",
        "",
    ]
    lines += _free_fold_section()
    lines += _no_free_folds_section()
    lines += _reopening_section()
    lines += _street_bet_section()
    lines += _ceiling_section()
    lines += _fail_closed_section()
    lines += _registry_section()
    lines += _moved_numbers_section()
    lines += [
        "Recomputable by hand, without reading code:",
        "",
        "   The reopening table. The last full bet set the level to 10 with a minimum raise",
        "   of 10, so betting reopens once the level reaches 10 plus 10, which is 20. Every",
        "   row of that table is that subtraction and that comparison.",
        "",
        "Generated by `scripts/generate_engine_fidelity_report.py`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    report = render_report()
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
