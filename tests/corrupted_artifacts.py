"""The two wrong-but-loadable artifacts the report command has to refuse.

Extracted from `tests/test_derived_chart_report_validators.py` on 2026-09-17, the ninth
cap-forced extraction in this repo. That file sits at the 700-line cap permanently - it was at
700 before MAINT-34 opened - and the assertion that made
`the-derived-chart-report-renders-whatever-it-is-handed` bite again would not fit.
`AGENTS.md` forbids compressing pre-existing reasoning to make room, so the builder moves out
whole and the assertions stay in the file that owns them.

This is a fixture rather than a check: it states no measurement and nothing here moves when a
solve does. The one figure it does carry, the node it invents, is read from
`test_chart_derivation.NARROWEST_REFUSED_KEY` rather than typed.
"""

from __future__ import annotations

import json
from pathlib import Path

import test_chart_derivation as derivation_tests
import test_derived_chart_report as report_tests

from poker_training_bot.solver_artifacts.importer import import_preflop_artifact
from poker_training_bot.solver_artifacts.schema import weights_checksum


def corrupted_artifact(tmp_path: Path, how: str) -> Path:
    """A committed artifact that loads cleanly and is wrong, which is the case that matters."""
    paths = sorted(report_tests.ARTIFACT_DIR.glob("*.json"))
    assert len(paths) == 1, f"expected exactly one committed preflop artifact, found {paths}"
    payload = json.loads(paths[0].read_text(encoding="utf-8"))
    source = payload["spots"][0]["spot_id"]
    if how == "drop-a-spot":
        payload["spots"] = [spot for spot in payload["spots"] if spot["spot_id"] != source]
        # Every per-spot map loses the spot too, or the importer refuses the file for its own
        # reason and no validator here is reached. The forms differ because the density rules do:
        # the first two owe an entry per declared spot, `arrival_ppb` only a subset in spot order.
        del payload["action_weights"][source]
        del payload["arriving_reach_bp"][source]
        payload["arrival_ppb"].pop(source, None)
    else:
        # The narrowest spot the exposure filter refuses - `NARROWEST_REFUSED_EXPOSURE_PCT`, which
        # this solve puts at 10.4362 against the ruled ten. Its cells are copied off a committed
        # spot, so the file stays internally consistent and only a comparison against the walk can
        # see it. Read the percentage from that constant rather than from this comment: it said
        # 10.0234 until 2026-09-17, which was the 7.5bb solve's figure.
        invented = derivation_tests.NARROWEST_REFUSED_KEY
        assert invented not in payload["action_weights"], f"{invented} is already committed"
        payload["spots"].append(
            {
                "spot_id": invented,
                "hero_position": invented.split("/")[2],
                "action_sequence": [
                    {"position": entry.position, "action": entry.action}
                    | ({} if entry.size_bb is None else {"size_bb": entry.size_bb})
                    for entry in derivation_tests.NARROWEST_REFUSED_SEQUENCE
                ],
            }
        )
        payload["action_weights"][invented] = dict(payload["action_weights"][source])
        payload["arriving_reach_bp"][invented] = dict(payload["arriving_reach_bp"][source])
    payload["audit_fields"]["spot_count"] = len(payload["spots"])
    # Restamped through the repo's own checksum, so the corruption stays a valid artifact.
    weights = tuple(
        (spot, tuple((text, tuple(acts.items())) for text, acts in sorted(cells.items())))
        for spot, cells in sorted(payload["action_weights"].items())
    )
    payload["audit_fields"]["weights_sha256"] = weights_checksum(weights)
    path = tmp_path / "corrupted.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    # If the schema rejected it the command would exit non-zero for the loader's reason.
    import_preflop_artifact(path)
    return path
