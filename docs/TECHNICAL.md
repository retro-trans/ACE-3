# Translation format and layout notes

The supported game is the Japanese PS2 release, SLPS-25784. The tools locate files through ISO9660 and inspect
the BND3 archive in `DATA.BIN`; do not apply file offsets to a compressed CHD or a different disc edition.

## Text identity and replacement

BND containers can nest. Use resource ID, structural table path and text ID to identify a row. Mission containers
can select a relocated table through their active pointer at offset 20. The public reader follows that pointer;
it does not search for arbitrary strings and assume they are active. Duplicate and legacy resources exist.

Text tables contain ID ranges, slot pointers and a CP932 string pool. Preserve null slots, table bounds and the
ordered control-token sequence. The public editor repools a changed table within its existing extent and rejects
overflow. Its post-write comparison permits only the planned table edits. An untouched export produces no output.

The versioned builders can append entire tables and update the relevant pointers. Never generalize that relocation
to model chunks or scene scripts. `work/ui/mission_relocations_021.json` preserves only structural offsets needed
by the advanced mission builder; it replaces its former dependency on a generated 0.1.21 build report.

## Rendering limits

Byte capacity, font support, pixel width, line count and widget character limits are separate constraints. CP932
encoding success does not guarantee a visible glyph. Fonts differ between menus, scene players and gameplay.
Keep glossary/control links intact and measure the visible text, including runtime-expanded placeholders.

- [UI capacity](UI_CAPACITY_FIX.md): growing text also affects menu widget allocation. Blanket capacity increases
  previously exhausted the hangar's arena; use measured limits and the corpus-derived bounds in `build_hangar_fix.py`.
- [Communication windows](COMMUNICATION_FIT_039.md): the lower dialogue area displays three lines. A linked term
  can exist in the script while its fourth line is hidden.
- [Encyclopedia pages](ENCYCLOPEDIA_PAGING_041.md): the 190-character display cap and eight-line page advance must
  agree. Preserve words and links when inserting page breaks.
- [Options](OPTIONS_FIT_040.md): short labels and three-line memory-card warnings need their own layout checks.
- [Combat UI](COMBAT_UI_036.md): abilities, support triggers and command lists use different containers and widths.

Layout JSON under `work/ui/` retains dimensions and source identifiers. Screenshot basenames are provenance only;
images, emulator logs and memory dumps are intentionally excluded from the source repository.

## Validation boundaries

Run structural checks and the relevant unit tests, then test a fresh game boot. The public reader excludes models,
battle shouts, packed-only strings, fixed parameter-name fields, image labels and movies. Their dedicated tools
must be used separately. The 0.1.42 comparison catalog is a release snapshot, including duplicate and legacy rows,
not a completion percentage. The generic editor does not synchronize other resource copies automatically.

For release packaging, preserve the original disc file order and ISO9660/UDF metadata conventions. Verify an
xdelta by decoding it against the intended source image and comparing the full output hash. Current source/output
hashes are in [the release manifest](releases/ACE3-English-0.1.42-manifest.json). Offline checks cannot establish
that every route, animation, save operation and translated screen works in game.
