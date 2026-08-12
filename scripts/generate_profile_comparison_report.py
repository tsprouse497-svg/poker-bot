"""Human evidence for the offline simulator, written for a reviewer who does not read code.

The report is organised around what it is *not* allowed to say, because that is the part a
reader will otherwise supply for themselves. Phase 06's fallback never bets and never
raises, so in self-play every postflop street checks through: a hand this bot plays is
decided preflop and then settled at showdown. Every figure below is therefore a preflop
figure with showdown resolution, and the first section says so before any number appears.

Two runs, because they do different jobs. The self-play run seats six copies of one
strategy, which has zero expectation against itself by symmetry, so it proves the
machinery rather than measuring quality: chips conserved every hand, every hand terminal,
the replayer agreeing about every decision point, and net chips across the table at
exactly zero. The floor run seats the chart bot against five copies of the reference
check-fold strategy and produces one directional number, which must come out positive or
something is broken. It is a floor check and it is labelled as one; ranking the bot
against a real opponent needs an opponent with a strategy, which this repo does not have.

Refusal coverage is printed as a headline rather than a footnote. A profile that refuses a
fifth of its hands has been measured over four fifths of them, and the reader has to know
that before reading anything else. The refusal codes are printed too, because "the chart
does not cover this spot" is the coverage signal Phases 04 through 06 were built to
produce and it is the most actionable number in the file.
"""

from __future__ import annotations

import sys
from collections import Counter

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.hand_history.replay import replay_hand
from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.profiles.seating import FLOOR, SELF_PLAY, seat_profiles
from poker_training_bot.simulator.run import (
    REFUSED,
    REQUIRED_DEPTH_BB,
    REQUIRED_SEATS,
    SimulationConfig,
    SimulationResult,
    run_simulation,
)

REPORT_OUTPUT = REPO_ROOT / "reports" / "active" / "latest_profile_comparison_report.txt"

# Stated rather than tuned. The coverage criterion needs at least one full orbit; the
# directional figure needs enough hands for its own standard error to be small beside it;
# and the gate has to stay something a person will wait for. Six hundred hands is a
# hundred orbits and runs in about a fifth of a second, so all three are satisfied at once
# and none of them is trading against another.
SEED = 20260812
HANDS = 600
SMALL_BLIND = 50
BIG_BLIND = 100
STARTING_STACK = REQUIRED_DEPTH_BB * BIG_BLIND

WRAP = 88

# The position vocabulary comes from the poker core rather than from a list here, so a
# column heading and the label a decision was made under cannot drift apart.
_POSITIONS = table_positions(REQUIRED_SEATS)


def wrapped(text: str, indent: str = "") -> list[str]:
    from textwrap import fill

    return fill(
        " ".join(text.split()),
        width=WRAP,
        initial_indent=indent,
        subsequent_indent=indent,
        break_long_words=False,
        break_on_hyphens=False,
    ).splitlines()


def simulate(kind: str) -> SimulationResult:
    return run_simulation(
        SimulationConfig(
            seed=SEED,
            hands=HANDS,
            profiles=seat_profiles(kind, REQUIRED_SEATS),
            starting_stack=STARTING_STACK,
            blinds=(SMALL_BLIND, BIG_BLIND),
        )
    )


def header_lines() -> list[str]:
    return [
        "Profile Comparison Report",
        "=========================",
        "",
        f"Seed: {SEED}    Hands per run: {HANDS}    Table: {REQUIRED_SEATS}-handed"
        f" at {REQUIRED_DEPTH_BB}bb    Blinds: {SMALL_BLIND}/{BIG_BLIND}",
        "",
        "## What these numbers measure, and what they do not",
        "",
        *wrapped(
            "Read this before any figure below. The postflop half of this bot is a continuity"
            " fallback that never bets and never raises, so when it plays against another copy"
            " of itself every postflop street checks through. A hand is decided preflop by the"
            " committed solver charts and then settled at showdown."
        ),
        "",
        *wrapped(
            "So every number in this file is a preflop number with showdown resolution. None"
            " of them says anything about postflop play, because there is no postflop play here"
            " to measure. A figure that looks like a river statistic is still a preflop"
            " statistic that happened to be resolved on a river."
        ),
        "",
        *wrapped(
            "Stacks reset to exactly"
            f" {REQUIRED_DEPTH_BB}bb before every hand, so each hand is an independent sample of"
            " the same spot and the figures are chips per hand rather than a running stack."
            " Nothing here models a session, a bankroll, or short-stack play, and no hand can"
            " show the bot busting or doubling through. That is not a simplification for"
            " convenience: the committed chart answers one flat depth and refuses any other, so"
            " a run that carried stacks would put every hand after the first into the refusal"
            " path."
        ),
        "",
        *wrapped(
            "Every hand is reproducible on its own. The run is a pure function of its seed, its"
            " seating and its profiles, and each hand carries the seed that produced it, so any"
            " figure a reader disputes can be regenerated rather than argued about."
        ),
    ]


def coverage_lines(result: SimulationResult, title: str) -> list[str]:
    refused = result.hands_dealt() - result.hands_counted()
    share = 100.0 * refused / result.hands_dealt() if result.hands_dealt() else 0.0
    lines = [
        f"### Coverage: {title}",
        "",
        f"  hands dealt                          {result.hands_dealt():>8}",
        f"  hands measured                       {result.hands_counted():>8}",
        f"  hands refused                        {refused:>8}   {share:5.1f}%",
        "",
    ]
    if refused:
        lines += wrapped(
            "A refused hand is one where the committed chart had no answer for the spot it"
            " reached. The hand is voided rather than guessed at: stacks are restored, no chips"
            " move, and it is excluded from the chips-per-hand figures below and counted here"
            " instead. That is the coverage signal, and it is the most actionable number in this"
            " file - it is a list of spots the charts do not yet hold."
        )
        lines += ["", "  refusals by reason:"]
        for code, count in sorted(result.refusal_codes().items()):
            lines.append(f"    {code:<52}{count:>6}")
        lines.append("")
        lines += wrapped(
            f"So this run measured the strategy over {result.hands_counted()} of"
            f" {result.hands_dealt()} hands. Whatever the figures below say, they say it about"
            " that subset."
        )
    else:
        lines += wrapped(
            "No hand was refused, so every hand dealt was measured. That is not the chart"
            " being more complete than it is: an opponent that folds to everything keeps the"
            " betting tree shallow, so the deeper spots the chart does not cover are never"
            " reached."
        )
    return lines


def figures_lines(result: SimulationResult, title: str) -> list[str]:
    lines = [
        f"### Chips per hand: {title}",
        "",
        f"{'profile':<46}{'seats':>6}{'total':>10}{'per hand':>10}{'std err':>10}",
    ]
    for name in result.profile_names():
        seats = sum(1 for seated in result.seat_names if seated == name)
        per_hand = result.chips_per_hand(name)
        total = per_hand * result.hands_counted()
        lines.append(
            f"{name:<46}{seats:>6}{total:>10.0f}{per_hand:>10.2f}"
            f"{result.standard_error(name):>10.2f}"
        )
    lines += [
        "",
        *wrapped(
            "A profile's figure sums every seat it occupies, because a comparison is between"
            " strategies rather than between chairs. `std err` is the run's own variation in"
            " that figure, so a reader can see whether a difference is a difference."
        ),
        "",
    ]
    separated = result.separated_profiles()
    if separated:
        lines += wrapped(
            "Clears its own noise by more than two standard errors, best first:"
            f" {', '.join(separated)}."
        )
    else:
        lines += wrapped(
            "Nothing here clears its own noise, so this run names no winner. That is the"
            " correct answer for a table of identical strategies: they have zero expectation"
            " against each other by symmetry, and a run that reported a winner would be"
            " reporting variance."
        )
    return lines


def self_play_lines(result: SimulationResult) -> list[str]:
    net = sum(
        sum(hand.stack_deltas.values()) for hand in result.hands if hand.outcome != REFUSED
    )
    outcomes = Counter(hand.outcome for hand in result.hands)
    replayed = sum(
        1
        for hand in result.hands
        if hand.outcome != REFUSED and replay_hand(hand.normalized) is not None
    )
    return [
        "## The self-play run: what it proves rather than what it measures",
        "",
        *wrapped(
            f"{REQUIRED_SEATS} copies of the same strategy at one table. They have zero"
            " expectation against each other, so this run measures no strategy quality at all."
            " It is here because symmetry gives a known expected answer to check the machinery"
            " against, which a run between different profiles cannot do."
        ),
        "",
        f"  net chips across the table            {net:>8}   (must be exactly 0)",
        f"  hands reaching a showdown            {outcomes['showdown']:>8}",
        f"  hands won uncontested                {outcomes['uncontested']:>8}",
        f"  hands refused                        {outcomes[REFUSED]:>8}",
        f"  hands re-derived by the replayer     {replayed:>8}",
        "",
        *wrapped(
            "The last line is the cross-check that matters most. Every dealt hand is written"
            " out in the Phase 02 normalized schema as it is played, then handed back to the"
            " Phase 02 replayer, which re-derives the whole hand from that record and compares"
            " its own settlement against the recorded result. Without it the simulator and the"
            " replayer would be two independent stories about the same rules, with nothing"
            " forcing them to agree."
        ),
        "",
        *wrapped(
            "Chips are also checked per hand rather than over the run. An aggregate that nets"
            " to zero can hide two errors that cancel each other out, so the books have to"
            " balance for every single hand, and a hand whose books do not balance stops the"
            " run rather than being averaged away."
        ),
        "",
        *coverage_lines(result, "six copies of the chart bot"),
        "",
        *figures_lines(result, "six copies of the chart bot"),
    ]


def floor_lines(result: SimulationResult) -> list[str]:
    return [
        "## The floor run: one directional number, and its limits",
        "",
        *wrapped(
            "The chart bot in one seat against five copies of the reference check-fold"
            " strategy, which folds to any bet and checks whenever it can. That is a floor"
            " that is deliberately bad and already trusted, so the number below is a floor"
            " check: the chart-driven bot must beat a bot that folds everything, and if it does"
            " not, something is broken."
        ),
        "",
        *wrapped(
            "What it is not: a ranking against a real opponent, or a measurement of how good"
            " the chart's ranges are. Against opponents who fold every hand preflop, the chart"
            " bot mostly collects blinds, so this figure is closer to how often the chart opens"
            " than to how well it opens. Producing the other kind of number needs an opponent"
            " with a strategy, and this repo does not have one yet."
        ),
        "",
        *coverage_lines(result, "chart bot against five check-fold seats"),
        "",
        *figures_lines(result, "chart bot against five check-fold seats"),
    ]


def position_lines(result: SimulationResult) -> list[str]:
    lines = [
        "## Position coverage, and the number to check by hand",
        "",
        *wrapped(
            "The button advances one seat per hand and the profiles stay in their seats, so"
            " over any multiple of the table size every seat has played every position an"
            " equal number of times. That is what makes a chips-per-hand figure a property of"
            " a strategy rather than of where it happened to be sitting."
        ),
        "",
        f"{'seat':<8}" + "".join(f"{position:>6}" for position in _POSITIONS),
    ]
    for seat in sorted(result.position_counts):
        counts = result.position_counts[seat]
        lines.append(
            f"{seat:<8}"
            + "".join(f"{counts[position]:>6}" for position in _POSITIONS)
        )
    lines += [
        "",
        "### Check this number by hand",
        "",
        *wrapped(
            f"The run deals {HANDS} hands at a {REQUIRED_SEATS}-handed table and the button"
            f" moves one seat every hand. So each seat should hold each position exactly"
            f" {HANDS} / {REQUIRED_SEATS} = {HANDS // REQUIRED_SEATS} times, and every cell in"
            " the table above should read that number. Divide the hand count in this report's"
            " own header by six and compare. No code required, and if any cell disagrees the"
            " rotation is broken and every per-profile figure in this file is contaminated by"
            " seat position."
        ),
        "",
        *wrapped(
            "A second check, on the normalization rather than the rotation: in the floor table"
            " above, multiply a profile's per-hand figure by the measured hand count and it"
            " reproduces that profile's total, and the two profiles' totals sum to zero. Chips"
            " do not appear or vanish at this table; they only change seats."
        ),
    ]
    return lines


def render() -> str:
    self_play = simulate(SELF_PLAY)
    floor = simulate(FLOOR)
    sections = [
        header_lines(),
        self_play_lines(self_play),
        floor_lines(floor),
        position_lines(floor),
    ]
    body: list[str] = []
    for section in sections:
        body.extend(section)
        body.append("")
    body.append("Generated by `scripts/generate_profile_comparison_report.py`.")
    return "\n".join(body) + "\n"


def main() -> int:
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUTPUT.write_text(render(), encoding="utf-8")
    print(f"wrote {REPORT_OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
