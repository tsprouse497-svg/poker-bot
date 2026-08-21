from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from poker_training_bot.solver_artifacts.importer import (
    AUDIT_COUNT_MISMATCH,
    CHECKSUM_MISMATCH,
    DUPLICATE_HAND_CLASS,
    DUPLICATE_SPOT,
    INVALID_JSON,
    INVALID_POSITION_VOCABULARY,
    INVALID_VALUE,
    INVALID_WEIGHT,
    MISSING_FIELD,
    MISSING_SPOT_WEIGHTS,
    NOT_AN_OBJECT,
    REASON_CODES,
    SPOT_KEY_MISMATCH,
    UNKNOWN_ACTION,
    UNKNOWN_FIELD,
    UNKNOWN_HAND_CLASS,
    UNKNOWN_SPOT_WEIGHTS,
    UNREADABLE_FILE,
    UNSUPPORTED_SCHEMA_VERSION,
    WEIGHT_SUM,
    ArtifactImportError,
    import_preflop_artifact,
    import_preflop_artifacts,
)
from poker_training_bot.solver_artifacts.schema import (
    ARTIFACT_SCHEMA_VERSION,
    PREFLOP_ACTIONS,
    SEQUENCE_ACTIONS,
    WEIGHT_SUM_TOLERANCE,
    PreflopAction,
    SpotActionWeights,
    spot_key,
    weights_checksum,
)

RFI_SPOT = "t6/d100/CO/rfi"
BTN_SPOT = "t6/d100/BTN/CO:raise@2.5"
BB_SPOT = "t6/d100/BB/BTN:raise@2.5"
SIX_MAX_POSITIONS = ["LJ", "HJ", "CO", "BTN", "SB", "BB"]


def weights_structure(action_weights: dict[str, Any]) -> SpotActionWeights:
    return tuple(
        (
            spot_id,
            tuple(
                (hand_class_text, tuple(actions.items()))
                for hand_class_text, actions in hand_classes.items()
            ),
        )
        for spot_id, hand_classes in action_weights.items()
    )


def stamped(payload: dict[str, Any]) -> dict[str, Any]:
    """Recompute the audit fields so the payload is internally consistent."""
    structure = weights_structure(payload["action_weights"])
    distinct = {name for _, classes in structure for name, _ in classes}
    payload["audit_fields"] = {
        "weights_sha256": weights_checksum(structure),
        "spot_count": len(payload["spots"]),
        "hand_class_count": len(distinct),
        "notes": "hand-authored fixture for importer tests",
    }
    return payload


def valid_payload() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "source": {
            "name": "Test Chart",
            "kind": "hand-authored",
            "reference": "tests/test_preflop_artifacts.py",
        },
        "generated_at": "2026-08-11T00:00:00Z",
        "table_size": 6,
        "stack_depth_bb": 100,
        "positions": list(SIX_MAX_POSITIONS),
        "spots": [
            {"spot_id": RFI_SPOT, "hero_position": "CO", "action_sequence": []},
            {
                "spot_id": BTN_SPOT,
                "hero_position": "BTN",
                "action_sequence": [{"position": "CO", "action": "raise", "size_bb": 2.5}],
            },
            {
                "spot_id": BB_SPOT,
                "hero_position": "BB",
                "action_sequence": [{"position": "BTN", "action": "raise", "size_bb": 2.5}],
            },
        ],
        "action_weights": {
            RFI_SPOT: {
                "AA": {"raise": 1.0},
                "AKs": {"raise": 1.0},
                "72o": {"fold": 1.0},
            },
            BTN_SPOT: {
                "AA": {"raise": 1.0},
                "AKs": {"call": 0.5, "raise": 0.5},
                "72o": {"fold": 1.0},
            },
            BB_SPOT: {
                "AA": {"raise": 1.0},
                "T9s": {"call": 0.75, "raise": 0.25},
                "72o": {"fold": 1.0},
            },
        },
    }
    return stamped(payload)


def write_payload(tmp_path: Path, payload: dict[str, Any], name: str = "chart.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def import_mutated(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], restamp: bool = False
) -> None:
    payload = valid_payload()
    mutate(payload)
    if restamp:
        stamped(payload)
    import_preflop_artifact(write_payload(tmp_path, payload))


def expect_code(
    tmp_path: Path, mutate: Callable[[dict[str, Any]], None], code: str
) -> ArtifactImportError:
    with pytest.raises(ArtifactImportError) as error:
        import_mutated(tmp_path, mutate)
    assert error.value.code == code
    return error.value


def test_valid_artifact_imports(tmp_path: Path) -> None:
    artifact = import_preflop_artifact(write_payload(tmp_path, valid_payload()))
    assert artifact.artifact_schema_version == ARTIFACT_SCHEMA_VERSION
    assert artifact.table_size == 6
    assert artifact.stack_depth_bb == 100
    assert artifact.positions == tuple(SIX_MAX_POSITIONS)
    assert [spot.spot_id for spot in artifact.spots] == [RFI_SPOT, BTN_SPOT, BB_SPOT]
    assert artifact.source.kind == "hand-authored"
    assert artifact.audit_fields.spot_count == 3
    assert artifact.audit_fields.hand_class_count == 4
    assert artifact.artifact_id == "t6/d100/test-chart"


def test_lookup_is_ordered_and_fail_closed(tmp_path: Path) -> None:
    artifact = import_preflop_artifact(write_payload(tmp_path, valid_payload()))
    assert artifact.weights_for(BTN_SPOT, "AKs") == (("call", 0.5), ("raise", 0.5))
    assert artifact.weights_for(RFI_SPOT, "AA") == (("raise", 1.0),)
    assert artifact.weights_for(RFI_SPOT, "T9s") is None
    assert artifact.weights_for("t6/d100/SB/rfi", "AA") is None
    assert artifact.spot(BB_SPOT).hero_position == "BB"
    with pytest.raises(ValueError):
        artifact.spot("t6/d100/SB/rfi")


def test_hand_classes_are_ordered_by_grid_index(tmp_path: Path) -> None:
    artifact = import_preflop_artifact(write_payload(tmp_path, valid_payload()))
    keyed = dict(artifact.action_weights)
    assert [name for name, _ in keyed[RFI_SPOT]] == ["AA", "AKs", "72o"]
    assert [name for name, _ in keyed[BB_SPOT]] == ["AA", "T9s", "72o"]


def test_action_weights_follow_spot_order(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["action_weights"] = {
        BB_SPOT: payload["action_weights"][BB_SPOT],
        RFI_SPOT: payload["action_weights"][RFI_SPOT],
        BTN_SPOT: payload["action_weights"][BTN_SPOT],
    }
    artifact = import_preflop_artifact(write_payload(tmp_path, stamped(payload)))
    assert [spot_id for spot_id, _ in artifact.action_weights] == [RFI_SPOT, BTN_SPOT, BB_SPOT]


def test_to_payload_round_trips_byte_for_byte(tmp_path: Path) -> None:
    artifact = import_preflop_artifact(write_payload(tmp_path, valid_payload()))
    first = json.dumps(artifact.to_payload())
    round_tripped = tmp_path / "round_trip.json"
    round_tripped.write_text(first, encoding="utf-8")
    again = import_preflop_artifact(round_tripped)
    assert json.dumps(again.to_payload()) == first
    assert again == artifact


def test_reason_codes_are_unique_and_namespaced() -> None:
    assert len(set(REASON_CODES)) == len(REASON_CODES)
    assert all(code.startswith("artifact:") for code in REASON_CODES)


def test_unreadable_file(tmp_path: Path) -> None:
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(tmp_path / "absent.json")
    assert error.value.code == UNREADABLE_FILE
    assert "absent.json" in error.value.message
    assert UNREADABLE_FILE in str(error.value)


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "chart.json"
    path.write_text('{"artifact_schema_version": 1,', encoding="utf-8")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(path)
    assert error.value.code == INVALID_JSON


def test_not_an_object(tmp_path: Path) -> None:
    path = tmp_path / "chart.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(path)
    assert error.value.code == NOT_AN_OBJECT


def test_nested_object_required(tmp_path: Path) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["source"] = ["Test Chart"]

    expect_code(tmp_path, mutate, NOT_AN_OBJECT)


def test_duplicate_hand_class(tmp_path: Path) -> None:
    text = json.dumps(valid_payload())
    marker = '"AA": {"raise": 1.0}, "AKs"'
    duplicated = text.replace(marker, '"AA": {"raise": 1.0}, "AA": {"call": 1.0}, "AKs"', 1)
    assert duplicated != text
    path = tmp_path / "chart.json"
    path.write_text(duplicated, encoding="utf-8")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(path)
    assert error.value.code == DUPLICATE_HAND_CLASS


def test_duplicate_spot_weights_key(tmp_path: Path) -> None:
    text = json.dumps(valid_payload())
    marker = f'"{RFI_SPOT}": {{'
    duplicated = text.replace(marker, f'"{RFI_SPOT}": {{"AA": {{"raise": 1.0}}}}, {marker}', 1)
    assert duplicated != text
    path = tmp_path / "chart.json"
    path.write_text(duplicated, encoding="utf-8")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(path)
    assert error.value.code == DUPLICATE_SPOT


def _missing_field(payload: dict[str, Any]) -> None:
    del payload["positions"]


def _unknown_field(payload: dict[str, Any]) -> None:
    payload["unexpected"] = True


def _unknown_nested_field(payload: dict[str, Any]) -> None:
    payload["audit_fields"]["extra"] = 1


def _missing_nested_field(payload: dict[str, Any]) -> None:
    del payload["spots"][0]["action_sequence"]


def _unsupported_version(payload: dict[str, Any]) -> None:
    payload["artifact_schema_version"] = ARTIFACT_SCHEMA_VERSION + 1


def _bad_stack_depth(payload: dict[str, Any]) -> None:
    payload["stack_depth_bb"] = 0


def _bad_table_size(payload: dict[str, Any]) -> None:
    payload["table_size"] = 12


def _bad_timestamp(payload: dict[str, Any]) -> None:
    payload["generated_at"] = "2026-08-11 00:00:00"


def _bad_source_kind(payload: dict[str, Any]) -> None:
    payload["source"]["kind"] = "vibes"


def _reordered_positions(payload: dict[str, Any]) -> None:
    payload["positions"] = list(reversed(SIX_MAX_POSITIONS))


def _short_positions(payload: dict[str, Any]) -> None:
    payload["positions"] = SIX_MAX_POSITIONS[:-1]


def _foreign_hero_position(payload: dict[str, Any]) -> None:
    payload["spots"][0]["hero_position"] = "UTG"
    payload["spots"][0]["spot_id"] = "t6/d100/UTG/rfi"


def _foreign_sequence_position(payload: dict[str, Any]) -> None:
    payload["spots"][1]["action_sequence"] = [
        {"position": "UTG", "action": "raise", "size_bb": 2.5}
    ]


def _spot_key_mismatch(payload: dict[str, Any]) -> None:
    payload["spots"][0]["hero_position"] = "HJ"


def _duplicate_spot(payload: dict[str, Any]) -> None:
    payload["spots"].append(dict(payload["spots"][0]))


def _unknown_spot_weights(payload: dict[str, Any]) -> None:
    payload["action_weights"]["t6/d100/SB/rfi"] = {"AA": {"raise": 1.0}}


def _missing_spot_weights(payload: dict[str, Any]) -> None:
    del payload["action_weights"][BB_SPOT]


def _empty_spot_weights(payload: dict[str, Any]) -> None:
    payload["action_weights"][BB_SPOT] = {}


def _unknown_hand_class(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["A2x"] = {"fold": 1.0}


def _unknown_weight_action(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"bet": 1.0}


def _folded_sequence_entry(payload: dict[str, Any]) -> None:
    payload["spots"][1]["action_sequence"] = [
        {"position": "HJ", "action": "fold"},
        {"position": "CO", "action": "raise", "size_bb": 2.5},
    ]


def _negative_weight(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"fold": -0.5, "raise": 1.5}


def _text_weight(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"raise": "1.0"}


def _weight_sum(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"raise": 0.5}


def _all_zero_weights(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"fold": 0.0, "raise": 0.0}


def _loose_weight_sum(payload: dict[str, Any]) -> None:
    payload["action_weights"][RFI_SPOT]["AA"] = {"raise": 1.0 - 1e-3}


def _checksum_mismatch(payload: dict[str, Any]) -> None:
    payload["audit_fields"]["weights_sha256"] = "0" * 64


def _malformed_checksum(payload: dict[str, Any]) -> None:
    payload["audit_fields"]["weights_sha256"] = "NOTAHASH"


def _spot_count_mismatch(payload: dict[str, Any]) -> None:
    payload["audit_fields"]["spot_count"] += 1


def _hand_class_count_mismatch(payload: dict[str, Any]) -> None:
    payload["audit_fields"]["hand_class_count"] += 1


def _duplicate_sequence_position(payload: dict[str, Any]) -> None:
    payload["spots"][1]["action_sequence"] = [
        {"position": "CO", "action": "raise", "size_bb": 2.5},
        {"position": "CO", "action": "call"},
    ]


def _out_of_order_sequence(payload: dict[str, Any]) -> None:
    payload["spots"][2]["action_sequence"] = [
        {"position": "BTN", "action": "raise", "size_bb": 2.5},
        {"position": "HJ", "action": "raise", "size_bb": 8.0},
    ]
    payload["spots"][2]["spot_id"] = "t6/d100/BB/BTN:raise@2.5,HJ:raise@8"


REJECTIONS: tuple[tuple[str, str, Callable[[dict[str, Any]], None]], ...] = (
    ("missing top-level field", MISSING_FIELD, _missing_field),
    ("missing nested field", MISSING_FIELD, _missing_nested_field),
    ("unknown top-level field", UNKNOWN_FIELD, _unknown_field),
    ("unknown nested field", UNKNOWN_FIELD, _unknown_nested_field),
    ("unsupported schema version", UNSUPPORTED_SCHEMA_VERSION, _unsupported_version),
    ("non-positive stack depth", INVALID_VALUE, _bad_stack_depth),
    ("table size out of range", INVALID_VALUE, _bad_table_size),
    ("non-RFC3339 timestamp", INVALID_VALUE, _bad_timestamp),
    ("unknown source kind", INVALID_VALUE, _bad_source_kind),
    ("malformed checksum text", INVALID_VALUE, _malformed_checksum),
    ("empty spot weights", INVALID_VALUE, _empty_spot_weights),
    ("duplicate sequence position", INVALID_VALUE, _duplicate_sequence_position),
    ("out-of-order sequence", INVALID_VALUE, _out_of_order_sequence),
    ("reordered positions", INVALID_POSITION_VOCABULARY, _reordered_positions),
    ("short positions", INVALID_POSITION_VOCABULARY, _short_positions),
    ("foreign hero position", INVALID_POSITION_VOCABULARY, _foreign_hero_position),
    ("foreign sequence position", INVALID_POSITION_VOCABULARY, _foreign_sequence_position),
    ("spot key mismatch", SPOT_KEY_MISMATCH, _spot_key_mismatch),
    ("duplicate spot", DUPLICATE_SPOT, _duplicate_spot),
    ("weights for undeclared spot", UNKNOWN_SPOT_WEIGHTS, _unknown_spot_weights),
    ("spot without weights", MISSING_SPOT_WEIGHTS, _missing_spot_weights),
    ("unknown hand class", UNKNOWN_HAND_CLASS, _unknown_hand_class),
    ("unknown weight action", UNKNOWN_ACTION, _unknown_weight_action),
    ("fold inside action sequence", UNKNOWN_ACTION, _folded_sequence_entry),
    ("negative weight", INVALID_WEIGHT, _negative_weight),
    ("non-numeric weight", INVALID_WEIGHT, _text_weight),
    ("weights below one", WEIGHT_SUM, _weight_sum),
    ("all-zero weights", WEIGHT_SUM, _all_zero_weights),
    ("weights outside tolerance", WEIGHT_SUM, _loose_weight_sum),
    ("checksum mismatch", CHECKSUM_MISMATCH, _checksum_mismatch),
    ("spot count mismatch", AUDIT_COUNT_MISMATCH, _spot_count_mismatch),
    ("hand class count mismatch", AUDIT_COUNT_MISMATCH, _hand_class_count_mismatch),
)


@pytest.mark.parametrize(
    ("code", "mutate"),
    [(code, mutate) for _, code, mutate in REJECTIONS],
    ids=[name for name, _, _ in REJECTIONS],
)
def test_rejections(
    tmp_path: Path, code: str, mutate: Callable[[dict[str, Any]], None]
) -> None:
    failure = expect_code(tmp_path, mutate, code)
    assert failure.message
    assert code in str(failure)


def test_every_reason_code_is_exercised() -> None:
    covered = {code for _, code, _ in REJECTIONS} | {
        UNREADABLE_FILE,
        INVALID_JSON,
        NOT_AN_OBJECT,
        DUPLICATE_HAND_CLASS,
    }
    assert covered == set(REASON_CODES)


def test_weight_sum_tolerance_edge(tmp_path: Path) -> None:
    payload = valid_payload()
    payload["action_weights"][RFI_SPOT]["AA"] = {"raise": 1.0 - 1e-7}
    artifact = import_preflop_artifact(write_payload(tmp_path, stamped(payload)))
    assert artifact.weights_for(RFI_SPOT, "AA") == (("raise", 1.0 - 1e-7),)
    assert WEIGHT_SUM_TOLERANCE == 1e-6


def test_restamped_mutation_still_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactImportError) as error:
        import_mutated(tmp_path, _loose_weight_sum, restamp=True)
    assert error.value.code == WEIGHT_SUM


def test_spot_key_rfi_and_sequence_forms() -> None:
    assert spot_key(6, 100, "CO", ()) == "t6/d100/CO/rfi"
    six = spot_key(6, 100, "BTN", (PreflopAction("HJ", "raise", 2.5),))
    assert six == "t6/d100/BTN/HJ:raise@2.5"
    heads_up = spot_key(2, 40, "BB", (PreflopAction("BTN", "raise", 2.5),))
    assert heads_up == "t2/d40/BB/BTN:raise@2.5"
    sequence = (PreflopAction("CO", "raise", 2.5), PreflopAction("BTN", "call"))
    assert spot_key(6, 100, "BB", sequence) == "t6/d100/BB/CO:raise@2.5,BTN:call"


def test_spot_key_allows_hero_inside_the_sequence() -> None:
    sequence = (PreflopAction("LJ", "raise", 2.5), PreflopAction("BTN", "raise", 8.0))
    assert spot_key(6, 100, "LJ", sequence) == "t6/d100/LJ/LJ:raise@2.5,BTN:raise@8"


def test_spot_key_requires_action_order() -> None:
    with pytest.raises(ValueError):
        spot_key(
            6, 100, "BB", (PreflopAction("BTN", "raise", 2.5), PreflopAction("HJ", "raise", 8.0))
        )


def test_spot_key_rejects_a_seat_taking_two_turns_in_a_row() -> None:
    """A position may act more than once since phase 12, but not twice running.

    Reaching the cutoff a second time means the ring came round, which means the big
    blind was passed - and the big blind is hero here, so hero would have folded.
    """
    with pytest.raises(ValueError):
        spot_key(6, 100, "BB", (PreflopAction("CO", "raise", 2.5), PreflopAction("CO", "call")))


@pytest.mark.parametrize("table_size", [-1, 0, 1, 10, 99])
def test_spot_key_rejects_bad_table_size(table_size: int) -> None:
    with pytest.raises(ValueError):
        spot_key(table_size, 100, "BB", ())


@pytest.mark.parametrize("stack_depth_bb", [-5, 0])
def test_spot_key_rejects_bad_stack_depth(stack_depth_bb: int) -> None:
    with pytest.raises(ValueError):
        spot_key(6, stack_depth_bb, "BB", ())


def test_spot_key_rejects_positions_outside_the_table() -> None:
    with pytest.raises(ValueError):
        spot_key(6, 100, "UTG", ())
    with pytest.raises(ValueError):
        spot_key(2, 100, "CO", ())
    with pytest.raises(ValueError):
        spot_key(2, 100, "BB", (PreflopAction("CO", "raise", 2.5),))


def test_preflop_action_rejects_folds_and_unknown_actions() -> None:
    assert "fold" in PREFLOP_ACTIONS
    assert "fold" not in SEQUENCE_ACTIONS
    with pytest.raises(ValueError):
        PreflopAction("CO", "fold")
    with pytest.raises(ValueError):
        PreflopAction("CO", "bet")
    with pytest.raises(ValueError):
        PreflopAction("ZZ", "raise", 2.5)


def test_import_directory_is_sorted_and_complete(tmp_path: Path) -> None:
    second = valid_payload()
    second["source"]["name"] = "Chart B"
    write_payload(tmp_path, second, name="b_chart.json")
    first = valid_payload()
    first["source"]["name"] = "Chart A"
    write_payload(tmp_path, first, name="a_chart.json")
    artifacts = import_preflop_artifacts(tmp_path)
    assert [artifact.source.name for artifact in artifacts] == ["Chart A", "Chart B"]
    assert [artifact.artifact_id for artifact in artifacts] == [
        "t6/d100/chart-a",
        "t6/d100/chart-b",
    ]


def test_import_directory_fails_closed_on_one_bad_file(tmp_path: Path) -> None:
    write_payload(tmp_path, valid_payload(), name="a_good.json")
    broken = valid_payload()
    _weight_sum(broken)
    write_payload(tmp_path, broken, name="b_broken.json")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifacts(tmp_path)
    assert error.value.code == WEIGHT_SUM
    assert "b_broken.json" in error.value.message


def test_import_directory_requires_json_files(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("not an artifact", encoding="utf-8")
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifacts(tmp_path)
    assert error.value.code == UNREADABLE_FILE


def test_import_directory_requires_an_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifacts(tmp_path / "absent")
    assert error.value.code == UNREADABLE_FILE


def test_import_accepts_string_paths(tmp_path: Path) -> None:
    path = write_payload(tmp_path, valid_payload())
    assert import_preflop_artifact(str(path)) == import_preflop_artifact(path)
    assert len(import_preflop_artifacts(str(tmp_path))) == 1


def test_weights_checksum_is_order_independent_and_stable() -> None:
    payload = valid_payload()
    reversed_weights = {
        spot_id: dict(reversed(list(classes.items())))
        for spot_id, classes in reversed(list(payload["action_weights"].items()))
    }
    assert weights_checksum(weights_structure(reversed_weights)) == weights_checksum(
        weights_structure(payload["action_weights"])
    )
    assert weights_checksum(()) == weights_checksum(())


def test_preflop_action_rejects_folds_and_checks() -> None:
    """A fold is implicit in absence, and a preflop check ends the round."""
    for action in ("fold", "check"):
        with pytest.raises(ValueError):
            PreflopAction("CO", action)


@pytest.mark.parametrize(
    ("label", "hero", "sequence"),
    [
        ("action from a position that acts later", "CO", (PreflopAction("BTN", "raise", 2.5),)),
        ("early position facing a later open", "LJ", (PreflopAction("CO", "raise", 2.5),)),
        (
            "small blind facing a big blind raise it never saw",
            "SB",
            (PreflopAction("BB", "raise", 2.5),),
        ),
        ("hero acted last in its own sequence", "CO", (PreflopAction("CO", "raise", 2.5),)),
        (
            "hero already acted and faces only a call",
            "CO",
            (PreflopAction("CO", "raise", 2.5), PreflopAction("BB", "call")),
        ),
    ],
)
def test_spot_key_rejects_spots_where_hero_is_not_to_act(
    label: str, hero: str, sequence: tuple[PreflopAction, ...]
) -> None:
    with pytest.raises(ValueError):
        spot_key(6, 100, hero, sequence)


def test_spot_key_rejects_folded_to_the_big_blind() -> None:
    """Folded to the big blind ends the hand, so it is not a decision."""
    with pytest.raises(ValueError):
        spot_key(6, 100, "BB", ())
    with pytest.raises(ValueError):
        spot_key(2, 100, "BB", ())


@pytest.mark.parametrize(
    ("label", "hero", "sequence", "expected"),
    [
        ("cutoff open", "CO", (), "t6/d100/CO/rfi"),
        ("small blind steal", "SB", (), "t6/d100/SB/rfi"),
        (
            "big blind versus a cutoff open",
            "BB",
            (PreflopAction("CO", "raise", 2.5),),
            "t6/d100/BB/CO:raise@2.5",
        ),
        ("blind vs blind", "BB", (PreflopAction("SB", "raise", 3.5),), "t6/d100/BB/SB:raise@3.5"),
        (
            "limped pot",
            "BB",
            (PreflopAction("LJ", "call"), PreflopAction("HJ", "call")),
            "t6/d100/BB/LJ:call,HJ:call",
        ),
        (
            "squeeze spot",
            "BB",
            (PreflopAction("CO", "raise", 2.5), PreflopAction("BTN", "call")),
            "t6/d100/BB/CO:raise@2.5,BTN:call",
        ),
        (
            "opener facing a three-bet",
            "CO",
            (PreflopAction("CO", "raise", 2.5), PreflopAction("BB", "raise", 11.0)),
            "t6/d100/CO/CO:raise@2.5,BB:raise@11",
        ),
        (
            "cold four-bet-or-fold",
            "BTN",
            (PreflopAction("LJ", "raise", 2.5), PreflopAction("HJ", "raise", 8.0)),
            "t6/d100/BTN/LJ:raise@2.5,HJ:raise@8",
        ),
        (
            "limper facing a later raise",
            "SB",
            (PreflopAction("SB", "call"), PreflopAction("BB", "raise", 3.5)),
            "t6/d100/SB/SB:call,BB:raise@3.5",
        ),
    ],
)
def test_spot_key_accepts_real_six_max_spots(
    label: str, hero: str, sequence: tuple[PreflopAction, ...], expected: str
) -> None:
    assert spot_key(6, 100, hero, sequence) == expected, label


def test_artifact_with_no_spots_is_rejected(tmp_path: Path) -> None:
    """An empty chart would still claim its table size and depth are covered."""
    payload = valid_payload()
    payload["spots"] = []
    payload["action_weights"] = {}
    payload = stamped(payload)
    payload["audit_fields"]["spot_count"] = 0
    payload["audit_fields"]["hand_class_count"] = 0

    with pytest.raises(ArtifactImportError) as error:
        import_preflop_artifact(write_payload(tmp_path, payload))

    assert error.value.code == INVALID_VALUE
