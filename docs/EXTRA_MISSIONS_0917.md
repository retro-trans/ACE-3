# Extra Mission text correction — 0.9.17

The user's five screenshots show Japanese text in Extra Missions 3 and 4.
Although the screenshots came from an older patch, inspection of the current
0.9.16 ISO confirmed that both active text tables still contained Japanese.
The earlier main-mission translation selection omitted these two scene IDs.

## Coverage

| Scene | Mission | Translated rows | Plain resource copies |
| --- | --- | --- | --- |
| 2002442 | Extra Mission 3 | 4 dialogue, 31 HUD/objective | 6442, 2002442, 3200442, 3201442 |
| 2002443 | Extra Mission 4 | 11 dialogue, 5 HUD/objective | 6443, 2002443, 3200443, 3201443 |

The 51 unique translations produce 204 changed instances. They include the
reinforcement warning, return-point objective, all stored kill-count milestones,
mission success/failure notifications, AP recovery and the complete support
dialogue in both tables. Examples from the screenshots:

- Benkei: “That's the spirit! Keep taking them down!”
- “Warning: Enemy reinforcements”
- “Info: Enemies destroyed: 200”
- “Objective: Return to the designated point”
- Faye: “That was amazing! I'm impressed!”

Extra Missions 1 and 2 each have one active objective row, already translated as
“Destroy all targets.” All eight copies of those active tables are checked and
retained. Older embedded Japanese strings outside those active tables are not
evidence of an untranslated active objective.

## Build and checks

Run `C:/Python/python.exe tools/build_extra_missions_patch.py` for a dry run,
then add `--write` to create `work/output/ACE3-English-0.9.17.iso` from the local
0.9.16 test ISO. The source hash is pinned. Published release images use a
different disc layout and are not interchangeable with this build input.

`work/translation/en/extra_missions_0917.json` stores English targets and source
hashes; it does not reproduce the Japanese script. The builder compacts the
existing table structure within its original 1,376/960-byte extents and checks
text IDs, null slots, game lookup results, controls, timing and complete readback.
Dialogue uses the existing embedded font and wraps within 400 units/four lines;
HUD notifications stay on one line within 480 units. No font or mission-script
changes are required. The stock duplicate 5000-count notification is preserved.

The copy audit examines every archive header. The 427 nonempty compressed-stream
headers contain no matching unpacked scene size. Nine plain resources share a
relevant size; exactly the eight expected resources match the source text-table
hashes. Zero-sized scene stubs share the compression magic but are treated as
plain resources. This bounded audit does not certify unknown container formats
or unrelated mission variants.

The writer verifies every byte of the completed ISO against the pinned base plus
the eight intended table edits. Geometry and translation measurements are saved
in `work/ui/extra_missions_0917/layout.json`; the build report is beside the ISO.
Fresh-boot in-game display is still unverified. Boot the test ISO and load a
normal memory-card save before testing Extra Missions 3 and 4.

This is a local test build. Published 0.9.16 assets remain immutable.
