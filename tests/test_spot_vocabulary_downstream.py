"""Phase 12: what the widened spot key changes downstream of the key itself.

The companion to `tests/test_spot_vocabulary.py`, split from it at the 700-line cap. That
file pins what a key can say; this one pins what the repo does once it can say it: the price
normaliser, the query and answer that carry a size and a substitution, and the corpus
measurements the vocabulary moves. The report a person reads was split off the same way and
is `tests/test_spot_vocabulary_report.py`. All three run under `pytest_spot_vocabulary`.
`ChartHit.price_substitutions` is `(sequence index, asked, answered)` per substituted raise,
empty when every price was exact.
"""

from __future__ import annotations

import hashlib
import json

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
REPO_ROOT = ARTIFACT_DIR.parents[2]
"""`data/artifacts/preflop` up to the checkout root. Derived rather than imported from
`scripts.repo_paths`, which is not on the path when this file is run on its own."""


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


def solved_line(library, hero: str, *raisers: str) -> tuple:
    """`hero`'s line where each seat raises at the price the chart solved there. `add_allin:
    false`, so each point offers one named raise and `min` is picking out of a single price."""
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
    """Ruling 8, measured: 80.8 percent of the corpus faced 2.25 or less. Read on the big blind
    facing a button open, one of the fifteen (opener, hero) pairs the cutover covers. The prices
    are read back rather than assumed, because a spot that already solved 2.25 would substitute
    nothing and still pass."""
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
    """Authored when the tree carried two opening prices, so a constant was already wrong. The
    rake-free solve opens everyone to 2.5 and that instance is gone; the claim is not. One
    sequence still carries an opening and a three-bet price no single constant can serve, and a
    normaliser reading one answers a three-bet at the opening price.

    The four-bet rung went with the family rather than with the ladder. 22.5 is what hero raises
    TO facing a three-bet, so it lives in the sizing table; a key naming it is hero facing a
    four-bet, which is three raises in and outside the raise-depth clause. That no committed key
    holds one is asserted here, because a normaliser left holding a stale 22.5 candidate would
    substitute a corpus four-bet into a spot the chart does not declare."""
    ladder = solved_line(library, "LJ", "LJ", "BTN")
    prices = [entry.size_bb for entry in ladder]

    assert len(set(prices)) == 2
    assert prices[0] < prices[1]
    for index, entry in enumerate(ladder):
        offered = library.solved_prices_bb(TABLE, DEPTH, "LJ", ladder[:index], entry.position)

        assert entry.size_bb in offered, index
        assert prices[0] not in offered or index == 0, index

    assert [key for key in library.spot_keys() if "@22.5" in key] == []


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

    A reader of a corpus key's shape, and no longer a filter: decision 40 dropped the
    opponent-investment clause as strictly weaker than exposure and the contract forbids
    reinstating it. The blinds are not in a key, so nothing is subtracted for them."""
    hero, entries = spot_shape(spot_key_text)
    return len({entry.split(":")[0] for entry in entries} - {hero})


RULED_PRICES = frozenset({2.5, 7.5, 22.5})
"""Every raise-to price the solved tree holds. None of the retired chart's 3.5, 8, 10.5, 11 or
13.5 survives, so a key carrying one of those is a key answered off the chart this phase
deletes, and the 100bb jam went with `add_allin: false`."""


def prices_in(spot_key_text: str) -> frozenset[float]:
    """Every raise-to price a key names, empty for an opening spot."""
    entries = spot_key_text.split("/")[-1].split(",")
    return frozenset(float(entry.split("@")[1]) for entry in entries if "@" in entry)


def raises_in(spot_key_text: str) -> int:
    """How many raises a key records in front of hero, which is the raise-depth clause."""
    return spot_key_text.split("/")[-1].count(":raise")


def acts_twice(spot_key_text: str) -> bool:
    """A second-orbit key: some seat is recorded acting more than once."""
    return any(spot_key_text.count(f"{seat}:") > 1 for seat in SEATS_IN_ACTION_ORDER)


RETIRED_CHART_PATH = "data/artifacts/preflop/six_max_100bb_rakefree.json"
RETIRED_CHART_SHA256 = "0111b5c943b5bcfc836ef656603970ab31fa99befe915a2970ab1f3e8d7c5c3f"
RETIRED_CHART_SPOTS = 86
RETIRED_CHART_SPOT_IDS = tuple(
    """
t6/d100/BB/BTN:raise@100 t6/d100/BB/BTN:raise@2.5
t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@100
t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5 t6/d100/BB/CO:raise@100
t6/d100/BB/CO:raise@2.5 t6/d100/BB/CO:raise@2.5,BB:raise@7.5,CO:raise@100
t6/d100/BB/CO:raise@2.5,BB:raise@7.5,CO:raise@22.5 t6/d100/BB/HJ:raise@100 t6/d100/BB/HJ:raise@2.5
t6/d100/BB/HJ:raise@2.5,BB:raise@7.5,HJ:raise@100
t6/d100/BB/HJ:raise@2.5,BB:raise@7.5,HJ:raise@22.5 t6/d100/BB/LJ:raise@100 t6/d100/BB/LJ:raise@2.5
t6/d100/BB/LJ:raise@2.5,BB:raise@7.5,LJ:raise@100
t6/d100/BB/LJ:raise@2.5,BB:raise@7.5,LJ:raise@22.5 t6/d100/BB/SB:raise@100 t6/d100/BB/SB:raise@2.5
t6/d100/BB/SB:raise@2.5,BB:raise@7.5,SB:raise@100
t6/d100/BB/SB:raise@2.5,BB:raise@7.5,SB:raise@22.5 t6/d100/BTN/BTN:raise@2.5,BB:raise@100
t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5
t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5,BB:raise@100
t6/d100/BTN/BTN:raise@2.5,SB:raise@100 t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5
t6/d100/BTN/BTN:raise@2.5,SB:raise@7.5,BTN:raise@22.5,SB:raise@100
t6/d100/BTN/CO:raise@2.5,BTN:raise@7.5,CO:raise@100
t6/d100/BTN/CO:raise@2.5,BTN:raise@7.5,CO:raise@22.5
t6/d100/BTN/HJ:raise@2.5,BTN:raise@7.5,HJ:raise@100
t6/d100/BTN/HJ:raise@2.5,BTN:raise@7.5,HJ:raise@22.5
t6/d100/BTN/LJ:raise@2.5,BTN:raise@7.5,LJ:raise@100
t6/d100/BTN/LJ:raise@2.5,BTN:raise@7.5,LJ:raise@22.5 t6/d100/CO/CO:raise@2.5,BB:raise@100
t6/d100/CO/CO:raise@2.5,BB:raise@7.5
t6/d100/CO/CO:raise@2.5,BB:raise@7.5,CO:raise@22.5,BB:raise@100
t6/d100/CO/CO:raise@2.5,BTN:raise@100 t6/d100/CO/CO:raise@2.5,BTN:raise@7.5
t6/d100/CO/CO:raise@2.5,BTN:raise@7.5,CO:raise@22.5,BTN:raise@100
t6/d100/CO/CO:raise@2.5,SB:raise@100 t6/d100/CO/CO:raise@2.5,SB:raise@7.5
t6/d100/CO/CO:raise@2.5,SB:raise@7.5,CO:raise@22.5,SB:raise@100
t6/d100/CO/HJ:raise@2.5,CO:raise@7.5,HJ:raise@100
t6/d100/CO/HJ:raise@2.5,CO:raise@7.5,HJ:raise@22.5
t6/d100/CO/LJ:raise@2.5,CO:raise@7.5,LJ:raise@100
t6/d100/CO/LJ:raise@2.5,CO:raise@7.5,LJ:raise@22.5 t6/d100/HJ/HJ:raise@2.5,BB:raise@100
t6/d100/HJ/HJ:raise@2.5,BB:raise@7.5
t6/d100/HJ/HJ:raise@2.5,BB:raise@7.5,HJ:raise@22.5,BB:raise@100
t6/d100/HJ/HJ:raise@2.5,BTN:raise@100 t6/d100/HJ/HJ:raise@2.5,BTN:raise@7.5
t6/d100/HJ/HJ:raise@2.5,BTN:raise@7.5,HJ:raise@22.5,BTN:raise@100
t6/d100/HJ/HJ:raise@2.5,CO:raise@100 t6/d100/HJ/HJ:raise@2.5,CO:raise@7.5
t6/d100/HJ/HJ:raise@2.5,CO:raise@7.5,HJ:raise@22.5,CO:raise@100
t6/d100/HJ/HJ:raise@2.5,SB:raise@100 t6/d100/HJ/HJ:raise@2.5,SB:raise@7.5
t6/d100/HJ/HJ:raise@2.5,SB:raise@7.5,HJ:raise@22.5,SB:raise@100
t6/d100/HJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@100
t6/d100/HJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@22.5 t6/d100/LJ/LJ:raise@2.5,BB:raise@100
t6/d100/LJ/LJ:raise@2.5,BB:raise@7.5
t6/d100/LJ/LJ:raise@2.5,BB:raise@7.5,LJ:raise@22.5,BB:raise@100
t6/d100/LJ/LJ:raise@2.5,BTN:raise@100 t6/d100/LJ/LJ:raise@2.5,BTN:raise@7.5
t6/d100/LJ/LJ:raise@2.5,BTN:raise@7.5,LJ:raise@22.5,BTN:raise@100
t6/d100/LJ/LJ:raise@2.5,CO:raise@100 t6/d100/LJ/LJ:raise@2.5,CO:raise@7.5
t6/d100/LJ/LJ:raise@2.5,CO:raise@7.5,LJ:raise@22.5,CO:raise@100
t6/d100/LJ/LJ:raise@2.5,HJ:raise@100 t6/d100/LJ/LJ:raise@2.5,HJ:raise@7.5
t6/d100/LJ/LJ:raise@2.5,HJ:raise@7.5,LJ:raise@22.5,HJ:raise@100
t6/d100/LJ/LJ:raise@2.5,SB:raise@100 t6/d100/LJ/LJ:raise@2.5,SB:raise@7.5
t6/d100/LJ/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5,SB:raise@100
t6/d100/SB/BTN:raise@2.5,SB:raise@7.5,BTN:raise@100
t6/d100/SB/BTN:raise@2.5,SB:raise@7.5,BTN:raise@22.5
t6/d100/SB/CO:raise@2.5,SB:raise@7.5,CO:raise@100
t6/d100/SB/CO:raise@2.5,SB:raise@7.5,CO:raise@22.5
t6/d100/SB/HJ:raise@2.5,SB:raise@7.5,HJ:raise@100
t6/d100/SB/HJ:raise@2.5,SB:raise@7.5,HJ:raise@22.5
t6/d100/SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@100
t6/d100/SB/LJ:raise@2.5,SB:raise@7.5,LJ:raise@22.5 t6/d100/SB/SB:raise@2.5,BB:raise@100
t6/d100/SB/SB:raise@2.5,BB:raise@7.5
t6/d100/SB/SB:raise@2.5,BB:raise@7.5,SB:raise@22.5,BB:raise@100 t6/d100/SB/rfi
""".split()
)
"""The chart this phase retires, generated from it and carried here rather than read at a git pin.

**Not read off `ARTIFACT_DIR` at test time, because stage 6 replaces that path in place**: a helper
reading the working tree would return the committed 249 the moment the cutover lands, and every
cost below would be the new chart compared against itself - green, and measuring nothing.

**And not out of git history either, because no git object survives this lane's workflow.** Commit
`db08304538c26361f3e692230e8cb544a9bf91c0` is reachable from one unpushed local branch, and
`AGENTS.md` has this lane rebase onto `main` whenever a sibling merges, which rewrites it and takes
the pin with it - permanently, and after stage 5 froze this file. Blob
`9bde32b4631d6c266b521b4b4c90653126a7d587` survives a rebase, content addressing being what it is,
but a blob no reachable commit names is a garbage-collection candidate, so it trades a certain
failure for a slower one. A tuple in a frozen test depends on no object, ref, remote or clone depth.

**What that costs is a copy, the shape that produced the defect this replaces**, so the copy is
generated rather than typed and is checked against its source while that source is on disk.
`RETIRED_CHART_SHA256` is the sha256 of that file's bytes - blob `9bde32b`, byte-identical to the
pin - and `test_the_retired_chart_fixture_agrees_with_its_source` compares the two every run, both
ways. Regenerate the pair together: hash the file, sort the `spot_id` of every entry in its `spots`.
86 is decision 53's count and is asserted on every read, so a fixture that lost an entry fails here
rather than as a wrong cost downstream - the hardcoded shape list this replaces went on describing
the 36-spot chart deleted at `a386c77`, the very commit that introduced the 86 it stood in for."""


def retired_chart_spot_ids() -> tuple[str, ...]:
    """Every spot id the retired chart declares, sorted, generated rather than transcribed."""
    assert len(RETIRED_CHART_SPOT_IDS) == RETIRED_CHART_SPOTS, (
        f"the fixture holds {len(RETIRED_CHART_SPOT_IDS)} spots, not {RETIRED_CHART_SPOTS}"
    )
    assert len(set(RETIRED_CHART_SPOT_IDS)) == RETIRED_CHART_SPOTS, "the fixture repeats a spot id"
    return RETIRED_CHART_SPOT_IDS


def retired_chart_on_disk() -> tuple[str, ...]:
    """The spot ids at `RETIRED_CHART_PATH` right now, empty if nothing is there to read."""
    source = REPO_ROOT / RETIRED_CHART_PATH
    if not source.exists():
        return ()
    document = json.loads(source.read_text(encoding="utf-8"))
    return tuple(sorted(spot["spot_id"] for spot in document["spots"]))


def test_the_retired_chart_fixture_agrees_with_its_source() -> None:
    """The fixture is a copy, so it is compared against the file it came from, both ways.

    While `RETIRED_CHART_PATH` still holds the retired chart - which its sha256 decides, not its
    name - the ids must match. Once stage 6 writes the 249 there the bytes change and the ids must
    then differ, which is the same claim read the other way and is what stops a stale checksum
    passing quietly. Neither branch skips, so this never goes dormant."""
    source = REPO_ROOT / RETIRED_CHART_PATH
    digest = hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else ""

    if digest == RETIRED_CHART_SHA256:
        assert retired_chart_on_disk() == retired_chart_spot_ids(), (
            f"{RETIRED_CHART_PATH} is still the retired chart and the fixture no longer matches it"
        )
    else:
        assert retired_chart_on_disk() != retired_chart_spot_ids(), (
            f"{RETIRED_CHART_PATH} declares exactly the fixture's 86 ids but hashes to"
            f" {digest or 'nothing'}, not {RETIRED_CHART_SHA256}, so the checksum is stale"
        )


def retired_chart_shapes() -> frozenset[tuple[str, tuple[str, ...]]]:
    """The retired chart under the **shape** reading: its 86 keys reduce to 51 shapes.

    Fewer than 86 because 35 of the 51 are declared twice, the second copy pricing the last
    raise as the 100bb jam - the superseded export's mark, all 36 of its sizing entries
    offering that jam. Every figure below says which reading it is under, the key reading
    giving a different set of the same size."""
    return frozenset(spot_shape(spot_id) for spot_id in retired_chart_spot_ids())


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


def test_the_second_orbit_rows_are_refused_by_name_rather_than_as_a_catch_all(
    comparison, library
) -> None:
    """Phase 12 gave these 19 decision points a key and left them uncovered, expecting phase 14
    to fill them. It does the opposite, and that is the ruling rather than a regression: the
    raise-depth clause commits nothing past two raises in, so no committed key names a seat
    twice and every four-bet-and-beyond continuation is refused. `CHART-COVERAGE-EXPANSION` is
    restated with its node count and a route back, not closed.

    What phase 12 bought survives and is the whole claim here. Each of the 19 is refused **by
    name**: before the widened key they were the inventory's catch-all row, 19 points naming no
    cell anybody could fill. The nearest-spot guard rides along - none may reach a shape the
    chart holds at another price - and the inventory is held to the rows it counts, because
    `InventoryEntry` carries no code and a hand-class refusal at a covered spot would otherwise
    arrive there wearing a covered shape and read as absent coverage."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    second_orbit = [row for row in keyed_rows(comparison) if acts_twice(row.asked_spot_key)]
    inventory = [
        entry for entry in comparison.refusal_inventory if acts_twice(entry.spot_key)
    ]

    assert len(second_orbit) == 19
    assert [key for key in library.spot_keys() if acts_twice(key)] == []
    assert sum(entry.count for entry in inventory) == len(second_orbit)
    for row in second_orbit:
        assert row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key
        assert spot_shape(row.asked_spot_key) not in covered, row.asked_spot_key


def test_the_corpus_keeps_its_sample(comparison) -> None:
    """A changed denominator means the replay changed, which this phase does not do."""
    assert comparison.hands_compared == 499
    assert len(comparison.rows) == 3048


def test_every_refusal_names_a_spot_key(comparison) -> None:
    """271 of the 290 refusals carried a key at the branch point; the missing 19 were the
    catch-all, and a refusal with no key names no cell anybody could fill."""
    keyless = [row for row in comparison.rows if row.refusal is not None and not row.spot_key]
    assert keyless == []


def test_the_two_raise_decisions_split_where_the_ruling_puts_them(comparison, library) -> None:
    """Phase 12 pinned 132 refusals here; the 2026-08-25 predicate inverted it onto the squeezes,
    and decision 40 has since dropped the clause that did the inverting. So the split of the
    corpus stays - 204 two-raise decisions, 125 with two opponents invested, 79 heads-up, all
    three read off the corpus's own key shapes and unmoved by any chart - and what each side owes
    is restated against the 249.

    The heads-up family must be answered, at the derived prices: every price in one of those keys
    is one of the three the tree holds, so a build keeping a retired 8, 11 or 13.5 three-bet fails
    here, and every such key is one the library declares, so a normaliser landing between two
    committed spots fails too.

    The squeeze family is no longer refused wholesale and is not asserted to be. That reader was
    the retired history clause and decision 40 dropped it as strictly weaker than exposure; the
    contract forbids reinstating it. What is asserted instead is the two clauses a key *can* carry.
    At most two raises are in - which is what retires every four-bet key - and hero is never the big
    blind with a cold caller in front, which is decision 48's ten. The nearest-spot guard moves to
    the family that is still ruled out to the last row: anything with three or more raises in.
    """
    covered = {spot_shape(key) for key in library.spot_keys()}
    declared = set(library.spot_keys())
    two_raise = [
        row
        for row in keyed_rows(comparison)
        if raises_in(row.asked_spot_key) == 2 and not acts_twice(row.asked_spot_key)
    ]
    squeezes = [row for row in two_raise if opponents_invested(row.asked_spot_key) >= 2]
    heads_up = [row for row in two_raise if opponents_invested(row.asked_spot_key) == 1]
    beyond = [row for row in keyed_rows(comparison) if raises_in(row.asked_spot_key) >= 3]

    assert (len(two_raise), len(squeezes), len(heads_up)) == (204, 125, 79)
    assert {key for key in declared if key.endswith("/rfi")} == {
        f"t6/d{DEPTH}/{seat}/rfi" for seat in ("LJ", "HJ", "CO", "BTN", "SB")
    }

    for key in declared:
        assert raises_in(key) <= 2, key
        assert not (key.split("/")[2] == "BB" and ":call" in key), key
    assert beyond, "no corpus decision past two raises, so the clause below is untested"
    for row in beyond:
        assert row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key
        assert spot_shape(row.asked_spot_key) not in covered, row.asked_spot_key
    for row in heads_up:
        assert row.asked_spot_key in declared, row.asked_spot_key
        assert prices_in(row.asked_spot_key) <= RULED_PRICES, row.asked_spot_key
        assert row.miss_code != lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key


def test_the_refusal_total_moved_only_where_the_ruling_gave_a_spot_up(
    comparison, library
) -> None:
    """Phase 12 pinned 290 because it added no coverage and a drop would have been a finding.
    Phase 14 moves the total a long way in **both** directions and the contract expects that: the
    chart answers 249 nodes where the retired one declared 86 keys, and it gives the whole
    four-bet family up. No ruling fixes where the two land, so a direction asserted here would be
    a guess dressed as a check, and the total is neither pinned nor bounded.

    What the number was standing in for is asserted instead, and it is the stronger half: what
    the cutover costs a trainee, measured against the chart actually being replaced.

    **Under the shape reading**, the retired 51 split 21 kept and 30 given up, and the 30 are
    exactly the four-bet family - every retired shape with three or more raises in front of hero,
    which is the raise-depth clause and nothing else. So the give-up is asserted as that
    characterisation rather than as a bare 30 a converter could match by dropping the wrong
    thirty. Nothing among the 21 kept may be refused for want of a spot, and each of the 15
    corpus decisions that reach one of the 30 must be - a count measured off the corpus's own
    key shapes, so it moves only if the replay does.

    **Under the key reading** the ledger balances on the 86: 21 retired ids are literally
    committed keys, 65 are refused, 228 keys are new, and 21 + 228 is the 249. That both readings
    produce 21 is coincidence and the sets differ - 41 of the 86 have a committed *shape* - so
    both are stated and neither figure is ever quoted for the other."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    declared = set(library.spot_keys())
    retired_ids = retired_chart_spot_ids()
    retired = retired_chart_shapes()
    given_up = retired - covered
    kept = retired & covered
    committed_ids = [key for key in retired_ids if key in declared]

    assert len(retired) == 51
    assert given_up == {spot_shape(key) for key in retired_ids if raises_in(key) >= 3}
    assert (len(kept), len(given_up)) == (21, 30)

    assert (len(committed_ids), len(retired_ids) - len(committed_ids)) == (21, 65)
    assert len(declared - set(retired_ids)) == 228
    assert len(committed_ids) + 228 == len(declared) == 249
    assert len([key for key in retired_ids if spot_shape(key) in covered]) == 41

    refused = [row for row in comparison.rows if row.refusal is not None]
    at_the_cost = [
        row for row in keyed_rows(comparison) if spot_shape(row.asked_spot_key) in given_up
    ]

    assert len(at_the_cost) == 15
    for row in at_the_cost:
        assert row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED, row.asked_spot_key
    for row in refused:
        if row.miss_code == lookup_module.MISS_SPOT_NOT_COVERED:
            assert spot_shape(row.spot_key) not in kept, row.spot_key


def test_no_limped_pot_is_answered_from_a_neighbouring_cell(comparison, library) -> None:
    """Phase 12's nearest-spot guard, on the one family with no cell in either chart: nobody
    limps in a `limp: false` tree, so a limped decision that gets answered was answered from a
    neighbour. That subject is preserved here rather than repurposed.

    What this test believed on arrival was that the retired chart declared `t6/d100/BB/SB:call`
    and answered 30 of these 52 from it, making the limped pot the cutover's measured cost. False
    of the chart being retired: the 86-spot chart holds **no** `:call` key at all - asserted here
    rather than taken on trust - so it answers none of the 52 today and the cutover neither gains
    nor loses a limped decision. That cell belonged to the 36-spot GTO Wizard chart deleted
    before this phase restarted. `CHART-CANNOT-ANSWER-A-LIMPED-POT` therefore stays a guard
    instead of becoming a claim about a cost, and the contract moves it to phase 17 rather than
    closing it. Both charts are held to it, one by key and one by shape."""
    covered = {spot_shape(key) for key in library.spot_keys()}
    limped = [
        row
        for row in keyed_rows(comparison)
        if row.asked_spot_key.split("/")[-1].split(",")[0].endswith(":call")
    ]

    assert len(limped) == 52
    assert [row for row in limped if row.refusal is None] == []
    assert [key for key in retired_chart_spot_ids() if ":call" in key] == []
    assert [shape for shape in covered if shape[1] and shape[1][0].endswith(":call")] == []


# --------------------------------------------------------------------------- #
# What the strategy puts on its answer
# --------------------------------------------------------------------------- #


def test_the_strategy_reports_a_substituted_price_on_its_decision(strategy) -> None:
    """The cheapest measurement of what ruling 8 costs in play, and it has to be on the answer or
    no report can split on it. Authored on a small blind five-bet jam over hero's three-bet, which
    the raise-depth clause now refuses along with the rest of the four-bet family; the line moves
    back to the open it was always measuring. The substituted price is still 2.25, the corpus
    median, and the spot it lands on is the big blind facing a small blind open - one of the five
    the big blind keeps fold, call and three-bet at - so the substitution is read off a decision
    rather than off a refusal that would carry no detail at all."""
    # Seats 0 to 3 folded. The small blind (seat 4) opened to 225 and hero (seat 5) is in for the
    # big blind. Every seat started on 10,000, so the table is flat at 100bb.
    contributed = {4: 225, 5: 100}
    query = contract_module.StrategyQuery(
        hand_id="h1",
        street="preflop",
        seat=5,
        button_seat=3,
        hole_cards=("As", "Kd"),
        board=(),
        legal_actions=("fold", "call", "raise"),
        to_call=125,
        current_bet=225,
        # The small blind raised by 125 over the big blind, so the standing minimum re-raise is
        # 350. Hero can pay it, which is what leaves a raise on the menu.
        min_raise_target=350,
        pot=325,
        seat_states=tuple(
            contract_module.SeatState(
                seat=seat,
                street_bet=contributed.get(seat, 0),
                committed_total=contributed.get(seat, 0),
                folded=seat in (0, 1, 2, 3),
                all_in=False,
            )
            for seat in range(6)
        ),
        stacks=tuple((seat, 10000 - contributed.get(seat, 0)) for seat in range(6)),
        blinds=(50, 100),
        preflop_actions=(contract_module.SeatAction(4, "raise", 225),),
    )
    outcome = strategy.decide(query)
    assert isinstance(outcome, contract_module.StrategyDecision)
    assert outcome.detail == (("price_substitution_0", "2.25->2.5"),)
