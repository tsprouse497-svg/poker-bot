"""What the committed chart says about where it came from and what it does not price.

Split out of `chart_derivation` because it is a different subject and because the pair
broke the 500-line cap: this module is prose for a human reading the chart, and the
derivation module is the rule that selects the nodes. Nothing here is a number a check
recomputes, and the two confessions are required by name - the artifact's notes state the
realization bias and the multiway defect with the excluded node count, so a reader can tell
that a withheld family is a decision rather than a gap in the conversion.
"""

from __future__ import annotations

SOURCE_NAME = "GTOpen 6-max 100bb rake-free"
EXPORT_REFERENCE = "data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz"
GENERATED_AT = "2026-08-27T00:00:00Z"

ARTIFACT_NOTES = (
    "Derived from the GTOpen six-max 100bb rake-free solve committed at"
    f" {EXPORT_REFERENCE}. The chart commits 249 of that solve's 33,969 action nodes, and"
    " those 249 carry 98.59 percent of the preflop decisions the bot ever faces. The"
    " 33,720 it excludes are 99.27 percent of the nodes and carry the other 1.41 percent"
    " of the decisions: a share of nodes and a share of decisions are different"
    " measurements of the same split, so each figure is stated over the set it was measured"
    " on. Every absence is a decision, and a reader who cannot see why would read a missing"
    " range as a gap in the conversion."
    "\n\n"
    "Three rules decide it. 33,362 nodes already have three raises in and are the four-bet"
    " family, which a later phase takes up. 348 more send too much of their decision mass"
    " to a flop with three or more players in it, and 10 are the big blind answering an"
    " open somebody has already called - the one committed shape whose chart would still"
    " offer hero a call into a multiway pot."
    "\n\n"
    "Multiway pots are priced wrong at the source, which is what the second and third rules"
    " are for. GTOpen values a pot with three or more players in it as the product of"
    " hero's equity against each opponent separately, which understates real three-way"
    " equity by about 10.5 points and by 14 on the suited connectors whose whole value is"
    " playing a multiway pot. A node ships only where under a tenth of its decision mass"
    " reaches such a flop, measured by walking to the leaves rather than by counting who is"
    " still live: 186 of the 249 committed spots still have three or more seats able to"
    " reach the flop, and a seat count would have refused every one of them."
    "\n\n"
    "The bot never cold-calls, so at the 20 spots where hero faces an open with nothing"
    " posted the solve's call is published as a raise rather than as a call. 165 cells"
    " move. Merged and not deleted: at 15 of those 20 spots, across 40 of the 165 cells, a"
    " hand's whole weight sits on calling, and deleting would leave a hand with no answer"
    " at all. Both figures are over the 20 merging spots and nothing wider. The big blind's"
    " defence is untouched, its blind being already paid, and so is every call to a"
    " three-bet."
    "\n\n"
    "The ranges also carry a realization bias, accepted rather than corrected. GTOpen"
    " settles a flop by scaling each hand's equity share instead of playing the street"
    " out, and that scaling does not pay position what position is worth. Facing a 2.5"
    " big blind open from the small blind, the big blind here folds 51.61 percent of its"
    " range while closing the action in position, paying 1.5 to win 3.5 and so needing 30"
    " percent equity to continue. A postflop solve defends far wider from that seat. The"
    " ranges are shipped as solved, and no spot in this chart is priced exactly."
)

SIZING_NOTES = (
    "Every price hero may raise to at a committed spot, per hand class, with the share of"
    " that class's own aggressive volume it puts on each. Read off the solve's own action"
    " labels, never from a constant here, so a re-solve at different sizings reprices the"
    " table by itself. The solve is `add_allin: false`, so hero's own shove lives only at"
    " the four-bet-facing spots this chart withholds, and every committed spot offers"
    " exactly one raise: 2.5 to open, 7.5 to three-bet, 22.5 to four-bet, keyed by what"
    " hero faces and by nothing else. Every weight in this table is therefore 1.0, and"
    " what the per-class shape carries is which classes are priced rather than how the"
    " weight is split - a per-spot entry would price the hands that only ever fold or"
    " call. The entries stay a list per class because the multiway family returns with"
    " two-price menus once the source can value those pots."
    "\n\n"
    "A class absent from a spot never raises there. A spot whose entry is empty offers hero"
    " a raise that no hand he can be holding there ever takes - 81 of the 249, all of them"
    " deep lines where hero's arriving range is a handful of classes - and is a different"
    " thing from a spot with no raise on the menu at all, which carries no key. In every"
    " case the strategy refuses rather than inventing a price."
)
