"""The numbers this repo repeats across documents, and the code that recomputes them.

A fact here is a property of committed data stated in the present tense: how many hands
the sample holds, how many contain an all-in, what opening size the chart was solved
for. It is deliberately not a record of a past run. "The gate was green across 33
commands" is a historical claim about the day a phase closed, and registering it would
demand rewriting history every time the gate grows.

Each fact carries the pattern that finds it in prose. Searching for the bare value would
match any number in the file; matching a sentence shape means a rewritten sentence stops
matching, which the checker treats as an error rather than a silent pass.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

PACKET = "reports/phase_audits/PHASE_08_SAMPLE_COMPARISON.md"
LIMITS = "docs/CORPUS_COMPARISON_LIMITS.md"
BACKLOG = "backlog.yml"


@dataclass(frozen=True)
class Fact:
    """One number, where it is quoted, and how to find it in the prose.

    `pattern` carries exactly one capture group. Captured values are compared with
    thousands separators stripped, so one fact covers both `3048` and `3,048`.
    """

    name: str
    description: str
    compute: Callable[[], str]
    pattern: str
    quoted_in: tuple[str, ...]


@lru_cache(maxsize=1)
def _comparison():
    """The committed sample and its comparison, computed once per process.

    Imported here rather than at module scope so that reading the fact list does not
    require the package, and so the two callers that only want names stay cheap.
    """
    from poker_training_bot.data_pipeline.comparison import compare_committed_sample
    from poker_training_bot.data_pipeline.sample import load_committed_sample

    sample = load_committed_sample()
    return sample, compare_committed_sample(sample)


def _committed_hands() -> str:
    sample, _ = _comparison()
    return str(len(sample.records))


def _excluded_hands() -> str:
    sample, _ = _comparison()
    return str(len(sample.exclusions))


def _all_in_hands() -> str:
    """Hands where a seat commits its whole starting stack.

    Every seat starts each hand on the same stack here, so committing all of it is the
    only thing an all-in can be. Three documents once said 7, which counted preflop
    shoves of a full stack and missed both the all-in reached on a later street and the
    caller facing one. That defect is why this file exists.
    """
    from poker_training_bot.hand_history.replay import replay_hand

    sample, _ = _comparison()
    return str(
        sum(
            1
            for record in sample.records
            if any(
                replay_hand(record.normalized).committed_by_seat[player.seat]
                == player.starting_stack
                for player in record.normalized.players
            )
        )
    )


def _preflop_decisions() -> str:
    _, result = _comparison()
    return str(len(result.rows))


def _refusals() -> str:
    _, result = _comparison()
    return str(sum(result.refusal_count(population) for population in result.populations))


def _distinct_refused_spots() -> str:
    _, result = _comparison()
    return str(len(result.refusal_inventory))


def _inexpressible_refusals() -> str:
    _, result = _comparison()
    return str(
        sum(entry.count for entry in result.refusal_inventory if entry.spot_key.startswith("("))
    )


def _solved_open_bb() -> str:
    from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy

    return f"{PreflopChartStrategy.from_repo().sizing.amount_bb('t6/d100/LJ/rfi'):g}"


FACTS: tuple[Fact, ...] = (
    Fact(
        name="corpus_committed_hands",
        description="hands in the committed public-corpus sample",
        compute=_committed_hands,
        pattern=r"(?:all|from) (\d+) hands",
        quoted_in=(PACKET, LIMITS),
    ),
    Fact(
        name="corpus_excluded_hands",
        description="selected hands excluded by name",
        compute=_excluded_hands,
        pattern=r"`corpus_exclusions\.json` names (\d+) hand",
        quoted_in=(PACKET,),
    ),
    Fact(
        name="corpus_all_in_hands",
        description="committed hands where a seat commits its whole stack",
        compute=_all_in_hands,
        pattern=r"(\d+) of the 499 (?:committed )?hands contain\s+an all-in",
        quoted_in=(PACKET, LIMITS),
    ),
    Fact(
        name="corpus_preflop_decisions",
        description="preflop decision points the comparison scores or refuses",
        compute=_preflop_decisions,
        pattern=r"([\d,]+) preflop decisions",
        quoted_in=(PACKET, LIMITS),
    ),
    Fact(
        name="corpus_refusals",
        description="decision points the chart could not answer",
        compute=_refusals,
        pattern=r"(\d+) refusals, outside every agreement denominator",
        quoted_in=(PACKET,),
    ),
    Fact(
        name="corpus_distinct_refused_spots",
        description="distinct spot keys the chart refuses against real hands",
        compute=_distinct_refused_spots,
        pattern=r"\*\*(\d+) distinct spots the chart",
        quoted_in=(PACKET,),
    ),
    Fact(
        name="corpus_inexpressible_refusals",
        description="refusals whose spot the chart vocabulary cannot express at all",
        compute=_inexpressible_refusals,
        pattern=r"(\d+) refusals (?:that name no spot at all|across the committed sample)",
        quoted_in=(PACKET, BACKLOG),
    ),
    Fact(
        name="chart_solved_open_bb",
        description="the opening size the committed chart was solved against",
        compute=_solved_open_bb,
        pattern=r"solved against a ([\d.]+) big blind open",
        quoted_in=(PACKET, LIMITS),
    ),
)


def computed_values() -> dict[str, str]:
    return {fact.name: fact.compute() for fact in FACTS}
