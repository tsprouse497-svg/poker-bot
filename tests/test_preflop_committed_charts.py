"""The committed chart itself, not synthetic fixtures.

These tests stop `data/artifacts/preflop/` drifting away from the export that produced it, and
they are the **migration** the contract's regression expectation asks for: every claim this file
made about the 86-spot chart is re-cut against the 249 here, before the freeze, rather than
repaired after it. Phases 11 and 12 each deferred that and each paid a separate repair task.

**What moved.** The retired set was 86 spots taken from a superseded export under a
history-and-liveness predicate. The committed set is **249** of the export's 33,969 action nodes -
5 first-in, 25 facing an open, 219 facing a three-bet - selected by three clauses: at most two
raises already in, multiway exposure below ten percent measured over the branches the bot can
take, and no big-blind squeeze spot. So all five opening ranges come back, every four-bet-facing
spot goes, and the price list is exactly 2.5, 7.5 and 22.5 with no jam anywhere.

**And hero stopped cold-calling.** At the 20 non-big-blind facing-an-open spots each cell's call
weight is added to its raise weight (decision 45), so the published menu there is raise or fold.
The big blind's five keep fold, call and raise. The 219 publish fold, call and four-bet.

Every claim the cutover reverses is kept as its reversal rather than deleted: the four opening
ranges that were refused are now answered, and the big blind's four-bet defence that was answered
is now refused. Only an assertion in both directions tells one selection rule from another.
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
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.solver_artifacts.schema import PreflopAction, weights_checksum
from poker_training_bot.solver_artifacts.schema import spot_key as derive_spot_key
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable
from scripts.repo_paths import REPO_ROOT

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
GTO_WIZARD_ARTIFACT = ARTIFACT_DIR / "six_max_nl25_100bb.json"
GTO_WIZARD_SIZINGS = ARTIFACT_DIR / "sizings" / "six_max_nl25_100bb.json"
"""Named for the source rather than for its status. Two files answer to "the retired chart" in
this phase and one identifier for both is how they get confused: these are the GTO Wizard pair,
which must not exist at all, while `six_max_100bb_rakefree.json` is the 86-spot chart stage 6
rewrites in place and reads out of git history - `RETIRED_SIZINGS` in
`tests/test_derived_chart_report.py` is that second file and is asserted to *exist* at its pin."""

DEPTH_BB = 100

COMMITTED_SPOTS = 249
FIRST_IN_SPOTS = 5
FACING_AN_OPEN_SPOTS = 25
FACING_A_THREE_BET_SPOTS = 219
"""Decision 48's final set, split by how many raises hero faces. Contract, decision 49."""

BB_FACING_AN_OPEN = 5
MERGED_FACING_AN_OPEN = 20
NON_BLIND_SQUEEZE_SPOTS = 10
"""How the 25 split. Ten non-blind seats face an open with nobody in between - LJ opens and four
seats can answer, HJ three, CO two, BTN one - ten more face an open with exactly one cold caller
already in, and the big blind's five close the action alone. The big blind's own ten squeeze
spots are the third clause's whole bucket (decision 48) and are refused."""

CELLS_AT_NON_ZERO_REACH = 18_431
"""Every cell the 249 declare. A class is declared where it arrives, so a spot at which hero has
not acted declares all 169 and the rest declare hero's arriving range. Decision 49."""

RETIRED_SPOTS = 86
"""What this file used to describe. Kept as a number so a chart that did not move fails loudly."""

OPEN_PRICE = 2.5
THREE_BET_PRICE = 7.5
FOUR_BET_PRICE = 22.5
RULED_PRICES = (OPEN_PRICE, THREE_BET_PRICE, FOUR_BET_PRICE)
"""`open_raises` is 2.5 and `raise_mults` is 3.0, so hero's price is the open times the multiplier
once per raise faced. The fourth rung crosses `allin_threshold` and snaps to the stack, and it
lives only at the four-bet-facing spots the depth clause refuses, so no committed spot holds it."""

OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
OPENING_ORDER = ("LJ", "HJ", "CO", "BTN")

ROWS_THE_RAKE_DID_NOT_MOVE = {("open", "HJ")}
"""The one of the reference's ten frequency rows the rake-free solve reproduces to within half a
point: the hijack opens 21.5649 against 21.65. Every other row moves by 0.72 to 19.89. Named so
the de-rake check can be stated per row instead of as a maximum, which one moving row satisfies."""


def rfi_key(seat: str) -> str:
    return f"t6/d{DEPTH_BB}/{seat}/rfi"


def hero_seat(spot_key_text: str) -> str:
    return spot_key_text.split("/")[2]


def raises_faced(spot_key_text: str) -> int:
    return spot_key_text.count(":raise@")


def cold_callers(spot_key_text: str) -> int:
    return spot_key_text.count(":call")


def prices_in(spot_key_text: str) -> list[float]:
    return [
        float(part.split(":raise@")[1])
        for part in spot_key_text.split("/", 3)[3].split(",")
        if ":raise@" in part
    ]


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(ARTIFACT_DIR))


@pytest.fixture(scope="module")
def committed_export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


def menus(library: PreflopChartLibrary) -> dict[str, tuple[str, ...]]:
    """Per spot, the actions any class puts weight on, sorted. The published menu shape."""
    found: dict[str, set[str]] = {}
    for spot_id, hand_classes in library.artifacts[0].action_weights:
        offered = found.setdefault(spot_id, set())
        for _, weights in hand_classes:
            offered.update(action for action, weight in weights if weight > 0.0)
    return {spot_id: tuple(sorted(actions)) for spot_id, actions in found.items()}


def solved_line(
    library: PreflopChartLibrary, hero: str, *raisers: str
) -> tuple[PreflopAction, ...]:
    """`hero`'s line where each named seat raises at the price the chart solved there.

    Each raising point now offers exactly one price, the jam having left with the four-bet family,
    so `min` picks the only entry. It still works for a line the chart *refuses*, which the
    refusal tests depend on: a refused query is still priced from the chart and misses anyway, so
    nothing about the price refused it.
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
    """The count is asserted rather than a direction. `> 36` was what this file could say while
    the tree fact lived in `test_derived_chart.py`; the cutover moves the set by a factor of three
    and a direction would pass on any of the four sets this phase has described."""
    artifacts = import_preflop_artifacts(ARTIFACT_DIR)

    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.table_size == 6
    assert artifact.stack_depth_bb == 100
    assert artifact.source.kind == "solver-export"
    assert artifact.audit_fields.spot_count == len(artifact.spots)
    assert len(artifact.spots) == COMMITTED_SPOTS
    assert len(artifact.spots) != RETIRED_SPOTS


def test_the_artifact_declares_the_blind_structure_it_was_solved_at() -> None:
    """Decision 4: the chart was solved at 0.5/1 with no ante. Without it the same hand at the same
    depth in a 1/3 game reads as a solved spot and nothing notices - phase 13's largest finding."""
    artifact = import_preflop_artifacts(ARTIFACT_DIR)[0]

    assert artifact.blind_structure.small_blind_bb == pytest.approx(0.5)
    assert artifact.blind_structure.big_blind_bb == pytest.approx(1.0)
    assert artifact.blind_structure.ante_bb == pytest.approx(0.0)


def test_the_retired_raked_chart_is_gone_from_the_artifact_directory() -> None:
    """Absence of a key collision is not retirement. The raked chart three-bets to 8, 11 and 13.5
    and opens the small blind to 3.5, so most of its keys collide with nothing the new artifact
    declares: `PreflopChartLibrary` would build clean with both loaded and the bot would answer
    three-bets and small-blind opens from raked ranges while believing it plays the rake-free
    solve. **Two files answer to "the retired chart" in this phase** - the GTO Wizard one this
    asserts is gone, and the 86-spot rake-free chart stage 6 replaces in place. Only the first is
    a file that must not exist; the second is a set of contents that must not survive."""
    assert not GTO_WIZARD_ARTIFACT.exists()
    assert not GTO_WIZARD_SIZINGS.exists()


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


def test_the_committed_keys_split_into_the_three_families(library: PreflopChartLibrary) -> None:
    """249 is not self-evidently three numbers. Counted key by key, because the artifact's own spot
    count cannot see a family that grew while another shrank - which is how a build on the depth
    clause alone reads: it keeps every four-bet-facing spot and still totals a number somebody
    could mistake for this one."""
    by_depth = Counter(raises_faced(key) for key in library.spot_keys())

    assert sum(by_depth.values()) == COMMITTED_SPOTS
    assert by_depth[0] == FIRST_IN_SPOTS
    assert by_depth[1] == FACING_AN_OPEN_SPOTS
    assert by_depth[2] == FACING_A_THREE_BET_SPOTS
    assert max(by_depth) == 2, "the depth clause admits at most two raises already in"


def test_every_opening_range_is_committed_now(library: PreflopChartLibrary) -> None:
    """The four opening ranges the 86 gave up come back, and this is the sharpest single statement
    of what decision 46 bought. Under the retired predicate a first-in decision from any seat but
    the small blind had three or more players live and was refused; exposure measured over the
    branches the bot can take reads those nodes low, because the bot's own answer to an open is a
    raise or a fold and neither of those makes a multiway flop."""
    openings = sorted(key for key in library.spot_keys() if key.endswith("/rfi"))

    assert openings == sorted(rfi_key(seat) for seat in OPENERS)
    assert len(openings) == FIRST_IN_SPOTS


@pytest.mark.parametrize(
    ("seat", "hand_class", "expected"),
    [
        ("SB", "AA", "raise"),
        ("SB", "ATo", "raise"),
        ("SB", "A5o", "raise"),
        ("SB", "72o", "fold"),
        ("LJ", "AA", "raise"),
        ("LJ", "K4s", "fold"),
        ("BTN", "AA", "raise"),
        ("BTN", "32o", "fold"),
    ],
)
def test_known_opening_entries(
    library: PreflopChartLibrary, seat: str, hand_class: str, expected: str
) -> None:
    """Hands whose correct action is not a judgement call, now from every seat that opens. The
    lojack's K4s fold comes back with the lojack's range: it opens about a fifth of hands with four
    seats behind it, where the small blind opens 54 percent against one opponent with half a blind
    already in and raises K4s 99.97 percent of the time. 72o and 32o are folds in any solve of this
    game, and A5o and ATo are pure opens from a seat with one opponent left."""
    weights = library.artifacts[0].weights_for(rfi_key(seat), hand_class)

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


@pytest.mark.parametrize(("hand_class", "expected"), [("AA", "raise"), ("72o", "fold")])
def test_known_big_blind_defence_entries(
    library: PreflopChartLibrary, hand_class: str, expected: str
) -> None:
    """The big blind facing a cutoff open, at whatever price the cutoff was solved at."""
    weights = library.artifacts[0].weights_for(solved_key(library, "BB", "CO"), hand_class)

    assert weights is not None
    assert max(weights, key=lambda entry: entry[1])[0] == expected


def test_the_facing_an_open_family_splits_by_seat_and_by_who_is_already_in(
    library: PreflopChartLibrary,
) -> None:
    """The 25, decomposed, because 25 is where two rulings meet and a wrong one of them still
    totals 25. Five are the big blind closing the action alone. Ten are a non-blind seat facing an
    open with nobody in between. Ten more are a non-blind seat facing an open with exactly one cold
    caller already in - the squeezes decision 46 admitted and decision 48 kept. None is the big
    blind facing an open with a caller in: those ten are the third clause's whole bucket."""
    facing = [key for key in library.spot_keys() if raises_faced(key) == 1]
    big_blind = [key for key in facing if hero_seat(key) == "BB"]
    squeezes = [key for key in facing if cold_callers(key) > 0]

    assert len(facing) == FACING_AN_OPEN_SPOTS
    assert len(big_blind) == BB_FACING_AN_OPEN
    assert all(cold_callers(key) == 0 for key in big_blind), big_blind
    assert len(squeezes) == NON_BLIND_SQUEEZE_SPOTS
    assert all(hero_seat(key) != "BB" for key in squeezes), squeezes
    assert all(cold_callers(key) == 1 for key in squeezes), squeezes
    assert len(facing) - len(big_blind) == MERGED_FACING_AN_OPEN


def test_the_twenty_merged_spots_publish_raise_or_fold_and_never_a_call(
    library: PreflopChartLibrary,
) -> None:
    """Decision 45, as the one thing a reader of the chart can check. The bot may not cold-call, so
    at every facing-an-open spot but the big blind's the call weight is added to the raise weight
    and the published menu is raise or fold. A converter that *dropped* the flat instead of merging
    it publishes the same menu over a narrower range, which this cannot see and
    `test_chart_conversion` can; what this sees is a converter that published the flat anyway."""
    shapes = menus(library)
    merged = [
        key for key in library.spot_keys() if raises_faced(key) == 1 and hero_seat(key) != "BB"
    ]

    assert len(merged) == MERGED_FACING_AN_OPEN
    for key in merged:
        assert shapes[key] == ("fold", "raise"), key


def test_the_big_blinds_five_keep_the_flat_and_the_three_bet_family_keeps_it_too(
    library: PreflopChartLibrary,
) -> None:
    """The other side of the same ruling, and the reason it is not "the chart never calls". The big
    blind closes the action for the rest of a blind it already posted, so its flat is not a cold
    call and stays. At the 219 the call is hero's call to a three-bet, which decision 52 says in
    terms is not removed. A merge applied to either family is a chart three-betting a range it
    should be continuing with, and only asserting `call` present here catches it."""
    shapes = menus(library)
    big_blind = [
        key for key in library.spot_keys() if raises_faced(key) == 1 and hero_seat(key) == "BB"
    ]
    three_bet_faced = [key for key in library.spot_keys() if raises_faced(key) == 2]

    assert len(big_blind) == BB_FACING_AN_OPEN
    assert len(three_bet_faced) == FACING_A_THREE_BET_SPOTS
    for key in big_blind + three_bet_faced:
        assert shapes[key] == ("call", "fold", "raise"), key


def test_the_published_menu_shapes_are_only_the_two(library: PreflopChartLibrary) -> None:
    """Counted rather than checked per family, so a spot publishing something else - a bare fold
    row, or a call at a merged spot - cannot hide inside a family that was only sampled."""
    counted = Counter(menus(library).values())

    assert dict(counted) == {
        ("call", "fold", "raise"): BB_FACING_AN_OPEN + FACING_A_THREE_BET_SPOTS,
        ("fold", "raise"): FIRST_IN_SPOTS + MERGED_FACING_AN_OPEN,
    }


def test_first_orbit_spots_cover_all_169_classes(library: PreflopChartLibrary) -> None:
    """Hero has not acted, so every hand is possible and must be answered. Every first-in spot and
    every facing-an-open spot is one of these: hero's first decision in the hand, whatever is in
    front of him. A spot declaring fewer classes there is a converter that dropped a row it had."""
    first_orbit = [key for key in library.spot_keys() if raises_faced(key) <= 1]

    assert len(first_orbit) == FIRST_IN_SPOTS + FACING_AN_OPEN_SPOTS
    for spot_id in first_orbit:
        assert len(library.hand_classes_for(spot_id)) == 169, spot_id


def test_a_spot_where_hero_already_acted_covers_only_heros_range(
    library: PreflopChartLibrary,
) -> None:
    """A hand the lojack would never open is not a lookup it can make, and committing a strategy
    for a holding hero cannot have would be fabricated coverage."""
    covered = library.hand_classes_for(solved_key(library, "LJ", "LJ", "CO"))

    assert 0 < len(covered) < 169
    assert "AA" in covered
    assert "72o" not in covered


def test_the_committed_cells_are_the_classes_that_arrive(library: PreflopChartLibrary) -> None:
    """The whole chart, counted. 18,431 cells at non-zero reach, and the converter drops the rest:
    a GTOpen payload is unconditional, so a hand hero folded upstream still carries a full strategy
    row and that row is the solver's untouched initialisation. Committing it is worse than a gap,
    because it does not read as missing (`UNIFORM-INITIALISATION-ROWS-ARE-NOT-STRATEGY`)."""
    counted = sum(len(hand_classes) for _, hand_classes in library.artifacts[0].action_weights)

    assert counted == CELLS_AT_NON_ZERO_REACH


def measured_aggregates(library: PreflopChartLibrary, export: SolverExport) -> Aggregates:
    """Both halves of the oracle read off the **chart** now. The 86 could not carry five opening
    ranges, so the ascent was measured over the export; the 249 hold all five, so the whole
    comparison travels through the conversion, which is where a transposed index or a mis-assigned
    actor would be introduced. The export stays an argument because the frequencies are asserted
    against it below, and because a chart that lost a row must fail rather than shrink the set."""
    assert export.node_count > 0
    return Aggregates(
        opening_pct={
            seat: library.action_frequency_pct(rfi_key(seat), "raise") for seat in OPENERS
        },
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
    chart is a rake-free solve by another program and **the reference is raked**, so a rake-free
    chart reading wider is expected rather than contradictory (decision 48). Widening the tolerance
    until it passes is picking a number to go green; deleting the class leaves no external number
    at all. So the oracle keeps the half that does not depend on rake - the two orderings - and
    gains the falsifiable consequence of removing rake.
    """

    def test_expectations_are_committed_in_reviewable_poker_terms(self) -> None:
        expectations = load_expectations(EXPECTATIONS_PATH)

        assert set(expectations.opening_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert set(expectations.defence_pct) == {"LJ", "HJ", "CO", "BTN", "SB"}
        assert expectations.limp_pct["SB"] == 13.73

    def test_the_chart_holds_every_row_the_reference_names(self, library) -> None:
        """The narrowing this class used to record, undone. "Measured over the export" was only
        honest while the chart held one opening range. It holds five, so the ascent is a property
        of the chart again and a build that lost four of them fails here rather than passing on a
        number read from somewhere else."""
        openings = {key for key in library.spot_keys() if key.endswith("/rfi")}

        assert openings == {rfi_key(seat) for seat in OPENERS}

    def test_the_two_orderings_hold_and_the_kept_frequencies_match_the_export(
        self, library, committed_export
    ) -> None:
        """The half of the oracle that survives a change of rake basis and of solver. Later
        position opens wider among the four non-blind positions, and the big blind defends more
        against whoever opens wider - the sanity check a poker player can confirm without reading
        code. A transposed hand index, a mis-assigned actor or an unnormalised row breaks both at
        once, which is what the magnitude comparison was really catching.

        The frequencies themselves, not only their order: otherwise nothing compares a chart weight
        against the export weight it came from over the real chart. Sound because all ten spots are
        at full reach - hero has not acted at any of them - so the export's reach-weighted reading
        and the chart's combo-weighted one are one number. A hundredth of a point, because
        renormalising each hand cannot move a combo-weighted frequency while one class dropped or
        transposed moves it by whole points. **Neither family carries the merge**: an opening spot
        has no cold call in it and the big blind's flat is not one, so both sides read the solve.
        """
        reference = load_expectations(EXPECTATIONS_PATH)
        as_measured = Aggregates(
            opening_pct=reference.opening_pct,
            defence_pct=reference.defence_pct,
            limp_pct=reference.limp_pct,
        )
        measured = measured_aggregates(library, committed_export)
        solved = aggregate_frequencies(committed_export)

        assert ordering_errors(measured) == []
        assert ordering_errors(as_measured) == []
        for tighter, wider in zip(OPENING_ORDER, OPENING_ORDER[1:], strict=False):
            assert measured.opening_pct[wider] > measured.opening_pct[tighter], (
                measured.opening_pct
            )
        for opener in OPENERS:
            assert measured.opening_pct[opener] == pytest.approx(
                solved.opening_pct[opener], abs=0.01
            ), opener
            assert measured.defence_pct[opener] == pytest.approx(
                solved.defence_pct[opener], abs=0.01
            ), opener

    def test_the_rake_free_chart_no_longer_matches_the_raked_reference(self, library) -> None:
        """Removing rake widens ranges, so a chart still within half a point of a raked reference
        would mean the conversion moved nothing - the failure a dropped assertion here would hide,
        and the report says which moved and why. No direction is asserted, deliberately: the
        contract's own reason a sign cannot answer this.

        Measured **row by row** over all ten of the reference's frequency rows, not as a maximum
        over them. A maximum is satisfied by one row moving and nine standing still, and widening
        this check from six rows to ten made that weaker rather than stronger: a conversion that
        widened only the small blind's open, whose gap is 19.9 points, would pass with the other
        nine identical to the raked source.

        One row genuinely does not move and is named rather than averaged away. The hijack opens
        21.5649 against the reference's 21.65, a gap of 0.085, so the rake-free solve and a raked
        GTO Wizard chart agree there to under a tenth of a point. That is the one place a sign
        test could not tell this conversion from no conversion at all, and it is asserted as the
        only such row: a second one appearing turns this red."""
        reference = load_expectations(EXPECTATIONS_PATH)
        gaps = {
            ("open", seat): abs(
                library.action_frequency_pct(rfi_key(seat), "raise") - reference.opening_pct[seat]
            )
            for seat in OPENERS
        } | {
            ("defence", opener): abs(
                (100.0 - library.action_frequency_pct(solved_key(library, "BB", opener), "fold"))
                - reference.defence_pct[opener]
            )
            for opener in OPENERS
        }

        assert len(gaps) == 2 * len(OPENERS)
        assert {row for row, gap in gaps.items() if gap <= 0.5} == ROWS_THE_RAKE_DID_NOT_MOVE
        for row, gap in gaps.items():
            if row not in ROWS_THE_RAKE_DID_NOT_MOVE:
                assert gap > 0.5, (row, gap)


class TestSizingTable:
    def test_sizings_carry_their_own_provenance(self) -> None:
        sizing = PreflopSizingTable.from_repo()

        assert sizing.source_kind == "solver-export"

    def test_a_class_carries_an_entry_for_every_price_it_offers_and_none_otherwise(
        self, library
    ) -> None:
        """The multi-size invariant, at the accessor the strategy actually calls, and both ways
        round: a class with aggressive weight carries an entry, a class without carries none.

        Decision 6's headline case is **unexercisable over the 249** and is labelled rather than
        counted: hero's own jam lives only at the four-bet-facing spots the depth clause withholds,
        so every committed spot offers exactly one price and no class can hold two. The `cells[2]`
        assertion is what makes that a measurement rather than a claim - a later solve that offers
        two turns it red instead of quietly passing.
        """
        sizing = PreflopSizingTable.from_repo()
        cells: Counter[int] = Counter()
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            for hand_class_text, weights in hand_classes:
                entries = sizing.sizes_bb(spot_id, hand_class_text)
                assert (entries is not None) == (dict(weights).get("raise", 0.0) > 0.0), (
                    spot_id,
                    hand_class_text,
                )
                cells[0 if entries is None else len(entries)] += 1

        assert sum(cells.values()) == CELLS_AT_NON_ZERO_REACH
        assert cells[2] == 0, "VACUOUS: no committed spot offers two prices, so the list schema"
        assert set(cells) <= {0, 1}

    def test_every_committed_spot_offers_a_raise_so_nothing_prices_nothing(self, library) -> None:
        """The other half of the two-directional sizing invariant, vacuous the same way: a spot
        offering no raise carries no key, and the 249 contain no such spot. Every family ends in an
        aggressive action - the five open, the twenty-five raise or three-bet, the two hundred and
        nineteen four-bet - so the case cannot be exercised. Asserted as an equality rather than
        skipped, because the equality *is* the measurement and a later solve moves it."""
        sizing = PreflopSizingTable.from_repo()
        priced = {
            spot_id
            for spot_id, hand_classes in library.artifacts[0].action_weights
            if any(sizing.sizes_bb(spot_id, name) for name, _ in hand_classes)
        }

        assert len(priced) == COMMITTED_SPOTS
        assert set(library.spot_keys()) - priced == set()

    def test_every_entry_is_ordered_by_price_and_carries_the_classs_whole_share(
        self, library
    ) -> None:
        """The shape of an entry, read through the table rather than off the file. A class's
        weights sum to one, because a weight is that class's share of its **own** aggressive volume
        rather than of its range - the other reading of decision 6 is a pair summing to the class's
        raise frequency, which is what a converter writes when it forgets to renormalise. Over the
        249 the two readings coincide at every cell, one price carrying the whole share, so this is
        a schema check here rather than a measurement; `test_chart_conversion` owns the perturbed
        export that proves a price came from the action label and not from a constant."""
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

        assert 0 < checked < CELLS_AT_NON_ZERO_REACH

    def test_each_family_is_priced_at_the_one_price_its_depth_offers(self, library) -> None:
        """Prices are exactly 2.5, 7.5 and 22.5, and which one a spot quotes is fixed by how many
        raises hero faces rather than by anything else about the spot. Asserted per family because
        the set alone passes on a chart quoting the four-bet price at an opening spot; the stack
        price is asserted absent because that is the retired chart's whole sizing table - 36 spots,
        every one of them priced at a jam the ruled config cannot produce."""
        sizing = PreflopSizingTable.from_repo()
        quoted: dict[int, set[float]] = {0: set(), 1: set(), 2: set()}
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            for hand_class_text, _ in hand_classes:
                entries = sizing.sizes_bb(spot_id, hand_class_text) or ()
                quoted[raises_faced(spot_id)].update(round(to_bb, 6) for to_bb, _ in entries)

        assert quoted == {0: {OPEN_PRICE}, 1: {THREE_BET_PRICE}, 2: {FOUR_BET_PRICE}}
        assert float(RULED_CONFIG["stack"]) not in set().union(*quoted.values())
        assert set(RULED_PRICES) == set().union(*quoted.values())

    def test_the_price_in_a_key_is_what_the_seats_before_hero_were_offered(self, library) -> None:
        """The keys' own prices, which are the other seats' rather than hero's. A facing-an-open key
        spells 2.5 and a three-bet-facing key spells 2.5 then 7.5, strictly ascending, and no key
        spells the stack: hero is never asked to answer a jam over the committed 249."""
        for key in library.spot_keys():
            prices = prices_in(key)

            assert prices == sorted(set(prices)), key
            assert prices == list(RULED_PRICES[: raises_faced(key)]), key

    def test_the_small_blinds_open_prices_every_raising_class_at_the_open(self) -> None:
        """What the two-price assertion became once the jam left the tree. Aces carried one price
        and six classes carried two while the export offered an open-shove; under `add_allin:
        false` the shove is gone, so every class that raises here raises to 2.5 and `amount_bb`
        answers for all of them. 2.5 is `open_raises`, a constant the contract froze, so no
        permitted re-solve moves it. The fold count is left to the walk: it is the small blind's
        opening range, and a number typed here would be a second copy of it."""
        sizing = PreflopSizingTable.from_repo()
        open_to = float(RULED_CONFIG["open_raises"][0])
        counted = Counter(len(sizing.sizes_bb(rfi_key("SB"), name) or ()) for name in HAND_CLASSES)

        assert [price for price, _ in sizing.sizes_bb(rfi_key("SB"), "AA")] == [
            pytest.approx(open_to)
        ]
        assert sizing.amount_bb(rfi_key("SB"), "AA") == pytest.approx(open_to)
        assert sizing.sizes_bb(rfi_key("SB"), "72o") is None
        assert set(counted) == {0, 1}, counted
        assert counted[0] + counted[1] == len(HAND_CLASSES)

    def test_a_class_with_one_price_answers_amount_bb(self, library) -> None:
        """One price is an unambiguous answer, so the table gives it - at every priced cell in the
        chart now, rather than at the fifteen jam-only spots this used to find. Without it the
        invariant above reads as "the table never prices anything"."""
        sizing = PreflopSizingTable.from_repo()
        answered = 0
        for spot_id, hand_classes in library.artifacts[0].action_weights:
            for name, _ in hand_classes:
                entries = sizing.sizes_bb(spot_id, name)
                if entries is None:
                    continue
                answered += 1
                assert sizing.amount_bb(spot_id, name) == pytest.approx(entries[0][0]), (
                    spot_id,
                    name,
                )

        assert answered > 0

    @pytest.mark.parametrize(
        ("label", "spot_id"),
        [
            ("a stack depth no artifact covers", "t6/d40/CO/rfi"),
            (
                "a four-bet the depth clause refuses",
                "t6/d100/CO/CO:raise@2.5,BTN:raise@7.5,CO:raise@22.5,BTN:raise@100",
            ),
        ],
    )
    def test_an_uncovered_spot_has_no_size_rather_than_a_default(
        self, label: str, spot_id: str
    ) -> None:
        """Two ways to be uncovered, and neither may produce a price for any class. The second is
        the one this cutover created: the retired chart's sizing table held the four-bet family and
        priced every one of those spots at a jam, so a table keeping the price after the chart lost
        the range would let a strategy shove at a spot the chart refuses."""
        sizing = PreflopSizingTable.from_repo()

        for hand_class_text in ("AA", "AKo", "72o"):
            assert sizing.sizes_bb(spot_id, hand_class_text) is None, (label, hand_class_text)
            assert sizing.amount_bb(spot_id, hand_class_text) is None, (label, hand_class_text)
