"""The numbers this repo repeats across documents, and the code that recomputes them.

Stage 4 stub: `FACTS` is empty and `computed_values` returns nothing, so every test
that demands a registered fact fails. The facts land at stage 6.

A fact here is a property of committed data stated in the present tense - how many
hands the sample holds, how many of them contain an all-in. It is deliberately not a
record of a past run. "The gate was green across 33 commands" is a historical claim
about the day a phase closed, and registering it as a fact would demand rewriting
history every time the gate grows.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Fact:
    """One number, where it is quoted, and how to find it in the prose.

    `pattern` carries exactly one capture group. Searching for the bare value would
    match any number in the file; matching a sentence shape means a rewritten sentence
    stops matching, which is itself an error rather than a silent pass.
    """

    name: str
    description: str
    compute: Callable[[], str]
    pattern: str
    quoted_in: tuple[str, ...]


FACTS: tuple[Fact, ...] = ()


def computed_values() -> dict[str, str]:
    return {}
