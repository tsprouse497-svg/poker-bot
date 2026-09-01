"""Phase 14: which solved nodes become committed spots, and why the others do not.

Authored at stage 4, before the derivation the rulings require exists, so this file is the
specification rather than a description of what got built. It owns the predicate, the two
withholdings that take thirty spots back, the five-way census and the four exclusion codes.
`tests/test_chart_conversion.py` owns what a committed row costs and imports this file's nodes
and walk helpers rather than copying them; the walk's own tests and the traced node moved to
`tests/test_chart_arrival_probability.py` on 2026-09-01, when the fourth exclusion code took this
file past the 700-line cap - that file re-walks the export per spot, so a broken walk shows there
first.

**Three rulings decide the committed set, and they stay separate because they are separate
rulings.** Decision 1 keeps a node when at most one opponent has voluntarily invested beyond the
blinds *and* at most two players are still live; over the re-sourced export it selects **51**.
Decision 20 then withholds the fifteen where hero **faces a four-bet**, the fit behind
`calibrated` having no four-bet-pot cell. Taylor's ruling of 2026-09-01 withholds fifteen more
where hero **faces a five-bet jam**: hero's answer to the jam range computed at the very
four-bet nodes decision 20 refuses, so the phase was refusing the parent as untrustworthy and
shipping the child. That leaves **21 committed**.

**The two withheld families are exactly `raises_faced >= 3`, and are still counted apart.**
Until 2026-09-01 this file named "three or more" as the wrong reading and pinned 21 as the count
it wrongly produced; the ruling makes 21 right, and that framing is gone deliberately rather
than loosened. A single filter still will not do: a node refused for its own mispricing and one
refused for its parent's come back by different routes and take different codes. The histogram
over the 51 is 0 raises 1 spot, 1 raise 5, 2 raises 15, 3 raises 15, 4 raises 15, so the
committed 21 are 1 + 5 + 15. Both withheld counts are 15, so a total cannot catch a build that
swapped them; the split is asserted whole and a node of each family named.

Every count is recomputed from the export by a walk written here, because a test that imports
the rule it checks is one copy of a rule agreeing with another. What is pinned is tree shape
rather than solve output, so the counts move only if the config moves, which decision 2 forbids.
Reach is the exception, asserted as a property. **`selected` means committed** - sibling files
import it - while `predicate_selects` is decision 1 alone, `faces_a_four_bet` is decision 20's
withholding and `faces_a_five_bet_jam` is the 2026-09-01 ruling's.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

# `lookup` as a module rather than by name for the derivation codes: the third one decision 20
# requires does not exist until stage 6, and naming it here would hide every assertion.
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

# The two withholding reasons, spelled here because this file is what names them for stage 6.
FOUR_BET_POT_CODE = "derivation:source-misprices-four-bet-pot"
JAM_INHERITS_CODE = "derivation:inherits-a-mispriced-four-bet-node"
"""The 2026-09-01 ruling's reason, a coordinator judgment call flagged for ratification. By the
contract's own test - which fix brings a node back - one code would do, both families returning
when the four-bet pot gains a fitted cell. Two are used so the census stays legible. If the next
`contract-update` prefers one, that is a rename rather than a re-derivation."""

# Tree facts: decision 2 permits a re-solve at the ruled config and nothing else.
EXPORTED_NODES = 33_969
PREDICATE_NODES = 51
COMMITTED_NODES = 21
WITHHELD_FOUR_BET_NODES = 15
WITHHELD_JAM_NODES = 15
HISTORY_CLAUSE_NODES = 65
SUBTREE_CLAUSE_NODES = 4_865
HISTORY_BUT_NOT_CLEAN = 14
RETIRED_FLOOR_BP = 200
"""Decision 1's retired 2-percent reach floor, kept only to assert it selects nothing the ruled
predicate does not - which is what made it a retirement rather than a retune."""

# The other two buckets. A node with a multiway terminal still reachable takes the multiway
# code, which a later phase reads to find what returns once GTOpen prices three-way; the two
# withheld buckets return by a fitted pot-type cell instead.
MISPRICED_MULTIWAY_NODES = 29_104
OUTSIDE_RULE_NODES = 4_814

# Both withholdings in one table: raises already in the pot hero is asked about, over the 51.
RAISES_FACED_OVER_THE_PREDICATE = {0: 1, 1: 5, 2: 15, 3: 15, 4: 15}
RAISES_FACED_WHEN_COMMITTED = {0: 1, 1: 5, 2: 15}
FOUR_BET_RAISE_COUNT = 3
FIVE_BET_RAISE_COUNT = 4
COMMITTED_UNDER_THREE_OR_MORE = 21
"""What a single `raises_faced >= 3` filter commits: the right answer since 2026-09-01 and the
named error before it. Renamed rather than deleted, so a reader meeting the change in git history
finds the reason here instead of concluding a check was loosened. The filter still cannot say
which reason a node was refused for, which is why both withheld counts sit beside it."""

# The spot the contract asks a non-coding reviewer to follow end to end: the big blind closing
# against a button open, at full reach, on fold, call and a three-bet to 7.5 - the most-played
# decision in six-max, `add_allin: false` having taken the duplicate all-in out.
TRACED_PATH = (0, 0, 0, 1, 0)
TRACED_KEY = "t6/d100/BB/BTN:raise@2.5"
TRACED_SEQUENCE = (PreflopAction("BTN", "raise", 2.5),)

# The one opening range the cutover commits, and the single committed spot offering hero a
# raise and no call - `CHART-HERO-MUST-NEVER-LIMP` holding by construction.
SB_OPEN_PATH = (0, 0, 0, 0)
SB_OPEN_KEY = "t6/d100/SB/rfi"

# The five opens the big blind answers; with the small blind's own open they are the six spots
# hero reaches without having acted.
OPENERS = ("LJ", "HJ", "CO", "BTN", "SB")
FULL_REACH_SPOTS = 6

# The button opens, the small blind flats, the big blind three-bets, the small blind acts. One
# of the 4,814: heads-up from here on, so every terminal below is priced exactly, but reached
# through a cold call, so it prices a range the same defect made.
COLD_CALLED_PATH = (0, 0, 0, 1, 1, 2, 0)
COLD_CALLED_KEY = "t6/d100/SB/BTN:raise@2.5,SB:call,BB:raise@7.5"
COLD_CALLED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("SB", "call"),
    PreflopAction("BB", "raise", 7.5),
)

# One of the 14 the 2026-08-25 supersession drops, and the sharpest: the lojack's own open.
# Every terminal below can go multiway, so the bot refuses a decision it answers today.
LOJACK_OPEN_PATH: tuple[int, ...] = ()
LOJACK_OPEN_KEY = "t6/d100/LJ/rfi"

# Hero faces a four-bet: button opens, big blind three-bets, button makes it 22.5, big blind
# holds fold, call or the stack. The predicate keeps it and decision 20 takes it back.
FOUR_BET_FACED_PATH = (0, 0, 0, 1, 0, 2, 2)
FOUR_BET_FACED_KEY = "t6/d100/BB/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5"
FOUR_BET_FACED_SEQUENCE = (
    PreflopAction("BTN", "raise", 2.5),
    PreflopAction("BB", "raise", 7.5),
    PreflopAction("BTN", "raise", 22.5),
)

# One action later, and withheld too since 2026-09-01: the big blind jams, the button answers
# with 22.5 in, and the 77.5bb call-off is priced against a range computed at the node above -
# the node decision 20 already refuses. Here KK calls 72.84 while QQ calls 94.29.
FIVE_BET_JAM_PATH = (0, 0, 0, 1, 0, 2, 2, 2)
FIVE_BET_JAM_KEY = "t6/d100/BTN/BTN:raise@2.5,BB:raise@7.5,BTN:raise@22.5,BB:raise@100"
FIVE_BET_JAM_SEQUENCE = (*FOUR_BET_FACED_SEQUENCE, PreflopAction("BB", "raise", 100.0))
FIVE_BET_CALL_OFF_BB = 77.5


# --- fixtures, and the definitions this file refuses to import ---


def derivation():
    """The module stage 6 finishes, imported inside the call rather than at module scope: a
    module-scope import of something that may not exist yet stops the file collecting and hides
    every assertion behind one ImportError - `LOOP-STAGE-4-RED-HIDES-LINT-AND-ASSERTIONS`.
    """
    import poker_training_bot.solver_artifacts.chart_derivation as module
    return module


def four_bet_pot_code() -> str | None:
    """The third exclusion reason as the module publishes it, or None while it is unwritten.
    `getattr` on purpose: naming an attribute stage 6 has not added raises inside the test body
    and proves nothing, where a None fails on an assertion naming what is missing.
    """
    return getattr(lookup, "DERIVATION_SOURCE_MISPRICES_FOUR_BET_POT", None)


def jam_inherits_code() -> str | None:
    """The fourth reason, read the same way and for the same reason."""
    return getattr(lookup, "DERIVATION_INHERITS_A_MISPRICED_FOUR_BET_NODE", None)


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
    jam"; an opener who later folds to a three-bet still counts.
    """
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
    is backward-induced over every terminal below the node, so heads-up-ness is a statement
    about the reachable subtree rather than about the action history.
    """
    folded, _, _ = state[node.path]
    return len(SEATS) - len(folded) <= 2


def predicate_selects(node: SolverNode, state) -> bool:
    """Decision 1 on its own: the conjunction, and the 51 it keeps."""
    return history_clause(node, state) and subtree_clause(node, state)


def raises_faced(node: SolverNode, state) -> int:
    """How many raises are already in the pot hero is being asked about."""
    return sum(1 for entry in state[node.path][2] if entry.action == "raise")


def faces_a_four_bet(node: SolverNode, state) -> bool:
    """Decision 20's withholding: hero faces the third raise, so the pot is a four-bet pot the
    fit behind `calibrated` has no cell for. Exactly three, never three or more."""
    return raises_faced(node, state) == FOUR_BET_RAISE_COUNT


def faces_a_five_bet_jam(node: SolverNode, state) -> bool:
    """The 2026-09-01 ruling's withholding: hero faces the fourth raise, which is the stack.
    Its own predicate rather than "three or more" because the two families take different
    exclusion codes and one filter cannot say which node got which."""
    return raises_faced(node, state) == FIVE_BET_RAISE_COUNT


def selected(node: SolverNode, state) -> bool:
    """Committed: the predicate keeps it and neither withholding takes it back."""
    withheld = faces_a_four_bet(node, state) or faces_a_five_bet_jam(node, state)
    return predicate_selects(node, state) and not withheld


def key_of(node: SolverNode, state) -> str:
    return spot_key(TABLE_SIZE, DEPTH_BB, node.actor_pos, state[node.path][2])


def measured_reach_bp(node: SolverNode) -> float:
    """Arriving reach spelled out here rather than imported from the module under test: the
    plain mean over the 169 hand classes of hero's range that reaches the node, in basis points,
    read straight off the node's own row."""
    return sum(node.reach_bp) / 169.0


def combo_weighted_reach_bp(node: SolverNode) -> float:
    """The same figure weighted by combinations - the plausible other definition."""
    pairs = [(node.reach_bp[gtopen_class_index(n)], class_combos(n)) for n in HAND_CLASSES]
    return sum(reach * combos for reach, combos in pairs) / sum(c for _, c in pairs)


# --- Decision 1: the predicate, and decision 20: what it hands back ---


def test_the_predicate_is_the_conjunction_and_neither_clause_alone(
    export: SolverExport, walked
) -> None:
    """The ruling, and the counts that prove it is not either clause on its own.

    Each supersession left a number behind that reads like the answer. The history clause alone
    keeps 65 and admits 14 whose terminals can still go multiway, all five opens among them; the
    subtree clause alone keeps 4,865 and admits 4,814 heads-up from here on that arrive carrying
    a range the same defect made. Both have to bite as sets, not merely totals.
    """
    history = {n.path for n in export.nodes if history_clause(n, walked)}
    subtree = {n.path for n in export.nodes if subtree_clause(n, walked)}
    both = history & subtree

    assert export.node_count == EXPORTED_NODES
    assert len(history) == HISTORY_CLAUSE_NODES
    assert len(subtree) == SUBTREE_CLAUSE_NODES
    assert len(both) == PREDICATE_NODES
    assert len(history - subtree) == HISTORY_BUT_NOT_CLEAN
    assert 0 < len(both) < len(history) < export.node_count
    assert len(both) < len(subtree) < export.node_count
    assert both == {n.path for n in export.nodes if predicate_selects(n, walked)}

    # And the module's own predicate is that conjunction at every node, not merely at the
    # count. Two rules can agree on a total and disagree on which nodes they picked.
    for node in export.nodes:
        assert derivation().is_committed_node(export.by_path(), node) is predicate_selects(
            node, walked
        ), node.path


def test_the_two_withholdings_are_counted_apart_though_together_they_are_three_or_more(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode], walked
) -> None:
    """The 51 down to 21, in two rulings that a single filter cannot tell apart.

    Decision 20 refuses the pot the `calibrated` fit has no cell for, hero facing the third
    raise. The 2026-09-01 ruling refuses hero's answer to the fourth, priced against a jam range
    computed at the very node decision 20 calls untrustworthy: at all five lojack spots AKs
    calls 0.00 percent after four-betting it to 22.5 at 100, and at the button spot named below
    KK calls 72.84 while QQ calls 94.29 - an inversion a trainee cannot detect. Shipping the
    child of a refused parent is worse than committing both, so both go. Together the two are
    exactly `raises_faced >= 3`, asserted rather than treated as an error; until this ruling 21
    was pinned here as the wrong reading's output. Both withheld families number 15, so a build
    that swapped them balances every total, and the histogram is asserted whole with one node of
    each family named.
    """
    kept = [node for node in export.nodes if predicate_selects(node, walked)]
    committed = [node for node in kept if selected(node, walked)]
    four_bet = [node for node in kept if faces_a_four_bet(node, walked)]
    jams = [node for node in kept if faces_a_five_bet_jam(node, walked)]
    three_or_more = [n for n in kept if raises_faced(n, walked) >= FOUR_BET_RAISE_COUNT]

    assert len(kept) == PREDICATE_NODES
    assert dict(Counter(raises_faced(n, walked) for n in kept)) == RAISES_FACED_OVER_THE_PREDICATE
    assert len(committed) == COMMITTED_NODES
    assert len(four_bet) == WITHHELD_FOUR_BET_NODES
    assert len(jams) == WITHHELD_JAM_NODES
    assert dict(Counter(raises_faced(n, walked) for n in committed)) == RAISES_FACED_WHEN_COMMITTED
    assert len(kept) - len(three_or_more) == COMMITTED_UNDER_THREE_OR_MORE == COMMITTED_NODES
    # The two families are disjoint and neither is empty, so "counted apart" has something to
    # bite on: a build folding one into the other keeps the total and loses the reason.
    assert {n.path for n in four_bet}.isdisjoint({n.path for n in jams})
    assert four_bet and jams

    faced = by_path[FOUR_BET_FACED_PATH]
    jammed = by_path[FIVE_BET_JAM_PATH]

    assert key_of(faced, walked) == FOUR_BET_FACED_KEY
    assert key_of(jammed, walked) == FIVE_BET_JAM_KEY
    assert predicate_selects(faced, walked) and not selected(faced, walked)
    assert predicate_selects(jammed, walked) and not selected(jammed, walked)
    assert faces_a_four_bet(faced, walked) and not faces_a_five_bet_jam(faced, walked)
    assert faces_a_five_bet_jam(jammed, walked) and not faces_a_four_bet(jammed, walked)
    # The jam is what hero answers rather than what hero can offer: fold, or call the whole
    # 100 with 22.5 already in. That call-off is the 77.5 the ruling refuses to advise.
    assert [action.kind for action in jammed.actions] == ["fold", "call"]
    call = next(action for action in jammed.actions if action.kind == "call")
    assert call.to == 100.0
    assert call.to - 22.5 == FIVE_BET_CALL_OFF_BB
    # Hero is never offered a jam at a committed spot and never has to answer one either, so
    # nothing the chart ships puts a whole stack in preflop.
    assert all(action.kind != "jam" for node in committed for action in node.actions)
    assert all(action.to != 100.0 for node in committed for action in node.actions)


def test_the_retired_reach_floor_now_selects_nothing_the_predicate_does_not(
    export: SolverExport, walked
) -> None:
    """Decision 1's 2-percent floor is retired rather than retuned, and this is why.

    Every committed spot clears it, so conjoining it changes nothing. Asserted redundant rather
    than deleted, because "the predicate needs no threshold" can only be checked against the
    threshold it replaced; re-tightening one to make the bytes work is a contract halt.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    conjoined = [node for node in committed if measured_reach_bp(node) >= RETIRED_FLOOR_BP]

    assert len(committed) == COMMITTED_NODES
    assert conjoined == committed
    assert not hasattr(derivation(), "REACH_FLOOR_BP"), (
        "the ruled predicate needs no threshold constant; a floor left in the module is a"
        " second selection rule nobody ruled"
    )


def test_arriving_reach_is_the_plain_mean_over_the_169_classes(
    export: SolverExport, by_path: dict[tuple[int, ...], SolverNode]
) -> None:
    """The definition, checked against the export rather than against itself.

    Reach stopped being the selection rule and stayed a published measurement - decision 5 carries
    it per cell - so its definition is still pinned, the combo-weighted reading being a different
    number for the same words. Where they disagree most is found at run time.
    """
    def gap(node: SolverNode) -> float:
        return abs(measured_reach_bp(node) - combo_weighted_reach_bp(node))

    assert gap(max(export.nodes, key=gap)) > 1.0

    named = by_path[COLD_CALLED_PATH]
    assert derivation().node_reach_bp(named) == pytest.approx(sum(named.reach_bp) / 169.0)
    for node in export.nodes:
        assert abs(derivation().node_reach_bp(node) - measured_reach_bp(node)) < 1e-6, node.path


def test_the_committed_spots_are_exactly_what_the_predicate_selects(
    export: SolverExport, walked, derived
) -> None:
    """The artifact holds both rulings' answer, not a subset chosen somewhere else.

    Computed from the export by hand here, then compared against what the derivation emitted,
    so a build that dropped an awkward spot fails even though its census adds up. The opening
    ranges are named in both directions because they are the ruled cost: the small blind's is
    kept, and the four the bot answers today are refused after the cutover. A chart carrying
    `LJ/rfi` was built on the history clause alone; one carrying the big blind against a button
    four-bet never reached decision 20; one carrying the button's answer to a jam predates the
    2026-09-01 ruling. The last two are named apart because a build applying one withholding and
    not the other lands on 36 either way.
    """
    expected = {key_of(node, walked) for node in export.nodes if selected(node, walked)}
    committed = set(derived.artifact_payload["action_weights"])

    assert len(expected) == COMMITTED_NODES, "the committed spots collide in the key grammar"
    assert committed == expected
    assert SB_OPEN_KEY in committed
    assert FOUR_BET_FACED_KEY not in committed
    assert FIVE_BET_JAM_KEY not in committed
    for position in ("LJ", "HJ", "CO", "BTN"):
        assert f"t{TABLE_SIZE}/d{DEPTH_BB}/{position}/rfi" not in committed
    # No committed key records a fourth raise or a 100bb price, which is the two withholdings
    # read off the artifact's own keys rather than off the walk that produced them.
    for key in committed:
        faced = key.split("/")[3]
        assert "raise@100" not in faced, key
        assert faced == "rfi" or faced.count(":raise@") <= 2, key


def test_the_committed_set_has_the_measured_seat_and_depth_shape(
    export: SolverExport, walked
) -> None:
    """The distributions the rulings that rest on the committed set were re-taken against.

    Decisions 5, 6 and 10 were each first ruled on a count over a set this phase no longer
    commits, and each was restated against these. They are tree facts, so a re-solve at the
    ruled config cannot move them. Depths 7 and 8 are absent: 7 is where hero faces a four-bet
    and 8 where hero answers the jam, so each withholding takes a whole layer. The withheld seat
    tables are mirror images - four-bet-facing heaviest at the blinds, jam-facing heaviest at the
    lojack - which is why they are asserted apart, not as one table of thirty.
    """
    kept = [n for n in export.nodes if predicate_selects(n, walked)]
    committed = [n for n in kept if selected(n, walked)]
    four_bet = [n for n in kept if faces_a_four_bet(n, walked)]
    jams = [n for n in kept if faces_a_five_bet_jam(n, walked)]
    heads_up = [n for n in export.nodes if history_clause(n, walked)]
    dropped = [n for n in heads_up if not subtree_clause(n, walked)]
    dropped_by_seat = Counter(n.actor_pos for n in dropped)

    seats = {"LJ": 5, "HJ": 4, "CO": 3, "BTN": 2, "SB": 2, "BB": 5}
    assert Counter(node.actor_pos for node in committed) == seats
    depths = [(4, 1), (5, 5), (6, 15)]
    assert sorted(Counter(len(node.path) for node in committed).items()) == depths
    assert Counter(n.actor_pos for n in four_bet) == {"BB": 5, "SB": 4, "BTN": 3, "CO": 2, "HJ": 1}
    assert Counter(n.actor_pos for n in jams) == {"LJ": 5, "HJ": 4, "CO": 3, "BTN": 2, "SB": 1}
    assert sorted(Counter(len(n.path) for n in jams).items()) == [(8, WITHHELD_JAM_NODES)]
    assert dropped_by_seat == {"LJ": 1, "HJ": 2, "CO": 3, "BTN": 4, "SB": 4}
    assert "BB" not in dropped_by_seat


def test_the_spots_at_full_reach_are_the_spots_where_hero_has_not_acted(
    export: SolverExport, walked
) -> None:
    """Decision 5's premise, asserted as the property rather than as the count.

    Six of the 21 sit at full reach, named by a rule instead of listed: hero's whole range
    arrives exactly where hero has not yet acted, so any other full-reach set has mis-assigned an
    actor or written reach it did not read. At the other fifteen hero has acted, so the field
    distinguishes at five spots in seven. The six are named as well as counted, six being what a
    chart holding the wrong six also reports.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    top = QUANTISATION_SCALE - 1e-9
    full = {key_of(n, walked) for n in committed if measured_reach_bp(n) >= top}
    unacted = {
        key_of(n, walked)
        for n in committed
        if all(entry.position != n.actor_pos for entry in walked[n.path][2])
    }

    assert full == unacted
    assert len(full) == FULL_REACH_SPOTS
    assert full == {SB_OPEN_KEY} | {
        f"t{TABLE_SIZE}/d{DEPTH_BB}/BB/{opener}:raise@2.5" for opener in OPENERS
    }
    assert TRACED_KEY in full


def test_the_two_action_menus_are_the_ruled_counts(export: SolverExport, walked) -> None:
    """A build that dropped an action passes every other check in this file.

    **Every committed spot now offers hero a raise, and that is new.** Until the 2026-09-01
    ruling fifteen offered fold and call only - hero answering a jam, the raise cap reached and
    nothing to price - and they were the whole of decision 6's "a spot with no size" half.
    Withholding them leaves two menus: twenty offering fold, call and a raise, and the small
    blind's open offering fold and a raise and no call, where `CHART-HERO-MUST-NEVER-LIMP` holds
    by construction. So the sizing table covers all 21. Prices are 2.5, 7.5 and 22.5.
    """
    committed = [node for node in export.nodes if selected(node, walked)]
    menus = Counter(tuple(action.kind for action in node.actions) for node in committed)
    prices = {act.to for node in committed for act in node.actions if act.kind == "raise"}

    assert menus == {("fold", "call", "raise"): 20, ("fold", "raise"): 1}
    assert sum(menus.values()) == COMMITTED_NODES
    assert sum(1 for n in committed if any(a.kind == "raise" for a in n.actions)) == COMMITTED_NODES
    assert sum(1 for n in committed if all(a.kind != "raise" for a in n.actions)) == 0
    assert sorted(prices) == [2.5, 7.5, 22.5]
    # Every menu offers a fold, which is what makes "played rather than folded" a quantity the
    # dominance measurements can be taken in at all.
    for node in committed:
        assert "fold" in {action.kind for action in node.actions}


# --- The five-way census, over two closed vocabularies ---


def test_the_five_way_census_accounts_for_every_node_the_source_card_publishes(
    export: SolverExport, walked, counted, derived
) -> None:
    """Committed, four exclusion reasons, inexpressible - and nothing falls between them.

    **21 committed, 15 mispriced in a four-bet pot, 15 inheriting a mispriced four-bet node,
    29,104 mispriced multiway, 4,814 outside the selection rule, summing to 33,969.** Four
    reasons because the families come back by different routes: the multiway nodes when GTOpen
    can price three-way, the four-bet nodes when the realization fit gains a four-bet-pot cell,
    the jams when their parent does. Under one code a later phase fixing one cannot tell which
    nodes it recovered. The buckets are compared as sets of paths rather than as a table of
    counts, because the two fifteens are the same size: a build filing each family under the
    other's code publishes a census that adds up exactly and describes a different chart. The
    total is checked against the source card rather than the export object, the card being what
    a reader of the report has. The inexpressible bucket publishes empty, a measurement rather
    than an omission: all 33,969 nodes derive a valid key and no two collide.
    """
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    subtree_paths = {n.path for n in export.nodes if subtree_clause(n, walked)}
    history_paths = {n.path for n in export.nodes if history_clause(n, walked)}
    kept = subtree_paths & history_paths
    multiway = {n.path for n in export.nodes} - subtree_paths
    outside = subtree_paths - history_paths
    four_bet = kept & {n.path for n in export.nodes if faces_a_four_bet(n, walked)}
    jams = kept & {n.path for n in export.nodes if faces_a_five_bet_jam(n, walked)}
    committed = kept - four_bet - jams
    buckets = (multiway, outside, four_bet, jams, committed)

    assert len(multiway) == MISPRICED_MULTIWAY_NODES
    assert len(outside) == OUTSIDE_RULE_NODES
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
    """The code per node, not merely the totals, because four wrong buckets can sum right.

    Five named nodes carry the distinction. The lojack's own open is heads-up by history and
    misprices, so it takes the multiway code; the cold-called node is priced exactly from here on
    and takes the selection-rule code. The big blind facing a button four-bet passes both clauses
    and takes the four-bet-pot code, the only way a reader tells it from a spot the predicate
    never wanted. The button answering the jam one action later takes the inherited code rather
    than the four-bet one, which is the second ruling's whole content: the node itself prices
    fine and its parent does not. Only the traced cell takes none.
    """
    code_for = derivation().exclusion_code
    multiway = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE

    assert code_for(by_path, by_path[LOJACK_OPEN_PATH]) == multiway
    assert code_for(by_path, by_path[COLD_CALLED_PATH]) == outside
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
        elif faces_a_four_bet(node, walked):
            assert code == FOUR_BET_POT_CODE, node.path
        else:
            assert code == JAM_INHERITS_CODE, node.path

    # And the parent of every jam-coded node is a four-bet-coded one, which is what the code's
    # name claims and what makes the two reasons a chain rather than two labels for one thing.
    for node in export.nodes:
        if code_for(by_path, node) == JAM_INHERITS_CODE:
            assert code_for(by_path, by_path[node.path[:-1]]) == FOUR_BET_POT_CODE, node.path


def test_both_reason_vocabularies_are_closed_and_enumerated_here() -> None:
    """The contract asks for "a closed vocabulary the phase's tests enumerate".

    Enumerated literally, so a code added without a ruling fails this file rather than passing
    quietly. The closure stops a node the build merely failed to handle being filed as a property
    of the grammar. `DERIVATION_BELOW_REACH_FLOOR` is asserted gone: a code nothing files tells
    a reader a selection rule that is not in force.
    """
    multiway = lookup.DERIVATION_SOURCE_MISPRICES_MULTIWAY
    outside = lookup.DERIVATION_OUTSIDE_SELECTION_RULE
    no_key = lookup.DERIVATION_NO_LEGAL_SPOT_KEY
    everything = lookup.DERIVATION_EXCLUSION_CODES + lookup.DERIVATION_INEXPRESSIBILITY_CODES

    assert multiway == "derivation:source-misprices-multiway"
    assert outside == "derivation:outside-selection-rule"
    assert no_key == "derivation:no-legal-spot-key"
    assert four_bet_pot_code() == FOUR_BET_POT_CODE, (
        "decision 20 needs a third exclusion reason; `lookup.py` must publish"
        f" DERIVATION_SOURCE_MISPRICES_FOUR_BET_POT = {FOUR_BET_POT_CODE!r}"
    )
    assert jam_inherits_code() == JAM_INHERITS_CODE, (
        "the 2026-09-01 ruling needs a fourth exclusion reason; `lookup.py` must publish"
        f" DERIVATION_INHERITS_A_MISPRICED_FOUR_BET_NODE = {JAM_INHERITS_CODE!r}"
    )
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        multiway,
        outside,
        FOUR_BET_POT_CODE,
        JAM_INHERITS_CODE,
    }
    assert len(lookup.DERIVATION_EXCLUSION_CODES) == 4
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
