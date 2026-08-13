"""Phase 08: ingesting a public hand corpus, and comparing the bot against real players.

These tests are authored before any implementation exists and frozen before any is
written, so they are the specification rather than a description of what got built.

The one that matters most is `test_every_committed_hand_settles_to_the_corpus_oracle`.
Every other check in this repo compares something this repo wrote against something
else this repo wrote. That one compares our settlement against a number published by
somebody else, and it is the only reason the phase exists.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from poker_training_bot.data_pipeline.comparison import (
    AGREE,
    DISAGREE,
    REFUSED,
    classify_observed_action,
    compare_committed_sample,
    render_comparison_report,
    render_refusal_inventory,
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
from poker_training_bot.hand_history.schema import HistoryActionKind, StreetName
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


# --------------------------------------------------------------------------- #
# Reading the corpus format
# --------------------------------------------------------------------------- #


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
    """The corpus reveals all six hands, which is what makes a comparison possible.

    A player who folds preflop still has cards, and the spot they folded is exactly
    the spot worth asking the chart about.
    """
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
    """An oracle derived from the thing it checks is a mirror.

    The parsed finishing stacks must be exactly the corpus's own integers, so a
    conversion bug that also fools the replayer still fails the settlement check.
    """
    assert "finishing_stacks = [10310, 9900, 10000, 9790, 10000, 10000]" in HAND_ZERO
    assert hand_zero.finishing_stacks == (10310, 9900, 10000, 9790, 10000, 10000)
    assert sum(hand_zero.finishing_stacks) == sum(hand_zero.starting_stacks)


# --------------------------------------------------------------------------- #
# Seats, the button, and positions
# --------------------------------------------------------------------------- #


def test_seats_and_the_button_follow_the_corpus_blind_placement(hand_zero) -> None:
    """An error here does not raise. It compares real hands against the wrong chart cells.

    The corpus posts the small blind first and the big blind second, so p1 and p2 are
    the blinds and the button is the last seat in the ring.
    """
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


# --------------------------------------------------------------------------- #
# The action vocabulary, and the two amount meanings
# --------------------------------------------------------------------------- #


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
    """The sharpest test in the file for the amount-meaning bug.

    The small blind already has 50 in front of them when they call a raise to 210, so
    the schema wants 160. A converter that copies the corpus number across writes 210,
    the hand still replays, and it settles to the wrong stacks.
    """
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


# --------------------------------------------------------------------------- #
# The oracle
# --------------------------------------------------------------------------- #


def _settled_stacks(hand_zero_like, normalized) -> tuple[int, ...]:
    replay = replay_hand(normalized)
    by_seat = {player.seat: player.starting_stack for player in normalized.players}
    for seat, amount in replay.committed_by_seat.items():
        by_seat[seat] -= amount
    for seat, amount in normalized.result.payouts.items():
        by_seat[seat] += amount
    return tuple(by_seat[seat] for seat in sorted(by_seat))


def test_one_hand_settles_to_the_corpus_finishing_stacks(hand_zero) -> None:
    normalized = convert_hand(hand_zero)

    assert _settled_stacks(hand_zero, normalized) == hand_zero.finishing_stacks


def test_every_committed_hand_settles_to_the_corpus_oracle(sample) -> None:
    """The phase's central criterion, stated as one assertion.

    A single seat off by a single chip on a single hand fails. There is no tolerance
    and no aggregate: an aggregate that nets to zero hides two errors that cancel.
    """
    mismatches = []
    for record in sample.records:
        settled = _settled_stacks(record.corpus, record.normalized)
        if settled != record.corpus.finishing_stacks:
            mismatches.append((record.corpus.hand_id, settled, record.corpus.finishing_stacks))

    assert mismatches == []


# --------------------------------------------------------------------------- #
# The committed sample itself
# --------------------------------------------------------------------------- #


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


def test_every_hand_in_the_sample_is_six_handed_at_one_hundred_big_blinds(sample) -> None:
    """The one spot the committed chart answers, which is why these hands were chosen."""
    for record in sample.records:
        assert len(record.corpus.players) == 6
        assert record.corpus.blinds == (50, 100)
        assert set(record.corpus.starting_stacks) == {10000}


def test_the_sample_is_committed_and_readable_without_the_network(sample) -> None:
    for path in sample.committed_paths:
        assert Path(path).is_file()


# --------------------------------------------------------------------------- #
# What agreement means
# --------------------------------------------------------------------------- #


def test_a_minority_action_the_chart_mixes_counts_as_agreement() -> None:
    """A strategy that folds seven times in ten does not disagree with a fold.

    Scoring a mixed cell action-for-action makes a correct chart look wrong in
    proportion to how mixed it is, which is exactly backwards.
    """
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


# --------------------------------------------------------------------------- #
# Who is being compared
# --------------------------------------------------------------------------- #


def test_the_machine_and_the_humans_are_reported_as_separate_populations(comparison) -> None:
    """Averaging a near-equilibrium bot with human players describes neither."""
    assert "Pluribus" in comparison.populations
    assert "humans" in comparison.populations
    assert len(comparison.populations) == 2


def test_no_human_decision_is_counted_in_the_machine_population(comparison) -> None:
    for row in comparison.rows:
        assert (row.player == "Pluribus") == (row.population == "Pluribus")


def test_only_preflop_decision_points_are_compared(comparison) -> None:
    """Phase 06's fallback never bets, so a postflop comparison measures the fallback."""
    for row in comparison.rows:
        assert row.street == "preflop"


def test_forced_blind_posts_are_not_decision_points(comparison) -> None:
    for row in comparison.rows:
        assert row.observed_action in {"fold", "check", "call", "bet", "raise"}


# --------------------------------------------------------------------------- #
# The refusal inventory, and the reports
# --------------------------------------------------------------------------- #


def test_the_refusal_inventory_is_keyed_by_the_refusal_s_own_detail(comparison) -> None:
    """Re-deriving the spot key here would give two places to disagree about it."""
    for entry in comparison.refusal_inventory:
        assert entry.spot_key
        assert entry.count > 0


def test_the_refusal_inventory_is_ordered_most_reached_first(comparison) -> None:
    counts = [entry.count for entry in comparison.refusal_inventory]

    assert counts == sorted(counts, reverse=True)


def test_the_inventory_says_which_spots_the_self_play_run_never_reached(comparison) -> None:
    for entry in comparison.refusal_inventory:
        assert entry.seen_in_self_play in {True, False}


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
