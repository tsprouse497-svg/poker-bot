"""`scripts/ask_preflop_chart.py`: the front door onto the committed ranges, held to asking.

The command's whole value is that a person can trust what it prints without reading the code,
so what is tested here is not that it runs but that it never becomes a second opinion. Nothing
below mocks the chart or the lookup. Every answer is read out of
`data/artifacts/preflop/six_max_100bb_rakefree.json` and compared with what the command
printed, so a test passes only when the printed number is the committed number.

Four properties are the reason this file exists, and each is the negative of a plausible
convenience somebody could add later.

**A refusal stays a refusal.** An uncovered spot prints `lookup`'s own reason code, never an
action, and exits non-zero. All six codes are reached from the command line, so a code that
stops being reachable - or a seventh that arrives with no plain-English line - fails here
rather than printing a blank where a cause should be.

**A substituted answer never looks like an exact one.** Ruling 8 lets a 2.3bb raise be answered
from the 2.5bb cell. The two commands are run side by side and their output is required to
differ, which is the assertion a future refactor that quietly drops the label would break.

**A mixed hand class keeps its whole distribution.** `best_action` returns None for a mix by
design, and the temptation is to print the heavier action anyway. The mixed cell asserted below
is 0.5003 call against 0.4997 raise: a command that picked a headline there would be inventing
a strategy out of six ten-thousandths.

**The order of the printed weights is the artifact's order.** Sorting them heaviest-first reads
as a recommendation, so the printed order is checked against the file's.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

import pytest
import test_preflop_lookup as lookup_tests

from poker_training_bot.solver_artifacts import lookup
from scripts.repo_paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ask_preflop_chart as ask  # noqa: E402

ARTIFACT_DIR = REPO_ROOT / "data" / "artifacts" / "preflop"
ARTIFACT_FILE = ARTIFACT_DIR / "six_max_100bb_rakefree.json"

# The three cells the assertions below are stated over, each named by what makes it useful.
PURE_SPOT = "t6/d100/BTN/CO:raise@2.5"
"""The button facing a cutoff open. `AKo` is a pure raise there, so it has a headline."""
MIXED_SPOT = "t6/d100/HJ/HJ:raise@2.5,BB:raise@7.5"
"""The hijack opened and was three-bet by the big blind. `22` is the closest cell in the
committed chart to a coin flip - 0.5003 call against 0.4997 raise - so it is the cell a
command that picks a headline for the reader would get most obviously wrong."""
SUBSTITUTED_SPOT = "t6/d100/BB/CO:raise@2.5"
"""What a 2.3bb cutoff open is answered out of. There is no 2.3bb cell anywhere."""

ANSWERED = ("--seat", "BTN", "--facing", "CO raise 2.5", "--hand", "AhKs")
REFUSED = ("--seat", "BB", "--facing", "SB raise 2.5,BB raise 7.5,SB raise 22.5", "--hand", "QQ")

# One command line per refusal code. `test_the_refusal_cases_cover_every_code_lookup_declares`
# holds this to `lookup.MISS_CODES`, so a code that becomes unreachable from a terminal - or one
# that arrives and nobody wired a way to hit - shows up as a failure rather than as a gap.
REFUSAL_CASES: dict[str, tuple[str, ...]] = {
    lookup.MISS_NO_ARTIFACT_FOR_TABLE: (
        "--seat", "CO", "--hand", "AA", "--table-size", "9", "--stack-depth", "100",
    ),
    lookup.MISS_NO_ARTIFACT_FOR_DEPTH: ("--seat", "CO", "--hand", "AA", "--stack-depth", "40"),
    lookup.MISS_POSITION_NOT_AT_TABLE: ("--seat", "UTG", "--hand", "AA"),
    lookup.MISS_UNREPRESENTABLE_SPOT: (
        "--seat", "CO", "--facing", "BTN raise 2.5", "--hand", "AA",
    ),
    lookup.MISS_SPOT_NOT_COVERED: REFUSED,
    lookup.MISS_HAND_CLASS_NOT_COVERED: (
        "--seat", "BTN", "--facing", "BTN raise 2.5,BB raise 7.5", "--hand", "72o",
    ),
}

# Each is a question the command cannot build at all, paired with the words its complaint has to
# carry. A typo reported as a gap in the solve is the failure this set exists to stop.
BAD_INPUT_CASES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("a hand class that is not one", ("--seat", "CO", "--hand", "AKx"), "169 hand classes"),
    ("the same card twice", ("--seat", "CO", "--hand", "AhAh"), "duplicate card"),
    ("three cards", ("--seat", "CO", "--hand", "AhKsQd"), "is not a hand"),
    (
        "a fold written out",
        ("--seat", "CO", "--hand", "AA", "--facing", "CO fold"),
        "must be one of",
    ),
    (
        "a raise with no size",
        ("--seat", "BB", "--hand", "AA", "--facing", "CO raise"),
        "must carry the amount",
    ),
    (
        "a size that is not a number",
        ("--seat", "BB", "--hand", "AA", "--facing", "CO raise two"),
        "not an amount in big blinds",
    ),
    (
        "a size finer than the key can hold",
        ("--seat", "BB", "--hand", "AA", "--facing", "CO raise 2.505"),
        "finer than a hundredth",
    ),
    (
        "a seat that is not a position anywhere",
        ("--seat", "BB", "--hand", "AA", "--facing", "XX raise 2.5"),
        "unknown position",
    ),
    (
        "a stray comma",
        ("--seat", "BB", "--hand", "AA", "--facing", "CO raise 2.5,,BTN call"),
        "empty entry",
    ),
)

_WEIGHT_LINE = re.compile(r"^ {4}(fold|check|call|raise) +([0-9.]+) +\(")

ACTION_WORDS = re.compile(r"\b(fold|check|call|raise)\w*", re.IGNORECASE)
"""Any word built on an action name, so `raises`, `folding` and `calls` count too.

This exists to state two things as properties rather than as the strings the code happens to
print today. An independent review got `"  If you must pick one: call."` appended to a mixed
answer past all 48 tests of an earlier draft, because that draft asserted `"Mixed" in out` and
`"One action carries weight" not in out` - the two strings, not the rule behind them.
"""


def committed_weights(spot_key: str, hand_class: str) -> dict[str, float]:
    """The cell as the committed file spells it, in the file's own order."""
    payload = json.loads(ARTIFACT_FILE.read_text(encoding="utf-8"))
    return payload["action_weights"][spot_key][hand_class]


def printed_weights(output: str) -> dict[str, float]:
    """The weights the command printed, in the order it printed them."""
    found: dict[str, float] = {}
    for line in output.splitlines():
        match = _WEIGHT_LINE.match(line)
        if match is not None:
            found[match.group(1)] = float(match.group(2))
    return found


def after_the_weight_table(output: str) -> str:
    """Everything the command printed below the last weight line, footer included.

    Deliberately not limited to the answer block. A recommendation is no less a recommendation
    for being printed under the scope note, so the property is stated over the whole tail.
    """
    lines = output.splitlines()
    weight_lines = [index for index, line in enumerate(lines) if _WEIGHT_LINE.match(line)]
    assert weight_lines, "no weight table was printed, so there is no tail to state this over"
    return "\n".join(lines[weight_lines[-1] + 1 :])


def scope_block(output: str) -> str:
    """The scope note, which `render` prints as its own blank-line-separated block."""
    blocks = [block for block in output.split("\n\n") if block.startswith("Scope")]
    assert len(blocks) == 1, "every run prints exactly one scope note"
    return blocks[0]


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = ask.main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_a_covered_spot_prints_the_artifacts_own_weights(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = run(capsys, *ANSWERED)

    assert code == ask.EXIT_ANSWERED
    assert err == ""
    assert printed_weights(out) == committed_weights(PURE_SPOT, "AKo")


def test_the_weights_print_in_the_artifacts_own_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Heaviest-first would read as a recommendation, and the chart is not making one."""
    _, out, _ = run(capsys, *ANSWERED)

    assert list(printed_weights(out)) == list(committed_weights(PURE_SPOT, "AKo"))


def test_the_derived_spot_key_is_printed(capsys: pytest.CaptureFixture[str]) -> None:
    """The only thing that shows what the typed words turned into."""
    _, out, _ = run(capsys, *ANSWERED)

    assert PURE_SPOT in out


def test_one_action_carrying_weight_gets_a_headline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    weights = committed_weights(PURE_SPOT, "AKo")
    only = [action for action, weight in weights.items() if weight > 0.0]

    _, out, _ = run(capsys, *ANSWERED)

    assert len(only) == 1
    assert f"One action carries weight here: {only[0]}." in out
    # The positive control for the mixed test below: `ACTION_WORDS` over the same tail does find
    # a named action here, so a green there is the absence of one rather than a blind regex.
    assert [found.lower() for found in ACTION_WORDS.findall(after_the_weight_table(out))] == [
        only[0]
    ]


def test_a_mixed_class_prints_its_whole_distribution(
    capsys: pytest.CaptureFixture[str],
) -> None:
    weights = committed_weights(MIXED_SPOT, "22")
    positive = [action for action, weight in weights.items() if weight > 0.0]

    code, out, _ = run(
        capsys, "--seat", "HJ", "--facing", "HJ raise 2.5,BB raise 7.5", "--hand", "2c2d"
    )

    assert code == ask.EXIT_ANSWERED
    assert len(positive) > 1
    assert printed_weights(out) == weights
    assert "Mixed" in out


def test_a_mixed_answer_names_no_action_outside_its_weight_table(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The property, not the wording: below the table, no action is named at all.

    `best_action` is None for a mix by design, and the convenience that would undo this whole
    command is a line picking one anyway - "if you must choose, call" - printed beside the
    distribution rather than instead of it. Anything of that shape names an action somewhere
    under the table, wherever in the body it is put, so that is what is asserted. The 0.5003
    against 0.4997 cell is the one where such a line would be most obviously wrong.
    """
    _, out, _ = run(
        capsys, "--seat", "HJ", "--facing", "HJ raise 2.5,BB raise 7.5", "--hand", "2c2d"
    )

    assert ACTION_WORDS.findall(after_the_weight_table(out)) == []


def test_a_refused_spot_prints_lookups_own_reason_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = run(capsys, *REFUSED)

    assert code == ask.EXIT_REFUSED
    assert err == ""
    assert lookup.MISS_SPOT_NOT_COVERED in out
    assert ask.PLAIN_ENGLISH[lookup.MISS_SPOT_NOT_COVERED] in out


def test_a_refusal_never_prints_an_action(capsys: pytest.CaptureFixture[str]) -> None:
    """No default, no nearest spot, no best guess: an uncovered spot gets no weights at all."""
    _, out, _ = run(capsys, *REFUSED)

    assert printed_weights(out) == {}
    assert "Answer" not in out


@pytest.mark.parametrize(("code_text", "argv"), sorted(REFUSAL_CASES.items()))
def test_every_reason_code_is_reachable_from_the_command_line(
    capsys: pytest.CaptureFixture[str], code_text: str, argv: tuple[str, ...]
) -> None:
    exit_code, out, _ = run(capsys, *argv)

    assert exit_code == ask.EXIT_REFUSED
    assert code_text in out
    assert ask.PLAIN_ENGLISH[code_text] in out


def test_the_refusal_cases_cover_every_code_lookup_declares() -> None:
    assert set(REFUSAL_CASES) == set(lookup.MISS_CODES)


def test_every_reason_code_has_a_plain_english_line() -> None:
    """A code with no line prints a placeholder, so this failing is the intended way to find out."""
    assert set(lookup.MISS_CODES) <= set(ask.PLAIN_ENGLISH)


def test_a_price_substitution_is_visible(capsys: pytest.CaptureFixture[str]) -> None:
    substituted = run(capsys, "--seat", "BB", "--facing", "CO raise 2.3", "--hand", "AKs")
    exact = run(capsys, "--seat", "BB", "--facing", "CO raise 2.5", "--hand", "AKs")

    assert substituted[0] == exact[0] == ask.EXIT_ANSWERED
    assert printed_weights(substituted[1]) == printed_weights(exact[1])
    assert printed_weights(exact[1]) == committed_weights(SUBSTITUTED_SPOT, "AKs")
    assert "PRICE SUBSTITUTION" in substituted[1]
    assert "2.3->2.5" in substituted[1]
    assert SUBSTITUTED_SPOT in substituted[1]
    assert "PRICE SUBSTITUTION" not in exact[1]
    assert substituted[1] != exact[1]


def test_a_refusal_also_carries_its_substitution(capsys: pytest.CaptureFixture[str]) -> None:
    """A price was moved and the spot still missed. Both facts are printed, not the second alone."""
    code, out, _ = run(
        capsys, "--seat", "BTN", "--facing", "BTN raise 2.4,BB raise 7.5", "--hand", "72o"
    )

    assert code == ask.EXIT_REFUSED
    assert "PRICE SUBSTITUTION" in out
    assert "asked at 2.4bb, answered from the 2.5bb cell" in out
    assert lookup.MISS_HAND_CLASS_NOT_COVERED in out


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("AhKs", "AKo"),
        ("AhKh", "AKs"),
        ("Ah Ks", "AKo"),
        ("Ah,Ks", "AKo"),
        ("2c2d", "22"),
        ("Td9d", "T9s"),
        ("AKs", "AKs"),
        ("ako", "AKo"),
        ("QQ", "QQ"),
        ("t9s", "T9s"),
    ],
)
def test_a_hand_is_read_from_cards_or_from_a_class(text: str, expected: str) -> None:
    assert ask.parse_hand(text) == expected


def test_cards_and_the_class_they_belong_to_ask_the_same_cell(
    capsys: pytest.CaptureFixture[str],
) -> None:
    by_cards = run(capsys, "--seat", "BTN", "--facing", "CO raise 2.5", "--hand", "AhKh")
    by_class = run(capsys, "--seat", "BTN", "--facing", "CO raise 2.5", "--hand", "AKs")

    assert printed_weights(by_cards[1]) == printed_weights(by_class[1])
    assert "AhKh -> AKs" in by_cards[1]


def test_a_spot_key_pasted_from_a_report_is_read_as_an_action(
    capsys: pytest.CaptureFixture[str],
) -> None:
    typed = run(capsys, "--seat", "BTN", "--facing", "CO raise 2.5", "--hand", "AhKs")
    pasted = run(capsys, "--seat", "BTN", "--facing", "CO:raise@2.5", "--hand", "AhKs")

    assert typed[1] == pasted[1]


@pytest.mark.parametrize(
    ("label", "argv", "expected"),
    [pytest.param(*case, id=case[0]) for case in BAD_INPUT_CASES],
)
def test_bad_input_fails_cleanly_rather_than_being_guessed_at(
    capsys: pytest.CaptureFixture[str], label: str, argv: tuple[str, ...], expected: str
) -> None:
    code, out, err = run(capsys, *argv)

    assert code == ask.EXIT_BAD_INPUT
    assert out == ""
    assert err.startswith("bad input: ")
    assert expected in err


def test_a_missing_required_flag_exits_on_the_bad_input_code() -> None:
    """argparse's own usage code and this file's bad-input code are deliberately the same."""
    with pytest.raises(SystemExit) as raised:
        ask.main(["--hand", "AA"])

    assert raised.value.code == ask.EXIT_BAD_INPUT


def test_the_table_and_depth_default_to_what_the_charts_hold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload = json.loads(ARTIFACT_FILE.read_text(encoding="utf-8"))
    library = ask.load_library(ARTIFACT_DIR)

    _, out, _ = run(capsys, "--seat", "CO", "--hand", "AA")

    assert ask.default_table_size(library) == payload["table_size"]
    assert (
        ask.default_stack_depth_bb(library, payload["table_size"]) == payload["stack_depth_bb"]
    )
    assert f"{payload['table_size']}-handed, {payload['stack_depth_bb']}bb deep" in out


def test_two_depths_leave_no_default_to_take(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two charts make a default a pick, and a pick is a question the person did not ask."""
    for depth in (100, 50):
        artifact = lookup_tests.make_artifact(stack_depth_bb=depth, name=f"Chart {depth}")
        (tmp_path / f"chart_{depth}.json").write_text(
            json.dumps(artifact.to_payload()), encoding="utf-8"
        )

    ambiguous = run(capsys, "--seat", "CO", "--hand", "AA", "--artifacts", str(tmp_path))
    named = run(
        capsys,
        "--seat", "CO", "--hand", "AA", "--artifacts", str(tmp_path), "--stack-depth", "50",
    )

    assert ambiguous[0] == ask.EXIT_BAD_INPUT
    assert "--stack-depth" in ambiguous[2]
    assert named[0] == ask.EXIT_ANSWERED
    assert "t6/d50/CO/rfi" in named[1]


def test_two_table_sizes_leave_no_default_to_take(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The twin of the depth rule, and the branch that matters when a second chart lands.

    Only one table size is committed, so this cannot be shown against the real artifacts and the
    branch sat unheld until a review replaced `default_table_size` with one silently taking the
    smallest and the whole suite stayed green.
    """
    for table_size in (6, 5):
        artifact = lookup_tests.make_artifact(
            table_size=table_size, name=f"Chart {table_size} handed"
        )
        (tmp_path / f"chart_{table_size}.json").write_text(
            json.dumps(artifact.to_payload()), encoding="utf-8"
        )

    ambiguous = run(capsys, "--seat", "CO", "--hand", "AA", "--artifacts", str(tmp_path))
    named = run(
        capsys,
        "--seat", "CO", "--hand", "AA", "--artifacts", str(tmp_path), "--table-size", "5",
    )

    assert ambiguous[0] == ask.EXIT_BAD_INPUT
    assert ambiguous[1] == ""
    assert "--table-size" in ambiguous[2]
    assert named[0] == ask.EXIT_ANSWERED
    assert "t5/d100/CO/rfi" in named[1]


def test_a_table_size_no_chart_covers_has_no_depth_to_default_to(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, out, err = run(capsys, "--seat", "CO", "--hand", "AA", "--table-size", "9")

    assert code == ask.EXIT_BAD_INPUT
    assert out == ""
    assert "--stack-depth" in err


def test_a_directory_holding_no_chart_is_bad_input(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run(capsys, "--seat", "CO", "--hand", "AA", "--artifacts", str(tmp_path))

    assert code == ask.EXIT_BAD_INPUT
    assert "no chart loaded" in err


@pytest.mark.parametrize("argv", [ANSWERED, REFUSED], ids=["answered", "refused"])
def test_every_run_names_the_boundary_of_what_it_asked(
    capsys: pytest.CaptureFixture[str], argv: tuple[str, ...]
) -> None:
    """A reader who is not told the boundary assumes a wider answer than they got."""
    _, out, _ = run(capsys, *argv)

    assert "committed preflop chart, and nothing else" in scope_block(out)


@pytest.mark.parametrize("argv", [ANSWERED, REFUSED], ids=["answered", "refused"])
def test_the_scope_note_claims_nothing_about_how_the_bot_plays(
    capsys: pytest.CaptureFixture[str], argv: tuple[str, ...]
) -> None:
    """A scope note that names an action has stopped describing scope.

    An earlier draft ended every run with "After the flop this repo still checks and folds", and
    a test asserted that string was printed. It was true at the time, hardcoded, and about a
    layer this command never loads - so the day phase 16 gives the bot a postflop bet, the test
    would have pinned the false sentence rather than caught it. Naming no action is the general
    form of not making that mistake again, and it holds whatever the next wrong sentence is.
    """
    _, out, _ = run(capsys, *argv)

    assert ACTION_WORDS.findall(scope_block(out)) == []


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (ANSWERED, ask.EXIT_ANSWERED),
        (REFUSED, ask.EXIT_REFUSED),
        (("--seat", "CO", "--hand", "AKx"), ask.EXIT_BAD_INPUT),
    ],
    ids=["answered", "refused", "bad-input"],
)
def test_the_command_exits_as_its_docstring_documents(
    argv: tuple[str, ...], expected: int
) -> None:
    """Run as a person runs it, because an exit code is what a wrapper reads."""
    finished = subprocess.run(
        [sys.executable, "scripts/ask_preflop_chart.py", *argv],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert finished.returncode == expected
