"""The numbers this repo repeats across documents, and the code that recomputes them.

A fact here is a property of committed data stated in the present tense: how many hands
the sample holds, how many contain an all-in, what opening size the chart was solved
for. It is deliberately not a record of a past run. "The gate was green across 33
commands" is a historical claim about the day a phase closed, and registering it would
demand rewriting history every time the gate grows.

Each fact carries the pattern that finds it in prose. Searching for the bare value would
match any number in the file; matching a sentence shape means a rewritten sentence stops
matching, which the checker treats as an error rather than a silent pass.

`quoted_in` names live documents only, never a completed phase's audit packet. Taylor
ruled on 2026-08-20 that a packet is a snapshot of what that phase found and believed,
and the check is a two-way trap: a stale value fails, and a sentence rewritten past the
pattern also fails. So a packet listed here can only ever be made to pass by restating a
number a later phase moved, which every phase contract forbids for the good reason that
rewriting a packet destroys the only evidence a number ever changed. That is the same
line the paragraph above draws about a fact's *content*, applied to its *location*: a
present-tense property of committed data does not belong to a dated document.

Three facts had that packet as their only quoter, and none is retired: a fact must be
quoted somewhere, which `tests/test_quality_hardening.py` asserts and which is right,
because a fact nobody states is a fact nobody can get wrong. They point at
`docs/CORPUS_COMPARISON_LIMITS.md` instead, which MAINT-10 wrote to be the live home for
exactly these caveats and which now states all three in its own prose.
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

LIMITS = "docs/CORPUS_COMPARISON_LIMITS.md"
BACKLOG = "backlog.yml"
DECISIONS = "reports/phase_audits/decisions/PHASE_08_SAMPLE_COMPARISON_DECISIONS.md"


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


def _human_call_disagreements(position: str | None = None) -> str:
    """Human call decisions the chart disagrees with, optionally in one seat.

    Registered because "70 of the 104" stood in four documents while the humans-only
    figure was 58 of 89. The wrong number was a pooled one carrying a humans label,
    which is the one operation the phase's own judgment call forbids, and no gate could
    see it because it was prose.
    """
    from poker_training_bot.data_pipeline.comparison import DISAGREE

    _, result = _comparison()
    return str(
        sum(
            1
            for row in result.rows
            if row.population == "humans"
            and row.observed_action == "call"
            and row.verdict == DISAGREE
            and (position is None or row.position == position)
        )
    )


def _human_call_disagreements_big_blind() -> str:
    return _human_call_disagreements("BB")


def _solved_open_bb() -> str:
    """The price the committed chart is solved to open to, read off the chart's own keys.

    Three things this cannot be. Not a constant: the value would have to be rewritten by
    hand every time a chart is replaced, which is the whole defect this module exists for.
    Not a spelled spot key: the cutover's selection predicate leaves one opening range, so
    `t6/d100/LJ/rfi` names a spot that no longer exists. And not `amount_bb`, because the
    sizing table is per hand class since decision 6 was re-cut and that accessor answers
    None wherever a class is offered more than one price - which the surviving opening range
    is, every class there being offered the solved raise and the all-in.

    So the named price is taken directly: every price the opening ranges offer, minus the
    all-in, which is hero's whole stack rather than a size the solve chose. Exactly one has
    to be left. Two would mean the chart opens to two sizes and this fact does not exist as
    a single number, which is a finding rather than something to average. It raises rather
    than defaulting, because a default is how a stale number survives a chart replacement
    with nobody reading it.
    """
    from poker_training_bot.strategy.preflop_chart import PreflopChartStrategy

    strategy = PreflopChartStrategy.from_repo()
    opening = [key for key in strategy.library.spot_keys() if key.endswith("/rfi")]
    if not opening:
        raise ValueError(
            "the committed chart holds no opening range, so it states no solved opening"
            " price; this fact describes a chart that opens from at least one seat"
        )
    depth = min(artifact.stack_depth_bb for artifact in strategy.library.artifacts)
    named = {
        price
        for spot in opening
        for hand_class_text in strategy.library.hand_classes_for(spot)
        for price, _ in strategy.sizing.sizes_bb(spot, hand_class_text) or ()
        if price < depth
    }
    if len(named) != 1:
        raise ValueError(
            f"the committed opening ranges {sorted(opening)} are priced at {sorted(named)}"
            " below the all-in, and this fact is one solved opening price"
        )
    return f"{named.pop():g}"


FACTS: tuple[Fact, ...] = (
    Fact(
        name="corpus_committed_hands",
        description="hands in the committed public-corpus sample",
        compute=_committed_hands,
        pattern=r"(?:all|from) (\d+) hands",
        quoted_in=(LIMITS,),
    ),
    Fact(
        name="corpus_excluded_hands",
        description="selected hands excluded by name",
        compute=_excluded_hands,
        pattern=r"`corpus_exclusions\.json` names (\d+) hand",
        quoted_in=(LIMITS,),
    ),
    Fact(
        name="corpus_all_in_hands",
        description="committed hands where a seat commits its whole stack",
        compute=_all_in_hands,
        pattern=r"(\d+) of the 499 (?:committed )?hands contain\s+an all-in",
        quoted_in=(LIMITS,),
    ),
    Fact(
        name="corpus_preflop_decisions",
        description="preflop decision points the comparison scores or refuses",
        compute=_preflop_decisions,
        # The first lookbehind skips "roughly 3,000 preflop decision points", which is
        # an approximation the decision record makes on purpose: a check that fails on a
        # sentence saying roughly is a check that is wrong, not a document that is. The
        # second one stops the match starting mid-number - without it the engine
        # backtracks to "000", where the text before it is a comma rather than the word
        # the first lookbehind is watching for, and the skip silently stops working.
        pattern=r"(?<!roughly )(?<![\d,])(\d[\d,]*) preflop decisions?(?: points)?",
        quoted_in=(LIMITS, DECISIONS),
    ),
    Fact(
        name="corpus_refusals",
        description="decision points the chart could not answer",
        compute=_refusals,
        # The thousands separator is inside the capture on purpose. The chart cutover took
        # this fact from three digits to four, and this repo writes a four-digit count as
        # 2,529; a bare `\d+` would capture "529" out of that and read as drift.
        pattern=r"(\d[\d,]*) refusals, outside every agreement denominator",
        quoted_in=(LIMITS,),
    ),
    Fact(
        name="corpus_distinct_refused_spots",
        description="distinct spot keys the chart refuses against real hands",
        compute=_distinct_refused_spots,
        pattern=r"\*\*(\d+) distinct spots the chart",
        quoted_in=(LIMITS,),
    ),
    Fact(
        name="corpus_inexpressible_refusals",
        description="refusals whose spot the chart vocabulary cannot express at all",
        compute=_inexpressible_refusals,
        pattern=r"(\d+) refusals (?:that name no spot at all|across the committed sample)",
        quoted_in=(BACKLOG,),
    ),
    Fact(
        name="corpus_human_call_disagreements",
        description="scored human call decisions the chart disagrees with",
        compute=_human_call_disagreements,
        pattern=r"holds \d+ of the (\d+) human call",
        quoted_in=(BACKLOG,),
    ),
    Fact(
        name="corpus_human_call_disagreements_big_blind",
        description="of those, the ones taken from the big blind",
        compute=_human_call_disagreements_big_blind,
        pattern=r"holds (\d+) of the \d+ human call",
        quoted_in=(BACKLOG,),
    ),
    Fact(
        name="chart_solved_open_bb",
        description="the opening size the committed chart was solved against",
        compute=_solved_open_bb,
        pattern=r"solved against a ([\d.]+) big blind open",
        quoted_in=(LIMITS,),
    ),
)


def computed_values() -> dict[str, str]:
    return {fact.name: fact.compute() for fact in FACTS}
