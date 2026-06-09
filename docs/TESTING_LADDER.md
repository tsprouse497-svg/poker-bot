# Testing Ladder

Prefer the lowest test that proves real behavior without hiding defects.

1. Static contract and schema checks.
2. Import smoke tests.
3. Unit tests with real fixtures.
4. Golden hand and replay checks.
5. CLI report generation.
6. Deterministic simulation comparisons.

Mocks are allowed only at hard external boundaries. Do not mock `poker_core`,
strategy legality validation, replay, or report generation just to pass tests.
