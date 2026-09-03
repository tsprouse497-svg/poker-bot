"""Phase 08: ingesting a public hand corpus, and comparing the bot against real players.

Authored before any implementation existed, so these are the specification rather than a
description. The one that matters most is `test_every_committed_hand_settles_to_the_corpus_oracle`:
every other check compares something this repo wrote against something else it wrote, and that one
compares our settlement against somebody else's number."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from poker_training_bot.data_pipeline import comparison as comparison_module
from poker_training_bot.data_pipeline.comparison import (
    AGREE,
    DISAGREE,
    PRICE_BANDS,
    REFUSED,
    REPORTED_POSITIONS,
    classify_observed_action,
    compare_committed_sample,
    price_band_for,
)
from poker_training_bot.data_pipeline.convert import ConversionError, convert_hand
from poker_training_bot.data_pipeline.corpus import CorpusParseError, parse_corpus_hand
from poker_training_bot.data_pipeline.sample import (
    SAMPLE_HAND_COUNT,
    SELECTION_STRIDE,
    load_committed_sample,
    select_source_paths,
)
from poker_training_bot.hand_history.replay import replay_hand
from poker_training_bot.hand_history.schema import (
    ExpectedResult,
    HistoryActionKind,
    StreetName,
)
from poker_training_bot.poker_core.positions import seat_positions

# The first hand of the corpus, verbatim. Embedded rather than read from the committed
# sample so the conversion tests describe the format itself and keep working even if
# the selection rule later changes which hands are committed.
HAND_ZERO = """\
variant = 'NT'
ante_trimming_status = true
antes = [0, 0, 0, 0, 0, 0]
blinds_or_straddles = [50, 100, 0, 0, 0, 0]
min_bet = 100
starting_stacks = [10000, 10000, 10000, 10000, 10000, 10000]
actions = ['d dh p1 TcQc', 'd dh p2 8s4c', 'd dh p3 9c3d', 'd dh p4 Ah4h', 'd dh p5 Th5s', \
'd dh p6 6c7s', 'p3 f', 'p4 cbr 210', 'p5 f', 'p6 f', 'p1 cc', 'p2 f', 'd db 7d5h9d', \
'p1 cc', 'p4 cc', 'd db 7c', 'p1 cc', 'p4 cc', 'd db Qh', 'p1 cbr 230', 'p4 f']
hand = 0
players = ['MrBlue', 'MrBlonde', 'MrWhite', 'MrPink', 'MrBrown', 'Pluribus']
finishing_stacks = [10310, 9900, 10000, 9790, 10000, 10000]
"""

HAND_ZERO_PATH = "pluribus/100/0.phh"


@pytest.fixture(scope="module")
def hand_zero():
    return parse_corpus_hand(HAND_ZERO, source_path=HAND_ZERO_PATH)


@pytest.fixture(scope="module")
def sample():
    return load_committed_sample()


@pytest.fixture(scope="module")
def comparison(sample):
    return compare_committed_sample(sample)


# --- Reading the corpus format ---


def test_a_corpus_hand_parses_into_the_fields_the_phase_needs(hand_zero) -> None:
    assert hand_zero.players == (
        "MrBlue",
        "MrBlonde",
        "MrWhite",
        "MrPink",
        "MrBrown",
        "Pluribus",
    )
    assert hand_zero.starting_stacks == (10000,) * 6
    assert hand_zero.finishing_stacks == (10310, 9900, 10000, 9790, 10000, 10000)
    assert hand_zero.blinds == (50, 100)
    assert hand_zero.min_bet == 100


def test_every_seat_carries_its_dealt_hole_cards(hand_zero) -> None:
    # The corpus reveals all six hands, which is what makes a comparison possible: a player who
    # folds preflop still has cards, and that is the spot worth asking the chart about.
    assert hand_zero.hole_cards == (
        ("Tc", "Qc"),
        ("8s", "4c"),
        ("9c", "3d"),
        ("Ah", "4h"),
        ("Th", "5s"),
        ("6c", "7s"),
    )


def test_the_hand_id_comes_from_the_source_path_not_the_corpus_hand_number(hand_zero) -> None:
    """Corpus hand numbers restart per session, so they are not unique across a sample."""
    assert hand_zero.hand_id == "pluribus/100/0"
    assert hand_zero.source_path == HAND_ZERO_PATH


def test_a_hand_without_finishing_stacks_is_rejected_rather_than_converted() -> None:
    """The oracle is not optional. A hand with no outside answer proves nothing."""
    text = HAND_ZERO.replace(
        "finishing_stacks = [10310, 9900, 10000, 9790, 10000, 10000]\n", ""
    )

    with pytest.raises(CorpusParseError):
        parse_corpus_hand(text, source_path=HAND_ZERO_PATH)


def test_the_corpus_settlement_is_never_computed_from_our_own_replay(hand_zero) -> None:
    """An oracle derived from the thing it checks is a mirror. The parsed finishing stacks must
    be the corpus's own integers, so a conversion bug that fools the replayer still fails."""
    assert "finishing_stacks = [10310, 9900, 10000, 9790, 10000, 10000]" in HAND_ZERO
    assert hand_zero.finishing_stacks == (10310, 9900, 10000, 9790, 10000, 10000)
    assert sum(hand_zero.finishing_stacks) == sum(hand_zero.starting_stacks)


# --- Seats, the button, and positions ---


def test_seats_and_the_button_follow_the_corpus_blind_placement(hand_zero) -> None:
    """An error here does not raise; it compares real hands against the wrong chart cells. The
    corpus posts the blinds first, so p1 and p2 are the blinds and the button is last."""
    hand = convert_hand(hand_zero)

    assert tuple(player.seat for player in hand.players) == (0, 1, 2, 3, 4, 5)
    assert hand.button_seat == 5
    assert hand.blinds.small_blind == 50
    assert hand.blinds.big_blind == 100


def test_every_seat_gets_the_position_the_repo_vocabulary_names(hand_zero) -> None:
    hand = convert_hand(hand_zero)

    assert seat_positions([player.seat for player in hand.players], hand.button_seat) == {
        0: "SB",
        1: "BB",
        2: "LJ",
        3: "HJ",
        4: "CO",
        5: "BTN",
    }


def test_the_first_voluntary_preflop_actor_is_the_seat_after_the_big_blind(hand_zero) -> None:
    hand = convert_hand(hand_zero)
    preflop = hand.streets[0].actions

    assert [action.kind for action in preflop[:2]] == [
        HistoryActionKind.POST_BLIND,
        HistoryActionKind.POST_BLIND,
    ]
    assert [action.seat for action in preflop[:2]] == [0, 1]
    assert preflop[2].seat == 2


# --- The action vocabulary, and the two amount meanings ---


def test_a_preflop_aggressive_action_becomes_a_raise_to_its_target_total(hand_zero) -> None:
    hand = convert_hand(hand_zero)
    raises = [
        action
        for action in hand.streets[0].actions
        if action.kind is HistoryActionKind.RAISE
    ]

    assert len(raises) == 1
    assert raises[0].seat == 3
    assert raises[0].amount == 210


def test_a_call_carries_added_chips_rather_than_the_target_total(hand_zero) -> None:
    """The sharpest test in the file for the amount-meaning bug. The small blind already has 50
    in front of them when they call a raise to 210, so the schema wants 160; a converter that
    copies the corpus number across writes 210, replays fine, and settles to wrong stacks."""
    hand = convert_hand(hand_zero)
    calls = [
        action
        for action in hand.streets[0].actions
        if action.kind is HistoryActionKind.CALL
    ]

    assert len(calls) == 1
    assert calls[0].seat == 0
    assert calls[0].amount == 160


def test_the_first_aggression_on_a_postflop_street_becomes_a_bet_of_added_chips(
    hand_zero,
) -> None:
    hand = convert_hand(hand_zero)
    river = next(street for street in hand.streets if street.name is StreetName.RIVER)
    bets = [action for action in river.actions if action.kind is HistoryActionKind.BET]

    assert len(bets) == 1
    assert bets[0].seat == 0
    assert bets[0].amount == 230


def test_a_passive_action_with_nothing_owed_becomes_a_check_without_an_amount(
    hand_zero,
) -> None:
    hand = convert_hand(hand_zero)
    flop = next(street for street in hand.streets if street.name is StreetName.FLOP)

    assert [action.kind for action in flop.actions] == [
        HistoryActionKind.CHECK,
        HistoryActionKind.CHECK,
    ]
    assert all(action.amount is None for action in flop.actions)


def test_a_hand_the_converter_cannot_express_raises_with_a_named_reason() -> None:
    """No silent skipping. An unconvertible hand is a finding, not a missing row."""
    text = HAND_ZERO.replace("variant = 'NT'", "variant = 'FT'")

    with pytest.raises(ConversionError) as raised:
        convert_hand(parse_corpus_hand(text, source_path=HAND_ZERO_PATH))

    assert raised.value.reason


# --- The oracle ---


def _settled_stacks(hand_zero_like, normalized) -> tuple[int, ...]:
    """Each seat's final stack as the engine settles it. Payouts come from `replay.settlement`,
    never `normalized.result`, which the converter derived from the corpus's own finishing
    stacks: sourcing them there collapses the expression back to those stacks regardless."""
    replay = replay_hand(normalized)
    by_seat = {player.seat: player.starting_stack for player in normalized.players}
    for seat, amount in replay.committed_by_seat.items():
        by_seat[seat] -= amount
    for seat, amount in replay.settlement.payouts.items():
        by_seat[seat] += amount
    return tuple(by_seat[seat] for seat in sorted(by_seat))


def test_one_hand_settles_to_the_corpus_finishing_stacks(hand_zero) -> None:
    normalized = convert_hand(hand_zero)

    assert _settled_stacks(hand_zero, normalized) == hand_zero.finishing_stacks


def test_every_committed_hand_settles_to_the_corpus_oracle(sample) -> None:
    """The phase's central criterion, as one assertion: a single seat off by a single chip
    on a single hand fails, since an aggregate netting to zero hides two errors."""
    mismatches = []
    for record in sample.records:
        settled = _settled_stacks(record.corpus, record.normalized)
        if settled != record.corpus.finishing_stacks:
            mismatches.append((record.corpus.hand_id, settled, record.corpus.finishing_stacks))

    assert mismatches == []


# A committed chopped pot: seats 0 and 3 take 2550 each of a 5100 pot. Named rather than searched
# for, so a sample that no longer holds it fails loudly rather than testing nothing.
MISALLOCATED_SETTLEMENT_HAND = "pluribus/41/18"


def test_a_settlement_that_misallocates_one_chip_is_refused(sample) -> None:
    """The guard that turns the published stacks into an oracle, exercised not assumed.
    Moving one chip between the two winners of a chopped pot leaves the pot and the winning
    seats identical, so the payout comparison is the only check that can catch it, and
    `corpus-settlement-check-disabled` in `verification/mutations.yml` proves it does."""
    record = next(
        item for item in sample.records if item.corpus.hand_id == MISALLOCATED_SETTLEMENT_HAND
    )
    result = record.normalized.result
    richer, poorer = result.winner_seats
    payouts = dict(result.payouts)
    payouts[richer] += 1
    payouts[poorer] -= 1
    misallocated = replace(
        record.normalized,
        result=ExpectedResult(result.winner_seats, result.pot, payouts),
    )

    with pytest.raises(ValueError, match="does not match expected result"):
        replay_hand(misallocated)


# --- The committed sample itself ---


def test_the_selection_rule_is_a_stride_over_a_stable_sort() -> None:
    paths = [
        f"pluribus/{group:03d}/{index}.phh"
        for group in range(100, 140)
        for index in range(30)
    ]

    selected = select_source_paths(paths)

    assert selected == tuple(sorted(paths)[::SELECTION_STRIDE])


def test_the_selection_rule_does_not_depend_on_the_order_it_is_handed(sample) -> None:
    paths = [record.corpus.source_path for record in sample.records]

    assert select_source_paths(list(reversed(paths))) == select_source_paths(paths)


def test_the_committed_sample_holds_the_ruled_hand_count(sample) -> None:
    assert len(sample.records) + len(sample.exclusions) == SAMPLE_HAND_COUNT


def test_no_hand_is_dropped_without_a_committed_named_reason(sample) -> None:
    """An exclusion a reviewer cannot read is the failure mode this rules out."""
    for exclusion in sample.exclusions:
        assert exclusion.hand_id
        assert exclusion.reason


def test_the_committed_source_text_matches_the_checksum_it_was_committed_under(
    sample,
) -> None:
    for record in sample.records:
        digest = hashlib.sha256(record.source_text.encode("utf-8")).hexdigest()
        assert digest == record.source_checksum, record.corpus.hand_id


def test_the_committed_source_text_reparses_into_the_committed_corpus_hand(sample) -> None:
    """The conversion is checkable offline, which is why the source text is committed."""
    for record in sample.records:
        assert parse_corpus_hand(
            record.source_text, source_path=record.corpus.source_path
        ) == record.corpus


def test_the_sidecar_covers_every_committed_hand_and_nothing_else(sample) -> None:
    assert {record.corpus.hand_id for record in sample.records} == set(sample.sidecar)


def test_the_sidecar_says_the_same_thing_as_the_corpus_text_it_describes(sample) -> None:
    """The largest committed file in the phase, checked rather than carried. Judgment call 3 put
    the hole cards and the published stacks in a sidecar so the oracle would never sit inside the
    record the replayer produces, and nothing reads it at run time."""
    for record in sample.records:
        entry = sample.sidecar[record.corpus.hand_id]

        assert entry["source_path"] == record.corpus.source_path
        assert entry["source_checksum"] == record.source_checksum
        assert tuple(entry["players"]) == record.corpus.players
        assert tuple(entry["hole_cards"]) == tuple(
            "".join(pair) for pair in record.corpus.hole_cards
        )
        assert tuple(entry["starting_stacks"]) == record.corpus.starting_stacks
        assert tuple(entry["finishing_stacks"]) == record.corpus.finishing_stacks


def test_the_all_in_coverage_the_documents_claim_is_the_coverage_the_sample_has(
    sample,
) -> None:
    """The number three committed documents state about this sample, pinned to it. They said
    7, counting only a preflop shove of a full stack: PHH writes an aggressive action as the
    total its actor's street bet reaches, so a later-street all-in, and every all-in reached by
    calling one, is invisible to that count."""
    all_in_hands = sum(
        1
        for record in sample.records
        if any(
            replay_hand(record.normalized).committed_by_seat[player.seat] == player.starting_stack
            for player in record.normalized.players
        )
    )

    assert all_in_hands == 24


def test_every_hand_in_the_sample_is_six_handed_at_one_hundred_big_blinds(sample) -> None:
    """The one spot the committed chart answers, which is why these hands were chosen."""
    for record in sample.records:
        assert len(record.corpus.players) == 6
        assert record.corpus.blinds == (50, 100)
        assert set(record.corpus.starting_stacks) == {10000}


def test_the_sample_is_committed_and_readable_without_the_network(sample) -> None:
    for path in sample.committed_paths:
        assert Path(path).is_file()


# --- What agreement means ---


def test_a_minority_action_the_chart_mixes_counts_as_agreement() -> None:
    """A strategy that folds seven times in ten does not disagree with a fold. Scoring a mixed
    cell action-for-action makes a correct chart look wrong in proportion to its mixing."""
    weights = (("raise", 0.3), ("fold", 0.7))

    assert classify_observed_action("raise", weights) == AGREE
    assert classify_observed_action("fold", weights) == AGREE


def test_an_action_the_chart_gives_no_weight_at_all_is_a_disagreement() -> None:
    weights = (("raise", 0.3), ("fold", 0.7))

    assert classify_observed_action("call", weights) == DISAGREE


def test_a_zero_weight_entry_is_not_agreement_merely_because_it_is_listed() -> None:
    weights = (("raise", 0.3), ("call", 0.0), ("fold", 0.7))

    assert classify_observed_action("call", weights) == DISAGREE


def test_a_refused_spot_is_never_scored_as_a_disagreement(comparison) -> None:
    """A missing chart cell and a wrong chart cell are different findings."""
    for row in comparison.rows:
        if row.refusal is not None:
            assert row.verdict == REFUSED


def test_refusals_sit_outside_the_agreement_denominator(comparison) -> None:
    for population in comparison.populations:
        rate = comparison.agreement(population)
        scored = sum(
            1
            for row in comparison.rows
            if row.population == population and row.verdict in {AGREE, DISAGREE}
        )
        assert rate.denominator == scored
        assert rate.denominator + comparison.refusal_count(population) == sum(
            1 for row in comparison.rows if row.population == population
        )


def test_every_reported_rate_carries_the_count_it_was_computed_over(comparison) -> None:
    for population in comparison.populations:
        rate = comparison.agreement(population)
        assert rate.denominator > 0
        assert 0 <= rate.numerator <= rate.denominator


# --- Who is being compared ---


def test_the_machine_and_the_humans_are_reported_as_separate_populations(comparison) -> None:
    """Averaging a near-equilibrium bot with human players describes neither."""
    assert "Pluribus" in comparison.populations
    assert "humans" in comparison.populations
    assert len(comparison.populations) == 2


def test_no_human_decision_is_counted_in_the_machine_population(comparison) -> None:
    for row in comparison.rows:
        assert (row.player == "Pluribus") == (row.population == "Pluribus")


def test_no_rate_can_be_asked_for_without_naming_a_population(comparison) -> None:
    """The pooled rate has no way to be spelled, which is the only durable version. Judgment
    call 7 forbids averaging the machine with the humans, and a convention would be broken the
    same way the first action split broke it; a required argument cannot be."""
    with pytest.raises(TypeError):
        comparison.agreement_within(action="call")


def test_every_decision_carries_the_position_it_was_taken_from(sample, comparison) -> None:
    """A preflop chart is indexed by position, so a rate without one hides the cell."""
    expected = {
        record.corpus.hand_id: seat_positions(
            [player.seat for player in record.normalized.players],
            record.normalized.button_seat,
        )
        for record in sample.records
    }

    for row in comparison.rows:
        assert row.position == expected[row.hand_id][row.seat]


def test_the_position_split_partitions_the_population_it_splits(comparison) -> None:
    """Every scored decision lands in exactly one seat's cell and none lands twice, which
    is what makes the table a breakdown rather than six overlapping views of one number."""
    for population in comparison.populations:
        whole = comparison.agreement(population)
        by_position = [
            comparison.agreement_within(population, position=position)
            for position in REPORTED_POSITIONS
        ]

        assert sum(rate.denominator for rate in by_position) == whole.denominator
        assert sum(rate.numerator for rate in by_position) == whole.numerator


def test_the_position_split_is_what_localises_the_calling_gap(comparison) -> None:
    """The finding this split exists for, pinned so it cannot quietly stop being true.

    Phase 08 found that calls are where the chart and real players part company, and that the
    gap was the big blind, which was also the seat the chart refused most often. Both halves
    were asserted, since either alone reads as a smaller problem than it is. Both move under the
    cutover and none of their numbers survives a chart answering 249 nodes where it answered 36
    keys, so the ruled mechanism replaces them - nothing here can re-measure before the artifact
    exists, and an invented figure would be a guess.

    **The calling gap is now every seat but the big blind, and the merge is why.** Decision 45
    keeps the bot's flats and merges them into its raises at the 20 non-big-blind spots facing
    an open, which publish raise-or-fold; the five big-blind spots keep fold, call and raise. A
    human who flat-calls an open therefore agrees in the big blind and disagrees at every other
    seat, by construction rather than by any disagreement about which hands are worth playing -
    the accepted defect "merged flats play differently", scored on a real corpus. Asserted as a
    partition and not as an ordering of percentages, which depends on what else each seat was
    scored on and is a measurement.

    **No decision is refused for being an opening range.** A first-in spot is committed for each
    of the five seats that can be first in, so a refusal naming a key ending `/rfi` would mean
    they did not arrive. Under the 86 four such families were most of the table's silence -
    lojack, hijack, cutoff and button each refused above 95 percent, while the big blind at 118
    of 361 came out the *least* refused seat. Which seat is most refused now is unasserted and
    recorded as unsettled: limped pots, squeezes and beyond-raise-depth spots still refuse.

    The small blind's own mechanism survives intact and is kept: `t6/d100/SB/rfi` is a committed
    opening range and the solve is `limp: false`, so every human limp there is scored a
    disagreement. Dropped is the share it was asserted at - more than half the small blind's
    scored calls - which any majority satisfied and which the cutover moves by widening that
    denominator. So is `calls["BB"].denominator > 100`: which facing-an-open keys the exposure
    clause kept is counted at 25 and never listed, so the floor is over the whole scored call
    population instead.
    """
    calls = {
        position: comparison.agreement_within("humans", action="call", position=position)
        for position in REPORTED_POSITIONS
    }

    # `Rate.percent` reports 0.0 on an empty denominator, so an emptied seat satisfies a claim
    # about rates by arithmetic rather than by measurement.
    for position, rate in calls.items():
        assert rate.denominator > 0, (position, calls)
    assert sum(rate.denominator for rate in calls.values()) > 100, calls

    # A cold call facing exactly one raise: the population decision 45 rules on. A scored
    # row cannot be a limped pot reopened by a raise, since no committed spot holds a limp.
    flats = [
        row
        for row in comparison.rows
        if row.population == "humans"
        and row.observed_action == "call"
        and row.raises_faced == 1
        and row.verdict in {AGREE, DISAGREE}
    ]
    defended = [row for row in flats if row.position == "BB"]
    elsewhere = [row for row in flats if row.position != "BB"]

    assert defended, "no scored blind defence, so the merge has nothing to be told from"
    assert elsewhere, "no scored flat outside the blind, so the merge is untested"
    assert all(row.verdict == DISAGREE for row in elsewhere), [
        (row.position, row.asked_spot_key) for row in elsewhere if row.verdict == AGREE
    ]
    # The other side of the partition, and the reason the line above is about the merge
    # rather than about the chart having no calls anywhere: a build that merged the big
    # blind too would leave this one with nothing.
    assert any(row.verdict == AGREE for row in defended), [
        row.asked_spot_key for row in defended
    ]

    limped_open = [
        row
        for row in comparison.rows
        if row.population == "humans"
        and row.position == "SB"
        and row.observed_action == "call"
        and row.verdict in {AGREE, DISAGREE}
        and row.asked_spot_key == "t6/d100/SB/rfi"
    ]

    assert limped_open, "no human limp was scored against the small blind's own open"
    assert all(row.verdict == DISAGREE for row in limped_open)

    opening_refusals = [
        row.asked_spot_key
        for row in comparison.rows
        if row.verdict == REFUSED and (row.asked_spot_key or "").endswith("/rfi")
    ]

    assert opening_refusals == [], sorted(set(opening_refusals))


def test_the_price_a_decision_faced_is_banded_only_where_a_band_means_something(
    comparison,
) -> None:
    """A band around an opening size is only about decisions facing a single open: facing
    no raise there is no price, and facing two the price is a three-bet's."""
    for row in comparison.rows:
        assert row.price_faced_bb >= 1.0
        if row.price_band is not None:
            assert row.price_band in {band for band, _ in PRICE_BANDS}

    assert price_band_for(2.0, raises_faced=0) is None
    assert price_band_for(9.5, raises_faced=2) is None
    assert price_band_for(2.25, raises_faced=1) == "at or under 2.25bb"
    assert price_band_for(2.5, raises_faced=1) == "2.26 to 2.50bb"
    assert price_band_for(4.0, raises_faced=1) == "over 2.50bb"


def test_only_preflop_decision_points_that_were_chosen_are_compared(comparison) -> None:
    """Phase 06's fallback never bets, so a postflop comparison measures the fallback, and
    a posted blind is forced rather than chosen."""
    for row in comparison.rows:
        assert row.street == "preflop"
        assert row.observed_action in {"fold", "check", "call", "bet", "raise"}


# --- The refusal inventory, and the reports ---


def test_the_refusal_inventory_is_keyed_by_the_refusal_s_own_detail(comparison) -> None:
    """Re-deriving the spot key here would give two places to disagree about it."""
    for entry in comparison.refusal_inventory:
        assert entry.spot_key
        assert entry.count > 0


def test_the_self_play_cross_reference_was_read_rather_than_defaulted(comparison) -> None:
    """The claim this column carries - that real hands reach spots self-play never does - survives
    only if the self-play side was read; an inventory yielding nothing marks every spot NEW.

    Phase 08 asserted both halves: that self-play had reached some of the corpus's gap spots,
    and that it had missed others. Both were written `any(...)`, the shape the cutover breaks
    silently rather than loudly. They partition the inventory, so once the spot set moves
    underneath them both can still hold while the column has stopped being a reading of anything
    - True by default satisfies the first, False the second, each held up by rows the other half
    was about. Asserted instead is the column's definition: `seen_in_self_play` is exactly
    membership of `_self_play_spots()`, recomputed from the same read, then both halves on sets.

    The overlap is no longer a certainty argued from one spot. Under the 86 the lojack opened
    every self-play hand into a retired key the corpus reached once a hand; all five opening
    ranges are committed now, so self-play refuses past the committed raise depth instead. The
    corpus reaches those too, by an argument this file cannot close yet, so a red at stage 6 is
    a finding about two refusal sets rather than a threshold to loosen.

    Both halves read a rendered report, so they depend on it being regenerated in the same commit
    as the chart: a stale inventory naming the retired chart's gaps lies.
    `SELF-PLAY-NO-LONGER-FINDS-COVERAGE-GAPS` was filed on the deleted reading and needs
    restating against this one."""
    reached = comparison_module._self_play_spots()
    inventory = comparison.refusal_inventory
    named = {entry.spot_key for entry in inventory}
    seen = {entry.spot_key for entry in inventory if entry.seen_in_self_play}
    unseen = {entry.spot_key for entry in inventory if not entry.seen_in_self_play}

    assert reached
    assert inventory
    assert seen == named & reached, sorted(seen.symmetric_difference(named & reached))
    assert unseen == named - reached, sorted(unseen.symmetric_difference(named - reached))
    assert seen, "no corpus gap spot is one self-play reaches, so the overlap half is gone"
    assert unseen, "self-play reaches every corpus gap spot, so the NEW half is gone"


def test_an_unreadable_self_play_inventory_fails_loudly_rather_than_emptily(
    tmp_path, monkeypatch
) -> None:
    """The cross-reference is the one input that is not the committed sample. It is recovered by
    pattern from a rendered report, so that format can move without anything here changing, and
    the honest outcome then is a broken build rather than every spot quietly upgraded to NEW."""
    missing = tmp_path / "not_written_yet.txt"
    monkeypatch.setattr(comparison_module, "SELF_PLAY_INVENTORY", missing)
    with pytest.raises(FileNotFoundError):
        comparison_module._self_play_spots()

    moved = tmp_path / "reformatted.txt"
    moved.write_text("points | spot | seen\n12 | six-handed 100bb BB vs CO raise | yes\n")
    monkeypatch.setattr(comparison_module, "SELF_PLAY_INVENTORY", moved)
    with pytest.raises(ValueError, match="no spot keys"):
        comparison_module._self_play_spots()


def test_the_refusal_inventory_is_ordered_most_reached_first(comparison) -> None:
    counts = [entry.count for entry in comparison.refusal_inventory]

    assert counts == sorted(counts, reverse=True)


def test_the_inventory_says_which_spots_the_self_play_run_never_reached(comparison) -> None:
    """The column's values; the test above owns its definition. `in {True, False}` was the whole
    body and admits 1, 0 and 1.0 as well as an empty inventory, so a column carrying a count read
    the same - `render_refusal_inventory` prints NEW on falsiness and would print it for 0."""
    flags = [entry.seen_in_self_play for entry in comparison.refusal_inventory]

    assert flags
    assert all(isinstance(flag, bool) for flag in flags)
    assert set(flags) == {True, False}, "the column reads the same at every spot"
