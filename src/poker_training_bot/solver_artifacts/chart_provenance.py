"""What the committed chart says about where it came from and what it does not price.

Split out of `chart_derivation` because it is a different subject and because the pair
broke the 500-line cap: this module is prose for a human reading the chart, and the
derivation module is the rule that selects the nodes. Nothing here is a number a check
recomputes, and the two confessions are required by name - the artifact's notes state the
realization bias and the multiway defect with the excluded node count, so a reader can tell
that four missing opening ranges are a decision rather than a gap in the conversion.
"""

from __future__ import annotations

SOURCE_NAME = "GTOpen 6-max 100bb rake-free"
EXPORT_REFERENCE = "data/artifacts/preflop/exports/gtopen_six_max_100bb_rakefree.gtx.gz"
GENERATED_AT = "2026-08-27T00:00:00Z"

ARTIFACT_NOTES = (
    "Derived from the GTOpen six-max 100bb rake-free solve committed at"
    f" {EXPORT_REFERENCE}. The chart commits 86 of that solve's 38,828 action nodes and"
    " excludes 38,742 of them. Both absences are decisions, and a reader who cannot see"
    " why would read the missing opening ranges as a gap in the conversion."
    "\n\n"
    "Multiway pots are priced wrong at the source, so they are not shipped. GTOpen values"
    " a pot with three or more players in it as the product of hero's equity against each"
    " opponent separately, which understates real three-way equity by about 10.5 points"
    " and by 14 on the suited connectors whose whole value is playing a multiway pot. A"
    " node is committed only where at most one opponent has voluntarily put money in"
    " beyond the blinds and at most two players are still live, so every way a committed"
    " hand can end is heads-up. 24 nodes are already heads-up by the action in front of"
    " hero and are still excluded, because a multiway pot is reachable below them: four"
    " of the five opening ranges are among those 24, which is why the bot opens only from"
    " the small blind and refuses a first-in decision from the lojack, hijack, cutoff and"
    " button rather than open from ranges the solve mispriced."
    "\n\n"
    "The ranges also carry a realization bias, accepted rather than corrected. GTOpen"
    " settles a flop by scaling each hand's equity share instead of playing the street"
    " out, and that scaling does not pay position what position is worth. Facing a 2.5"
    " big blind open from the small blind, the big blind here folds 50.98 percent of its"
    " range while closing the action in position, paying 1.5 to win 3.5 and so needing 30"
    " percent equity to continue. A postflop solve defends far wider from that seat. The"
    " ranges are shipped as solved, and no spot in this chart is priced exactly."
)

SIZING_NOTES = (
    "Every price hero may raise to at a committed spot, per hand class, with the share of"
    " that class's own aggressive volume it puts on each. Read off the solve's own action"
    " labels, never from a constant here, so a re-solve at different sizings reprices the"
    " table by itself. The weights are a class's shares rather than a spot's: at the big"
    " blind closing against a button open the shove is 7.6 percent of the spot's"
    " aggression and runs from nothing on aces to 88.4 percent on 44, so one weight per"
    " spot would shove aces once in thirteen three-bets where the solve never shoves"
    " them. A jam is priced at hero's whole stack, because that is the price the solve"
    " offers and there is no named raise to take one from at 15 of the 86 spots. A spot"
    " absent here offers hero no raise at all - 50 of the 86 - and a class absent from a"
    " spot never raises there; in both cases the strategy refuses rather than inventing a"
    " price."
)
