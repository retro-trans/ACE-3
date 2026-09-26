# Another Century's Episode 3: The Final — English patch

Fan translation of the PS2 game *Another Century's Episode 3: The Final* (SLPS-25784) into English. The patch is
distributed as an xdelta file that you apply to your own disc image. This repository contains translation text,
glossaries, layout metadata and tools; disc images, extracted artwork and memory dumps are excluded.

## Applying the patch

Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) for automatic patching:

1. Open **Automatic**, click **Refresh catalog**, and browse to your original Japanese ISO or a supported previously patched ISO.
2. Select the **English prologue** patch, which translates the game text and opening movie subtitles.
3. Leave **Target** on **Latest**, choose a new output filename, and apply the patch. Retro Trans downloads the
   matching patch and verifies the resulting disc. Use the latest Retro Trans app when refreshing the catalog.

See the [release notes](https://github.com/retro-trans/ACE-3/releases) for changes, known limitations and supported upgrade paths.
Boot the result fresh and load a normal memory-card save; older save states retain old text in memory.

For manual patching:

1. Dump your own Japanese disc to an ISO. Full patches apply to the original image:
   - `Another Century's Episode 3 - The Final (Japan).iso`, 4,447,076,352 bytes
   - SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`
2. Download a patch from [Releases](https://github.com/retro-trans/ACE-3/releases/latest):
   - `ACE3-English-<version>-movie.xdelta`: English text and English prologue subtitles.
   - Files named `<previous>-to-<version>-movie` update the matching previously released ISO.
     These do not apply to local test builds; check the release's source hashes.
3. Apply it with xdelta3 (or any VCDIFF tool such as Delta Patcher):

   ```bash
   xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-<version>-movie.xdelta ACE3-English-<version>.iso
   ```

4. Compare the output SHA-256 with the release notes or manifest, then play it in PCSX2. Boot it fresh and load
   your normal memory-card save: save states made with the Japanese disc or an older patch keep the old text in memory.

## Check the translation

Compare the Japanese from your own original disc with the English in the bundled comparison catalog:

```text
python tools/compare_translation.py "Another Century's Episode 3 - The Final (Japan).iso"
python tools/compare_translation.py "Another Century's Episode 3 - The Final (Japan).iso" --write
```

Open `work/local/translation-review.html` in your browser. It works offline and lets you search either language,
filter by resource or status, and page through the results. No patched image is needed. The checked-in comparison
catalog contains English, source locations and hashes; Japanese is read from your ISO when you generate the page.

Use `--resource 2002010` to focus on a resource, or `--only untranslated` to show matched Japanese rows that remain
unchanged. `no_match` means the tool could not pair a row, not that its translation is missing. Counts include
duplicate and legacy content and are **not a whole-game completion percentage**. The reader covers BND text tables
and mission text tables; models/battle shouts, packed-only text, fixed name fields, images and movies are excluded.
See [the comparison guide](docs/TRANSLATING.md#check-the-translation) for details.

## Translate it

Fork this project to improve the English or work on another language. Start with
[the translation guide](docs/TRANSLATING.md) for the export/edit/build loop and its limits:

```text
python tools/extract_script.py english.iso work/local/script.json --write
# Edit only the "text" fields, then preview the changes:
python tools/apply_script.py english.iso work/local/script.json --version <version>
python tools/apply_script.py english.iso work/local/script.json --version <version> --write
python tools/verify_translation.py work/output/ACE3-English-<version>-local.iso --script work/local/script.json
```

Replace `<version>` with your new build version. Omit `--write` for a dry run before creating an export or ISO.
The generic editor preserves table sizes and writes
a new ISO; longer text that exceeds the pool needs a format-specific relocation builder. It does not add fonts,
update other resource copies automatically, or prove that text fits on screen. An unchanged export produces no edits.

## Repository layout

- `docs/` — translation guide, tool guide, format/layout notes, changelog and latest release metadata
- `tools/` — comparison, export/edit/apply/verify tools, format-specific builders and their tests
- `work/glossary/` — researched names and terms (with sources) every translation must follow
- `work/translation/en/` — the English text: UI tables, scene files, 80-row dialogue batches with their independent
  reviews
- `work/ui/` — layout measurements and resource metadata; referenced screenshots remain local

Start with [the tool guide](docs/TOOLS.md) and [contribution guide](CONTRIBUTING.md). The public editing commands
take an ISO path explicitly. Advanced builders have version-specific inputs: read their requirements before running
them. Local builds go under `work/output/`; original data and generated review pages stay outside Git.

## Credits

| Role | Contributors |
| --- | --- |
| Project Lead | pow |
| Playtesting | SecondarySebs, BlackHowling \| QiyoShiro |

## License

Translation text and tools: [MIT](LICENSE). The game and its assets belong to Banpresto / FromSoftware and the
respective anime rights holders. Bring your own disc image; this license does not cover the game or its assets.
