# Stat panel fixes, 0.1.43

The user confirmed the supplied Deployment and Unit Upgrades screenshots came
from 0.1.42. They show an untranslated Player Sorties caption, a heading crossing
the upgrade panel border, and absent Vernier, Turning and Evasion labels.

## Findings and scope

The three missing labels already exist in English in table 3013. Their native
font widths are 74, 80 and 75 units, while their text quads are about 62 units
wide and the adjacent bars begin about 66 units from the label origin. This
supports a layout issue, but does not establish the engine's precise clipping
behavior without an in-game check.

The patch expands the local text boxes to hold complete words and fits their
display widths to 60 units, with unchanged vertical scale. It applies to the
shared Deployment panel, the separate Unit Upgrades panel and both recruitment
panel copies. Parameters uses a 90-unit display limit; Consec. Sorties uses 96
units in its wider cell. The upgrade heading moves down four units. All font
resources, text bindings, character capacities and gameplay values stay intact.

Player Sorties is baked into texture 50101 rather than stored in that text
table. The builder replaces only its 78-by-17-pixel region using the game's
Latin glyphs and original palette. Five byte-identical menu copies are patched;
other variants are untouched. Geometry and coverage are recorded in
`work/ui/stats_043/layout.json`; editable English labels are in
`work/translation/en/stats_043.json`.

## Build and check

Run the builder without arguments first. Inspect the reported label fits, then
use `--preview` to inspect the local caption artwork. `--write` creates
`work/output/ACE3-English-0.1.43.iso` from the local 0.1.42 test ISO. It never
overwrites an existing output. The JSON report records hashes and verifies
every finished-disc byte against the intended edits. The English prologue and
other inherited 0.1.42 content are retained.

Fresh-boot the test ISO, load a normal memory-card save and check Deployment,
Player/Ally selection, Unit Upgrades and Recruit Units. Confirm Player Sorties,
Consec. Sorties, the Parameters heading and all six stat labels remain visible
while changing units. Verify bars and numeric counts still update normally.
The user handles game navigation. Runtime appearance has not yet been verified.

This is a local test build. Any later published release must follow
`docs/RETRO_TRANS_RELEASES.md`; no published 0.1.42 asset is replaced.
