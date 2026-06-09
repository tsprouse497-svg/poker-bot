# Hand History Schema

Phase 00 defines the normalized hand-history shape without implementing replay.

Supported committed formats:

- `.json` for single-hand golden fixtures.
- `.jsonl` for multi-hand sample datasets.

Each hand record must include:

- `schema_version`
- `hand_id`
- `table`
- `players`
- `button_seat`
- `blinds`
- `streets`
- `showdown`
- `result`

The tiny examples in `data/samples/` are scaffold examples only. They are not
proof of engine correctness.
