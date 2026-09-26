# Contributing

Use [Check the translation](README.md#check-the-translation) to compare the original Japanese from your disc
with the released English, then follow [the editing guide](docs/TRANSLATING.md) to test a correction.

Keep translation files under `work/translation/<language-code>/`, shared terminology under `work/glossary/`,
and resource/layout metadata under `work/ui/`. Preserve IDs, source hashes, control codes and glossary links.
Read adjacent lines and the [translation rules](BASE_RULES.md); record uncertainty instead of inventing context.

Include the resource/text IDs, changed English, the source ISO version, and what you checked in game. Add an entry
to `docs/CHANGELOG.md`. Give local test builds an unused `0.x.y` version. Screenshots may be attached to an issue
for a visual bug; do not commit disc data, memory dumps, saves, generated HTML containing Japanese, or local backups.

Run `python tools/test_translation_workflow.py` for the public editing tools. For format-specific changes, run the
relevant tests with their documented disc prerequisites. Test a fresh boot and normal memory-card save; emulator
save states can retain old resources. Report offline validation and in-game testing separately.

The public repository starts with a single source snapshot. Contributors with a clone from before the reset
should clone again rather than merge the old history into a new contribution.
