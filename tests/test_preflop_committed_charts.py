"""The committed chart itself, not synthetic fixtures.

These tests are what stop `data/artifacts/preflop/` from drifting away from the
export that produced it, and what prove the real file goes through the real importer
and the real lookup.

The hand-authored reference chart these tests originally described is gone. It
covered three spots, it overlapped the solver export on all three, and its big-blind
defence had been widened during Phase 04 on a rake-free heuristic that the raked
solution contradicts. Two artifacts claiming one spot is a library error, so keeping
both was never an option and keeping the invented one was the wrong choice.

Phase 14 replaced the raked GTO Wizard chart these tests were written against with one
derived from the rake-free GTOpen solve. Nothing here spells a raise price any more:
the two charts share no three-bet price and no small-blind opening price, so a spelled
price is a fixture that points at a cell nobody solved. Prices are read out of the keys
the artifact declares, which is the rule the lookup normaliser already follows.
"""

from __future__ import annotations

import subprocess

import pytest

from poker_training_bot.solver_artifacts.gtopen_expectations import (
    EXPECTATIONS_PATH,
    Aggregates,
    load_expectations,
    ordering_errors,
)
from poker_training_bot.solver_artifacts.gtopen_export import COMMITTED_EXPORT_PATH
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
LJ_OPEN = "t6/d100/LJ/rfi"
BTN_OPEN = "t6/d100/BTN/rfi"


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


def solved_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[PreflopAction, ...]:
    """`hero`'s line where each named seat raises at the price the chart solved there.

    Each raising point in the solved tree offers two prices - the named raise and the
    all-in that decision 6 records as a raise to hero's whole stack - so the named raise
    is the smaller of them. Reading both out of the artifact rather than spelling either
    is what lets a re-solve at a different price move these fixtures with it.
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
    # The retired chart held exactly 36 spots and that number was the claim. The count
    # the reach floor selects is decision 1's arithmetic rather than its ruling, and the
    # permitted re-solve moves it, so what is pinned here is only that the cutover is not
    # a coverage reduction. Which spots the chart must hold is asserted by name below.
    assert len(artifact.spots) > 36


def test_the_artifact_declares_the_blind_structure_it_was_solved_at() -> None:
    """Decision 4. The chart was solved at 0.5/1 with no ante.

    Without this the same hand at the same stack depth in a 1/3 game reads as a solved
    spot and nothing anywhere notices, which was phase 13's largest single finding.
    """
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert artifact.blind_structure.small_blind_bb == pytest.approx(0.5)
    assert artifact.blind_structure.big_blind_bb == pytest.approx(1.0)
    assert artifact.blind_structure.ante_bb == pytest.approx(0.0)


def test_the_retired_raked_chart_is_gone_from_the_artifact_directory() -> None:
    """Absence of a key collision is not retirement, and must not be read as it.

    The retired chart three-bets to 8, 11 and 13.5 and opens the small blind to 3.5,
    while the export three-bets to 7.5 and opens to 2.5, so 17 of its 36 keys collide
    with nothing the new artifact declares. `PreflopChartLibrary` would build clean with
    both loaded, and the bot would answer every three-bet spot and every small-blind open
    from raked GTO Wizard ranges while believing it plays the rake-free solve.
    """
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
    """The one committed artifact points at the one committed export, by path.

    Asserted against `COMMITTED_EXPORT_PATH` rather than a filename spelled here, because
    the contract's criterion is that the library holds exactly one artifact whose source
    reference names the committed export.
    """
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert (REPO_ROOT / artifact.source.reference) == COMMITTED_EXPORT_PATH
    assert COMMITTED_EXPORT_PATH.exists()


@pytest.mark.parametrize(
    ("hand_class", "expected"),
    [
        ("AA", "raise"),
        ("72o", "fold"),
        ("K4s", "fold"),
    ],
)
def test_known_lojack_opening_entries(
    library: PreflopChartLibrary, hand_class: str, expected: str
) -> None:
    """Hands whose correct action is not a judgement call, from the tightest opener.

    The lojack opens about a fifth of hands rake-free, so K4s and 72o are folds there in
    any solve of this game, and aces are never folded in any of them.
    """
    weights = library.artifacts[0].weights_for(LJ_OPEN, hand_class)

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


@pytest.mark.parametrize(
    ("hand_class", "expected"),
    [
        ("A5o", "raise"),
        ("ATo", "raise"),
        ("32o", "fold"),
    ],
)
def test_known_button_opening_entries(
    library: PreflopChartLibrary, hand_class: str, expected: str
) -> None:
    """The retired hand-authored chart had the button opening A2o purely. The raked
    solution folds it 91% of the time, so that expectation was carried over from an
    invented range rather than from a solve, and it is gone. A5o and ATo are pure
    opens in the raked chart and in the rake-free solve alike."""
    weights = library.artifacts[0].weights_for(BTN_OPEN, hand_class)

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
    """Hero has not acted, so every hand is possible and must be answered."""
    for spot_id in (LJ_OPEN, BTN_OPEN, solved_key(library, "BB", "CO")):
        assert len(library.hand_classes_for(spot_id)) == 169, spot_id


def test_a_spot_where_hero_already_acted_covers_only_heros_range(
    library: PreflopChartLibrary,
) -> None:
    """A hand the lojack would never open is not a lookup it can make.

    Committing a strategy for a holding hero cannot have would be fabricated
    coverage; an explicit miss is the honest answer.
    """
    covered = library.hand_classes_for(solved_key(library, "LJ", "LJ", "CO"))

    assert 0 < len(covered) < 169
    assert "AA" in covered
    assert "72o" not in covered


def test_lookup_hits_the_committed_chart_from_hole_cards(library: PreflopChartLibrary) -> None:
    result = library.lookup_hole_cards(6, 100, "LJ", (), ("Ah", "As"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == LJ_OPEN
    assert result.hand_class == "AA"
    assert result.best_action == "raise"


def test_lookup_hits_the_defense_spot(library: PreflopChartLibrary) -> None:
    expected = solved_key(library, "BB", "CO")

    result = library.lookup(ChartQuery(6, 100, "BB", solved_line(library, "BB", "CO"), "AA"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == expected


def test_the_cutoff_facing_a_lojack_open_is_now_covered(library: PreflopChartLibrary) -> None:
    """Phase 04's chart missed this spot; the full-table export holds it."""
    result = library.lookup(ChartQuery(6, 100, "CO", solved_line(library, "CO", "LJ"), "AA"))

    assert isinstance(result, ChartHit)


def test_the_squeeze_the_retired_chart_refused_is_now_covered(
    library: PreflopChartLibrary,
) -> None:
    """An open and a cold call in front of the button.

    The retired chart refused this: it held opens, single-open responses, the opener
    facing a three-bet and one limped spot, and nothing else. Cold calls are in the
    solved tree - only limps were removed - so the cutover answers it. Asserted as a hit
    rather than as a refusal because a migration that only repriced the query would keep
    passing for the wrong reason.
    """
    sequence = (*solved_line(library, "BTN", "LJ"), PreflopAction("CO", "call"))

    result = library.lookup(ChartQuery(6, 100, "BTN", sequence, "AA"))

    assert isinstance(result, ChartHit)
    assert result.spot_key.endswith("CO:call")


def test_the_big_blind_facing_a_four_bet_is_now_covered(
    library: PreflopChartLibrary,
) -> None:
    """Phase 12 gave this cell a key and the raked chart had no four-bet node to fill it.

    The solved tree holds four-bets, and the big blind reaches this one often enough to
    clear the reach floor, so the assertion that used to prove it was refused now proves
    it is answered.
    """
    result = library.lookup(
        ChartQuery(6, 100, "BB", solved_line(library, "BB", "CO", "BB", "CO"), "AA")
    )

    assert isinstance(result, ChartHit)
    assert result.spot_key.count(":raise@") == 3


def test_a_limped_pot_is_refused_because_the_solve_holds_no_limp(
    library: PreflopChartLibrary,
) -> None:
    """The coverage this phase gave up, asserted as the refusal it became.

    The retired chart answered the big blind facing a small-blind limp. Limps left the
    solve at phase 10's human gate on the measurement that they are 87 percent of the
    tree and that hero never limps, so the committed export is `limp: false` and no
    limped node exists at any reach floor. `CHART-CANNOT-ANSWER-A-LIMPED-POT` is the
    entry that carries this, and a refusal is the honest answer where a neighbouring
    cell would be a guess.
    """
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
            # What no legal preflop order produces, which is what the unrepresentable code
            # still means: the cutoff acts before the button. These four are properties of
            # the vocabulary rather than of the chart, so the cutover leaves them alone.
            "the button raising in front of the cutoff",
            ChartQuery(6, 100, "CO", (PreflopAction("BTN", "raise", 2.5),), "AA"),
            "lookup:unrepresentable-spot",
        ),
    ],
)
def test_uncovered_queries_fail_closed_against_the_committed_chart(
    library: PreflopChartLibrary, label: str, query: ChartQuery, code: str
) -> None:
    result = library.lookup(query)

    assert isinstance(result, ChartMiss), label
    assert result.code == code, label


def measured_aggregates(library: PreflopChartLibrary) -> Aggregates:
    return Aggregates(
        opening_pct={
            position: library.action_frequency_pct(f"t6/d{DEPTH_BB}/{position}/rfi", "raise")
            for position in ("LJ", "HJ", "CO", "BTN", "SB")
        },
        defence_pct={
            opener: 100.0
            - library.action_frequency_pct(solved_key(library, "BB", opener), "fold")
            for opener in ("LJ", "HJ", "CO", "BTN", "SB")
        },
        limp_pct={"SB": 0.0},
    )


class TestSourceFrequencies:
    """The phase's external oracle, and what the cutover did to it.

    These ten numbers are GTO Wizard's own displayed output, and phase 05 asserted the
    chart matched every one within half a point - the only place a uniformly wrong range
    could be caught rather than merely reproduced. The cutover makes that comparison false
    rather than loose: the chart is a rake-free solve by another program, the reference is
    raked, and the non-goals forbid rederiving the reference so it stays external.
    Widening the tolerance until a rake-free chart passes is picking a number to go green;
    deleting the class leaves no external number at all. So the oracle keeps the half that
    does not depend on rake - the two orderings, held against both - and gains the
    falsifiable consequence of removing rake. The magnitude comparison moves to the
    phase 14 report, gated by nothing, as phase 10's decision 6 ruled for the export.
    """

    def test_expectations_are_committed_in_reviewable_poker_terms(self) -> None:
        expectations = load_expectations(EXPECTATIONS_PATH)

        assert set(expectations.opening_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert set(expectations.defence_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert expectations.limp_pct["SB"] == 13.73

    def test_both_the_reference_and_the_chart_satisfy_the_same_two_orderings(
        self, library
    ) -> None:
        """The half of the oracle that survives a change of rake basis and of solver.

        Later position opens wider among the four non-blind positions, and the big blind
        defends more against whoever opens wider - the sanity check a poker player can
        confirm without reading code. A transposed hand index, a mis-assigned actor or an
        unnormalised row breaks both at once, which is what the magnitude comparison was
        really catching.
        """
        reference = load_expectations(EXPECTATIONS_PATH)
        as_measured = Aggregates(
            opening_pct=reference.opening_pct,
            defence_pct=reference.defence_pct,
            limp_pct=reference.limp_pct,
        )

        assert ordering_errors(measured_aggregates(library)) == []
        assert ordering_errors(as_measured) == []

    def test_the_rake_free_chart_no_longer_matches_the_raked_reference(
        self, library
    ) -> None:
        """Removing rake widens ranges, so a chart still within half a point of a raked
        reference on all ten would mean the conversion moved nothing - the failure a
        silently dropped assertion here would hide. The report says which moved and why."""
        reference = load_expectations(EXPECTATIONS_PATH)
        measured = measured_aggregates(library)
        gaps = [
            abs(measured.opening_pct[name] - value)
            for name, value in reference.opening_pct.items()
        ] + [
            abs(measured.defence_pct[name] - value)
            for name, value in reference.defence_pct.items()
        ]

        assert max(gaps) > 0.5


class TestSizingTable:
    def test_sizings_carry_their_own_provenance(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.source_kind == "solver-export"

    def test_a_spot_carries_a_committed_size_exactly_when_it_offers_a_raise(
        self, library
    ) -> None:
        """The invariant rather than the universal, and the stronger of the two.

        Every spot in the 36-spot chart offered a raise, so the two said the same thing.
        Thousands of committed nodes now offer hero only fold and call - facing a shove,
        or past the four-raise cap - and pricing one of those is a size for an action the
        chart does not offer, which the universal cannot catch. Neither set is empty.
        """
        sizing = PreflopSizingTable.from_repo()
        priced: list[str] = []
        sizeless: list[str] = []
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            offers_raise = any(
                weight > 0.0
                for _, weights in hand_classes
                for action, weight in weights
                if action == "raise"
            )
            (priced if offers_raise else sizeless).append(spot_id)

            assert (sizing.amount_bb(spot_id) is not None) == offers_raise, spot_id

        assert priced and sizeless

    def test_the_lojack_opens_to_the_size_the_solution_used(self) -> None:
        """2.5 is `open_raises` in the ruled config, which the permitted re-solve may not
        change, so it is a constant the contract froze rather than one this file chose."""
        sizing = PreflopSizingTable.from_repo()

        assert sizing.amount_bb(f"t6/d{DEPTH_BB}/LJ/rfi") == pytest.approx(2.5)

    def test_an_uncovered_spot_has_no_size_rather_than_a_default(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.amount_bb("t6/d40/CO/rfi") is None
