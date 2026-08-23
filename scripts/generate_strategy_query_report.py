from __future__ import annotations

import sys

from repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.hand_history import load_hand_history_file
from poker_training_bot.hand_history.replay import DecisionPoint, replay_hand
from poker_training_bot.poker_core.cards import card_texts
from poker_training_bot.strategy.contract import (
    DECISION_AUDIT_SCHEMA_VERSION,
    DecisionAuditRecord,
    SeatAction,
    SeatState,
    StrategyDecision,
    StrategyQuery,
    records_to_jsonl,
)
from poker_training_bot.strategy.reference import CheckFoldStrategy

FIXTURE = REPO_ROOT / "data" / "samples" / "normalized_hands.json"
AUDIT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_decision_audit.jsonl"
REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_strategy_query_report.txt"


def preflop_history(points: list[DecisionPoint], index: int) -> tuple[SeatAction, ...]:
    """The preflop actions in front of this decision point.

    Passing nothing is not neutral: an empty history is the positive claim that the action
    folded to hero, so a decision facing a raise used to carry a query saying its pot was
    unopened. Nothing downstream of this command reads it - the reference strategy checks and
    folds, and no chart is consulted - so no count in this report moves. The audit lines it
    writes are committed evidence, though, and a query that misdescribes the pot it came from
    is evidence of the wrong thing.

    A preflop point sees only what came before it. A postflop point sees the whole preflop
    orbit, which is the real context: a chart derives a spot key from it, and a query carrying
    a truncated one is a different query than the hand produced. Blind posts are forced rather
    than chosen, so the replayer never offers them as decision points and `SeatAction` has no
    name for them. A raise carries the amount it raised to, which is what `HistoryAction`
    holds for a raise and for nothing else.
    """
    earlier = points[:index] if points[index].street.value == "preflop" else points
    return tuple(
        SeatAction(
            point.seat,
            point.action.kind.value,
            point.action.amount if point.action.kind.value == "raise" else None,
        )
        for point in earlier
        if point.street.value == "preflop"
    )


def build_query(
    point: DecisionPoint, hole_cards: tuple[str, str], history: tuple[SeatAction, ...] = ()
) -> StrategyQuery:
    """Build the query for one recorded decision point.

    `current_bet` is the street's current bet level, not hero's own contribution to it.
    This generator passed the contribution until Phase 11, which is
    `STREET-BET-MEANING-AMBIGUOUS`. Hero's own contribution is now carried on hero's seat
    record and read from there rather than worked back out of the level and the price,
    which the cap on `to_call` made impossible to do correctly.

    Every per-seat figure comes off the replayer's own `PlayerState` under the engine's
    four names, and `pot` is the sum of those hand totals rather than a second number
    stated beside them.
    """
    state = point.turn.round
    player = state.player(point.seat)
    seated = sorted(state.players, key=lambda entry: entry.seat)
    return StrategyQuery(
        hand_id=point.hand.hand_id,
        street=point.street.value,
        seat=point.seat,
        button_seat=point.hand.button_seat,
        hole_cards=hole_cards,
        board=tuple(card_texts(point.board)),
        legal_actions=tuple(kind.value for kind in point.legal_actions),
        to_call=min(max(0, state.current_bet - player.street_bet), player.stack),
        current_bet=state.current_bet,
        min_raise_target=state.current_bet + state.min_raise,
        pot=sum(entry.committed_total for entry in seated),
        stacks=tuple((entry.seat, entry.stack) for entry in seated),
        seat_states=tuple(
            SeatState(
                seat=entry.seat,
                street_bet=entry.street_bet,
                committed_total=entry.committed_total,
                folded=entry.folded,
                all_in=entry.all_in,
            )
            for entry in seated
        ),
        blinds=(point.hand.blinds.small_blind, point.hand.blinds.big_blind),
        preflop_actions=history,
    )


def render_reports() -> tuple[str, str]:
    strategy = CheckFoldStrategy()
    records: list[DecisionAuditRecord] = []
    lines = [
        "Strategy Query Report",
        "=====================",
        "",
        f"Fixture: `{FIXTURE.relative_to(REPO_ROOT)}`",
        f"Strategy: {strategy.strategy_id} v{strategy.strategy_version}",
        "",
    ]
    totals = {"points": 0, "queried": 0, "skipped": 0, "refusals": 0, "agreements": 0}
    for hand in load_hand_history_file(FIXTURE):
        points: list[DecisionPoint] = []
        replay_hand(hand, on_decision=points.append)
        hole_cards = {
            entry.seat: tuple(card_texts(entry.hole_cards)) for entry in hand.showdown
        }
        queried = skipped = refusals = agreements = 0
        for index, point in enumerate(points):
            if point.seat not in hole_cards:
                skipped += 1
                continue
            query = build_query(point, hole_cards[point.seat], preflop_history(points, index))
            outcome = strategy.decide(query)
            records.append(
                DecisionAuditRecord(
                    schema_version=DECISION_AUDIT_SCHEMA_VERSION,
                    strategy_id=strategy.strategy_id,
                    strategy_version=strategy.strategy_version,
                    query=query,
                    outcome=outcome,
                )
            )
            queried += 1
            if isinstance(outcome, StrategyDecision):
                if outcome.action == point.action.kind.value:
                    agreements += 1
            else:
                refusals += 1
        totals["points"] += len(points)
        totals["queried"] += queried
        totals["skipped"] += skipped
        totals["refusals"] += refusals
        totals["agreements"] += agreements
        lines.extend(
            [
                f"## {hand.hand_id}",
                "",
                f"Decision points: {len(points)}",
                f"Queried: {queried}",
                f"Skipped (no recorded hole cards): {skipped}",
                f"Refusals: {refusals}",
                f"Reference strategy agreed with the recorded action: {agreements}",
                "",
            ]
        )
    lines.extend(
        [
            "## Totals",
            "",
            f"Decision points: {totals['points']}",
            f"Queried: {totals['queried']}",
            f"Skipped (no recorded hole cards): {totals['skipped']}",
            f"Refusals: {totals['refusals']}",
            f"Agreements: {totals['agreements']}",
            f"Audit records written: {len(records)}",
            "",
            "Generated by `scripts/generate_strategy_query_report.py`.",
        ]
    )
    return "\n".join(lines) + "\n", records_to_jsonl(records)


def main() -> int:
    report_text, audit_jsonl = render_reports()
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(report_text, encoding="utf-8")
    AUDIT_OUTPUT.write_text(audit_jsonl, encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    print(f"wrote {AUDIT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
