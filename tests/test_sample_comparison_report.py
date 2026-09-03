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
    PRICE_BANDS,
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

# Every seat that can be first in, and so every opening range the cutover commits. The
# retired 86 held one of them - the small blind's - which is why this file used to read a
# single price out by name and why the lojack's row went missing when it did.
OPEN_SPOTS = ("LJ", "HJ", "CO", "BTN", "SB")


@pytest.fixture(scope="module")
def sample():
    return load_committed_sample()


@pytest.fixture(scope="module")
def comparison(sample):
    return compare_committed_sample(sample)


def solved_open_bb() -> float:
    """The price the committed opening ranges come in at, read through `sizes_bb`.

    Not through `amount_bb`. Decision 6's table answers None at any spot offering more than
    one price, and it was the small blind's open offering the 2.5 and a 100bb jam that made
    `amount_bb` unusable here. The cutover settles that in the other direction: prices are
    exactly 2.5, 7.5 and 22.5, one per spot, with hero's own jam living only at the
    four-bet-facing spots the selection rule excludes. So a first-in spot names one price
    and it is 2.5.

    Which price the *bot* opens to was ruled on 2026-08-26 - the strategy draws it from
    these same entries with the seed it already collapses a mixed cell with - and that is
    hero's own action, not the number this report grades against. The graded number is the
    price the solved tree assumes an open arrives at.

    Gathered across the 169 hand classes, because the 2026-08-26 ruling put the entry under
    the class: `sizes_bb` takes a spot and a class, and no single class can be asked on the
    whole spot's behalf. Every class's named price is the same 2.5 and that is asserted
    rather than assumed, at each of the five spots rather than at one of them, and
    cross-checked against `RULED_CONFIG` so the number is the config decision 2 froze.
    """
    sizing = PreflopSizingTable.from_repo()

    # Asked for rather than called into, so a table that has not grown the accessor yet
    # fails as the assertion it is instead of as an AttributeError halfway down.
    assert hasattr(sizing, "sizes_bb"), "the sizing table must offer sizes_bb(spot_key, class)"
    named: set[float] = set()
    for position in OPEN_SPOTS:
        spot = f"t6/d100/{position}/rfi"
        priced = {
            hand_class_text: sizing.sizes_bb(spot, hand_class_text)
            for hand_class_text in HAND_CLASSES
        }

        assert any(entries for entries in priced.values()), f"{spot} is a committed open"
        here = sorted(
            {
                to_bb
                for entries in priced.values()
                for to_bb, _ in entries or ()
                if to_bb < float(RULED_CONFIG["stack"])
            }
        )
        assert here == [pytest.approx(RULED_CONFIG["open_raises"][0])], (position, here)
        named.update(here)

    assert len(named) == 1, sorted(named)
    return named.pop()


def test_the_sample_was_played_at_a_price_the_chart_was_not_solved_for(comparison) -> None:
    """The caveat that turns out to be most of the finding, measured rather than said.

    The committed solve opens to 2.5 big blinds. These players mostly opened smaller, and a
    cheaper price is a correct reason to continue with more hands, so a chart answering at
    2.5 is answering a more expensive question than the one it was asked.

    **Whose price sensitivity the band gap measures.** The chart's is not in it. Its big-blind
    flat is 19.63, 20.98, 22.44, 21.09 and 20.30 percent against the five openers - a 2.81-point
    spread, which the neighbouring range test pins as a defect in its own right - and the lookup
    keys on the solved 2.5 whatever the human actually faced, so the chart's answer is the same
    at every band. A constant cannot produce a gap. What the ten points below therefore measure is
    the humans moving: they defend a materially different set of hands at 2.25 than at 2.75, and
    the fixed chart scores the cheap band worse. That is a real finding about the sample and it is
    a different one from the sentence above it, which reads the gap as a fact about the chart.

    The mapping moved twice and is pinned at its ruled shape rather than at a seat. It held
    five seats, then one when `t6/d100/LJ/rfi` and three siblings were read as retired, and
    the cutover puts all five back: a first-in spot is committed for every seat that can be
    first in. Absence is asserted with presence, because `"LJ" not in` is true of the empty
    mapping and the empty mapping is how this actually breaks - `comparison.py` builds the
    pair with `amount_bb`, which answers None at a spot offering two prices, and one price
    per spot is what makes it answer at all five now.

    The comparison against the corpus is not a chart claim and does not move with it:
    `open_sizes_bb` reads every decision that faced exactly one raise, and a band is
    assigned on the raise count alone. What was added is the guard against an empty
    population, since `len(below) > len(sizes) / 2` says nothing about a sample with no
    opens in it.

    The cheap-against-dear split is narrowed to the big blind, which is where it was
    measured. Under the 86 the only banded decisions the chart scored were blind defence,
    so the seat was implicit; the cutover commits 20 more facing-an-open spots and decision
    45 publishes every one of them raise-or-fold, so a human flat there is a disagreement by
    construction. Pooling those in would drag both bands toward zero and compress the gap
    between them, which would read as the finding weakening when nothing about it had
    changed. Naming the seat keeps the population the ten-point margin was measured over.
    The two arbitrary floors it carried - fifty cheap decisions and ten dear ones - are
    replaced by a partition: every scored blind-defence call falls in exactly one band.
    """
    solved = solved_open_bb()
    sizes = comparison.open_sizes_bb()
    below = [size for size in sizes if size < solved]

    assert dict(comparison.solved_open_bb) == pytest.approx(
        {position: solved for position in OPEN_SPOTS}
    )
    assert sizes, "no decision faced a single open, so there is no opening price at all"
    assert len(below) > len(sizes) / 2

    defence = [
        row
        for row in comparison.rows
        if row.population == "humans"
        and row.position == "BB"
        and row.observed_action == "call"
        and row.price_band is not None
        and row.verdict in {AGREE, DISAGREE}
    ]
    bands = {
        band: comparison.agreement_within(
            "humans", action="call", position="BB", price_band=band
        )
        for band, _ in PRICE_BANDS
    }

    assert defence, "no blind defence was scored, so the split is a rate about nothing"
    assert sum(rate.denominator for rate in bands.values()) == len(defence), bands
    assert all(rate.denominator > 0 for rate in bands.values()), bands
    assert bands["at or under 2.25bb"].percent < bands["over 2.50bb"].percent - 10.0, bands


def test_price_banded_decisions_are_no_longer_blind_defence_alone(comparison) -> None:
    """Who the split above is a rate about, after the cutover, said rather than implied.

    A band is only assigned to a decision facing exactly one raise. Of the 86 committed keys
    exactly ten held one raise - the big blind against each of the five openers, at 2.5 and
    at 100 - so every banded decision the chart scored was blind defence, and every other
    seat facing a single open still had players behind it, failed the subtree clause and
    refused. The cutover commits 25 facing-an-open spots, 20 of them outside the big blind,
    so the banded scored population spans several seats and a reader who takes the cheap and
    dear rates for blind defence is reading them off the retired chart. That is why the test
    above names its seat.

    Two things are asserted rather than the old equality, because the ruled census counts
    the 25 without listing them and this file will not guess which. The big blind is a
    strict subset of the seats scored, which fails if the merged spots did not arrive. And
    the lojack is absent, which is not a fact about the chart at all: the lojack acts first,
    so it faces one raise only in a limped pot reopened by a raise, and no committed spot
    holds a limp, so such a row refuses and is never scored.

    The refusals that remain are asserted as present rather than as everything. Squeezes and
    spots above the multiway exposure threshold are still refused facing a single raise, and
    a build that committed them would be committing what decisions 46 and 48 exclude.
    """
    banded = [row for row in comparison.rows if row.price_band is not None]
    scored = [row for row in banded if row.verdict in {AGREE, DISAGREE}]
    seats = {row.position for row in scored}

    assert scored, "no banded decision was scored at all"
    assert seats > {"BB"}, seats
    assert "LJ" not in seats, seats
    assert [row for row in banded if row.verdict == REFUSED], "no banded decision refused"


def test_the_price_section_names_every_seat_the_chart_opens_from(comparison) -> None:
    """The graded price has to come from the seats the chart holds, or the section is a lie.

    The section read its solved size out of the lojack by name and formatted it
    unconditionally, so while that spot was read as retired it put `None` into a format
    string and the whole report raised before a reader saw any of it. The repair at the time
    was to name the small blind, the one seat left. The cutover puts all five back, so the
    section names five seats and only those five: the big blind never opens, and a section
    that grades an opening price at a seat which cannot open is the same failure in the
    other direction.

    Which of a seat's prices was ruled on 2026-08-26, and the answer is not the one this
    section publishes. The bot's own opening price is drawn per hand from `sizes_bb`; this
    section grades the sample against the price the solved tree assumes an *opponent's* open
    came in at, which is the number both price-band boundaries are drawn from. So the report
    publishes the price the chart offers, and it cannot publish a drawn one: a seeded draw
    differs hand to hand and there is no hand here to seed it with.

    Both places the number appears are asserted, and the count is recomputed against it. The
    line hero reads first names the seats and the price; the line under it grades the sample,
    and a report that names 2.5 and then counts against something else reads right and is
    wrong.
    """
    section = render_comparison_report(comparison).split("## The price these rates")[1]
    section = section.split("\n## ")[0]
    solved = solved_open_bb()
    graded = f"{solved:g}"
    at_least = sum(1 for size in comparison.open_sizes_bb() if size >= solved)

    assert set(re.findall(r"\b(?:LJ|HJ|CO|BTN|SB|BB)\b", section)) == set(OPEN_SPOTS), section
    assert re.search(rf"at {re.escape(graded)} big blinds", section), section
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

    It is the lesser number - on a mixed cell a single draw against a single observed action
    mostly measures the seed - but the ruling said both would be there, and the fallback the
    ruling offered a disagreeing reader was that both are in the report.

    **The equality between the two denominators comes back.** Its own docstring named the
    condition before it happened: "a spot whose weights are readable but whose raise size is
    not committed would give no draw". Decision 6 holds every price a spot offers, and 21 of
    the 86 committed spots offered two - a named raise and the 100bb jam - so `amount_bb`
    answered None at every one of them and the round-4 rewrite dropped `drawn == denominator`
    for a nine-in-ten floor. The cutover holds prices exactly 2.5, 7.5 and 22.5, one per
    spot, with hero's own jam only at the four-bet-facing spots the selection rule excludes.
    No committed spot offers two prices, so no scored decision can come back undrawn, and the
    floor goes back to being the equality it was written as. A sizing table answering None
    anywhere now fails it by exactly the rows it could not price.

    That leaves the legality guard, which the equality covers: a charted raise the table
    refuses in front of hero because it does not clear the minimum. That can only happen
    where the lookup moved the price it was asked about, since over a price the tree itself
    solved the next raise up is always legal - 7.5 over 2.5, 22.5 over 7.5 - so every undrawn
    decision would carry a substitution, and `stranded` names any that does not.

    `exact` is floored in the other direction and stays at one in five. Non-emptiness would
    be satisfied by one unsubstituted decision in the whole sample, and a normaliser that
    moved every price it touched is a real defect this is the only test positioned to see.
    The floor was well under the measurement on both sides of the old cutover - 299 of 456
    and 1,490 of 2,302 under the 86, 23 of 72 and 165 of 447 under the six-spot reading - and
    the direction it moves now is up: a first-in decision carries no price in its key at all,
    and four more first-in families are committed than were before.
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
        # way this test does.
        assert nonzero_weight.denominator == len(scored)
        assert sampled.denominator == len(drawn)
        assert not stranded, stranded
        assert undrawn == [], [row.spot_key for row in undrawn]
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
