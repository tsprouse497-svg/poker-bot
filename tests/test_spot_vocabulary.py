"""Phase 12: what a spot key can say, pinned from both sides.

Authored from `docs/phase_contracts/PHASE_12_SPOT_VOCABULARY.md` before any
implementation exists. Almost every test here is red on the branch point, because the
size is a new field on `PreflopAction` and constructing one is the first thing most of
these tests do. That kind of red is weaker than an assertion failure - the assertion
never runs, which is `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS` - so every expected
key string below was written out by hand against
`data/artifacts/preflop/sizings/six_max_nl25_100bb.json` rather than derived, and the
sections that can assert against today's code do.

This file pins the key itself: how a size renders, what an entry may carry, what a
sequence may say, and that the committed artifact re-derives under the new keys. What
the widened key then changes for everything downstream of it - the price normaliser,
the query and the answer, the corpus, the report - is
`tests/test_spot_vocabulary_downstream.py`, and `pytest_spot_vocabulary` runs both.

The surface this file pins, so stage 6 has no freedom to drift from it:

- `schema.render_size_bb(value) -> str`: hundredths, trailing zeros stripped.
- `schema.PreflopAction(position, action, size_bb=None)`: a raise requires a positive
  size in big blinds, anything else requires None.
- `schema.spot_key(...)`: unchanged signature. Renders `POS:raise@<size>` and
  `POS:call`. Accepts a position acting more than once. Rejects a sequence whose
  raises do not strictly increase, whose sizes cannot be paid at the stated depth, or
  which needs a folded seat to act again.
- `PreflopSizingTable.sizes_bb(spot_key, hand_class)`: the prices that hand class raises
  to at that spot with the weight hero gives each, in ascending price order, or None where
  the class has no aggressive weight there. **Two arguments, not one.** Phase 14's decision
  6 replaced the one-float-per-spot field this file used to read, and the 2026-08-26 ruling
  made the entry per hand class rather than per spot: at `t6/d100/BB/BTN:raise@2.5` the jam
  is 0.0 of hero's aggression on aces and 0.884 on 44 against a 0.076 spot aggregate, so
  one weight per spot would jam aces where the solve never does. Which price the strategy
  then draws is the strategy's claim rather than the vocabulary's, so nothing here asks.

  Two claims in this file changed meaning with the argument. The price VOCABULARY is still
  a whole-table claim and is now gathered across classes, because a price no class puts
  weight on is a price the table cannot put in front of hero. And "exactly the spots that
  raise carry an entry" gains its per-class half: within a spot, the classes the table
  prices must be exactly the classes the chart raises with.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from poker_training_bot.solver_artifacts import schema as schema_module
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

TABLE = 6
DEPTH = 100

# The big blind closing against a button open: export node `(0,0,0,1,0)`, every class at
# full reach, and the spot the per-class ruling was measured at.
TRACED_KEY = "t6/d100/BB/BTN:raise@2.5"


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


def key(hero: str, *entries: object) -> str:
    return schema_module.spot_key(TABLE, DEPTH, hero, tuple(entries))


def raise_weight(library: PreflopChartLibrary, spot: str, hand_class_text: str) -> float:
    """What the committed chart gives `raise` in one cell, or 0.0 where there is no cell.

    Read out of the artifact rather than out of `action_frequency_pct`, which is the
    combo-weighted figure over a whole spot and cannot say which classes carry it. A class
    the artifact never declares - hero's own range is normalised where hero has already
    acted, so the classes hero folded upstream are dropped - answers 0.0, which is what
    makes a sizing entry for such a class visible below rather than merely unused.
    """
    for artifact in library.artifacts:
        weights = artifact.weights_for(spot, hand_class_text)
        if weights is not None:
            return dict(weights).get("raise", 0.0)
    return 0.0


@pytest.fixture(scope="module")
def library() -> PreflopChartLibrary:
    return PreflopChartLibrary.from_directory(ARTIFACT_DIR)


@pytest.fixture(scope="module")
def sizing() -> PreflopSizingTable:
    return PreflopSizingTable.from_repo()


# --------------------------------------------------------------------------- #
# How a size renders
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("value", "rendered"),
    [
        (2.5, "2.5"),
        (7.5, "7.5"),
        (22.5, "22.5"),
        (11.0, "11"),
        (13.5, "13.5"),
        (2.25, "2.25"),
        (100.0, "100"),
        (0.5, "0.5"),
    ],
)
def test_a_size_renders_as_hundredths_with_trailing_zeros_stripped(value, rendered) -> None:
    """Taylor ruled this rendering on 2026-08-20 and it goes into committed data.

    Every case is a size the committed sizing table, the grammar or the corpus actually
    holds, so none is a shape nobody will meet. 2.5, 7.5 and 22.5 are the three the derived
    chart carries; 100 is the depth bound a key may still name even though no committed
    spot jams; 11 and 13.5 are corpus prices the normaliser has to render to answer.
    """
    assert schema_module.render_size_bb(value) == rendered


def test_a_size_finer_than_a_hundredth_is_rejected_rather_than_rounded() -> None:
    """Rounding would move a size into a neighbouring cell without saying so."""
    with pytest.raises(ValueError):
        schema_module.render_size_bb(2.255)


def test_rendering_is_injective_over_the_committed_sizes(library, sizing) -> None:
    """Two sizes must never render the same, or two spots collapse into one key.

    Decision 6 made a spot's entry every price it offers with hero's weight on each, and the
    2026-08-26 ruling put that entry under the hand class, so neither the table nor a spot
    has *a* size any more. The vocabulary is the union over every (spot, class) pair the
    table answers at, which is why this gathers across the 169 classes rather than asking
    each spot once: a per-spot read would report the menu, and the menu is not what the
    table can put in front of hero. The two readings agree here and it is not a tautology
    that they do - every price in every committed menu carries weight for at least one class,
    the 22.5 four-bet included, which lives only at the 219 spots facing a three-bet.

    The committed tree offers three prices - 2.5, 7.5 and 22.5 - which is tree shape and is
    pinned here. The 100bb stack went with the cutover: the export is solved `add_allin:
    false`, so hero's own jam lives only at the four-bet-facing spots the raise-depth clause
    refuses. The counter is the spots that contributed a price: all 249, because the no-raise
    half of the sizing invariant has no instance over the committed set - every committed
    spot offers hero a raise - so a table answering None anywhere fails here as well as in
    the invariant below rather than passing an empty union.
    """
    priced = {
        spot: {
            to_bb
            for hand_class_text in HAND_CLASSES
            for to_bb, _ in (sizing.sizes_bb(spot, hand_class_text) or ())
        }
        for spot in library.spot_keys()
    }
    prices = sorted({to_bb for found in priced.values() for to_bb in found})
    rendered = [schema_module.render_size_bb(price) for price in prices]

    assert prices == [2.5, 7.5, 22.5]
    assert len(set(rendered)) == len(prices)
    assert sum(1 for found in priced.values() if found) == 249


# --------------------------------------------------------------------------- #
# What a PreflopAction may carry
# --------------------------------------------------------------------------- #


def test_a_raise_entry_requires_a_size() -> None:
    """A sizeless raise is the v1 shape, and admitting it is admitting a wildcard."""
    with pytest.raises(ValueError):
        schema_module.PreflopAction("CO", "raise")


def test_a_raise_size_must_be_positive() -> None:
    with pytest.raises(ValueError):
        schema_module.PreflopAction("CO", "raise", 0.0)


def test_a_call_entry_must_not_carry_a_size() -> None:
    """A call pays a price the rest of the key already states."""
    with pytest.raises(ValueError):
        schema_module.PreflopAction("SB", "call", 2.5)


def test_a_call_entry_still_needs_no_size() -> None:
    assert call_by("SB").size_bb is None


# --------------------------------------------------------------------------- #
# The size in the key
# --------------------------------------------------------------------------- #


def test_facing_an_open_carries_the_openers_price() -> None:
    """The button facing a cutoff open, where the cutoff opened to the solved 2.5."""
    assert key("BTN", raise_to("CO", 2.5)) == "t6/d100/BTN/CO:raise@2.5"


def test_two_prices_are_two_spots() -> None:
    """The defect, in one line: these shared a cell in v1 and must not now."""
    cheap = key("BTN", raise_to("CO", 2.25))
    solved = key("BTN", raise_to("CO", 2.5))
    assert cheap != solved
    assert cheap == "t6/d100/BTN/CO:raise@2.25"


def test_the_opener_facing_a_three_bet_carries_both_prices() -> None:
    """LJ opened to 2.5, the button three-bet to 8, LJ is to act."""
    assert (
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0))
        == "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8"
    )


def test_a_second_opening_price_is_a_second_spot() -> None:
    """The vocabulary has to be able to say it whether or not a chart uses it.

    The raked chart opened the small blind to 3.5 and the rake-free solve opens everyone
    to 2.5, so this is now a key for a spot no committed artifact declares - which is the
    point: a grammar that could only spell the prices one solve happened to pick would
    have to be re-cut every time a solve is replaced.
    """
    assert key("BB", raise_to("SB", 3.5)) == "t6/d100/BB/SB:raise@3.5"
    assert key("BB", raise_to("SB", 2.5)) == "t6/d100/BB/SB:raise@2.5"


def test_a_limp_carries_no_price_and_reads_as_it_did() -> None:
    """Still a legal key, and since the cutover no longer a covered spot. The grammar
    and the coverage are different questions and this file only asks the first."""
    assert key("BB", call_by("SB")) == "t6/d100/BB/SB:call"


def test_a_cold_call_behind_an_open_carries_only_the_raisers_price() -> None:
    assert (
        key("BTN", raise_to("LJ", 2.5), call_by("CO")) == "t6/d100/BTN/LJ:raise@2.5,CO:call"
    )


def test_folded_to_hero_is_still_rfi_with_no_size_anywhere() -> None:
    assert key("BTN") == "t6/d100/BTN/rfi"


# --------------------------------------------------------------------------- #
# A position acting more than once
# --------------------------------------------------------------------------- #


def test_a_four_bet_spot_has_a_key() -> None:
    """The whole of SECOND-ORBIT-PREFLOP-SPOTS, in one assertion.

    LJ opens to 2.5, the button three-bets to 8, LJ four-bets to 21.5, and the button
    has to act. v1 rejects this outright: "v1 supports single-orbit spots only".
    """
    assert (
        key("BTN", raise_to("LJ", 2.5), raise_to("BTN", 8.0), raise_to("LJ", 21.5))
        == "t6/d100/BTN/LJ:raise@2.5,BTN:raise@8,LJ:raise@21.5"
    )


def test_the_deepest_sequence_the_committed_corpus_reached_has_a_key() -> None:
    """Five raises, which is what makes a two-orbit cap a cap set below evidence.

    `HJ:raise,CO:raise,HJ:raise,CO:raise,HJ:raise` occurs in the committed sample and
    is the reason decision 4 chose legality and stack depth over an orbit count.
    """
    assert key(
        "CO",
        raise_to("HJ", 2.5),
        raise_to("CO", 8.0),
        raise_to("HJ", 21.5),
        raise_to("CO", 50.0),
        raise_to("HJ", 100.0),
    ) == "t6/d100/CO/HJ:raise@2.5,CO:raise@8,HJ:raise@21.5,CO:raise@50,HJ:raise@100"


def test_a_limped_pot_that_got_raised_twice_has_a_key() -> None:
    """The one limped second-orbit row in the corpus inventory."""
    assert (
        key("BB", call_by("SB"), raise_to("BB", 3.5), raise_to("SB", 10.0))
        == "t6/d100/BB/SB:call,BB:raise@3.5,SB:raise@10"
    )


def test_a_seat_the_action_already_passed_cannot_act_later() -> None:
    """The small blind folded to the three-bet, so it cannot four-bet afterwards.

    This is the case a test authored from the first draft of the contract would have
    got backwards: absence means folded only once the action has gone by.
    """
    with pytest.raises(ValueError):
        key(
            "BTN",
            raise_to("LJ", 2.5),
            raise_to("BTN", 8.0),
            raise_to("LJ", 21.5),
            raise_to("SB", 50.0),
        )


def test_a_folded_seat_cannot_reappear_when_hero_is_not_in_the_way() -> None:
    """The fold rule on its own, with nothing else able to reject the sequence.

    `test_a_seat_the_action_already_passed_cannot_act_later` puts hero on the button,
    so the walk reaches hero before it reaches the folded seat and the rejection comes
    from the neighbouring rule that hero can never be folded. Both rules are right and
    the test could not tell them apart, which `check_gate_bite` proved by mutating the
    fold rule away and watching the suite stay green.

    Here hero opened and is out of the walk's path: LJ opens, the button three-bets, LJ
    four-bets - which passes the blinds and folds them - and the big blind then tries to
    five-bet. Nothing but the fold rule rejects that.
    """
    with pytest.raises(ValueError):
        key(
            "LJ",
            raise_to("LJ", 2.5),
            raise_to("BTN", 8.0),
            raise_to("LJ", 21.5),
            raise_to("BB", 50.0),
        )


def test_a_seat_still_to_act_in_the_first_orbit_may_appear() -> None:
    """The over-application guard for the rule above, and it holds on the branch point.

    After LJ opens and the button three-bets, the blinds are absent because their turn
    has not come. v1 accepts this and so must v2.
    """
    assert key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0)).endswith(
        "LJ:raise@2.5,BTN:raise@8"
    )


def test_hero_must_still_be_the_player_to_act_after_its_last_action() -> None:
    """A call behind hero does not give hero another turn, at any orbit depth."""
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), call_by("BTN"))


def test_a_seat_cannot_act_twice_in_a_row() -> None:
    """LJ opens, the button three-bets, and the button four-bets its own three-bet.

    The live set is LJ and the button, so the order alternates. Nothing about a second
    orbit lets one seat take two turns running.
    """
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 8.0), raise_to("BTN", 21.5))


# --------------------------------------------------------------------------- #
# What the sizes in the key let the key check
# --------------------------------------------------------------------------- #


def test_a_raise_beyond_the_stated_depth_is_rejected() -> None:
    """A check the key could not perform before it carried sizes.

    It is also what stops an uncapped orbit count admitting a five-bet to 300bb in a
    100bb game.
    """
    with pytest.raises(ValueError):
        key("BTN", raise_to("CO", 100.5))


def test_a_raise_exactly_at_the_stated_depth_is_accepted() -> None:
    """All-in is a legal raise, so the bound is inclusive."""
    assert key("BTN", raise_to("CO", 100.0)) == "t6/d100/BTN/CO:raise@100"


def test_raises_must_strictly_increase_along_the_sequence() -> None:
    """A three-bet to less than the open it faces is not a three-bet."""
    with pytest.raises(ValueError):
        key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 2.5))


def test_a_short_all_in_re_raise_is_still_an_increase() -> None:
    """The guard for the rule above: a raise can be small without being flat."""
    assert key("LJ", raise_to("LJ", 2.5), raise_to("BTN", 3.0)).endswith("BTN:raise@3")


# --------------------------------------------------------------------------- #
# The committed artifact, re-keyed
# --------------------------------------------------------------------------- #


def test_every_committed_raise_entry_carries_a_size(library) -> None:
    """Asserts against today's artifact, so this red is a real assertion failure.

    The empty list on its own would be satisfied by a chart holding no raise entries at
    all, so the counter says how many keys the filter really read a price out of: 244 of the
    249, every key but the five where nobody has raised in front of hero. Those five are the
    committed first-in spots, and they are the whole of that family because only five seats
    can ever be first in six-handed - the big blind is never folded to, it is walked.
    """
    keys = library.spot_keys()
    sizeless = [
        spot_key_text
        for spot_key_text in keys
        if ":raise" in spot_key_text and ":raise@" not in spot_key_text
    ]

    assert sizeless == []
    assert sum(1 for spot_key_text in keys if ":raise@" in spot_key_text) == 244
    assert sorted(
        spot_key_text for spot_key_text in keys if ":raise@" not in spot_key_text
    ) == [f"t6/d100/{seat}/rfi" for seat in ("BTN", "CO", "HJ", "LJ", "SB")]


def test_the_committed_spot_count_is_the_one_the_artifact_declares(library) -> None:
    """Phase 12 asserted 36 here, on the argument that re-keying is not re-solving.

    Phase 14 re-selects, so the number moves to 249: 5 first-in, 25 facing an open and 219
    facing a three-bet, what the ruled three-clause predicate keeps out of the export's
    33,969 action nodes. That is tree shape rather than solve output, so it is pinned rather
    than floored - a floor would pass for any rule that kept more than the retired chart,
    which is exactly the confusion decision 1's two supersessions left behind. What survives
    from phase 12 is the half re-keying was really guarding: the keys the library exposes and
    the count the artifact audits itself against are one number, so a re-keying that dropped
    or collided a spot cannot pass silently.
    """
    assert len(library.spot_keys()) == library.artifacts[0].audit_fields.spot_count
    assert len(library.spot_keys()) == 249


SEATS_IN_ACTION_ORDER = ("LJ", "HJ", "CO", "BTN", "SB", "BB")


def facing_an_open_keys() -> set[str]:
    """The facing-an-open family, enumerated here rather than read off the artifact.

    Three ruled clauses decide it and all three are readable from a key. At most two raises
    are in, so this family carries exactly one. The bot never cold-calls but opponents do,
    so one opponent may already have flat-called - decision 46 admits the single-cold-caller
    spots, and decision 48 takes back only the ones where hero is the big blind. Everyone
    opens to 2.5, the one price the first-in family carries.

    That is every strictly-ordered (opener, hero) pair and every strictly-ordered (opener,
    cold caller, hero) triple whose hero is not the big blind: fifteen and ten. Their sum is
    the ruled 25, which is what makes this enumeration a derivation rather than a guess.
    """
    keys: set[str] = set()
    for opener_index, opener in enumerate(SEATS_IN_ACTION_ORDER):
        opened = (raise_to(opener, 2.5),)
        for hero_index, hero in enumerate(SEATS_IN_ACTION_ORDER[opener_index + 1 :],
                                          opener_index + 1):
            keys.add(key(hero, *opened))
            if hero == "BB":
                continue
            for caller in SEATS_IN_ACTION_ORDER[opener_index + 1 : hero_index]:
                keys.add(key(hero, *opened, call_by(caller)))
    return keys


def test_the_committed_keys_are_the_measured_ones(library) -> None:
    """Hand-checked keys on both sides of the ruled predicate, each one walked.

    Keep a node when at most two raises are already in, when under a tenth of its decision
    mass reaches a multiway flop, and when it is not the big blind's squeeze.

    Kept: the lojack's own open, one of the five first-in spots; the big blind facing a
    cutoff open; the button facing a cutoff open, which the retired predicate refused for
    having players behind it and the exposure clause admits; the button facing an open with
    the cutoff cold-calling in front, because the bot's never cold-calling says nothing
    about the opponents'; and the opener facing a three-bet.

    Refused, and this is the ruled cost rather than a gap. `t6/d100/BB/CO:raise@2.5,
    BB:raise@7.5,CO:raise@22.5` has three raises in - hero faces a four-bet - and the whole
    four-bet family goes with the raise-depth clause, which is what retires every key
    carrying a 22.5 and every key naming one seat twice. `t6/d100/BB/CO:raise@2.5,BTN:call`
    is the same shape as the button's admitted squeeze with hero in the big blind, and
    decision 48 refuses exactly those ten. `t6/d100/BB/SB:call` passes every clause and
    still has no node, because the solve is `limp: false`.
    """
    keys = set(library.spot_keys())
    assert "t6/d100/LJ/rfi" in keys
    assert "t6/d100/BB/CO:raise@2.5" in keys
    assert "t6/d100/BTN/CO:raise@2.5" in keys
    assert "t6/d100/BTN/LJ:raise@2.5,CO:call" in keys
    assert "t6/d100/LJ/LJ:raise@2.5,BTN:raise@7.5" in keys
    assert "t6/d100/BB/CO:raise@2.5,BB:raise@7.5,CO:raise@22.5" not in keys
    assert "t6/d100/BB/CO:raise@2.5,BTN:call" not in keys
    assert "t6/d100/BB/SB:call" not in keys

    expected = facing_an_open_keys()

    assert len(expected) == 25
    assert expected <= keys
    assert {spot for spot in keys if spot.count(":raise") == 1} == expected


def test_exactly_the_spots_that_raise_carry_a_sizing_entry(library, sizing) -> None:
    """The key says what hero faces; the sizing table says what hero may raise to.

    They are indexed the same way, so a re-keying that moved one and not the other would
    leave every raise refusing for no committed size. After the cutover the table holds all
    249: the no-raise half of the invariant has no instance, because every committed spot
    offers hero a raise - the first-in spots open, the facing-an-open spots three-bet, and
    the three-bet-facing spots four-bet. Absence would still be `sizes_bb` returning None
    rather than an empty list, because an empty list is a spot that raises for no price
    wearing the shape of a spot that cannot raise.

    The invariant is two-directional on purpose. A priced spot the ranges never raise at
    is a price for an action the chart does not offer; an unpriced spot the ranges do
    raise at is a raise the strategy cannot make.

    Since 2026-08-26 it is two-directional inside a spot as well, and that half is the one
    a per-spot table cannot satisfy: the classes the table prices at a spot must be exactly
    the classes the chart raises with there. A table carrying one entry for the whole spot
    would price the classes that only ever fold or call at `t6/d100/BB/BTN:raise@2.5`. That
    is caught by the set equality rather than by a count, so it cannot hide in a total.

    The two-price schema itself is **vacuous over the committed 249** and is labelled so
    rather than counted as a check that passed: `add_allin: false` leaves each spot one
    named raise, so no class anywhere is offered two. The vacuity premise is asserted before
    it is relied on - a build that reintroduced a second price would fail here rather than
    slip past an empty list - and decision 6's schema is proved against a synthetic export
    elsewhere. Aces are pinned at the one price the traced spot offers.
    """
    covered = set(library.spot_keys())
    raising = {key for key in covered if library.action_frequency_pct(key, "raise") > 0.0}
    priced = {
        spot: {
            hand_class_text
            for hand_class_text in HAND_CLASSES
            if sizing.sizes_bb(spot, hand_class_text) is not None
        }
        for spot in covered
    }

    assert {spot for spot, classes in priced.items() if classes} == raising
    assert set(sizing.raise_to_bb) <= covered
    assert len(raising) == 249
    assert covered - raising == set()

    for spot in sorted(covered):
        charted = {
            hand_class_text
            for hand_class_text in HAND_CLASSES
            if raise_weight(library, spot, hand_class_text) > 0.0
        }
        assert priced[spot] == charted, spot

    offered = [
        (spot, hand_class_text, sizing.sizes_bb(spot, hand_class_text))
        for spot, classes in priced.items()
        for hand_class_text in sorted(classes)
    ]
    two_priced = [(spot, name) for spot, name, prices in offered if len(prices) > 1]

    assert offered, "no priced class anywhere, so the vacuity below states nothing"
    assert two_priced == [], "the two-price schema is vacuous only while this holds"
    assert [to_bb for to_bb, _ in sizing.sizes_bb(TRACED_KEY, "AA")] == [7.5]


def test_the_artifact_re_derives_from_its_source() -> None:
    """`convert_preflop_export.py --check` is what makes the re-keying auditable.

    Green at the branch point, so this is an over-application guard: a chart nobody can
    regenerate is a chart nobody can diff against its origin, and re-keying must not
    cost that property.
    """
    completed = subprocess.run(
        [sys.executable, "scripts/convert_preflop_export.py", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


