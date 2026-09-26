# Communication-window overflow — 0.1.39

Base: `work/output/ACE3-English-0.1.38.iso`. Output: `work/output/ACE3-English-0.1.39.iso`.

## Cause

The two screenshots show dialogue IDs `dialogue_00823` and `dialogue_00833` (Mission 02 scene 2002020, text IDs 521 and 531). Their active English strings contain `<book(10)>Londo Bell<endbook()>` on a fourth body line. The bottom communication window visibly accommodates only three body lines before its footer. The glossary entry is correctly linked; the linked words were hidden below the visible text area. The encyclopedia pane's downward arrow indicates scrolling and is unrelated to the missing dialogue line.

The older mission wrapper used a four-line limit for both top HUD chatter (`<op()>`) and bottom communication dialogue (`<on()>`). This patch treats them separately. Future communication-window additions must use **at most three body lines, each at most 460 native font units**, retaining complete book/color spans. Do not remove links to conceal text overflow.

## Changes

- Audit all 3,411 active `<on()>` dialogue rows in mission scene resources. Fix all 114 four-line entries in every corresponding scene copy: 99 require only different line breaks, and 15 have independently reviewed wording reductions with the full original meaning retained.
- Preserve every control command in order, glossary link ID and linked label, speaker/timing command, and unselected row. Append updated tables and redirect only the existing table pointer; preserve all original scene bytes outside that pointer.
- Change the recruitment notice template from `Can add: %s` to **`Purchasable: %s`** in all three menu copies. Check expansion against all 103 runtime roster entries for width, record size and the shared dialog's capacity. Keep the unit names and formatting placeholder unchanged.
- Inherit the English prologue, 0.1.37 pause alignment and 0.1.38 translations. No game navigation or release upload.

Meaning review: `work/translation/en/dialogue_fit_039.json`. Complete English change inventory: `work/translation/en/communication_reflow_039.json`. Screenshots and regions: `work/ui/communication_fit_039/`.

## Validation and user check

`tools/build_communication_fit_patch.py` defaults to a read-only dry run. It checks all eight gameplay font variants, unchanged command/link sequences, matching scene copies, untouched script bytes, notice expansion and full archive/disc payloads. `tools/test_communication_fit_patch.py` tests the actual Ruri regression, every finished-disc communication row, all modified scene copies, and the Purchasable templates.

Boot the ISO fresh and load a normal memory-card save. Revisit the Mission 02 orders for Isamu and Barrel; both should display Londo Bell without a fourth line. Check the subsequent Intermission notice for Purchasable. Runtime verification remains with the user.

Completed validation: all four targeted tests and four boot-metadata regression tests pass. All 3,411 audited communication rows on the finished disc have at most three body lines. The 456 changed instances preserve commands and links; the 114 distinct edits preserve highlighted names exactly. All 10,344 archive payloads and 133 disc files verified. Size: 4,447,076,352 bytes. SHA-256: `112c10a50bbedebb03733d5fab2895a92fdd1d67b0c0eb43223f2510e3b3ff3a`.
