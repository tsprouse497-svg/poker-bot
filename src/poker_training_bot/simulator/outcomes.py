"""The three ways a hand can end, named once.

Its own module so `run` and `measure` can share the vocabulary without either importing
the other. A hand ends at a showdown, uncontested, or refused, and the contract requires
that list to be exhaustive: no hand ends by exhaustion, exception, or timeout.
"""

from __future__ import annotations

SHOWDOWN = "showdown"
UNCONTESTED = "uncontested"
REFUSED = "refused"
