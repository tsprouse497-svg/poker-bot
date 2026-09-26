"""Phase 21, stage 4: part 2's money and proofs - the spend ledger, the candidate ranking, and
the two determinism comparisons.

Authored from the contract before any implementation exists; see the head of
`tests/test_flop_campaign_threads.py` for how the missing modules are reached.

**No price in this file is real.** Taylor ruled that the machine types and their hourly prices
go to him before anything is rented, so every candidate below is invented and named as such. What
is pinned is the rule: a candidate that cannot hold the memory bar is never ranked, the ranking is
on cost per solved flop over the whole billed stretch, and no run starts that the cap cannot pay
for.

**The determinism checks run on committed data.** `determinism.json` is phase 16's record of two
runs on the M4 compared exactly; the re-solve check compares a re-solve's cell documents and
strategy digests against the committed sample and index. The solves themselves never run here.
"""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from poker_training_bot.solver_artifacts import postflop_solve_driver as driver
from scripts.repo_paths import REPO_ROOT

POSTFLOP_DIR = REPO_ROOT / "data" / "artifacts" / "postflop"
SAMPLE_DIR = POSTFLOP_DIR / "sample"
GIB = 1024**3


@pytest.fixture(scope="module")
def costs():
    """`solver_artifacts.postflop_campaign_costs`: the ledger and the candidate ranking."""
    import poker_training_bot.solver_artifacts.postflop_campaign_costs as module

    return module


@pytest.fixture(scope="module")
def determinism():
    """`solver_artifacts.postflop_determinism`: the re-run and re-solve comparisons."""
    import poker_training_bot.solver_artifacts.postflop_determinism as module

    return module


def owed(module, name: str):
    found = getattr(module, name, None)
    assert found is not None, (
        f"{module.__name__} must publish {name}; phase 21's contract requires it and no"
        " implementation has been written yet"
    )
    return found


def load(name: str):
    return json.loads((POSTFLOP_DIR / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# The spend ledger
# --------------------------------------------------------------------------- #


class TestEveryRentedHourIsLoggedAndTheCapHolds:
    """Criterion: every rented hour is logged with its price, the running total is printed
    beside the cap it counts against, and work halts at a cap rather than past it. Decision 6:
    a $100 trial budget covering every rented run before the campaign, the GPU trial included."""

    def test_the_benchmark_cap_is_the_ruled_hundred_dollars(self, costs) -> None:
        assert owed(costs, "BENCHMARK_CAP_USD") == 100.0

    def test_the_total_is_every_hour_times_its_price(self, costs) -> None:
        ledger = owed(costs, "SpendLedger")(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=1.5, price_per_hour_usd=2.0, what="sweep")
        ledger.record(machine="invented-cpu-b", hours=0.25, price_per_hour_usd=4.0, what="solve")

        assert ledger.total_usd == pytest.approx(4.0)
        assert ledger.remaining_usd == pytest.approx(96.0)
        assert [entry["machine"] for entry in ledger.entries] == [
            "invented-cpu-a",
            "invented-cpu-b",
        ]

    def test_the_running_total_is_printed_beside_the_cap(self, costs) -> None:
        ledger = owed(costs, "SpendLedger")(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=1.5, price_per_hour_usd=2.0, what="sweep")

        summary = ledger.summary()
        assert "$3.00" in summary and "$100.00" in summary

    def test_a_run_the_cap_cannot_pay_for_is_refused_before_it_starts(self, costs) -> None:
        ledger = owed(costs, "SpendLedger")(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=45.0, price_per_hour_usd=2.0, what="trial")

        with pytest.raises(owed(costs, "SpendCapError")):
            ledger.authorise(hours=3.0, price_per_hour_usd=4.0)

    def test_a_run_the_cap_can_pay_for_is_authorised(self, costs) -> None:
        """The positive control: a ledger that refuses everything is not a cap, it is a stop."""
        ledger = owed(costs, "SpendLedger")(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=45.0, price_per_hour_usd=2.0, what="trial")

        ledger.authorise(hours=2.0, price_per_hour_usd=4.0)

    def test_a_run_that_spends_the_cap_to_the_cent_is_authorised(self, costs) -> None:
        """Work halts at a cap rather than past it: $90 spent and a $10 run reaches $100, which
        is at the cap and not past it. $10.01 is past it."""
        ledger = owed(costs, "SpendLedger")(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=45.0, price_per_hour_usd=2.0, what="trial")

        ledger.authorise(hours=2.5, price_per_hour_usd=4.0)
        with pytest.raises(owed(costs, "SpendCapError")):
            ledger.authorise(hours=1.0, price_per_hour_usd=10.01)

    def test_the_ledger_round_trips_through_its_committed_document(self, costs) -> None:
        ledger_type = owed(costs, "SpendLedger")
        ledger = ledger_type(cap_usd=100.0)
        ledger.record(machine="invented-cpu-a", hours=1.5, price_per_hour_usd=2.0, what="sweep")

        document = json.loads(json.dumps(ledger.to_document()))
        again = ledger_type.from_document(document)

        assert again.total_usd == pytest.approx(ledger.total_usd)
        assert again.entries == ledger.entries
        assert document["cap_usd"] == 100.0
        assert document["total_usd"] == pytest.approx(3.0)


# --------------------------------------------------------------------------- #
# The candidate ranking
# --------------------------------------------------------------------------- #

FULL_STRETCH = {
    "server_start": 30.0,
    "tree_build": 60.0,
    "solve": 1_200.0,
    "harvest": 1_800.0,
    "upload": 150.0,
}
"""Seconds, invented. The five parts the contract bills: server start, tree build, solve,
harvest of every flop, turn and river decision point, and upload."""

BAR = 17_674_107_736
"""A memory bar in bytes; the small blind's line's largest planned arena in the server's unit,
from `tests/test_flop_campaign_tree.py`. The reading applied to it is the driver's business."""


def candidate(costs, name: str, gib: int, price: float, stretch=None):
    return owed(costs, "Candidate")(
        name=name,
        memory_bytes=gib * GIB,
        price_per_hour_usd=price,
        billed_seconds=dict(stretch or FULL_STRETCH),
    )


def rank(costs, candidates, *, concurrent_solves: int = 1):
    return owed(costs, "rank_candidates")(
        candidates,
        memory_bar_bytes=BAR,
        ceiling_fraction=driver.MEMORY_CEILING_FRACTION,
        concurrent_solves=concurrent_solves,
    )


class TestCandidatesAreRankedOnCostPerSolvedFlop:
    """Criteria: a candidate that cannot hold the memory bar is excluded with that reason and never
    ranked; the choice is made on cost per solved flop - the price times the billed time for one
    closed flop - and a box running more than one solve applies the bar to their sum."""

    def test_cost_per_solved_flop_is_the_price_times_the_whole_billed_stretch(self, costs) -> None:
        found = owed(costs, "cost_per_solved_flop")(candidate(costs, "invented-a", 64, 3.6))

        assert found == pytest.approx(3.6 * sum(FULL_STRETCH.values()) / 3600)

    def test_a_stretch_that_leaves_out_a_billed_part_is_refused(self, costs) -> None:
        """Pricing the solve alone is the cheapest-looking lie available: on a closed flop the
        harvest may cost more than the solve."""
        partial = {part: seconds for part, seconds in FULL_STRETCH.items() if part != "harvest"}

        with pytest.raises((ValueError, KeyError)):
            owed(costs, "cost_per_solved_flop")(candidate(costs, "invented-a", 64, 3.6, partial))

    def test_the_billed_parts_are_the_five_the_contract_names(self, costs) -> None:
        assert tuple(owed(costs, "BILLED_PARTS")) == tuple(FULL_STRETCH)

    def test_a_candidate_that_cannot_hold_the_bar_is_excluded_even_when_cheapest(
        self, costs
    ) -> None:
        """32 GiB at the 0.40 ceiling is 13.7 GB, under an arena near 17.7 GB."""
        ranking = rank(
            costs,
            [
                candidate(costs, "invented-small", 32, 0.5),
                candidate(costs, "invented-mid", 128, 3.0),
                candidate(costs, "invented-big", 256, 2.0),
            ],
        )

        assert [found.name for found in ranking.ranked] == ["invented-big", "invented-mid"]
        assert set(ranking.excluded) == {"invented-small"}
        assert "memory" in ranking.excluded["invented-small"].lower()

    def test_a_candidate_whose_ceiling_exactly_equals_the_bar_holds_it(self, costs) -> None:
        """Ruled here, deliberately: the contract excludes "a candidate that cannot hold the
        bar", and a ceiling equal to the bar holds it, so equality is admitted and only a
        ceiling below the bar excludes. 50,000,000,000 bytes at 0.40 is 20,000,000,000 exactly
        in floating point, so the comparison is at equality and not a rounding either side."""
        exact = owed(costs, "Candidate")(
            name="invented-exact",
            memory_bytes=50_000_000_000,
            price_per_hour_usd=1.0,
            billed_seconds=dict(FULL_STRETCH),
        )
        ranking = owed(costs, "rank_candidates")(
            [exact], memory_bar_bytes=20_000_000_000, ceiling_fraction=0.40
        )

        assert [found.name for found in ranking.ranked] == ["invented-exact"]
        below = owed(costs, "rank_candidates")(
            [exact], memory_bar_bytes=20_000_000_001, ceiling_fraction=0.40
        )
        assert set(below.excluded) == {"invented-exact"}

    def test_the_ranking_is_cheapest_per_solved_flop_first(self, costs) -> None:
        """A faster, dearer box can be cheaper per flop; the hourly price alone would rank it
        last."""
        slow = {**FULL_STRETCH, "solve": 4_000.0, "harvest": 4_000.0}
        ranking = rank(
            costs,
            [
                candidate(costs, "invented-cheap-slow", 128, 1.0, slow),
                candidate(costs, "invented-dear-fast", 128, 2.0),
            ],
        )

        assert [found.name for found in ranking.ranked] == [
            "invented-dear-fast",
            "invented-cheap-slow",
        ]

    def test_two_solves_at_once_apply_the_bar_to_their_sum(self, costs) -> None:
        """128 GiB at 0.40 is 55.0 GB: one 17.7 GB arena fits and so do two; 64 GiB is 27.5 GB,
        which holds one and not two."""
        machines = [
            candidate(costs, "invented-64", 64, 1.0),
            candidate(costs, "invented-128", 128, 2.0),
        ]

        assert {found.name for found in rank(costs, machines).ranked} == {
            "invented-64",
            "invented-128",
        }
        paired = rank(costs, machines, concurrent_solves=2)
        assert [found.name for found in paired.ranked] == ["invented-128"]
        assert set(paired.excluded) == {"invented-64"}


# --------------------------------------------------------------------------- #
# Determinism re-proved on the box, compared as determinism.json compares
# --------------------------------------------------------------------------- #


class TestTheBoxRerunIsComparedAsPhase16ComparedItsOwn:
    """Criterion: phase 16's four boards are solved twice on the chosen box and compared as
    `determinism.json` compares them. Whether the box also matches the M4's committed digests is
    printed as a separate finding and is not a pass condition."""

    def test_phase_16_s_own_record_reads_as_identical(self, determinism) -> None:
        assert owed(determinism, "rerun_verdict")(load("determinism.json")) is True

    def test_one_digest_that_differs_between_the_runs_fails(self, determinism) -> None:
        """The top-level `identical` flag is left true, so a verdict that reads the flag instead
        of the cells passes this and is wrong."""
        document = copy.deepcopy(load("determinism.json"))
        document["cells"][2]["strategy_digest"][1] = "0" * 64

        assert owed(determinism, "rerun_verdict")(document) is False

    def test_one_iteration_count_that_differs_between_the_runs_fails(self, determinism) -> None:
        document = copy.deepcopy(load("determinism.json"))
        document["cells"][0]["iterations"][1] += 20

        assert owed(determinism, "rerun_verdict")(document) is False

    def test_a_second_run_that_is_a_copy_of_the_first_is_refused(self, determinism) -> None:
        """`determinism.json`'s own rule: "a second tree whose wall clock matched the first to the
        microsecond is refused rather than compared", because that is one run compared with
        itself. Only a microsecond tie is pinned here; two honest runs on a quiet box can land
        on the same tenth of a second, and phase 16's record rounds to tenths."""
        document = copy.deepcopy(load("determinism.json"))
        document["cells"][1]["wall_seconds"] = [1677.388112, 1677.388112]

        with pytest.raises(ValueError):
            owed(determinism, "rerun_verdict")(document)

    def test_two_runs_a_microsecond_apart_are_compared_not_refused(self, determinism) -> None:
        document = copy.deepcopy(load("determinism.json"))
        document["cells"][1]["wall_seconds"] = [1677.388112, 1677.388113]

        assert owed(determinism, "rerun_verdict")(document) is True

    def test_the_m4_record_matches_the_committed_index(self, determinism) -> None:
        assert owed(determinism, "matches_committed")(load("determinism.json"), load("index.json"))

    def test_a_box_that_repeats_itself_but_differs_from_the_m4_still_passes(
        self, determinism
    ) -> None:
        """Both runs on the box agree with each other and not with the M4: determinism holds on
        the box, and the M4 match is the separate finding."""
        document = copy.deepcopy(load("determinism.json"))
        document["cells"][0]["strategy_digest"] = ["e" * 64, "e" * 64]

        assert owed(determinism, "rerun_verdict")(document) is True
        assert owed(determinism, "matches_committed")(document, load("index.json")) is False


# --------------------------------------------------------------------------- #
# The Mac re-solve reproduces phase 16's cells byte for byte
# --------------------------------------------------------------------------- #

SAMPLE_CELLS = (
    "monotone-connected-cbet",
    "rainbow-dry-high-donk",
    "rainbow-dry-high-facing-a-bet",
    "two-tone-paired-donk",
)


def committed_resolve():
    """What a re-solve that reproduced phase 16 exactly would hand back: the four cell documents
    git holds, and the strategy digest of every one of the five indexed spots - the fifth,
    `Ac8c3c`, is indexed but its cell document is not in git, so its digest is all there is."""
    cells = {name: (SAMPLE_DIR / f"{name}.json").read_bytes() for name in SAMPLE_CELLS}
    digests = {
        entry["spot_key"]: entry["strategy_digest"] for entry in load("index.json")["entries"]
    }
    return cells, digests


class TestTheMacResolveMustReproduceTheCommittedCells:
    """Criterion: phase 16's four boards re-solved on the M4 at the fastest count reproduce the
    four committed cell documents byte for byte and the fifth cell's strategy digest. If they do
    not, the phase halts and Taylor is asked; no tolerance is set."""

    def test_an_exact_reproduction_passes(self, determinism) -> None:
        cells, digests = committed_resolve()

        assert owed(determinism, "reproduction_errors")(cells, digests) == []

    def test_one_changed_byte_in_one_cell_fails_and_names_the_cell(self, determinism) -> None:
        cells, digests = committed_resolve()
        cells["two-tone-paired-donk"] = cells["two-tone-paired-donk"].replace(b"0.", b"1.", 1)

        errors = owed(determinism, "reproduction_errors")(cells, digests)
        assert errors and any("two-tone-paired-donk" in error for error in errors)

    def test_a_changed_digest_for_the_unheld_fifth_cell_fails(self, determinism) -> None:
        cells, digests = committed_resolve()
        key = next(key for key in digests if "/b:Ac8c3c/" in key)
        digests[key] = hashlib.sha256(b"a different strategy").hexdigest()

        errors = owed(determinism, "reproduction_errors")(cells, digests)
        assert errors and any("Ac8c3c" in error for error in errors)

    def test_a_resolve_missing_a_committed_cell_fails(self, determinism) -> None:
        cells, digests = committed_resolve()
        del cells["monotone-connected-cbet"]

        assert owed(determinism, "reproduction_errors")(cells, digests)

    def test_a_resolve_missing_the_fifth_digest_fails(self, determinism) -> None:
        cells, digests = committed_resolve()
        del digests[next(key for key in digests if "/b:Ac8c3c/" in key)]

        assert owed(determinism, "reproduction_errors")(cells, digests)
