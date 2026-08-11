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
    "t6/d100/BB/CO:raise",
    "t6/d100/LJ/LJ:raise,CO:raise",
)


def seat_of(position: str) -> int:
    from poker_training_bot.poker_core.positions import position_for_seat

    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise ValueError(position)


def refusal_probe(label: str, **overrides) -> tuple[str, StrategyQuery]:
    hero = seat_of(overrides.pop("hero", "LJ"))
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND}
    fields = {
        "hand_id": "probe",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": ("As", "Ks"),
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        "to_call": BIG_BLIND,
        "street_bet": BIG_BLIND,
        "min_raise_target": 2 * BIG_BLIND,
        "pot": SMALL_BLIND + BIG_BLIND,
        "stacks": tuple((seat, 100 * BIG_BLIND - committed.get(seat, 0)) for seat in SEATS),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": (),
    }
    fields.update(overrides)
    return label, StrategyQuery(**fields)


def probes() -> list[tuple[str, StrategyQuery]]:
    shallow = tuple((seat, 40 * BIG_BLIND) for seat in SEATS)
    return [
        refusal_probe("covered: lojack opens", hero="LJ"),
        refusal_probe("covered: big blind faces a cutoff open",
                      hero="BB",
                      preflop_actions=(SeatAction(seat_of("CO"), "raise"),)),
        refusal_probe("uncovered: forty big blinds deep", stacks=shallow),
        refusal_probe("uncovered: straddled pot", street_bet=2 * BIG_BLIND),
        refusal_probe("uncovered: anted pot", pot=SMALL_BLIND + BIG_BLIND + 60),
        refusal_probe(
            "uncovered: squeeze after an open and a cold call",
            hero="BTN",
            preflop_actions=(
                SeatAction(seat_of("LJ"), "raise"),
                SeatAction(seat_of("CO"), "call"),
            ),
        ),
        refusal_probe(
            "uncovered: facing a four-bet",
            hero="CO",
            preflop_actions=(
                SeatAction(seat_of("CO"), "raise"),
                SeatAction(seat_of("BB"), "raise"),
                SeatAction(seat_of("CO"), "raise"),
                SeatAction(seat_of("BB"), "raise"),
            ),
        ),
        refusal_probe("uncovered: postflop", street="flop", board=("2c", "7h", "Ts")),
    ]


def frequency_lines(strategy: PreflopChartStrategy) -> list[str]:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    lines = [
        "## Frequencies against the source solution",
        "",
        "The expected column is what GTO Wizard displayed for the same spot. It is the",
        "only column here this repo did not compute, so a range that is uniformly wrong",
        "shows up as a gap rather than as agreement.",
        "",
        f"{'Spot':<34}{'this chart':>12}{'source':>10}{'delta':>8}",
    ]
    for position, expected in sorted(expectations["open_frequency_pct"].items()):
        spot = f"t6/d100/{position}/rfi"
        actual = strategy.library.action_frequency_pct(spot, "raise")
        lines.append(
            f"{position + ' opens':<34}{actual:>11.2f}%{expected:>9.2f}%{actual - expected:>+8.2f}"
        )
    for position, expected in sorted(expectations["big_blind_defence_pct"].items()):
        spot = f"t6/d100/BB/{position}:raise"
        actual = 100.0 - strategy.library.action_frequency_pct(spot, "fold")
        lines.append(
            f"{'BB defends vs ' + position:<34}{actual:>11.2f}%{expected:>9.2f}%"
            f"{actual - expected:>+8.2f}"
        )
    for position, expected in sorted(expectations.get("limp_frequency_pct", {}).items()):
        spot = f"t6/d100/{position}/rfi"
        actual = strategy.library.action_frequency_pct(spot, "call")
        lines.append(
            f"{position + ' limps':<34}{actual:>11.2f}%{expected:>9.2f}%{actual - expected:>+8.2f}"
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
