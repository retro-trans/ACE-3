# Mission-ending comm sequence — 0.1.53

The reported screenshot shows Jamil's name in English, with his congratulatory comm line still in Japanese. Its exact text is in a separate mission-ending table, not in the main mission table audited by 0.1.45.

## Scope

- Scene resource: `2002341`; equivalent copies: `6341`, `3200341`, `3201341`.
- All 18 live rows: text IDs 271–287 and 495 (17 timed lines and the quit prompt).
- Corpus IDs: `dialogue_11239` through `dialogue_11255`, plus `dialogue_00517`.
- The previous mission audit enumerated main scenes ending in zero and a small set of known variants. It did not enumerate this variant. A successful audit of that set must not be interpreted as coverage of every in-mission comm resource.

The translation receives a meaning review of the complete table and four following context rows. Names follow the project glossary. Baldora Charge follows the adjacent translated scene; the underlying Baldora terminology is still provisional in the glossary.

## Build and checks

Run `python tools/build_ending_dialogue_patch.py` to preview every translated row. Add `--write` to build the local English-prologue test image from 0.1.52.

The builder matches each live source row by its corpus SHA-256, translates the complete table, appends the new table, and redirects the scene header pointer. The original table and scripts remain intact. All four copies must produce identical English rows, preserve every control sequence and row ID, and fit the existing 400-unit/four-line comm budget. The longest resulting line measures 386 units; no row needs more than two lines.

The disc builder verifies every archive payload and every ISO file, retaining unrelated content from 0.1.52. The final check reopens the output disc and compares all four changed resources against the planned bytes.

This is a local test build, not a published release. In-game display and timing remain unverified. Other unclassified mission variants and battle shouts are outside this fix's coverage. Test with a fresh boot and a memory-card save; restoring an old emulator state can restore old dialogue resources.
