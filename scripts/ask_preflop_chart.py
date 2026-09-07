"""Ask the committed preflop chart one question from a terminal, and print what it says.

Every other caller of `solver_artifacts.lookup` in this repo is a report generator: it sweeps
the whole chart and publishes a file. So the only way to find out what the bot does with one
hand in one spot was to write a throwaway script, and a throwaway script is where a wrong
answer comes from - it gets written once, believed, and never reviewed. This is that question
with a front door on it.

**It asks and it prints. It never decides.** The chart is the whole answer and this file adds
nothing to it: no default action when a spot is uncovered, no nearest spot, no invented price,
no tie broken, and no headline action picked out of a mixed hand class for the reader's
convenience. Every one of those would be strategy, and strategy living in a convenience script
is strategy nobody reviews. When `lookup` returns a `ChartMiss`, this prints the refusal.

**A refusal prints `lookup`'s own reason code as well as a plain-English line.** Replacing the
code with friendlier wording is how a cause gets lost: the code is what a person greps for,
what the reports count, and what names the cell somebody would have to fill. Both, always. A
code with no plain-English line here prints as itself and says the line is missing, because a
guess at what a new code means would read exactly like a fact.

**A price substitution is shouted, not whispered.** Ruling 8 lets the library answer a 2.3bb
raise out of the 2.5bb cell, and the answer carries the substitution. A substituted answer that
printed identically to an exact one is the defect this command exists to avoid, so it is
labelled above the weights rather than left in a footnote.

**Preflop only, and every run says so.** A reader who is not told the boundary assumes a wider
answer than they got, so the footer names what was asked. It says nothing about how the bot
plays after the flop: that is a different layer, this file never loads it, and a sentence about
it here would be a claim nothing can check - true on the day it was typed and silently false
afterwards, with a test holding it in place.

Nothing here is hand-typed that the loaded artifacts could say instead. The table size and the
stack depth default to what the charts on disk actually cover, so committing a second chart
changes the defaults with no edit here, and an ambiguous default - in either the table size or
the depth - is a question to the person rather than a pick.

Exit codes, because a person pipes this and a script wraps it:

- `0` answered: the chart holds the cell, and its weights are printed.
- `1` refused: the chart has no answer, and the reason code says which kind of gap it is.
- `2` bad input: the question could not be built at all - an unparseable hand, an action
  sequence that is not one, a chart directory that will not load. `2` is argparse's own code
  for a usage error, so its refusals and this file's land in the same bucket with no
  interception and no second convention to remember.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "src"))

from poker_training_bot.solver_artifacts.hand_classes import (  # noqa: E402
    hand_class as canonical_hand_class,
)
from poker_training_bot.solver_artifacts.hand_classes import (  # noqa: E402
    is_hand_class,
)
from poker_training_bot.solver_artifacts.importer import ArtifactImportError  # noqa: E402
from poker_training_bot.solver_artifacts.lookup import (  # noqa: E402
    MISS_HAND_CLASS_NOT_COVERED,
    MISS_NO_ARTIFACT_FOR_DEPTH,
    MISS_NO_ARTIFACT_FOR_TABLE,
    MISS_POSITION_NOT_AT_TABLE,
    MISS_SPOT_NOT_COVERED,
    MISS_UNREPRESENTABLE_SPOT,
    ChartHit,
    ChartLibraryError,
    ChartMiss,
    ChartQuery,
    PreflopChartLibrary,
)
from poker_training_bot.solver_artifacts.price_normalisation import (  # noqa: E402
    PriceSubstitutions,
)
from poker_training_bot.solver_artifacts.schema import (  # noqa: E402
    PreflopAction,
    render_entry,
    render_size_bb,
)

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"

EXIT_ANSWERED = 0
EXIT_REFUSED = 1
EXIT_BAD_INPUT = 2

# One line per refusal code, printed *beside* the code and never instead of it. Written for
# somebody who does not read the source: each says which kind of gap it is, because "the chart
# cannot answer" is the same sentence for all six and tells a person nothing about what would
# have to change. `check_every_reason_code_has_a_plain_english_line` in the tests fails when
# `lookup` grows a code this mapping has not been taught, so the fallback below is a safety net
# for a stale checkout rather than the way a new code is meant to arrive.
PLAIN_ENGLISH: dict[str, str] = {
    MISS_NO_ARTIFACT_FOR_TABLE: (
        "no committed chart covers a table with this many seats at all"
    ),
    MISS_NO_ARTIFACT_FOR_DEPTH: (
        "a chart covers this table size, but nothing covers it at this stack depth"
    ),
    MISS_POSITION_NOT_AT_TABLE: (
        "a seat named here does not exist at a table this size, so no such hand can be dealt"
    ),
    MISS_UNREPRESENTABLE_SPOT: (
        "no legal preflop order produces this action, so hero is not the player to act in it"
    ),
    MISS_SPOT_NOT_COVERED: (
        "this is a real spot and no committed chart holds it; the cell has never been solved"
    ),
    MISS_HAND_CLASS_NOT_COVERED: (
        "the chart holds this spot but says nothing about this hand in it"
    ),
}

EXAMPLES = """\
examples:
  ask what the button does with ace-king against a cutoff open
    --seat BTN --facing "CO raise 2.5" --hand AhKs

  ask what the big blind does with queens facing a four-bet
    --seat BB --facing "SB raise 2.5,BB raise 7.5,SB raise 22.5" --hand QQ

  ask what the lojack opens with when the pot is folded to it
    --seat LJ --hand 72o

--facing is one entry per seat that acted, in order, separated by commas. An entry is a
position, an action, and - for a raise - the amount it raised *to* in big blinds: "CO raise 2.5"
or "BTN call". Folds are never written; a seat that folded is simply absent, and an empty
--facing means the pot was folded to hero. A spot key pasted from a report works too, so
"CO:raise@2.5" is read the same as "CO raise 2.5".

--hand takes two real cards (AhKs, "Ah Ks") or one of the 169 classes (AKs, AKo, QQ).\
"""


class AskInputError(ValueError):
    """A question this command could not build, as opposed to one the chart would not answer.

    Kept apart from a `ChartMiss` on purpose and given its own exit code. "The chart has no
    cell for this spot" is a fact about the committed ranges that a person may want to act on;
    "AKx is not a hand" is a typo. Reporting them the same way would let a typo read as a gap
    in the solve.
    """


def _field(label: str, value: object) -> str:
    return f"  {label:<14}{value}"


def parse_size_bb(text: str) -> float:
    """Read a raise-to amount in big blinds, tolerating a trailing `bb`.

    Nothing else is tolerated. A size finer than a hundredth of a big blind is rejected by
    `PreflopAction`, not rounded here, because rounding it would move the question into a
    neighbouring cell without saying so.
    """
    cleaned = text.strip().lower()
    if cleaned.endswith("bb"):
        cleaned = cleaned[:-2].strip()
    try:
        return float(cleaned)
    except ValueError:
        raise AskInputError(
            f"{text!r} is not an amount in big blinds; a raise is written as the amount it"
            ' raised *to*, such as "CO raise 2.5"'
        ) from None


def parse_facing(text: str) -> tuple[PreflopAction, ...]:
    """Read `--facing` into the action sequence the chart is keyed by.

    An empty string is the folded-to-hero spot rather than a missing argument, which is why
    it is a default rather than something the person has to spell. An empty *entry* - a stray
    comma - is an error instead: the two look alike in a shell and reading one as the other
    would answer a different question from the one that was asked.
    """
    stripped = text.strip()
    if not stripped:
        return ()
    entries: list[PreflopAction] = []
    for chunk in stripped.split(","):
        tokens = chunk.replace(":", " ").replace("@", " ").split()
        if not tokens:
            raise AskInputError(
                f"--facing {text!r} has an empty entry; entries are separated by commas and"
                ' each is a position, an action, and a size for a raise: "CO raise 2.5,BTN call"'
            )
        if len(tokens) < 2 or len(tokens) > 3:
            raise AskInputError(
                f"{chunk.strip()!r} is not an action; write a position, an action, and - for a"
                ' raise - the amount it raised to: "CO raise 2.5" or "BTN call"'
            )
        size_bb = parse_size_bb(tokens[2]) if len(tokens) == 3 else None
        try:
            entries.append(PreflopAction(tokens[0].upper(), tokens[1].lower(), size_bb))
        except ValueError as error:
            raise AskInputError(f"{chunk.strip()!r} is not an action: {error}") from None
    return tuple(entries)


def _class_from_cards(cards: Sequence[str]) -> str:
    try:
        return canonical_hand_class(cards)
    except ValueError as error:
        raise AskInputError(f"{' '.join(cards)!r} is not two cards: {error}") from None


def parse_hand(text: str) -> str:
    """Read `--hand` as either two real cards or one of the 169 classes.

    The two forms cannot collide: a class is two or three characters and a pair of cards is
    four, so nothing has to be guessed at. Suits are read where they are given and dropped
    where they are not, because the chart is keyed by class - `AhKs` and `AsKs` are different
    hands and the same cell only when the second is suited, which is what `hand_class` decides
    rather than this file.
    """
    cleaned = text.strip().replace(",", " ")
    parts = cleaned.split()
    if len(parts) == 2:
        return _class_from_cards(parts)
    if len(parts) != 1 or not parts[0]:
        raise AskInputError(
            f"--hand {text!r} is not a hand; write two cards (AhKs) or a class (AKs, AKo, QQ)"
        )
    token = parts[0]
    if len(token) == 4:
        return _class_from_cards((token[:2], token[2:]))
    if len(token) in (2, 3):
        label = token[0].upper() + token[1].upper() + token[2:].lower()
        if not is_hand_class(label):
            raise AskInputError(
                f"{token!r} is not one of the 169 hand classes; the higher card comes first and"
                " the suffix is s or o, as in AKs, AKo, QQ"
            )
        return label
    raise AskInputError(
        f"--hand {text!r} is not a hand; write two cards (AhKs) or a class (AKs, AKo, QQ)"
    )


def load_library(directory: Path) -> PreflopChartLibrary:
    """Import every committed chart under `directory`, or say why nothing loaded.

    Import is all-or-nothing upstream, so there is no half-loaded library to answer out of and
    nothing here has to decide whether a partial load is good enough.
    """
    try:
        return PreflopChartLibrary.from_directory(directory)
    except (ArtifactImportError, ChartLibraryError) as error:
        raise AskInputError(f"no chart loaded from {directory}: {error}") from None


def default_table_size(library: PreflopChartLibrary) -> int:
    """The table size the loaded charts cover, when they cover exactly one.

    Two would make a default a pick, and a pick is this command answering a question the person
    did not ask. It says which sizes it found and stops.
    """
    sizes = sorted({artifact.table_size for artifact in library.artifacts})
    if len(sizes) != 1:
        raise AskInputError(
            f"the loaded charts cover table sizes {sizes}, so there is no single default;"
            " say which with --table-size"
        )
    return sizes[0]


def default_stack_depth_bb(library: PreflopChartLibrary, table_size: int) -> int:
    """The stack depth the loaded charts cover at `table_size`, when they cover exactly one.

    A table size nothing covers has no depth to default to. That is not the same fact as the
    chart refusing the spot, and it is reported as a question this command could not build so
    that the person passes `--stack-depth` and gets the chart's own refusal instead of this
    file's paraphrase of one.
    """
    depths = sorted(
        {
            artifact.stack_depth_bb
            for artifact in library.artifacts
            if artifact.table_size == table_size
        }
    )
    if not depths:
        raise AskInputError(
            f"no loaded chart covers a {table_size}-handed table, so there is no default stack"
            " depth; pass --stack-depth to ask anyway and the chart will say why it cannot"
            " answer"
        )
    if len(depths) != 1:
        raise AskInputError(
            f"the loaded {table_size}-handed charts cover depths {depths}bb, so there is no"
            " single default; say which with --stack-depth"
        )
    return depths[0]


def question_lines(query: ChartQuery, hand_text: str) -> list[str]:
    """What was asked, including the key the query derived from it.

    The key is printed because it is the only thing that shows what the words turned into: a
    person who typed the wrong seat sees `t6/d100/SB/...` and knows immediately, where a wrong
    answer to a nearby question looks exactly like a right one.
    """
    facing = ", ".join(render_entry(entry) for entry in query.action_sequence)
    return [
        "Question",
        _field("table", f"{query.table_size}-handed, {query.stack_depth_bb}bb deep"),
        _field("hero", query.hero_position),
        _field("facing", facing or "nothing - the pot is folded to hero"),
        _field("hand", f"{hand_text} -> {query.hand_class}"),
        _field(
            "spot key",
            query.spot_key or "none - no legal preflop order produces this sequence",
        ),
    ]


def substitution_lines(
    query: ChartQuery, substitutions: PriceSubstitutions, *, detail: tuple[tuple[str, str], ...]
) -> list[str]:
    """The prices that were moved, above the answer rather than under it.

    Ruling 8 is the one abstraction the lookup has, and it is only safe while it stays visible:
    an answer read off the 2.5bb cell is a real answer to a question about 2.5bb and an
    approximate one to a question about 2.3bb. The `price_substitution_N` pairs are printed in
    the exact spelling the audit reports use, so a line here can be matched to a line there.
    """
    if not substitutions:
        return []
    # Worded to fit a refusal as well as an answer: a price can be moved and the spot miss
    # anyway, and "this answer is not exact" would be a sentence about an answer that is not
    # there. The label appears on both, because the question that was answered is not quite
    # the question that was asked either way.
    lines = ["PRICE SUBSTITUTION - the price asked is not the price answered"]
    for index, asked, answered in substitutions:
        position = query.action_sequence[index].position
        lines.append(
            _field(
                f"entry {index}",
                f"{position} raise asked at {render_size_bb(asked)}bb, answered from the"
                f" {render_size_bb(answered)}bb cell",
            )
        )
    if detail:
        reported = ", ".join(f"{name} = {value}" for name, value in detail)
        lines.append(_field("as reported", reported))
    lines.extend(
        [
            "  The chart holds no cell at the price asked, so the nearest price it does hold"
            " answered",
            "  instead. That is allowed for prices and for nothing else: no nearer seat, no"
            " nearer",
            "  depth, no nearer hand, no nearer action.",
        ]
    )
    return lines


def answer_lines(hit: ChartHit, asked_key: str | None) -> list[str]:
    """The chart's weights, in the chart's own order, with no action chosen for the reader.

    A headline is printed only when exactly one action carries weight, which is `best_action`'s
    own rule rather than a second one stated here. A mixed class prints its whole distribution
    and says it is mixed: naming one action of two would be this command playing the hand.
    """
    lines = [
        "Answer - the chart's own weights, unchanged and in its own order",
        _field("artifact", hit.artifact_id),
    ]
    if asked_key is not None and hit.spot_key != asked_key:
        lines.append(_field("answered at", hit.spot_key))
    name_width = max(len(action) for action, _ in hit.action_weights)
    weight_width = max(len(str(weight)) for _, weight in hit.action_weights)
    lines.append("")
    for action, weight in hit.action_weights:
        # The chart's own number first and a percentage of it second. The percentage is
        # rounded and the weight beside it is not, so a hand played one time in ten thousand
        # cannot read as one never played at all.
        lines.append(
            f"    {action:<{name_width}}   {str(weight):>{weight_width}}"
            f"   ({weight * 100:.2f}% of this hand)"
        )
    lines.append("")
    headline = hit.best_action
    if headline is not None:
        lines.append(f"  One action carries weight here: {headline}.")
    else:
        lines.extend(
            [
                "  Mixed: more than one action carries weight, so the chart has no single action",
                "  for this hand here. The weights above are the whole of the answer.",
            ]
        )
    return lines


def refusal_lines(miss: ChartMiss) -> list[str]:
    """The refusal, carrying `lookup`'s code and a plain-English line, never one without other."""
    plain = PLAIN_ENGLISH.get(miss.code)
    if plain is None:
        plain = (
            "there is no plain-English line for this code in scripts/ask_preflop_chart.py;"
            " read the detail below rather than trusting a guess at what it means"
        )
    lines = [
        "No answer - the chart refuses rather than guessing",
        _field("reason code", miss.code),
        _field("in English", plain),
        _field("detail", miss.detail),
    ]
    if miss.spot_key is not None:
        lines.append(_field("spot asked", miss.spot_key))
    return lines


def scope_lines() -> list[str]:
    """The boundary of the question, and nothing about a layer this command cannot see.

    An earlier draft ended by saying what the bot does after the flop. It was true when it was
    written, it was hardcoded, and a test pinned it - so on the day it stopped being true the
    test would have held the false sentence in place instead of catching it. A scope note that
    names an action is making a claim about play rather than about scope, which is why the test
    beside this one asserts that no action is named here at all.
    """
    return [
        "Scope",
        "  Asked: the committed preflop chart, and nothing else - which action one hand takes at",
        "  one preflop spot, at the weights the chart itself holds.",
        "  Not asked: any street after the preflop one, and the amount hero puts in. Sizes are a",
        "  separate table and a separate question.",
    ]


def render(query: ChartQuery, hand_text: str, result: ChartHit | ChartMiss) -> tuple[str, int]:
    """The whole printed answer, and the exit code that goes with it."""
    blocks = [question_lines(query, hand_text)]
    if isinstance(result, ChartHit):
        blocks.append(
            substitution_lines(
                query, result.price_substitutions, detail=result.substitution_detail()
            )
        )
        blocks.append(answer_lines(result, query.spot_key))
        code = EXIT_ANSWERED
    else:
        blocks.append(substitution_lines(query, result.price_substitutions, detail=()))
        blocks.append(refusal_lines(result))
        code = EXIT_REFUSED
    blocks.append(scope_lines())
    return "\n\n".join("\n".join(block) for block in blocks if block) + "\n", code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ask_preflop_chart",
        description="Ask the committed preflop chart what it does with one hand in one spot.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--seat", required=True, help="hero's position, such as BTN, CO or BB")
    parser.add_argument(
        "--facing",
        default="",
        help='the action in front of hero, such as "CO raise 2.5,BTN call".'
        " Empty, the default, means the pot was folded to hero",
    )
    parser.add_argument(
        "--hand", required=True, help="two cards (AhKs) or a class (AKs, AKo, QQ)"
    )
    parser.add_argument(
        "--table-size",
        type=int,
        default=None,
        metavar="SEATS",
        help="seats at the table; defaults to the size the loaded charts cover",
    )
    parser.add_argument(
        "--stack-depth",
        type=int,
        default=None,
        metavar="BB",
        help="stack depth in big blinds; defaults to the depth the loaded charts cover",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=ARTIFACT_DIR,
        # Shown relative to the repo, so `--help` reads the same on every machine, and derived
        # rather than typed so it cannot drift from the directory actually loaded.
        help="directory of committed chart artifacts to ask"
        f" (default: {ARTIFACT_DIR.relative_to(REPO_ROOT)})",
    )
    return parser


def ask(arguments: argparse.Namespace) -> tuple[str, int]:
    """Build the question, ask it once, and render the answer.

    The seat is upper-cased and otherwise passed straight through. Checking it against the
    table here would duplicate `lookup`'s own `position-not-at-table` refusal in a second
    place, and the two could then disagree about what a table holds.
    """
    hand_class_text = parse_hand(arguments.hand)
    action_sequence = parse_facing(arguments.facing)
    library = load_library(arguments.artifacts)
    table_size = (
        arguments.table_size if arguments.table_size is not None else default_table_size(library)
    )
    stack_depth_bb = (
        arguments.stack_depth
        if arguments.stack_depth is not None
        else default_stack_depth_bb(library, table_size)
    )
    try:
        query = ChartQuery(
            table_size=table_size,
            stack_depth_bb=stack_depth_bb,
            hero_position=arguments.seat.strip().upper(),
            action_sequence=action_sequence,
            hand_class=hand_class_text,
        )
    except ValueError as error:
        raise AskInputError(str(error)) from None
    return render(query, arguments.hand.strip(), library.lookup(query))


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        text, code = ask(arguments)
    except AskInputError as error:
        print(f"bad input: {error}", file=sys.stderr)
        return EXIT_BAD_INPUT
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
