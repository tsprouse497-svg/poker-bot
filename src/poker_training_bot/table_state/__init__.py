"""What a table's own chips say about the hand, independent of any strategy.

Pure arithmetic over a table state: what each seat should hold, what a price should be,
what a depth is. Nothing here refuses anything or reads a chart. It sits outside
`strategy` so a report and a strategy can ask the same question of the same code rather
than deriving it twice and drifting apart, which is the failure this package exists to
prevent.
"""
