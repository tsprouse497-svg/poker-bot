"""Phase 12: what the widened spot key changes downstream of the key itself.

The companion to `tests/test_spot_vocabulary.py`, split from it at the 700-line cap. That
file pins what a key can say; this one pins what the repo does once it can say it: the price
normaliser, the query and answer that carry a size and a substitution, the corpus
measurements the vocabulary moves, and the report a person reads. Both run under
`pytest_spot_vocabulary`. `ChartHit.price_substitutions` is `(sequence index, asked,
answered)` per substituted raise, empty when every price was exact.
"""

from __future__ import annotations

import pytest

from poker_training_bot.data_pipeline.comparison import compare_committed_sample
from poker_training_bot.data_pipeline.sample import load_committed_sample
from poker_training_bot.solver_artifacts import lookup as lookup_module
from poker_training_bot.solver_artifacts import schema as schema_module
from poker_training_bot.solver_artifacts.lookup import (
    MISS_UNREPRESENTABLE_SPOT,
    ChartHit,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.strategy import contract as contract_module
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR, PreflopChartStrategy

TABLE = 6
DEPTH = 100


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


def solved_line(library, hero: str, *raisers: str) -> tuple:
    """`hero`'s line where each seat raises at the price the chart solved there. Every raising
    point offers a named raise and the all-in decision 6 prices at hero's whole stack, so the
    named raise is the smaller."""
    sequence: list = []
    for raiser in raisers:
        prices = library.solved_prices_bb(TABLE, DEPTH, hero, tuple(sequence), raiser)
        assert prices, (hero, raiser, tuple(sequence))
        sequence.append(schema_module.PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@pytest.fixture(scope="module")
def strategy() -> PreflopChartStrategy:
    return PreflopChartStrategy.from_repo()


@pytest.fixture(scope="module")
def comparison():
    return compare_committed_sample(load_committed_sample())


# --------------------------------------------------------------------------- #
# Normalising a price the tree does not hold
# --------------------------------------------------------------------------- #


def query_facing(hero: str, *entries: object, hand: str = "AKs") -> ChartQuery:
    return ChartQuery(
        table_size=TABLE,
        stack_depth_bb=DEPTH,
        hero_position=hero,
        action_sequence=tuple(entries),
        hand_class=hand,
    )


def test_a_cheap_open_is_answered_from_the_solved_cell(library) -> None:
    """Ruling 8, measured: 80.8 percent of the corpus faced 2.25 or less. Authored on the
    button facing a cutoff open, which the predicate retires - the big blind is the one seat
    that ever faces a single open. The prices are read back rather than assumed, because a
    spot that already solved 2.25 would substitute nothing and still pass."""
    offered = library.solved_prices_bb(TABLE, DEPTH, "BB", (), "BTN")

    assert 2.25 not in offered
    assert min(offered) == 2.5

    found = library.lookup(query_facing("BB", raise_to("BTN", 2.25)))

    assert isinstance(found, ChartHit)
    assert found.spot_key == "t6/d100/BB/BTN:raise@2.5"


def test_the_answer_says_which_price_it_was_asked_at(library) -> None:
    """Without this an exact answer and a substituted one are indistinguishable."""
    found = library.lookup(query_facing("BB", raise_to("BTN", 2.25)))
    assert isinstance(found, ChartHit)
    assert found.price_substitutions == ((0, 2.25, 2.5),)


def test_an_exact_price_records_no_substitution(library) -> None:
    found = library.lookup(query_facing("BB", raise_to("BTN", 2.5)))
    assert isinstance(found, ChartHit)
    assert found.price_substitutions == ()


def test_a_three_bet_at_an_unsolved_price_is_answered_too(library) -> None:
    """Taylor ruled on 2026-08-20 that three-bets have to be accommodated. Of the 79 three-bet
    decisions the phase 12 chart held a cell for, 72 faced a price the tree does not hold. The
    rake-free solve holds far more of these cells, so the count moves and the property does
    not."""
    solved = solved_line(library, "LJ", "LJ", "BTN")
    three_bet = solved[1].size_bb
    cheap = round(three_bet * 0.78, 2)

    found = library.lookup(query_facing("LJ", solved[0], raise_to("BTN", cheap)))

    assert isinstance(found, ChartHit)
    assert found.spot_key == schema_module.spot_key(TABLE, DEPTH, "LJ", solved)
    assert found.price_substitutions == ((1, cheap, three_bet),)


def test_both_prices_normalise_independently(library) -> None:
    """A cheap open and a cheap three-bet in the same sequence."""
    solved = solved_line(library, "LJ", "LJ", "BTN")
    open_to, three_bet = solved[0].size_bb, solved[1].size_bb
    cheap_open = round(open_to * 0.9, 2)
    cheap_three_bet = round(three_bet * 0.78, 2)

    found = library.lookup(
        query_facing("LJ", raise_to("LJ", cheap_open), raise_to("BTN", cheap_three_bet))
    )

    assert isinstance(found, ChartHit)
    assert found.spot_key == schema_module.spot_key(TABLE, DEPTH, "LJ", solved)
    assert found.price_substitutions == (
        (0, cheap_open, open_to),
        (1, cheap_three_bet, three_bet),
    )


def test_the_solved_prices_come_from_the_loaded_keys_not_from_a_constant(library) -> None:
    """Authored when the tree carried two opening prices, so a constant was already wrong.
    The rake-free solve opens everyone to 2.5 and that instance is gone; the claim is not.
    One sequence carries an opening, a three-bet and a four-bet price no single constant can
    serve, and a normaliser reading one answers a four-bet at the opening price."""
    ladder = solved_line(library, "BB", "CO", "BB", "CO")
    prices = [entry.size_bb for entry in ladder]

    assert len(set(prices)) == 3
    assert prices[0] < prices[1] < prices[2]
    for index, entry in enumerate(ladder):
        offered = library.solved_prices_bb(TABLE, DEPTH, "BB", ladder[:index], entry.position)

        assert entry.size_bb in offered, index
        assert prices[0] not in offered or index == 0, index


def test_normalising_a_price_is_not_finding_a_nearest_spot(library) -> None:
    """The line between the ruled abstraction and heuristic guessing. Authored on a squeeze,
    which the rake-free solve holds, so the instance moves to the one structurally uncovered
    spot: nobody limps in a `limp: false` tree, and the neighbour a nearest-spot matcher
    would reach for - the small blind raising instead of calling - is at full reach."""
    found = library.lookup(query_facing("BB", call_by("SB")))

    assert not isinstance(found, ChartHit)
    assert found.code == lookup_module.MISS_SPOT_NOT_COVERED
    neighbour = library.lookup(query_facing("BB", *solved_line(library, "BB", "SB")))

    assert isinstance(neighbour, ChartHit)


def test_an_uncovered_table_size_still_refuses(library) -> None:
    found = library.lookup(
        ChartQuery(
            table_size=2,
            stack_depth_bb=DEPTH,
            hero_position="BTN",
            action_sequence=(),
            hand_class="AKs",
        )
    )
    assert not isinstance(found, ChartHit)
    assert found.code == lookup_module.MISS_NO_ARTIFACT_FOR_TABLE


def test_the_unrepresentable_code_survives_for_a_genuinely_illegal_sequence(library) -> None:
    """A code that disappears takes the distinction it drew with it."""
    found = library.lookup(query_facing("CO", raise_to("BTN", 2.5), raise_to("HJ", 8.0)))
    assert not isinstance(found, ChartHit)
    assert found.code == MISS_UNREPRESENTABLE_SPOT


# --------------------------------------------------------------------------- #
# What the query and the answer carry
# --------------------------------------------------------------------------- #


def test_a_recorded_raise_carries_its_raise_to_amount() -> None:
    """A size-aware key cannot be derived from a history that does not hold a size."""
    entry = contract_module.SeatAction(3, "raise", 225)
    assert entry.amount == 225


def test_a_recorded_raise_without_an_amount_is_rejected() -> None:
    with pytest.raises(ValueError):
        contract_module.SeatAction(3, "raise")


def test_a_recorded_fold_carries_no_amount() -> None:
    with pytest.raises(ValueError):
        contract_module.SeatAction(3, "fold", 225)


def test_a_decision_can_carry_structured_detail() -> None:
    """The shape `StrategyRefusal.detail` has, on the branch that answers instead."""
    decision = contract_module.StrategyDecision(
        "call", None, "test", (("price_substitution_0", "2.25->2.5"),)
    )
    assert decision.detail == (("price_substitution_0", "2.25->2.5"),)


def test_a_decision_detail_name_cannot_repeat() -> None:
    with pytest.raises(ValueError):
        contract_module.StrategyDecision(
            "call", None, "test", (("price_substitution_0", "a"), ("price_substitution_0", "b"))
        )


def test_a_decision_with_nothing_to_add_carries_no_detail() -> None:
    assert contract_module.StrategyDecision("fold", None, "test").detail == ()


def test_the_decision_audit_schema_version_moved() -> None:
    """The payload keeps changing shape and the version has to keep up, or two shapes share
    one number - DECISION-AUDIT-VERSION-SPANS-TWO-STREET-BET-READINGS. Phase 12 moved it to 2
    for the raise-to amount; Phase 13 to 3, for per-seat states and `current_bet`."""
    assert contract_module.DECISION_AUDIT_SCHEMA_VERSION == 3


# --------------------------------------------------------------------------- #
# The committed corpus
# --------------------------------------------------------------------------- #

SEATS_IN_ACTION_ORDER = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

BASELINE_REFUSALS = 290
"""The refusal count the retired chart measured over the committed sample. The contract names
that chart as the refusal rate's baseline and this phase deletes it, so this is the one figure
below that is recorded rather than recomputed."""


def spot_shape(spot_key_text: str) -> tuple[str, tuple[str, ...]]:
    """A spot key with its prices stripped: hero, and who did what in front of him.

    Coverage survives the cutover as a shape rather than as a key, because ruling 8 moves an
    opponent's price to a solved one. Stated over keys instead, every confinement below would
    read the whole cutover as lost coverage: no retired three-bet price survives."""
    _, _, hero, sequence = spot_key_text.split("/")
    if sequence == "rfi":
        return hero, ()
    return hero, tuple(entry.split("@")[0] for entry in sequence.split(","))


def opponents_invested(spot_key_text: str) -> int:
    """Seats other than hero that put money in voluntarily before hero acts.

    The first half of the ruled predicate, read off a key. The blinds are not in a key at
    all, so nothing has to be subtracted for them. The second half is not readable from a
    key at any price, because a key records no folds."""
    hero, entries = spot_shape(spot_key_text)
    return len({entry.split(":")[0] for entry in entries} - {hero})


RULED_PRICES = frozenset({2.5, 7.5, 22.5, 100.0})
"""Every raise-to price the solved tree holds, re-derived by a walk of the committed export.
None of the retired chart's 3.5, 8, 10.5, 11 or 13.5 survives, so a key carrying one of those
is a key answered off the chart this phase deletes."""


def prices_in(spot_key_text: str) -> frozenset[float]:
    """Every raise-to price a key names, empty for an opening spot."""
    entries = spot_key_text.split("/")[-1].split(",")
    return frozenset(float(entry.split("@")[1]) for entry in entries if "@" in entry)


def acts_twice(spot_key_text: str) -> bool:
    """A second-orbit key: some seat is recorded acting more than once."""
    return any(spot_key_text.count(f"{seat}:") > 1 for seat in SEATS_IN_ACTION_ORDER)


def retired_chart_shapes() -> frozenset[tuple[str, tuple[str, ...]]]:
    """The 36 spots the retired `six_max_nl25_100bb.json` declared, as shapes.

    Generated rather than transcribed: the retired chart is every opening range but the big
    blind's, every hero facing one earlier opener, every opener facing one three-bet, and the
    limped pot - five, fifteen, fifteen and one, reproducing its spot ids at `da05adf`."""
    shapes: set[tuple[str, tuple[str, ...]]] = set()
    for index, opener in enumerate(SEATS_IN_ACTION_ORDER[:5]):
        shapes.add((opener, ()))
        for behind in SEATS_IN_ACTION_ORDER[index + 1 :]:
            shapes.add((behind, (f"{opener}:raise",)))
            shapes.add((opener, (f"{opener}:raise", f"{behind}:raise")))
    shapes.add(("BB", ("SB:call",)))
    return frozenset(shapes)


def ruled_cost_shapes() -> frozenset[tuple[str, tuple[str, ...]]]:
    """The fifteen retired spots the cutover gives up, as the ruling states them.

    Not fourteen keys plus a limp, but what the predicate reduces to: hero opens from the
    small blind only, so four opening ranges go; hero faces a single open in the big blind
    only, so ten pairs go; and the limped pot has no node. Four, ten and one."""
    shapes: set[tuple[str, tuple[str, ...]]] = {
        (opener, ()) for opener in ("LJ", "HJ", "CO", "BTN")
    }
    for index, opener in enumerate(SEATS_IN_ACTION_ORDER[:5]):
        for behind in SEATS_IN_ACTION_ORDER[index + 1 :]:
            if behind != "BB":
                shapes.add((behind, (f"{opener}:raise",)))
    shapes.add(("BB", ("SB:call",)))
    return frozenset(shapes)


def keyed_rows(comparison) -> tuple:
    """Every decision the lookup asked about, refused or answered.

    `ComparisonRow.spot_key` is filled on the refusals only; `asked_spot_key` is on every
    row, and a population built from the first is refusals wearing the name of decisions."""
    return tuple(row for row in comparison.rows if row.asked_spot_key)


def test_no_corpus_decision_refuses_as_unrepresentable(comparison) -> None:
    """CORPUS-INEXPRESSIBLE-SPOTS closed. All 19 were a position acting twice."""
    unrepresentable = [
        row
        for row in comparison.rows
        if row.refusal is not None and row.refusal.code.endswith(MISS_UNREPRESENTABLE_SPOT)
    ]
    assert unrepresentable == []


def test_the_inventory_has_no_catch_all_row(comparison) -> None:
    """19 points, the inventory's largest row and the one nobody could act on."""
    catch_all = [
        entry
        for entry in comparison.refusal_inventory
        if entry.spot_key == "(no expressible spot)"
    ]
    assert catch_all == []


def test_every_inventory_row_names_a_spot_a_chart_phase_could_fill(comparison) -> None:
    for entry in comparison.refusal_inventory:
        assert entry.spot_key.startswith("t6/d100/")


def test_the_second_orbit_rows_are_no_longer_all_refused(comparison, library) -> None:
    """Phase 12 gave these 19 decision points a key and left them uncovered, because it
    added no coverage. That was `CHART-COVERAGE-EXPANSION` at proposed phase 14, and this is
    the one family the cutover moves the right way: four-bet and five-bet continuations are
    committed, heads-up only, so the count falls.

    Not asserted to reach zero, and the residue is confined rather than tolerated - but
    confined on the rows, not on the inventory. `InventoryEntry` carries a key and a count and
    no code, and `refusal_inventory` collects every refused row whatever its code, so a
    hand-class refusal at a spot the chart *does* hold arrives there wearing a covered shape
    and reads as absent coverage. Not hypothetical: 75 of the 86 spots hold fewer than 169
    classes, and the corpus asks `LJ:raise,SB:raise,LJ:raise,SB:raise` - a committed shape -
    with AQo, whose arriving reach there is zero. So the confinement is guarded on the code,
    the way the two tests below guard theirs, and the inventory is held to the rows it counts.
    The heads-up half is the count that moved: 15 second-orbit decisions reach a committed
    shape, and none may be refused for want of a spot."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    second_orbit = [
        entry for entry in comparison.refusal_inventory if acts_twice(entry.spot_key)
    ]
    refused = [
        row
        for row in comparison.rows
        if row.refusal is not None and row.spot_key and acts_twice(row.spot_key)
    ]

    assert sum(entry.count for entry in second_orbit) == len(refused)
    assert len(refused) < 19
    for row in refused:
        if row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED:
            assert spot_shape(row.spot_key) not in covered, row.spot_key

    heads_up = [
        row
        for row in keyed_rows(comparison)
        if acts_twice(row.asked_spot_key) and spot_shape(row.asked_spot_key) in covered
    ]

    assert len(heads_up) == 15
    for row in heads_up:
        assert row.miss_code != lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key


def test_the_corpus_keeps_its_sample(comparison) -> None:
    """A changed denominator means the replay changed, which this phase does not do."""
    assert comparison.hands_compared == 499
    assert len(comparison.rows) == 3048


def test_every_refusal_names_a_spot_key(comparison) -> None:
    """271 of the 290 refusals carried a key at the branch point; the missing 19 were the
    catch-all, and a refusal with no key names no cell anybody could fill."""
    keyless = [row for row in comparison.rows if row.refusal is not None and not row.spot_key]
    assert keyless == []


def test_the_squeeze_refusals_stay_refused_and_the_heads_up_ones_do_not(
    comparison, library
) -> None:
    """Phase 12 pinned this at 132 and expected phase 14 to shrink it by covering the cells.
    The 2026-08-25 predicate reverses that: a squeeze has two opponents invested, the clause
    the ruling refuses on, so the family is ruled out rather than uncovered pending a later
    phase, and a test hoping the number falls hides that.

    So the claim inverts and splits, and the split is pinned rather than merely non-empty:
    204 two-raise decisions, 125 squeezes, 79 heads-up. Counted together they gave 132 and
    said nothing about either. The squeezes are refused to the last row and none is a spot
    the chart holds at another price, so the guard against nearest-spot matching still bites.
    The heads-up family must be answered - and answered at the derived prices, which is the
    half that pins the cutover rather than the chart before it: every price in a heads-up key
    is one of the four the tree holds, so a build keeping a retired 8, 11 or 13.5 three-bet
    fails here, and every heads-up key is one the library declares, so a normaliser landing
    between two committed spots fails too.

    Over the artifact `opponents_invested` states the history clause and cannot state the
    other one, because a key records no folds. The one consequence of the live-players clause
    a key *can* carry is asserted instead: it leaves exactly one opening range, the small
    blind's - which is also what separates the ruled predicate from the history clause alone,
    that keeping all five."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    declared = set(library.spot_keys())
    two_raise = [
        row
        for row in keyed_rows(comparison)
        if row.asked_spot_key.split("/")[-1].count(":raise") == 2
        and not acts_twice(row.asked_spot_key)
    ]
    squeezes = [row for row in two_raise if opponents_invested(row.asked_spot_key) >= 2]
    heads_up = [row for row in two_raise if opponents_invested(row.asked_spot_key) == 1]

    assert (len(two_raise), len(squeezes), len(heads_up)) == (204, 125, 79)
    assert {key for key in declared if key.endswith("/rfi")} == {"t6/d100/SB/rfi"}

    for key in declared:
        assert opponents_invested(key) <= 1, key
    for row in squeezes:
        assert row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key
        assert spot_shape(row.asked_spot_key) not in covered, row.asked_spot_key
    for row in heads_up:
        assert row.asked_spot_key in declared, row.asked_spot_key
        assert prices_in(row.asked_spot_key) <= RULED_PRICES, row.asked_spot_key
        assert row.miss_code != lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key


def test_the_refusal_total_rose_only_where_the_ruling_gave_a_spot_up(
    comparison, library
) -> None:
    """Phase 12 pinned 290 because it added no coverage and a drop would have been a
    finding. Phase 14 was written expecting the number to fall; the predicate reversed it,
    and the contract says so in terms - measured against the retired chart, the refusal
    rate **must rise**, on the fourteen spots the predicate drops plus the limped pot and
    nowhere else, and a rise outside those fifteen is a defect rather than this cost.

    A bare inequality with a larger number on the right would give the regression away, so
    the rise is confined instead of bounded. The retired 36 split against the committed keys
    into the fifteen the ruling names and the 21 it keeps; nothing among the 21 may be refused
    for want of a spot; all 2,259 decisions reaching one of the fifteen must be. The split is
    computed from the artifact, so a converter that committed one of the fifteen, or dropped
    one of the 21, fails here rather than reading as a smaller cost.

    `CHART-CANNOT-ANSWER-A-LIMPED-POT` moves from a guard to a claim: the retired chart
    declared `t6/d100/BB/SB:call` and answered 30 of the corpus's 52 limped decisions from it,
    and the solve is `limp: false`, so no committed spot opens with a call and all 52 refuse."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    retired = retired_chart_shapes()
    given_up = retired - covered
    kept = retired & covered

    assert len(retired) == 36
    assert given_up == ruled_cost_shapes()
    assert len(given_up) == 15
    assert len(kept) == 21

    refused = [row for row in comparison.rows if row.refusal is not None]
    at_the_cost = [
        row for row in keyed_rows(comparison) if spot_shape(row.asked_spot_key) in given_up
    ]

    assert len(refused) > BASELINE_REFUSALS
    assert len(at_the_cost) == 2259
    for row in at_the_cost:
        assert row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key
    for row in refused:
        if row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED:
            assert spot_shape(row.spot_key) not in kept, row.spot_key

    limped = [
        row
        for row in keyed_rows(comparison)
        if row.asked_spot_key.split("/")[-1].split(",")[0].endswith(":call")
    ]

    assert len(limped) == 52
    assert [row for row in limped if row.refusal is None] == []
    assert [shape for shape in covered if shape[1] and shape[1][0].endswith(":call")] == []


# --------------------------------------------------------------------------- #
# What the strategy puts on its answer
# --------------------------------------------------------------------------- #


def test_the_strategy_reports_a_substituted_price_on_its_decision(strategy) -> None:
    """The cheapest measurement of what ruling 8 costs in play, and it has to be on the answer
    or no report can split on it. Authored on the button facing a 225-chip cutoff open, which
    the predicate retires; the substituted price is still the open and still 2.25, the corpus
    median, but the line runs on to a spot the predicate keeps: the small blind opens, hero
    three-bets from the big blind, the small blind five-bets all in, two players throughout.
    The all-in is load-bearing - that spot offers hero fold and call and nothing else, so this
    never asks the sizing table what a raise costs and the assertion stays on the
    substitution."""
    # Seats 0 to 3 folded. The small blind (seat 4) opened to 225, hero (seat 5) made it 750
    # from the big blind, the small blind moved in for his 10,000. Every seat started on
    # 10,000, so the table is flat at 100bb and the contributions sum to the stated pot.
    contributed = {4: 10000, 5: 750}
    query = contract_module.StrategyQuery(
        hand_id="h1",
        street="preflop",
        seat=5,
        button_seat=3,
        hole_cards=("As", "Kd"),
        board=(),
        legal_actions=("fold", "call"),
        to_call=9250,
        current_bet=10000,
        # The standing minimum is the small blind's own 9,250 increment, so a re-raise
        # would have to reach 19,250. Hero cannot, which is why raising is not legal here.
        min_raise_target=19250,
        pot=10750,
        seat_states=tuple(
            contract_module.SeatState(
                seat=seat,
                street_bet=contributed.get(seat, 0),
                committed_total=contributed.get(seat, 0),
                folded=seat in (0, 1, 2, 3),
                all_in=seat == 4,
            )
            for seat in range(6)
        ),
        stacks=((0, 10000), (1, 10000), (2, 10000), (3, 10000), (4, 0), (5, 9250)),
        blinds=(50, 100),
        preflop_actions=(
            contract_module.SeatAction(4, "raise", 225),
            contract_module.SeatAction(5, "raise", 750),
            contract_module.SeatAction(4, "raise", 10000),
        ),
    )
    outcome = strategy.decide(query)
    assert isinstance(outcome, contract_module.StrategyDecision)
    assert outcome.detail == (("price_substitution_0", "2.25->2.5"),)


# --------------------------------------------------------------------------- #
# The report a person reads
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def report() -> str:
    from poker_training_bot.solver_artifacts import vocabulary_report

    return vocabulary_report.render_spot_vocabulary_report()


REPORT_EXAMPLE_KEY = "t6/d100/BB/BTN:raise@2.5"
"""The spot `vocabulary_report._key_examples` works through, and the one thing a chart cutover
breaks outright: the module raises `VocabularyReportError` when the library stops declaring
it, which exits `generate_spot_vocabulary_report` non-zero - a completed phase's gate command.
Authored as the retired `t6/d100/BTN/CO:raise@2.5`, so this key is the substitution stage 6
owes it; checked against a walk of the export, it is one of the 86."""


def report_row(report: str, label: str, value_prefix: str = "") -> str:
    """What the report prints after `label`, on the one indented row beginning with it.

    Every figure and key the report states as a claim sits on an indented row, and the prose
    around them is flush left. Read from anywhere else a claim proves nothing: `key in report`
    is satisfied by the key-mapping table, a bare figure by any number of the same digits.
    `value_prefix` narrows the match where the label is an ordinary English word - "before"
    and "after" head the worked example's two rows, and stage 6 rewrites that section, so any
    indented prose row it adds beginning with either word would be a false red."""
    indented = [row.strip() for row in report.splitlines() if row.startswith(" ")]
    rows = [
        row
        for row in indented
        if row.startswith(label) and row[len(label) :].strip().startswith(value_prefix)
    ]

    assert len(rows) == 1, f"{label!r} begins {len(rows)} rows of the report, not one"
    return rows[0][len(label) :].strip()


def report_figure(report: str, label: str) -> int:
    """The single number the report prints on that row."""
    figures = report_row(report, label).split()

    assert len(figures) == 1, f"{label!r} carries {len(figures)} figures, not one"
    return int(figures[0].replace(",", ""))


def test_the_report_shows_a_key_before_and_after(report) -> None:
    """Read off the worked example's own two rows. As `REPORT_EXAMPLE_KEY in report` it passed
    while `_key_examples` still worked through the retired `t6/d100/BTN/CO:raise@2.5`, matching
    a key-mapping row instead. The two rows differ only by the `@2.5`, so both are asserted."""
    assert report_row(report, "after", "t6/d100/") == REPORT_EXAMPLE_KEY
    assert report_row(report, "before", "t6/d100/") == REPORT_EXAMPLE_KEY.split("@")[0]


def test_the_worked_example_is_a_spot_the_committed_chart_declares(library) -> None:
    """Deliberately without the `report` fixture: it is module-scoped, so a retired example
    raises at setup rather than failing here."""
    assert REPORT_EXAMPLE_KEY in set(library.spot_keys())


def test_the_report_shows_a_four_bet_key_that_could_not_be_written_before(
    report, library
) -> None:
    # The 8 and 21.5 are prices no committed spot holds, which is not a defect:
    # `_key_examples` builds this key and never checks it, so it demonstrates the grammar
    # rather than claiming coverage. What the chart owes past it is that it uses that
    # grammar - a repeated seat.
    example = report_row(report, "could not be written before")

    assert example == "t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5"

    entries = [key.split("/")[-1].split(",") for key in library.spot_keys()]

    assert any(len({entry.split(":")[0] for entry in row}) < len(row) for row in entries)


def test_the_report_publishes_the_measured_spot_counts(report) -> None:
    """The roadmap's 1,691 and 848 do not reproduce; enumerating spot_key gives these, checked
    against `vocabulary_measures.expressible_spots` before they were pinned.
    ROADMAP-SPOT-COUNTS-DO-NOT-REPRODUCE owns correcting the documents."""
    assert report_row(report, "v1, one orbit only").split() == ["1,949", "977"]


def test_the_report_carries_the_price_substitution_census(report, comparison) -> None:
    """Split by whether the substituted raise was the open or a later one, so the cost of
    ruling 8 stays separable from the cost of extending it past the open. Phase 12 pinned 72
    here, the three-bet decisions the extension buys, and the cutover moves that count.

    Recomputed from the rows rather than loosened to a keyword: a substring test on
    "substitution" and "open" cannot fail while the section heading exists.
    `ComparisonRow.price_substitutions` carries the raise index, and index 0 is the open."""
    answered = [row for row in comparison.rows if row.refusal is None]
    moved = [row.price_substitutions for row in answered if row.price_substitutions]
    opener = sum(1 for subs in moved if any(index == 0 for index, _, _ in subs))
    later = sum(1 for subs in moved if any(index > 0 for index, _, _ in subs))
    both = sum(
        1 for subs in moved if any(i == 0 for i, _, _ in subs) and any(i > 0 for i, _, _ in subs)
    )

    assert opener and later, "one side of the split is empty, so it separates nothing"
    assert report_figure(report, "the opener's price was moved") == opener
    assert report_figure(report, "a later raise's price was moved") == later
    assert report_figure(report, "both, counted once in each line above") == both


def test_the_report_states_the_refusal_total_it_measured(report, comparison) -> None:
    """Phase 12 asserted 290 at its branch point; the cutover moves it up, which the contract
    requires, so the total is confined against the baseline and against what the report states.
    `str(refused) in report` passed off the restatement table's carried-over `refusals` row."""
    refused = sum(1 for row in comparison.rows if row.refusal is not None)

    assert refused > BASELINE_REFUSALS
    assert report_figure(report, "total refusals over the committed sample") == refused


def test_the_report_restates_the_phase_eleven_numbers_with_a_cause(report, comparison) -> None:
    """Every number the Phase 07 and Phase 08 packets quote, labelled with a cause. Read off
    the restatement's own row, whose columns are the packet's figure, the branch point's and
    this run's. `"3048" in report` was satisfied by the header, which gives no cause."""
    row = report_row(report, "preflop decision points").split()

    assert "phase 11" in report.lower()
    assert row[:3] == [str(len(comparison.rows))] * 3
    assert "unchanged" in row
