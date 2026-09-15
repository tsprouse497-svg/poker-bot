"""The committed flop solve: what a cell says, and every way it is refused.

A sibling of `schema` and `importer`, not an extension. The preflop artifact ships a whole chart
in one file; this one ships **an index plus a three-flop sample**, because decision 6 measured the
solve at about 15 MB per hero decision node per preflop line against a 20 MiB `data/artifacts` cap.
The bytes the bot plays live in object storage outside git and nothing here fetches anything, so
the gate reads the sample and the index with no network and no solver.

**Every check refuses rather than repairs.** A weight outside 0 to 1 is not a frequency any dealer
can deal, and a committed size above what the acting seat can put in is a legality failure
`DecisionAuditRecord` would raise on mid-hand, once, at whichever table reached it first. Refused
at import each is one red against a file nobody has played yet, and nothing is clamped, rounded
into range, or skipped over.

**The key is derived and compared, never parsed**, and **pot and effective stack follow from the
line rather than being stored on trust**: `postflop_key.postflop_spot_key` is the single producer,
and the line closes with hero paying the standing level, so a 2.5bb button open at 100bb gives 5.5
and 97.5 and an SB three-bet to 7.5 gives 16.0 - decision 10's two figures, reproduced here.

What this module does **not** do: it re-derives no digest, which
`A-COMMITTED-SOLVE-DIGEST-IS-A-CLAIM-NO-GATE-RE-DERIVES` owns, and it names no table-side refusal
code, since which cause a miss is reported under belongs to whoever is answering a table."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_training_bot.poker_core.positions import table_positions
from poker_training_bot.solver_artifacts.postflop_key import (
    FlopAction,
    board_suit_map,
    canonical_board,
    canonical_hole_cards,
    postflop_spot_key,
    price_within_band,
)
from poker_training_bot.solver_artifacts.schema import WEIGHT_SUM_TOLERANCE, PreflopAction
from poker_training_bot.solver_artifacts.schema import spot_key as derive_preflop_spot_key
from poker_training_bot.solver_artifacts.solve_conditions import (
    BlindStructure,
    parse_blind_structure,
)
from poker_training_bot.solver_artifacts.strict_json import (
    INVALID_VALUE,
    ArtifactImportError,
    _object_pairs_hook,
    _require_int,
    _require_keys,
    _require_list,
    _require_object,
    _require_str,
    _require_unique_keys,
)

CELL_SCHEMA_VERSION = 1
INDEX_SCHEMA_VERSION = 1

EXPLOITABILITY_TARGET_PCT_OF_POT = 0.3
"""What the campaign solves for, as a percent of the starting pot - never in big blinds, because
phase 10's 0.01bb is preflop, in the wrong unit, and reproduces none of the measured counts."""

EXPLOITABILITY_CEILING_PCT_OF_POT = 1.0
"""The worst a played cell may carry, not an accuracy anyone aimed at: a cap-bound cell is
committed under it and refused above, and the report prints the spread rather than one number."""

SOLVE_ITERATION_CAP = 1200

RANGE_WEIGHT_FLOOR = 0.01
"""Decision 12, ruled by Taylor 2026-09-09: floor the input ranges at 1 percent, class-level.
Class-level is a constraint rather than a preference: one suit-specific weight collapses the
isomorphism group to the identity and forfeits the whole saving on every non-rainbow board."""

POSTFLOP_DIR = Path(__file__).resolve().parents[3] / "data" / "artifacts" / "postflop"
INDEX_PATH = POSTFLOP_DIR / "index.json"
SAMPLE_DIR = POSTFLOP_DIR / "sample"

UNREADABLE_FILE = "postflop:unreadable-file"
INVALID_JSON = "postflop:invalid-json"
UNSUPPORTED_SCHEMA_VERSION = "postflop:unsupported-schema-version"
INVALID_VALUE_CODE = "postflop:invalid-value"
PREFLOP_KEY_MISMATCH = "postflop:preflop-key-mismatch"
POT_DOES_NOT_FOLLOW_FROM_THE_LINE = "postflop:pot-does-not-follow-from-the-line"
BOARD_DRESSING_MISMATCH = "postflop:board-dressing-mismatch"
SPOT_KEY_MISMATCH = "postflop:spot-key-mismatch"
EXPLOITABILITY_ABOVE_CEILING = "postflop:exploitability-above-ceiling"
ITERATIONS_ABOVE_CAP = "postflop:iterations-above-cap"
UNPLAYABLE_SIZE = "postflop:unplayable-size"
WEIGHT_OUT_OF_BOUNDS = "postflop:weight-out-of-bounds"
WEIGHT_SUM = "postflop:weight-sum"
PRICE_OUTSIDE_BAND = "postflop:price-outside-band"

REASON_CODES: tuple[str, ...] = (
    UNREADABLE_FILE, INVALID_JSON, UNSUPPORTED_SCHEMA_VERSION, INVALID_VALUE_CODE,
    PREFLOP_KEY_MISMATCH, POT_DOES_NOT_FOLLOW_FROM_THE_LINE, BOARD_DRESSING_MISMATCH,
    SPOT_KEY_MISMATCH, EXPLOITABILITY_ABOVE_CEILING, ITERATIONS_ABOVE_CAP, UNPLAYABLE_SIZE,
    WEIGHT_OUT_OF_BOUNDS, WEIGHT_SUM, PRICE_OUTSIDE_BAND,
)

_CELL_KEYS = set(
    "cell_schema_version spot_key board suit_map preflop_spot_key table_size stack_depth_bb"
    " hero_position blind_structure preflop_actions price_substitutions pot_bb"
    " effective_stack_bb flop_actions hero_street_bet_bb actions bet_sizes_bb hand_classes"
    " class_weights achieved_exploitability_pct_of_pot iterations".split()
)
_INDEX_KEYS = set(
    "index_schema_version object_storage covered_preflop_lines line_count_bound_by"
    " cells_solved_and_rejected_above_one_percent committed_bytes headroom_bytes entries".split()
)
_ACTION_KEYS = {"position", "action"}
_SUBSTITUTION_KEYS = {"position", "actual_bb", "solved_bb"}
_SUIT_KEYS = {"c", "d", "h", "s"}
_SIZED_ACTIONS = frozenset({"bet", "raise"})


class PostflopArtifactError(ValueError):
    """A fail-closed refusal of a committed flop cell or index, naming the file and the cause."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _refuse(code: str, origin: str, message: str) -> PostflopArtifactError:
    return PostflopArtifactError(code, f"{origin}: {message}")


def _bad(origin: str, message: str) -> PostflopArtifactError:
    return _refuse(INVALID_VALUE_CODE, origin, message)


def _number(payload: Mapping[str, Any], origin: str, key: str, path: str = "cell") -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _bad(origin, f"{path}.{key} must be a number, got {value!r}")
    return float(value)


def check_size_is_playable(
    size_chips: float, hero_street_bet: float, hero_stack: float, *, cell: str
) -> None:
    """Refuse a bet or raise the acting seat could not put in: everything in front of hero is the
    chips already committed on this street plus the stack behind. The unit is the caller's and the
    comparison a bare inequality, so it holds in big blinds at import and in chips at a table."""
    if size_chips > hero_street_bet + hero_stack:
        raise _refuse(
            UNPLAYABLE_SIZE, cell,
            f"a committed size of {size_chips} is above the {hero_street_bet + hero_stack} the"
            " acting seat can put in, so it is refused here rather than mid-hand at a table")


def floor_range(weights: Mapping[str, float]) -> dict[str, float]:
    """Apply decision 12's class-level floor to one input range: every class keeps its identity
    and every weight comes out at or above the floor. Note what that does to a hand the export
    left at zero - it **lifts** it to the floor rather than dropping it, the behaviour
    `tests/test_postflop_artifact.py` pins by name, where decision 12 measured the other operation
    (deleting the 878 combos under 0.01 costs 0.199% of the defending range's weight). Two
    different ranges, and a report has to say which one it published."""
    floored: dict[str, float] = {}
    for hand, weight in weights.items():
        if isinstance(weight, bool) or not isinstance(weight, int | float):
            raise PostflopArtifactError(INVALID_VALUE_CODE, f"{hand!r} weighs {weight!r}")
        if len(hand) not in (2, 3):
            raise PostflopArtifactError(INVALID_VALUE_CODE, f"{hand!r} is not a hand class")
        floored[hand] = max(float(weight), RANGE_WEIGHT_FLOOR)
    return floored


@dataclass(frozen=True)
class PostflopCell:
    """One committed hero decision node on one flop, with the evidence it was solved under."""

    spot_key: str
    board: tuple[str, ...]
    suit_map: tuple[tuple[str, str], ...]
    preflop_spot_key: str
    hero_position: str
    preflop_actions: tuple[PreflopAction, ...]
    price_substitutions: tuple[tuple[str, float, float], ...]
    pot_bb: float
    effective_stack_bb: float
    flop_actions: tuple[FlopAction, ...]
    hero_street_bet_bb: float
    actions: tuple[str, ...]
    bet_sizes_bb: tuple[float, ...]
    hand_classes: tuple[str, ...]
    class_weights: tuple[tuple[float, ...], ...]
    achieved_exploitability_pct_of_pot: float
    iterations: int

    @property
    def hero_stack_bb(self) -> float:
        """What is behind hero here: the effective stack less what is already in this street."""
        return self.effective_stack_bb - self.hero_street_bet_bb

    def weights_for(self, hand_class: str) -> tuple[float, ...] | None:
        """Hero's strategy for one canonical combo, or `None` - a combo the cell does not
        hold is a miss the caller names, never a row filled in from the nearest hand."""
        for name, row in zip(self.hand_classes, self.class_weights, strict=True):
            if name == hand_class:
                return row
        return None


def _entries(raw: list[Any], origin: str, label: str, size_key: str) -> list[dict[str, Any]]:
    """One recorded action list, shape-checked before anything poker-specific reads it."""
    parsed: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        path = f"cell.{label}[{index}]"
        payload = _require_object(item, origin, path)
        _require_unique_keys(payload, origin, path, INVALID_VALUE)
        _require_keys(payload, origin, path, set(_ACTION_KEYS), {size_key})
        size = None if size_key not in payload else _number(payload, origin, size_key, path)
        parsed.append({
            "path": path, "size": size,
            "position": _require_str(payload, origin, path, "position"),
            "action": _require_str(payload, origin, path, "action"),
        })
    return parsed


def _parse_actions(raw: list[Any], origin: str, label: str, size_key: str, factory: Any) -> tuple:
    """Build one street's recorded actions, letting the vocabulary itself do the refusing."""
    built = []
    for entry in _entries(raw, origin, label, size_key):
        try:
            built.append(factory(entry["position"], entry["action"], entry["size"]))
        except ValueError as error:
            raise _bad(origin, f"{entry['path']}: {error}") from error
    return tuple(built)


def _derive_pot_and_stack(
    table_size: int, depth: int, blinds: BlindStructure, hero: str, entries: Sequence[PreflopAction]
) -> tuple[float, float]:
    """The pot and the effective stack this line produces, in big blinds. The line closes with
    hero paying the standing level, because a flop exists only once the preflop betting is over
    and the key names hero's decision rather than the finished street; both live seats therefore
    sit at that level, so the effective stack is the depth less it."""
    positions = table_positions(table_size)
    bets = dict.fromkeys(positions, 0.0)
    # Heads-up the button posts the small blind; at every larger table the small blind does.
    for label, posted in (
        ("BTN" if table_size == 2 else "SB", blinds.small_blind_bb), ("BB", blinds.big_blind_bb)
    ):
        if label in bets:
            bets[label] = posted
    level = blinds.big_blind_bb
    for entry in entries:
        if entry.action == "raise":
            level = float(entry.size_bb or 0.0)
        bets[entry.position] = level
    bets[hero] = level
    return sum(bets.values()) + blinds.ante_bb * len(positions), float(depth) - level


def _check_price_substitutions(
    raw: list[Any], origin: str, entries: Sequence[PreflopAction]
) -> tuple[tuple[str, float, float], ...]:
    """Every recorded substitution names a price this line declares, and sits inside the band.
    The substitution is a fact about which ranges the cell was solved against, settled when the
    solve is committed rather than recomputed at a table; outside the band it is no substitution
    at all, since a 12bb three-bet from a 7.5bb cell moves SPR from 5.78 to 3.52."""
    declared = {
        entry.position: float(entry.size_bb or 0.0) for entry in entries if entry.action == "raise"
    }
    recorded: list[tuple[str, float, float]] = []
    for index, item in enumerate(raw):
        path = f"cell.price_substitutions[{index}]"
        payload = _require_object(item, origin, path)
        _require_unique_keys(payload, origin, path, INVALID_VALUE)
        _require_keys(payload, origin, path, set(_SUBSTITUTION_KEYS))
        position = _require_str(payload, origin, path, "position")
        actual = _number(payload, origin, "actual_bb", path)
        solved = _number(payload, origin, "solved_bb", path)
        if declared.get(position) != solved:
            raise _refuse(
                PRICE_OUTSIDE_BAND, origin,
                f"{path} substitutes onto {solved}bb, not what {position} raises to here",
            )
        if not price_within_band(solved, actual):
            raise _refuse(
                PRICE_OUTSIDE_BAND, origin,
                f"{path} records an actual {actual}bb against a cell solved at {solved}bb, which"
                " is outside the band this phase answers at all",
            )
        recorded.append((position, actual, solved))
    return tuple(recorded)


def _check_strategy_block(
    payload: Mapping[str, Any], origin: str, representative: tuple[str, ...]
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[tuple[float, ...], ...]]:
    """Hero's classes and their weights, which is the part a wrong number reaches a student by."""
    actions = tuple(str(item) for item in _require_list(payload, origin, "cell", "actions"))
    raw_classes = _require_list(payload, origin, "cell", "hand_classes")
    raw_rows = _require_list(payload, origin, "cell", "class_weights")
    if not raw_rows or len(raw_classes) != len(raw_rows):
        raise _bad(origin, f"{len(raw_classes)} classes against {len(raw_rows)} rows is ragged")
    classes: list[str] = []
    for index, item in enumerate(raw_classes):
        path = f"cell.hand_classes[{index}]"
        if not isinstance(item, str) or len(item) != 4:
            raise _bad(origin, f"{path} must be two cards, got {item!r}")
        try:
            moved = "".join(canonical_hole_cards(representative, (item[:2], item[2:])))
        except ValueError as error:
            raise _bad(origin, f"{path}: {error}") from error
        if moved != item:
            raise _bad(origin, f"{path} is {item!r}, which reads {moved!r} on the representative")
        classes.append(item)
    if len(set(classes)) != len(classes):
        raise _bad(origin, "cell.hand_classes names one class twice")
    rows: list[tuple[float, ...]] = []
    for index, raw_row in enumerate(raw_rows):
        path = f"cell.class_weights[{index}]"
        if not isinstance(raw_row, list) or len(raw_row) != len(actions):
            raise _bad(origin, f"{path} must hold one weight per action, {len(actions)} of them")
        total = 0.0
        for weight in raw_row:
            if isinstance(weight, bool) or not isinstance(weight, int | float):
                raise _bad(origin, f"{path} holds {weight!r}")
            if not 0.0 <= weight <= 1.0:
                raise _refuse(
                    WEIGHT_OUT_OF_BOUNDS, origin,
                    f"{path} holds {weight!r}, which is not a frequency any dealer can deal, so"
                    " the cell is refused rather than handed to the table",
                )
            total += float(weight)
        if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
            raise _refuse(WEIGHT_SUM, origin, f"{path} sums to {total!r} rather than to one")
        rows.append(tuple(float(weight) for weight in raw_row))
    return actions, tuple(classes), tuple(rows)


def _build_cell(raw: Any, origin: str) -> PostflopCell:
    payload = _require_object(raw, origin, "cell")
    _require_unique_keys(payload, origin, "cell", INVALID_VALUE)
    _require_keys(payload, origin, "cell", set(_CELL_KEYS))
    version = _require_int(payload, origin, "cell", "cell_schema_version")
    if version != CELL_SCHEMA_VERSION:
        raise _refuse(UNSUPPORTED_SCHEMA_VERSION, origin, f"cell version {version} is unsupported")
    table_size = _require_int(payload, origin, "cell", "table_size")
    stack_depth_bb = _require_int(payload, origin, "cell", "stack_depth_bb")
    hero_position = _require_str(payload, origin, "cell", "hero_position")
    blinds = parse_blind_structure(payload, origin)
    preflop_actions = _parse_actions(
        _require_list(payload, origin, "cell", "preflop_actions"),
        origin, "preflop_actions", "size_bb", PreflopAction,
    )
    try:
        line_key = derive_preflop_spot_key(
            table_size, stack_depth_bb, hero_position, preflop_actions
        )
    except ValueError as error:
        raise _bad(origin, f"cell describes no preflop spot: {error}") from error
    if line_key != _require_str(payload, origin, "cell", "preflop_spot_key"):
        raise _refuse(
            PREFLOP_KEY_MISMATCH, origin, f"cell.preflop_spot_key re-derives as {line_key!r}"
        )
    substitutions = _check_price_substitutions(
        _require_list(payload, origin, "cell", "price_substitutions"), origin, preflop_actions
    )
    pot_bb = _number(payload, origin, "pot_bb")
    effective_stack_bb = _number(payload, origin, "effective_stack_bb")
    derived = _derive_pot_and_stack(
        table_size, stack_depth_bb, blinds, hero_position, preflop_actions
    )
    if (pot_bb, effective_stack_bb) != derived:
        raise _refuse(
            POT_DOES_NOT_FOLLOW_FROM_THE_LINE, origin,
            f"cell states a pot of {pot_bb} with {effective_stack_bb} behind, and its own"
            f" substituted line produces {derived[0]} with {derived[1]}")
    board = tuple(_require_list(payload, origin, "cell", "board"))
    try:
        representative, derived_map = canonical_board(board), board_suit_map(board)
    except ValueError as error:
        raise _bad(origin, f"cell.board: {error}") from error
    stored_map = _require_object(payload.get("suit_map"), origin, "cell.suit_map")
    _require_keys(stored_map, origin, "cell.suit_map", set(_SUIT_KEYS))
    if dict(stored_map) != derived_map:
        raise _refuse(
            BOARD_DRESSING_MISMATCH, origin,
            f"cell.suit_map does not carry {list(board)} to {list(representative)}; a second"
            " dressing of one class is a second cell for a class that already has one")
    flop_actions = _parse_actions(
        _require_list(payload, origin, "cell", "flop_actions"),
        origin, "flop_actions", "size_pct", FlopAction,
    )
    try:
        derived_key = postflop_spot_key(line_key, board, flop_actions, pot_bb, effective_stack_bb)
    except ValueError as error:
        raise _bad(origin, f"cell describes no flop spot: {error}") from error
    if derived_key != _require_str(payload, origin, "cell", "spot_key"):
        raise _refuse(SPOT_KEY_MISMATCH, origin, f"cell.spot_key re-derives as {derived_key!r}")
    achieved = _number(payload, origin, "achieved_exploitability_pct_of_pot")
    if not 0.0 <= achieved <= EXPLOITABILITY_CEILING_PCT_OF_POT:
        raise _refuse(
            EXPLOITABILITY_ABOVE_CEILING, origin,
            f"cell was solved to {achieved}% of pot, over the"
            f" {EXPLOITABILITY_CEILING_PCT_OF_POT}% a played cell may carry")
    iterations = _require_int(payload, origin, "cell", "iterations")
    if not 0 < iterations <= SOLVE_ITERATION_CAP:
        raise _refuse(
            ITERATIONS_ABOVE_CAP, origin, f"cell ran {iterations} of {SOLVE_ITERATION_CAP}")
    hero_street_bet = _number(payload, origin, "hero_street_bet_bb")
    if not 0.0 <= hero_street_bet <= effective_stack_bb:
        raise _bad(origin, f"cell.hero_street_bet_bb is {hero_street_bet} of {effective_stack_bb}")
    actions, hand_classes, rows = _check_strategy_block(payload, origin, representative)
    sizes: list[float] = []
    for index, item in enumerate(_require_list(payload, origin, "cell", "bet_sizes_bb")):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise _bad(origin, f"cell.bet_sizes_bb[{index}] must be a number, got {item!r}")
        sizes.append(float(item))
    sized = sum(1 for action in actions if action in _SIZED_ACTIONS)
    if len(sizes) != sized:
        raise _bad(origin, f"{sized} sized actions against {len(sizes)} sizes leaves one unpriced")
    behind = effective_stack_bb - hero_street_bet
    for size in sizes:
        check_size_is_playable(size, hero_street_bet, behind, cell=origin)
    return PostflopCell(
        spot_key=derived_key, board=board, suit_map=tuple(sorted(derived_map.items())),
        preflop_spot_key=line_key, hero_position=hero_position, preflop_actions=preflop_actions,
        price_substitutions=substitutions, pot_bb=pot_bb, effective_stack_bb=effective_stack_bb,
        flop_actions=flop_actions, hero_street_bet_bb=hero_street_bet, actions=actions,
        bet_sizes_bb=tuple(sizes), hand_classes=hand_classes, class_weights=rows,
        achieved_exploitability_pct_of_pot=achieved, iterations=iterations,
    )


def _read_json(path: Path | str) -> tuple[Any, str]:
    file_path = Path(path)
    origin = str(file_path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as error:
        raise _refuse(UNREADABLE_FILE, origin, f"cannot be read: {error}") from error
    try:
        return json.loads(text, object_pairs_hook=_object_pairs_hook), origin
    except json.JSONDecodeError as error:
        raise _refuse(INVALID_JSON, origin, f"is not valid JSON: {error}") from error


def import_postflop_cell(path: Path | str) -> PostflopCell:
    """Import one committed flop cell, or refuse it. Nothing partially loaded is returned: a cell
    is either fully re-derived - its preflop key, its pot and stack, its board dressing, its spot
    key, its accuracy, its sizes and every weight - or this raises, naming what disagreed."""
    raw, origin = _read_json(path)
    try:
        return _build_cell(raw, origin)
    except ArtifactImportError as error:
        raise PostflopArtifactError(error.code, error.message) from error


def import_postflop_sample(directory: Path | str = SAMPLE_DIR) -> tuple[PostflopCell, ...]:
    """Import every committed sample cell by filename. One unimportable file fails the call."""
    root = Path(directory)
    if not root.is_dir():
        raise _refuse(UNREADABLE_FILE, str(root), "is not a directory")
    files = sorted(item for item in root.glob("*.json") if item.is_file())
    if not files:
        raise _refuse(UNREADABLE_FILE, str(root), "holds no committed sample flop")
    return tuple(import_postflop_cell(item) for item in files)


def import_postflop_index(path: Path | str = INDEX_PATH) -> dict[str, Any]:
    """Read the committed index strictly, or refuse it.

    A plain mapping rather than a typed record: the index's own obligations - four figures an
    entry, no placeholder, one digest width - are pinned against the committed bytes by
    `tests/test_postflop_artifact.py`, and a second layer here would be a second source of truth.
    What this adds is what `json.loads` cannot do alone: a file declaring a field twice is refused
    rather than read as whichever copy came last."""
    raw, origin = _read_json(path)
    try:
        payload = _require_object(raw, origin, "index")
        _require_unique_keys(payload, origin, "index", INVALID_VALUE)
        _require_keys(payload, origin, "index", set(_INDEX_KEYS), {"digest_authenticates"})
        version = _require_int(payload, origin, "index", "index_schema_version")
    except ArtifactImportError as error:
        raise PostflopArtifactError(error.code, error.message) from error
    if version != INDEX_SCHEMA_VERSION:
        raise _refuse(UNSUPPORTED_SCHEMA_VERSION, origin, f"index version {version} is unsupported")
    return dict(payload)


def indexed_spot_keys(index: Mapping[str, Any]) -> frozenset[str]:
    """Every spot the solve holds, fetched here or not - a different question from what
    `import_postflop_sample` returns, and a caller pooling the two understates its coverage by the
    whole artifact: on a fresh clone 1,752 of 1,755 classes are listed here and fetched nowhere."""
    return frozenset(str(entry["spot_key"]) for entry in index["entries"])
