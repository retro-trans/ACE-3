# Tool guide

## Start here

These commands use Python 3.8+ and the standard library. Supply an unpacked ISO from your own disc. Readers do not
change it, and commands that create output preview their work unless passed `--write`.

| Tool | Purpose |
| --- | --- |
| `compare_translation.py` | Generate an offline Japanese/English comparison page using the original disc and the 0.1.42 catalog. |
| `extract_script.py` | Export editable rows with source hashes and stable resource/table/text IDs. |
| `apply_script.py` | Preview edits or write a new ISO, preserving table extents and verifying every changed byte range. |
| `verify_translation.py` | Check supported tables and optionally compare them with the edited export. |
| `build_translation_pairs.py` | Refresh the English/offset-only comparison catalog from original and translated ISOs. |
| `test_translation_workflow.py` | Run synthetic-disc tests without a game image. |

See [TRANSLATING.md](TRANSLATING.md) for complete commands, format coverage and editing constraints.

## Advanced work

The remaining modules preserve the format knowledge and English build steps. They are not a single portable
one-command rebuild of the release. Many select a specific base ISO under `work/output/`, and some require the
original ISO in the repository root. Read each module's `BASE`, inputs and argument parser before running it.
Use a copy of your game image and inspect the dry run first. Generated files and old build reports are not shipped.

| Area | Entry points |
| --- | --- |
| Disc and archive layout | `build_ui_patch.py`, `dialogue_corpus.py`, `repair_disc_layout.py`, `relayout_disc.py` |
| Dialogue and scenes | `scene_source.py`, `build_scene_patch.py`, `build_wave_patch.py`, `seal_scenes.py` |
| Names, abilities, commands | `build_names_patch.py`, `build_combat_ui_patch.py`, `build_remaining_labels_patch.py` |
| Model battle shouts | `build_shouts_patch.py` |
| Font and text geometry | `ui_font.py`, `dialogue_font.py`, `gameplay_font.py`, `build_hangar_fix.py` |
| Encyclopedia and comm windows | `build_encyclopedia_paging_patch.py`, `build_communication_fit_patch.py` |
| Packed scenes and images | `packed_resource.py`, `build_crawl_inplace_patch.py`, `ui_textures.py`, `meeting_captions.py` |
| Movies | `pss_inspect.py`, `pss_video.py`, `pss_remux.py`, `movie_subtitles.py` |
| Release packaging | `package_release_042.py`, `package_retro_trans.py` ([Retro Trans metadata guide](RETRO_TRANS_RELEASES.md)) |

Some advanced modules use `pycdlib` or Pillow; movie processing also needs external media tools. Install only the
dependencies required by the module you use. `test_*.py` beside the modules includes both synthetic checks and
tests requiring local base/output ISOs. A successful public-workflow test does not certify the whole historical
pipeline or in-game rendering. Withdrawn experimental steps are identified in the changelog; they are references,
not recommended release builders.
