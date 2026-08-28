"""Phase 08: what the two committed reports are allowed to put in front of a reader.

Split from the measurement tests because these check a different kind of claim. A
number being right and a reader being led to the right conclusion by it are separate
properties, and this phase has already been wrong about the second while right about
the first more than once.
"""

from __future__ import annotations

import re

import pytest

from poker_training_bot.data_pipeline.comparison import (
    AGREE,
    DISAGREE,
    REFUSED,
    compare_committed_sample,
)
from poker_training_bot.data_pipeline.comparison_report import (
    render_comparison_report,
    render_refusal_inventory,
)
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

# The one opening range the cutover commits. The lojack's, which this file used to read
# the solved price out of, is one of the fourteen spots the predicate retires.
SB_OPEN = "t6/d100/SB/rfi"


@pytest.fixture(scope="module")
def sample():
    return load_committed_sample()


@pytest.fixture(scope="module")
def comparison(sample):
    return compare_committed_sample(sample)


def solved_open_bb() -> float:
    """The price the one committed opening range comes in at, read through `sizes_bb`.

    Not through `amount_bb`. The small blind's open offers two prices - the 2.5 open and
    the 100bb jam - and decision 6's table answers None at every spot offering more than
    one, so `amount_bb` can name no price here at all. Which price the *bot* opens to was
    ruled on 2026-08-26: the strategy draws it from these same entries with the seed it
    already collapses a mixed cell with. That is hero's own action, and it is not the
    number this report grades against. The graded number is the price the solved tree
    assumes an open arrives at, which is the entry below the stack: a jam is a stack
    rather than a solved bet size, which is what the committed sizing card has always
    said in its own notes.

    Gathered across the 169 hand classes, because the 2026-08-26 ruling put the entry under
    the class: `sizes_bb` takes a spot and a class, and no single class can be asked on the
    whole spot's behalf. Aces are the case that proves it - at `t6/d100/SB/rfi` they carry
    the 2.5 alone, since the jam is 1.0317e-05 of the spot's aggression and only six classes
    carry any of it, so asking any one class would report a menu the spot does not have.
    Every class's named price is the same 2.5 and that is asserted rather than assumed: the
    set is pinned, not its first member.

    Cross-checked against `RULED_CONFIG`, so the number is the config decision 2 froze
    rather than one this file remembered.
    """
    sizing = PreflopSizingTable.from_repo()

    # Asked for rather than called into, so a table that has not grown the accessor yet
    # fails as the assertion it is instead of as an AttributeError halfway down.
    assert hasattr(sizing, "sizes_bb"), "the sizing table must offer sizes_bb(spot_key, class)"
    priced = {
        hand_class_text: sizing.sizes_bb(SB_OPEN, hand_class_text)
        for hand_class_text in HAND_CLASSES
    }

    assert any(entries for entries in priced.values()), f"{SB_OPEN} is the one opening range"
    named = sorted(
        {
            to_bb
            for entries in priced.values()
            for to_bb, _ in entries or ()
            if to_bb < float(RULED_CONFIG["stack"])
        }
    )
    assert named == [pytest.approx(RULED_CONFIG["open_raises"][0])]
    return named[0]


def test_the_sample_was_played_at_a_price_the_chart_was_not_solved_for(comparison) -> None:
    """The caveat that turns out to be most of the finding, measured rather than said.

    The committed solve opens to 2.5 big blinds. These players mostly opened smaller,
    and a cheaper price is a correct reason to continue with more hands, so a chart
    answering at 2.5 is answering a more expensive question than the one it was asked.

    The lojack's row is gone. This read `solved_open_bb["LJ"]` while all five opening
    ranges were committed; the cutover refuses `t6/d100/LJ/rfi` outright, because four
    opponents are still live behind an under-the-gun open, so there is no lojack size to
    read and the subscript raised `KeyError`. The claim survives at the seat that still
    opens, which is the ruled cost paid rather than worked around.

    Absence is asserted with presence, because `"LJ" not in` is true of the empty mapping
    and the empty mapping is the way this actually breaks: `comparison.py` builds the pair
    with `amount_bb`, which answers None at every spot offering two prices, so after the
    cutover the one surviving seat drops out too and the price section below formats a
    None. The whole mapping is pinned - one seat, at the price the tree opens to.
    """
    solved = solved_open_bb()
    sizes = comparison.open_sizes_bb()
    below = [size for size in sizes if size < solved]

    assert dict(comparison.solved_open_bb) == pytest.approx({"SB": solved})
    assert len(below) > len(sizes) / 2

    cheap = comparison.agreement_within("humans", action="call", price_band="at or under 2.25bb")
    dear = comparison.agreement_within("humans", action="call", price_band="over 2.50bb")
    assert cheap.denominator > 50
    assert dear.denominator > 10
    assert cheap.percent < dear.percent - 10.0


def test_every_price_banded_decision_the_chart_answers_is_a_blind_defence(comparison) -> None:
    """Who the split above is a rate about, after the cutover, said rather than implied.

    A band is only assigned to a decision facing exactly one raise, and of the 86 committed
    keys exactly ten hold one raise: the big blind against each of the five openers, at 2.5
    and at 100. Every other seat facing a single open still has players behind it, fails the
    subtree clause, and refuses - the cutoff and the button facing a lojack open among them.
    Counted by a walk over the committed export rather than taken from prose.

    So the cheap-versus-dear rates are blind defence and nothing else, and a reader who
    takes them for a rate about the whole table is reading the retired chart's number. The
    other seats keep their banded decisions; what changes is that they are all refusals, and
    that is asserted here rather than left to be inferred from an absence.
    """
    banded = [row for row in comparison.rows if row.price_band is not None]
    scored = [row for row in banded if row.verdict in {AGREE, DISAGREE}]
    elsewhere = [row for row in banded if row.position != "BB"]

    assert scored, "no banded decision was scored at all"
    assert {row.position for row in scored} == {"BB"}
    assert elsewhere and all(row.verdict == REFUSED for row in elsewhere)


def test_the_price_section_names_the_only_seat_the_chart_still_opens_from(comparison) -> None:
    """The graded price has to come from a seat the chart holds, or the section is a lie.

    The section reads its solved size out of the lojack by name and then formats it
    unconditionally, so with `t6/d100/LJ/rfi` retired it puts `None` into a format string
    and the whole report raises before a reader sees any of it. The seat is the small blind
    now, and it is the only one.

    Which of the small blind's two prices was ruled on 2026-08-26, and the answer is not
    the one this section publishes. The bot's own opening price is drawn per hand from
    `sizes_bb` with the strategy's existing seed; this section grades the sample against
    the price the solved tree assumes an *opponent's* open came in at, which is the number
    both price-band boundaries are drawn from and the number every committed spot key
    facing a single open is written at. So the report publishes the price the chart
    offers, and it cannot publish a drawn one: a seeded draw differs hand to hand and
    there is no hand here to seed it with.

    Both places the number appears are asserted, and the count is recomputed against it.
    The line hero reads first names the seat and the price; the line under it grades the
    sample, and today it grades against `dict(...).get("LJ")` - a report that names 2.5
    and then counts against something else reads right and is wrong.
    """
    section = render_comparison_report(comparison).split("## The price these rates")[1]
    section = section.split("\n## ")[0]
    solved = solved_open_bb()
    graded = f"{solved:g}"
    at_least = sum(1 for size in comparison.open_sizes_bb() if size >= solved)

    assert "SB" in section
    assert "LJ" not in section
    assert re.search(rf"from SB at {re.escape(graded)} big blinds", section), section
    assert re.search(rf"solved {re.escape(graded)}\D+{at_least}\D", section), section


def test_the_report_says_the_chart_is_rake_free_like_the_corpus(comparison) -> None:
    """The caveat the cutover retires, and the reason the old form could not notice.

    This used to require the opposite claim: that a raked solution defends the blinds more
    tightly than a rake-free one, so a chart folding the big blind more than these players
    did was behaving as designed. The committed solve is rake-free - `RULED_CONFIG` posts
    `rake_pct` and `rake_cap` at 0.0, and the contract says in terms that this "removes one
    of phase 08's explanations for the calling gap" - so the caveat is now false, and a
    reader who believes it credits the chart with a defence it has no reason to make.

    The old assertions could not see any of that, and this is the shape rather than an
    accident: `"rake" in preamble` and `"rake" in chart_source` are both satisfied by the
    substring inside "rake-free". Measured, the post-cutover source name is
    `GTOpen 6-max 100bb rake-free` and the preamble as it stands already contains the words
    "rake-free" in the sentence that draws the contrast, so tightening the substring alone
    would fix nothing either. What is asserted instead is the provenance the artifact
    carries, printed into the report verbatim so the reader takes the rake from the solve
    rather than from prose, plus the absence of the sentence the cutover falsifies.
    """
    text = render_comparison_report(comparison)
    preamble = text.split("## Coverage")[0].lower()

    # The premise, read off the config decision 2 froze rather than remembered here.
    assert (float(RULED_CONFIG["rake_pct"]), float(RULED_CONFIG["rake_cap"])) == (0.0, 0.0)
    assert "rake-free" in comparison.chart_source.lower()
    assert comparison.chart_source in text
    assert "rake-free" in preamble
    # Not the one sentence today's preamble happens to use: a negative assertion pinned to a
    # wording is satisfied by the same claim rephrased. Every "rake"/"raked" in the preamble
    # must belong to "rake-free", so a caveat telling the reader the ranges are raked fails
    # however it is worded.
    assert not re.search(r"\brakes?\b|\braked\b", preamble.replace("rake-free", "")), preamble


def test_the_sampled_action_match_rate_is_reported_as_judgment_call_5_ruled(
    comparison,
) -> None:
    """Ruled to be reported alongside, and it was not, for two maintenance tasks.

    It is the lesser number - on a mixed cell a single draw against a single observed
    action mostly measures the seed - but the ruling said both would be there, and the
    fallback the ruling offered a disagreeing reader was that both are in the report.

    The equality between the two denominators is gone, and its own docstring named why
    before it happened: "a spot whose weights are readable but whose raise size is not
    committed would give no draw". Decision 6 holds every price a spot offers, and 21 of
    the 86 committed spots offer two - a named raise and the 100bb jam - counted by a walk
    over the committed export. `amount_bb` answers None at every one of those 21, and the
    2026-08-26 ruling is that the strategy stops asking it there: having decided to raise
    it draws the price from `sizes_bb` with the seed it already collapses a mixed cell
    with. So a multi-price spot yields an action like any other and is no longer a reason
    for a scored decision to come back undrawn.

    What is left is the legality guard: a charted raise the table refuses in front of hero
    because it does not clear the minimum. That can only happen where the lookup moved the
    price it was asked about, since over a price the tree itself solved the next raise up is
    always legal - 7.5 over 2.5, 22.5 over 7.5, 100 over 22.5 - and a jam is capped at hero's
    stack and legal by construction. So the gap is named rather than tolerated: every undrawn
    decision carries a substitution.

    That bound alone guards nothing, and saying so is the point of the two below it.
    `stranded` is a subset of `undrawn`, and `undrawn` is empty on both sides of the
    cutover - 456 of 456 Pluribus decisions and 2,302 of 2,302 human ones draw against the
    committed chart, 72 of 72 and 447 of 447 against a walked 86-spot one - so `not
    stranded` is empty by construction and a build that stranded a third of the graded
    population would pass it silently. The floor is what the round-4 rewrite dropped when it
    dropped `drawn == denominator`: nine in ten scored decisions must come back drawn. A
    sizing table answering None at the 21 spots that offer two prices leaves every
    substituted row undrawn, 157 of 456 and 812 of 2,302, and fails it by a wide margin.

    `exact` is floored for the same reason and in the other direction. Non-emptiness would
    be satisfied by one unsubstituted decision in the whole sample, and a normaliser that
    moved every price it touched is a real defect this is the only test positioned to see.
    One in five is well under both measurements - 299 of 456 and 1,490 of 2,302 today, 23 of
    72 and 165 of 447 after the cutover, which is where the exact share falls to a third
    because the sample's cheap opens no longer meet a chart holding five opening ranges.
    """
    text = render_comparison_report(comparison)
    assert "sampled-action match rate" in text.lower()

    for population in comparison.populations:
        sampled = comparison.sampled_action_match(population)
        nonzero_weight = comparison.agreement(population)
        scored = [
            row
            for row in comparison.rows
            if row.population == population and row.verdict in {AGREE, DISAGREE}
        ]
        drawn = [row for row in scored if row.sampled_action is not None]
        undrawn = [row for row in scored if row.sampled_action is None]
        exact = [row for row in scored if not row.price_substitutions]
        stranded = [row.spot_key for row in undrawn if not row.price_substitutions]

        # The rate's own denominator is the decisions that drew, and it counts them the
        # way this test does. A gap below the scored population is a price the sizing
        # table could not put in front of hero, never a miss, and blaming the collapse
        # rule for one is what the bound keeps out.
        assert nonzero_weight.denominator == len(scored)
        assert sampled.denominator == len(drawn)
        assert not stranded, stranded
        assert len(drawn) * 10 >= len(scored) * 9, (population, len(drawn), len(scored))
        assert len(exact) * 5 >= len(scored), (population, len(exact), len(scored))

        # And it must be the stricter measurement, not a second printing of the looser
        # one. A mixed cell that draws the other way agrees and does not match.
        assert sampled.percent < nonzero_weight.percent - 3.0


def test_the_comparison_is_a_pure_function_of_the_committed_sample(sample) -> None:
    first = compare_committed_sample(sample)
    second = compare_committed_sample(sample)

    assert render_comparison_report(first) == render_comparison_report(second)
    assert render_refusal_inventory(first) == render_refusal_inventory(second)


def test_the_report_states_its_preflop_boundary_before_any_number(comparison) -> None:
    text = render_comparison_report(comparison)
    first_digit = next(
        (index for index, character in enumerate(text) if character.isdigit()), len(text)
    )

    assert "preflop" in text[:first_digit].lower()


def test_the_report_says_a_disagreement_is_not_proof_the_chart_is_wrong(comparison) -> None:
    text = render_comparison_report(comparison).lower()

    assert "disagreement" in text
    assert "does not" in text or "not establish" in text
