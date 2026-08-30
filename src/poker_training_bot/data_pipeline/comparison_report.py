"""Rendering the real-hand comparison into the two committed reports.

Split from the measurement it renders because they are different jobs with different
failure modes. A wrong number here is a formatting bug; a wrong number there is a
false claim about the chart. Keeping them in one file also pushed it past the repo's
own size cap, which is the cap doing what it is for.

The preamble carries more weight than report preambles usually do. Two properties of
the committed chart explain a large part of what the numbers show before any of them
are read, and a reader who does not know them will draw the opposite conclusion from
the right data.
"""

from __future__ import annotations

from poker_training_bot.data_pipeline.comparison import (
    DISAGREE,
    PRICE_BANDS,
    REPORTED_ACTIONS,
    REPORTED_POSITIONS,
    ComparisonResult,
    Rate,
)

_PREAMBLE = """\
Real-Hand Comparison Report
===========================

Read this before any number below.

This compares the bot's preflop decisions against what real players did in the same
spots, using a committed slice of a public hand corpus that nobody in this repo wrote.
It is a preflop comparison and nothing else. The postflop half of this bot is a
continuity fallback that never bets and never raises, so comparing it against real
postflop play would measure the fallback's known shape rather than these hands.

A disagreement means this chart and this player did different things in this spot. It
does not establish that either is wrong. Real players are not an oracle for strategy
quality, and one of the seats here is a near-equilibrium machine while the others are
people, which is why they are never averaged together.

Agreement means the action the player took carries nonzero weight in the chart's own
distribution, not that it matched the single action the chart happens to draw. A chart
that folds a hand seven times in ten does not disagree with a fold.

A spot the chart could not answer is a refusal. Refusals are reported on their own and
are never counted as disagreements, because a missing chart cell and a wrong chart cell
need different fixes.

Two properties of the chart explain part of what follows before any of it is measured,
and a reader who does not know them will draw the wrong conclusion from the numbers.

The committed ranges are solved rake-free, and these hands were played rake-free, so the
two settings agree on that point and nothing below is explained by it. That is a change
of reading rather than a change of numbers: this report used to tell you the ranges were
solved with a house share taken out of every pot won, and that a solve paying one defends
the blinds more tightly, so a chart folding the big blind more often than these players
did was behaving as designed. The committed solve takes no share, so that explanation is
gone and it was doing real work - where this chart continues less than these players do,
the difference is between the chart and the players and has nothing to excuse it.

The ranges were also solved against one opening size. These players used a smaller one
most of the time, and a cheaper price is a correct reason to continue with more hands.
The report measures that rather than leaving it as a caveat.
"""


def _cell(rate: Rate) -> str:
    """One cell of the position table: agreed over scored, or a dash for no decisions."""
    return f"{rate.numerator}/{rate.denominator}" if rate.denominator else "-"


def render_comparison_report(result: ComparisonResult) -> str:
    lines = [_PREAMBLE, ""]
    lines.append("## Coverage")
    lines.append("")
    lines.append(f"  hands compared                    {result.hands_compared:6d}")
    lines.append(f"  hands excluded, named below       {result.hands_excluded:6d}")
    lines.append(f"  preflop decision points           {len(result.rows):6d}")
    lines.append("")
    lines.append("## Agreement, by population")
    lines.append("")
    lines.append("  Every rate carries the count it was computed over. Refusals are not in")
    lines.append("  the denominator; they are reported beside it.")
    lines.append("")
    for population in result.populations:
        rate = result.agreement(population)
        refused = result.refusal_count(population)
        total = sum(1 for row in result.rows if row.population == population)
        lines.append(f"  {population}")
        lines.append(
            f"    agreed {rate.numerator} of {rate.denominator} scored decisions"
            f"  ({rate.percent:.1f}%)"
        )
        lines.append(f"    refused {refused} of {total} decision points")
        lines.append("")
    lines.append("## The number that matters more than the one above")
    lines.append("")
    lines.append("  Read this before quoting any figure from the previous section.")
    lines.append("")
    lines.append("  Roughly seven in ten preflop decisions in any six-handed sample are folds,")
    lines.append("  and folding a bad hand is the easiest agreement in poker. An unsplit")
    lines.append("  agreement rate is therefore mostly a measurement of how often both sides")
    lines.append("  threw away junk, and it will look high no matter what the chart does with")
    lines.append("  the hands people actually play. Split by what the player did:")
    lines.append("")
    for population in result.populations:
        lines.append(f"  {population}")
        for action in REPORTED_ACTIONS:
            rate = result.agreement_within(population, action=action)
            if not rate.denominator:
                continue
            lines.append(
                f"    player {action:6s} agreed {rate.numerator:5d} of {rate.denominator:5d}"
                f"  ({rate.percent:.1f}%)"
            )
        lines.append("")
    lines.append("  Where those diverge, the low one is the finding. A chart that matches on")
    lines.append("  folds and misses on calls is not 'mostly right'; it is right about the")
    lines.append("  decisions that cost nothing and unproven about the ones that cost chips.")
    lines.append("")
    lines.append("## Which seat the disagreement is in")
    lines.append("")
    lines.append("  A preflop chart is indexed by position before anything else, so a rate")
    lines.append("  without one names a symptom rather than a cell. Each entry below is")
    lines.append("  agreed/scored for that seat, and the last column is how many of that")
    lines.append("  seat's decision points the chart could not answer at all.")
    lines.append("")
    lines.append("  Refusals are outside every rate here, as they are everywhere in this")
    lines.append("  report. They are printed alongside because they are not spread evenly. A")
    lines.append("  seat with many refusals has its rate computed over the subset of its")
    lines.append("  decisions the chart could answer, and that subset is not a random sample")
    lines.append("  of them, so the rate is a narrower claim there than the same number would")
    lines.append("  be in a seat the chart answers everywhere.")
    lines.append("")
    for population in result.populations:
        lines.append(f"  {population}")
        header = "    seat" + "".join(f"{action:>12s}" for action in REPORTED_ACTIONS)
        lines.append(header + f"{'refused':>14s}")
        for position in REPORTED_POSITIONS:
            cells = [
                _cell(result.agreement_within(population, action=action, position=position))
                for action in REPORTED_ACTIONS
            ]
            refused = result.refusal_count(population, position=position)
            points = result.decision_count(population, position=position)
            lines.append(
                f"    {position:<4s}"
                + "".join(f"{cell:>12s}" for cell in cells)
                + f"{f'{refused}/{points}':>14s}"
            )
        lines.append("")
    lines.append("## The price these rates were graded at")
    lines.append("")
    lines.append(f"  The committed chart is {result.chart_source}.")
    for position, amount in result.solved_open_bb:
        lines.append(f"  It solves an open from {position} at {amount:g} big blinds.")
    sizes = result.open_sizes_bb()
    # The price the sample is graded against, taken from the seats the chart actually opens
    # from rather than from a seat named here. This read `.get("LJ")` while all five opening
    # ranges were committed; the cutover retires the lojack's, so the name returned None and
    # the row below formatted it into a size. Earliest actor first, because that is the seat
    # an open in front of hero most often came from, and it is the whole mapping today: the
    # small blind is the one seat with a single opponent behind it and so the one the ruled
    # predicate keeps an opening range for.
    opens = dict(result.solved_open_bb)
    graded = next((opens[seat] for seat in REPORTED_POSITIONS if seat in opens), None)
    if sizes:
        middle = sizes[len(sizes) // 2]
        mean = sum(sizes) / len(sizes)
        lines.append("")
        lines.append(f"  Decisions facing exactly one raise      {len(sizes):6d}")
        lines.append(f"  Median size of that raise, big blinds   {middle:6g}")
        lines.append(f"  Mean size of that raise, big blinds     {mean:6.2f}")
        # No graded row rather than a row graded against nothing: a chart holding no opening
        # range at all has no price the sample can be read against, and printing the count of
        # opens "at or above" a missing number is the shape that put a None in a format string.
        if graded is not None:
            at_least = sum(1 for size in sizes if size >= graded)
            label = f"At or above the solved {graded:g}"
            lines.append(
                f"  {label:<38s}{at_least:6d}  ({100.0 * at_least / len(sizes):.1f}%)"
            )
    lines.append("")
    lines.append("  A smaller open is a better price, and a better price is a correct reason")
    lines.append("  to continue with more hands. So the chart is being asked what to do at a")
    lines.append("  price it was not solved for, and the answer it gives is the answer for a")
    lines.append("  more expensive spot. Split by the price faced:")
    lines.append("")
    for population in result.populations:
        lines.append(f"  {population}")
        for band, _ in PRICE_BANDS:
            rate = result.agreement_within(population, action="call", price_band=band)
            if not rate.denominator:
                continue
            lines.append(
                f"    called facing {band:20s} agreed {rate.numerator:4d} of"
                f" {rate.denominator:4d}  ({rate.percent:.1f}%)"
            )
        lines.append("")
    lines.append("## The sampled-action match rate, which is the lesser number")
    lines.append("")
    lines.append("  Agreement above means the player's action carries nonzero weight in the")
    lines.append("  chart's distribution. This instead asks whether it equalled the single")
    lines.append("  action the chart's seeded draw produced, which on a mixed cell mostly")
    lines.append("  measures the seed. It is reported because a reader who prefers the")
    lines.append("  stricter definition should not have to regenerate anything to get it.")
    lines.append("")
    for population in result.populations:
        rate = result.sampled_action_match(population)
        lines.append(
            f"    {population:10s} matched {rate.numerator} of {rate.denominator} drawn"
            f" decisions  ({rate.percent:.1f}%)"
        )
    lines.append("")
    lines.append("## What a disagreement looked like")
    lines.append("")
    disagreements = [row for row in result.rows if row.verdict == DISAGREE]
    for row in disagreements[:20]:
        vector = ",".join(f"{name}={weight:g}" for name, weight in row.weights)
        lines.append(
            f"  {row.hand_id}  {row.position:<4s} {row.player}"
            f"  {row.hole_cards[0]}{row.hole_cards[1]}"
            f"  played {row.observed_action}  chart [{vector}]"
        )
    if len(disagreements) > 20:
        lines.append(f"  ... and {len(disagreements) - 20} more")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_refusal_inventory(result: ComparisonResult) -> str:
    lines = [
        "Real-Hand Refusal Inventory",
        "===========================",
        "",
        "Every spot below is one the committed charts could not answer while replaying",
        "real hands. Each row names a spot key taken from the refusal's own detail, the",
        "number of decision points that reached it, and whether the self-play run had",
        "already found it. Most-reached first.",
        "",
        "A spot marked new is one only real hands reached, which is a different priority",
        "from one the simulator already surfaces on every run.",
        "",
        "This is a lower bound on the gap, not a census of the charts: it reports only the",
        "spots this committed sample actually reached.",
        "",
        f"  distinct spots  {len(result.refusal_inventory)}",
        "",
        "   points  spot key                                      also in self-play",
    ]
    for entry in result.refusal_inventory:
        marker = "yes" if entry.seen_in_self_play else "NEW"
        lines.append(f"  {entry.count:6d}  {entry.spot_key:<44s}  {marker}")
    return "\n".join(lines) + "\n"
