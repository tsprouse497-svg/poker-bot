"""Phase 21, stage 4: a raise is keyed by its multiplier, and a flop object checked by its keys.

Authored before any implementation exists, from decision 16 of
`reports/phase_audits/decisions/PHASE_21_FLOP_CAMPAIGN_DECISIONS.md`, ruled by Taylor on 2026-10-03:
**a raise is named in the key by the multiplier the solve configures, which is exact, and a bet
keeps its percent of pot.** `THE-KEY-CANNOT-NAME-A-RAISE-THE-COMMITTED-MENU-HOLDS` carries the
diagnosis: the solve is configured `raise: "2.5x"`, a 2.5x raise over the 33 percent bet goes to
4.5375bb into 7.315bb, 62.030075... percent of pot, and a key refuses anything finer than a
hundredth, so eight of a flop's fourteen decision points had no key and the round 3 review could not
ask a fetched flop object to hold them.

**Why `BB:raise@2.5x`.** Every sized entry in both key grammars already carries its size after an
`@` - a preflop raise its raise-to in big blinds (`BTN:raise@2.5`), a flop bet its percent of pot
(`BTN:bet@33`) - so the multiplier goes in the same slot, rendered by the same `render_size_bb` to a
hundredth with trailing zeros stripped (never `2.50x`), and refused rather than rounded when finer.
The `x` is GTOpen's own token: `parse_sizes` in `crates/solver/src/tree.rs` reads a size ending in
`x` as `PrevMult`, so the key carries the string `solve_config.json` configures. Without it,
`raise@2.5` would read as 2.5 percent of pot, a third unit sharing one spelling. GTOpen raises
**to** the multiplier times the level faced (`legal_actions`: `st.street_bet[opp] * m`), so the
multiplier is the raise-to over the faced level, which is how a re-raise is read too.

**Where the menu is enforced.** The key names any exact multiplier, as it names any exact bet
percent; the harvest is where the solver's own number arrives, and it refuses a raise that is not
on the configured menu, naming the menu - a raise GTOpen clamped to all-in, say - rather than
snapping it onto `2.5x`. `FlopAction` gains a `multiplier` field: a raise carries it and no
`size_pct`, a bet the reverse, and a committed cell's `flop_actions` entry records it under the same
name, so the file and the key say the same thing.

**The count is derived, not copied.** `tests/fixtures/flop_campaign/flop_decision_points.json`
walks `tree.rs` `legal_actions` and `apply_action` over the committed configuration: 14 flop
decision points, seven a seat, of which eight follow a raise - four facing one and four facing a
re-raise, where `max_raises: 2` ends the tree. No flop raise on either tree shape is clamped, so
every one of them is exactly 2.5x. Missing modules are reached as in
`tests/test_flop_campaign_threads.py`; a name a module gains is reached through `owed` or the
`multiplier` guard below, so the red is an assertion and never a collection error.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from poker_training_bot.solver_artifacts import postflop_artifact as artifact
from poker_training_bot.solver_artifacts import postflop_harvest as harvest
from poker_training_bot.solver_artifacts import postflop_key as key
from poker_training_bot.solver_artifacts.postflop_sizing import CellAction
from poker_training_bot.solver_artifacts.schema import PreflopAction
from poker_training_bot.solver_artifacts.solve_conditions import BlindStructure
from scripts.repo_paths import REPO_ROOT
from tests.test_flop_campaign_manifest import (
    CLOSED_COUNTS,
    COMMITTED_LINE,
    FLOP_DECISION_POINTS,
    INDEX_KEY,
    SMALL_BLIND_LINE,
    DictStore,
    flop_object,
    flop_spot_keys,
    published_line,
    sha256,
)

POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
SAMPLE_DIR = POSTFLOP_DIR / "sample"
BOARD = ("Kh", "7d", "2c")
BET_33 = 0.33 * 5.5
"""The solver's 33 percent bet into 5.5, `1.8150000000000002` in binary, as it arrives."""
CHECK_RAISE_TO = 2.5 * BET_33
RE_RAISE_TO = 2.5 * CHECK_RAISE_TO
BUTTON_TAIL = "/p:5.5/e:97.5"


@pytest.fixture(scope="module")
def lines():
    """`solver_artifacts.postflop_lines`: the admitted lines and what each one's tree holds."""
    import poker_training_bot.solver_artifacts.postflop_lines as module

    return module


@pytest.fixture(scope="module")
def fetch():
    """`solver_artifacts.postflop_fetch`: the command a fresh machine runs, as a function."""
    import poker_training_bot.solver_artifacts.postflop_fetch as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; decision 16 requires it and no implementation"
        " has been written yet"
    )
    return found


def multiplier_is_carried() -> None:
    names = {field.name for field in dataclasses.fields(key.FlopAction)}
    assert "multiplier" in names, (
        "FlopAction must carry a raise's multiplier: decision 16 names a raise in the key by the"
        " multiplier the solve configures, and no implementation has been written yet"
    )


def raising(position: str, multiplier: float):
    multiplier_is_carried()
    return key.FlopAction(position, "raise", multiplier=multiplier)


def button_line(hero: str):
    return key.completed_preflop_line(
        6, 100, hero, (PreflopAction("BTN", "raise", 2.5), PreflopAction("BB", "call"))
    )


def button_key(hero: str, flop_actions) -> str:
    line = button_line(hero)
    return key.postflop_spot_key(line, BOARD, flop_actions, line.pot_bb, line.effective_stack_bb)


def check_and_bet():
    return (key.FlopAction("BB", "check"), key.FlopAction("BTN", "bet", 33.0))


# --------------------------------------------------------------------------- #
# The key names a raise by its multiplier
# --------------------------------------------------------------------------- #


class TestARaiseIsNamedByItsMultiplier:
    """Decision 16 (a). Each test fails on an implementation that keys a raise as a percent of
    pot, renders `2.50x`, or rounds a multiplier it cannot name exactly."""

    def test_a_raise_renders_as_the_configured_multiplier(self) -> None:
        assert key.render_flop_action(raising("BB", 2.5)) == "BB:raise@2.5x"

    def test_the_check_raise_key_names_the_bet_by_percent_and_the_raise_by_multiplier(self):
        """The button facing the big blind's check-raise: unnameable before this ruling."""
        spot = button_key("BTN", (*check_and_bet(), raising("BB", 2.5)))

        assert spot == (
            "f/b:Kh7d2c/t6/d100/BTN/BTN:raise@2.5,BB:call/f:BB:check,BTN:bet@33,BB:raise@2.5x"
            + BUTTON_TAIL
        )

    def test_a_re_raise_is_named_by_its_own_multiplier(self) -> None:
        spot = button_key("BB", (*check_and_bet(), raising("BB", 2.5), raising("BTN", 2.5)))

        assert spot.endswith("/f:BB:check,BTN:bet@33,BB:raise@2.5x,BTN:raise@2.5x" + BUTTON_TAIL)

    def test_a_raise_and_a_bet_of_one_number_are_two_keys(self) -> None:
        """The `x` is what keeps a multiplier from reading as a percent of pot."""
        multiplier_is_carried()
        bet = key.render_flop_action(key.FlopAction("BB", "bet", 2.5))

        assert bet == "BB:bet@2.5"
        assert key.render_flop_action(raising("BB", 2.5)) != bet.replace("bet", "raise")

    @pytest.mark.parametrize("percent", [62.03, 62.030075187969])
    def test_a_raise_keyed_as_a_percent_of_pot_is_refused(self, percent) -> None:
        multiplier_is_carried()
        with pytest.raises(ValueError):
            key.FlopAction("BB", "raise", percent)
        with pytest.raises(ValueError):
            key.FlopAction("BB", "raise", percent, multiplier=2.5)

    def test_a_raise_without_its_multiplier_is_refused(self) -> None:
        multiplier_is_carried()
        with pytest.raises(ValueError):
            key.FlopAction("BB", "raise")

    @pytest.mark.parametrize("action", ["bet", "check", "call", "fold"])
    def test_nothing_but_a_raise_carries_a_multiplier(self, action) -> None:
        multiplier_is_carried()
        size = 33.0 if action == "bet" else None
        with pytest.raises(ValueError):
            key.FlopAction("BTN", action, size, multiplier=2.5)

    @pytest.mark.parametrize("multiplier", [2.505, 2.501, 2.5 + 1e-7])
    def test_a_multiplier_finer_than_a_hundredth_is_refused_rather_than_rounded(self, multiplier):
        multiplier_is_carried()
        with pytest.raises(ValueError):
            key.FlopAction("BB", "raise", multiplier=multiplier)

    @pytest.mark.parametrize("multiplier", [1, 1.0, 0.5, 0, -2.5, True, "2.5x", "2.5", None])
    def test_a_multiplier_that_names_no_raise_is_refused(self, multiplier) -> None:
        """GTOpen's own `parse_sizes` refuses a multiple of one or less; a string is the config's
        spelling and not a number, and `None` is a raise without its size."""
        multiplier_is_carried()
        with pytest.raises(ValueError):
            key.FlopAction("BB", "raise", multiplier=multiplier)


class TestBetsKeepTheirPercent:
    """A bet's rendering is unchanged, so every key phase 16 committed is unchanged.
    The two regression tests here pass before stage 6 as well, which is the point of them."""

    def test_every_committed_cell_re_derives_its_own_key(self) -> None:
        cells = artifact.import_postflop_sample(SAMPLE_DIR)
        raw = {
            json.loads(path.read_text(encoding="utf-8"))["spot_key"]
            for path in SAMPLE_DIR.glob("*.json")
        }

        assert {cell.spot_key for cell in cells} == raw
        assert len(raw) == 4

    def test_the_committed_index_keys_are_the_five_phase_16_wrote(self) -> None:
        index = json.loads((POSTFLOP_DIR / "index.json").read_text(encoding="utf-8"))
        prefix = "f/b:{}/t6/d100/{}/BTN:raise@2.5,BB:call/f:{}" + BUTTON_TAIL

        assert sorted(entry["spot_key"] for entry in index["entries"]) == sorted(
            [
                prefix.format("9c8c7c", "BTN", "BB:check"),
                prefix.format("Kh7d2c", "BB", "none"),
                prefix.format("Kh7d2c", "BB", "BB:check,BTN:bet@33"),
                prefix.format("8c8d3c", "BB", "none"),
                prefix.format("Ac8c3c", "BB", "none"),
            ]
        )


class TestTheConfiguredRaiseMenu:
    def test_the_raise_menu_is_the_one_the_solve_configures_for_both_seats(self) -> None:
        menu = owed(key, "FLOP_RAISE_MENU")
        config = json.loads((POSTFLOP_DIR / "solve_config.json").read_text(encoding="utf-8"))
        configured = ",".join(f"{key.render_size_bb(entry)}x" for entry in menu)

        assert tuple(menu) == (2.5,)
        for seat in ("oop", "ip"):
            assert config["seats"][seat]["flop"]["raise"] == configured, seat


# --------------------------------------------------------------------------- #
# The harvest reads a raise off the solver as its multiplier, or refuses it
# --------------------------------------------------------------------------- #


def node_after(steps, hero: int, put) -> dict:
    """An `/api/node` answer as `flop_line` reads it: one history step per flop action, each
    with the pot as it stood and the menu it chose from, then the seat now deciding."""
    history = [
        {"player": player, "pot": pot, "chosen": 0, "actions": [{"kind": kind, "amount": amount}]}
        for player, pot, kind, amount in steps
    ]
    return {"history": [*history, {"player": hero}], "put": list(put)}


def check_raise_node(raise_to: float) -> dict:
    """The big blind checks, the button bets 33 percent and the big blind raises to `raise_to`;
    the button decides. Player 0 is the big blind, out of position, on the button's line."""
    steps = [(0, 5.5, "check", None), (1, 5.5, "bet", BET_33), (0, 5.5 + BET_33, "raise", raise_to)]
    return node_after(steps, 1, (2.75 + raise_to, 2.75 + BET_33))


SEATS = {0: "BB", 1: "BTN"}


class TestTheHarvestReadsARaiseAsItsMultiplier:
    def test_a_check_raise_is_harvested_as_exactly_two_and_a_half(self) -> None:
        multiplier_is_carried()
        line, street_bet = harvest.flop_line(check_raise_node(CHECK_RAISE_TO), SEATS, 5.5)

        assert [key.render_flop_action(entry) for entry in line] == [
            "BB:check",
            "BTN:bet@33",
            "BB:raise@2.5x",
        ]
        assert line[2].multiplier == 2.5
        assert line[2].size_pct is None
        assert street_bet == pytest.approx(BET_33)

    def test_a_re_raise_is_read_against_the_level_it_faced(self) -> None:
        """6.25 over the bet and 3.5 over what the raise added are the two wrong readings."""
        multiplier_is_carried()
        steps = [
            (0, 5.5, "bet", BET_33),
            (1, 5.5 + BET_33, "raise", CHECK_RAISE_TO),
            (0, 5.5 + BET_33 + CHECK_RAISE_TO, "raise", RE_RAISE_TO),
        ]
        node = node_after(steps, 1, (2.75 + RE_RAISE_TO, 2.75 + CHECK_RAISE_TO))

        line, _ = harvest.flop_line(node, SEATS, 5.5)

        assert [key.render_flop_action(entry) for entry in line] == [
            "BB:bet@33",
            "BTN:raise@2.5x",
            "BB:raise@2.5x",
        ]

    @pytest.mark.parametrize(
        "raise_to",
        [2.49 * BET_33, 2.51 * BET_33, 2.5 * (1 + 1e-7) * BET_33, 3.0 * BET_33, 97.5],
        ids=["2.49x", "2.51x", "a ten-millionth over", "3x", "clamped all-in"],
    )
    def test_a_raise_off_the_configured_menu_is_refused_naming_the_menu(self, raise_to) -> None:
        """Rounding to one decimal snaps the first two onto 2.5x, rounding to a hundredth the
        third; GTOpen clamps a raise to all-in when the stack is short, and that is no 2.5x."""
        multiplier_is_carried()
        with pytest.raises(harvest.HarvestError) as raised:
            harvest.flop_line(check_raise_node(raise_to), SEATS, 5.5)

        assert "2.5x" in str(raised.value)


class TestACellAfterARaiseRoundTrips:
    """What the harvest writes is what the importer re-derives: the produce side and the consume
    side of one cell agree on the key and on the pot hero decides into."""

    def document(self):
        multiplier_is_carried()
        committed = json.loads(
            (SAMPLE_DIR / "rainbow-dry-high-facing-a-bet.json").read_text(encoding="utf-8")
        )
        node = harvest.HarvestedNode(
            actions=(CellAction("fold"), CellAction("call"), CellAction("raise", RE_RAISE_TO)),
            hand_classes=tuple(committed["hand_classes"]),
            class_weights=tuple(tuple(row) for row in committed["class_weights"]),
            flop_actions=(*check_and_bet(), raising("BB", 2.5)),
            hero_street_bet_bb=BET_33,
            combos=len(committed["hand_classes"]),
            class_divergence=0.0,
            zero_reach_classes=0,
        )
        return harvest.cell_document(
            node,
            preflop_line=button_line("BTN"),
            board=BOARD,
            blinds=BlindStructure(0.5, 1.0, 0.0),
            price_substitutions=(("BTN", 2.5, 2.5),),
            achieved_exploitability_pct_of_pot=0.283,
            iterations=340,
        )

    def test_the_cell_is_written_and_imported_under_the_multiplier_key(self, tmp_path) -> None:
        """Hero's classes and weights are the committed facing-a-bet cell's, borrowed; what is
        tested is the key and the pot, not what the node plays."""
        document = self.document()
        path = tmp_path / "check-raised.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        cell = artifact.import_postflop_cell(path)

        assert document["flop_actions"][2] == {
            "position": "BB",
            "action": "raise",
            "multiplier": 2.5,
        }
        assert cell.spot_key == button_key("BTN", (*check_and_bet(), raising("BB", 2.5)))
        assert cell.pot_before_hero_bb == pytest.approx(5.5 + BET_33 + CHECK_RAISE_TO)

    def test_a_cell_that_records_its_raise_as_a_percent_is_refused(self, tmp_path) -> None:
        document = self.document()
        document["flop_actions"][2] = {"position": "BB", "action": "raise", "size_pct": 62.03}
        document["spot_key"] = document["spot_key"].replace("raise@2.5x", "raise@62.03")
        path = tmp_path / "percent.json"
        path.write_text(json.dumps(document), encoding="utf-8")

        with pytest.raises(artifact.PostflopArtifactError):
            artifact.import_postflop_cell(path)


# --------------------------------------------------------------------------- #
# Every flop decision point of a line has a key
# --------------------------------------------------------------------------- #


def fixture_actions(flop: str):
    """The fixture's flop segment as `FlopAction`s. A reader in a test, never in the module:
    the key module publishes no parser, and this one exists only to feed the producer."""
    if flop == "none":
        return ()
    built = []
    for entry in flop.split(","):
        position, action = entry.split(":")
        if "@" not in action:
            built.append(key.FlopAction(position, action))
        elif action.endswith("x"):
            built.append(raising(position, float(action.split("@")[1][:-1])))
        else:
            built.append(key.FlopAction(position, "bet", float(action.split("@")[1])))
    return tuple(built)


LATE_OPENERS = ("CO", "HJ", "LJ")


class TestEveryFlopDecisionPointHasAKey:
    """Closure needs every decision point nameable. Eight of fourteen follow a raise."""

    @pytest.mark.parametrize("line", [COMMITTED_LINE, SMALL_BLIND_LINE])
    def test_the_line_s_flop_keys_are_the_tree_s_fourteen(self, lines, line) -> None:
        found = owed(lines, "flop_spot_keys")(line, BOARD)

        assert len(found) == len(set(found)) == CLOSED_COUNTS["flop"]
        assert sorted(found) == sorted(flop_spot_keys(line, BOARD))

    @pytest.mark.parametrize("line", [COMMITTED_LINE, SMALL_BLIND_LINE])
    def test_eight_follow_a_raise_and_each_seat_holds_seven(self, lines, line) -> None:
        found = owed(lines, "flop_spot_keys")(line, BOARD)
        flop_segments = [spot.split("/f:")[1].split("/p:")[0] for spot in found]
        shape = FLOP_DECISION_POINTS["lines"][line]

        assert sum(":raise@" in segment for segment in flop_segments) == 8
        assert sum(point["after_a_raise"] for point in shape["decision_points"]) == 8
        assert all(
            part.endswith("@2.5x")
            for segment in flop_segments
            for part in segment.split(",")
            if ":raise@" in part
        )
        for seat in (shape["out_of_position"], shape["in_position"]):
            assert sum(spot.startswith(f"f/b:Kh7d2c/t6/d100/{seat}/") for spot in found) == 7

    @pytest.mark.parametrize("opener", LATE_OPENERS)
    def test_a_late_position_line_builds_the_button_s_tree_under_its_own_label(
        self, lines, opener
    ) -> None:
        line = COMMITTED_LINE.replace("BTN", opener)
        expected = [spot.replace("BTN", opener) for spot in flop_spot_keys(COMMITTED_LINE, BOARD)]

        assert sorted(owed(lines, "flop_spot_keys")(line, BOARD)) == sorted(expected)

    @pytest.mark.parametrize("line", [COMMITTED_LINE, SMALL_BLIND_LINE])
    def test_every_fixture_key_is_one_the_key_producer_derives(self, line) -> None:
        """Ties the fixture to the grammar: each of its keys is what `postflop_spot_key` writes
        for that line, which also proves every one is a node a dealer reaches."""
        shape = FLOP_DECISION_POINTS["lines"][line]
        opener = line.split(":")[0]
        for point, expected in zip(
            shape["decision_points"], flop_spot_keys(line, BOARD), strict=True
        ):
            preflop = key.completed_preflop_line(
                6,
                100,
                point["hero"],
                (PreflopAction(opener, "raise", 2.5), PreflopAction("BB", "call")),
            )
            derived = key.postflop_spot_key(
                preflop, BOARD, fixture_actions(point["flop"]), preflop.pot_bb, 97.5
            )
            assert derived == expected


# --------------------------------------------------------------------------- #
# A fetched flop object is checked by its contents
# --------------------------------------------------------------------------- #

FLOP_KEY = "postflop/btn-v-bb/8c8d3c.flop.json"
SECOND_BOARD = ("8c", "8d", "3c")


def with_flop_keys(keys):
    """The published line with the second board's flop object replaced by one holding `keys`,
    and the index and the manifest re-fingerprinted to match, so the digests and the counts
    all agree and only a check of the object's contents can see what is wrong."""
    manifest, index, objects = published_line()
    objects = dict(objects)
    objects[FLOP_KEY] = flop_object(keys)
    index["boards"][1]["objects"]["flop"]["sha256"] = sha256(objects[FLOP_KEY])
    objects[INDEX_KEY] = json.dumps(index, sort_keys=True).encode()
    manifest["index"]["sha256"] = sha256(objects[INDEX_KEY])
    manifest["index"]["bytes"] = len(objects[INDEX_KEY])
    return manifest, objects


FULL = flop_spot_keys(COMMITTED_LINE, SECOND_BOARD)
RE_RAISED_BB = next(spot for spot in FULL if "BB:raise@2.5x,BTN:raise@2.5x/" in spot)
CHECK_RAISED_BTN = next(
    spot for spot in FULL if spot.endswith("BTN:bet@33,BB:raise@2.5x" + BUTTON_TAIL)
)
THIRD_RAISE = (
    f"f/b:8c8d3c/t6/d100/BTN/{COMMITTED_LINE}"
    f"/f:BB:check,BTN:bet@33,BB:raise@2.5x,BTN:raise@2.5x,BB:raise@2.5x{BUTTON_TAIL}"
)
"""A key the grammar can write and the tree never builds: `max_raises: 2` stops at the second."""

WRONG_CONTENTS = {
    "a decision point after a re-raise is missing": [spot for spot in FULL if spot != RE_RAISED_BB],
    "the button's seven are missing": [spot for spot in FULL if "/t6/d100/BTN/" not in spot],
    "a raise the tree's two-raise cap never builds is extra": [*FULL, THIRD_RAISE],
    "a raise keyed as a percent of pot": [
        spot.replace("BB:raise@2.5x", "BB:raise@62.03") if spot == CHECK_RAISED_BTN else spot
        for spot in FULL
    ],
    "one decision point twice and another missing": [
        CHECK_RAISED_BTN if spot == RE_RAISED_BB else spot for spot in FULL
    ],
    "the small blind line's fourteen": flop_spot_keys(SMALL_BLIND_LINE, SECOND_BOARD),
}


class TestAFetchedFlopObjectIsCheckedByItsContents:
    """The round 3 blocker. The fetch reads each flop object it fetches as `{"cells": [...]}` and
    refuses it unless its cells' keys are exactly the line's flop decision points on that board,
    for both seats, after a raise as well as before. Counting cells is not enough: three of the
    six cases below hold fourteen."""

    def test_an_object_holding_every_decision_point_fetches(self, fetch, tmp_path) -> None:
        manifest, objects = with_flop_keys(FULL)

        owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        owed(fetch, "require_fetched")(manifest, tmp_path, street="flop")

    def test_the_fixture_fits_the_argument(self) -> None:
        """A guard on this file's own cases: three hold fourteen cells, so a count cannot tell."""
        assert len(FULL) == CLOSED_COUNTS["flop"]
        assert sum(len(keys) == len(FULL) for keys in WRONG_CONTENTS.values()) == 3
        assert THIRD_RAISE.count("raise@2.5x") == 3 and "/t6/d100/BTN/" in THIRD_RAISE

    @pytest.mark.parametrize("case", sorted(WRONG_CONTENTS))
    def test_an_object_whose_keys_are_not_the_tree_s_is_refused(self, fetch, tmp_path, case):
        manifest, objects = with_flop_keys(WRONG_CONTENTS[case])

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert raised.value.code == owed(fetch, "DECISION_POINTS_MISMATCH")

    def test_the_refusal_names_the_decision_point_that_is_missing(self, fetch, tmp_path) -> None:
        missing = WRONG_CONTENTS["a decision point after a re-raise is missing"]
        manifest, objects = with_flop_keys(missing)

        with pytest.raises(owed(fetch, "FetchError")) as raised:
            owed(fetch, "fetch_line")(manifest, DictStore(objects), tmp_path, streets=("flop",))

        assert RE_RAISED_BB in str(raised.value)
