# Memory-card warnings and option labels — 0.1.40

Base: `ACE3-English-0.1.39.iso`. Output: `work/output/ACE3-English-0.1.40.iso`.

The checking message stored the rest of its caution on a fourth line. Reflow the four operation warnings: checking, formatting, saving and loading. They retain the operation, memory card (PS2), slot 1, power-off prohibition and insert/remove prohibition. The independent review examined all 42 active rows against the original disc; see `work/translation/en/memory_warnings_040.json`. Its four additional confirmation/error recommendations are not applied: those use narrower scrolling panels.

Requested wording in every menu copy:

| Table / text ID | Before | After |
|---|---|---|
| 3070 / 10 | Attack Demo | Combo scene |
| 3070 / 11 | Text | Comm messages |
| 3071 / 8 | Camera Control | Camera Movement |

The Combo scene on/off help also uses the new term. The three bundles are 4002050, 4002054 and 4002057.

The reportedly blank Camera Control and Target Priority labels are present in the active tables. Their previous widths are 154/152 units, near the left-row boundary; Camera Movement requires 177. Fit long left-column text to a conservative 140-unit width by adjusting only the label's horizontal scale. This also accommodates Control Scheme, Button Mapping, Restore Defaults and other long labels. Keep vertical scale, row positions, backgrounds, bindings, choices and allocations unchanged. There are 22 such scale edits across the six Game/Controls layouts. This is a scoped layout correction; the exact cause of blank runtime labels is not confirmed without an in-game check.

The operation-warning width budget is 520 native units, inside the wide caution panel: stock operation warnings use lines as wide as 553 units. In contrast, the stock confirmation/error messages use approximately 391-unit lines and up to six scrolling lines. Those remain unchanged. Only the four operation warnings are restricted to three lines here. An internal draft with overly wide confirmation reflows was rejected before delivery; its artifacts are kept outside the test-output folder.

Builder: `tools/build_options_fit_patch.py` (read-only dry run by default). Tests: `tools/test_options_fit_patch.py`. The build preserves unrelated bundle resources and all unselected strings. The existing English prologue and prior translation/alignment fixes remain inherited.

Boot fresh and load a normal memory-card save. Check the initial card warning and both Game and Controls option pages. Runtime appearance remains pending; the user controls navigation.

Final validation: four targeted finished-disc tests passed, including preservation of unselected rows/resources and all layout bytes except selected horizontal scales. Four boot-metadata tests passed. The builder verified 10,344 archive payloads and 133 disc files. Output size: 4,447,076,352 bytes. SHA-256: `08673dbe4c80cdb119b971704b2580f23d770f48581c80ad720ff92107ecd167`. Machine-readable evidence: `work/ui/options_fit_040/validation.json`.
