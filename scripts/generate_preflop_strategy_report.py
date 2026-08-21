"""Human evidence for the preflop strategy: what it covers, and what it refuses.

Written for a reviewer who does not read code. The frequency table is the part that
matters most, because it is the only place in this phase where numbers this repo
produced are set against numbers it did not: the expected column comes from the
source solution's own displayed output. Everything else here can only prove the code
agrees with itself.

The refusal census is the second half of the same idea. An artifact-backed bot is
supposed to decline where its chart is silent, so a report that showed only decisions
would hide the behavior most worth checking.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.poker_core.positions import table_positions  # noqa: E402
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key  # noqa: E402
from poker_training_bot.strategy.contract import (  # noqa: E402
    SeatAction,
    StrategyDecision,
    StrategyQuery,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy  # noqa: E402

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
ARTIFACT = PREFLOP_DIR / "six_max_nl25_100bb.json"
EXPECTATIONS = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"
REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_preflop_strategy_report.txt"

BIG_BLIND = 100
SMALL_BLIND = 50
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3
SAMPLE_HANDS = ("AA", "AKs", "AJo", "76s", "72o")
SAMPLE_SPOTS = (
    "t6/d100/LJ/rfi",
    "t6/d100/BTN/rfi",
    "t6/d100/BB/CO:raise@2.5",
    "t6/d100/LJ/LJ:raise@2.5,CO:raise@8",
)


def seat_of(position: str) -> int:
    from poker_training_bot.poker_core.positions import position_for_seat

    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise ValueError(position)


def refusal_probe(
    label: str, preflop_actions: tuple[SeatAction, ...] = (), **overrides
) -> tuple[str, StrategyQuery]:
    """One probe query, with its chips derived from the actions rather than fixed.

    Since a recorded raise carries the amount it raised to, a probe that states an
    open and a bet level independently can state two different opens. So the level,
    the price to call, the pot, and the stacks are all walked out of the recorded
    actions here, and a probe that wants an unrepresentable pot - a straddle, an ante -
    overrides exactly the field that makes it one.
    """
    hero = seat_of(overrides.pop("hero", "LJ"))
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND}
    level = BIG_BLIND
    min_raise = BIG_BLIND
    for entry in preflop_actions:
        if entry.action == "raise":
            min_raise = max(min_raise, (entry.amount or 0) - level)
            level = entry.amount or level
            committed[entry.seat] = level
        elif entry.action == "call":
            committed[entry.seat] = level
    fields = {
        "hand_id": "probe",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": ("As", "Ks"),
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": level - committed.get(hero, 0),
        "street_bet": level,
        "min_raise_target": level + min_raise,
        "pot": sum(committed.values()),
        "stacks": tuple((seat, 100 * BIG_BLIND - committed.get(seat, 0)) for seat in SEATS),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": preflop_actions,
    }
    fields.update(overrides)
    return label, StrategyQuery(**fields)


def probes() -> list[tuple[str, StrategyQuery]]:
    shallow = tuple((seat, 40 * BIG_BLIND) for seat in SEATS)
    return [
        refusal_probe("covered: lojack opens", hero="LJ"),
        refusal_probe(
            "covered: big blind faces a cutoff open at the solved 2.5bb",
            hero="BB",
            preflop_actions=(SeatAction(seat_of("CO"), "raise", 250),),
        ),
        refusal_probe(
            "covered by substitution: the same open at 2.25bb",
            hero="BB",
            preflop_actions=(SeatAction(seat_of("CO"), "raise", 225),),
        ),
        refusal_probe("uncovered: forty big blinds deep", stacks=shallow),
        refusal_probe("uncovered: straddled pot", street_bet=2 * BIG_BLIND),
        refusal_probe("uncovered: anted pot", pot=SMALL_BLIND + BIG_BLIND + 60),
        refusal_probe(
            "uncovered: squeeze after an open and a cold call",
            hero="BTN",
            preflop_actions=(
                SeatAction(seat_of("LJ"), "raise", 250),
                SeatAction(seat_of("CO"), "call"),
            ),
        ),
        refusal_probe(
            "uncovered but expressible since phase 12: facing a five-bet",
            hero="CO",
            preflop_actions=(
                SeatAction(seat_of("CO"), "raise", 250),
                SeatAction(seat_of("BB"), "raise", 1350),
                SeatAction(seat_of("CO"), "raise", 2150),
                SeatAction(seat_of("BB"), "raise", 5000),
            ),
        ),
        refusal_probe(
            "no legal preflop order produces it: the button raising before the cutoff",
            hero="CO",
            preflop_actions=(SeatAction(seat_of("BTN"), "raise", 250),),
        ),
        refusal_probe("uncovered: postflop", street="flop", board=("2c", "7h", "Ts")),
    ]


DRAWS_PER_HAND = 40


def combos_of(hand: str) -> int:
    if len(hand) == 2:
        return 6
    return 4 if hand.endswith("s") else 12


def realised_pct(strategy: PreflopChartStrategy, spot: str, action: str) -> float:
    """What the strategy itself does at a spot, over a deterministic sample.

    The chart's frequency and the bot's are not the same number, and the gap is
    exactly what a collapse rule can hide. An earlier version of this phase took the
    highest-weight action and over-folded to three-bets by 13 points while this
    table, showing only the chart, said everything was fine.
    """
    taken = 0.0
    total = 0.0
    for hand in strategy.library.hand_classes_for(spot):
        weight = combos_of(hand)
        total += weight
        for index in range(DRAWS_PER_HAND):
            outcome = strategy.decide_spot(spot, hand, seed_suffix=str(index))
            if isinstance(outcome, StrategyDecision) and outcome.action == action:
                taken += weight / DRAWS_PER_HAND
    return 0.0 if total == 0.0 else 100.0 * taken / total


def big_blind_defence_spot(strategy: PreflopChartStrategy, position: str) -> str | None:
    """The committed key for the big blind facing an open from `position`.

    The open's price is read out of the committed keys rather than spelled here, which
    is the same rule the lookup normaliser follows and the reason it matters: this
    solve opens the small blind to 3.5 and everyone else to 2.5, so one constant would
    already be wrong today. A position the artifact holds two opening prices for has no
    single defence spot, and it is skipped rather than guessed at.
    """
    prices = strategy.library.solved_prices_bb(6, 100, "BB", (), position)
    if len(prices) != 1:
        return None
    return spot_key(6, 100, "BB", (PreflopAction(position, "raise", prices[0]),))


def frequency_lines(strategy: PreflopChartStrategy) -> list[str]:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    lines = [
        "## Frequencies against the source solution",
        "",
        "The source column is what GTO Wizard displayed for the same spot. The chart",
        "column is what the committed artifact holds. The bot column is what the",
        "strategy actually does once its mixed cells are drawn, which is a different",
        "number and the one that matters: a collapse rule that distorts the chart shows",
        "up only here.",
        "",
        f"{'Spot':<30}{'chart':>9}{'source':>9}{'bot':>9}{'bot-chart':>11}",
    ]
    for position, expected in sorted(expectations["open_frequency_pct"].items()):
        spot = f"t6/d100/{position}/rfi"
        actual = strategy.library.action_frequency_pct(spot, "raise")
        bot = realised_pct(strategy, spot, "raise")
        lines.append(
            f"{position + ' opens':<30}{actual:>8.2f}%{expected:>8.2f}%{bot:>8.2f}%"
            f"{bot - actual:>+11.2f}"
        )
    for position, expected in sorted(expectations["big_blind_defence_pct"].items()):
        spot = big_blind_defence_spot(strategy, position)
        if spot is None:
            continue
        actual = 100.0 - strategy.library.action_frequency_pct(spot, "fold")
        bot = 100.0 - realised_pct(strategy, spot, "fold")
        lines.append(
            f"{'BB defends vs ' + position:<30}{actual:>8.2f}%{expected:>8.2f}%{bot:>8.2f}%"
            f"{bot - actual:>+11.2f}"
        )
    for position, expected in sorted(expectations.get("limp_frequency_pct", {}).items()):
        spot = f"t6/d100/{position}/rfi"
        actual = strategy.library.action_frequency_pct(spot, "call")
        bot = realised_pct(strategy, spot, "call")
        lines.append(
            f"{position + ' limps':<30}{actual:>8.2f}%{expected:>8.2f}%{bot:>8.2f}%"
            f"{bot - actual:>+11.2f}"
        )
    return lines


def coverage_lines(strategy: PreflopChartStrategy) -> list[str]:
    lines = [
        "## Coverage",
        "",
        "Every seat at a six-handed 100bb table can be asked. That is not the same as",
        "every situation being charted, and the spots below are the ones that are.",
        "",
    ]
    for spot in strategy.library.spot_keys():
        covered = len(strategy.library.hand_classes_for(spot))
        note = "" if covered == 169 else "  (hero has acted, so only hero's own range)"
        lines.append(f"  {spot:<40}{covered:>4} hand classes{note}")
    return lines


def sample_lines(strategy: PreflopChartStrategy) -> list[str]:
    lines = ["## What it does with a few named hands", ""]
    lines.append("A mixed cell is drawn from its weights, so a hand can appear more than")
    lines.append("one way across different hands. The draw below is seeded on the spot.")
    lines.append("")
    for spot in SAMPLE_SPOTS:
        lines.append(f"  {spot}")
        for hand in SAMPLE_HANDS:
            outcome = strategy.decide_spot(spot, hand)
            if isinstance(outcome, StrategyDecision):
                amount = f" to {outcome.amount / BIG_BLIND:g}bb" if outcome.amount else ""
                verdict = f"{outcome.action}{amount}"
            else:
                verdict = f"refuses ({outcome.code})"
            lines.append(f"    {hand:<6}{verdict}")
        lines.append("")
    return lines


def refusal_lines(strategy: PreflopChartStrategy) -> list[str]:
    lines = ["## Refusals", "", "What the bot does where its chart is silent.", ""]
    codes: Counter[str] = Counter()
    for label, query in probes():
        outcome = strategy.decide(query)
        if isinstance(outcome, StrategyDecision):
            verdict = f"decides: {outcome.action}"
        else:
            verdict = f"refuses: {outcome.code}"
            codes[outcome.code] += 1
        lines.append(f"  {label:<52}{verdict}")
    lines += ["", "Refusal codes seen:"]
    for code, count in sorted(codes.items()):
        lines.append(f"  {code:<58}{count}")
    return lines


def spot_check_lines(strategy: PreflopChartStrategy) -> list[str]:
    spot = "t6/d100/BTN/rfi"
    weights = strategy.library.artifacts[0].weights_for(spot, "A2o")
    rendered = ", ".join(f"{name} {weight:.4f}" for name, weight in weights)
    return [
        "## Check one number by hand",
        "",
        "Open data/artifacts/preflop/six_max_nl25_100bb.json, find action_weights ->",
        f'"{spot}" -> "A2o". It reads: {rendered}.',
        "",
        "So the button folds ace-deuce offsuit most of the time. That is a real property",
        "of a raked solution and it disagrees with the hand-authored chart this replaced,",
        "which opened it always. Nothing in this repo computed that number.",
    ]


def render_report() -> str:
    strategy = PreflopChartStrategy.from_repo()
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    header = [
        "Preflop Strategy Report",
        "=======================",
        "",
        f"Artifact: {ARTIFACT.relative_to(REPO_ROOT)}",
        f"Source: {artifact['source']['name']} ({artifact['source']['kind']})",
        f"Table: {artifact['table_size']}-handed, {artifact['stack_depth_bb']}bb,"
        f" positions {', '.join(table_positions(artifact['table_size']))}",
        f"Spots: {artifact['audit_fields']['spot_count']}",
        "",
        "These ranges were solved with NL25 rake. Raked ranges are tighter than",
        "rake-free ones, most visibly in the blinds, so the big blind folds more here",
        "than a rake-free chart would have it fold.",
        "",
    ]
    sections = [
        frequency_lines(strategy),
        coverage_lines(strategy),
        sample_lines(strategy),
        refusal_lines(strategy),
        spot_check_lines(strategy),
    ]
    body: list[str] = []
    for section in sections:
        body.extend(section)
        body.append("")
    footer = ["Generated by `scripts/generate_preflop_strategy_report.py`.", ""]
    return "\n".join(header + body + footer)


def main() -> int:
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(render_report(), encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
