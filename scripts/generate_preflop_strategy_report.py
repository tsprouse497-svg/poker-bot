"""Human evidence for the preflop strategy: what it covers, and what it refuses.

Written for a reviewer who does not read code. The frequency table is the part that
matters most, because it is the only place in this phase where numbers this repo
produced are set against numbers it did not: the reference column is a GTO Wizard
solution's own displayed output. Everything else here can only prove the code agrees
with itself.

That column is a cross-solve reference rather than an expectation, and it says so where
it is printed. The committed ranges came from a raked GTO Wizard solve until the chart
cutover and come from a rake-free GTOpen solve after it, while the reference file stays
the retired source's on purpose - a reference regenerated from what it checks cannot
fail. So it is printed beside this chart for a reader and gates on nothing.

The refusal census is the second half of the same idea. An artifact-backed bot is
supposed to decline where its chart is silent, so a report that showed only decisions
would hide the behavior most worth checking. It matters more after the cutover than
before: the committed chart holds one opening range where the retired one held five, and
the four seats that lost theirs now refuse rather than folding.

No spot key and no chart filename is spelled here. Every spot this report works through
is read out of the committed artifact, because each of the four ways the cutover broke
this command was a constant naming something the artifact stopped holding.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.poker_core.positions import table_positions  # noqa: E402
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key  # noqa: E402
from poker_training_bot.strategy.contract import (  # noqa: E402
    SeatAction,
    SeatState,
    StrategyDecision,
    StrategyQuery,
)
from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy  # noqa: E402

PREFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
EXPECTATIONS = PREFLOP_DIR / "expectations" / "six_max_nl25_100bb.json"
REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_preflop_strategy_report.txt"

BIG_BLIND = 100
SMALL_BLIND = 50
SEATS = (0, 1, 2, 3, 4, 5)
BUTTON = 3
# What every seat sits down with, in big blinds, unless a probe asks for another depth.
FULL_DEPTH_BB = 100
# The seat that posts the straddle probe's forced two big blinds, and the size of it. A
# straddle is a forced post: it lifts the level the way a blind does, and no recorded
# action explains the chips, which is what makes the pot describe a straddled table.
STRADDLE_SEAT_POSITION = "LJ"
STRADDLE_BB = 2
# The ante probe's per-seat ante. Dead money: it goes into the pot and buys nothing off
# the price, so it lives in each seat's hand total and never in its street figure.
ANTE = 10
SAMPLE_HANDS = ("AA", "AKs", "AJo", "76s", "72o")
# The hand the "check one number by hand" section works through. Its cell has to be one a
# reader can look up in the file, so it is checked against the spot's declared classes and
# the section says which hand it used rather than assuming this one is there.
HAND_CHECK_CLASS = "A2o"


class PreflopStrategyReportError(RuntimeError):
    """A section that cannot be written honestly, raised rather than published.

    The alternative this file shipped with was worse than a crash: a spelled spot key the
    artifact stopped declaring read back as an empty range, and the report published a
    0.00 percent opening frequency, which states that hero folds everything where the truth
    is that nothing was ever solved there.
    """


def committed_chart_path() -> Path:
    """The one committed chart, found rather than named.

    The retired chart's filename was spelled in three places in this file and the cutover
    deleted the file, so the constant is gone. One artifact is a rule the report depends on
    everywhere else too: the frequency table, the coverage census and the hand check all
    describe a single solve, and two loaded charts would silently interleave two.
    """
    charts = sorted(path for path in PREFLOP_DIR.glob("*.json"))
    if len(charts) != 1:
        raise PreflopStrategyReportError(
            f"this report is written against one committed chart, found {len(charts)} in"
            f" {PREFLOP_DIR.relative_to(REPO_ROOT)}: {[path.name for path in charts]}"
        )
    return charts[0]


def hero_and_actions(spot: str) -> tuple[str, tuple[str, ...]]:
    """A spot key split into hero's position and the actions recorded before it.

    `t6/d100/BB/BTN:raise@2.5` is the big blind with one action behind it; `rfi` is the
    empty sequence and not an action named "rfi".
    """
    _, _, hero, tail = spot.split("/")
    return hero, () if tail == "rfi" else tuple(tail.split(","))


def _spot_sort_key(spot: str) -> tuple[int, int, str]:
    """Shortest line first, then lines with no all-in in them, then alphabetical.

    The all-in term is what keeps this section on a spot worth reading. Every raising point
    in this tree offers an all-in alongside its named raise, and a key facing one offers
    hero fold and call and nothing else, so a plain alphabetical pick lands on the spot
    where there is least to see - `@100` sorts below `@2.5` character by character.
    """
    _, actions = hero_and_actions(spot)
    prices = [float(entry.split("@")[1]) for entry in actions if "@" in entry]
    return (len(actions), sum(1 for price in prices if price >= FULL_DEPTH_BB), spot)


def _first_spot(candidates: list[str], description: str) -> str:
    """The simplest key of a family, or a loud failure if the family is empty.

    Ordered rather than picked, so the report is byte-comparable between runs.
    """
    if not candidates:
        raise PreflopStrategyReportError(
            f"the committed chart declares no spot that is {description}, so this report"
            " cannot show one; it has changed shape rather than moved"
        )
    return min(candidates, key=_spot_sort_key)


def sample_spots(strategy: PreflopChartStrategy) -> tuple[str, ...]:
    """Three committed keys: an opening range, a defence, and a spot behind hero's own raise.

    The three families are what this section was written to show, and they are found in the
    committed keys rather than spelled. Spelled, they were `t6/d100/LJ/rfi`,
    `t6/d100/BTN/rfi` and `t6/d100/LJ/LJ:raise@2.5,CO:raise@8`, all three of which the
    cutover retired: the chart it committed opens from one seat and prices three-bets at
    7.5 rather than 8.
    """
    declared = strategy.library.spot_keys()
    opening: list[str] = []
    defence: list[str] = []
    behind_own_raise: list[str] = []
    for spot in declared:
        hero, actions = hero_and_actions(spot)
        actors = [entry.split(":")[0] for entry in actions]
        if not actions:
            opening.append(spot)
        elif len(actions) == 1 and ":raise" in actions[0]:
            defence.append(spot)
        if hero in actors:
            behind_own_raise.append(spot)
    return (
        _first_spot(opening, "an opening range"),
        _first_spot(defence, "hero facing a single open"),
        _first_spot(behind_own_raise, "hero acting again behind a raise of hero's own"),
    )


def seat_of(position: str) -> int:
    from poker_training_bot.poker_core.positions import position_for_seat

    for seat in SEATS:
        if position_for_seat(SEATS, BUTTON, seat) == position:
            return seat
    raise ValueError(position)


def refusal_probe(
    label: str,
    preflop_actions: tuple[SeatAction, ...] = (),
    *,
    straddle: bool = False,
    ante: int = 0,
    depth_bb: int = FULL_DEPTH_BB,
    **overrides,
) -> tuple[str, StrategyQuery]:
    """One probe query, with its chips derived from the forced posts and the actions.

    Since a recorded raise carries the amount it raised to, a probe that states an
    open and a bet level independently can state two different opens. So the level,
    the price to call, the pot, the per-seat records and the stacks are all walked out of
    the forced posts and the recorded actions here. A probe that wants a table the chart
    cannot describe asks for the forced money or the depth that makes it one, rather than
    overriding a single number and leaving the rest of the table disagreeing with it.

    A straddle is a forced post by a seat that never acted for it, so it lifts the level
    the way a blind does and nothing in the history explains the chips. An ante is dead
    money: it is in the pot and it buys nothing off the price, so it sits in each seat's
    hand total and never in its street figure. Putting it in the street figure would make
    an anted seat owe less to call than an unanted one at the same level.
    """
    hero = seat_of(overrides.pop("hero", "LJ"))
    committed = {seat_of("SB"): SMALL_BLIND, seat_of("BB"): BIG_BLIND}
    level = BIG_BLIND
    min_raise = BIG_BLIND
    if straddle:
        committed[seat_of(STRADDLE_SEAT_POSITION)] = STRADDLE_BB * BIG_BLIND
        level = max(level, STRADDLE_BB * BIG_BLIND)
    folded: set[int] = set()
    for entry in preflop_actions:
        if entry.action == "raise":
            # The engine holds the minimum raise at the largest raise made on the street
            # so far, and at one big blind until something raises. `min_raise_target`
            # below is the level plus that, which is the engine's own derivation:
            # computing it any other way makes the strategy report a straddle the table
            # does not hold, because a disagreement with the predicted minimum is exactly
            # the signal that catches a straddler who has already called to the level.
            min_raise = max(min_raise, (entry.amount or 0) - level)
            level = entry.amount or level
            committed[entry.seat] = level
        elif entry.action == "call":
            committed[entry.seat] = level
        elif entry.action == "fold":
            folded.add(entry.seat)
    sat_down = depth_bb * BIG_BLIND
    hero_stack = sat_down - committed.get(hero, 0) - ante
    fields = {
        "hand_id": "probe",
        "street": "preflop",
        "seat": hero,
        "button_seat": BUTTON,
        "hole_cards": ("As", "Ks"),
        "board": (),
        "legal_actions": ("fold", "call", "raise"),
        # The price hero can actually pay, capped at what hero holds.
        "to_call": min(level - committed.get(hero, 0), hero_stack),
        "current_bet": level,
        "min_raise_target": level + min_raise,
        "pot": sum(committed.values()) + ante * len(SEATS),
        "stacks": tuple(
            (seat, sat_down - committed.get(seat, 0) - ante) for seat in SEATS
        ),
        "seat_states": tuple(
            SeatState(
                seat=seat,
                street_bet=committed.get(seat, 0),
                committed_total=committed.get(seat, 0) + ante,
                folded=seat in folded,
                # No probe seats an all-in player: every seat sits down at least forty big
                # blinds deep and the largest recorded raise leaves chips behind it. Stated
                # rather than read off a zero stack, which cannot tell a seat that is
                # all-in from one that sat down with nothing.
                all_in=False,
            )
            for seat in SEATS
        ),
        "blinds": (SMALL_BLIND, BIG_BLIND),
        "preflop_actions": preflop_actions,
    }
    fields.update(overrides)
    return label, StrategyQuery(**fields)


def probes() -> list[tuple[str, StrategyQuery]]:
    """The tables and lines this section asks about, each described rather than graded.

    The labels used to carry a `covered:` or `uncovered:` prefix, which is a claim about
    the answer standing next to the answer. The cutover made four of those prefixes wrong
    in one commit - the lojack open they called covered is the headline thing the ruled
    predicate gives up - and a label disagreeing with the verdict beside it is worse than
    no label. So each probe now says what table it is, and the verdict column says what the
    bot did with it. The list spans both halves on purpose: lines the committed chart holds
    a cell for, and tables and lines it does not.
    """
    return [
        # The one opening range the committed chart holds, and one it gave up. Both are
        # printed because the difference between them is what the cutover cost in play.
        refusal_probe("the small blind opens", hero="SB"),
        refusal_probe("the lojack opens", hero="LJ"),
        refusal_probe(
            "the big blind faces a cutoff open at the solved 2.5bb",
            hero="BB",
            preflop_actions=(SeatAction(seat_of("CO"), "raise", 250),),
        ),
        refusal_probe(
            "the same open at 2.25bb, a price the tree does not hold",
            hero="BB",
            preflop_actions=(SeatAction(seat_of("CO"), "raise", 225),),
        ),
        # A whole table forty big blinds deep, so the depth is what the chart is missing.
        # Overriding the stacks alone would leave the two blinds having sat down deeper
        # than everybody else, and the refusal would be about the ragged table instead.
        refusal_probe("a table forty big blinds deep", depth_bb=40),
        # The lojack posts two big blinds it never acted for, and hero is behind it.
        refusal_probe("a straddled pot", hero="HJ", straddle=True),
        refusal_probe("an anted pot", ante=ANTE),
        refusal_probe(
            "a squeeze after an open and a cold call",
            hero="BTN",
            preflop_actions=(
                SeatAction(seat_of("LJ"), "raise", 250),
                SeatAction(seat_of("CO"), "call"),
            ),
        ),
        # Expressible only since the key carried sizes and allowed a seat to act twice, and
        # covered only since the cutover committed the heads-up continuations.
        refusal_probe(
            "the cutoff facing a five-bet",
            hero="CO",
            preflop_actions=(
                SeatAction(seat_of("CO"), "raise", 250),
                SeatAction(seat_of("BB"), "raise", 1350),
                SeatAction(seat_of("CO"), "raise", 2150),
                SeatAction(seat_of("BB"), "raise", 5000),
            ),
        ),
        # No legal preflop order produces this, so it is unrepresentable rather than
        # uncovered: the action passes the cutoff before it reaches the button.
        refusal_probe(
            "the button raising before the cutoff",
            hero="CO",
            preflop_actions=(SeatAction(seat_of("BTN"), "raise", 250),),
        ),
        refusal_probe("a flop", street="flop", board=("2c", "7h", "Ts")),
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


def named_open_price_bb(strategy: PreflopChartStrategy, position: str) -> float | None:
    """The price `position` is solved to open to, read out of the committed keys.

    A jam is priced at hero's whole stack rather than at a size the solve chose, so the
    all-in branch is dropped before the count. Left in, every opening point offers two
    prices and this would answer None at every seat. What remains has to be a single price:
    two solved open sizes at one seat means the defence has two cells and no one row of the
    frequency table describes it, so it is skipped rather than guessed at.
    """
    offered = strategy.library.solved_prices_bb(6, FULL_DEPTH_BB, "BB", (), position)
    named = sorted({price for price in offered if price < FULL_DEPTH_BB})
    return named[0] if len(named) == 1 else None


def big_blind_defence_spot(strategy: PreflopChartStrategy, position: str) -> str | None:
    """The committed key for the big blind facing an open from `position`."""
    price = named_open_price_bb(strategy, position)
    if price is None:
        return None
    return spot_key(
        6, FULL_DEPTH_BB, "BB", (PreflopAction(position, "raise", price),)
    )


def _frequency_row(label: str, chart: float, reference: float, bot: float) -> str:
    return (
        f"{label:<30}{chart:>8.2f}%{reference:>8.2f}%{bot:>8.2f}%{bot - chart:>+11.2f}"
    )


def frequency_lines(strategy: PreflopChartStrategy) -> list[str]:
    """The frequency table, over the opening ranges and defences the chart actually holds.

    An absent range is named in prose and never given a row. It used to get one, and the
    row read 0.00 percent, which is a different and much stronger claim than the truth: a
    chart that opens nothing folds every hand from that seat, where a chart with no cell
    there refuses and the bot never acts on it at all. The cutover turned four of the five
    opening rows into exactly that, and no test in the tree would have said a word.
    """
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    declared = set(strategy.library.spot_keys())
    lines = [
        "## Frequencies against the GTO Wizard reference",
        "",
        "The ref column is what GTO Wizard displayed for the same spot in the raked NL25",
        "solution the retired chart came from. It is a cross-solve reference and not an",
        "expectation: these ranges are a rake-free GTOpen solve, the two disagree by",
        "construction, and nothing gates on the gap. The file is left unrewritten because",
        "a reference regenerated from what it checks cannot fail.",
        "",
        "The chart column is what the committed artifact holds. The bot column is what the",
        "strategy actually does once its mixed cells are drawn, which is a different",
        "number and the one that matters: a collapse rule that distorts the chart shows",
        "up only here.",
        "",
        f"{'Spot':<30}{'chart':>9}{'ref':>9}{'bot':>9}{'bot-chart':>11}",
    ]
    absent_openings: list[str] = []
    for position, reference in sorted(expectations["open_frequency_pct"].items()):
        spot = f"t6/d100/{position}/rfi"
        if spot not in declared:
            absent_openings.append(position)
            continue
        chart = strategy.library.action_frequency_pct(spot, "raise")
        lines.append(
            _frequency_row(
                f"{position} opens", chart, reference, realised_pct(strategy, spot, "raise")
            )
        )
    for position, reference in sorted(expectations["big_blind_defence_pct"].items()):
        spot = big_blind_defence_spot(strategy, position)
        if spot is None:
            continue
        chart = 100.0 - strategy.library.action_frequency_pct(spot, "fold")
        bot = 100.0 - realised_pct(strategy, spot, "fold")
        lines.append(_frequency_row(f"BB defends vs {position}", chart, reference, bot))
    limps_shown = False
    for position, reference in sorted(expectations.get("limp_frequency_pct", {}).items()):
        spot = f"t6/d100/{position}/rfi"
        if spot not in declared:
            continue
        chart = strategy.library.action_frequency_pct(spot, "call")
        bot = realised_pct(strategy, spot, "call")
        lines.append(_frequency_row(f"{position} limps", chart, reference, bot))
        limps_shown = True
    if absent_openings:
        lines += [
            "",
            "The reference holds an opening frequency for four seats this chart holds no",
            f"opening range for at all: {', '.join(absent_openings)}. They have no row here.",
            "A 0.00 percent row would say the solve opens nothing from them, which is a",
            "claim about a range; the truth is that there is no range, and the bot refuses",
            "rather than folding. The ruled selection predicate is what dropped them: it",
            "keeps a spot only where the source prices every terminal below it, and an open",
            "with four seats still to act can end multiway.",
        ]
    if limps_shown:
        lines += [
            "",
            "The limp row is the one place a 0.00 percent chart figure is the real answer",
            "rather than an absent cell. The reference's small blind limps; this solve was",
            "run with limping switched off, so the spot is committed, hero is offered no",
            "call there, and the frequency is zero because of the configuration rather than",
            "because of a range.",
        ]
    return lines


def coverage_lines(strategy: PreflopChartStrategy) -> list[str]:
    declared = strategy.library.spot_keys()
    openings = [spot for spot in declared if not hero_and_actions(spot)[1]]
    lines = [
        "## Coverage",
        "",
        "Every seat at a six-handed 100bb table can be asked. That is not the same as",
        "every situation being charted, and the spots below are the ones that are.",
        "",
        f"{len(declared)} spots, and the seats holding an opening range are"
        f" {', '.join(hero_and_actions(spot)[0] for spot in openings) or 'none'}.",
        "Every other seat refuses a pot that is folded to it, which is the largest single",
        "thing this chart does not do.",
        "",
    ]
    for spot in declared:
        covered = len(strategy.library.hand_classes_for(spot))
        note = "" if covered == 169 else "  (hero has acted, so only hero's own range)"
        lines.append(f"  {spot:<40}{covered:>4} hand classes{note}")
    return lines


def sample_lines(strategy: PreflopChartStrategy, spots: tuple[str, ...]) -> list[str]:
    lines = ["## What it does with a few named hands", ""]
    lines.append("A mixed cell is drawn from its weights, so a hand can appear more than")
    lines.append("one way across different hands. The draw below is seeded on the spot.")
    lines.append("")
    lines.append("Three spots, found in the committed keys rather than named here: an")
    lines.append("opening range, hero facing a single open, and hero acting again behind a")
    lines.append("raise of hero's own. A spot offering hero two prices is drawn between them")
    lines.append("with the same seed that draws between a cell's actions, so the amount below")
    lines.append("is one of the solve's own prices and never an average of them.")
    lines.append("")
    for spot in spots:
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
    lines = [
        "## Refusals",
        "",
        "What the bot does where its chart is silent. Each row names a table or a line and",
        "the verdict is what the bot did with it; the labels claim nothing about coverage,",
        "because a label that grades the answer beside it goes wrong the moment the chart",
        "changes and reads as a defect in the bot rather than in the label.",
        "",
    ]
    codes: Counter[str] = Counter()
    for label, query in probes():
        outcome = strategy.decide(query)
        if isinstance(outcome, StrategyDecision):
            verdict = f"decides: {outcome.action}"
        else:
            verdict = f"refuses: {outcome.code}"
            codes[outcome.code] += 1
        lines.append(f"  {label:<58}{verdict}")
    lines += ["", "Refusal codes seen:"]
    for code, count in sorted(codes.items()):
        lines.append(f"  {code:<58}{count}")
    return lines


def spot_check_lines(
    strategy: PreflopChartStrategy, spots: tuple[str, ...], chart_path: Path
) -> list[str]:
    """One cell a reader can look up in the committed file with no code.

    Both halves of it are read rather than stated. The spot is the one the sample section
    found, and the sentence underneath names the action the cell weights highest rather than
    asserting a direction, so it cannot go stale against a re-derived chart the way the
    retired version did - that one named a button opening range the cutover deleted and a
    filename it deleted with it.
    """
    spot = spots[1]
    classes = strategy.library.hand_classes_for(spot)
    if not classes:
        raise PreflopStrategyReportError(f"{spot} declares no hand class to check")
    hand = HAND_CHECK_CLASS if HAND_CHECK_CLASS in classes else classes[0]
    weights = strategy.library.artifacts[0].weights_for(spot, hand)
    if not weights:
        raise PreflopStrategyReportError(f"{spot} carries no weights for {hand}")
    rendered = ", ".join(f"{name} {weight:.4f}" for name, weight in weights)
    leading, share = max(weights, key=lambda pair: (pair[1], pair[0]))
    hero, _ = hero_and_actions(spot)
    return [
        "## Check one number by hand",
        "",
        f"Open {chart_path.relative_to(REPO_ROOT)}, find action_weights ->",
        f'"{spot}" -> "{hand}". It reads: {rendered}.',
        "",
        f"So the {hero} {leading}s {hand} {100.0 * share:.2f} percent of the time there.",
        "Nothing in this repo computed that number: it is the weight the solve gave that",
        "action at that node, carried through the conversion unchanged. The chart it",
        "replaced was a raked solution and answered this cell differently, which is the",
        "cutover rather than a defect in either file.",
    ]


def render_report() -> str:
    strategy = PreflopChartStrategy.from_repo()
    chart_path = committed_chart_path()
    artifact = json.loads(chart_path.read_text(encoding="utf-8"))
    spots = sample_spots(strategy)
    header = [
        "Preflop Strategy Report",
        "=======================",
        "",
        f"Artifact: {chart_path.relative_to(REPO_ROOT)}",
        f"Source: {artifact['source']['name']} ({artifact['source']['kind']})",
        f"Table: {artifact['table_size']}-handed, {artifact['stack_depth_bb']}bb,"
        f" positions {', '.join(table_positions(artifact['table_size']))}",
        f"Spots: {artifact['audit_fields']['spot_count']}",
        "",
        "These ranges are rake-free, so they are wider than the raked chart they replaced,",
        "most visibly in the blinds: a raked solution gives up a share of every pot it wins",
        "and defends the blinds more tightly for it. What they are not is wider in coverage.",
        "The selection predicate keeps only the spots the source prices every terminal",
        "below, which leaves one opening range and the big blind's defences, so this chart",
        "answers far fewer questions than the retired one and refuses the rest.",
        "",
    ]
    sections = [
        frequency_lines(strategy),
        coverage_lines(strategy),
        sample_lines(strategy, spots),
        refusal_lines(strategy),
        spot_check_lines(strategy, spots, chart_path),
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
