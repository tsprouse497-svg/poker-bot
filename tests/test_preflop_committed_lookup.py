"""What the committed chart does when it is *asked* something, rather than what it holds.

Split from `tests/test_preflop_committed_charts.py` at the 700-line cap. That file owns the
chart's contents - the 249 keys, the menus, the cells, the sizing table. This one owns the
contract's runtime half: **an excluded node is a lookup miss, refused with a code naming the
spot, no neighbouring cell and no price substitution consulted.** The helpers and the counts come
from the sibling as a module, so a number lives in one file and is read in two.

The cutover reverses claims in both directions and every one is kept as its reversal rather than
deleted. Four opening ranges the 86 refused are answered. The cutoff facing a lojack open comes
back. A squeeze in front of a non-blind seat comes back. The big blind's four-bet defence, which
the 86 answered, is refused, and so is every other spot with three raises already in. A test that
only ever asserted in one direction cannot tell one selection rule from another.
"""

from __future__ import annotations

import pytest

# The sibling as a module rather than by name: the counts, the key helpers and the price
# constants all live where the chart's contents are on trial, and `charts.` says so at each use.
import test_preflop_committed_charts as charts

from poker_training_bot.solver_artifacts.importer import import_preflop_artifacts
from poker_training_bot.solver_artifacts.lookup import (
    ChartHit,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction

DEPTH_BB = charts.DEPTH_BB


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_artifacts(import_preflop_artifacts(charts.ARTIFACT_DIR))


def test_lookup_hits_the_committed_chart_from_hole_cards(library: PreflopChartLibrary) -> None:
    result = library.lookup_hole_cards(6, 100, "SB", (), ("Ah", "As"))

    assert isinstance(result, ChartHit)
    assert result.spot_key == charts.rfi_key("SB")
    assert result.hand_class == "AA"
    assert result.best_action == "raise"


def test_lookup_hits_the_defence_spot(library: PreflopChartLibrary) -> None:
    expected = charts.solved_key(library, "BB", "CO")

    result = library.lookup(
        ChartQuery(6, 100, "BB", charts.solved_line(library, "BB", "CO"), "AA")
    )

    assert isinstance(result, ChartHit)
    assert result.spot_key == expected


def test_the_big_blind_squeeze_spots_are_refused(library: PreflopChartLibrary) -> None:
    """Decision 48's ten, asserted as the refusal they became. They passed the exposure filter
    *because* the big blind folds 93 percent there, so almost no mass reaches the three-way flop:
    the filter is blindest exactly where the mispricing has already turned a call into a fold. The
    failure is silent without this - a converter on the first two clauses commits all ten and every
    one converts, imports, keys legally and answers, at a defence of 6.67 to 15.01 percent while
    closing the action getting better than four to one."""
    sequence = (*charts.solved_line(library, "BB", "LJ"), PreflopAction("HJ", "call"))

    result = library.lookup(ChartQuery(6, 100, "BB", sequence, "AA"))
    committed = [
        key
        for key in library.spot_keys()
        if charts.hero_seat(key) == "BB"
        and charts.raises_faced(key) == 1
        and charts.cold_callers(key) > 0
    ]

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"
    assert result.spot_key is not None
    assert result.spot_key.endswith("HJ:call")
    assert result.price_substitutions == ()
    assert committed == [], "no big-blind squeeze spot may be committed"


def test_a_squeeze_in_front_of_a_non_blind_seat_is_answered(library: PreflopChartLibrary) -> None:
    """The reversal of what the 86 said, and the general form decision 52 names: a cold call in
    front of hero refuses nothing on its own. Ten such spots are committed and the button facing a
    lojack open with the cutoff already in is one. Under the retired predicate it failed twice over
    - two opponents invested and three players live - and decision 46 measures its exposure over
    the branches the bot can take at under ten percent, because the button's answer is a three-bet
    or a fold and neither of those makes the flop three-handed."""
    sequence = (*charts.solved_line(library, "BTN", "LJ"), PreflopAction("CO", "call"))

    result = library.lookup(ChartQuery(6, 100, "BTN", sequence, "AA"))

    assert isinstance(result, ChartHit)
    assert result.spot_key.endswith("CO:call")
    assert result.best_action == "raise"


def test_the_big_blind_facing_a_four_bet_is_refused_again(library: PreflopChartLibrary) -> None:
    """The reversal in the other direction, and the one this pair of files most owes. Phase 12 gave
    this cell a key, the raked chart had no four-bet node to fill it, and the 86 answered it. The
    depth clause takes it back: three raises are already in, so the spot is beyond the committed
    raise depth and the whole four-bet family goes with it - the family whose terminal the source
    has not fitted (`THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL`). Deleting this test would
    leave a widening that reinstates 33,362 nodes unopposed."""
    result = library.lookup(
        ChartQuery(6, 100, "BB", charts.solved_line(library, "BB", "CO", "BB", "CO"), "AA")
    )
    deeper = [key for key in library.spot_keys() if charts.raises_faced(key) > 2]

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"
    assert deeper == [], "nothing past a three-bet is committed"


def test_the_small_blind_answers_a_button_open_and_refuses_the_four_bet_behind_it(
    library: PreflopChartLibrary,
) -> None:
    """The pair of spots that makes the selection rule legible, inverted from what the 86 said.
    Facing a button open the small blind now answers - it raises or folds, and the two seats behind
    it cannot make that pot multiway often enough to matter. Three-bet it, have the button
    four-bet, and the small blind is refused: the clause is about how much money is already in, not
    about how many seats are live. Both keys are built from prices the chart declares, so neither
    assertion is about a price, and the empty substitution list proves nothing was repriced."""
    facing_open = library.lookup(
        ChartQuery(6, 100, "SB", charts.solved_line(library, "SB", "BTN"), "AA")
    )
    four_bet = library.lookup(
        ChartQuery(6, 100, "SB", charts.solved_line(library, "SB", "BTN", "SB", "BTN"), "AA")
    )

    assert isinstance(facing_open, ChartHit)
    assert facing_open.spot_key == f"t6/d{DEPTH_BB}/SB/BTN:raise@{charts.OPEN_PRICE}"
    assert facing_open.price_substitutions == ()

    assert isinstance(four_bet, ChartMiss)
    assert four_bet.code == "lookup:spot-not-covered"
    assert four_bet.price_substitutions == ()


def test_the_cutoff_facing_a_lojack_open_is_answered_again(library: PreflopChartLibrary) -> None:
    """Phase 04's chart missed this spot, the raked chart held it, the 86 refused it, and it comes
    back. It was the clearest case of the coverage the full-table export bought, and it is the
    clearest case of what decision 46 returned."""
    result = library.lookup(
        ChartQuery(6, 100, "CO", charts.solved_line(library, "CO", "LJ"), "AA")
    )

    assert isinstance(result, ChartHit)
    assert result.spot_key == f"t6/d{DEPTH_BB}/CO/LJ:raise@{charts.OPEN_PRICE}"


def test_a_limped_pot_is_refused_because_the_solve_holds_no_limp(
    library: PreflopChartLibrary,
) -> None:
    """The coverage this phase gave up and did not get back. Limps left the solve at phase 10's
    human gate - 87 percent of the tree, and hero never limps - so the export is `limp: false` and
    holds no limped node. It is the one refusal here that no selection clause caused: the spot
    passes all three and has nothing to derive from."""
    result = library.lookup(ChartQuery(6, 100, "BB", (PreflopAction("SB", "call"),), "AA"))

    assert isinstance(result, ChartMiss)
    assert result.code == "lookup:spot-not-covered"


def test_a_hand_the_lojack_cannot_hold_facing_a_three_bet_is_refused(
    library: PreflopChartLibrary,
) -> None:
    """72o is not in the lojack's opening range, so no three-bet cell can hold it. A different code
    from every other refusal here: the spot is covered and the holding is not."""
    result = library.lookup(
        ChartQuery(6, 100, "LJ", charts.solved_line(library, "LJ", "LJ", "CO"), "72o")
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
            # What no legal preflop order produces: the cutoff acts before the button. These four
            # are vocabulary properties, so the cutover leaves them alone.
            "the button raising in front of the cutoff",
            ChartQuery(6, 100, "CO", (PreflopAction("BTN", "raise", charts.OPEN_PRICE),), "AA"),
            "lookup:unrepresentable-spot",
        ),
        (
            # The fifth is the one the selection rule creates, and it reaches a code the other four
            # cannot: a legal, expressible, six-handed, 100bb spot at a position that exists, and
            # uncovered. It used to be the lojack's open, which is committed now; it is the
            # four-bet family instead, which is what the depth clause withholds.
            "a four-bet the depth clause withholds",
            ChartQuery(
                6,
                100,
                "CO",
                (
                    PreflopAction("CO", "raise", charts.OPEN_PRICE),
                    PreflopAction("BTN", "raise", charts.THREE_BET_PRICE),
                    PreflopAction("CO", "raise", charts.FOUR_BET_PRICE),
                    PreflopAction("BTN", "raise", 100.0),
                ),
                "AA",
            ),
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
