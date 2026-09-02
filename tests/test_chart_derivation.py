"""Phase 14: which solved nodes become committed spots, and why the others do not.

Authored at stage 4, before the derivation the rulings require exists, so this file is the
specification rather than a description of what got built. It owns the predicate, the three
withholdings that take forty-five spots back, the six-way census and the five exclusion codes.
`test_chart_conversion.py` owns what a committed row costs and `test_chart_arrival_probability.py`
the walk's own tests; both import this file's nodes rather than copying them.

**Four rulings decide the committed set, and they stay separate because they are separate
rulings.** Decision 1 keeps a node when at most one opponent has voluntarily invested beyond the
blinds *and* at most two players are still live; it selects **51**. Decision 20 withholds the
fifteen where hero **faces a four-bet**, the `calibrated` fit having no four-bet-pot cell.
Taylor's first ruling of 2026-09-01 withholds the fifteen where hero **faces a five-bet jam**,
hero's answer to a jam range computed at those very nodes. His second withholds the fifteen
where hero **faces a three-bet**, which sit above those nodes and weigh their own raise branch
entirely on them. That leaves **6 committed**: the small blind's open, and the big blind's
answer to each of the five opens.

**The three withheld families are exactly `raises_faced >= 2`, and are still counted apart**,
because the census has to say which nodes a later fix recovers. The histogram over the 51 is 0
raises 1 spot, 1 raise 5, 2 raises 15, 3 raises 15, 4 raises 15, so the committed 6 are 1 + 5.
All three withheld counts are 15, so no total catches a build that swapped two of them.

**Why the three-bet spots went, in poker.** Over the twenty-one spots committed until
2026-09-01 there are twenty places where a higher pocket pair is played less often than the pair
one rank below, past decision 10's one-point tolerance, across twelve of the twenty-one. All
twenty sit in three-bet-facing spots and none in the six that remain; seven are outright, the
lojack folding 33 and playing 22 at 100 against four different three-bettors. The contract names
that shape and its disposition - "A shape like that is a halt and a decision, not a caveat."

Every count is recomputed from the export by a walk written here, because a test that imports
the rule it checks is one copy of a rule agreeing with another, and what is pinned is tree shape
rather than solve output. **`selected` means committed** - sibling files import it - while
`predicate_selects` is decision 1 alone and the three `faces_a_*` are the withholdings.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

# `lookup` as a module rather than by name for the derivation codes: the three decision 20 and
# the 2026-09-01 rulings require do not exist until stage 6, and naming them here would hide
# every assertion behind one ImportError.
from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverExport,
    SolverNode,
    class_combos,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import MISS_CODES
from poker_training_bot.solver_artifacts.schema import PreflopAction, spot_key

TABLE_SIZE = 6
DEPTH_BB = 100
SEATS = ("LJ", "HJ", "CO", "BTN", "SB", "BB")

# The shape `lookup.py` uses for every refusal it publishes; the derivation codes share it.
NAMESPACED_CODE = re.compile(r"\A[a-z]+:[a-z0-9-]+\Z")

# The three withholding reasons, spelled here because this file is what names them for stage 6.
FOUR_BET_POT_CODE = "derivation:source-misprices-four-bet-pot"
JAM_INHERITS_CODE = "derivation:inherits-a-mispriced-four-bet-node"
THREE_BET_BRANCH_CODE = "derivation:weighs-a-mispriced-four-bet-branch"
"""Three reasons rather than one repeated, because a reader has to tell which node is wrong.
All three return by the same fix - a realization fit with a four-bet-pot cell - so by the
contract's test one code would do. The four-bet node is itself mispriced; the jam node after it
prices fine and `inherits` a range computed there; the three-bet node before it prices fine too
and `weighs` its own raise branch on that node's value, the mispricing arriving from the child
rather than the parent. The word is the contract's: the committed three-bet spots "weigh hero's
four-bet on terminals the fit has no cell for"."""

# Tree facts: decision 2 permits a re-solve at the ruled config and nothing else.
EXPORTED_NODES = 33_969
PREDICATE_NODES = 51
COMMITTED_NODES = 6
WITHHELD_THREE_BET_NODES = 15
WITHHELD_FOUR_BET_NODES = 15
WITHHELD_JAM_NODES = 15
HISTORY_CLAUSE_NODES = 65
SUBTREE_CLAUSE_NODES = 4_865
HISTORY_BUT_NOT_CLEAN = 14
RETIRED_FLOOR_BP = 200
"""Decision 1's retired 2-percent reach floor, kept only to assert it selects nothing the ruled
predicate does not - which is what made it a retirement rather than a retune."""

# The other two buckets. A node with a multiway terminal still reachable takes the multiway
# code, which a later phase reads to find what returns once GTOpen prices three-way.
MISPRICED_MULTIWAY_NODES = 29_104
OUTSIDE_RULE_NODES = 4_814

# All three withholdings in one table: raises already in the pot, over the 51.
RAISES_FACED_OVER_THE_PREDICATE = {0: 1, 1: 5, 2: 15, 3: 15, 4: 15}
RAISES_FACED_WHEN_COMMITTED = {0: 1, 1: 5}
THREE_BET_RAISE_COUNT = 2
FOUR_BET_RAISE_COUNT = 3
FIVE_BET_RAISE_COUNT = 4
COMMITTED_UNDER_TWO_OR_MORE = 6
"""What a single `raises_faced >= 2` filter commits: the right total since the second
2026-09-01 ruling and still the wrong rule, unable to say which reason refused a node."""

# The spot the contract asks a non-coding reviewer to follow end to end: the big blind closing
# against a button open on fold, call and a three-bet to 7.5, six-max's most-played decision.
TRACED_PATH = (0, 0, 0, 1, 0)
TRACED_KEY = "t6/d100/BB/BTN:raise@2.5"
TRACED_SEQUENCE = (PreflopAction("BTN", "raise", 2.5),)

# The one opening range the cutover commits, and the only committed spot offering hero a raise
# and no call - `CHART-HERO-MUST-NEVER-LIMP` holding by construction.
SB_OPEN_PATH = (0, 0, 0, 0)
SB_OPEN_KEY = "t6/d100/SB/rfi"

# The five opens the big blind answers; with the small blind's own open they are the six spots
# hero reaches without having acted, and since the third withholding they are the whole chart.
OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
FULL_REACH_SPOTS = 6

# The button opens, the small blind flats, the big blind three-bets, the small blind acts. One
# of the 4,814: heads-up from here on, but reached through a cold call.
COLD_CALLED_PATH = (0, 0, 0, 1, 1, 2, 0)
COLD_CALLED_KEY = "t6/d100/SB/BTN:raise@2.5,SB:call,BB:raise@7.5"
COLD_CALLED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("SB", "call"),
    PreflopAction("BB", "raise", 7.5),
)

# One of the 14 the 2026-08-25 supersession drops, and the sharpest: the lojack's own open,
# every terminal below it able to go multiway.
LOJACK_OPEN_PATH: tuple[int, ...] = ()
LOJACK_OPEN_KEY = "t6/d100/LJ/rfi"

# Hero faces a three-bet: the button opens, the small blind folds, the big blind makes it 7.5,
# the button holds fold, call or a four-bet to 22.5. The second 2026-09-01 ruling's, that 22.5
# branch running into the node below, which decision 20 refuses.
THREE_BET_FACED_PATH = (0, 0, 0, 1, 0, 2)
THREE_BET_FACED_KEY = "t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5"
THREE_BET_FACED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("BB", "raise", 7.5),
)

# One action later: hero faces a four-bet, holding fold, call or the stack. Decision 20's.
FOUR_BET_FACED_PATH = (*THREE_BET_FACED_PATH, 2)
FOUR_BET_FACED_KEY = "t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5"
FOUR_BET_FACED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("BB", "raise", 7.5),
    PreflopAction("BTN", "raise", 22.5),
)

# One action later again, the first 2026-09-01 ruling's: the big blind jams, the button answers
# with 22.5 in, and the 77.5bb call-off is priced against a range computed at the node above.
FIVE_BET_JAM_PATH = (*FOUR_BET_FACED_PATH, 2)
FIVE_BET_JAM_KEY = "t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5,BB:raise@100"
FIVE_BET_JAM_SEQUENCE = (*FOUR_BET_FACED_SEQUENCE, PreflopAction("BB", "raise", 100.0))
FIVE_BET_CALL_OFF_BB = 77.5

# The jam spot that actually carries the rank inversion, corrected on 2026-09-01: the lojack's,
# not the button's. Here KK calls 72.84 against QQ at 94.29 and AKs calls 0.00 after four-betting
# it to 22.5 at 100, where at the button's jam spot above AA, KK, QQ and AKs all call 100.00 and
# there is no inversion. Asserted in `tests/test_chart_arrival_probability.py`, which has the
# room; the node is named here because this file names the nodes.
INVERTED_JAM_PATH = (1, 0, 0, 0, 0, 2, 2, 2)
INVERTED_JAM_KEY = "t6/d100/LJ/LJ:raise@2.5,BB:raise@7.5,LJ:raise@22.5,BB:raise@100"


# --- fixtures, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 finishes, imported inside the call rather than at module scope: a
    module-scope import of something that may not exist yet stops the file collecting and hides
    every assertion behind one ImportError - `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`."""
    import poker_training_bot.solver_artifacts.chart_derivation as module
    return module


def published_code(name: str) -> str | None:
    """One of the three new reasons as `lookup` publishes it, or None while it is unwritten.
    `getattr` on purpose: naming an attribute stage 6 has not added raises inside the test body
    and proves nothing, where a None fails on an assertion naming what is missing."""
    return getattr(lookup, name, None)


@pytest.fixture(scope="module")
def export() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


@pytest.fixture(scope="module")
def by_path(export: SolverExport) -> dict[tuple[int, ...], SolverNode]:
    return export.by_path()


@pytest.fixture(scope="module")
def derived(export: SolverExport):
    return derivation().derive_chart(export)


@pytest.fixture(scope="module")
def counted(export: SolverExport):
    return derivation().census(export)


def walk_state(
    by_path: dict[tuple[int, ...], SolverNode],
) -> dict[tuple[int, ...], tuple[frozenset[str], frozenset[str], tuple[PreflopAction, ...]]]:
    """Who has folded, who has voluntarily invested, and what hero faces, at every node.
    Written here rather than imported, because the predicate is on trial. Blinds are posted and
    never appear in the tree, so "voluntarily invested" is exactly "took a call, a raise or a
    jam"; an opener who later folds to a three-bet still counts."""
    state = {(): (frozenset(), frozenset(), ())}
    for path in sorted(by_path, key=len):
        node = by_path[path]
        folded, invested, entries = state[path]
        for index, action in enumerate(node.actions):
            child = (*path, index)
            if child not in by_path:
                continue
            if action.kind == "fold":
                state[child] = (folded | {node.actor_pos}, invested, entries)
            elif action.kind in ("call", "raise", "jam"):
                called = action.kind == "call"
                entry = PreflopAction(
                    node.actor_pos, "call" if called else "raise", None if called else action.to
                )
                state[child] = (folded, invested | {node.actor_pos}, (*entries, entry))
            else:
                raise AssertionError(f"node {path} offers an unhandled kind {action.kind!r}")
    return state


@pytest.fixture(scope="module")
def walked(by_path: dict[tuple[int, ...], SolverNode]) -> dict:
    state = walk_state(by_path)
    assert len(state) == len(by_path), "the walk did not reach every node"
    return state


def history_clause(node: SolverNode, state) -> bool:
    """At most one opponent has voluntarily put money in beyond the blinds."""
    _, invested, _ = state[node.path]
    return len(invested - {node.actor_pos}) <= 1


def subtree_clause(node: SolverNode, state) -> bool:
    """At most two players are still live, so every terminal below is heads-up - the clause the
    history reading was missing. The product approximation bites at *terminals* and a strategy
    is worked out backwards from every terminal below the node, so heads-up-ness is a statement
    about the reachable subtree rather than about the action history."""
    folded, _, _ = state[node.path]
    return len(SEATS) - len(folded) <= 2


def predicate_selects(node: SolverNode, state) -> bool:
    """Decision 1 on its own: the conjunction, and the 51 it keeps."""
    return history_clause(node, state) and subtree_clause(node, state)


def raises_faced(node: SolverNode, state) -> int:
    """How many raises are already in the pot hero is being asked about."""
    return sum(1 for entry in state[node.path][2] if entry.action == "raise")


def faces_a_three_bet(node: SolverNode, state) -> bool:
    """The second 2026-09-01 ruling: hero faces the second raise, so his own raise branch is a
    four-bet the fit cannot price. Exactly two, never two or more."""
    return raises_faced(node, state) == THREE_BET_RAISE_COUNT


def faces_a_four_bet(node: SolverNode, state) -> bool:
    """Decision 20: hero faces the third raise, so the pot is a four-bet pot the `calibrated`
    fit has no cell for. Exactly three, never three or more."""
    return raises_faced(node, state) == FOUR_BET_RAISE_COUNT


def faces_a_five_bet_jam(node: SolverNode, state) -> bool:
    """The first 2026-09-01 ruling: hero faces the fourth raise, which is the stack. Its own
    predicate rather than "three or more" because the families take different codes."""
    return raises_faced(node, state) == FIVE_BET_RAISE_COUNT


def selected(node: SolverNode, state) -> bool:
    """Committed: the predicate keeps it and no withholding takes it back."""
    withheld = (
        faces_a_three_bet(node, state)
        or faces_a_four_bet(node, state)
        or faces_a_five_bet_jam(node, state)
    )
    return predicate_selects(node, state) and not withheld


def key_of(node: SolverNode, state) -> str:
    return spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, state[node.path][2])


def measured_reach_bp(node: SolverNode) -> float:
    """Arriving reach spelled out rather than imported from the module under test: the plain
    mean over the 169 hand classes, in basis points, read off the node's own row."""
    return sum(node.reach_bp) / 169.0


def combo_weighted_reach_bp(node: SolverNode) -> float:
    """The same figure weighted by combinations - the plausible other definition."""
    pairs = [(node.reach_bp[gtopen_class_index(n)], class_combos(n)) for n in HAND_CLASSES]
    return sum(reach * combos for reach, combos in pairs) / sum(c for _, c in pairs)


# --- Decision 1: the predicate, and the three rulings that hand it back ---


def test_the_three_withholdings_are_counted_apart_though_together_they_are_two_or_more(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], walked
) -> None:
    """The 51 down to 6, in three rulings that a single filter cannot tell apart.

    Decision 20 refuses the four-bet pot the `calibrated` fit has no cell for. The first
    2026-09-01 ruling refuses hero's answer to the jam after it, priced against a range computed
    at that node. The second refuses hero facing a three-bet, whose only aggressive branch runs
    straight into it: those spots exist to answer "do I four-bet" and weigh that branch on a
    value the phase calls wrong. All three number 15, so a build swapping two balances totals."""
    kept = [node for node in export.nodes if predicate_selects(node, walked)]
    committed = [node for node in kept if selected(node, walked)]
    three_bet = [node for node in kept if faces_a_three_bet(node, walked)]
    four_bet = [node for node in kept if faces_a_four_bet(node, walked)]
    jams = [node for node in kept if faces_a_five_bet_jam(node, walked)]
    two_or_more = [n for n in kept if raises_faced(n, walked) >= THREE_BET_RAISE_COUNT]

    assert len(kept) == PREDICATE_NODES
    assert dict(Counter(raises_faced(n, walked) for n in kept)) == RAISES_FACED_OVER_THE_PREDICATE
    assert len(committed) == COMMITTED_NODES
    assert len(three_bet) == WITHHELD_THREE_BET_NODES
    assert len(four_bet) == WITHHELD_FOUR_BET_NODES
    assert len(jams) == WITHHELD_JAM_NODES
    assert dict(Counter(raises_faced(n, walked) for n in committed)) == RAISES_FACED_WHEN_COMMITTED
    assert len(kept) - len(two_or_more) == COMMITTED_UNDER_TWO_OR_MORE == COMMITTED_NODES
    # The three families are disjoint and none is empty, so "counted apart" has something to
    # bite on: a build folding one into another keeps the total and loses the reason.
    families = [{n.path for n in family} for family in (three_bet, four_bet, jams)]
    for index, family in enumerate(families):
        assert family
        for other in families[index + 1 :]:
            assert family.isdisjoint(other)

    raised_at = by_path[THREE_BET_FACED_PATH]
    faced = by_path[FOUR_BET_FACED_PATH]
    jammed = by_path[FIVE_BET_JAM_PATH]

    assert key_of(raised_at, walked) == THREE_BET_FACED_KEY
    assert key_of(faced, walked) == FOUR_BET_FACED_KEY
    assert key_of(jammed, walked) == FIVE_BET_JAM_KEY
    for node in (raised_at, faced, jammed):
        assert predicate_selects(node, walked) and not selected(node, walked)
    assert faces_a_three_bet(raised_at, walked) and not faces_a_four_bet(raised_at, walked)
    assert faces_a_four_bet(faced, walked) and not faces_a_five_bet_jam(faced, walked)
    assert faces_a_five_bet_jam(jammed, walked) and not faces_a_four_bet(jammed, walked)
    # The chain the codes claim, read off the tree: hero's only aggressive answer at the
    # three-bet spot leads to the four-bet spot, which leads to the jam.
    raising = [i for i, a in enumerate(raised_at.actions) if a.kind in ("raise", "jam")]
    assert len(raising) == 1 and (*raised_at.path, raising[0]) == FOUR_BET_FACED_PATH
    assert jammed.path[:-1] == faced.path
    # The jam is what hero answers rather than what hero can offer: fold, or call the whole
    # 100 with 22.5 already in. That call-off is the 77.5 the first ruling refuses to advise.
    assert [action.kind for action in jammed.actions] == ["fold", "call"]
    call = next(action for action in jammed.actions if action.kind == "call")
    assert call.to == 100.0
    assert call.to - 22.5 == FIVE_BET_CALL_OFF_BB
    # Hero is never offered a jam at a committed spot and never has to answer one either, so
    # nothing the chart ships puts a whole stack in preflop.
    assert all(action.kind != "jam" for node in committed for action in node.actions)
    assert all(action.to != 100.0 for node in committed for action in node.actions)


def test_arriving_reach_is_the_plain_mean_and_the_retired_floor_selects_nothing_extra(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], walked
) -> None:
    """The definition checked against the export rather than against itself, and decision 1's
    retired 2-percent floor asserted redundant rather than deleted.

    Reach stayed a published measurement after it stopped being the selection rule, so its
    definition is still pinned, the combo-weighted reading being a different number for the same
    words. They are separated over the whole export rather than the committed set, where since
    the third withholding every node sits at full reach and the readings agree exactly. The floor
    stays asserted because "no threshold is needed" is only checkable against the one replaced."""
    def gap(node: SolverNode) -> float:
        return abs(measured_reach_bp(node) - combo_weighted_reach_bp(node))

    committed = [node for node in export.nodes if selected(node, walked)]

    assert gap(max(export.nodes, key=gap)) > 1.0
    assert len(committed) == COMMITTED_NODES
    assert [n for n in committed if measured_reach_bp(n) >= RETIRED_FLOOR_BP] == committed
    assert not hasattr(derivation(), "REACH_FLOOR_BP"), (
        "the ruled predicate needs no threshold constant; a floor left in the module is a"
        " second selection rule nobody ruled"
    )

    named = by_path[COLD_CALLED_PATH]
    assert derivation().node_reach_bp(named) == pytest.approx(sum(named.reach_bp) / 169.0)
    for node in export.nodes:
        assert abs(derivation().node_reach_bp(node) - measured_reach_bp(node)) < 1e-6, node.path


def test_the_committed_spots_are_exactly_what_the_predicate_selects(
    export: SolverExport, walked, derived
) -> None:
    """The artifact holds every ruling's answer, not a subset chosen somewhere else.

    Computed from the export by hand, then compared against what the derivation emitted, so a
    build that dropped an awkward spot fails even though its census adds up. The six are named
    outright, being few enough to list and a claim a reader checks against the poker: the small
    blind opening a folded pot, the big blind answering each open. The refused ones are named
    apart because a build applying two withholdings and not the third lands on 21."""
    expected = {key_of(node, walked) for node in export.nodes if selected(node, walked)}
    committed = set(derived.artifact_payload["action_weights"])
    named = {SB_OPEN_KEY} | {
        f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/{opener}:raise@2.5" for opener in OPENERS
    }

    assert len(expected) == COMMITTED_NODES, "the committed spots collide in the key grammar"
    assert expected == named
    assert committed == expected
    assert THREE_BET_FACED_KEY not in committed
    assert FOUR_BET_FACED_KEY not in committed
    assert FIVE_BET_JAM_KEY not in committed
    for position in ("LJ", "HJ", "CO", "BTN"):
        assert f"t{TABLE_SIZE}/d{DEPTH_BB}/{position}/rfi" not in committed
    # No committed key records a second raise or a 100bb price, which is the three withholdings
    # read off the artifact's own keys rather than off the walk that produced them.
    for key in committed:
        faced = key.split("/")[3]
        assert "raise@100" not in faced, key
        assert faced == "rfi" or faced.count(":raise@") <= 1, key


def test_the_committed_set_has_the_measured_seat_depth_reach_and_menu_shape(
    export: SolverExport, walked
) -> None:
    """The distributions the rulings that rest on the committed set were re-taken against.

    Decisions 5, 6 and 10 were each first ruled on a count over a set this phase no longer
    commits and each was restated against these; they are tree facts, so a re-solve at the ruled
    config cannot move them. **Only depths 4 and 5 survive**: 6 is where hero faces a three-bet,
    7 a four-bet, 8 the jam, so each withholding takes a whole layer. The three withheld seat
    tables are asserted apart, and the three-bet and jam tables are identical seat for seat,
    which is why a seat table cannot tell them apart and the codes must.

    **Reach is folded in because it stopped distinguishing anything.** Every committed spot is
    one hero reaches without having acted, so all six sit at full reach and all 1,014 cells read
    10,000 basis points. Asserted as a measurement rather than left implied: decision 5's
    argument for the field, telling a trained cell from a barely visited one, is unexercised over
    what ships.

    **And the menus, because a build that dropped an action passes every other check here.** Two
    survive: five offering fold, call and a raise, and the small blind's own open offering fold
    and a raise and no call, where `CHART-HERO-MUST-NEVER-LIMP` holds by construction. All six
    carry a sizing entry, and every menu offers a fold, which is what makes "played rather than
    folded" a quantity the dominance measurements can be taken in. **The prices are 2.5 and 7.5
    and nothing else** - 22.5 was only offered facing a three-bet and 100 only facing a four-bet
    - so the contract's "exactly [2.5, 7.5, 22.5]" is stale by one price."""
    kept = [n for n in export.nodes if predicate_selects(n, walked)]
    committed = [n for n in kept if selected(n, walked)]
    three_bet = [n for n in kept if faces_a_three_bet(n, walked)]
    four_bet = [n for n in kept if faces_a_four_bet(n, walked)]
    jams = [n for n in kept if faces_a_five_bet_jam(n, walked)]
    heads_up = [n for n in export.nodes if history_clause(n, walked)]
    dropped = [n for n in heads_up if not subtree_clause(n, walked)]
    dropped_by_seat = Counter(n.actor_pos for n in dropped)
    deep = {"LJ": 5, "HJ": 4, "CO": 3, "BTN": 2, "SB": 1}

    assert Counter(node.actor_pos for node in committed) == {"SB": 1, "BB": 5}
    assert sorted(Counter(len(node.path) for node in committed).items()) == [(4, 1), (5, 5)]
    assert Counter(n.actor_pos for n in three_bet) == deep
    assert Counter(n.actor_pos for n in jams) == deep
    assert Counter(n.actor_pos for n in four_bet) == {"BB": 5, "SB": 4, "BTN": 3, "CO": 2, "HJ": 1}
    three_deep = [(6, WITHHELD_THREE_BET_NODES)]
    assert sorted(Counter(len(n.path) for n in three_bet).items()) == three_deep
    assert sorted(Counter(len(n.path) for n in four_bet).items()) == [(7, WITHHELD_FOUR_BET_NODES)]
    assert sorted(Counter(len(n.path) for n in jams).items()) == [(8, WITHHELD_JAM_NODES)]
    assert dropped_by_seat == {"LJ": 1, "HJ": 2, "CO": 3, "BTN": 4, "SB": 4}
    assert "BB" not in dropped_by_seat

    top = QUANTISATION_SCALE - 1e-9
    full = {key_of(n, walked) for n in committed if measured_reach_bp(n) >= top}
    unacted = {
        key_of(n, walked)
        for n in committed
        if all(entry.position != n.actor_pos for entry in walked[n.path][2])
    }

    assert full == unacted
    assert len(full) == FULL_REACH_SPOTS == COMMITTED_NODES
    assert full == {SB_OPEN_KEY} | {
        f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/{opener}:raise@2.5" for opener in OPENERS
    }
    assert TRACED_KEY in full
    for node in committed:
        assert set(node.reach_bp) == {QUANTISATION_SCALE}, key_of(node, walked)

    menus = Counter(tuple(action.kind for action in node.actions) for node in committed)
    prices = {act.to for node in committed for act in node.actions if act.kind == "raise"}

    assert menus == {("fold", "call", "raise"): 5, ("fold", "raise"): 1}
    assert sum(menus.values()) == COMMITTED_NODES
    assert sorted(prices) == [2.5, 7.5]
    for node in committed:
        assert "fold" in {action.kind for action in node.actions}


# --- The six-way census, over two closed vocabularies ---


def test_the_six_way_census_accounts_for_every_node_the_source_card_publishes(
    export: SolverExport, walked, counted, derived
) -> None:
    """The predicate, then the buckets: committed, five exclusion reasons, inexpressible, and
    nothing falling between them.

    **6 committed, 15 weighing a mispriced four-bet branch, 15 mispriced in a four-bet pot, 15
    inheriting a mispriced four-bet node, 29,104 mispriced multiway, 4,814 outside the selection
    rule, summing to 33,969.** Buckets are compared as sets of paths rather than counts, the
    three fifteens being the same size, so a build filing each under another's code adds up and
    describes a different chart. The total is checked against the source card, what a reader of
    the report has, and the inexpressible bucket publishes empty."""
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    subtree_paths = {n.path for n in export.nodes if subtree_clause(n, walked)}
    history_paths = {n.path for n in export.nodes if history_clause(n, walked)}
    kept = subtree_paths & history_paths
    multiway = {n.path for n in export.nodes} - subtree_paths
    outside = subtree_paths - history_paths
    three_bet = kept & {n.path for n in export.nodes if faces_a_three_bet(n, walked)}
    four_bet = kept & {n.path for n in export.nodes if faces_a_four_bet(n, walked)}
    jams = kept & {n.path for n in export.nodes if faces_a_five_bet_jam(n, walked)}
    committed = kept - three_bet - four_bet - jams
    buckets = (multiway, outside, three_bet, four_bet, jams, committed)

    # Decision 1 is the conjunction and neither clause alone. The history clause alone keeps 65
    # and admits 14 whose terminals can still go multiway, all five opens among them; the subtree
    # clause alone keeps 4,865 and admits 4,814 reached through a cold call. Both bite as sets
    # rather than totals, and the module's own predicate is that conjunction at every node.
    by_path = export.by_path()
    assert export.node_count == EXPORTED_NODES
    assert len(history_paths) == HISTORY_CLAUSE_NODES
    assert len(subtree_paths) == SUBTREE_CLAUSE_NODES
    assert len(kept) == PREDICATE_NODES
    assert 0 < len(kept) < len(history_paths) < len(subtree_paths) < export.node_count
    assert kept == {n.path for n in export.nodes if predicate_selects(n, walked)}
    for node in export.nodes:
        assert derivation().is_committed_node(by_path, node) is predicate_selects(
            node, walked
        ), node.path

    assert len(multiway) == MISPRICED_MULTIWAY_NODES
    assert len(outside) == OUTSIDE_RULE_NODES
    assert len(three_bet) == WITHHELD_THREE_BET_NODES
    assert len(four_bet) == WITHHELD_FOUR_BET_NODES
    assert len(jams) == WITHHELD_JAM_NODES
    assert len(committed) == COMMITTED_NODES
    for index, bucket in enumerate(buckets):
        for other in buckets[index + 1 :]:
            assert bucket.isdisjoint(other)
    assert len(set().union(*buckets)) == sum(len(b) for b in buckets) == EXPORTED_NODES
    assert committed == {n.path for n in export.nodes if selected(n, walked)}

    assert counted.total == card["node_counts"]["exported"] == EXPORTED_NODES
    assert counted.committed == COMMITTED_NODES
    assert counted.excluded == {
        lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY: MISPRICED_MULTIWAY_NODES,
        lookup.DERIVATION_OUTSIDE_SELECTION_RULE: OUTSIDE_RULE_NODES,
        THREE_BET_BRANCH_CODE: WITHHELD_THREE_BET_NODES,
        FOUR_BET_POT_CODE: WITHHELD_FOUR_BET_NODES,
        JAM_INHERITS_CODE: WITHHELD_JAM_NODES,
    }
    assert counted.committed + sum(counted.excluded.values()) == counted.total
    assert dict(counted.inexpressible) == {}
    assert len({key_of(n, walked) for n in export.nodes}) == export.node_count == EXPORTED_NODES
    assert set(counted.excluded) == set(lookup.DERIVATION_EXCLUSION_CODES)
    assert set(counted.inexpressible).issubset(lookup.DERIVATION_INEXPRESSIBILITY_CODES)
    assert derived.census.committed == counted.committed
    assert dict(derived.census.excluded) == dict(counted.excluded)

    # The 14 heads-up-by-history nodes sit inside the multiway bucket rather than beside it,
    # which is the point of the precedence: they are outside the rule *because* the source
    # misprices what is still reachable below them.
    dropped = history_paths - subtree_paths
    assert len(dropped) == HISTORY_BUT_NOT_CLEAN
    assert dropped <= multiway


def test_each_node_is_given_the_reason_that_names_what_is_wrong_with_it(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], walked
) -> None:
    """The code per node, not merely the totals, because five wrong buckets can sum right.

    The lojack's own open is heads-up by history and misprices below, so it takes the multiway
    code; the cold-called node prices exactly from here on and takes the selection-rule code. The
    big blind facing a button four-bet takes the four-bet-pot code, the button answering the jam
    after it the inherited code - that node prices fine and its parent does not - and the button
    facing the three-bet before it the branch code, for the mirror-image reason."""
    code_for = derivation().exclusion_code
    multiway = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE

    assert code_for(by_path, by_path[LOJACK_OPEN_PATH]) == multiway
    assert code_for(by_path, by_path[COLD_CALLED_PATH]) == outside
    assert code_for(by_path, by_path[THREE_BET_FACED_PATH]) == THREE_BET_BRANCH_CODE
    assert code_for(by_path, by_path[FOUR_BET_FACED_PATH]) == FOUR_BET_POT_CODE
    assert code_for(by_path, by_path[FIVE_BET_JAM_PATH]) == JAM_INHERITS_CODE
    assert code_for(by_path, by_path[TRACED_PATH]) is None

    for node in export.nodes:
        code = code_for(by_path, node)
        if selected(node, walked):
            assert code is None, node.path
        elif not subtree_clause(node, walked):
            assert code == multiway, node.path
        elif not history_clause(node, walked):
            assert code == outside, node.path
        elif faces_a_three_bet(node, walked):
            assert code == THREE_BET_BRANCH_CODE, node.path
        elif faces_a_four_bet(node, walked):
            assert code == FOUR_BET_POT_CODE, node.path
        else:
            assert code == JAM_INHERITS_CODE, node.path

    # And the chain each code names, read off the tree rather than asserted as prose: every
    # jam-coded node's parent is four-bet-coded, and every three-bet-coded node's one aggressive
    # branch leads to a four-bet-coded node. That is what makes the three reasons a chain rather
    # than three labels for one thing, and it is the only thing that says which way a fix runs.
    for node in export.nodes:
        code = code_for(by_path, node)
        if code == JAM_INHERITS_CODE:
            assert code_for(by_path, by_path[node.path[:-1]]) == FOUR_BET_POT_CODE, node.path
        if code == THREE_BET_BRANCH_CODE:
            raising = [i for i, a in enumerate(node.actions) if a.kind in ("raise", "jam")]
            assert len(raising) == 1, node.path
            child = by_path[(*node.path, raising[0])]
            assert code_for(by_path, child) == FOUR_BET_POT_CODE, node.path


def test_both_reason_vocabularies_are_closed_and_enumerated_here() -> None:
    """The contract asks for "a closed vocabulary the phase's tests enumerate", so it is
    enumerated literally: a code added without a ruling fails this file rather than passing
    quietly, and a node the build merely failed to handle cannot be filed as a property of the
    grammar. `DERIVATION_BELOW_REACH_FLOOR` is asserted gone, a code nothing files telling a
    reader a selection rule that is not in force."""
    multiway = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE
    no_key = lookup.DERIVATION_NO_LEGAL_SPOT_KEY
    everything = lookup.DERIVATION_EXCLUSION_CODES + lookup.DERIVATION_INEXPRESSIBILITY_CODES

    assert multiway == "derivation:source-misprices-multiway"
    assert outside == "derivation:outside-selection-rule"
    assert no_key == "derivation:no-legal-spot-key"
    assert published_code("DERIVATION_SOURCE_MISPRICES_FOUR_BET_POT") == FOUR_BET_POT_CODE, (
        "decision 20 needs a third exclusion reason; `lookup.py` must publish"
        f" DERIVATION_SOURCE_MISPRICES_FOUR_BET_POT = {FOUR_BET_POT_CODE!r}"
    )
    assert published_code("DERIVATION_INHERITS_A_MISPRICED_FOUR_BET_NODE") == JAM_INHERITS_CODE, (
        "the first 2026-09-01 ruling needs a fourth exclusion reason; `lookup.py` must publish"
        f" DERIVATION_INHERITS_A_MISPRICED_FOUR_BET_NODE = {JAM_INHERITS_CODE!r}"
    )
    branch = published_code("DERIVATION_WEIGHS_A_MISPRICED_FOUR_BET_BRANCH")
    assert branch == THREE_BET_BRANCH_CODE, (
        "the second 2026-09-01 ruling needs a fifth exclusion reason; `lookup.py` must publish"
        f" DERIVATION_WEIGHS_A_MISPRICED_FOUR_BET_BRANCH = {THREE_BET_BRANCH_CODE!r}"
    )
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        multiway,
        outside,
        THREE_BET_BRANCH_CODE,
        FOUR_BET_POT_CODE,
        JAM_INHERITS_CODE,
    }
    assert len(lookup.DERIVATION_EXCLUSION_CODES) == 5
    assert lookup.DERIVATION_INEXPRESSIBILITY_CODES == (no_key,)
    assert not hasattr(lookup, "DERIVATION_BELOW_REACH_FLOOR")
    for code in everything:
        assert NAMESPACED_CODE.fullmatch(code), code
        assert code.split(":")[0] == "derivation"
    # They live beside the refusal codes and must not shadow one: `lookup:` tells a reader a
    # query was refused, `derivation:` that a node never shipped.
    assert set(everything).isdisjoint(MISS_CODES)
    for code in MISS_CODES:
        assert NAMESPACED_CODE.fullmatch(code), code
