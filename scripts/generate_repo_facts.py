"""Write the committed facts file.

The writer is deliberately separate from the checker and absent from the gate, the same
way `freeze_tests.py` is: a gate that refreshes the file it checks against is not
checking anything. The gate recomputes the values and compares; this script is what a
person runs when a number has legitimately moved.
"""

from __future__ import annotations

import yaml

try:
    from repo_paths import REPO_ROOT
except ModuleNotFoundError:
    from scripts.repo_paths import REPO_ROOT

try:
    from repo_facts import FACTS, computed_values
except ModuleNotFoundError:
    from scripts.repo_facts import FACTS, computed_values

FACTS_PATH = REPO_ROOT / "reports" / "active" / "repo_facts.yml"


def main() -> int:
    payload = {
        "schema_version": 1,
        "facts": computed_values(),
        "descriptions": {fact.name: fact.description for fact in FACTS},
    }
    FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FACTS_PATH.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    print(f"wrote {FACTS_PATH.relative_to(REPO_ROOT)} with {len(payload['facts'])} facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
