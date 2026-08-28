"""The committed chart itself, not synthetic fixtures.

These tests stop `data/artifacts/preflop/` drifting away from the export that produced it. The
hand-authored chart is gone, and phase 14 replaced the raked GTO Wizard chart with one derived from
the rake-free GTOpen solve, so nothing here spells a raise price. **The ruled predicate moved what
the bot can be asked**: keep a node when at most one opponent has voluntarily invested beyond the
blinds *and* at most two players are still live, 86 of 38,828, so the bot opens from one seat and
faces a single open from one, and four opening ranges it answers today become refusals (Taylor,
2026-08-25). Every claim about those spots is kept as the refusal it became rather than deleted: a
converter built on either clause alone commits them again and they convert, import, key legally and
answer, so only an assertion that the keys are absent tells the predicates apart. "Later position
opens wider" is a property of the solve now and is measured over the export; big-blind defence
stays on the chart.
"""

from __future__ import annotations

import subprocess
from collections import Counter

import pytest

from poker_training_bot.solver_artifacts.gtopen_config import RULED_CONFIG
from poker_training_bot.solver_artifacts.gtopen_expectations import (
    EXPECTATIONS_PATH,
    Aggregates,
    aggregate_frequencies,
    load_expectations,
    ordering_errors,
)
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    SolverExport,
    load_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction, weights_checksum
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
RETIRED_ARTIFACT = ARTIFACT_DIR / "six_max_nl25_100bb.json"
RETIRED_SIZINGS = ARTIFACT_DIR / "sizings" / "six_max_nl25_100bb.json"

DEPTH_BB = 100

SB_OPEN = "t6/d100/SB/rfi"
"""The one opening range the predicate commits, and the only `/rfi` key among the 86. Walked over
the export: exactly one selected node has an empty action sequence and it is the small blind's,
every other seat's first-in node having two or more players live behind it."""

REFUSED_OPENS = ("LJ", "HJ", "CO", "BTN")
"""The four opening ranges the cutover gives up - four of the fourteen retired spots the
predicate drops, and the sharpest single statement of what the ruling cost.
"""

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
OPENING_ORDER = ("LJ", "HJ", "CO", "BTN")

SPOTS_OFFERING_TWO_PRICES = 21
SPOTS_OFFERING_ONE_PRICE = 15
SPOTS_OFFERING_NO_RAISE = 50
"""How the 86 split by what hero may put in, walked over the committed export: 20 offer a named
raise and a jam beside a call, one offers a raise and a jam with no call - the small blind's open
- and 15 offer a jam with no named raise. The other 50 offer fold and call, so there is nothing
to price."""

TWO_PRICE_CELLS = 531
ONE_PRICE_CELLS = 1688
UNPRICED_CELLS = 4893
JAM_ONLY_CELLS = 693
"""And how the 7,112 cells those spots declare split, ruled per hand class on 2026-08-26: 531
classes offer two prices, 1,688 one and 4,893 none, and 693 of the priced ones sit at the 15
jam-only spots. A class is declared where it reaches the spot, so the 11 full-reach spots declare
all 169 and the rest declare hero's arriving range."""


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


@pytest.fixture(scope="module")
def committed_export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


def solved_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[PreflopAction, ...]:
    """`hero`'s line where each named seat raises at the price the chart solved there.

    Each raising point offers two prices - the named raise and the all-in - so the named raise is
    the smaller, and reading both out of the artifact lets a re-solve move these fixtures with it.
    It still works for a line the chart *refuses*, which the refusal tests depend on: a refused
    query is still priced from the chart and misses anyway, so nothing about the price refused it.
    """
    sequence: list[PreflopAction] = []
    for raiser in raisers:
        prices = library.solved_prices_bb(6, DEPTH_BB, hero, tuple(sequence), raiser)
        assert prices, (hero, raiser, tuple(sequence))
        sequence.append(PreflopAction(raiser, "raise", min(prices)))
    return tuple(sequence)


def solved_key(library: PreflopChartLibrary, hero: str, *raisers: str) -> str:
    return derive_spot_key(6, DEPTH_BB, hero, solved_line(library, hero, *raisers))


def test_committed_artifact_imports() -> None:
    artifacts = import_preflop_artifacts(ARTIFACT_DIR)

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.table_size == 6
    assert artifact.stack_depth_bb == 100
    assert artifact.source.kind == "solver-export"
    assert artifact.audit_fields.spot_count == len(artifact.spots)
    # The retired chart held 36 spots; the 86 is a tree fact `test_derived_chart.py` pins, so
    # only the aggregate direction is pinned here. It is not a coverage gain everywhere: 14
    # spots the bot answers today are refused after the cutover, asserted individually below.
    assert len(artifact.spots) > 36


def test_the_artifact_declares_the_blind_structure_it_was_solved_at() -> None:
    """Decision 4: the chart was solved at 0.5/1 with no ante. Without it the same hand at the same
    depth in a 1/3 game reads as a solved spot and nothing notices - phase 13's largest finding."""
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert artifact.blind_structure.small_blind_bb == pytest.approx(0.5)
    assert artifact.blind_structure.big_blind_bb == pytest.approx(1.0)
    assert artifact.blind_structure.ante_bb == pytest.approx(0.0)


def test_the_retired_raked_chart_is_gone_from_the_artifact_directory() -> None:
    """Absence of a key collision is not retirement. The retired chart three-bets to 8, 11 and 13.5
    and opens the small blind to 3.5 against the export's 7.5 and 2.5, so 17 of its 36 keys collide
    with nothing the new artifact declares: `PreflopChartLibrary` would build clean with both
    loaded and the bot would answer three-bets and small-blind opens from raked ranges while
    believing it plays the rake-free solve."""
    assert not RETIRED_ARTIFACT.exists()
    assert not RETIRED_SIZINGS.exists()


def test_committed_artifact_checksum_covers_its_weights() -> None:
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert weights_checksum(artifact.action_weights) == artifact.audit_fields.weights_sha256


def test_committed_file_reproduces_from_its_source_export() -> None:
    """The export is the source of truth; the artifact is its output."""
    result = subprocess.run(
        ["python", str(REPO_ROOT / "scripts" / "convert_preflop_export.py"), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_provenance_names_the_export_it_came_from() -> None:
    """The one committed artifact points at the one committed export, by path - asserted against
    `COMMITTED_EXPORT_PATH` rather than a spelled filename, which is the contract's criterion."""
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert (REPO_ROOT / artifact.source.reference) == COMMITTED_EXPORT_PATH
    assert COMMITTED_EXPORT_PATH.exists()


@pytest.mark.parametrize(
    ("hand_class", "expected"),
    [
        ("AA", "raise"),
        ("ATo", "raise"),
        ("A5o", "raise"),
        ("72o", "fold"),
        ("32o", "fold"),
    ],
)
def test_known_small_blind_opening_entries(
    library: PreflopChartLibrary, hand_class: str, expected: str
) -> None:
    """Hands whose correct action is not a judgement call, from the one seat that opens. This was
    two tests, over the lojack's open and the button's, and both are refusals now; A5o and ATo were
    the button's cases and are still pure opens from the small blind. What did not transfer is the
    lojack's K4s fold: the lojack opens about a fifth of hands with four seats behind it, while the
    small blind opens 54 percent against one opponent with half a blind in and raises K4s 99.97
    percent of the time. 72o and 32o survive the move: folds in any solve of this game."""
    weights = library.artifacts[0].weights_for(SB_OPEN, hand_class)

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


@pytest.mark.parametrize(("hand_class", "expected"), [("AA", "raise"), ("72o", "fold")])
def test_known_big_blind_defence_entries(
    library: PreflopChartLibrary, hand_class: str, expected: str
) -> None:
    """The big blind facing a cutoff open, at whatever price the cutoff was solved at."""
    weights = library.artifacts[0].weights_for(
        solved_key(library, "BB", "CO"), hand_class
    )

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


def test_first_orbit_spots_cover_all_169_classes(library: PreflopChartLibrary) -> None:
    """Hero has not acted, so every hand is possible and must be answered. Eleven of the 86 are at
    full reach and they are exactly the spots where hero has not yet acted: the small blind's open,
    and the big blind facing each of the five openers at each of the two prices an opener offers."""
    for spot_id in (SB_OPEN, solved_key(library, "BB", "CO")):
        assert len(library.hand_classes_for(spot_id)) == 169, spot_id


def test_a_spot_where_hero_already_acted_covers_only_heros_range(
    library: PreflopChartLibrary,
) -> None:
    """A hand the lojack would never open is not a lookup it can make, and committing a strategy for
    a holding hero cannot have would be fabricated coverage. The lojack's own opening range is
    refused and this spot is not: the lojack facing a three-bet with everybody else folded has one
    opponent live and nothing multiway below it, because the predicate excludes decisions whose
    *future* can still go multiway, not ones deep inside a heads-up line."""
    covered = library.hand_classes_for(solved_key(library, "LJ", "LJ", "CO"))

    assert 0 < len(covered) < 169
    assert "AA" in covered
    assert "72o" not in covered


def test_lookup_hits_the_committed_chart_from_hole_cards(library: PreflopChartLibrary) -> None:
    result = library.lookup_hole_cards(6, 100, "SB", (), ("Ah", "As"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == SB_OPEN
    assert result.hand_class == "AA"
    assert result.best_action == "raise"


def test_lookup_hits_the_defense_spot(library: PreflopChartLibrary) -> None:
    expected = solved_key(library, "BB", "CO")

    result = library.lookup(ChartQuery(6, 100, "BB", solved_line(library, "BB", "CO"), "AA"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == expected


@pytest.mark.parametrize("opener", REFUSED_OPENS)
def test_the_four_retired_opening_ranges_are_refused(
    library: PreflopChartLibrary, opener: str
) -> None:
    """The ruled cost, asserted as the refusal it became rather than deleted. All four are in the
    retired chart and the bot answers them today. The subtree clause drops them: a first-in
    decision from those seats has at least three players live, so a multiway terminal is reachable
    below it, and `MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION` says GTOpen prices those as the
    product of hero's pairwise equities - understating three-way equity by 10.5 points and by 14
    on the suited connectors whose whole value is multiway. Kept as an assertion because the
    failure is silent: the history clause alone commits all four and every one answers."""
    result = library.lookup(ChartQuery(6, 100, opener, (), "AA"))

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"
    assert result.spot_key == f"t6/d{DEPTH_BB}/{opener}/rfi"


def test_the_small_blind_refuses_a_button_open_and_answers_the_four_bet_behind_it(
    library: PreflopChartLibrary,
) -> None:
    """The pair of spots that makes the predicate legible, and the retired chart held one. Facing
    a button open the small blind still has the big blind to act, so three are live and the node
    is outside the subtree clause. Three-bet it and have the big blind fold, and the button's
    four-bet arrives with two live and one opponent invested - committed. So the chart refuses a
    decision and answers its own continuation: the clause is about what can still happen, not how
    deep the line runs. Both keys are built from prices the chart declares, so neither assertion
    is about a price, and the empty substitution list proves the miss is the predicate."""
    facing_open = library.lookup(
        ChartQuery(6, 100, "SB", solved_line(library, "SB", "BTN"), "AA")
    )
    four_bet = library.lookup(
        ChartQuery(6, 100, "SB", solved_line(library, "SB", "BTN", "SB", "BTN"), "AA")
    )

    assert isinstance(facing_open, ChartMiss)
    assert facing_open.code == "lookup:spot-not-covered"
    assert facing_open.spot_key == f"t6/d{DEPTH_BB}/SB/BTN:raise@2.5"
    assert facing_open.price_substitutions == ()

    assert isinstance(four_bet, ChartHit)
    assert four_bet.spot_key.startswith(f"t6/d{DEPTH_BB}/SB/BTN:raise@2.5,")
    assert four_bet.spot_key.count(":raise@") == 3


def test_the_cutoff_facing_a_lojack_open_is_refused_with_seats_behind_it(
    library: PreflopChartLibrary,
) -> None:
    """Phase 04's chart missed this spot, the retired chart held it, and it goes again. It was the
    clearest case of the coverage the full-table export bought, and the predicate takes it back for
    the reason it takes the four opening ranges: the cutoff facing a lojack open has the button,
    the small blind and the big blind still live. Asserted as a miss rather than removed, because a
    converter on either clause alone answers it."""
    result = library.lookup(ChartQuery(6, 100, "CO", solved_line(library, "CO", "LJ"), "AA"))

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"
    assert result.spot_key == f"t6/d{DEPTH_BB}/CO/LJ:raise@2.5"


def test_the_squeeze_stays_refused_and_now_for_the_ruled_reason(
    library: PreflopChartLibrary,
) -> None:
    """An open and a cold call in front of the button, refused before and after. Cold calls *are*
    in the solved tree - only limps were removed - so the export has a node here and the predicate
    declines it twice over: two opponents invested fails the history clause, three players live
    fails the subtree clause. It is the one spot in this file both clauses reject. The key is
    asserted, not only the code: a migration that repriced the query and nothing else would keep
    passing while asking about something that is not a squeeze."""
    sequence = (*solved_line(library, "BTN", "LJ"), PreflopAction("CO", "call"))

    result = library.lookup(ChartQuery(6, 100, "BTN", sequence, "AA"))

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"
    assert result.spot_key is not None
    assert result.spot_key.endswith("CO:call")


def test_the_big_blind_facing_a_four_bet_is_now_covered(
    library: PreflopChartLibrary,
) -> None:
    """Phase 12 gave this cell a key and the raked chart had no four-bet node to fill it. The
    solved tree holds four-bets and every one of the big blind's is inside the predicate, so the
    assertion that used to prove this spot was refused now proves it is answered. All twenty
    survive, and that is structural: the big blind acts last preflop, so a node where it decides
    has at most one opponent left to resolve."""
    result = library.lookup(
        ChartQuery(6, 100, "BB", solved_line(library, "BB", "CO", "BB", "CO"), "AA")
    )

    assert isinstance(result, ChartHit)
    assert result.spot_key.count(":raise@") == 3


def test_a_limped_pot_is_refused_because_the_solve_holds_no_limp(
    library: PreflopChartLibrary,
) -> None:
    """The coverage this phase gave up, asserted as the refusal it became. Limps left the solve at
    phase 10's human gate - 87 percent of the tree, and hero never limps - so the export is
    `limp: false` and holds no limped node. It is the fifteenth spot the refusal rate may rise on
    and the only one not the predicate's doing: it *passes* the predicate, one opponent invested
    and two live, and has no node to derive from. That is why the retired chart's survivors count
    22 by the predicate and 21 by what got committed."""
    result = library.lookup(ChartQuery(6, 100, "BB", (PreflopAction("SB", "call"),), "AA"))

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"


def test_a_hand_the_lojack_cannot_hold_facing_a_three_bet_is_refused(
    library: PreflopChartLibrary,
) -> None:
    """72o is not in the lojack's opening range, so no three-bet cell can hold it."""
    result = library.lookup(
        ChartQuery(6, 100, "LJ", solved_line(library, "LJ", "LJ", "CO"), "72o")
    )

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:hand-class-not-covered"


@pytest.mark.parametrize(
    ("label", "query", "code"),
    [
        (
            "nine-handed table",
            ChartQuery(9, 100, "CO", (), "AA"),
            "lookup:no-artifact-for-table-size",
        ),
        (
            "forty big blinds",
            ChartQuery(6, 40, "CO", (), "AA"),
            "lookup:no-artifact-for-stack-depth",
        ),
        (
            "position off the table",
            ChartQuery(6, 100, "UTG", (), "AA"),
            "lookup:position-not-at-table",
        ),
        (
            # What no legal preflop order produces: the cutoff acts before the button. These
            # four are vocabulary properties, so the cutover leaves them alone.
            "the button raising in front of the cutoff",
            ChartQuery(6, 100, "CO", (PreflopAction("BTN", "raise", 2.5),), "AA"),
            "lookup:unrepresentable-spot",
        ),
        (
            # The fifth is the one the predicate created, and it reaches a code the other four
            # cannot: the lojack's open is a legal, expressible, six-handed, 100bb spot at a
            # position that exists, and it is uncovered.
            "an opening range outside the selection rule",
            ChartQuery(6, 100, "LJ", (), "AA"),
            "lookup:spot-not-covered",
        ),
    ],
)
def test_uncovered_queries_fail_closed_against_the_committed_chart(
    library: PreflopChartLibrary, label: str, query: ChartQuery, code: str
) -> None:
    result = library.lookup(query)

    assert isinstance(result, ChartMiss), label
    assert result.code == code, label


def measured_aggregates(library: PreflopChartLibrary, export: SolverExport) -> Aggregates:
    """The two halves of the oracle, each read where it still lives. Opening frequency comes off
    the **export**, since the predicate commits one opening range so the chart cannot carry five;
    big-blind defence comes off the **chart**, the half that travels through the conversion."""
    return Aggregates(
        opening_pct=dict(aggregate_frequencies(export).opening_pct),
        defence_pct={
            opener: 100.0
            - library.action_frequency_pct(solved_key(library, "BB", opener), "fold")
            for opener in OPENERS
        },
        limp_pct={"SB": 0.0},
    )


class TestSourceFrequencies:
    """The phase's external oracle, and what the cutover did to it.

    These ten numbers are GTO Wizard's own displayed output, and phase 05 asserted the chart
    matched every one within half a point - the only place a uniformly wrong range could be caught
    rather than merely reproduced. The cutover makes that comparison false rather than loose: the
    chart is a rake-free solve by another program and the reference is raked. Widening the
    tolerance until a rake-free chart passes is picking a number to go green; deleting the class
    leaves no external number at all. So the oracle keeps the half that does not depend on rake -
    the two orderings - and gains the falsifiable consequence of removing rake. The predicate then
    narrowed it again: four of the five opening rows have no cell, so the opening ordering is
    measured over the export.
    """

    def test_expectations_are_committed_in_reviewable_poker_terms(self) -> None:
        expectations = load_expectations(EXPECTATIONS_PATH)

        assert set(expectations.opening_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert set(expectations.defence_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert expectations.limp_pct["SB"] == 13.73

    def test_the_chart_holds_one_opening_range_so_the_oracle_narrows_to_the_export(
        self, library
    ) -> None:
        """The narrowing above, as an assertion rather than as a paragraph.

        "Measured over the export" is only honest while the chart really does hold a single opening
        range. A chart holding five is one built on the history clause alone.
        """
        openings = [key for key in library.spot_keys() if key.endswith("/rfi")]

        assert openings == [SB_OPEN]

    def test_the_two_orderings_hold_and_the_kept_frequencies_match_the_export(
        self, library, committed_export
    ) -> None:
        """The half of the oracle that survives a change of rake basis and of solver. Later
        position opens wider among the four non-blind positions, and the big blind defends more
        against whoever opens wider - the sanity check a poker player can confirm without reading
        code. A transposed hand index, a mis-assigned actor or an unnormalised row breaks both at
        once, which is what the magnitude comparison was really catching. Only one relation is
        still a property of the chart: the opening ascent is measured over the export, where phase
        10 gated it, while the defence relation travels through the conversion, because the big
        blind's twenty spots are the only place the chart holds a full 169-class range."""
        reference = load_expectations(EXPECTATIONS_PATH)
        as_measured = Aggregates(
            opening_pct=reference.opening_pct,
            defence_pct=reference.defence_pct,
            limp_pct=reference.limp_pct,
        )
        measured = measured_aggregates(library, committed_export)

        assert ordering_errors(measured) == []
        assert ordering_errors(as_measured) == []

        # And the ascent is genuinely read off the export rather than off a chart that
        # happens to answer: four of these five seats have no opening cell to read.
        assert set(measured.opening_pct) >= set(OPENERS)
        for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
            assert measured.opening_pct[wider] > measured.opening_pct[tighter], (
                measured.opening_pct
            )

        # The frequencies themselves, not only their order: otherwise nothing in the tree compares
        # a chart weight against the export weight it came from over the real chart. Sound because
        # the chart carries no arriving range and these six spots are among the eleven at full
        # reach - walked over the export, every class reaches them at 10000 basis points, so its
        # reach-weighted reading and the chart's combo-weighted one are one number. A hundredth of
        # a point, because renormalising each hand and folding the jam into the raise cannot move a
        # combo-weighted frequency, while one class dropped or transposed moves it by whole points.
        solved = aggregate_frequencies(committed_export)
        assert library.action_frequency_pct(SB_OPEN, "raise") == pytest.approx(
            solved.opening_pct["SB"], abs=0.01
        )
        for opener in OPENERS:
            assert measured.defence_pct[opener] == pytest.approx(
                solved.defence_pct[opener], abs=0.01
            ), opener

    def test_the_rake_free_chart_no_longer_matches_the_raked_reference(
        self, library
    ) -> None:
        """Removing rake widens ranges, so a chart still within half a point of a raked reference
        would mean the conversion moved nothing - the failure a dropped assertion here would hide,
        and the report says which moved and why. Measured over the six of the reference's eleven
        rows the chart still holds a cell for: the small blind's open and the five big-blind
        defences. The other four opening rows are dropped rather than answered from the export,
        because a gap there is two programs disagreeing and says nothing about this conversion.
        No direction is asserted, deliberately: defence widens against four openers and comes back
        *tighter* against the button, the contract's own reason a sign cannot answer this."""
        reference = load_expectations(EXPECTATIONS_PATH)
        gaps = [
            abs(library.action_frequency_pct(SB_OPEN, "raise") - reference.opening_pct["SB"])
        ] + [
            abs(
                (100.0 - library.action_frequency_pct(solved_key(library, "BB", opener), "fold"))
                - reference.defence_pct[opener]
            )
            for opener in OPENERS
        ]

        assert len(gaps) == 6
        assert max(gaps) > 0.5


class TestSizingTable:
    def test_sizings_carry_their_own_provenance(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.source_kind == "solver-export"

    def test_a_class_carries_an_entry_for_every_price_it_offers_and_none_otherwise(
        self, library
    ) -> None:
        """The multi-size invariant, at the accessor the strategy actually calls.

        Decision 6 extended 2026-08-24 and re-ruled 2026-08-26: the table holds every raise size a
        spot offers with the weight hero gives each, and those weights are per **hand class**. The
        per-spot form is not a rounding of the per-class one - at the big blind facing a button
        open the spot jams 7.61 percent of hero's aggressive volume while aces jam none and 44
        jams 88.4, so an aggregate shoves aces once in thirteen three-bets - so the subject is the
        cell. Walked over the export, the 86 declare 7,112 cells, split 531 at two prices, 1,688
        at one and 4,893 with nothing to price. The spot-level partition is asserted beside it
        because the artifact and the reports still count in it: 21 spots hold a class at two
        prices, 15 price every priced class at one, and 50 price nothing.
        """
        sizing = PreflopSizingTable.from_repo()
        cells: Counter[int] = Counter()
        widest: Counter[int] = Counter()
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            most = 0
            for hand_class_text, weights in hand_classes:
                entries = sizing.sizes_bb(spot_id, hand_class_text)
                offered = 0 if entries is None else len(entries)

                assert (entries is not None) == (dict(weights).get("raise", 0.0) > 0.0), (
                    spot_id,
                    hand_class_text,
                )
                cells[offered] += 1
                most = max(most, offered)
            widest[most] += 1

        assert [cells[0], cells[1], cells[2]] == [
            UNPRICED_CELLS, ONE_PRICE_CELLS, TWO_PRICE_CELLS
        ]
        assert set(cells) == {0, 1, 2}, "no committed class offers a third price"
        assert [widest[0], widest[1], widest[2]] == [
            SPOTS_OFFERING_NO_RAISE, SPOTS_OFFERING_ONE_PRICE, SPOTS_OFFERING_TWO_PRICES
        ]

    def test_every_entry_is_ordered_by_price_and_carries_the_classs_whole_share(
        self, library
    ) -> None:
        """The shape of an entry, read through the table rather than off the file.

        Ascending by price, so a reader and a report see the same order at every cell. And a
        class's weights sum to one, because a weight is that class's share of its **own**
        aggressive volume rather than of its range - the other plausible reading of decision 6 is
        a pair summing to the class's raise frequency, which is what a converter writes when it
        forgets to renormalise, and the 531 two-price cells are the only place the two differ.
        Weights are asserted strictly positive rather than above a round epsilon: walked over the
        export the smallest is one basis point in 10,000, aces shoving at
        `t6/d100/LJ/LJ:raise@2.5,SB:raise@7.5`, so even a thousandth would drop a price.
        """
        sizing = PreflopSizingTable.from_repo()
        checked = 0
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            for hand_class_text, _ in hand_classes:
                entries = sizing.sizes_bb(spot_id, hand_class_text)
                if entries is None:
                    continue
                checked += 1
                cell = (spot_id, hand_class_text)
                prices = [to_bb for to_bb, _ in entries]

                assert prices == sorted(prices), cell
                assert all(to_bb > 0.0 for to_bb in prices), cell
                assert all(weight > 0.0 for _, weight in entries), cell
                assert sum(weight for _, weight in entries) == pytest.approx(1.0), cell

        assert checked == ONE_PRICE_CELLS + TWO_PRICE_CELLS

    def test_the_small_blinds_open_prices_aces_at_one_price_and_six_classes_at_two(self) -> None:
        """What the lojack's opening-size assertion became, at the seat that still opens.

        2.5 is `open_raises` and 100 is `stack`, both constants the contract froze, and decision
        2's ship-as-solved means no re-solve moves either. Walked over the export: of the 169
        classes here 45 fold pure and carry no entry, 118 hold the open alone, and exactly six put
        weight on the open-shove - AKs, AQs and 99 at one basis point, JJ and TT at two, AKo at
        three. So aces carry **one** price, the sharpest statement of the per-class ruling: the
        retired per-spot shape reads two here for every class and would let the draw shove them.
        `amount_bb` follows the class, so the two-price rule is the strategy's and is asserted in
        `test_full_table_preflop`.
        """
        sizing = PreflopSizingTable.from_repo()
        open_to = float(RULED_CONFIG["open_raises"][0])
        stack = float(RULED_CONFIG["stack"])

        assert [price for price, _ in sizing.sizes_bb(SB_OPEN, "AA")] == [pytest.approx(open_to)]
        assert sizing.amount_bb(SB_OPEN, "AA") == pytest.approx(open_to)
        for hand_class_text in ("AKs", "AQs", "AKo", "JJ", "TT", "99"):
            entries = sizing.sizes_bb(SB_OPEN, hand_class_text)

            assert [price for price, _ in entries] == [
                pytest.approx(open_to), pytest.approx(stack)
            ], hand_class_text
            assert sizing.amount_bb(SB_OPEN, hand_class_text) is None, hand_class_text
        assert sizing.sizes_bb(SB_OPEN, "72o") is None

        # And the six are all of them: naming six says nothing about the other 163, and the
        # global two-price total absorbs any redistribution. So the split is counted.
        counted = Counter(len(sizing.sizes_bb(SB_OPEN, name) or ()) for name in HAND_CLASSES)
        assert counted == {2: 6, 1: 118, 0: 45}, counted

    def test_a_class_with_one_price_answers_amount_bb_and_it_is_heros_stack(
        self, library
    ) -> None:
        """One price is an unambiguous answer, so the table gives it. 15 of the 86 offer hero a jam
        and no named raise - facing a four-bet, or past the raise cap - and there every priced
        class holds exactly one price and `amount_bb` returns it. Without this the invariant
        above reads as "the table never prices anything". The spots are found rather than
        spelled, because a key hardcoded here would point at a cell the permitted re-solve could
        move; every price must be hero's whole stack, which `RULED_CONFIG` fixes and no re-solve
        of this game changes. Walked over the export, those 15 spots price 693 cells between
        them, which is what stops this passing on a table that priced two."""
        sizing = PreflopSizingTable.from_repo()
        stack = float(RULED_CONFIG["stack"])
        jam_only, cells = set(), 0
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            priced = [name for name, _ in hand_classes if sizing.sizes_bb(spot_id, name)]
            if priced and all(len(sizing.sizes_bb(spot_id, name)) == 1 for name in priced):
                jam_only.add(spot_id)
                cells += len(priced)
                for name in priced:
                    assert sizing.amount_bb(spot_id, name) == pytest.approx(stack), (spot_id, name)

        assert len(jam_only) == SPOTS_OFFERING_ONE_PRICE
        assert cells == JAM_ONLY_CELLS

    @pytest.mark.parametrize(
        ("label", "spot_id"),
        [
            ("a stack depth no artifact covers", "t6/d40/CO/rfi"),
            ("an opening range the predicate refuses", "t6/d100/LJ/rfi"),
        ],
    )
    def test_an_uncovered_spot_has_no_size_rather_than_a_default(
        self, label: str, spot_id: str
    ) -> None:
        """Two ways to be uncovered, and neither may produce a price for any class. The second is
        the one the cutover created: the retired chart and its sizing table both held the
        lojack's open, so a table keeping the price after the chart lost the range would let a
        strategy raise 2.5 at a spot the chart refuses."""
        sizing = PreflopSizingTable.from_repo()

        for hand_class_text in ("AA", "AKo", "72o"):
            assert sizing.sizes_bb(spot_id, hand_class_text) is None, (label, hand_class_text)
            assert sizing.amount_bb(spot_id, hand_class_text) is None, (label, hand_class_text)
