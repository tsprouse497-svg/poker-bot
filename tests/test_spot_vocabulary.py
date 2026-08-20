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
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from poker_training_bot.solver_artifacts import schema as schema_module
from poker_training_bot.solver_artifacts.lookup import PreflopChartLibrary
from poker_training_bot.strategy.preflop_chart import ARTIFACT_DIR
from poker_training_bot.strategy.preflop_sizing import PreflopSizingTable

TABLE = 6
DEPTH = 100


def raise_to(position: str, size_bb: float) -> object:
    """A raise entry carrying its raise-to size, in big blinds."""
    return schema_module.PreflopAction(position, "raise", size_bb)


def call_by(position: str) -> object:
    return schema_module.PreflopAction(position, "call")


def key(hero: str, *entries: object) -> str:
    return schema_module.spot_key(TABLE, DEPTH, hero, tuple(entries))


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
        (8.0, "8"),
        (11.0, "11"),
        (13.5, "13.5"),
        (2.25, "2.25"),
        (21.5, "21.5"),
        (100.0, "100"),
        (0.5, "0.5"),
    ],
)
def test_a_size_renders_as_hundredths_with_trailing_zeros_stripped(value, rendered) -> None:
    """Taylor ruled this rendering on 2026-08-20 and it goes into committed data.

    Every case is a size the committed sizing table or the corpus actually holds, so
    none of them is a shape nobody will meet.
    """
    assert schema_module.render_size_bb(value) == rendered


def test_a_size_finer_than_a_hundredth_is_rejected_rather_than_rounded() -> None:
    """Rounding would move a size into a neighbouring cell without saying so."""
    with pytest.raises(ValueError):
        schema_module.render_size_bb(2.255)


def test_rendering_is_injective_over_the_committed_sizes(sizing) -> None:
    """Two sizes must never render the same, or two spots collapse into one key."""
    sizes = sorted(set(sizing.raise_to_bb.values()))
    rendered = [schema_module.render_size_bb(size) for size in sizes]
    assert len(set(rendered)) == len(sizes)


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


def test_a_small_blind_open_carries_its_own_larger_price() -> None:
    """The tree already has two opening prices: the small blind opens to 3.5."""
    assert key("BB", raise_to("SB", 3.5)) == "t6/d100/BB/SB:raise@3.5"


def test_a_limp_carries_no_price_and_reads_as_it_did() -> None:
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
    """Asserts against today's artifact, so this red is a real assertion failure."""
    sizeless = [
        spot_key_text
        for spot_key_text in library.spot_keys()
        if ":raise" in spot_key_text and ":raise@" not in spot_key_text
    ]
    assert sizeless == []


def test_the_committed_artifact_still_holds_thirty_six_spots(library) -> None:
    """Re-keying is not re-solving. Each prefix admits one solved size, so the count
    does not move, which is what makes the size free in cells."""
    assert len(library.spot_keys()) == 36


def test_the_committed_keys_are_the_measured_ones(library) -> None:
    """Five hand-checked keys, each traceable to a sizing entry by a reader.

    `t6/d100/CO/rfi` is 2.5 and `t6/d100/BTN/LJ:raise` is 8.0, which is where the two
    prices in the three-bet key below come from.
    """
    keys = set(library.spot_keys())
    assert "t6/d100/BTN/CO:raise@2.5" in keys
    assert "t6/d100/BB/SB:raise@3.5" in keys
    assert "t6/d100/BB/SB:call" in keys
    assert "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8" in keys
    assert "t6/d100/SB/SB:raise@3.5,BB:raise@10.5" in keys


def test_every_sizing_key_is_a_key_the_artifact_declares(library, sizing) -> None:
    """The key says what hero faces; the sizing table says what hero does. They are
    indexed the same way, so a re-keying that moved one and not the other would leave
    every raise refusing for no committed size."""
    assert set(sizing.raise_to_bb) == set(library.spot_keys())


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


