# solver_artifacts

Committed preflop chart artifacts, strict offline import, and fail-closed lookup.

- `hand_classes.py`: canonical 169-class hand notation.
- `schema.py`: the artifact format and the derived spot key.
- `importer.py`: strict import; every rejection carries a reason code.
- `lookup.py`: chart queries answered with a hit or an explicit miss code.

The format is documented in `docs/PREFLOP_ARTIFACT_CONTRACT.md`.
Committed charts live in `data/artifacts/preflop/`.
