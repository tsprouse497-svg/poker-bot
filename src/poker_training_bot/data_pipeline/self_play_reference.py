"""Which chart gaps the self-play run already surfaces, read from its own report.

Split out of `comparison.py` when that file reached its 500-line cap, but the seam is real
rather than a place to put lines. This is the one input to the comparison that is not the
committed sample; it is recovered by pattern from a rendered report rather than from a
structured file; and since 2026-09-03 it carries a matching rule of its own.

**Spots match on SHAPE, not on the key.** A shape is the key with every `@price` removed, which
is `vocabulary_measures.strip_sizes` and is imported rather than restated - a second stripper
here would be a second answer to "is this the same spot". Taylor ruled this on 2026-09-03.

On full keys the answer is always no, and structurally so rather than by accident: self-play
plays only the three prices the solved tree holds - 2.5, 7.5 and 22.5 - while the corpus plays
the prices real players used, so `SB:raise@10.5,LJ:raise@25.25` and the solved
`SB:raise@7.5,LJ:raise@22.5` are the same decision at different money and can never be the same
string. Measured against the committed sample, the column reads SEEN at 7 of the 61 gap spots
and NEW at 54. On keys it read NEW at all 61 and carried no information whatever.

Every one of the 7 is a four-bet spot, and self-play refuses every one of them on every run -
the chart commits nothing past two raises in. That is exactly the priority the inventory claims
to publish: a gap the simulator surfaces anyway is worth less to a person filling cells than a
gap only real hands reach.
"""

from __future__ import annotations

from pathlib import Path

from poker_training_bot.solver_artifacts.vocabulary_measures import strip_sizes

SELF_PLAY_INVENTORY = (
    Path(__file__).resolve().parents[3] / "reports" / "active" / "latest_refusal_inventory.txt"
)


def self_play_spots() -> frozenset[str]:
    """Spot keys the self-play run already reached, read from its committed report.

    Read rather than recomputed. The point of the cross-reference is "did the simulator already
    find this", and only the simulator's own output can answer it.

    It fails loudly when it finds nothing, and that is the important part. An empty result is
    indistinguishable from a real answer: every spot silently becomes NEW, and the phase's most
    actionable claim - that real hands find spots self-play never reaches - inverts into a claim
    that they find all of them, with a passing gate underneath it. A missing or unrecognisable
    inventory is a broken cross-reference, not an empty one.
    """
    if not SELF_PLAY_INVENTORY.is_file():
        raise FileNotFoundError(
            f"{SELF_PLAY_INVENTORY} is missing, so no spot can be marked as already found"
            " by self-play. Run generate_profile_comparison_report first"
        )
    spots = set()
    for line in SELF_PLAY_INVENTORY.read_text(encoding="utf-8").splitlines():
        # A key prints twice per spot, bare and as `<key>:` heading its hand classes.
        for token in (word.rstrip(":") for word in line.split()):
            if token.startswith("t") and token.count("/") >= 3:
                spots.add(token)
    if not spots:
        raise ValueError(
            f"{SELF_PLAY_INVENTORY} yielded no spot keys, so the self-play cross-reference"
            " would mark every real-hand spot NEW without that meaning anything."
            " The inventory's format moved and this reader has to move with it"
        )
    return frozenset(spots)


def self_play_shapes() -> frozenset[str]:
    """`self_play_spots()` with every `@price` stripped, which is what the column compares.

    Gathered once per comparison rather than per row, and called early so a missing or
    unreadable inventory raises before the replay rather than after it.
    """
    return frozenset(strip_sizes(spot) for spot in self_play_spots())
