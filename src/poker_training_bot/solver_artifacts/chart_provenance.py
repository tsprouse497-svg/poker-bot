"""What the committed chart says about where it came from and what it does not price.

Split out of `chart_derivation` because it is a different subject and because the pair broke
the 500-line cap: this is prose for a human reading the chart, that is the rule selecting the
nodes. The two confessions are required by name - the notes state the realization bias and the
multiway defect with the excluded node count, so a reader can tell a withheld family is a
decision rather than a gap in the conversion.

**Every number in the prose is recomputed by the run that writes the chart.** It used to be
hand-typed, and this docstring used to say "nothing here is a number a check recomputes" as
though that were the subject rather than a defect with no guard anywhere:
`convert_preflop_export.py --check` reproduces whatever this code emits, so a sentence a
re-solve left behind ships inside `audit_fields.notes` with the gate green. MAINT-34's
re-solve falsified eleven figures at once, the ladder sentence three ways. `GENERATED_AT` and
`MULTIWAY_EQUITY_UNDERSTATEMENT` are the two literals left, each saying so in its own
docstring, and the note labels the second where it states it.
"""

from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

from poker_training_bot.solver_artifacts.chart_selection import (
    SEATS,
    cold_call_index,
    exclusion_code,
    is_committed_node,
    raises_faced,
    require_known_kind,
)
from poker_training_bot.solver_artifacts.gtopen_export import class_combos, gtopen_class_index
from poker_training_bot.solver_artifacts.hand_classes import HAND_CLASSES
from poker_training_bot.solver_artifacts.lookup import (
    DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH,
    DERIVATION_BIG_BLIND_SQUEEZE_SPOT,
    DERIVATION_EXCLUSION_CODES,
    DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD,
    DERIVATION_NO_ARRIVING_HAND_CLASS,
)

if TYPE_CHECKING:
    from poker_training_bot.solver_artifacts.chart_derivation import NodeCensus
    from poker_training_bot.solver_artifacts.gtopen_export import SolverExport, SolverNode

    _ByPath = dict[tuple[int, ...], SolverNode]

__all__ = [
    "EXPORT_REFERENCE",
    "GENERATED_AT",
    "MULTIWAY_EQUITY_UNDERSTATEMENT",
    "SOURCE_NAME",
    "artifact_notes",
    "sizing_notes",
]

SOURCE_NAME = "GTOpen 6-max 100bb rake-free"
EXPORT_REFERENCE = "data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz"

GENERATED_AT = "2026-09-16T00:00:00Z"
"""When this chart was derived, as a literal, and the only date anything here states.

Three readings were checked rather than assumed. **Stamped at derivation time** cannot be:
`--check` compares the text this code produces against the committed file, so a wall clock
makes the chart irreproducible a second after writing and reddens the gate for good.
**Read from the export's own solve record** is the right answer and there is nothing to read:
the payload carries `config`, `positions`, `quantisation_scale`, `nodes` and `saved_solve`,
the card the gap, the iterations and a wall-clock duration, neither a date. So it stays a
literal restamped by hand, the one thing here a re-solve can still strand. The durable fix is
upstream - `extract_gtopen_preflop.py` writing a `solved_at` into the card.
"""

MULTIWAY_EQUITY_UNDERSTATEMENT = (10.5, 14)
"""How far GTOpen's product approximation falls below true three-way equity: points on average
across the 169 classes, and points on the suited connectors, which are worst.

Measured at 4,000 trials a class in phase 14's cold-call verification and filed as
`MULTIWAY-EQUITY-IS-A-PRODUCT-APPROXIMATION`. A property of the solver's equity model rather
than of a solve, so no re-solve moves it and no export holds anything to recompute it from.
"""

_PERCENT = 100.0
_AGGRESSIVE_KINDS = ("raise", "jam")
_TIER_NAMES = ("Opening, with nothing in front of hero", "Facing an open", "Facing a three-bet")


def _derivation() -> ModuleType:
    """`chart_derivation`, fetched at call time rather than imported at the top.

    That module imports this one, so a module-level import here would be a cycle; by the time
    anything asks for a note it is fully loaded. Fetched rather than restated: the readings the
    note shares with the chart are ruled, and a second copy is how the two come to disagree.
    """
    from poker_training_bot.solver_artifacts import chart_derivation

    return chart_derivation


def _committed(by_path: _ByPath) -> tuple[SolverNode, ...]:
    """Every node the chart commits, in export order.

    Takes the mapping rather than the export, and so does everything above and below it that
    can, up to the two public entry points. `SolverExport.by_path()` builds a FRESH dict on every
    call and `chart_selection` caches its tree walk on that dict's identity, so a mapping per
    sentence re-walks the whole tree per sentence. Threading `derive_chart`'s own mapping through
    leaves exactly one rebuild, inside `merged_cells`, which takes the export, and took the
    notes' share of `--check` from about 9 seconds to about 3.3 here. The seconds are
    machine-dependent; the one-rebuild count is not.
    """
    return tuple(node for node in by_path.values() if is_committed_node(by_path, node))


def _kind_at(by_path: _ByPath, path: tuple[int, ...], index: int) -> str:
    """What the seat to act at `path` did when it took its action `index`."""
    return require_known_kind(by_path[path], by_path[path].actions[index])


def _seats_live(by_path: _ByPath, node: SolverNode) -> int:
    """How many seats have not folded on the line into a node - the reading the multiway clause
    was deliberately written *not* to use. A seat count asks who could still enter the pot, the
    clause asks where the decision mass ends up, and the note states the gap between them.
    """
    folds = [d for d, i in enumerate(node.path) if _kind_at(by_path, node.path[:d], i) == "fold"]
    return len(SEATS) - len(folds)


def _faced_price(by_path: _ByPath, node: SolverNode) -> float:
    """The largest amount anybody has raised to on the line into a node."""
    raised = [
        float(by_path[node.path[:depth]].actions[index].to)
        for depth, index in enumerate(node.path)
        if _kind_at(by_path, node.path[:depth], index) in _AGGRESSIVE_KINDS
    ]
    return max(raised, default=0.0)


def _combo_weighted_fold_pct(node: SolverNode) -> float:
    """How much of hero's range folds at a node, weighted by combinations rather than by the
    plain mean over the 169 classes: the two disagree by four to five points at the spots this
    note quotes, and the one a reader checks against a published range is the weighted one.
    """
    folded = 0.0
    combos = 0.0
    for hand_class_text in HAND_CLASSES:
        column = gtopen_class_index(hand_class_text)
        weight = class_combos(hand_class_text)
        folded += weight * sum(
            node.strategy_bp[index][column]
            for index, action in enumerate(node.actions)
            if require_known_kind(node, action) == "fold"
        )
        combos += weight
    return folded / combos / 100.0


def _closes_into_a_multiway_flop(by_path: _ByPath, node: SolverNode) -> bool:
    """Whether a call the chart publishes here ends the betting into a three-or-more-way pot.

    Hero's cold call is skipped, the chart republishing it as a raise. "Closes" is the whole
    claim - a terminal, not a subtree that mostly ends multiway - so the child must be absent
    from the tree and three or more seats live when the call is made.
    """
    cold = cold_call_index(by_path, node)
    return _seats_live(by_path, node) >= 3 and any(
        require_known_kind(node, action) == "call"
        and index != cold
        and (*node.path, index) not in by_path
        for index, action in enumerate(node.actions)
    )


def _aggressive_prices(node: SolverNode) -> tuple[tuple[str, float], ...]:
    """Every price hero may put in at a node, as (kind, to), deduplicated and sorted."""
    offered = {
        (require_known_kind(node, action), float(action.to))
        for action in node.actions
        if require_known_kind(node, action) in _AGGRESSIVE_KINDS
    }
    return tuple(sorted(offered))


def _decision_shares(by_path: _ByPath) -> tuple[float, float]:
    """What share of the bot's preflop decisions the committed set carries, and what the rest
    do. Weighted by arrival - the chance the line gets played at all - not by node count, which
    is the other figure in the same sentence and a different reading of the same split.
    """
    node_arrival_ppb = _derivation().node_arrival_ppb
    total = 0.0
    committed = 0.0
    for node in by_path.values():
        arrival = node_arrival_ppb(by_path, node)
        total += arrival
        if is_committed_node(by_path, node):
            committed += arrival
    if total <= 0.0:
        return (0.0, 0.0)
    return (_PERCENT * committed / total, _PERCENT * (total - committed) / total)


def _price_text(kind: str, to: float) -> str:
    """A price as the ladder should read it, so a shove is never mistaken for a sized raise."""
    return f"{_number(to)} as a shove" if kind == "jam" else _number(to)


def _number(value: float) -> str:
    """A price as the chart writes it: 2.5 stays 2.5, 100.0 becomes 100."""
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,g}"


def _listed(values: tuple[str, ...]) -> str:
    """`a`, `a and b`, `a, b and c` - the notes are prose, not a bullet list."""
    if len(values) <= 1:
        return "".join(values)
    return f"{', '.join(values[:-1])} and {values[-1]}"


def _exclusion_clauses(by_path: _ByPath, census: NodeCensus) -> str:
    """One sentence per exclusion bucket that has anything in it, in the rule's own order, so a
    bucket that empties loses its sentence and one that fills gains one. The fourth clause was
    dead at a 7.5bb three-bet and has hundreds of nodes under it at 13.5bb; under the old
    hand-typed note it simply went unmentioned, which is why the clause count is counted too.
    """
    counted = census.excluded
    parts: list[str] = []
    depth = counted.get(DERIVATION_BEYOND_COMMITTED_RAISE_DEPTH, 0)
    if depth:
        parts.append(
            f"{depth:,} nodes already have three raises in and are the four-bet family, which a"
            " later phase takes up."
        )
    exposure = counted.get(DERIVATION_MULTIWAY_EXPOSURE_ABOVE_THRESHOLD, 0)
    if exposure:
        parts.append(
            f"{exposure:,} nodes send too much of their decision mass to a flop with three or"
            " more players in it."
        )
    squeeze = counted.get(DERIVATION_BIG_BLIND_SQUEEZE_SPOT, 0)
    if squeeze:
        band = sorted(
            _combo_weighted_fold_pct(node)
            for node in by_path.values()
            if exclusion_code(by_path, node) == DERIVATION_BIG_BLIND_SQUEEZE_SPOT
        )
        parts.append(
            f"{squeeze:,} nodes are the big blind answering an open somebody has already called,"
            " refused by a rule naming the seat rather than by the exposure measurement, which"
            f" cannot reach them - the big blind folds between {band[0]:.2f} and {band[-1]:.2f}"
            " percent of its range at them, so that call branch carries too little mass to trip"
            " the threshold even though what the call buys is a three-way pot every time."
        )
    barren = counted.get(DERIVATION_NO_ARRIVING_HAND_CLASS, 0)
    if barren:
        parts.append(
            f"{barren:,} nodes clear every other clause and still have no hand class hero can"
            " be holding, so there is no range to publish at all."
        )
    clauses = len(DERIVATION_EXCLUSION_CODES)
    return f"{clauses} clauses can refuse a node and {len(parts)} of them do here. " + " ".join(
        parts
    )


def _kept_multiway_calls(by_path: _ByPath) -> str:
    """The committed calls that do close into a multiway pot, and what they all face."""
    kept = [node for node in _committed(by_path) if _closes_into_a_multiway_flop(by_path, node)]
    if not kept:
        return "No committed spot publishes a call that closes into a three-or-more-way flop."
    faced = {raises_faced(by_path, node) for node in kept}
    qualifier = ", every one of them facing a three-bet" if faced == {2} else ""
    return (
        f"Elsewhere in the chart {len(kept):,} committed spots do publish a call that closes"
        f" into a guaranteed three-or-more-way flop{qualifier}, and those are kept on purpose -"
        " the paragraph below says why a call to a three-bet is not a cold call."
    )


def _merge_sentences(export: SolverExport, by_path: _ByPath) -> str:
    """Decision 45's own figures: the merging spots, the cells they move, and the exemptions."""
    derivation = _derivation()
    merging = [
        node for node in _committed(by_path) if derivation.merges_the_cold_call(by_path, node)
    ]
    moved = derivation.merged_cells(export)
    whole_spots: set[tuple[int, ...]] = set()
    whole_cells = 0
    for node in merging:
        for hand_class_text in HAND_CLASSES:
            column = gtopen_class_index(hand_class_text)
            # Deliberately the same private helper `merged_cells` reads the flat with, so the
            # cells counted here are a subset of the cells counted there by construction.
            if node.reach_bp[column] > 0 and derivation._flat_bp(node, column) == (
                export.quantisation_scale
            ):
                whole_spots.add(node.path)
                whole_cells += 1
    small_blind = sum(1 for node in merging if node.actor_pos == "SB")
    posted = dict(zip(export.config["positions"], export.config["posts"], strict=True))
    return (
        f"The bot never cold-calls, so at the {len(merging):,} spots where hero faces an open"
        " with nothing in BEYOND THE BLINDS the solve's call is published as a raise rather than"
        f" as a call. {len(moved):,} cells move. Merged and not deleted: at {len(whole_spots):,}"
        f" of those {len(merging):,} spots, across {whole_cells:,} of the {len(moved):,} cells, a"
        " hand's whole weight sits on calling, and deleting would leave a hand with no answer at"
        f" all. Both figures are over the {len(merging):,} merging spots and nothing wider."
        f" {small_blind:,} of the {len(merging):,} are the SMALL BLIND, which has posted"
        f" {_number(float(posted['SB']))}: a blind is posted rather than chosen, so calling from"
        " there is still money going in behind an opener and it merges like the rest. The big"
        " blind's defence and every call to a three-bet are untouched, for the reasons"
        " `merges_the_cold_call` gives."
    )


def _realization_sentences(export: SolverExport, by_path: _ByPath) -> str:
    """The bias, priced at the one spot a reader can check against a postflop solve. Looked up
    rather than named, so a selection that stops committing the big blind's defence of a
    small-blind open loses the sentence rather than describing a spot nothing answers.
    """
    node_action_sequence = _derivation().node_action_sequence
    posted = dict(zip(export.config["positions"], export.config["posts"], strict=True))
    big_blind = float(posted["BB"])
    head = (
        "The ranges also carry a realization bias, accepted rather than corrected. GTOpen"
        " settles a flop by scaling each hand's equity share instead of playing the street out,"
        " and that scaling does not pay position what position is worth."
    )
    tail = " The ranges are shipped as solved, and no spot in this chart is priced exactly."
    for node in _committed(by_path):
        if node.actor_pos != "BB":
            continue
        faced = node_action_sequence(by_path, node)
        if len(faced) != 1 or faced[0].position != "SB" or faced[0].action != "raise":
            continue
        price = float(faced[0].size_bb)
        to_call = price - big_blind
        pot = price + big_blind
        return (
            f"{head} Facing a {_number(price)} big blind open from the small blind, the big"
            f" blind here folds {_combo_weighted_fold_pct(node):.2f} percent of its range while"
            f" closing the action in position, paying {_number(to_call)} to win {_number(pot)}"
            f" and so needing {_PERCENT * to_call / (pot + to_call):.0f} percent equity to"
            f" continue. A postflop solve defends far wider from that seat.{tail}"
        )
    return head + tail


def artifact_notes(export: SolverExport, by_path: _ByPath, census: NodeCensus) -> str:
    """The chart's `audit_fields.notes`, computed off the export and the caller's mapping - see
    `_committed` for why a fresh mapping is never built here.
    """
    committed = census.committed
    total = census.total
    decisions, excluded_decisions = _decision_shares(by_path)
    seat_count_reading = sum(1 for node in _committed(by_path) if _seats_live(by_path, node) >= 3)
    average, connectors = MULTIWAY_EQUITY_UNDERSTATEMENT
    return (
        "Derived from the GTOpen six-max 100bb rake-free solve committed at"
        f" {EXPORT_REFERENCE}. The chart commits {committed:,} of that solve's {total:,} action"
        f" nodes, and those {committed:,} carry {decisions:.2f} percent of the preflop decisions"
        f" the bot ever faces. The {total - committed:,} it excludes are"
        f" {_PERCENT * (total - committed) / total:.2f} percent of the nodes and carry the other"
        f" {excluded_decisions:.2f} percent of the decisions: a share of nodes and a share of"
        " decisions are different measurements of the same split, so each figure is stated over"
        " the set it was measured on. Every figure here but one is recomputed by the run that"
        " writes the chart, and the exception is named where it appears. Every absence is a"
        " decision, and a reader who cannot see why would read a missing range as a gap."
        "\n\n"
        f"{_exclusion_clauses(by_path, census)} {_kept_multiway_calls(by_path)}"
        "\n\n"
        "Multiway pots are priced wrong at the source, which is what the exposure rule and the"
        " seat rule are for. GTOpen values a pot with three or more players in it as the product"
        " of hero's equity against each opponent separately, which understates real three-way"
        f" equity by about {average} points and by {connectors} on the suited connectors whose"
        " whole value is playing a multiway pot. Those two are the figures nobody here"
        " recomputes: they measure the solver's equity model rather than this solve, at 4,000"
        " trials a class in phase 14's cold-call verification. A node ships only where under a"
        " tenth of its decision mass reaches such a flop, measured by walking to the leaves"
        " rather than by counting who is still live:"
        f" {seat_count_reading:,} of the {committed:,} committed spots still have three or more"
        " seats able to reach the flop, and a seat count would have refused every one of them."
        "\n\n"
        f"{_merge_sentences(export, by_path)}"
        "\n\n"
        f"{_realization_sentences(export, by_path)}"
    )


def _ladder(by_path: _ByPath) -> str:
    """What the chart will actually charge hero, counted off the solve's own action labels.

    The sentence this replaces read "every committed spot offers exactly one raise: 2.5 to open,
    7.5 to three-bet, 22.5 to four-bet". One price a spot survived the re-solve and is asserted
    elsewhere only after being counted; the single global ladder did not, three ways at once.
    Counted per tier and per menu, so a tier that splits prints two prices.
    """
    tiers: dict[int, dict[tuple[tuple[str, float], ...], int]] = {}
    for node in _committed(by_path):
        menus = tiers.setdefault(raises_faced(by_path, node), {})
        menu = _aggressive_prices(node)
        menus[menu] = menus.get(menu, 0) + 1
    lines: list[str] = []
    for faced in sorted(tiers):
        menus = tiers[faced]
        priced = tuple(
            f"{count:,} at {_listed(tuple(_price_text(kind, to) for kind, to in menu))}"
            if menu
            else f"{count:,} with no raise on the menu at all"
            for menu, count in sorted(menus.items(), key=lambda pair: (-pair[1], pair[0]))
        )
        label = _TIER_NAMES[faced] if faced < len(_TIER_NAMES) else f"Facing {faced} raises"
        lines.append(f"{label}, {sum(menus.values()):,} spots: {_listed(priced)}")
    return f"{'. '.join(lines)}."


def _jam_only(export: SolverExport, by_path: _ByPath) -> str:
    """The committed spots whose only price is hero's whole stack, and why they exist.

    Its own paragraph because a summary of a ladder drops it first and it is what a student at
    the table most needs: the chart never hands him a four-bet price here, and a reader who
    took the tier above's sized four-bet as the answer would sit waiting for one.
    """
    jam_only = [
        node
        for node in _committed(by_path)
        if (menu := _aggressive_prices(node)) and all(kind == "jam" for kind, _ in menu)
    ]
    if not jam_only:
        return "No committed spot is priced at a shove alone; every one offers a sized raise."
    seats = _listed(tuple(sorted({node.actor_pos for node in jam_only})))
    prices = sorted({_faced_price(by_path, node) for node in jam_only})
    stack = float(export.config["stack"])
    threshold = float(export.config["allin_threshold"]) * stack
    return (
        f"At {len(jam_only):,} committed spots the only price is hero's whole {_number(stack)}"
        f" big blind stack. Hero is in the {seats} there and the raise in front of him is"
        f" {_listed(tuple(_number(price) for price in prices))}: the re-raise his seat's"
        " multiplier would make lands at or above the solve's own all-in threshold of"
        f" {_number(threshold)} big blinds, and GTOpen clamps a raise that big to a shove. The"
        " solve is `add_allin: false`, so this is not an extra offer somebody switched on - it"
        " is the four-bet, priced out of existence. The answer there is fold, call or shove."
    )


def _empty_entries(
    by_path: _ByPath, prices: dict[str, dict[str, list[dict[str, float]]]]
) -> str:
    """Spots that carry a price key whose class map came out empty, and how narrow they are."""
    node_spot_key = _derivation().node_spot_key
    committed = _committed(by_path)
    empty = {key for key, spot in prices.items() if not spot}
    arriving = max(
        (
            sum(1 for reach in node.reach_bp if reach > 0)
            for node in committed
            if node_spot_key(by_path, node) in empty
        ),
        default=0,
    )
    narrow = f", at most {arriving:,} of the 169 classes arriving at any of them" if empty else ""
    return (
        "A class absent from a spot never raises there. A spot whose entry is empty offers hero"
        " a raise that no hand he can be holding there ever takes -"
        f" {len(empty):,} of the {len(committed):,}{narrow} - and is a different thing from a"
        " spot with no raise on the menu at all, which carries no key;"
        f" {len(committed) - len(prices):,} committed spots are in that second state. In every"
        " case the strategy refuses rather than inventing a price."
    )


def sizing_notes(
    export: SolverExport, by_path: _ByPath, prices: dict[str, dict[str, list[dict[str, float]]]]
) -> str:
    """The sizing table's `notes`, computed off the export, the caller's mapping and the table."""
    committed = _committed(by_path)
    menus = {len(_aggressive_prices(node)) for node in committed}
    per_class = {len(entries) for spot in prices.values() for entries in spot.values()}
    pairs = sum(len(spot) for spot in prices.values())
    weights = (
        " Every committed spot offers hero exactly one price, so every weight in this table is"
        " 1.0, and what the per-class shape carries is which classes are priced rather than how"
        " the weight is split - a per-spot entry would price the hands that only fold or call."
        if menus <= {1} and per_class <= {1}
        else " Where a spot offers two prices a class carries an entry each and its weights sum"
        " to one, so the shape carries how a class splits its aggression too."
    )
    return (
        "Every price hero may raise to at a committed spot, per hand class, with the share of"
        " that class's own aggressive volume it puts on each. Read off the solve's own action"
        " labels, and so is every count in this note, so a re-solve at different sizings"
        f" reprices the table and restates the prose with it. {pairs:,} (spot, hand class) pairs"
        f" are priced across {len(prices):,} of the {len(committed):,} committed spots.{weights}"
        " The entries stay a list per class because the multiway family returns with two-price"
        " menus once the source can value those pots."
        "\n\n"
        f"{_ladder(by_path)}"
        "\n\n"
        f"{_jam_only(export, by_path)}"
        "\n\n"
        f"{_empty_entries(by_path, prices)}"
    )
