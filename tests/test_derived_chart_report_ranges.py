"""Phase 14: what the report publishes about the committed ranges themselves.

Split off `tests/test_derived_chart_report.py` at the 700-line cap. That file keeps the whole
module-scope interface - the ruled numbers, the row patterns, the section reader and the walks
over the committed keys - and this file reaches every one of them as an attribute on it, so no
count is owned twice and no constant is copied.

Owned here: the four relations, the group-order ladders, the two counterfactual arms over the ten
partitions, the equity relation, the four accepted defects, the two orderings against the raked
expectations, the big blind's defence and flat, every published band, and the menu each family
publishes with its merged flats. Each is checked as **printed**: the rules behind these figures
belong to `test_chart_derivation.py`, `test_derived_chart.py` and `test_chart_cutover_evidence.py`,
and this file never re-implements one.
"""

from __future__ import annotations

import json
import re

import pytest
import test_derived_chart_report as report


@pytest.fixture(scope="module")
def generator():
    return report.load_generator()


@pytest.fixture(scope="module")
def report_text(generator) -> str:
    return report.load_report_text(generator)


@pytest.fixture(scope="module")
def artifact():
    return report.load_artifact()


def test_the_four_relations_are_published_with_their_counts_and_gate_nothing(report_text) -> None:
    """Four relations, each measured over every cell, none gated as an order.

    Three run on play-not-fold - the pair ladder, the suited-versus-offsuit twins, and the kicker
    row ladder at 132 comparisons over a full grid. The fourth runs on the **merged raise weight
    the bot plays**, and it is the one that matters: the inversion that halted this phase sits at
    cells where both hands are played 100 percent, so play-not-fold reads nothing there at all. 25
    pair inversions are visible only on the raise action and were invisible to every relation and
    both arms.

    What is gated is that the measurement was taken over every cell and published with its worst
    case. Gating the order itself would refuse correct play, which this repo has learned twice,
    and decision 51 settles that a hand somebody finds odd is not a defect without a measurement:
    a pick among hands the solve prices alike is bluff selection, and no packet may call it noise.
    """
    body = report.section(report_text, "relations")
    rows = {
        name.strip(): (int(bad), int(over), worst)
        for name, bad, over, worst in report.RELATION_ROW.findall(body)
    }

    assert len(rows) == 4, f"the report publishes {len(rows)} relations rather than four: {rows}"
    assert "raise weight" in " ".join(rows).lower(), (
        f"no relation is measured on the raise action, which is what halted this phase: {rows}"
    )
    for name, (bad, over, worst) in rows.items():
        assert over > 0, f"{name} was measured over no comparisons at all"
        assert bad <= over, (name, bad, over)
        assert re.search(r"\d", worst), f"{name} publishes no worst case with a number: {worst!r}"
    kicker = [name for name in rows if "kicker" in name.lower()]
    assert len(kicker) == 1, f"no single kicker relation among {sorted(rows)}"
    assert rows[kicker[0]][1] % report.ROW_LADDER_COMPARISONS == 0, (
        f"the kicker relation was measured over {rows[kicker[0]][1]} comparisons, which is not a"
        f" whole number of full grids at {report.ROW_LADDER_COMPARISONS} each"
    )
    assert re.search(r"gates? nothing|not gated|measured rather than", body, re.IGNORECASE), (
        "the section does not say the relations gate nothing, so a reader cannot tell a published"
        " count from a failure"
    )
    assert "noise" not in body.lower() or "not noise" in body.lower()


def test_the_group_ladders_are_published_and_say_they_gate_nothing(report_text) -> None:
    """The family that returned a different verdict on every committed set it has been run over.

    It fails over the uncut 51, passes over 36, comes out mixed over 21 and blind over 6, so what
    it measures is set composition rather than the hand index. It is retained and printed because
    a human reads it, and it is labelled so a reader cannot mistake a published tie for a gate
    that passed.
    """
    body = report.section(report_text, "ladders")
    rows = report.LADDER_ROW.findall(body)

    assert rows, "the report publishes no group-order ladder at all"
    assert len({label.strip() for label, _, _ in rows}) == len(rows), "a ladder published twice"
    for label, solved, transposed in rows:
        assert int(solved) >= 0 and int(transposed) >= 0, (label, solved, transposed)
    assert re.search(r"gates? nothing|not gated|published only", body, re.IGNORECASE), (
        "the ladders are printed without saying they gate nothing"
    )
    assert re.search(r"set composition|different verdict", body, re.IGNORECASE), (
        "the section does not say why the ladders were retired from gating"
    )


def test_both_arms_are_published_on_every_partition_with_the_rank_arms_skipped_count(
    report_text, artifact
) -> None:
    """Ten partitions, two arms, and the rank arm's coverage published rather than assumed.

    The suit arm transposes each suited hand with its offsuit twin and scores spots; the rank arm
    reverses every rank and scores cells on the row ladder. Two arms, because a chart with every
    rank reversed - one that opens 32o and folds aces - maps pairs to pairs and twins to twins, so
    the suit arm scores it bit for bit identically to a correct chart. Neither arm passing is
    evidence the ranges are sound: both are extraction checks and cannot see over-folding, a
    mis-assigned actor, or a cross-family inversion.

    `reverse_hand_ranks` is total only on a full grid and most committed spots do not carry one,
    so the rank arm scores every spot and skips the comparisons whose partner cell is absent. What
    it skipped is published per partition **on each side**, because the two sides skip different
    comparisons and one number standing for both is how the withdrawn "149 against 69" was built.
    The skipped count is checked against the comparisons the partition could have offered, so a
    report printing a plausible number rather than a measured one has to get the arithmetic right
    as well. Below five scored spots the partition publishes rather than asserts, and the report
    says which, a partition that quietly stopped asserting being a gate that quietly stopped
    existing.
    """
    body = report.section(report_text, "arms")
    rows = {
        match[0].strip(): (
            int(match[1]), int(match[2]), int(match[3]), int(match[4]),
            int(match[5]), int(match[6]), int(match[7]), int(match[8]), match[9],
        )
        for match in report.ARM_ROW.findall(body)
    }
    walked = report.partitions(artifact)

    assert set(rows) == set(walked) == set(report.ARM_ROWS), sorted(
        set(rows) ^ set(report.ARM_ROWS)
    )
    for label, row in rows.items():
        spots, suit_solved, transposed, rank_solved, permuted = row[:5]
        scored, skipped, skipped_permuted, verdict = row[5:]
        possible = report.ROW_LADDER_COMPARISONS * spots
        assert spots == len(walked[label]), (label, spots, len(walked[label]))
        assert scored <= spots, f"{label} scored more spots than the partition holds"
        assert 0 <= skipped < possible and 0 <= skipped_permuted < possible, (
            f"{label}: {skipped} and {skipped_permuted} skipped against {possible} comparisons"
            f" its {spots} spots could have offered"
        )
        assert transposed <= spots, f"{label} flags more spots than the partition holds"
        measured = (suit_solved, transposed, rank_solved, permuted, scored, skipped,
                    skipped_permuted)
        assert measured == report.ARM_ROWS[label], label
        assert suit_solved < transposed, ("suit swap", label, suit_solved, transposed)
        expected = "asserted" if scored >= report.RANK_ARM_SPOT_FLOOR else "published"
        assert verdict == expected, (
            f"{label} scores {scored} spots and is {verdict}; below"
            f" {report.RANK_ARM_SPOT_FLOOR} the rank arm publishes rather than asserts"
        )
        if verdict == "asserted":
            assert rank_solved < permuted, ("rank reversal", label, rank_solved, permuted)

    seats = [row for label, row in rows.items() if label.startswith("hero=")]
    faced = [row for label, row in rows.items() if label.startswith("raises faced")]
    whole = rows["the committed set"]
    assert sum(row[0] for row in seats) == whole[0] == len(artifact.spots)
    assert sum(row[0] for row in faced) == whole[0]
    for column in (5, 6, 7):
        assert sum(row[column] for row in seats) == whole[column], (column, "by seat")
        assert sum(row[column] for row in faced) == whole[column], (column, "by raises faced")
    assert "THE-DISCRIMINATION-GATE-CANNOT-SEE-OVER-FOLDING-OR-A-MIS-ASSIGNED-ACTOR" in body


def test_the_equity_relation_is_published_and_labelled_as_gating_nothing(report_text) -> None:
    """Decision 42: a correct chart fails this one, so it publishes and gates nothing.

    The relation is that at a spot where hero closes the action, no class folded above 99 percent
    holds more equity against the opponent's arriving range than a class played above 99 percent.
    Measured, it fires on `A9s` folded while `87s` and `76s` are played, at six-point gaps in
    three-bet pots - which is good poker, a weak suited ace being dominated by the three-bettor's
    broadway aces where a suited connector keeps its playability. All-in equity is not the property
    that orders preflop hands.

    So the report has to say, in words a reader can act on, that firing is not by itself a defect,
    and the backlog entry stays open rather than being claimed closed by a measurement toward it.
    """
    body = report.section(report_text, "equity")
    fires = re.search(r"^\s*fires at\s+(\d+) of (\d+) spots where hero closes\s*$", body, re.M)

    assert fires is not None, "the equity relation publishes no firing count over its own domain"
    assert int(fires.group(2)) == report.HERO_CLOSES_SPOTS, (
        f"the relation is defined where hero closes the action, which decision 49 re-derives at"
        f" {report.HERO_CLOSES_SPOTS} spots over the committed set, not {fires.group(2)}"
    )
    assert int(fires.group(1)) <= int(fires.group(2))
    assert re.search(r"gates? nothing|not a check|measurement rather than a check", body, re.I)
    assert re.search(r"a correct chart (?:would )?fails? it", body, re.IGNORECASE), (
        "the section does not tell a reader that firing is not by itself a defect"
    )
    assert "GATE-ONE-RELATION-AGAINST-A-COMMITTED-EQUITY-TABLE" in body
    assert "deferred" in body.lower(), "the deferred entry is published as though it were closed"


def test_the_four_accepted_defects_are_published_as_defects_with_their_measurements(
    report_text,
) -> None:
    """Accepted defects, never caveats, each with the number the phase accepted it on.

    The wheel-ace cases are separated out because they are correct poker - `A9s` folded at 39.6
    against `A5s` played at 39.0 is the wheel-ace premium GTOpen's own fit measures - and lumping
    them in over-states what is wrong with the chart by about half. 87 of the 181 kicker
    inversions are that, 29 have no poker story at a 50-point gap and 65 below it.

    The mixed-cell share sits here because it is what makes the merged flats a real cost rather
    than a relabelling: in the solve, 93.20 percent of cells at non-zero reach put 99 percent or
    more on one action, so there was no near-indifference to fall back on when the flats were
    merged away. Both readings are published and each says which grid it is over - the merge turns
    165 mixed cells pure, so the chart this phase writes reads 93.48, and a report printing one
    figure under the other's name would be the mistake that produced two meanings for "27".
    """
    body = report.section(report_text, "defects")
    rows = dict(re.findall(r"^\s*defect\s+(.+?)\s{2,}(\S.*?)\s*$", body, re.MULTILINE))
    named = " ".join(rows).lower()

    assert len(rows) == 4, f"the report publishes {len(rows)} accepted defects, not four: {rows}"
    for token in ("big blind", "pair", "kicker", "merged"):
        assert token in named, f"no accepted defect named for {token!r}: {sorted(rows)}"
    for name, measurement in rows.items():
        assert re.search(r"\d", measurement), f"{name} is accepted without a measurement"
    assert "caveat" not in body.lower(), (
        "an accepted defect published as a caveat is the wording the packet requirements forbid"
    )

    numbers = [int(value) for value in re.findall(r"\b(\d+)\b", body)]
    for count in (
        report.PAIR_INVERSIONS,
        report.KICKER_INVERSIONS,
        report.KICKER_WHEEL_ACE,
        report.RAISE_ACTION_INVERSIONS,
        report.RAISE_ACTION_INVERSIONS_INVISIBLE,
    ):
        assert count in numbers, f"{count} is not published anywhere in the defects section"
    assert (
        report.KICKER_WHEEL_ACE + report.KICKER_NO_STORY_WIDE + report.KICKER_NO_STORY_NARROW
        == report.KICKER_INVERSIONS
    )
    assert re.search(r"wheel[- ]ace", body, re.IGNORECASE), (
        "the wheel-ace cases are not separated out, so the defect count over-states the defect"
    )
    assert str(report.MERGED_CELLS) in body
    for share in (
        report.PURE_AT_99_PCT_SOLVED,
        report.MIXED_BELOW_90_PCT_SOLVED,
        report.PURE_AT_99_PCT_PUBLISHED,
        report.MIXED_BELOW_90_PCT_PUBLISHED,
    ):
        assert f"{share}" in body, f"{share} is not published in the defects section"
    assert re.search(r"solve|before the merge", body, re.IGNORECASE), (
        "the mixed-cell shares are published without saying which grid each is measured over"
    )


def test_the_orderings_hold_and_the_chart_is_printed_against_the_expectations(report_text) -> None:
    """Two orderings that survive any rake basis and any solver, and a comparison that gates
    nothing.

    Later position opens wider among the four non-blind seats, and the big blind defends more
    against whoever opens wider - both recomputed from the report's own columns rather than read
    off a sentence claiming they hold. An ordering is not a level, though, and only the level
    catches a broken realization model, which is why the expectations comparison sits beside it.

    The expectations file is the only figure in this phase this repo did not produce, so it is
    read here rather than trusted, and it grades nothing: it is a raked NL25 reference against a
    rake-free solve, and decision 6 rules the comparison un-gated.
    """
    body = report.section(report_text, "orderings")
    rows = {
        seat: (float(opens), float(defends))
        for seat, opens, defends in re.findall(
            r"^\s*(LJ|HJ|CO|BTN|SB)\s+opens\s+(\d+\.\d+)\s+big blind defends\s+(\d+\.\d+)\s*$",
            body,
            re.MULTILINE,
        )
    }

    assert set(rows) == set(report.OPENERS), sorted(rows)
    opens = [rows[seat][0] for seat in ("LJ", "HJ", "CO", "BTN")]
    assert opens == sorted(opens), f"later position does not open wider: {opens}"
    ordered = sorted(rows, key=lambda seat: rows[seat][0])
    defence = [rows[seat][1] for seat in ordered]
    assert defence == sorted(defence), f"the big blind does not defend more against wider: {rows}"

    against = report.section(report_text, "expectations")
    printed = re.findall(
        r"^\s*(LJ|HJ|CO|BTN|SB)\s+(opens|big blind defends)\s+derived\s+(\d+\.\d+)"
        r"\s+GTO Wizard\s+(\d+\.\d+)\s*$",
        against,
        re.MULTILINE,
    )
    reference = json.loads(report.EXPECTATIONS.read_text(encoding="utf-8"))
    quoted = {
        "opens": reference["open_frequency_pct"],
        "big blind defends": reference["big_blind_defence_pct"],
    }

    assert {(seat, measure) for seat, measure, _, _ in printed} == {
        (seat, measure) for measure in quoted for seat in quoted[measure]
    }
    for seat, measure, derived, cited in printed:
        assert float(cited) == pytest.approx(quoted[measure][seat], abs=0.005), (seat, measure)
        column = rows[seat][0 if measure == "opens" else 1]
        assert float(derived) == pytest.approx(column, abs=0.05), (seat, measure)
    assert re.search(r"gated by nothing|does not gate|not a threshold", against)
    assert "rake" in against.lower(), (
        "the comparison does not say the reference is a raked game, so a reader cannot reconcile"
        " a rake-free solve reading wider than it"
    )


def test_the_big_blind_defence_and_flat_are_published_with_the_band_at_both_ends(
    report_text, artifact
) -> None:
    """The defect this phase accepts on purpose, published where it is signed off.

    **The accepted defect is the over-folding, and it is what the band prices.** Decision 34 ruled
    it in those words and is unamended: the big blind defends too tight against every opener, and
    the flat's near-invariance to who opened - a 2.81-point spread across openers whose own ranges
    span 18.74 to 54.30 - is the fingerprint it named, not a separate defect and not what the cost
    below is measured on. The cause is the fit's own realization number for facing a bet in a
    single-raised pot, taken from raked games where flatting genuinely is worse, rather than the
    cold-call branch, since hero closes the action at all five of these nodes.

    **Two things are printed here and each names its own reference, because they read opposite
    ways.** `expectations/six_max_nl25_100bb.json` is GTO Wizard 6-max 100bb NL25 **with rake**,
    and the chart defends wider than it at four of the five openers, narrower only against the
    button. That direction is asserted below and is expected rather than contradictory - a
    rake-free solve should defend wider than a raked reference. It is therefore the floor a
    rake-free solve has to clear and never evidence the level is sound; the repo commits no
    rake-free reference to read the level against at all
    (`NOTHING-READS-THE-DEFENCE-LEVEL-AGAINST-A-RAKE-FREE-REFERENCE`). Decision 48 records the
    review that compared the two without saying which reference it meant and got the direction
    claim wrong, so each row carries its own wider/narrower verdict, recomputed here from the
    row's own columns, and the section has to name the reference each verdict is against.

    **Both backlog entries are cited, so neither reading can be followed alone.** The level is
    `COMMITTED-SPOTS-NEVER-FLAT-A-RAISE`, which the contract renames onto the over-folding and
    which carries the 14-to-21-point figure; the flat is
    `BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT`. A reader given only the second never reaches the
    first.

    The cost is a band because it turns on a realization number nothing in this repo measures, so
    both ends are printed and a midpoint is forbidden - a single figure would be a measurement
    this phase did not take. The band is over all five spots of the family it names, which is the
    rule decision 48 found being broken by a band measured over a subset of it.
    """
    body = report.section(report_text, "big_blind")
    rows = {
        seat: (float(defends), float(flat), float(cited), verdict)
        for seat, defends, flat, cited, verdict in report.BIG_BLIND_ROW.findall(body)
    }
    spread = re.search(r"^\s*flat spread\s+(\d+\.\d+) points\s*$", body, re.MULTILINE)
    bands = {
        float(realization): (float(low), float(high))
        for realization, low, high in re.findall(
            r"^\s*R = (\d+\.\d+)\s+(\d+\.\d+) to (\d+\.\d+) bb per 100\s*$", body, re.MULTILINE
        )
    }
    reference = json.loads(report.EXPECTATIONS.read_text(encoding="utf-8"))["big_blind_defence_pct"]
    family = [
        spot.spot_id
        for spot in artifact.spots
        if report.hero_seat(spot.spot_id) == "BB" and report.raises_faced(spot.spot_id) == 1
    ]

    assert set(rows) == set(report.OPENERS), sorted(rows)
    assert len(family) == report.BIG_BLIND_OPEN_FACING_SPOTS, family
    assert spread is not None, "the flat's near-invariance to who opened is not published"
    for seat, (defends, flat, cited, verdict) in rows.items():
        assert cited == pytest.approx(reference[seat], abs=0.005), (
            f"{seat}'s reference is {cited}, where the expectations file says {reference[seat]}"
        )
        assert 0.0 < flat < defends <= 100.0, (seat, defends, flat)
        assert verdict == ("wider" if defends > cited else "narrower"), (seat, defends, cited)
    flats = [flat for _, flat, _, _ in rows.values()]
    assert float(spread.group(1)) == pytest.approx(max(flats) - min(flats), abs=0.05)
    wider = sorted(seat for seat, row in rows.items() if row[3] == "wider")
    assert wider == ["CO", "HJ", "LJ", "SB"], (
        "the chart's defence against the raked reference no longer reads wider at four of the five"
        f" openers and narrower only against the button, but at {wider}; this row says which"
        " reference the verdict is against and is not a reading on the accepted defect, which is"
        " the over-folding and is graded against a rake-free level the repo does not commit"
    )

    assert set(bands) == set(report.EV_BAND), f"the EV forgone is published at {sorted(bands)}"
    for realization, ends in bands.items():
        assert ends == pytest.approx(report.EV_BAND[realization], abs=0.005), realization
        assert ends[0] < ends[1], f"R = {realization} publishes a band with one end"
    assert "midpoint" not in body.lower(), "decision 34 forbids the band published as a midpoint"
    assert re.search(r"\braked\b", body), "the section does not say the reference is a raked game"
    assert re.search(r"rake-free[^.]*wider|wider[^.]*rake-free", body), (
        "the section does not say a rake-free solve should defend wider than a raked reference"
    )
    assert "six_max_nl25_100bb" in body, (
        "the section publishes wider/narrower verdicts without naming the reference file they are"
        " against, which is what lets 'wider than the reference' be read as 'does not over-fold'"
    )
    assert re.search(r"over-fold", body), (
        "the section does not name the over-folding as what the band prices, so decision 34's cost"
        " travels to the packet attached to whatever defect the heading happens to name"
    )
    assert "BIG-BLIND-FLAT-IS-NEARLY-OPENER-INVARIANT" in body
    assert "COMMITTED-SPOTS-NEVER-FLAT-A-RAISE" in body, (
        "the flat entry is cited without the level entry the band actually prices, so a reader"
        " following the section's one citation never reaches the over-folding measurement"
    )


def test_every_published_band_is_its_familys_true_extremes(report_text, artifact) -> None:
    """A band over a subset of the family it names is the failure decision 48 caught.

    Decision 34's cost band was measured over the five no-caller big-blind spots while being
    published as the big blind's, which is why the contract forbids it in terms. So every band row
    carries the size of the family it is over, that size is recomputed here from the committed
    set, and the ends are the family's true min and max rather than a summary.

    Four-bet frequencies are singled out by the contract: no band over them may be offered as
    evidence that the unfitted terminal fails to reach the output, because the family that would
    show it is the one this phase withholds.
    """
    body = report.section(report_text, "bands")
    rows = report.BAND_ROW.findall(body)
    walked = report.partitions(artifact)
    sizes = {
        "the committed set": len(artifact.spots),
        "the big blind facing an open": report.BIG_BLIND_OPEN_FACING_SPOTS,
        "the merged spots": report.MERGED_SPOTS,
        "the three-bet-facing spots": report.THREE_BET_FACING_SPOTS,
        "the first-in spots": len(walked["raises faced 0"]),
    }

    assert rows, "the report publishes no band at all"
    assert {name.strip() for name, *_ in rows} & set(sizes), (
        f"no published band names a family this file can size: {[name for name, *_ in rows]}"
    )
    for name, over, unit, low, high in rows:
        assert float(low) <= float(high), f"{name} publishes a band the wrong way round"
        assert unit, f"{name} publishes a band with no unit"
        assert int(over) > 1, f"{name} publishes a band over {over} member"
        if name.strip() in sizes:
            assert int(over) == sizes[name.strip()], (
                f"the band for {name.strip()!r} is over {over} of the family's"
                f" {sizes[name.strip()]}, which is a band over a subset of what it names"
            )
    assert "THREE-BET-SPOTS-ARE-PRICED-ON-AN-UNFITTED-TERMINAL" in body
    assert re.search(r"four-bet[^.]*not evidence|no four-bet frequency", body, re.IGNORECASE), (
        "the section does not say a four-bet frequency is not evidence about the unfitted terminal"
    )


def test_the_menu_per_family_and_each_merged_spots_defence_against_the_solve(
    report_text, artifact
) -> None:
    """Three families, three menus, and the merge shown preserving the range exactly.

    The bot never cold-calls outside the big blind, and decision 45 rules that its flats are
    merged into its raise rather than deleted: at 9 of the facing-an-open spots the solve puts a
    hand's entire weight on `call`, so printing fold would publish "fold pocket nines to an open"
    and an all-zero row would be the untouched initialisation the contract requires absent. So 20
    spots publish raise-or-fold with each cell's raise weight being the solve's raise plus its
    call, 165 cells move, and the published defence equals the solve's raise-plus-call to the
    basis point at every one of them.

    The cost is real and is stated rather than waved through: three-betting `66` commits 7.5bb and
    can face a four-bet, where the solve would have seen a cheap flop.
    """
    body = report.section(report_text, "menus")
    families = {
        name.strip(): (int(spots), menu)
        for name, spots, menu in report.MENU_ROW.findall(body)
    }
    merged = report.MERGED_ROW.findall(body)
    moved = re.search(r"^\s*cells moved\s+(\d+)\s*$", body, re.MULTILINE)
    menus = report.spot_menus(artifact)
    walked = report.partitions(artifact)

    assert len(families) == 3, f"the report publishes {len(families)} families, not three"
    by_size = {spots: menu for spots, menu in families.values()}
    assert set(by_size) == {
        report.BIG_BLIND_OPEN_FACING_SPOTS,
        report.MERGED_SPOTS,
        report.THREE_BET_FACING_SPOTS,
    }, sorted(by_size)
    merged_menu = by_size[report.MERGED_SPOTS]
    assert set(merged_menu.split("/")) == {"fold", "raise"}, merged_menu
    for size in (report.BIG_BLIND_OPEN_FACING_SPOTS, report.THREE_BET_FACING_SPOTS):
        assert set(by_size[size].split("/")) == {"fold", "call", "raise"}, by_size[size]
    assert sum(by_size) == len(walked["raises faced 1"]) + len(walked["raises faced 2"])

    assert moved is not None and int(moved.group(1)) == report.MERGED_CELLS, body
    assert len(merged) == report.MERGED_SPOTS, (
        f"{len(merged)} merged spots published, not {report.MERGED_SPOTS}"
    )
    for key, defence, raise_plus_call in merged:
        assert key in menus, f"{key} is published as merged and is not a committed spot"
        assert menus[key] == frozenset({"fold", "raise"}), (key, sorted(menus[key]))
        assert float(defence) == pytest.approx(float(raise_plus_call), abs=0.01), (
            f"{key} publishes a defence of {defence} against the solve's {raise_plus_call}; the"
            " merge has to preserve the range to the basis point"
        )
    assert "MERGED-FLATS-PLAY-DIFFERENTLY-NOT-JUST-DIFFERENTLY-LABELLED" in body
