"""Phase 10: the committed GTOpen export, and the checks that can say it is wrong.

Authored before the reader, the extractor, the expectations checker and the report exist,
and frozen before any of them does, so this file is the specification rather than a
description of what got built. Every threshold in it is a ruling from
`reports/phase_audits/decisions/PHASE_10_SOLVER_EXTRACTION_DECISIONS.md`, and one test
reads that record and fails if a constant drifts away from what was ruled.

Three kinds of test live here. Against `gtopen_node_payloads.captured.json`, a real
payload captured from a real solve at the ruled config, which is what stops the reader
agreeing with a fixture invented by whoever wrote the reader. Against deliberately broken
exports built below, because a check that has only ever run on data satisfying it has not
been shown to fail. And against the committed export, card and report, which do not exist
yet and whose tests are red on purpose until the solve stage runs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from poker_training_bot.solver_artifacts.gtopen_expectations import (
    aggregate_frequencies,
    ordering_errors,
)
from poker_training_bot.solver_artifacts.gtopen_export import (
    COMMITTED_EXPORT_PATH,
    COMMITTED_SOURCE_CARD_PATH,
    QUANTISATION_SCALE,
    SOLVE_ITERATION_CAP,
    SOLVE_TARGET_GAP_BB,
    SolverExport,
    class_combos,
    export_checksum,
    gtopen_class_index,
    load_solver_export,
    load_source_card,
    node_from_payload,
    source_card_errors,
    write_solver_export,
)
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES, hand_class_grid_index
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from check_file_sizes import DIRECTORY_BYTE_LIMITS  # noqa: E402
from run_verify import COMMANDS  # noqa: E402

ARTIFACTS = REPO_ROOT / "data" / "artifacts"
CAPTURED_PATH = ARTIFACTS / "preflop" / "exports" / "gtopen_node_payloads.captured.json"
POSITIONS = ["LJ", "HJ", "CO", "BTN", "SB", "BB"]

FOLD = {"label": "Fold", "kind": "fold", "to": 0.0, "terminal": True}
OPEN = {"label": "Raise 2.5", "kind": "raise", "to": 2.5, "terminal": False}
JAM = {"label": "All-in 100", "kind": "jam", "to": 100.0, "terminal": True}
CALL = {"label": "Call 2.5", "kind": "call", "to": 2.5, "terminal": True}
LIMP = {"label": "Limp 1.0", "kind": "limp", "to": 1.0, "terminal": False}

RULED_CONFIG = {
    "positions": POSITIONS,
    "stack": 100.0,
    "posts": [0, 0, 0, 0, 0.5, 1.0],
    "ante": 0.0,
    "limp": False,
    "open_raises": [2.5],
    "raise_mults": [3.0],
    "max_raises": 4,
    "add_allin": True,
    "allin_threshold": 0.67,
    "rake_pct": 0.0,
    "rake_cap": 0.0,
    "no_flop_no_drop": True,
    "realization": "calibrated",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def captured() -> dict:
    return json.loads(CAPTURED_PATH.read_text(encoding="utf-8"))


def view(captured: dict, name: str) -> dict:
    return captured["nodes"][name]["view"]


def uniform_node(path: tuple[int, ...], actor: str, actions: list[dict], split: tuple[int, ...]):
    """A node whose every hand class plays the same mix.

    Real strategies vary by class. These fixtures exist to exercise the validator, so
    they trade poker realism for fitting on one line.
    """
    return {
        "path": list(path),
        "actor_pos": actor,
        "actions": actions,
        "strategy_bp": [[weight] * 169 for weight in split],
        "reach_bp": [QUANTISATION_SCALE] * 169,
    }


def minimal_payload(**overrides) -> dict:
    """The smallest export the validator should accept: a root and one child."""
    payload = {
        "export_schema_version": 1,
        "config": dict(RULED_CONFIG),
        "positions": list(POSITIONS),
        "quantisation_scale": QUANTISATION_SCALE,
        "nodes": [
            uniform_node((), "LJ", [FOLD, OPEN, JAM], (8000, 2000, 0)),
            uniform_node((1,), "HJ", [FOLD, CALL, JAM], (7000, 3000, 0)),
        ],
    }
    payload.update(overrides)
    return payload


# --------------------------------------------------------------------------- #
# What the solver actually returns, read off a captured payload
# --------------------------------------------------------------------------- #


def test_the_captured_payload_came_from_a_solve_at_the_ruled_config() -> None:
    """A fixture stands in for the solver only if it came from the solver.

    If it was captured under some other config, every shape assertion below describes a
    tree nobody is going to commit.
    """
    payload = json.loads(CAPTURED_PATH.read_text(encoding="utf-8"))

    assert payload["config_posted"] == RULED_CONFIG
    assert re.fullmatch(r"[0-9a-f]{40}", payload["solver"]["commit"])
    assert payload["solve_status"]["state"] == "done"
    # Measured against the target this capture was actually given rather than against
    # today's module constant, because phase 14's decision 2 lowers the constant for the
    # permitted re-solve and a fixture captured before that still came from the ruled
    # config. The claim is unchanged: the capture converged to the target it was set.
    assert payload["solve_status"]["gap_total"] < payload["solve_request"]["target_gap"]
    assert payload["solve_request"]["iterations"] == SOLVE_ITERATION_CAP


def test_a_strategy_row_is_uniform_where_the_hand_never_arrives(captured: dict) -> None:
    """The conditioning discriminator the contract asks for, kept as a test.

    After LJ opens and HJ three-bets, LJ is to act holding only its opening range. 72o is
    folded at full frequency, so it never arrives - and the payload still carries a full
    strategy row for it, untouched uniform at a quarter per action.

    So the payload is unconditional, and `reach` is the only thing that conditions it. A
    converter that ignores reach produces ranges that are self-consistent and wrong, which
    is why decision 7 weights every aggregate by it and decision 10 commits it per node.

    The reach bound is 1e-6 rather than exact zero, because the captured value is
    3.6852573e-08: a solver that folds a hand at full frequency leaves the float residue of
    however many iterations it took to get there, and one basis point - the unit decision 8
    stores - is 1e-4. Anything under 1e-6 quantises to zero and is zero for every purpose in
    this phase. Exact equality here would have been an assertion about float arithmetic
    rather than about conditioning.
    """
    node = view(captured, "lj_vs_hj_threebet")
    never_arrives = gtopen_class_index("72o")
    action_count = len(node["actions"])

    assert node["reach"][never_arrives] < 1e-6
    row = [node["strategy"][k * 169 + never_arrives] for k in range(action_count)]
    assert row == pytest.approx([1 / action_count] * action_count, abs=1e-6)
    assert node["reach"][gtopen_class_index("AA")] > 0.99


def test_the_hand_class_index_is_the_solver_s_own_and_not_this_repo_s() -> None:
    """Two 169-class orderings now live in this package and they disagree.

    `hand_class_grid_index` walks the grid high to low for chart reports; GTOpen numbers
    ranks low to high and puts suited above the diagonal. Confusing them transposes suited
    and offsuit, which is the single most likely extraction defect.
    """
    assert gtopen_class_index("AA") == 168
    assert gtopen_class_index("22") == 0
    assert gtopen_class_index("AKs") == 167
    assert gtopen_class_index("AKo") == 155
    assert gtopen_class_index("72o") == 5
    assert sorted(gtopen_class_index(name) for name in HAND_CLASSES) == list(range(169))

    disagreements = [
        name for name in HAND_CLASSES if gtopen_class_index(name) != hand_class_grid_index(name)
    ]
    assert len(disagreements) > 150


def test_combo_counts_are_six_four_and_twelve() -> None:
    assert (class_combos("AA"), class_combos("AKs"), class_combos("AKo")) == (6, 4, 12)
    assert sum(class_combos(name) for name in HAND_CLASSES) == 1326


def test_the_captured_tree_offers_no_limp_anywhere(captured: dict) -> None:
    """Ruling 1 dropped limps, and the capture is the evidence the config obeyed it."""
    for name, entry in captured["nodes"].items():
        actions = entry["view"]["actions"]
        assert "limp" not in {action["kind"] for action in actions}, name
        assert "limp" not in " ".join(action["label"] for action in actions).lower(), name


def test_the_captured_tree_reaches_a_four_bet(captured: dict) -> None:
    """GTOpen labels its own raise levels, so the deep branch is identifiable by name.

    The contract's parenthetical calls this the fourth raise counting the open as the
    first; the solver calls the same action a 4-bet, which is the third raise and the
    ordinary poker reading. Asserting on the label means the two readings need not be
    reconciled here.
    """
    deep = captured["nodes"]["hj_vs_lj_fourbet"]
    reached_by = deep["view"]["history"][-2]

    assert "4-bet" in reached_by["actions"][reached_by["chosen"]]["label"]
    assert deep["view"]["actor_pos"] == "HJ"


# --------------------------------------------------------------------------- #
# Conversion into the committed format: decision 8's quantisation
# --------------------------------------------------------------------------- #


def test_every_converted_class_sums_to_the_quantisation_scale(captured: dict) -> None:
    """Decision 8: basis points, each class's distribution renormalised to 10,000.

    Rounding four actions independently loses or gains a basis point most of the time, so
    this fails unless the renormalisation is real.
    """
    for name, entry in captured["nodes"].items():
        node = node_from_payload(entry["view"], tuple(entry["path"]))
        for index in range(169):
            total = sum(row[index] for row in node.strategy_bp)
            assert total == QUANTISATION_SCALE, f"{name} class {index} sums to {total}"


def test_a_weight_below_one_basis_point_becomes_zero() -> None:
    """Precision the solve does not have is dropped rather than rounded up to one."""
    tiny = 0.00009  # 0.9 basis points: dropped by the ruled rule, kept by naive rounding
    payload = {
        "actor_pos": "LJ",
        "actions": [FOLD, OPEN, JAM],
        "strategy": [0.0] * 169 + [1.0] * 169 + [0.0] * 169,
        "reach": [1.0] * 169,
    }
    payload["strategy"][2 * 169 + gtopen_class_index("AA")] = tiny
    payload["strategy"][1 * 169 + gtopen_class_index("AA")] = 1.0 - tiny

    node = node_from_payload(payload, ())

    assert node.weight_bp(2, "AA") == 0
    assert node.weight_bp(1, "AA") == QUANTISATION_SCALE


def test_conversion_preserves_the_solver_s_own_action_frequency(captured: dict) -> None:
    """Decision 7's definition is not this repo's invention, and this is the proof.

    Combo-weighted and reach-weighted, the converted node reproduces the frequency GTOpen
    reports for the same action, on every captured node including the conditioned ones. A
    transposed index, a dropped reach or an unnormalised row moves these by tens of points.
    """
    for name, entry in captured["nodes"].items():
        node = node_from_payload(entry["view"], tuple(entry["path"]))
        for index, action in enumerate(entry["view"]["actions"]):
            assert node.action_frequency(index) == pytest.approx(
                action["freq"], abs=2e-4
            ), f"{name}/{action['label']}"


def test_a_flat_169_average_is_a_different_number_where_it_matters(captured: dict) -> None:
    """The weighting rule is load-bearing rather than a style preference.

    At an unconditioned node the two agree, which is why a flat average survives casual
    review. Behind a raise they are more than ten points apart.
    """
    unconditioned = node_from_payload(view(captured, "root_lj_rfi"), ())
    assert unconditioned.action_frequency(1) == pytest.approx(
        unconditioned.action_frequency(1, weight_by_reach=False), abs=1e-6
    )

    conditioned = node_from_payload(view(captured, "lj_vs_hj_threebet"), (1, 2, 0, 0, 0, 0))
    flat = conditioned.action_frequency(0, weight_by_reach=False)
    assert abs(conditioned.action_frequency(0) - flat) > 0.10


def test_reach_survives_conversion_because_nothing_else_carries_it(captured: dict) -> None:
    """Decision 10. Drop reach and the conditioning is gone, not merely unindexed."""
    node = node_from_payload(view(captured, "lj_vs_hj_threebet"), (1, 2, 0, 0, 0, 0))

    assert node.reach_bp[gtopen_class_index("72o")] == 0
    assert node.reach_bp[gtopen_class_index("AA")] > 9900
    assert len(set(node.reach_bp)) > 20


# --------------------------------------------------------------------------- #
# The reader, shown failing on exports that are each wrong in one way
# --------------------------------------------------------------------------- #


def test_the_minimal_export_is_accepted() -> None:
    export = SolverExport.from_payload(minimal_payload())

    assert export.node_count == 2
    assert export.node(()).actor_pos == "LJ"
    assert export.node((1,)).actor_pos == "HJ"


def _unbalanced(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][gtopen_class_index("AA")] = 7999


def _missing_row(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"].pop()


def _negative_weight(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][0] = -1


def _oversized_weight(payload: dict) -> None:
    payload["nodes"][0]["strategy_bp"][0][0] = QUANTISATION_SCALE + 1


def _no_child(payload: dict) -> None:
    payload["nodes"] = payload["nodes"][:1]


def _child_of_a_terminal(payload: dict) -> None:
    payload["nodes"].append(uniform_node((0,), "HJ", [FOLD, CALL], (5000, 5000)))


def _orphan(payload: dict) -> None:
    payload["nodes"].append(uniform_node((1, 1, 1), "CO", [FOLD, CALL], (5000, 5000)))


def _duplicate_path(payload: dict) -> None:
    payload["nodes"].append(uniform_node((1,), "HJ", [FOLD, CALL, JAM], (1, 9999, 0)))


def _unknown_actor(payload: dict) -> None:
    payload["nodes"][0]["actor_pos"] = "UTG"


def _carries_a_limp(payload: dict) -> None:
    payload["nodes"][0]["actions"] = [FOLD, LIMP, OPEN]
    payload["nodes"][0]["strategy_bp"] = [[8000] * 169, [1000] * 169, [1000] * 169]


BROKEN_EXPORTS = [
    # a class whose action weights no longer form a distribution
    ("unbalanced-class", _unbalanced, "10000"),
    # a strategy with fewer rows than the node has actions
    ("missing-row", _missing_row, "row"),
    ("negative-weight", _negative_weight, "weight"),
    ("oversized-weight", _oversized_weight, "weight"),
    # the traversal must close: a branch silently dropped is the failure that matters
    ("non-terminal-with-no-child", _no_child, "child"),
    ("child-hanging-off-a-terminal", _child_of_a_terminal, "terminal"),
    ("node-whose-parent-is-absent", _orphan, "parent"),
    ("two-nodes-at-one-path", _duplicate_path, "duplicate"),
    ("actor-outside-the-vocabulary", _unknown_actor, "UTG"),
    # ruling 1 read backwards: this is what fails if the wrong config produced the file
    ("limp-in-a-no-limp-tree", _carries_a_limp, "limp"),
]


@pytest.mark.parametrize(
    "mutate,match", [(m, x) for _, m, x in BROKEN_EXPORTS], ids=[n for n, _, _ in BROKEN_EXPORTS]
)
def test_a_broken_export_is_rejected(mutate, match: str) -> None:
    payload = minimal_payload()
    mutate(payload)

    with pytest.raises(ValueError, match=match):
        SolverExport.from_payload(payload)


@pytest.mark.parametrize(
    "field,value", [("rake_pct", 5.0), ("realization", "static"), ("limp", True)]
)
def test_an_export_whose_config_is_not_the_ruled_one_is_rejected(field: str, value) -> None:
    payload = minimal_payload()
    payload["config"][field] = value

    with pytest.raises(ValueError, match=field):
        SolverExport.from_payload(payload)


# --------------------------------------------------------------------------- #
# The file on disk: deterministic bytes, and a checksum over the data
# --------------------------------------------------------------------------- #


def test_writing_the_same_export_twice_gives_the_same_bytes(tmp_path: Path) -> None:
    """A container that stamps a timestamp makes every checksum a moving target."""
    export = SolverExport.from_payload(minimal_payload())
    first, second = tmp_path / "a.json.gz", tmp_path / "b.json.gz"

    write_solver_export(first, export)
    write_solver_export(second, export)

    assert first.read_bytes() == second.read_bytes()


def test_the_checksum_is_over_the_data_rather_than_the_container(tmp_path: Path) -> None:
    payload = minimal_payload()
    path = tmp_path / "export.json.gz"
    write_solver_export(path, SolverExport.from_payload(payload))

    assert export_checksum(load_solver_export(path)) == export_checksum(
        SolverExport.from_payload(payload)
    )

    moved = minimal_payload()
    moved["nodes"][0]["strategy_bp"][0][0] -= 1
    moved["nodes"][0]["strategy_bp"][1][0] += 1
    assert export_checksum(SolverExport.from_payload(moved)) != export_checksum(
        SolverExport.from_payload(payload)
    )


def test_an_export_round_trips_through_the_file(tmp_path: Path) -> None:
    export = SolverExport.from_payload(minimal_payload())
    path = tmp_path / "export.json.gz"
    write_solver_export(path, export)

    reloaded = load_solver_export(path)

    assert reloaded.node_count == export.node_count
    assert reloaded.node((1,)).strategy_bp == export.node((1,)).strategy_bp


# --------------------------------------------------------------------------- #
# The source card: the numbers the gate can never recompute
# --------------------------------------------------------------------------- #


def complete_card() -> dict:
    return {
        "config_posted": dict(RULED_CONFIG),
        "solver": {"name": "gtopen", "commit": "4aee435bdeb155b25f0c8140e707a8342ce4356f"},
        "solve": {
            "target_gap_bb": SOLVE_TARGET_GAP_BB,
            "achieved_gap_bb": 0.0062,
            "iterations": 300,
            "iteration_cap": SOLVE_ITERATION_CAP,
            "wall_clock_seconds": 132.4,
        },
        "determinism": {
            "result": "byte-identical",
            "method": "the ruled config solved twice in a fresh process and the exports diffed",
            "max_divergence_bp": 0,
        },
        "walk": {"reresolved_nodes": 38828, "mismatches": 0},
        "node_counts": {"exported": 38828, "solver_action_nodes": 38828, "reconciliation": "equal"},
        "conditioning": {
            "payload": "unconditional",
            "discriminator": "72o at the LJ-vs-3bet node carries a uniform row at zero reach",
        },
        "licence": "GTOpen ships no LICENSE file upstream; this is an unresolved limitation.",
        "model": (
            "realization=calibrated. GTOpen's preflop engine resolves flops by scaled equity"
            " share rather than by playing them."
        ),
        "size": {
            "bytes": 1,
            "limit_bytes": 20 * 1024 * 1024,
            "headroom_bytes": 1,
            "bytes_per_node": 1.0,
            "bytes_per_expressible_spot": 1.0,
        },
        "saved_solve": {"path": "gtopen-saves/six-max-100bb-rakefree", "bytes": 1,
                        "sha256": "0" * 64},
        "export_sha256": "0" * 64,
    }


def test_a_complete_card_reports_nothing() -> None:
    assert source_card_errors(complete_card()) == []


@pytest.mark.parametrize(
    "field",
    [
        "determinism",
        "solve",
        "licence",
        "model",
        "conditioning",
        "node_counts",
        "walk",
        "size",
        "saved_solve",
    ],
)
def test_a_card_missing_a_required_block_fails(field: str) -> None:
    card = complete_card()
    card.pop(field)

    assert any(field in error for error in source_card_errors(card))


@pytest.mark.parametrize("placeholder", ["", "TBD", "TODO", "unknown", None])
def test_a_placeholder_is_not_an_answer(placeholder) -> None:
    """Neither the determinism result nor the timing can be recomputed inside the gate.

    Requiring them as structured fields is worth something only if the field cannot be
    left saying nothing, which is the drift defect Phase 09 exists to have closed.
    """
    card = complete_card()
    card["determinism"]["result"] = placeholder

    assert any("determinism" in error for error in source_card_errors(card))


def test_a_zero_wall_clock_is_a_placeholder_too() -> None:
    card = complete_card()
    card["solve"]["wall_clock_seconds"] = 0

    assert any("wall_clock" in error for error in source_card_errors(card))


def test_a_card_that_does_not_state_the_licence_gap_fails() -> None:
    card = complete_card()
    card["licence"] = "permitted for internal use"

    assert any("licence" in error.lower() for error in source_card_errors(card))


def test_a_card_that_does_not_name_the_realization_setting_fails() -> None:
    """The setting is the difference between a usable range and a calling station."""
    card = complete_card()
    card["model"] = "a preflop solver"

    assert any("realization" in error for error in source_card_errors(card))


def test_node_counts_that_disagree_need_a_reconciliation() -> None:
    card = complete_card()
    card["node_counts"] = {"exported": 38820, "solver_action_nodes": 38828, "reconciliation": ""}

    assert any("reconcil" in error for error in source_card_errors(card))

    card["node_counts"]["reconciliation"] = "eight are chance nodes GTOpen counts separately"
    assert source_card_errors(card) == []


def test_a_walk_with_a_mismatch_fails() -> None:
    """The path encoding cannot be re-derived offline, so the extractor's own
    re-resolution is what the card carries, and a mismatch is a failed extraction."""
    card = complete_card()
    card["walk"]["mismatches"] = 1

    assert any("mismatch" in error for error in source_card_errors(card))


# --------------------------------------------------------------------------- #
# The committed export, the committed card, the committed report
# --------------------------------------------------------------------------- #


@pytest.fixture(scope="module")
def committed() -> SolverExport:
    assert COMMITTED_EXPORT_PATH.exists(), f"no committed export at {COMMITTED_EXPORT_PATH}"
    return load_solver_export(COMMITTED_EXPORT_PATH)


def test_the_committed_export_holds_the_whole_solved_tree(committed: SolverExport) -> None:
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)

    assert committed.node_count == card["node_counts"]["exported"]
    assert committed.node_count > 38000


def test_the_committed_export_reaches_a_four_bet(committed: SolverExport) -> None:
    """Requiring the whole tree in prose is not the same as failing when a branch goes
    missing, and this is the branch no v1 spot key can reach."""
    labels = {action.label for node in committed.nodes for action in node.actions}

    assert any("4-bet" in label for label in labels)


def test_the_committed_export_offers_no_limp(committed: SolverExport) -> None:
    assert "limp" not in {action.kind for node in committed.nodes for action in node.actions}


def test_the_committed_export_passes_both_orderings(committed: SolverExport) -> None:
    """Both are internal to the export, so this asserts the solve is self-consistent
    rather than that it agrees with another solver."""
    assert ordering_errors(aggregate_frequencies(committed)) == []


def test_the_committed_card_is_complete_and_matches_the_export(committed: SolverExport) -> None:
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)

    assert source_card_errors(card) == []
    assert card["export_sha256"] == export_checksum(committed)
    assert card["config_posted"] == RULED_CONFIG


def test_the_committed_export_sits_under_the_limit_with_stated_headroom() -> None:
    assert COMMITTED_EXPORT_PATH.exists(), "the export has not been committed yet"
    card = load_source_card(COMMITTED_SOURCE_CARD_PATH)
    limit = dict(DIRECTORY_BYTE_LIMITS)["data/artifacts"]
    total = sum(path.stat().st_size for path in ARTIFACTS.rglob("*") if path.is_file())

    assert COMMITTED_EXPORT_PATH.stat().st_size == card["size"]["bytes"]
    assert total < limit
    assert card["size"]["headroom_bytes"] == limit - total
    assert card["size"]["bytes_per_node"] > 0


# --------------------------------------------------------------------------- #
# Gate wiring
# --------------------------------------------------------------------------- #


def test_this_phase_s_command_ids_are_registered() -> None:
    for command_id in (
        "pytest_solver_export",
        "check_solver_export_expectations",
        "generate_solver_export_report",
    ):
        assert command_id in COMMANDS
