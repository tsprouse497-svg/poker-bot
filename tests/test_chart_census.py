"""Phase 14: every solved node accounted for, and the vocabulary the accounting is written in.

Authored at stage 4, before the derivation exists, so this file is a specification rather than a
description. It owns the four-bucket census and its precedence, the closed `namespace:reason`
vocabulary and its disjointness from the runtime miss codes, the refusal an unknown action kind
raises instead of taking a code, and what an excluded node does at the table.

`test_chart_derivation.py` owns the selection rule itself - the three clauses, each alone - and
this file imports its counts, its walk and its named nodes rather than restating them. The split
is a line-cap split and nothing more: a census is the same measurement as a selection, read from
the other end.
"""

from __future__ import annotations

import json
import re
from array import array

import pytest

# The counts, the walk and the named nodes have one owner. Importing the module rather than the
# names keeps `spec.` in front of every borrowed figure, so a reader can see what this file
# measured and what it took on trust.
import test_chart_derivation as spec

from poker_training_bot.solver_artifacts import lookup
from poker_training_bot.solver_artifacts.chart_query import ChartQuery
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SolverAction,
    SolverExport,
    SolverNode,
    load_source_card,
)
from poker_training_bot.solver_artifacts.importer import import_preflop_artifact
from poker_training_bot.solver_artifacts.lookup import (
    MISS_CODES,
    MISS_SPOT_NOT_COVERED,
    ChartMiss,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.schema import PreflopAction

# The shape `lookup.py` uses for every refusal it publishes; the derivation codes share it.
NAMESPACED_CODE = re.compile(r"\A[a-z]+:[a-z0-9-]+\Z")

# Fixtures do not travel with the module: `import test_chart_derivation as spec` binds the
# module, and pytest only collects a fixture it finds in the module it is collecting. So the
# three the owner defines are rebound here by name, which is the whole of what "this file
# imports its walk from its owner" means. Session scope is preserved because the objects are
# the owner's own fixture functions rather than copies, so the export is loaded and walked
# once for both files.
export = spec.export
walked = spec.walked
committed = spec.committed


@pytest.fixture(scope="module")
def counted(export: SolverExport):
    return spec.derivation().census(export)


def published_code(name: str) -> str | None:
    """One of the three reasons as `lookup` publishes it, or None while it is unwritten.
    `getattr` on purpose: naming an attribute stage 6 has not added raises inside the test body
    and proves nothing, where a None fails on an assertion naming what is missing."""
    return getattr(lookup, name, None)


@pytest.fixture(scope="module")
def committed_library(export: SolverExport, tmp_path_factory) -> PreflopChartLibrary:
    """The derived artifact, written out and imported the way the runtime imports it."""
    derived = spec.derivation().derive_chart(export)
    directory = tmp_path_factory.mktemp("derived-chart")
    path = directory / "six_max_100bb_rakefree.json"
    path.write_text(json.dumps(derived.artifact_payload, indent=2) + "\n", encoding="utf-8")
    return PreflopChartLibrary.from_artifacts([import_preflop_artifact(path)])


def test_the_four_bucket_census_accounts_for_every_node_the_source_card_publishes(
    export: SolverExport, walked: spec.Walk, counted
) -> None:
    """Committed, then one bucket per clause, and nothing falling between them.

    **249 committed, 348 above the exposure threshold, 10 big-blind squeeze spots, 33,362 beyond
    the committed raise depth, summing to 33,969.** Buckets are compared as sets of paths rather
    than as counts, because the precedence is what makes them a partition: sixteen of the
    twenty-six squeeze nodes are over the threshold too and are filed under exposure, so a build
    ordering the clauses differently balances and describes a different chart. The total is
    checked against the source card, which is what a reader of the report has.
    """
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    beyond = {n.path for n in export.nodes if not spec.within_raise_depth(walked, n)}
    exposed = {
        n.path
        for n in export.nodes
        if n.path not in beyond and not spec.below_exposure_threshold(walked, n)
    }
    squeezed = {
        n.path
        for n in export.nodes
        if n.path not in beyond
        and n.path not in exposed
        and spec.is_big_blind_squeeze(walked, n)
    }
    kept = {n.path for n in export.nodes} - beyond - exposed - squeezed
    buckets = (kept, exposed, squeezed, beyond)

    assert len(kept) == spec.COMMITTED_NODES
    assert len(exposed) == spec.EXPOSURE_REFUSED_NODES
    assert len(squeezed) == spec.BB_SQUEEZE_REFUSED_NODES
    assert len(beyond) == spec.BEYOND_DEPTH_NODES
    for index, bucket in enumerate(buckets):
        for other in buckets[index + 1 :]:
            assert bucket.isdisjoint(other)
    assert len(set().union(*buckets)) == sum(len(b) for b in buckets) == spec.EXPORTED_NODES
    assert kept == {node.path for node in spec.selected(export)}
    # 249 nodes are not self-evidently 249 spots, and 33,969 are not 33,969 keys.
    assert len({spec.key_of(walked, node) for node in export.nodes}) == spec.EXPORTED_NODES

    assert counted.total == card["node_counts"]["exported"] == spec.EXPORTED_NODES
    assert counted.committed == spec.COMMITTED_NODES
    assert dict(counted.excluded) == {
        spec.EXPOSURE_CODE: spec.EXPOSURE_REFUSED_NODES,
        spec.SQUEEZE_CODE: spec.BB_SQUEEZE_REFUSED_NODES,
        spec.DEPTH_CODE: spec.BEYOND_DEPTH_NODES,
    }
    assert counted.committed + sum(counted.excluded.values()) == counted.total
    # The inexpressible bucket publishes empty: a result rather than an omission, since all
    # 33,969 nodes derive a legal spot key and no two collide.
    assert dict(counted.inexpressible) == {}
    assert set(counted.excluded) == set(lookup.DERIVATION_EXCLUSION_CODES)


def test_a_census_that_folds_two_codes_together_balances_and_is_refused_anyway(
    export: SolverExport, walked: spec.Walk, counted
) -> None:
    """The failure a total cannot see, written out as the census a lazier build would publish.

    Folding the ten big-blind squeeze spots into the exposure bucket keeps the sum at 33,969 and
    loses the one thing a bucket is for: a later phase reading `exposure` would find ten spots
    that are not over the threshold, and the fix that returns them - a big blind that defends
    correctly, not a source that prices multiway - is a different fix.
    """
    folded = {
        spec.EXPOSURE_CODE: spec.EXPOSURE_REFUSED_NODES + spec.BB_SQUEEZE_REFUSED_NODES,
        spec.DEPTH_CODE: spec.BEYOND_DEPTH_NODES,
    }

    assert spec.COMMITTED_NODES + sum(folded.values()) == spec.EXPORTED_NODES, "it balances"
    assert dict(counted.excluded) != folded, "and is refused anyway"
    assert len(counted.excluded) == 3
    assert spec.SQUEEZE_CODE in counted.excluded
    # Every one of the ten is inside the threshold, so the folded bucket would be a false claim
    # about all ten rather than a rounding of one.
    squeezed = [
        node
        for node in export.nodes
        if spec.is_big_blind_squeeze(walked, node)
        and spec.below_exposure_threshold(walked, node)
    ]
    assert len(squeezed) == spec.BB_SQUEEZE_REFUSED_NODES
    for node in squeezed:
        assert spec.exposure_pct(walked, node) < spec.EXPOSURE_THRESHOLD_PCT, node.path


def test_each_node_takes_the_code_that_names_why_it_is_not_committed(
    export: SolverExport, walked: spec.Walk
) -> None:
    """The code per node, not merely the totals, because three wrong buckets can sum right.

    The precedence is asserted rather than assumed: raise depth first, then exposure, then the
    squeeze. It is what puts the sixteen squeeze nodes that are also over the threshold under
    exposure and leaves ten under their own code, and reversing it is a census that balances at
    33,969 with a bucket of 26 and a bucket of 332.
    """
    code_for = spec.derivation().exclusion_code
    by_path = walked.by_path

    assert code_for(by_path, by_path[spec.TRACED_PATH]) is None
    assert code_for(by_path, by_path[spec.COLD_CALLED_COMMITTED_PATH]) is None
    assert code_for(by_path, by_path[spec.FOUR_BET_FACED_PATH]) == spec.DEPTH_CODE
    assert code_for(by_path, by_path[spec.NARROWEST_REFUSED_PATH]) == spec.EXPOSURE_CODE
    assert code_for(by_path, by_path[spec.BB_SQUEEZE_PATH]) == spec.SQUEEZE_CODE

    for node in export.nodes:
        code = code_for(by_path, node)
        if not spec.within_raise_depth(walked, node):
            assert code == spec.DEPTH_CODE, node.path
        elif not spec.below_exposure_threshold(walked, node):
            assert code == spec.EXPOSURE_CODE, node.path
        elif spec.is_big_blind_squeeze(walked, node):
            assert code == spec.SQUEEZE_CODE, node.path
        else:
            assert code is None, node.path


def test_both_reason_vocabularies_are_closed_enumerated_and_apart_from_the_miss_codes() -> None:
    """The contract asks for "a closed vocabulary the tests enumerate", so it is enumerated
    literally: a code added without a ruling fails this file rather than passing quietly.

    The codes retired with the rules that produced them are asserted gone.
    `derivation:source-misprices-multiway` and `derivation:outside-selection-rule` named a
    live-player rule and an opponent-investment clause that decisions 40, 46 and 48 replaced, and
    `derivation:hero-closes-into-a-multiway-pot` named the wider closing rule decision 48 measured
    at 68 nodes and explicitly did not take. A later phase reading a bucket by its name would have
    got the wrong set, which is the one job a closed vocabulary has.
    """
    exposure = published_code("DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD")
    squeeze = published_code("DERIVATION_BIG_BLIND_SQUEEZE_SPOT")
    depth = published_code("DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH")

    assert exposure == spec.EXPOSURE_CODE, (
        "decision 46's filter needs its own reason; `lookup.py` must publish"
        f" DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD = {spec.EXPOSURE_CODE!r}"
    )
    assert squeeze == spec.SQUEEZE_CODE, (
        "decision 48's third clause needs its own reason; `lookup.py` must publish"
        f" DERIVATION_BIG_BLIND_SQUEEZE_SPOT = {spec.SQUEEZE_CODE!r}"
    )
    assert depth == spec.DEPTH_CODE, (
        "the withheld four-bet family needs its own reason; `lookup.py` must publish"
        f" DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH = {spec.DEPTH_CODE!r}"
    )
    no_key = lookup.DERIVATION_NO_LEGAL_SPOT_KEY
    assert no_key == "derivation:no-legal-spot-key"
    assert set(lookup.DERIVATION_EXCLUSION_CODES) == {
        spec.EXPOSURE_CODE,
        spec.SQUEEZE_CODE,
        spec.DEPTH_CODE,
    }
    assert len(lookup.DERIVATION_EXCLUSION_CODES) == 3
    assert lookup.DERIVATION_INEXPRESSIBILITY_CODES == (no_key,)
    for retired in (
        "DERIVATION_SOURCE_MISPRICES_MULTIWAY",
        "DERIVATION_OUTSIDE_SELECTION_RULE",
        "DERIVATION_HERO_CLOSES_INTO_A_MULTIWAY_POT",
        "DERIVATION_BELOW_REACH_FLOOR",
    ):
        assert not hasattr(lookup, retired), (
            f"{retired} names a selection rule that is not in force; a stale code in a closed"
            " vocabulary is a bucket a later phase can read the wrong set out of"
        )

    everything = lookup.DERIVATION_EXCLUSION_CODES + lookup.DERIVATION_INEXPRESSIBILITY_CODES
    for code in everything:
        assert NAMESPACED_CODE.fullmatch(code), code
        assert code.split(":")[0] == "derivation"
    # They live beside the refusal codes and must not shadow one: `lookup:` tells a reader a
    # query was refused at the table, `derivation:` that a node never shipped as a cell at all.
    assert set(everything).isdisjoint(MISS_CODES)
    for code in MISS_CODES:
        assert NAMESPACED_CODE.fullmatch(code), code


def test_an_unknown_action_kind_raises_rather_than_taking_a_reason_code(
    export: SolverExport,
) -> None:
    """A kind the derivation has no rule for is a converter that met something new.

    Filing it under `derivation:no-legal-spot-key` would record it as a property of the spot
    grammar, and filing it under an exclusion would claim a measurement nobody took: all three
    clauses count what each seat did, so none of them can be evaluated there at all. It raises,
    and the message names the kind, so whoever meets it knows what the source grew.
    """
    row = array("H", [QUANTISATION_SCALE] * 169)
    node = SolverNode(
        path=(),
        actor_pos="LJ",
        actions=(SolverAction(label="check", kind="check", to=0.0, terminal=True),),
        strategy_bp=(row,),
        reach_bp=array("H", [QUANTISATION_SCALE] * 169),
    )
    synthetic = SolverExport.from_nodes([node], config=export.config, positions=export.positions)

    with pytest.raises(ValueError, match="check"):
        spec.derivation().census(synthetic)
    with pytest.raises(ValueError, match="check"):
        spec.derivation().derive_chart(synthetic)


def test_a_cold_call_in_front_of_hero_refuses_nothing_on_its_own(
    walked: spec.Walk, committed: tuple[SolverNode, ...]
) -> None:
    """The sentence decision 52 corrected, asserted in the only form that can be wrong.

    Ten committed spots have a caller already in and hero still to act - the cutoff, the button
    and the small blind answering an open somebody flatted - and 194 of the 249 carry a call
    somewhere in their sequence. So nothing about a cold call refuses a node; the ten big-blind
    squeeze spots are refused for being the big blind's, which is what makes the third clause a
    clause about a seat rather than about an action.
    """
    facing_an_open = [node for node in committed if spec.raises_faced(walked, node) == 1]
    with_a_caller = [
        node
        for node in facing_an_open
        if any(entry.action == "call" for entry in walked.sequence[node.path])
    ]
    anywhere = [
        node
        for node in committed
        if any(entry.action == "call" for entry in walked.sequence[node.path])
    ]

    assert len(with_a_caller) == spec.COMMITTED_WITH_A_CALLER_ALREADY_IN
    assert len(anywhere) == spec.COMMITTED_WITH_A_CALL_IN_THE_SEQUENCE
    assert {node.actor_pos for node in with_a_caller} == {"CO", "BTN", "SB"}
    named = walked.by_path[spec.COLD_CALLED_COMMITTED_PATH]
    assert spec.key_of(walked, named) == spec.COLD_CALLED_COMMITTED_KEY
    assert named in with_a_caller
    # The same board, one seat over, and refused. The only difference is who hero is.
    squeeze = walked.by_path[spec.BB_SQUEEZE_PATH]
    assert walked.sequence[squeeze.path] == walked.sequence[named.path]
    assert not spec.is_committed(walked, squeeze)
    assert spec.is_committed(walked, named)


def test_exposure_is_published_per_committed_spot_with_its_terminal_split(
    walked: spec.Walk, committed: tuple[SolverNode, ...]
) -> None:
    """The measurement the report prints per spot, and what makes it a measurement.

    Three shares per committed spot - hand over preflop, heads-up flop, multiway flop - taken
    over the branches the bot can take. They close on 100 up to the mass reaching a node no hand
    class arrives at, which the solve publishes no strategy to redistribute. The multiway share
    **is** the exposure figure rather than a second derivation of it, which is what stops a
    report printing a split that disagrees with the filter that used it.

    A build carrying these figures forward instead of re-measuring would pass every count in this
    file and be wrong the moment the flats are repaired
    (`MULTIWAY-EXPOSURE-IS-LOW-ONLY-BECAUSE-THE-FLATS-ARE-BROKEN`), so the split is asserted at
    named spots as well as in aggregate.
    """
    for node in committed:
        preflop, heads_up, multiway = spec.terminal_split_pct(walked, node)
        assert multiway == spec.exposure_pct(walked, node), node.path
        assert multiway < spec.EXPOSURE_THRESHOLD_PCT, node.path
        assert min(preflop, heads_up, multiway) >= 0.0, node.path
        closes = pytest.approx(100.0, abs=spec.SPLIT_LEAK_PCT)
        assert preflop + heads_up + multiway == closes, node.path

    widest = walked.by_path[spec.WIDEST_ADMITTED_PATH]
    split = spec.terminal_split_pct(walked, widest)
    assert tuple(round(value, 4) for value in split) == spec.WIDEST_ADMITTED_SPLIT
    assert round(spec.exposure_pct(walked, walked.by_path[spec.TRACED_PATH]), 4) == 0.0
    assert round(spec.exposure_pct(walked, walked.by_path[spec.SB_OPEN_PATH]), 4) == 0.0

    # Exposure is a property of the leaves, so the deepest committed family is not the most
    # exposed: 149 of the 219 three-bet-facing spots carry any at all and 76 committed spots
    # carry none. A rule reading live players at the node would have had it the other way.
    assert sum(1 for node in committed if spec.exposure_pct(walked, node) == 0.0) == (
        spec.COMMITTED_AT_ZERO_EXPOSURE
    )
    three_bet = [node for node in committed if spec.raises_faced(walked, node) == 2]
    assert sum(1 for node in three_bet if spec.exposure_pct(walked, node) > 0.0) == (
        spec.THREE_BET_SPOTS_WITH_ANY_EXPOSURE
    )


@pytest.mark.parametrize(
    ("label", "key", "hero", "sequence", "committed_here"),
    [
        ("the big blind's squeeze spot, refused by the third clause",
         spec.BB_SQUEEZE_KEY, "BB", spec.BB_SQUEEZE_SEQUENCE, False),
        ("the same board one seat over, committed - a cold call refuses nothing",
         spec.COLD_CALLED_COMMITTED_KEY, "CO", spec.COLD_CALLED_COMMITTED_SEQUENCE, True),
        ("a four-handed pot over the exposure threshold at 10.0234",
         spec.NARROWEST_REFUSED_KEY, "BTN", spec.NARROWEST_REFUSED_SEQUENCE, False),
        ("hero facing a four-bet, beyond the committed raise depth",
         spec.FOUR_BET_FACED_KEY, "BB", spec.FOUR_BET_FACED_SEQUENCE, False),
        ("the big blind closing against a button open, committed",
         spec.TRACED_KEY, "BB", spec.TRACED_SEQUENCE, True),
    ],
)
def test_an_excluded_node_is_refused_at_the_table_rather_than_answered_from_a_neighbour(
    committed_library: PreflopChartLibrary,
    label: str,
    key: str,
    hero: str,
    sequence: tuple[PreflopAction, ...],
    committed_here: bool,
) -> None:
    """What a trainee meets when the chart does not hold a spot.

    A refusal naming the spot it could not answer, with no neighbouring cell consulted and no
    price moved to reach one. The two committed rows are the control: a test that only ever asks
    about excluded spots passes just as well against an empty chart.
    """
    query = ChartQuery(spec.TABLE_SIZE, spec.DEPTH_BB, hero, sequence, "AKs")
    answer = committed_library.lookup(query)

    assert query.spot_key == key, label
    if committed_here:
        assert not isinstance(answer, ChartMiss), f"{label}: {answer}"
        assert answer.spot_key == key, label
        assert answer.price_substitutions == (), label
        return
    assert isinstance(answer, ChartMiss), f"{label}: the chart answered a spot it does not hold"
    assert answer.code == MISS_SPOT_NOT_COVERED, label
    assert answer.spot_key == key, label
    assert answer.price_substitutions == (), (
        f"{label}: the lookup moved a price to reach a neighbouring cell rather than refusing"
    )
    assert key not in committed_library.spot_keys(), label
    assert committed_library.hand_classes_for(key) == (), label
