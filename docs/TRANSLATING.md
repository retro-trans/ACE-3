# Translating and reviewing ACE3

Use Python 3.8 or later and an unpacked ACE3 Japanese-edition ISO (SLPS-25784) that you own.
The public review/edit tools use the Python standard library; the advanced build tools may additionally need
`pycdlib` or image libraries. CHD, BIN and CUE input are not supported by these tools: extract an ISO first.

## Check the translation

The comparison catalog records release **0.1.42** text, paired by resource ID, structural BND path or active mission
table pointer, and text ID. It is a release snapshot, not a live merge of later translation JSON edits. Japanese
is read from your original ISO and checked against each row's SHA-256. A patched ISO is not the source for this command.

```text
python tools/compare_translation.py original.iso
python tools/compare_translation.py original.iso --write
```

The first command previews counts; the second creates `work/local/translation-review.html`. Open it in any modern
browser. No server or internet is needed. Search covers Japanese, English and row IDs. Control codes are hidden
for readability; turn on Show control codes to inspect them. The page shows 100 rows at a
time and has status and resource filters. Generate a smaller page with a unique filename when useful:

```text
python tools/compare_translation.py original.iso --resource 2002010 --output work/local/mission-01.html
python tools/compare_translation.py original.iso --resource 2002010 --output work/local/mission-01.html --write
python tools/compare_translation.py original.iso --only untranslated --output work/local/unchanged-japanese.html
```

Add `--write` to the last command after reviewing its preview. Existing files are never overwritten; choose a new
output filename for another run. `--rec` is an alias for `--resource`.

| Status | Meaning |
| --- | --- |
| translated | Matched row changed to text without Japanese script; this is not a quality or human-review verdict. |
| untranslated | Matched Japanese row is unchanged in the release snapshot. |
| unchanged | Matched non-Japanese text is unchanged, often numbers or control-only rows. |
| no_match | No target row with the same structural identity; the tool makes no translation claim. |
| needs_review | Target changed but still contains Japanese; target text is omitted from the committed catalog. |

Scope is **BND text tables and active mission text-table pointers**, including menus, Encyclopedia, mission text,
meetings and hangar text that use those formats. Some resources belong to unused/legacy content or are duplicate
copies. Counts describe row instances in these formats, not unique dialogue lines or game completion. Models and
battle shouts, packed-only resources, fixed parameter-name fields, image labels and movie subtitles are excluded.
Unsupported candidate containers are listed in the catalog's scan reports; they are not labelled untranslated.

The catalog contains no Japanese script. Generated HTML does contain Japanese read locally from your disc, so
keep it local. `work/local/` is ignored by Git. Do not commit source-disc dumps or generated comparison pages.

## Export and edit

For English corrections, export from the **patched ISO you intend to change**. For a new language, you may export
from the original ISO, but its fonts will also need work if they lack the target glyphs.

```text
python tools/extract_script.py english.iso work/local/script.json
python tools/extract_script.py english.iso work/local/script.json --write
```

Optional `--resource 4002050` restricts the export; repeat the option for more resource IDs. Edit only `text` fields.
Do not change IDs, table locators, resource filters or preimage hashes. A row such as `4002050:3010:21` means resource
4002050, BND table 3010, text ID 21. Mission tables use `active` as their locator.

English is exported as editable text. A row containing Japanese is exported with `text: null`, plus its source
hash, so this workflow does not create a Japanese JSON corpus. Leave null to preserve that row; replace null with
your translation to change it. An empty string explicitly empties the row, subject to the control-code checks.
Consult the comparison page or the read-only source tools to view the original Japanese and surrounding lines.

An unchanged export creates no edits or output ISO. Shared string pointers and null slots are preserved logically
when a changed table is rebuilt. The editor checks every exported row and every table preimage before writing.

## Preview, build and verify

Choose an unused `0.x.y` version for your local build. The example uses 0.1.43; it is not a published release.

```text
python tools/apply_script.py english.iso work/local/script.json --version 0.1.43
python tools/apply_script.py english.iso work/local/script.json --version 0.1.43 --write
python tools/verify_translation.py work/output/ACE3-English-0.1.43-local.iso --script work/local/script.json
```

The preview lists table IDs, text IDs and replacement text. The writer creates a new ISO and a JSON report;
`--output path/to/new.iso` changes the destination. It refuses to overwrite the source or an existing output/report.
After writing, it compares the complete output against the source: only the planned fixed-size table extents may
differ. The report records the output size, SHA-256 and verification result. Keep that report with your local build.

The verification command checks supported table structure and, with `--script`, every exported row against its
expected text. It is not a validator for excluded formats or in-game rendering. Boot fresh in PCSX2 and load a
normal memory-card save; an old save state can retain old text. Test the changed screen and its adjacent screens.

## Engine constraints and resource copies

- Text must encode as CP932 and contain no embedded NUL. Encoding success alone does not mean the game's font has
  those glyphs. Another language may need font work; the generic editor does not install new glyphs.
- Preserve control tags, glossary links, button icons and formatting placeholders. The editor rejects changes to
  their ordered token sequence and keeps the runtime save-slot number field at its original byte position.
  Link text can be edited, but link IDs must stay valid.
- A whole changed table is repooled within its existing byte extent. IDs, slots, table length, archive layout and
  unrelated bytes stay fixed. If the pool is too small, the build is refused. Do not delete the end of a sentence
  to satisfy a byte limit: use the appropriate relocation builder and verify the engine's memory/layout constraints.
- Width, line count and text-widget character limits vary by screen. This generic tool does not certify them.
  Consult `work/ui/` and the versioned builders. Encyclopedia pages, communication windows and short menu labels
  have different limits; a structural check alone cannot detect clipping.
- **Only listed resource copies change.** Menus and missions often have multiple copies. A matching phrase in
  another resource is not automatically replaced because its context may differ. Export the corresponding resources,
  edit the relevant rows explicitly and test the paths that load them. Do not assume one edit updates every copy.
- Models, packed resources and fixed parameter fields need their existing format-specific builders. Never move
  model chunks or scene script data with a generic text insertion.

## Existing builders and translation sources

`work/translation/en/dialogue/` holds reviewed dialogue batches; `work/translation/en/scenes/` holds meeting,
briefing and hangar drafts. UI categories and later corrections live in the other English JSON files.
`work/glossary/` defines names and terminology; keep them consistent. The [base rules](../BASE_RULES.md) cover
translation context and review. For a new language, keep its data under `work/translation/<language-code>/`.

Advanced builders are version-specific steps with declared base ISOs. They are not a single
all-purpose build command. Check the relevant module's `BASE`, input files and dry-run output before using it.
Useful entry points include `build_wave_patch.py` for mission/dialogue waves, `build_combat_ui_patch.py` for
abilities and commands, `build_shouts_patch.py` for model shout tables, and `build_encyclopedia_paging_patch.py`
for the Encyclopedia page limits. An edited export is a local build input, not an automatic update to those
historical source files. When contributing, include the corresponding English source edits and a changelog entry.

The repository excludes generated build reports, screenshots, RAM dumps, extracted artwork and one-off local setup
scripts. Layout JSON can retain screenshot basenames as provenance; those images are not distributed here. Build
your own prerequisites for advanced builders. For a self-contained starting point, use the export/edit/apply loop
above on a published patched ISO. See [TOOLS.md](TOOLS.md) and [TECHNICAL.md](TECHNICAL.md).

## Refreshing the comparison catalog (maintainers)

Build from the original Japanese ISO and the verified release ISO, never from guessed offsets or an arbitrary
collection of translation drafts. Use a new output filename for another release, then update the comparison
tool's default catalog and this documentation.

```text
python tools/build_translation_pairs.py original.iso english.iso --version 0.1.43 --output work/translation/en/comparison_0.1.43.json.gz
python tools/build_translation_pairs.py original.iso english.iso --version 0.1.43 --output work/translation/en/comparison_0.1.43.json.gz --write
python tools/test_translation_workflow.py
```

The compressed JSON is reproducible and contains English, row identities, original-source offsets/hashes and
scan diagnostics. It excludes original Japanese text and changed targets that still contain Japanese. Keep
unmatched rows explicit rather than guessing a pairing. The comparison reports software-derived status, not
human proofreading coverage.
