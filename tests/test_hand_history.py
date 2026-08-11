from __future__ import annotations

import json

import pytest

from poker_training_bot.hand_history import load_hand_history_file, parse_hand_history, replay_hand
from scripts.repo_paths import REPO_ROOT

FIXTURE = REPO_ROOT / "data" / "samples" / "phase_02_normalized_hands.json"
JSONL_FIXTURE = REPO_ROOT / "data" / "samples" / "phase_02_normalized_hands.jsonl"


def test_loads_and_replays_normalized_hand_history_fixture() -> None:
    replays = tuple(replay_hand(hand) for hand in load_hand_history_file(FIXTURE))
    by_id = {replay.hand.hand_id: replay for replay in replays}

    assert by_id["phase02-heads-up-showdown"].settlement.total_pot == 20
    assert by_id["phase02-heads-up-showdown"].settlement.payouts == {0: 20, 1: 0}
    assert by_id["phase02-three-way-side-pot"].committed_by_seat == {0: 50, 1: 100, 2: 200}
    assert by_id["phase02-three-way-side-pot"].settlement.payouts == {0: 150, 1: 100, 2: 100}
    assert all(replay.passed_expected_result for replay in replays)


def test_loads_jsonl_normalized_hand_history_fixture() -> None:
    replays = tuple(replay_hand(hand) for hand in load_hand_history_file(JSONL_FIXTURE))

    assert len(replays) == 2
    assert replays[0].hand.hand_id == "phase02-jsonl-heads-up"
    assert replays[0].settlement.payouts == {0: 20, 1: 0}
    assert replays[1].hand.hand_id == "phase02-jsonl-fold-out"
    assert replays[1].settlement.payouts == {0: 0, 1: 15}


def test_replays_uncontested_fold_out_hands() -> None:
    replays = tuple(replay_hand(hand) for hand in load_hand_history_file(FIXTURE))
    by_id = {replay.hand.hand_id: replay for replay in replays}

    preflop = by_id["phase02-preflop-fold-out"]
    assert preflop.settlement.payouts == {0: 0, 1: 15, 2: 0}
    assert preflop.settlement.pots[0].hand_rank is None
    assert preflop.folded_seats == (0, 2)

    turn = by_id["phase02-turn-fold-out"]
    assert turn.committed_by_seat == {0: 30, 1: 90}
    assert turn.settlement.payouts == {0: 0, 1: 120}
    assert all(replay.passed_expected_result for replay in replays)


def test_uncontested_replay_rejects_showdown_entries() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    assert raw["hand_id"] == "phase02-preflop-fold-out"
    raw["showdown"] = [{"seat": 1, "hole_cards": ["Ah", "Ad"]}]

    with pytest.raises(ValueError, match="must not include showdown entries"):
        replay_hand(parse_hand_history(raw))


def test_replay_rejects_streets_after_uncontested_finish() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    raw["streets"].append({"name": "flop", "board": ["2h", "3h", "4h"], "actions": []})

    with pytest.raises(ValueError, match="follows an uncontested hand"):
        replay_hand(parse_hand_history(raw))


def test_schema_rejects_street_gaps_and_wrong_board_sizes() -> None:
    skipped_flop = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][0]
    skipped_flop["streets"] = [
        skipped_flop["streets"][0],
        skipped_flop["streets"][2],
        skipped_flop["streets"][3],
    ]
    with pytest.raises(ValueError, match="without gaps"):
        parse_hand_history(skipped_flop)

    short_flop = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][0]
    short_flop["streets"][1]["board"] = ["As", "Ks"]
    with pytest.raises(ValueError, match="flop street must deal exactly 3"):
        parse_hand_history(short_flop)


def test_short_stack_all_in_blind_post_replays() -> None:
    raw = {
        "schema_version": 1,
        "hand_id": "short-blind",
        "table": {"table_id": "phase02", "max_seats": 2},
        "players": [
            {"seat": 0, "player_id": "short", "starting_stack": 3},
            {"seat": 1, "player_id": "covering", "starting_stack": 100},
        ],
        "button_seat": 0,
        "blinds": {"small_blind": 5, "big_blind": 10},
        "streets": [
            {
                "name": "preflop",
                "board": [],
                "actions": [
                    {"seat": 0, "kind": "post_blind", "amount": 3},
                    {"seat": 1, "kind": "post_blind", "amount": 10},
                ],
            },
            {"name": "flop", "board": ["2h", "3h", "4h"], "actions": []},
            {"name": "turn", "board": ["8c"], "actions": []},
            {"name": "river", "board": ["Kd"], "actions": []},
        ],
        "showdown": [
            {"seat": 0, "hole_cards": ["Ah", "Kh"]},
            {"seat": 1, "hole_cards": ["8s", "8d"]},
        ],
        "result": {
            "winner_seats": [0, 1],
            "pot": 13,
            "payouts": [{"seat": 0, "amount": 6}, {"seat": 1, "amount": 7}],
        },
    }

    replay = replay_hand(parse_hand_history(raw))

    assert replay.settlement.payouts == {0: 6, 1: 7}


def test_blind_post_must_match_blind_unless_all_in() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    raw["streets"][0]["actions"][0] = {"seat": 0, "kind": "post_blind", "amount": 7}

    with pytest.raises(ValueError, match="must match a configured blind"):
        replay_hand(parse_hand_history(raw))


def test_replay_fails_closed_when_expected_result_does_not_match() -> None:
    hand = load_hand_history_file(FIXTURE)[0]
    raw = {
        "schema_version": hand.schema_version,
        "hand_id": hand.hand_id,
        "table": {"table_id": hand.table_id, "max_seats": hand.max_seats},
        "players": [
            {
                "seat": player.seat,
                "player_id": player.player_id,
                "starting_stack": player.starting_stack,
            }
            for player in hand.players
        ],
        "button_seat": hand.button_seat,
        "blinds": {"small_blind": hand.blinds.small_blind, "big_blind": hand.blinds.big_blind},
        "streets": [
            {
                "name": street.name.value,
                "board": [str(card) for card in street.board],
                "actions": [
                    {
                        "seat": action.seat,
                        "kind": action.kind.value,
                        **({"amount": action.amount} if action.amount is not None else {}),
                    }
                    for action in street.actions
                ],
            }
            for street in hand.streets
        ],
        "showdown": [
            {"seat": entry.seat, "hole_cards": [str(card) for card in entry.hole_cards]}
            for entry in hand.showdown
        ],
        "result": {
            "winner_seats": [1],
            "pot": 20,
            "payouts": [{"seat": 0, "amount": 0}, {"seat": 1, "amount": 20}],
        },
    }

    with pytest.raises(ValueError, match="does not match expected result"):
        replay_hand(parse_hand_history(raw))


def test_replay_rejects_over_committed_stack() -> None:
    raw = {
        "schema_version": 1,
        "hand_id": "over-commit",
        "table": {"table_id": "phase02", "max_seats": 2},
        "players": [
            {"seat": 0, "player_id": "a", "starting_stack": 4},
            {"seat": 1, "player_id": "b", "starting_stack": 100},
        ],
        "button_seat": 0,
        "blinds": {"small_blind": 5, "big_blind": 10},
        "streets": [
            {
                "name": "preflop",
                "board": [],
                "actions": [
                    {"seat": 0, "kind": "post_blind", "amount": 5},
                    {"seat": 1, "kind": "post_blind", "amount": 10},
                ],
            },
            {"name": "flop", "board": ["As", "Ks", "Qs"], "actions": []},
            {"name": "turn", "board": ["Js"], "actions": []},
            {"name": "river", "board": ["2d"], "actions": []},
        ],
        "showdown": [
            {"seat": 0, "hole_cards": ["Ts", "9c"]},
            {"seat": 1, "hole_cards": ["2c", "2h"]},
        ],
        "result": {
            "winner_seats": [0],
            "pot": 15,
            "payouts": [{"seat": 0, "amount": 15}, {"seat": 1, "amount": 0}],
        },
    }

    with pytest.raises(ValueError, match="committed more than its starting stack"):
        replay_hand(parse_hand_history(raw))


def test_replay_rejects_action_after_deciding_fold() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][0]
    raw["streets"][0]["actions"] = [
        {"seat": 0, "kind": "post_blind", "amount": 5},
        {"seat": 1, "kind": "post_blind", "amount": 10},
        {"seat": 0, "kind": "fold"},
        {"seat": 1, "kind": "raise", "amount": 30},
    ]

    with pytest.raises(ValueError, match="acts after the hand is decided"):
        replay_hand(parse_hand_history(raw))


def test_replay_rejects_blind_posts_by_wrong_seat_or_amount() -> None:
    wrong_seat = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    wrong_seat["streets"][0]["actions"][0]["seat"] = 1
    with pytest.raises(ValueError, match="owed by seat 0"):
        replay_hand(parse_hand_history(wrong_seat))

    covering_stack_post = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    covering_stack_post["players"][0]["starting_stack"] = 7
    covering_stack_post["streets"][0]["actions"][0]["amount"] = 7
    with pytest.raises(ValueError, match="must match a configured blind"):
        replay_hand(parse_hand_history(covering_stack_post))

    missing_big_blind = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][2]
    missing_big_blind["streets"][0]["actions"] = [
        {"seat": 0, "kind": "post_blind", "amount": 5}
    ]
    with pytest.raises(ValueError, match="must open with small and big blind"):
        replay_hand(parse_hand_history(missing_big_blind))


def test_short_all_in_blind_does_not_lower_the_price() -> None:
    raw = {
        "schema_version": 1,
        "hand_id": "short-bb-price",
        "table": {"table_id": "phase02", "max_seats": 3},
        "players": [
            {"seat": 0, "player_id": "sb", "starting_stack": 100},
            {"seat": 1, "player_id": "short_bb", "starting_stack": 4},
            {"seat": 2, "player_id": "button", "starting_stack": 100},
        ],
        "button_seat": 2,
        "blinds": {"small_blind": 5, "big_blind": 10},
        "streets": [
            {
                "name": "preflop",
                "board": [],
                "actions": [
                    {"seat": 0, "kind": "post_blind", "amount": 5},
                    {"seat": 1, "kind": "post_blind", "amount": 4},
                    {"seat": 2, "kind": "call", "amount": 5},
                ],
            }
        ],
        "showdown": [],
        "result": {
            "winner_seats": [1],
            "pot": 14,
            "payouts": [
                {"seat": 0, "amount": 0},
                {"seat": 1, "amount": 14},
                {"seat": 2, "amount": 0},
            ],
        },
    }

    with pytest.raises(ValueError, match="call amount does not match"):
        replay_hand(parse_hand_history(raw))

    raw["streets"][0]["actions"][2] = {"seat": 2, "kind": "raise", "amount": 19}
    with pytest.raises(ValueError, match="minimum raise"):
        replay_hand(parse_hand_history(raw))


def test_schema_rejects_unknown_fields() -> None:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))["hands"][0]
    raw["unexpected"] = True

    with pytest.raises(ValueError, match="unknown keys"):
        parse_hand_history(raw)


def test_schema_rejects_duplicate_payout_seats() -> None:
    hand = load_hand_history_file(FIXTURE)[0]
    raw = {
        "schema_version": hand.schema_version,
        "hand_id": hand.hand_id,
        "table": {"table_id": hand.table_id, "max_seats": hand.max_seats},
        "players": [
            {
                "seat": player.seat,
                "player_id": player.player_id,
                "starting_stack": player.starting_stack,
            }
            for player in hand.players
        ],
        "button_seat": hand.button_seat,
        "blinds": {"small_blind": hand.blinds.small_blind, "big_blind": hand.blinds.big_blind},
        "streets": [
            {
                "name": street.name.value,
                "board": [str(card) for card in street.board],
                "actions": [
                    {
                        "seat": action.seat,
                        "kind": action.kind.value,
                        **({"amount": action.amount} if action.amount is not None else {}),
                    }
                    for action in street.actions
                ],
            }
            for street in hand.streets
        ],
        "showdown": [
            {"seat": entry.seat, "hole_cards": [str(card) for card in entry.hole_cards]}
            for entry in hand.showdown
        ],
        "result": {
            "winner_seats": [0],
            "pot": 20,
            "payouts": [{"seat": 0, "amount": 20}, {"seat": 0, "amount": 0}],
        },
    }

    with pytest.raises(ValueError, match="duplicate payout seats"):
        parse_hand_history(raw)
