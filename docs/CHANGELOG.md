# Changelog

## Unreleased — 2026-09-26

- Reformat both published release descriptions to follow SRW-Z: Apply, changes, release status, included content, translation details, acknowledgements, source code and Contribute. Preserve ACE3-specific source/output hashes, patch routes and runtime limitations; distinguish manual installation of the older release from current automatic patching. Keep local copies of both descriptions. Release assets are unchanged.

- Add a Contribute section to published release notes, matching SRW-Z's invitation for bug reports, proofreading and playtesting with the shared Discord link.

- Remove the Source history reset section from published release notes and its obsolete guide reference. Release assets are unchanged.

- Remove the Method section from the README at the user's request. Documentation only.

- Make the README version-independent, link release-specific changes and limitations to Releases, and remove the What is translated section. Use version placeholders in editing examples. Documentation only.

- Record the standing requirement in `AGENTS.md`: every future release must support Retro Trans Tools, pass patch and package validation before publishing, and have verified catalog registration and automatic routing before completion.

- Make the cleaned ACE-3 repository public and add Retro Trans automatic-patching metadata to release 0.1.42. Keep all four published patches unchanged; distinguish Original prologue and English prologue routes for original discs and matching 0.1.35 upgrades. Add a reusable dry-run-first metadata packager and user/maintainer instructions. No game version or translation changes.
- Decode-verify all four patches with Retro Trans's bundled xdelta engine against the published ISO sizes and SHA-256 hashes. Check its catalog routing for both original-disc choices, matching 0.1.35 upgrades, current 0.1.42 discs and unknown-disc rejection. This verifies patch compatibility; in-game coverage is unchanged.

- Validate cleanup with 13 public-workflow tests and 16 targeted advanced-builder tests. Check the public snapshot for valid Python/JSON, working local documentation links, omitted binary artifacts and common credential patterns. Keep a verified private backup of the prior source history and release assets.

- Prepare a public contributor source snapshot and reset Git history to a single initial commit. Keep translation sources, glossary and review notes, editing tools, format-specific builders/tests and useful layout metadata. Move 283 generated files, extracted images, crash dumps, logs, one-off scripts and superseded build journals out of the repository into a private local backup. No game release or translation wording changes.
- Add contributor, tool and technical guides plus the MIT license text. Keep the latest release notes and hashes under `docs/releases/`; exclude local binaries, build output and backups. Retain the 20 relocation records actually needed by the advanced mission builder instead of its generated report dependency.

- Add Check the translation and Translate it README sections, a standalone offline comparison page, an English/offset-only 0.1.42 comparison catalog, and a documented export/edit/apply/verify workflow for supported BND and mission text tables. The generic editor checks preimages and controls, preserves fixed extents, writes a new ISO and verifies the exact output delta. Unsupported formats, resource-copy handling and runtime layout limits are explicit. Tooling only; no new game release.
- Verify the workflow with 13 automated tests, including a synthetic-disc edit/write/verify round trip. Check the 91,074-row catalog against the original disc, a 2,709-row export/no-op verification and a single-table edit preview against 0.1.42, plus browser search, filtering, pagination and the control-code toggle. No Japanese script is stored in the committed catalog.
- Add a README credits table matching the SRW-Z project's format: Project Lead — pow; Playtesting — SecondarySebs, BlackHowling | QiyoShiro. Documentation only; no new game build.

## 0.9.3 — 2026-09-29 (release)

- Integrate the two remaining prepared English movie tracks: MOVIE003 (Axis, 48 subtitle cues) and MOVIE006 (resonance / two Earths, 11 cues). Retain the reviewed preview wording, timing and layout. Preserve original movie audio, non-video packets, frame counts, frame rates and file sizes; decode-check both remuxes and verify the full output disc.
- Include the 0.9.1 **Combo Attack / Damage** Deployment-column repair and the 0.9.2 lock-on HUD font repair. Preserve opening lyrics, prologue subtitles, simultaneous credits dialogue/song captions and the ending disclaimer.
- Package the supported English-prologue edition with an original-disc full patch and a published 0.9.0 upgrade, using canonical Retro Trans metadata and complete decode verification. New movie playback and the two UI fixes still require fresh-boot in-game confirmation; the unresolved short speaker label in MOVIE006 remains documented.
- Published `v0.9.3` after both patch round trips, upstream package validation and uploaded asset size/SHA-256 checks passed. Catalog workflow `36506289941` succeeded; the actual public catalog routes original, 0.1.35, 0.1.42, 0.1.47, 0.1.65 and 0.9.0 images to 0.9.3, recognizes 0.9.3 as current, excludes the discontinued edition and rejects unknown discs. Records are in `docs/releases/0.9.3/`. Release output SHA-256: `e8a5173150f3c44017adb652aee4798696d3e6ab1ebf86d4bc611b800d53b02b`.

## 0.9.2 — 2026-09-29 (test build)

- Repair the separate lock-on HUD font in all eight gameplay bundles. Its missing ASCII letters reproduced the reported **Monsuno type10** label as `???s??? ????10`. Add 32 aliases and 47 glyphs from the game's own complete font, covering all printable ASCII without changing enemy names.
- Preserve all 242 original glyphs and the HUD atlas dimensions, GPU header and palette. Build from 0.9.1, retaining the Deployment caption repair; verify all archive payloads and disc files. In-game confirmation remains pending. The two outstanding CG movies are still not integrated; no public release is created.

## 0.9.1 — 2026-09-29 (test build)

- Repair the blank **Combo Attack** and **Damage** captions in the Deployment team summary. Both translations were already present, but exceeded their original local text boxes. Widen the caption column and move its separators and values right through vertex geometry, preserving origins, text, bindings and the outer panel.
- Build from published 0.9.0 with guarded layout edits and a complete output-disc byte check. In-game confirmation remains pending; this is a local test build, not a public release.

## 0.9.0 — 2026-09-28 (release)

- Adopt the requested **0.9.0** version for the latest 0.1.68 content. Include the empty-ally **None** correction, the **BATTLE STATIONS** briefing banner, and the Parameters gauge geometry repair. Preserve the prior opening/ending subtitles and all earlier translation work.
- Package only the supported English-prologue edition, with a full original-disc patch and a smaller upgrade from published 0.1.65. Earlier supported releases upgrade through the existing chain. Keep canonical Retro Trans metadata, decode verification and public route verification with the release records.
- Published `v0.9.0` after both patch round trips, upstream package validation and uploaded asset size/SHA-256 checks passed. Catalog workflow `36397824901` succeeded; the actual public catalog routes original, 0.1.35, 0.1.42, 0.1.47 and 0.1.65 images to 0.9.0, recognizes 0.9.0 as current, excludes the discontinued edition and rejects unknown discs. Records are in `docs/releases/0.9.0/`. Release output SHA-256: `68b7fc22f7cde93b453223af0d45ca4e040be40f0edb263acc128f354e1e37d1`.
- The three latest fixes passed whole-disc byte checks. Briefing animation and stat gauge behavior still need fresh in-game confirmation; earlier movie/credits runtime limitations remain. The version change does not certify full translation coverage.

## 0.1.68 — 2026-09-28 (test build)

- Repair Parameters gauge fills overlapping their captions in the reported Player Select screen. The 0.1.49 fix shortened the fill meshes and shifted their widget origins, while the screenshot shows fills remaining at their old positions despite correctly shifted tick frames. Bake the 28-unit shift into the fill vertices and restore the native widget origins, following the Controls spacing fix.
- Apply the correction to all 42 fill layers across the four previously adjusted Deployment, Unit Upgrades and recruitment layouts. Preserve intended world bounds, native fill/frame offsets, text, values, bindings, frame artwork and other layout fields. Build from 0.1.67 and verify the complete disc delta. In-game rendering and gauge animation still need testing; no public release is created.

## 0.1.67 — 2026-09-28 (test build)

- Translate the image-based briefing alert, 戦闘配備, as **BATTLE STATIONS** in all three shared briefing bundles. Render with the game's English glyphs and fit the four original character quads together into one line inside the existing brackets.
- Preserve the indexed texture size, palette, animated border artwork, unrelated layout nodes and event data. Build from 0.1.66, retaining its empty-ally **None** correction. Inspect a reconstructed banner preview and verify the complete output disc against the six intended resource edits. In-game animation remains unverified; this is a local test build, not a public release.

## 0.1.66 — 2026-09-28 (test build)

- Translate the empty ally-slot placeholder to None in all four shared unit-name table copies (resources 4002050, 4002053, 4002054 and 4002057; table 3077, text ID 2). The earlier unit-name pass had excluded it as a non-unit sentinel, leaving Japanese in the deployment confirmation dialog.
- Build from the exact published 0.1.65 image. Preserve every pointer, other table row, dialog format and unit selection; replace only the four five-byte string spans. Check copy coverage, native font width and the entire output disc against the intended edits. In-game appearance remains unverified; no public release is created.

## 0.1.65 — 2026-09-28 (release)

- Package the approved 0.1.64 content as a distinct release identity using the original disc's file order. All 133 game files match the local test build. Release size: 4,455,581,696 bytes; SHA-256 `b8d7f75e714eb2a0575bf9b7d79030bdc7859a75552b4560bb13e166f633486a`.
- Provide an original-disc full patch and a published English-prologue v0.1.47 upgrade, using the current Retro Trans builder and validator. Retain older supported upgrade paths through the catalog. Release notes follow the established Apply/changes/status/included/translation/acknowledgements/source/Contribute format and preserve the remaining runtime and translation limitations.
- Both patches passed full decode verification; all five uploaded assets matched their local sizes and SHA-256 hashes. Published v0.1.65 and confirmed successful catalog workflow 36372451127. Verified public automatic routes from original, 0.1.35, 0.1.42 and 0.1.47, plus the 0.1.65 no-op and unknown-disc rejection. Store canonical metadata and the published route check under `docs/releases/0.1.65`.

## 0.1.64 — 2026-09-28 (test build)

- Integrate the user-approved 0.1.63 opening layout: full CG picture with compact romaji and English subtitles inside the picture, using the exact preview subtitle script.
- Re-encode only the opening video and preserve original audio packets, movie extent and frame timestamps. Build on 0.1.62 to retain the ending dialogue and lyric hold changes. Verify complete movie decoding and every output disc byte; emulator playback is not yet verified. No public release is created.

## 0.1.63 — 2026-09-28 (opening preview only)

- Prepare an MP4 of the opening with compact romaji/English lyrics inside the full CG picture. Remove the added subtitle band, reduce native font sizes to 14/15 pixels, tighten the line spacing to 18 pixels and add an outline for readability over the picture.
- Preserve the approved wording, timing and original audio. Render all 19 bilingual cues at 960x720, validate complete audio/video decoding and inspect sampled frames. This is a layout preview for user review; no game movie or ISO is changed.

## 0.1.62 — 2026-09-28 (test build)

- Keep ending dialogue and song captions visible for 0.5 seconds after their timed line ends, unless the next cue on the same track starts sooner. Preserve the native two-frame text-slot turnover margin for adjacent lines.
- Check all 98 cues and extend 90 durations. Change only native event-duration fields; preserve text, cue starts, audio, layout and all other disc bytes. Build on 0.1.61 without replacing it. Whole-disc verification is performed by `tools/build_credits_hold_patch.py`; this timing revision has not been replayed in the emulator.

## 0.1.61 — 2026-09-28 (test build)

- Add 72 English credits-dialogue captions and 26 simultaneous romaji/English ending-song captions through the game's native animation text events. Preserve the live credits, music, voices, staff names and existing postcredits dialogue; retain the approved opening from 0.1.59.
- Align the supplied MP3 against nine sections of the actual credits recording and convert recording timestamps to native animation frames. Keep dialogue below and lyrics above the scrolling staff names.
- Verify all 98 caption cues in native saved-state playback. Clip scrolling logos as well as staff names so the IKONOS/JSI section does not cover dialogue; preserve full image bounds outside the roll.
- Relocate the four matching ending text tables, append caption tracks to the original animation and verify the complete rebuilt archive and disc. Native saved-state testing is separate from fresh-disc loading verification; see `ENDING_SUBTITLES_061.md`. No public release is created.

## 0.1.60 — 2026-09-28 (ending song preview only)

- Transcribe the user's supplied ending-song MP3 locally with Whisper large-v3-turbo and large-v3, compare targeted verse checks, and independently review the meaning of all 74 useful-pass transcript rows. Exclude unsupported credits, social-media and closing-phrase hallucinations.
- Prepare 26 timed romaji/English captions and a full-track MP4 lyric preview with a playback clock and waveform. Mark four captions covering three unresolved wording/pronunciation questions for user review. Keep the source MP3 and Japanese transcripts ignored; no game patch or release changes.
- Add reusable dry-run-first transcription and lyric-preview tools, caption layout/timing guards and full MP4 audio/video decode validation. The preview follows the supplied MP3, not game-credit timing.

## 0.1.59 — 2026-09-28 (test build)

- Integrate the user-approved 0.1.58 opening romaji/English captions into MOVIE001, keeping the complete picture proportional inside the game's fixed movie frame and retaining original audio/non-video packets. Preserve all 4,980 frames at the opening's exact 30 fps.
- Add bounded packet pacing and explicit frame-clock handling to the PSS remuxer, with three regression tests. Full movie decoding and full-disc comparison passed; only the opening movie extent differs from 0.1.54.
- Local ISO only: 4,447,076,352 bytes; SHA-256 `02a88eef45164866969f6892910b4f88ff739eda62cf6f182a84739744ce1faa`. In-game playback verification remains incomplete because Computer Use was stopped before playback. No public release was created.

## 0.1.58 — 2026-09-28 (opening lyric preview only)

- Replace the partial opening-song draft with 19 romaji/English cues covering the first verse and chorus heard in the game edit, using the lyrics supplied by the user. Resolve all previously marked lyric gaps and correct the first-person questions and heartache/yearning wording after meaning review.
- Refine phrase timing using the supplied lyric phonetics and local Whisper alignment. Retain a separate band below the full picture and identify the result as a preview requiring audiovisual review. Preserve the older preview; no game patch or release is changed.

## 0.1.57 — 2026-09-28 (credits subtitle preview only)

- Capture the user's earlier slot-2 credits state in an isolated PCSX2 profile, recovering the complete opening exchange. Preserve the original state and leave memory cards disconnected.
- Prepare English credits dialogue subtitles from local Whisper large-v3-turbo transcription, targeted large-v3 checks and an independent meaning review. Record recognition uncertainties rather than inventing missing speech.
- Add a preview renderer with timing and text-fit checks, a separate subtitle band below the intact credits picture, and MP4 decode validation. Keep Japanese transcripts, save states and media local and ignored. No game patch or release is produced; user review comes before integration.

## 0.1.56 — 2026-09-28 (credits capture only)

- Locate the user's slot-1 credits save state from build 0.1.53 and preserve a verified identical local copy. Restore it in an isolated PCSX2 2.8.2 profile with both memory-card slots disconnected.
- Capture 5 minutes 25 seconds of the credit roll and following scene, verify MP4 decoding, and run local Whisper transcription. Confirm spoken dialogue is present during the roll. The first sentence is incomplete because the save begins mid-line; transcription is unreviewed and no new subtitles or game patch are produced in this capture step. Keep the state, recording and Japanese draft in ignored local folders.

## 0.1.55 — 2026-09-28 (movie previews only)

- Prepare local MP4 previews of the five remaining PSS movies using local Whisper transcription and reviewed English subtitles. MOVIE003 has 48 dialogue cues; MOVIE006 has 11, with one short speaker name still uncertain. The two short transition movies have no reliable speech and retain no invented captions.
- Add a partial opening-song review draft with romaji above English in a separate band below the intact picture. Mark unresolved sung phrases visibly; Whisper produced substantial lyric errors even with larger models. This is not a complete or human-audio-verified lyric translation.
- Keep source media and Japanese machine transcripts local and ignored. Add reproducible audio extraction and preview rendering tools with timing/fit checks, hashes and review metadata. No game ISO/PSS or published release is changed. User preview review is required before game integration; engine-rendered staff-credits voices remain a separate unresolved task.

## 0.1.54 — 2026-09-27 (test build)

- Translate the image-based story disclaimer after the credits. Replace the sole 256×128 texture in ending resource 4350; keep its header, palette, dimensions, scene placement and all other disc bytes unchanged.
- Meaning-reviewed English preserves the distinction between the game's original story and the settings/storylines of the featured anime works. Local English-prologue test build from 0.1.53; does not add credits voice subtitles or translate the remaining movies. In-game appearance remains unverified.
- Inspected the decoded English preview; all six lines fit inside the original texture. Full-disc comparison passed with only its indexed pixels changed. Size: 4,447,076,352 bytes; SHA-256: `19c494ad099d38cc4efaf8aaa3676bfec7f8def7f6bf621e2b882efd6dcbbc85`.

## 0.1.53 — 2026-09-27 (test build)

- Translate the separate mission-ending comm sequence containing Jamil's “Everyone...! Well done!”: all 17 timed lines and the quit prompt in scene 2002341 and its three copies. This variant was outside the earlier active-mission audit. Other unclassified mission variants and battle shouts are not certified translated.
- Relocate complete English tables, preserve source scripts, timing commands, row IDs and sparse-slot structure, and check the existing 400-unit/four-line HUD budget and Latin glyph availability. Meaning review covers all 18 rows plus four following context rows; names follow the project glossary and adjacent-scene terminology.
- Local English-prologue test build from 0.1.52, retaining its menu-spacing changes. Runtime appearance remains unverified.
- Verified all four ending resources, 10,344 archive payloads and 133 ISO files. Size: 4,447,076,352 bytes; SHA-256: `d323b46805dcbfbcbb8e688bb203db70b7b2dd46512546e16664876e96d002c3`.

## 0.1.52 — 2026-09-27 (test build)

- Move Controls choices into a separate right column and extend its visible right edge. The 0.1.51 screenshot shows shortened panels retaining their old origins; bake the new positions into mesh vertices and restore original widget origins instead of relying on origin changes alone. Give every choice a full native text width plus padding and reserve separate 14-unit arrow gaps, including Flight Rev. and Invert X/Y. Keep the full option names and all settings bindings.
- Widen all normal and selected Intermission button borders by 32 native units in both copies, retaining space after Combat Records for the selection marker. Preserve captions and their positions.
- Local English-prologue test build from 0.1.51. Checks cover caption-column clearance, all choice/arrow intervals, screen limits, button clearance, bindings and unchanged unrelated fields; runtime appearance remains unverified.
- Spacing validation passed for 39 choices, 24 arrows and 15 option rows across three Controls copies, plus both Intermission copies. Full-disc comparison confirms only the five intended layouts changed. Size: 4,447,076,352 bytes; SHA-256: `99652863265618c436709256d49d5870e5062de3a47a3458cfb2d920e83ff96d`.

## 0.1.51 — 2026-09-27 (test build)

- Address the Controls screenshot's absent Camera Movement, Button Mapping and Restore Defaults captions, plus the clipped Control Scheme caption. These strings already exist in English. Replace scale-dependent fitting with 192-unit caption boxes at scale 1 and widen the actual caption column by 36 units in all three Controls menu copies.
- Shift and shorten the adjacent choice area without moving its right edge. Give long choices such as Flight Rev. and Invert X/Y complete unscaled text boxes, keeping their right edges fixed. Preserve all option names, control mappings, settings values, help text and bindings.
- Reuse the Game column layout routine with explicit Controls configuration. Local English-prologue test build from 0.1.50; in-game visibility is still unverified.
- Verified 21 caption instances and 39 choices, with at least 15 and 8 native units of spare text-box width respectively. A regression check confirms the shared routine still reproduces the 0.1.50 Game layouts byte-for-byte. Full-disc comparison passed with only the three Controls layouts changed. Size: 4,447,076,352 bytes; SHA-256: `3660248c74beed04f64e1dcffd5e70f7ddffdcee42ec146931a6a31b2bb3cb19`.

## 0.1.50 — 2026-09-27 (test build)

- The user reports Lock-On Priority is still blank; the PCSX2 log confirms a boot of 0.1.49. Correcting the skewed quad in 0.1.48 was insufficient. Replace scale-dependent caption fitting with a physically wider Game menu column: all nine caption boxes are 180 units wide at scale 1, and normal/selected button borders widen by 24 units. Keep the full requested option names.
- Move the adjacent choice area's left edge right by 24 units and shorten its geometry while preserving its right edge. Check full native text widths for all choices, including alternate difficulty widgets, in all three Game menu copies. Preserve help text, bindings, capacities, settings values, vertical positions and unrelated resources.
- Local English-prologue test build from 0.1.49. Geometry validation is not in-game verification; visibility still needs testing.
- Verified 27 unscaled captions and 69 choice texts, with minimum spare box widths of 14 and 27.95 native units respectively. The full-disc comparison passed: only the three Game layouts change. Size: 4,447,076,352 bytes; SHA-256: `93cc89c3e958fc6e751e29c4f6e6e6e4ebfe6e68a1980632edc5087052b203c0`.

## 0.1.49 — 2026-09-27 (test build)

- Respond to the new Deployment screenshot showing visible stat names overlapping their gauges and Consec. Sorties colliding with the count. Replace the prior scale-dependent fitting with an actual wider caption column in Deployment, Unit Upgrades and both recruitment panels. Preserve all six full stat names in 88-unit boxes at scale 1; shift gauge fills and their tick frames right 28 units and shorten them by the same amount, retaining their right edges and value bindings.
- Shorten the consecutive-deployment caption to Streak in the three shared English tables and restore its original caption cell. Preserve the count, Player Sorties sprite, other wording and game values. Remove horizontal scaling from Parameters while retaining its widened box and the earlier Upgrade heading's vertical correction.
- The dry run checks complete text boxes, at least six units of caption-to-gauge clearance, all fill layers, matching frame geometry, preserved gauge right edges and unchanged nonselected fields. Local test build from 0.1.48; runtime appearance remains unverified.
- Verified 24 captions and 42 gauge layers: minimum unscaled clearance improves from -17.84 to +6.15 native units. Full-disc comparison passed with only the planned four layouts and three caption strings changed. Size: 4,447,076,352 bytes; SHA-256: `b9caa1cd0cef5e350d7393226ef3a26f1617cce05d61324f9ec90df103cfe15c`.

## 0.1.48 — 2026-09-27 (test build)

- Repair the still-blank Lock-On Priority option in all three Game menu copies. The 0.1.44 builder used exact equality on slightly different floating-point vertex coordinates and widened only the bottom-right corner. The top edge remained 158.21 units wide for a 164–166-unit label, depending on the menu font. Make both edges 172–174 units wide while retaining the existing horizontal fit within the 140-unit row.
- Correct the earlier builder's corner selection and add a regression check that rejects the old skewed text box. Audit the previously fitted stat panels; none has this malformed right edge. Wording, bindings, scripts and other menu elements are unchanged.
- Local English-prologue test image built from 0.1.47; in-game visibility still requires testing.
- Two geometry regression tests and the corrected earlier builder's dry run pass. Whole-disc verification confirms only three four-byte coordinates changed. Size: 4,447,076,352 bytes; SHA-256: `904ad87a1dc019992e31869c1fc3e3b19fab528cf4ba1acd41da879b5721c8e0`.

## 0.1.47 — 2026-09-26

- Publish the 0.1.43–0.1.47 translation and UI fixes as an English-prologue-only release, with a full original-disc patch and matching published 0.1.42 movie upgrade. Both patches passed complete decode verification and the current Retro Trans package validator. Release image: 4,455,428,096 bytes, SHA-256 `b86f9a52d2b8bfae419d5a7d7bd48d59665787b3e6393e3722d9dc757129aa8e`.
- At the user's request, discontinue non-movie downloads from this release and older releases. Update the README, release notes and old metadata to the supported edition. Preserve exact withdrawn catalog identities while removing their automatic routes; Retro Trans 0.3.1 adds compatible refresh support. Remaining published movie patches are unchanged.

- Use the user-requested spelling Nu Gundam, including Nu Gundam (HWS), throughout the English unit-name glossaries, translation inputs and dialogue. Supersede old review notes that required lowercase spelling.
- Correct 40 stored occurrences in the 0.1.46 disc: 36 indexed text occurrences and four fixed-field unit parameter names. Check each source string and preserve all pointers, control codes and record sizes. The builder previews changes by default and verifies the complete written image against the intended output hash.
- Local test build; in-game visibility remains unverified.
- Finished-image verification passed. Size 4,447,076,352 bytes; SHA-256 `77fa368be1d5e287ebf6a560c363bdadc85f4d2a3c8672ca23b91ce22b8c12df`. No lowercase nu Gundam spelling remains in the English translation or glossary JSON files.

## 0.1.46 — 2026-09-26 (test build)

- Fit the missing Briefing headings by shortening Victory Conditions and Defeat Conditions to Victory and Defeat in all three shared menu copies. The objective column begins only 96.53 native units after the headings; the previous labels measured 174–187 units. Keep objective text and pause-menu headings unchanged.
- Apply six fixed-size string edits on top of 0.1.45, preserving the branching report translations, layouts and scripts. The builder checks exact preimages, unaliased string storage, font widths and unchanged neighboring rows, then verifies every output byte against the intended delta.
- Confirm that the finished 0.1.45 Hojo Army report already contains its English title and all three English dialogue rows. The build/save-state provenance of the newly supplied Japanese screenshot is awaiting confirmation; no additional dialogue defect is claimed resolved here.
- Whole-disc verification passed: only the six intended heading strings differ from 0.1.45. Size 4,447,076,352 bytes; SHA-256 `9c4e95b4294ed8b017279ef5e957cb3388bd5802d444c08b9524baab9a7035f8`. In-game heading visibility remains unverified.

## 0.1.45 — 2026-09-26 (test build)

- Translate all 16 missed branching Situation Report resources, including Federation Movements and the reported Shirahime dialogue: 141 Japanese title/dialogue rows, plus normalization of the D.O.M.E. title. These sparse report tables were absent from the prior translation inputs.
- Preserve every topic, speaker, speed, thumbnail, color and glossary command in its original order. Keep null slots and text IDs intact, append English strings, and retain all other script/image chunks. Fit report dialogue into three lines across all three menu fonts, with linked terms kept on one line.
- Audit all 156 window resources (191 active tables, 2,939 rows) and the 40 previously supported mission resources (6,338 dialogue rows, including both routes). No Japanese remains in those audited active text rows after the patch. This does not certify unused/legacy scenes, unclassified mission variants, or Japanese baked into images.
- Inherit 0.1.44 and the English prologue. Build using `tools/build_branch_reports_patch.py`; review and editable translations are in `work/translation/en/branch_reports_045.json`. In-game route navigation remains unverified; this is a local test build.
- Finished-disc verification passed for all 10,344 archive payloads, 133 disc files and 16 changed report bundles. The finished-ISO audit confirms zero Japanese rows in the stated window/mission scope; four boot-metadata tests pass. Size 4,447,076,352 bytes; SHA-256 `879cd6a564669ce82966c26fd96099b0cbed4ee41e65b6c4aaff4ee435c0de7f`.

## 0.1.44 — 2026-09-26 (test build)

- Use the user-requested Game option names Lock-On Info, Lock-On Priority and Ingame Comm in all three menu copies. Help descriptions, option values and controls remain unchanged.
- Fit these labels into their existing rows with complete local line boxes, preserving text height, bindings and character capacities. The previous blank rows already contained English strings; the layout change still needs in-game visibility verification.
- Build from 0.1.43 with `tools/build_game_labels_patch.py`, preserving its stat-panel changes and earlier fixes. The dry run checks exact text preimages, serialized label widths and unchanged neighboring text/resources. The build verifies every archive payload, disc file and all three finished menu bundles. This is a local test build, not a published release.
- Verified all 10,344 archive payloads, 133 disc files and nine updated label instances; four boot-metadata tests pass. Size 4,447,076,352 bytes; SHA-256 `d0191dd3b4cc2c3936b54ba69d5d0fc40bb48c5a7f3a24f111a2111fdc81fab8`. In-game visibility remains pending.

## 0.1.43 — 2026-09-26 (test build)

- Translate the baked Player Sorties label with native game glyphs in five identical menu texture copies. Preserve the palette, texture headers and all pixels outside its caption rectangle.
- Fit Parameters and all six stat labels in Deployment, Unit Upgrades and both recruitment menu copies. Expand each local text box before horizontal fitting; retain text height, bindings and allocation capacities. Also fit Consec. Sorties in Deployment.
- Move the Unit Upgrades Parameters heading down four native units to clear the panel border. Existing English stat wording is unchanged.
- Build from 0.1.42 using `tools/build_stats_panel_patch.py`. The builder checks source textures, label bindings, glyph capacity, measured widths, non-overlapping fixed extents and the complete finished-disc byte delta. In-game visibility and alignment still require a fresh-boot check; this test build is not a published release.
- Verified all nine patched resources and all 29 fitted text quads; the complete disc matches only the intended changes. Size 4,447,076,352 bytes; SHA-256 `181104eb34146c323186e0bda6205c7bbdb1de7031c4df6c870e3a92819f9bbc`.

## 0.1.42 — 2026-09-25

- Rename the situation briefing screen from Situation Archive to the user-requested Situation Report in all three shared title copies (table 3010, text 21). The replacement fits inside the previous title width and character capacity.
- Record Situation Report as the preferred screen name in the UI glossary. Preserve historical build inputs, all scene text, layouts, fonts and earlier fixes, including the English prologue and 0.1.41 Encyclopedia pagination.
- Build with `tools/build_situation_report_patch.py`; its dry run verifies exact title preimages, unchanged neighboring rows/resources and existing width bounds. Finished-disc verification is recorded in the output JSON. In-game appearance remains pending.
- Verified all three finished-disc title bundles, all 10,344 archive payloads and 133 disc files. Size 4,447,076,352 bytes; SHA-256 `0ccdd0680135bb3138c1248f81fcad35450af892c9f1b09b8a4e486637572f5e`.
- Package the changes since 0.1.35 as full text/movie patches and matching updates from the published 0.1.35 editions. The release discs retain the original file order, verify all 133 file payloads and are 4,455,411,712 bytes. Text SHA-256: `ad9dffa95cf8b8144c13d25c014d73992574c6f50ce4518661ac9c2be486557d`; movie SHA-256: `c72752b32b5982b63ef8c5db5f171090469e3aad94999245cace2cb760565353`. The package tool decode-verifies each patch against its intended ISO and records input/output hashes in the release manifest. See [release notes](releases/RELEASE_NOTES_0.1.42.md). Runtime verification remains pending.

## 0.1.41 — 2026-09-25

- Fix text lost between Encyclopedia pages. The 190-character display limit cut Zentradi at "insuff", while the eight-line page advance skipped the rest. Preserve all wording and glossary links while fitting complete text into each page.
- Audit all 88 entries across three menu copies; adjust page breaks for 60 entries (180 instances). Keep paragraphs together where possible; longer entries may gain pages or extra bottom spacing. Preserve all fonts, layouts, allocations, executable code and separate gameplay glossary copies.
- Inherit 0.1.40 and the English prologue. See [cause, pagination and runtime check](ENCYCLOPEDIA_PAGING_041.md). Fresh-boot in-game verification remains pending.
- Five pagination/finished-disc tests and four boot-metadata tests pass. All 10,344 archive payloads and 133 disc files verified. Size 4,447,076,352 bytes; SHA-256 `8f439b6e501abf6ab44ebe92581f48c2764d6550c3912df6a98cf814b10375be`.

## 0.1.40 — 2026-09-25

- Fit the four memory-card operation warnings into three lines; retain complete power/card-removal cautions and slot information. Review all 42 category rows against the original disc; preserve the narrower scrolling confirmation/error panels.
- Rename Attack Demo to Combo scene, Text to Comm messages, and Camera Control to Camera Movement; update Combo scene help consistently in all three menu copies.
- Fit long Game/Controls labels inside their existing left-hand rows, preserving text height and menu geometry. This addresses the clipped Control Scheme and overwide labels visible in the supplied screenshots; blank-label runtime behavior still needs fresh-boot verification.
- Apply 27 text changes and 22 horizontal fitting changes, retaining earlier translation fixes and the English prologue. See [scope and test route](OPTIONS_FIT_040.md).
- Finished-disc verification passes: four targeted tests and four boot-metadata tests; all 10,344 archive payloads and 133 disc files verified. Size 4,447,076,352 bytes; SHA-256 `08673dbe4c80cdb119b971704b2580f23d770f48581c80ad720ff92107ecd167`. Runtime appearance remains pending.

## 0.1.39 — 2026-09-25

- Fix hidden fourth lines in the bottom communication window. Both reported Londo Bell links were correct; their linked words were below the visible body area. Audit 3,411 active communication rows and fit all 114 overflowing entries into three lines across 104 scene copies (456 changed text instances).
- Preserve all wording in 99 entries by changing line breaks only. Independently review 15 compact display translations against 70 original/context rows; retain ranks, timing, qualifications, commands, links and locked names. Append updated tables while preserving original scene scripts.
- Replace `Can add: %s` with the user-requested `Purchasable: %s` in all three notice templates. All 309 runtime roster expansions fit (maximum 373 font units and 36 characters).
- Retain the English prologue, 0.1.37 pause alignment and 0.1.38 translations. See [cause, coverage and test route](COMMUNICATION_FIT_039.md). Runtime verification remains pending with the user.
- Finished-disc checks pass: all 3,411 audited communication rows use at most three body lines; all links and highlighted names remain exact. Four targeted tests and four boot-metadata tests pass; all 10,344 archive payloads and 133 disc files verified. Size 4,447,076,352 bytes; SHA-256 `112c10a50bbedebb03733d5fab2895a92fdd1d67b0c0eb43223f2510e3b3ff3a`.

## 0.1.38 — 2026-09-25

- Translate all eight shared confirmation rows in four table copies, including the Japanese Yes/No footer on Retry. Preserve button icons, IDs and the fixed table extent.
- Review all 177 playable model parameter name fields and their legacy counterparts; update matching compressed twins. Translate Ixbrau's separate Results-name source while preserving all stats, scripts and model chunk boundaries. Document truncated-source uncertainties without inventing missing qualifiers.
- Verify that all 338 ability/support rows in four active menu tables remain English, including Mood, Vital Jump and Organic Energy. The originating screenshot's build/save-state is not yet confirmed; runtime verification remains pending with the user.
- Inherit the English prologue and 0.1.37 alignment fixes. See [scope and test route](TECHNICAL.md); final verification counts and SHA-256 are recorded in the output JSON.
- Built and verified all 10,344 archive payloads and 133 disc files. Four targeted built-disc/field tests and four boot-metadata tests pass. Changed 344 model name fields and verified all 218 repacked twins. Size 4,447,076,352 bytes; SHA-256 `e6718d535239246d025058a6630f2c50e5ff068efe219cc8356997a3b3d133ab`. Runtime testing remains pending.

## 0.1.37 — 2026-09-25

- Fix overlapping Victory Conditions / Defeat Conditions headings in all seven pause layouts. Stack objective rows below headings, align their left edges, and enlarge/reposition the backgrounds to retain all three victory and two defeat rows. Keep the font size unchanged.
- Fit six long objective phrases to a 355-pixel body width with reviewed abbreviations; preserve counts, conditions, and separators. Check 905 English objective occurrences across the gameplay font variants. All four targeted layout tests pass.
- Build from 0.1.36-movie-test, retaining the English prologue. Fixed-size edits preserve disc/resource offsets and scripts. See [layout details and test route](TECHNICAL.md). Runtime verification remains pending.
- Whole-disc comparison passed: only the 209 planned edits differ from 0.1.36-movie-test. Output size 4,447,076,352 bytes; SHA-256 `94ddf27105ddcfcac9af3797f1b04c4315cf5397f39934df8005375fd1157530`.

## 0.1.36 — 2026-09-25

- Translate the complete ability/support category (338 rows), all 104 unit command lists (432 distinct strings, 1,966 rows per menu copy), 136 shared action/input rows, and 191 unit/object/ship labels. Translate matching scene-specific pause-map names and legacy model command/title copies, including compressed twins.
- Preserve button sequences, continuation markers, null slots, command table format, scene offsets, and model chunk boundaries. Check text against both menu and gameplay fonts; retain full meanings alongside display abbreviations.
- Independent meaning reviews and glossary corrections recorded in `work/translation/en/*_036.json`. Scope, uncertainties, and test route: [Combat UI 0.1.36](COMBAT_UI_036.md). The baked Player Sorties sprite is outside this text-table pass. Runtime testing remains with the user.
- Verified all 10,344 archive payloads and 133 disc files; all eight combat UI tests and four boot-metadata regression tests pass. Text ISO SHA-256: `5ce1cde7eeb0dc53d8c83c2224742cc70d8d628b6b1e57b0bfc3d67c55543fc8`. Changed 416 resources, including 111 compressed twins and 1,999 scene-label instances. No executable changes.
- Movie-inclusive test ISO also built; whole-disc comparison confirms only MOVIE002 differs from the text ISO. SHA-256: `0c8e8088a9ed4499d0f3071c76b627b52114a16432346bfadb1ea07a88a5a170`. Both local ISOs are 4,447,076,352 bytes. No release upload or in-game navigation performed.

## 0.1.35 — 2026-09-24

- **Hikaru's pilot label.** The six VF-1 Hikaru units (2814010/11/30/31/60/70) now show "Hikaru" above their shouts. Their PPN1 table is 48 bytes and the standard layout leaves 4 bytes for text, so the game's own string lookup was located in SLPS_257.84 (routine at 0x1b60c0, reached from the VMD chunk loader's PPN1/PMS handlers): it binary-searches the range index at +28 and reads the pointer array at the offset stored in header word +20, and never reads header words +4, +8, +16 or +24. `rebuild_compact()` in `tools/build_shouts_patch.py` therefore moves the one-entry pointer array into the unread word +24, freeing 8 bytes at +40 for "Hikaru\0". `game_lookup()` mirrors the routine and is asserted on every rebuilt name table (and agrees with the parser on the stock tables). With that, no unit label, pilot label or shout row is skipped: 101 shout tables, 102 unit labels, 109 pilot labels.
- Same content as 0.1.34 otherwise (rebuilt from 0.1.33 with the same inputs). The 0.1.34 draft release is superseded.
- Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256 (pycdlib layout): `1fff95f1fa0f89b03fe5485238a184de60a8157ba950266e91dd8b82e994243c`; `ACE3-English-0.1.35-movie-test.iso`: `9238028ab8e579ff9d308c68114ab1db384248bbadac686c3beff4bec6843987`. Original-layout release discs: `15f69e6ca194b8f8a58ca8e0cc84b54e946923b1efe732345015a81443f61da3` (text) and `db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c` (movie), 4,452,986,880 bytes; xdelta 46.5 MB / 130 MB. Not runtime-tested.

## 0.1.34 — 2026-09-24

- **Pilot battle shouts.** The per-unit shout tables (PMS chunk of the unit model resources 28xxxxx and their packed twins 48xxxxx) are English for 101 of 101 units: 4,256 distinct rows (7,198 on-disc instances, index rows 12197-16452) translated by 13 Sonnet translators and checked by 13 independent Sonnet reviewers (55 review files, 104 meaning fixes: reversed "let's go home" invitations, wrong addressee on "if they start it, take it", first-person vows turned into commands, a "no more pointless fighting" polarity flip, and the like). Each table is rebuilt in place inside its own chunk, so every row had a hard byte budget; ten of Asuham's and Gain's longest lines were shortened by hand to make the last three tables fit. The shared alert "Enemy reinforcements!" (dialogue_04005, five VF-1/Queadluun-Rau tables) and the one-character stub row of Izumi's Aestivalis are covered by `batch_shared_04005.json` and a literal in the builder.
- **Unit and pilot labels in the same resources.** FNM (target label, 102 units) and PPN1 (pilot name above the shouts, 103 units) rebuilt from the locked roster spellings; `names_034.json` adds Dragonar-1 (Lifter) and the leftover A.C.E.2 pilots Kou, Duo and Zechs. Not done: the six VF-1 Hikaru units (2814010/11/30/31/60/70) keep the Japanese pilot label 輝 because their 48-byte table leaves 4 bytes for text and "Hikaru" needs 7; growing the chunk would shift the model data that follows it, and the executable search for a safe compact table layout was inconclusive.
- **Series names.** Table 3031 (the source-work line under Encyclopedia entry titles and in the in-mission Terms) in the four gameplay bundles: 18 official English titles (`ui_034.json`).
- **Encyclopedia.** The three on-disc rows still reading "Kizz Munt" now say the locked "Kids Munt" (table 3019 row 55 in bundles 4002050/54/57).
- Glossary: 18 rulings from the wave recorded in `terms_028.json` (psycommu, Category F, Getter Rays, Overskill, London IMA, Zaku/Gouf, Plamo Spirit, Omega 1, Turn A terms, the Yarf/machine-men/Getter Wing provisional readings).
- Still Japanese: ability names (table 3079), the "battle stations" banner texture, MOVIE003/MOVIE006 burned-in subtitles, the six Hikaru pilot labels.
- Built the ISO and verified all 10,344 archive payloads and 133 disc files; SHA-256 (pycdlib layout): `4c200c72cf655701e00b93f716ebb0428a2535f032b9c4d59b0efb12b9c48215`; `ACE3-English-0.1.34-movie-test.iso`: `6244ca5753aad74e8a6e92df9e1315e1d85b934dadb714b80a1692933a6039b8`. Original-layout release discs (`tools/relayout_disc.py`, DATA.BIN now +5,910,528 bytes): `1f0b768086f7220913b94805395b204955cd26584e13f246ee43b7aaa3d0b8c2` (text) and `6efc232ec2d9931713bfcc09565880b8931a14eb5c3de8b624c408cf6c457fca` (movie), both 4,452,986,880 bytes. xdelta patches: 46.5 MB (text) / 130 MB (movie), up from 4 MB / 87 MB, because the 111 repacked LZSS twins (48xxxxx) are byte-different from the original encoder's output even where the content is unchanged; a splice-preserving repack would bring this back down. Not runtime-tested.

## 0.1.33a — 2026-09-23 (corpus only, no disc built)

- Name-script pass: "Kizz Munt" -> "Kids Munt" (King Gainer Wikipedia) in `encyclopedia_021_b.json` (entry body and name) and both copies of the entry in `encyclopedia_022.json`; the dialogue batches, scenes and review records already carried the corrected spelling or document the ruling. "Kids Munt" is now a locked, do-not-touch name in `work/glossary/terms_028.json`. The Encyclopedia text on the 0.1.33 discs still shows the old spelling until the Encyclopedia is rebuilt in a later build.

## 0.1.33 — 2026-09-23

- **Dialogue pass complete.** In-mission dialogue for the remaining fourteen live scenes: missions 17B, 18B, 19B and 20-29 (2002230-2002350) plus the second table of mission 25 (2002311), in all four copies (11,708 row instances; index rows 7412-7608, 7846-7961, 8031-8214, 8696-8891, 8955-9146, 9215-9387, 9615-9813, 9814-9991, 10307-10606, 10637-10781, 10886-11057, 11058-11238, 11256-11420) with their HUD labels; Global Meetings 17B-20 and 21-29 (13 scenes); the last six briefings 4003761-4003811; the 29 short Free Mission / training briefings 4003881-4003921; Situation Archives 4003972/982/992; hangar conversations 4004683-4004733 (6 scenes, including the 132-row finale). 912 window rows. Same pipeline (Sonnet translator, independent Sonnet reviewer); about 45 meaning fixes (e.g. a "who gets attacked" reversal, invented pronouns for untagged pilots, "Kudan's Limit" corrected to the locked "Limit of Questions", a cover-story causality, "It's coming" vs "It's here" for the Shin Dragon's arrival) and ~50 glyph rewordings. Eight meeting/archive rows and one HUD placeholder (a fullwidth x) were shortened or mapped by hand to fit.
- Every mission slot (35), every meeting, briefing, archive and hangar talk is now English. Still Japanese: per-unit pilot battle shouts (28xxxxx/48xxxxx), ability names (table 3079), enemy target labels, the "battle stations" banner texture, MOVIE003/MOVIE006 burned-in subtitles. Encyclopedia still says "Kizz Munt" where dialogue uses the wiki spelling "Kids Munt".
- New terms this wave: Tripartite Alliance, Ginga (Dewey's flagship), Priest Norb, Swan, CFS, Porolocca / Pororoca, Vodara Shrine, Michiru Saotome, Lalah Sune, Geara Doga, Psycho-Frame, Oversense, Funnel, Marshal (Char's 総帥), New Order, Nergal Dock, A-class Jumper, Distortion Field, Konpei Island, heart's voice (Planetta), mobile weapon.
- **Release layout.** The pycdlib-mastered discs place almost every file about 1.7 GB from its original position, so a whole-disc xdelta against the Japanese image came out at 1 GB. New `tools/relayout_disc.py` rewrites a built disc onto the original disc's file order (original metadata prefix and tail; only DATA.BIN grows, so files after it shift by 4,222,976 bytes) and verifies every file byte-for-byte; the xdelta of that disc is a few MB (text) or ~87 MB (with the re-encoded prologue movie). The release patches are made from these original-layout discs, which have not been boot-tested yet; the pycdlib layout was.
- Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256 (pycdlib layout): `583f8c22b4e26a276476adf2c85d91ac6fda9a15e527a1b24f32842a709ffddb`; `ACE3-English-0.1.33-movie-test.iso`: `691233d6fab07f0cd09f692c8cddfda3d8e3743deebede54d52dad992fac208a`. Original-layout release discs (`tools/relayout_disc.py`): text-only `2ab24afc28efc77b80458fd2bf5f7e948147305eab5dab82402a50b93d4de78f` (4,451,299,328 bytes; `ACE3-English-0.1.33.xdelta`, 3.96 MB), with movie `563433ddb4101cd9f638305f874e09f40a603fab76c6e98eadf38708ee26589c` (4,452,253,696 bytes; `ACE3-English-0.1.33-movie.xdelta`, 87 MB). Repository pushed to github.com/retro-trans/ACE-3; release notes in `work/release/RELEASE_NOTES_0.1.33.md`. Not runtime-tested.

## 0.1.32 — 2026-09-23

- **Missions 13, 14, 15, 16 and 17A, 18A, 19A**: in-mission dialogue for scenes 2002160-2002220 in all four copies (4,240 row instances; index rows 4864-5023, 5223-5317, 5534-5714, 5863-6044, 6396-6548, 6683-6832, 7034-7153) with HUD labels; Global Meetings 13-16 and 17A-19A; briefings 4003681-4003751 (8); hangar conversations 4004593-4004673 (9). 616 window rows. Same pipeline as 0.1.31 (Sonnet translator + independent Sonnet reviewer per scene). Meaning fixes from review include a reversed "who gets attacked" in the missile-defence orders (14), the shuttle-explosion cover story in the Inez backstory (15), a mistaken "should never have happened" tense (17A), "New Order" as Neo Zeon's slogan (18A) and pronoun removal for a pilot whose gender rests only on sentence particles; about 40 glyph rewordings in window scenes.
- One more shared line ("What!?", row 3422) supplied via `batch_shared_01866.json` for the mission 15 scene.
- New locked terms recorded this wave: Tripartite Alliance (三者連合), Kids Munt (King Gainer Wikipedia; the Encyclopedia still says Kizz Munt), Overskill, Swan (the Beams' ship), Common folk (Byston Well), Aura Battler, Aura Road, Get Machine, Archetype / Scub / Limit of Questions, Yurika Misumaru, Cyber Newtype, Colonel Dewey, New Edwards Base, Dorchenov, Sharon Apple, Konpei Island.
- Coverage: missions 01-16 plus 17A-19A (23 of 35 slots); meetings 01-19A; hangar talks through 4004673 (mission 26 slot). Remaining: missions 17B-19B and 20-29 (scenes 2002230-2002350), meetings 4003230-4003350, briefings 4003761-4003811 and the short 4003881-4003921 set, archives 4003972/982/992, hangar 4004683-4004733.
- Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `dd4286e3a8d8c7d28ab231c3f3dce0bbf0baf285faa17f16c74bb3e8495b3315`. `ACE3-English-0.1.32-movie-test.iso`: `34ee4b52f6e933625e6208d85fc7644eb1c707b46fb5b58423144e530342f274`. Not runtime-tested.

## 0.1.31 — 2026-09-23

- **Missions 08, 09A, 10A, 11A, 09B, 10B, 11B, 12B**: in-mission dialogue for scenes 2002080-2002150 in all four copies (4,860 row instances; index rows 2563-2702, 2868-3039, 3230-3365, 3549-3703, 3803-3937, 4202-4331, 4398-4541, 4656-4797) with their HUD labels; Global Meetings 08-12B (4003080-4003150); briefings 4003551-4003671 (13 scenes); hangar conversations 4004473-4004583 (12 scenes). 776 window rows. Every row translated by one Sonnet agent and meaning-checked by a second; 30-odd meaning fixes in total (e.g. a reversed "convenient/inconvenient", "commoner" -> the Byston Well "Common folk", an invented "sir", "Domepolis police", Invader capitalised as the faction name), plus about 60 glyph rewordings (lowercase j/q) in window scenes.
- **HUD labels are now generated**: `tools/hud_labels.py` translates the 555 objective/warning/nav labels of all 28 remaining live scenes from a phrase table (wording follows 0.1.21) into `work/translation/en/hud_labels.json`; every label fits the 480-unit HUD budget. `tools/build_wave_patch.py --version X --base Y` builds any later wave with the 0.1.29 machinery.
- Window wrapping: a <color> span may now break across lines in meeting/hangar windows (the window keeps the colour); <book> links still stay on one line. Seven rows that exceeded three lines were shortened by hand.
- One shared line ("Like I'd let you!", index row 1866) first stored in a leftover ACE2 scene but used by Mission 09B is supplied by `batch_shared_01866.json`.
- Process note: several Sonnet agents ran `find /` and `grep -r work/` (which recurses into the 4 GB discs); the orphaned processes were killed and the agent briefs now forbid such searches.
- Open terminology: the Encyclopedia says "Kizz Munt" where the King Gainer wiki has "Kids Munt" (dialogue uses Kids); "aircraft silhouettes" (機影), "direction indicator", "drone unit"/"unmanned support ships" have no locked term yet.
- Coverage: missions 01-12B (16 of 35 slots), meetings 01-12B, hangar talks through 4004583 (mission 20). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `ea511b93830cf064940cd16befbbe40162bc6b07da287c99995b9ddf14b04a79`. `ACE3-English-0.1.31-movie-test.iso`: `b1ba65574136078d3413f1990dc78a7f15564ab4aa5d0ff0775c534b14167059`. Not runtime-tested.

## 0.1.30 — 2026-09-20

- **Mission 07 (Destroy Shin Dragon) in-mission dialogue**: scene 2002070 in all four copies (1,064 row instances) with its 26 HUD labels (mothership/Tower/Gekko/Nadesico B damage warnings, objectives). Index rows 2215-2454 translated and independently reviewed (240 rows; one meaning fix, row 2374, where a merged sentence left "it" pointing at the wrong thing). Row 2212 was reworded after two reviewers independently read it as a muttered curse about Saotome rather than direct address. Rows 2438-2454 are leftover ACE2 material (Albion, Preventers) and are not inserted.
- Built with `tools/build_030_patch.py`, a thin wrapper over the 0.1.29 builder; the repainted caption pictures are recognised as already done. Runtime questions carried over: post-battle conference rows had hand-placed line breaks in Japanese and are now wrapped by the builder (460 units, at most four lines).
- Dialogue coverage so far: missions 01-07, meetings 01-07, hangar talks 01-08. Translated and reviewed index rows: 1-2454 (of 16,973; several hundred of those are ACE2 leftovers).
- Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `12a1f700210c25c81efc1f61b5160cc588799dc9183b79daecd92bad2a4d0779`. `ACE3-English-0.1.30-movie-test.iso`: `b02065e5ac844ae6924b0c9348350842e89598909b8337ee054c5c54de5355d8`. Not runtime-tested.

## 0.1.29 — 2026-09-20

- **Global Meeting picture captions are now English** (user captures: Ra Cailum / Bright Noa, Ixbrau / Barrel / Faye, Nadesico B / Ruri Hoshino). The captions are not text: they are painted into 256x256 8-bit indexed pictures stored inside the 4003xxx meeting, briefing and archive files. 80 distinct pictures exist; 37 carry captions (79 captions, 56 picture instances in 34 files). `tools/meeting_captions.py` finds each caption's glyph rows and columns on its bar, replaces the glyphs with the bar's own row colours, draws the locked English name (Georgia, 15 px, shrunk only where a bar is narrow) and maps the result back to the picture's own palette. Header, palette, size and every pixel outside the caption rows are unchanged; before/after proofs are in `work/ui/meeting_captions/`. Two new spellings from research: **Deins** and **Gewei** (Giganos metal armors). Tight bars, abbreviated: "Martian Succ.", "New Fed. Main Force", "VF-1A Hikaru / VF-1A Max / VF-1S Fokker".
- A test caught a real defect before the build: the erase band drifted upward for the second caption on the same bar and would have smeared part of a portrait. Fixed; the test now requires every changed pixel row to lie inside a caption band.
- **Dialogue pass, second tranche** (each with an independent review): meetings 05, 06, 07; briefings 4003511/521/531/541; Situation Archive "History of the Other World / The Nadesico's Situation" (90 rows, no meaning fixes, one row shortened to fit three lines); hangar talks 4004443/453/463 (135 rows, 1 fix); in-mission scene 2002060 (Mission 06, Support the Exodus) in all four copies with its HUD labels (index rows 1895-2214 translated and reviewed, 320 rows, 3 fixes). Rows 2064-2208 are more leftover ACE2 scenes (0083 naval review); translated in the corpus, not inserted.
- Rulings recorded in `work/glossary/terms_028.json`: "Siberian Railway" also for the characters' clipped nickname (the coined "Sibe-Rail" was withdrawn by review); Barrel's rank is "Ensign"; "Gauli Team"; "high priest"; Eureka Seven motto in its official dub wording; "quick turn" keeps the released tutorial term.
- Still open: the briefing "battle stations" banner (a texture not yet located); pilot battle shouts in 28xxxxx/48xxxxx unit resources; ability names (table 3079) and enemy target labels; caption tables 3061-3063 (unit/ship labels whose on-screen use is unknown).
- Five new tests pass (`tools/test_029_patch.py`). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `34805721a1387bb07e6e31abe574c66d8909fc644377d2d1d01a5a1d49c71630`. `ACE3-English-0.1.29-movie-test.iso` adds the English prologue movie: `1d71599a0eed8bccded5b353319ef43b64c2061564f8de2db0f9567602772f34`. Not runtime-tested.

## 0.1.28 — 2026-09-20

- **Garbled real-time story demos fixed** (user capture: speaker "??a?u", body "atteedoyoutnkyoure"). The in-mission demo player is bundle **1200011**, which carries its own font; it was the only font on the disc that never received the Latin glyphs (it had only `abdeknoprtuy`, `EMORSZ`, digits and a few signs: exactly the letters that showed). It now has all of printable ASCII, by the same alias/supplement method as the other bundles; every original glyph bitmap is preserved. A disc-wide survey (plain and packed resources) found no other font left unpatched.
- **Portrait chatter re-wrapped at 400 units** (was 460): the user's capture showed "The two units from Project Super No…" running under the wingman icons; the visible part measures 412 units. Only `<op()>` rows use the narrower width; event/demo-window rows (`<on()>`) keep 460. The five 0.1.21 scenes are rebuilt from their untouched stock tables, so they do not grow a second appended table.
- **Table 3013 (eight gameplay bundles): mission Results screen, HUD state labels, group labels, real-time demo footer and the Comm tag** — 33 rows, wording taken from the released menu-side Results screen and demo footer. **Table 3090 (three menu bundles): all 125 Movie Viewer titles**, with locked unit/character spellings. Independent review 157/157 rows: no meaning errors; applied `Mothership`, `Ally 1/2` (matches the deployment screen) and added `D.O.M.E.`. No text buffer grows.
- **Start of the full dialogue pass.** Inserted, each with an independent meaning review: meetings 01, 03, 04; briefings 4003471/491/501; Situation Archive "Unidentified Life-forms" and "Baldora Drive" (93 rows, 3 fixes); hangar conversations for missions 01–05 (4004393–4004433, 142 rows, 2 fixes); in-mission scenes 2002040 (Mission 04, Freeden/Frost brothers) and 2002050 (Mission 05, Gekko) in all four copies with their HUD labels (dialogue index rows 1266–1825 translated and reviewed, 560 rows, 7 fixes). Rows 1447–1602 and 1799–1825 turned out to be leftover ACE2 scenes (Chulips, GP02, Albion); they are translated in the corpus but not inserted.
- New pipeline for window scenes: `tools/scene_source.py` (console-only source), `tools/speaker_lookup.py`, `work/translation/en/scenes/<id>.json`, `tools/seal_scenes.py` (binds reviewed rows to source hashes), `tools/build_028_patch.py`. Hangar-demo files end in an unpadded chunk, so they get a tail-preserving rebuild.
- Name-script pass: the one released "Exbrau" (meeting 02) is now "Ixbrau"; `meeting_terms_015.json` corrected.
- Found but not yet done: the meeting picture captions (Ra Cailum / Bright Noa …) are painted into 80 picture textures, about 37 of which carry captions (repaint tool in progress, `tools/meeting_captions.py`); the briefing "battle stations" banner is not text either; pilot battle shouts live in per-unit resources 28xxxxx with packed twins 48xxxxx; ability names (table 3079, 330 rows) and enemy target labels are still Japanese.
- Risks only the game can settle: bundle 1200011 grows by 1,024 bytes; hangar-demo windows now hold up to 120 characters where stock never passed 60; 4004xxx files grow (first time these are enlarged).
- Six new tests pass (`tools/test_028_patch.py`). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `a1e05e316a65d54dc2d66265ce9d7de682c5f2de2d70b313d9ca33c1eda4d6b7`. `ACE3-English-0.1.28-movie-test.iso` adds the English prologue movie: `8bfc24420b658187ab51f54867f0a06891bcea0b8323222615271d8c440a2067`. Not runtime-tested.

## 0.1.27 — 2026-09-20

- **0.1.26 froze the same demo at the same address as 0.1.25, so the "scene grew by 544 bytes" diagnosis below was wrong** (or at least not the cause). Both are withdrawn and renamed `…-WITHDRAWN-freezes-stage1-demo.iso`. The real cause was found by reading the game's own unpacker out of a save state's RAM (EE code at 0x0023E950; `tools/mips_dis.py` is the small disassembler used): while fewer than 4,096 bytes have been written, a back-reference's field is an **absolute offset from the start of the output**; only after that does the window base slide, making it "4,096 minus distance". `packed_resource.py` had used the sliding rule everywhere. It still decoded stock files almost correctly, which hid the error, but every early reference it *wrote* pointed at the wrong bytes, so the first bytes of the scene, its chunk header, unpacked wrong and the game walked off the end of memory (load from scene + 0x01001AF0).
- With the rule corrected, stock resource 701009 unpacks to **exactly** plain resource 4010, byte for byte; the 2,113 "small differences" reported in 0.1.25 were decoding errors of the old codec, not a variant scene. A step-by-step transcription of the game's decoder is now part of the tests and must agree with the codec on both the stock stream and the newly packed one.
- 0.1.27 is otherwise 0.1.26 as designed: built on 0.1.24; the English crawl rebuilt inside the original 2,304-byte table in both copies of the scene (packed 701009 and plain 4010), no size or offset changed anywhere, slot index cut from 200 to the 81 used IDs, tightened reviewed wording laid out inside the original span (50 lines, last on the original last slot). The packed resource is padded to the stock packed size.
- **Confirmed by the user in PCSX2 (2026-09-20, `0.1.27-movie-test`): the history crawl now plays in English and the demo no longer freezes.** That settles both open points: the 81-slot index is accepted and the renderer follows the slot pointers. It is also the first runtime proof of the packed-resource codec.
- Nine packed-scene tests pass (four in-place, four codec/packed, one transcribed-decoder cross-check). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `13d2c562bc4f5c37357141d1898d2bc4ea40aa223046b84d05b469b9eabd99d0`. `ACE3-English-0.1.27-movie-test.iso` adds the English prologue movie: `fa2f67f787a5a6392254c7ccc860a9668da2183711a0a3e86f799e9ad9a23c96`. Not runtime-tested.

## 0.1.26 — 2026-09-20

- **0.1.25 is withdrawn: it freezes the Stage 1 ending demo** (user report; PCSX2 log: TLB miss, load from 0x020226B0 at pc 0x0012AFF0, then null-pointer loads). `ACE3-English-0.1.25.iso` was renamed `…-WITHDRAWN-freezes-stage1-demo.iso`; the 0.1.25 movie-test disc was still open in the emulator and keeps its name. Do not use either.
- Cause, as far as it can be told offline: not the compression. The repacked stream uses nothing the stock packer does not (same reference range, lengths 2–16, overlapping copies, references before the start). What changed was the scene's size: the English table made the unpacked scene 544 bytes longer, and the scene's chunks are fixed up with pointers after loading (in RAM every large chunk differs from the disc in its pointer fields), so everything behind the enlarged STUF chunk moved. The same growth has sat in plain resource 4010 since 0.1.12; it never showed because the demo loads the packed copy.
- 0.1.26 changes no size or offset anywhere. Built on 0.1.24. The crawl table is rebuilt inside its original 2,304 bytes in both copies of the scene (packed 701009, which the demo loads, and plain 4010, which returns to its original size and layout). To make room the table's slot index is cut from 200 to the 81 IDs the Japanese crawl uses (IDs 82–200 were empty), and the English is laid out inside the original span, IDs 11–81, so the scroll length is unchanged: 50 lines, last line on the original last slot, widest line 470 units, 1,732 of 1,940 available bytes. The packed resource is padded to the stock packed size.
- The crawl wording was tightened about 12% for this (`opening_history_compact.json`; the fuller 0.1.12 text stays in `opening_history.json`). Independent review of 16/16 paragraphs against all 39 source rows: three defects fixed ("among" misread the war and an added "other"; a stray lowercase j in "joint"; a dropped "begins" in the military reorganization), uncertainties recorded. One heading moved from slot 78 to 77 so the last paragraph still ends on the original last line.
- Risks that only the game can settle: whether shrinking the slot index from 200 to 81 is accepted, and whether the crawl renderer follows the slot pointers (if it still showed Japanese that question would be moot, since no Japanese crawl text remains in either copy).
- Four new regression tests (no size changes; only the 2,304 table bytes differ and every chunk keeps its offset; English inside the original span; both copies carry the same table). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `411e6d7292334e786b8c32b4664cd10e3a0a9579127d4843679612891fb416c0`. `ACE3-English-0.1.26-movie-test.iso` adds the English prologue movie: `99e7cff0e11a5a0ee5babcb6e3430700c09db3e1314913f132122ae46419f6f4`. Not runtime-tested.
- Lesson recorded for all later work on packed or chunked scenes: never change a scene's size; rebuild text inside the space it already has.

## 0.1.25 — 2026-09-20

- **Root cause of the Japanese history crawl found.** With the user's permission PCSX2's disc-read logging was switched on for one run (and switched off again afterwards). `tools/cdvd_reads.py` maps every logged read to its file and DATA.BIN resource: before the Stage 1 ending demo the game never reads resource 4010 at all. It reads resource **701009**, which is an LZSS-compressed variant of the same scene (1,690,816 bytes packed, 3,377,616 unpacked, starting `PRM`), and that copy still held the Japanese crawl table. Every earlier conclusion about this crawl (0.1.12 "translated", "gone from 0.1.23", "stale save state", the 0.1.24 pool theory) was wrong for the same reason: the text was only ever looked for as plain bytes.
- New codec `tools/packed_resource.py`. Format: `00 01 00 00`, unpacked size as big-endian u32, four zero bytes, then LZSS: flag byte with eight items, least significant bit first; clear bit = literal; set bit = two bytes, field = b0<<4 | b1>>4, length = (b1&15)+1, copy starts 4096−field bytes back, bytes before the start read as zero. Settled by brute force against 701009 and its plain twin 4010; the decoder consumes the stock stream to within its zero padding, and the encoder round-trips.
- 0.1.25 unpacks 701009, replaces its STUF text table with the English crawl table built in 0.1.24, repacks it and replaces the resource. Every other chunk of the scene is byte-identical. Unpacked size grows by 544 bytes (as plain 4010 did); packed size shrinks by 2,112 bytes. No other 7xxxxx resource contains the crawl.
- **Wider consequence, not yet acted on:** 4,138 of the 10,344 resources are packed this way, including 1,980 in the 32xxxxx range and 905 in the 20xxxxx range where scene copies live. The dialogue index (0.1.6) and every "only copy on the disc" search looked at plain bytes only, so packed scene copies have never been indexed, and where the game loads a packed copy the inserted English will not show. A survey that unpacks first is the next job.
- Four new regression tests (decoder consumes the stock stream exactly; encoder round-trips including empty, tiny, repetitive and real data; crawl English and Japanese gone; all other chunks identical). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `9e25f9dc16fe86310abddb75b26657b12d2aed5d8174b5c54b764ef843311ac6`. Also `ACE3-English-0.1.25-movie-test.iso` (adds the English prologue movie, confirmed by the user to play to the end with good picture): `819c00e09f0261d3c190f7d778f01ba4477b06b9f0fdb0f95aa5b0ab0b127f70`. The crawl itself is not runtime-tested yet.

## 0.1.24 — 2026-09-19

- Fix attempt for the opening history crawl, which the user still sees in Japanese on 0.1.19+ at the end of Stage 1 and in the Movie Viewer entry "01 Probe Unknown Lifeform / Prologue 2". That demo is engine-rendered: its spoken line "Please let this be the end of it!!" comes from scene 2002010 and already shows in English; only the crawl does not.
- Cause as far as it can be established offline: 0.1.12 kept the Japanese string pool of the crawl table (resource 4010, STUF, text 3) directly behind the pointer array, appended the English pool after it and redirected all 200 slot pointers. The pointers are correct and parse to English, yet the game shows Japanese, so the crawl renderer evidently does not follow them; the likeliest reading is that it walks the string storage from its start. The table is now rebuilt with the 68 English lines stored in slot order from the pool start and the Japanese pool removed. Rows, IDs, slots and every other chunk of the scene are unchanged; the resource shrinks by 1,440 bytes.
- **Finding after the user's test (2026-09-20).** The user reported the crawl still Japanese on `0.1.24-movie-test` and saved a PCSX2 state with the crawl on screen. The state's EE RAM holds the complete Stage 1 resource 4010 at 0x01020BC0 in its *original* layout: the crawl table is byte-identical to the original disc's, the STUF chunk declares 2,384 bytes (0.1.12–0.1.23: 4,368; 0.1.24: 2,928) and the chunks behind it sit at the original offsets. A corrected whole-disc search (`tools/find_text.py`, which rewinds before scanning) finds no Japanese crawl text anywhere on the 0.1.24 disc. The same RAM also holds 0.1.22/0.1.23 text ("Tresor Institute", "Ex-Giganos Officer"). So the Stage 1 data in that session was loaded from an original or pre-0.1.12 disc and carried forward in emulator save states, while menus and gameplay bundles were reloaded from newer discs. The crawl has therefore never actually been tested from a patched disc: neither the 0.1.12 pointer redirection nor the 0.1.24 pool rewrite is confirmed or refuted. It needs a full boot and a memory-card load, not a save state.
- **Second correction (2026-09-20).** The PCSX2 log shows the "carried forward in save states" explanation above is wrong too: both captured states were saved 74–76 s after a *full boot* of `0.1.24-movie-test.iso` with no state load in between. The facts that stand: (1) the booted ISO is byte-identical to the verified build (SHA-256 re-checked) and contains no Japanese crawl text anywhere (two independent whole-disc scans); (2) the game's own archive index in RAM is the 0.1.24 one (entry 4010 = 3,378,160 bytes); (3) yet RAM holds a 3,377,616-byte blob at 0x01020BC0 equal to the *original* resource 4010, including the Japanese crawl table, and the loader's record beside it says 3,377,616; (4) the memory card does not contain it; PCSX2 has precaching, HostFs, cheats and save-on-shutdown all off. Where the game gets those bytes is unknown. The Stage 1 ending demo is scene 2002010 rows 301–308 (English, working) with the crawl between rows 301 and 302. Next step: a PCSX2 run with CDVD read logging, to see exactly which sectors are read before the crawl appears.
- **User test, 2026-09-20:** the English prologue movie (MOVIE002 remux) plays in PCSX2 from the 0.1.24-movie-test disc with English subtitles; this is the first runtime confirmation of the PSS remux. End-to-end sync is not yet reported.
- This is a hypothesis under test, not a confirmed fix. If the renderer walks the pool with a fixed count of 39 lines, the English crawl (68 lines) will appear but be cut short; if it still shows Japanese, the text comes from somewhere not yet found.
- Correction to the previous entry: the statement that the Japanese crawl text was gone from 0.1.23 was wrong. It came from a faulty whole-disc search. A direct check of resource 4010 shows every build from 0.1.12 to 0.1.23 carries both the Japanese pool and the English one.
- Four new regression tests (rows unchanged, pool starts with English and holds no Japanese, strings in slot order, other chunks identical, Japanese table refused). Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `6566c3b9222c46f56d5e4763a1e7a3b4008686dad4922820006c3a1b2535331c`. Also built `ACE3-English-0.1.24-movie-test.iso` (0.1.24 plus the English MOVIE002), SHA-256 `c8077a83f2fb15ecd80a289f6792a60c4267b0e28fef852acc9f9c3eb9dd244d`. Neither is runtime-tested.

## 0.1.23-movie-test — 2026-09-19

- Separate test disc, not a numbered release: 0.1.23 with `/MOVIE0/MOVIE002.PSS` (the Stage 1 prologue) replaced by an English-subtitled remux. All six PSS movies were decoded and inspected first: only MOVIE002 belongs to Stage 1; MOVIE003 and MOVIE006 are late-game movies with burned-in subtitles and are not done; MOVIE001, 004 and 005 have no Japanese text.
- 34 burned-in subtitles were timed from the frames and matched to the reviewed lines of scene table 2002410; the in-picture date caption is covered by a dark strip with the English caption. Video re-encoded to the original's parameters (MPEG-2 MP@ML 640x448p, 29.97 fps, CBR 4.5 Mb/s, VBV 1,835,008, GOP 18/M 3): `ffmpeg -i MOVIE002.PSS -vf "drawbox=x=0:y=356:w=640:h=92:color=black:t=fill,drawbox=x=286:y=303:w=352:h=26:color=black@0.78:t=fill:enable='between(t,29.00,33.20)',ass=MOVIE002_en.ass" -an -c:v mpeg2video -profile:v 4 -level:v 8 -pix_fmt yuv420p -r 30000/1001 -aspect 4:3 -b:v 4500k -minrate 4500k -maxrate 4500k -bufsize 1835008 -g 18 -bf 2 -sc_threshold 0 -dc 8 -mbd rd -trellis 2 -cmp 2 -subcmp 2 -f mpeg2video MOVIE002_en.m2v`.
- New remuxer keeps the original PSS as skeleton: pack headers, SCRs and all audio packets byte-for-byte, same file size; only video payload and its timestamps change. Offline checks: 9,043 pictures in and out, clean DTS/PTS, zero decode errors, audio bit-identical, no non-video packet changed, ISO identical to 0.1.23 outside the movie extent. SHA-256 `bbf23817bd649f62d7ca9fc81a2093c28aca8fa7469930efa597f3a2ba72bbc6`. Whether the PS2 player accepts it is untested. See MOVIE_SUBTITLES.md.
- Also fixed the preview audio: PSS PCM is interleaved in 512-byte blocks per channel, not per sample; the first preview MP4 had both channels chopped together.
- Open: the user reports the opening history crawl still in Japanese. On the original disc that text exists only in resource 4010, and in 0.1.23 the Japanese is gone from DATA.BIN, so the build and boot method the user saw it on need confirming before anything else is concluded.

## 0.1.23 — 2026-09-19

- Translated every pilot full name and short speaker label in the shared name tables: full names (table 3014, five menu bundles), menu-side speaker labels used by story demos and briefings (3026 in 4002053, 3074 in 4002054; the Japanese "Faye" label in the user's hangar capture) and in-mission speaker labels (3021, eight gameplay bundles). 1,462 text instances in 13 bundles. This completes the 93 speaker IDs left pending in 0.1.11.
- Names are looked up, never freely translated: glossary.json first, then the new sourced research file character_names_021.json (97 characters and factions from three research passes, each with gender, role, source URLs, variants and a confidence level), then speaker_names.json. Generic labels (Operator, Enemy Officer, Fed. Soldier, Martian Successor, ...) are listed in tools/prepare_names_023.py. Two people share one Japanese short label; the character ID decides between Sala (Tyrrell) and Sara (Kodama). The disc labels Gym Ghingham by given name in one table and by surname in another, and the English follows it.
- Open name questions recorded with the research: Harry (nickname label, low confidence; reviewed dialogue still mixes Harry and Hari), Tapp Oceano (wiki) vs Tap Oseano (official Dragonar site), Roybea vs Roabea Loy, Milia Fallyna vs Farina Jenius, Greg Bear Egan. Scene-specific actor labels outside the shared tables are not covered.
- No font, texture, layout, allocation or executable change; every glyph needed already exists. Lowercase j in names such as Gain Bijou uses the known smaller fallback glyph.
- All 90 regression tests pass, including five new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `c8d41638731491c9398ac947a0d169536206b45053eb8d3e2c6d68f9ac778c87`. Not runtime-tested; fresh boot required. Build with `python tools/prepare_names_023.py` then `python tools/build_names_patch.py`.

## 0.1.22 — 2026-09-19

- Translated every Encyclopedia entry at the user's request: all 88 term names and all 88 pages, in the three menu copies (tables 3018/3019) and the four gameplay copies (3028/3029). 1,232 text instances in seven bundles.
- Two translators (44 entries each) researched 86 names and terms with sources; two independent reviewers examined 88/88 entries: no mistranslation, dropped fact, wrong number or invented gender; seven soft fixes applied. Cross-reference links keep their targets and counts, and link text always equals the target entry's English name. Provisional names and open spelling decisions (Baldora vs Bardona, New Federation, First Defense War) are listed in ENCYCLOPEDIA_022.md.
- Pages stay inside every stock maximum measurable offline (17 lines, 443 units per line, 599 bytes per page; labels within 220 units in both fonts). They cannot stay inside the stock glyph count: up to 480 visible characters against 237. The page renderer's capacity is unknown, so the longest pages are listed for testing first. No layout, allocation, font or executable change; gameplay bundles grow about 25 KB each.
- Extended the shared text builder for page text (reorderable link tags, per-row length bound, tags excluded from width, page text excluded from label-buffer sizing). Name research for 97 characters and factions was merged into work/glossary/character_names_021.json for the pending pilot/speaker-name build.
- All 85 regression tests pass, including five new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `e98daceab6473d09c2f57f49d6572a49c110de00778f4652df6eabe8c8cbf600`. Not runtime-tested; fresh boot required.

## 0.1.21 — 2026-09-19

- Inserted five scenes whose dialogue had been translated and independently reviewed for 0.1.6 but never put on the disc: 2002011 (training follow-up), 2002020 and 2002021 (Mission 02, including the Amuro line and the Nadesico B nav alert in the user's captures), 2002030 and 2002031 (Mission 03), each with its 60xx, 3200xxx and 3201xxx copies. 20 resources, 1,948 rows: 438 reviewed dialogue strings and 49 label rows per copy set (some labels pass through unchanged).
- Translated the HUD labels stored beside the dialogue (objectives, damage warnings, reinforcements, mission failed/complete, nav and info alerts, evade hints) using released wording: Objective, Warning, 5 minutes remaining, Mission Failed: Time Over, Destroy/Capture, Gun Ark, Giganos, Nadesico B. Percent signs stay fullwidth; button icons are preserved.
- Found and fixed a wrapping defect before release: the 0.1.7 tutorial wrapper moved spaces and punctuation around inline colour and link tags and could split a link across lines. The tutorial has no inline tags so it never showed. The new wrapper keeps tags glued to their words and link/highlight spans whole. Three reviewed rows whose hand-placed breaks exceeded the four-line window are reflowed; words and commands are unchanged.
- Same relocation as the tutorial; original tables, scripts and commands intact. No font, layout, allocation or executable change. The story-demo conversation in the user's third capture (Faye and Barrel in the hangar) is a different container, resource 4004403 in the operator/speed format used by briefings, and is not covered here.
- All 80 regression tests pass, including five new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `913972cfb4f46d544dd4c90ed0c6cfdc296ec45730dc31af32b9a8b1e0c2dc7e`. Not runtime-tested; window width (460 units, four lines) is the tutorial's measurement. Reviewed batches still mix Harry and Hari for one Nadesico character; a name pass is pending. Build with `python tools/build_reviewed_scenes_patch.py`.

## 0.1.20 — 2026-09-19

> **Correction, same day.** The user reported the opening still in Japanese. Frames decoded from `/MOVIE0/MOVIE002.PSS` show the subtitles ("gentle coercion", the Saint Cruz City caption) burned into the video picture. The claim below that the subtitle "is engine text, not baked video" was wrong: it was inferred from finding the same lines in scene table 2002410 and was never checked against the movie. The 62 translated lines are inserted and harmless, but they are not what this cutscene displays; whether the game shows them anywhere is unknown. Making the opening English means re-encoding the MPEG-2 video (640x448, 29.97 fps, 4.5 Mb/s, audio in private stream 0xBD) with English drawn over the letterbox and remuxing it into the PSS container. Not done.

- Translated the opening prologue cutscene the user captured ("gentle coercion" monologue, evacuation broadcast, Barrel meeting Faye). The subtitle is engine text, not baked video: scene table 2002410 with copies 6410, 3200410 and 3201410. All 62 timed strings and 3 objective labels are inserted in all four copies, 260 instances.
- Same relocation as the tutorial: a complete new table is appended to each scene resource and the header pointer redirected; the original table, script and every command stay intact. No font, layout, allocation or executable change.
- The whole scene was read in order and independently reviewed, 62/62 rows plus the 3 labels as context: no mistranslation; five fixes applied (a three-line technical subtitle relaid to two lines, "Hey, boy!" so the call does not read as an interjection, and three rows where the draft had supplied an object, subject or possessive the source lacks). Uncertainties recorded in review_scene_2002410.json: speakers are inferred from text without video; rows 353/354 are two stored takes of one reply; row 359 looks like a placeholder; rows 360–362 may be out of sequence.
- Subtitles are wrapped at 500 font units and held to two lines, inside the stock letterbox maximum of about 530 units on one line. This is a measurement from one capture, not a proven limit; voice timing commands are unchanged and English reading time is untested.
- All 75 regression tests pass, including five new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `da8a36e5717032afff5e9f5d0a407ebf7291c7e7aa8be7b509170a1e2494c821`. Not runtime-tested; fresh boot required. Build with `python tools/build_scene_patch.py`.

## 0.1.19 — 2026-09-19

- Translated the complete ACE3 mission-title and secret-goal categories (tables 3055 and 3057) in all three menu copies: 67 titles and 35 goals, 306 text instances. These are the Japanese title and secret condition visible in the user's Free Mission capture. The legacy previous-game tables under the same IDs in bundle 4002055 remain out of scope.
- Researched every name first and added a sourced glossary (mission_terms_019.json): Shishiki, Metal Beast, Freeden, Vulture, Frost brothers, G-Bit, Coralian, Antibody Coralian, Norb, the Zone, Exodus, go Hyper. Infinite Mobile Cannon and Kleid are provisional: no official English exists and the fan wiki's forms were rejected with reasons.
- Independent meaning review examined 102/102 rows and every number: no mistranslation, four suggestions applied, uncertainties recorded. Flagged for a later corpus-wide decision: Baldora Drive and Jill Bardona share one kana spelling and are both provisional.
- Titles fit the 290-unit selector and goals two 420-unit lines. Three goals were abbreviated after review so that no text allocation grows; fonts, layouts, textures and the executable are unchanged. The 0.1.18 builder was parametrized for reuse; its 0.1.18 output is unchanged.
- All 70 regression tests pass, including five new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `93d980a938ecd71af03d95d9e1a752dfddf5fe703d6e8863ad01326d2aeb2d36`. Not runtime-tested; fresh boot required. See MISSIONS_019.md.

## 0.1.18 — 2026-09-19

- Translated every remaining modal Help/confirmation message in the shared menu bundles, starting from the user's Combat Records (by series) capture (table 3091, text 12), together with the menus that host them. Complete categories: Combat Records, Encyclopedia menu, Model Viewer, Versus/Multiplayer unit selection, Game, Screen and Controller options, Multiplayer menu, movie sound selection. Partial: Versus menu and Sound options (song titles excluded), Movie Viewer (story movie titles excluded). 786 text instances in 37 table copies across six bundles; 287 reviewed rows.
- Fixed Free Mission labels that overflowed in the user's 0.1.17 capture: Combat Records → Records (also in Multiplayer), Completion Status → Status, Secret Conditions → Secret Goal. Replaced an ASCII percent sign that ended the printf-style 0.1.17 discount prompt with the source's fullwidth sign; the builder now rejects stray percent signs. Option screens use Reset Defaults because Restore Defaults is wider than their button.
- Independent meaning review examined 287/287 rows: no mistranslation, two suggestions applied, uncertainties recorded with the translation. "Ace title" is rendered Ace Series; the VFX volume item is Voice Volume per its own description.
- No text allocation, font, layout, texture or executable change. The first draft would have enlarged 1,204 text buffers (the 0.1.15 hangar-crash mechanism), so four long lines were compressed after review without dropping meaning. Label limits come from the captures (131/156/140/620 font units) and are not proven engine limits.
- All 65 regression tests pass, including six new ones. Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `a19bd7038cfe7204e2ac6fe5aa990e54c487e8e10fc8da84d2cc2e6b4d9c5ddf`. Not runtime-tested; fresh boot required. Only one of the six captures was saved to disk and archived. Mission titles and secret conditions remain Japanese pending glossary research; song, story-movie and encyclopedia text, pilot names and ability descriptions also remain. See DIALOGS_OPTIONS_018.md.

## 0.1.17 — 2026-09-19

- Translated all 181 non-null deployment category entries in all three copies. Includes deployment/player/ally selection, upgrades, emergency repairs, recruitment, training, statistics, restrictions, confirmation dialogs and button guides.
- Translated all 18 series labels in their related indexes (19 source variants) and matching labels in sound settings; translated Barrel Orland's full name in all five full-name tables. 827 reviewed text instances across 19 tables in five bundles. Unrelated pilot names, ability descriptions and sound-setting text remain outside this category.
- Checked native font widths, nine-line help dialogs and substitutions of all primary roster names and ten-digit point costs. Shortened narrow training labels to Ground, Space and Basics; full actions remain in their descriptions. Kept the game's Japanese name-sort behavior explicit. Preserved all button markers, discount icon and format arguments.
- Relocated English strings while preserving original pools, IDs and null slots. No font, executable or allocation changes: every new label fits the 0.1.16 bounds. All 59 regression tests pass, including five new deployment tests. Runtime testing is left to the user.
- Built the ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `9194ff8b9d41728aeebce03c9e57a2cf9ccb789e1188f634006939e79e6f5663`. Fresh boot required to load the new text.

## 0.1.16 — 2026-09-19

- Diagnosed the post-briefing hangar crash from the user's paused 0.1.15 EE RAM and debugger registers. Menu 24's 37-widget array was allocated, but its subsequent 5,120-byte buffer allocation failed with only 3,840 bytes remaining. Initialization returned before setting widget callbacks, and execution attempted to call stale asset bytes at PC `0x61a1adb1`.
- Replaced the blanket 128-character capacities introduced in 0.1.9 with bounds derived from 615 existing translation pairs. Adjusted 2,512 fields across 19 shared UI bundles, using 32–115 characters while retaining stock larger allocations and the 255-character flight/help buffers. No executable hooks or translated text changes.
- Verified the entire ISO byte-for-byte against 0.1.15 plus only the planned fields; 54 regression tests passed. SHA-256: `32d4316d77f4826cd13bc0fe19a9b5339d28ad23cfa31330d0916dff6deb23c0`.
- User confirmed the crash is fixed and supplied successful deployment/player-selection screenshots. The normal emulator log confirms a fresh 0.1.16 boot preceding that report. This verifies the reported route, not every mission or multiplayer menu. Original save card was not modified by diagnostic work.

## 0.1.15 — 2026-09-18

- Translated the complete Mission 02 Global Meeting and Zentradi/Nadesico support briefing shown in the user's screenshots: 33 scene/title entries. Preserved all glossary links, highlighting, speaker commands, topics, map markers, camera movements and picture cues. Kept three body lines within 460 font units and the inherited 128-character allocation.
- Translated the complete ACE3 victory/defeat category: 152 slots / 40 distinct labels in three copies, plus matching condition fields in 264 scene resources. Updated Amuro Ray, Faye Rochenante and Kouichiro Misumaru in all five relevant speaker-name tables. Total: 904 translated instances across 271 resources. Earlier ACE2 mission tables are excluded.
- Appended new text and relocated scene tables without editing original scripts, executable, fonts, textures or allocations. Added sourced terminology, original screenshot metadata, an English reading copy and four regression tests. Other meeting/briefing dialogue, glossary descriptions and small baked thumbnail captions remain Japanese; in-game rendering and cue timing are unverified. See MEETING_BRIEFING_015.md.
- All 50 regression tests pass, including complete scene/category coverage, ordered controls, unchanged non-target assets, script-preserving relocation and rejection of oversized dialogue.
- Built ISO and verified all 10,344 archive payloads and 133 disc files. SHA-256: `ef63009060685af7d873fba6dfdcdcdcc1e70cdfe5d475d7d797e7b7e9378bd0`. Runtime testing remains pending; fresh boot required.

## 0.1.14 — 2026-09-18

- Completed Intermission update notices: all 21 non-null rows reviewed, 14 translated entries in each of three copies. Covers units joining/leaving, evolution and recruitment availability, weapon/armament additions, Model Viewer and Encyclopedia additions, Free Mission and Versus unlocks. Inherits the complete Intermission menu, help and controls guide from 0.1.13.
- Added 197 reviewed unit-name rows (193 distinct source labels), including pilot, equipment and transformation variants. Applied 1,711 entries across 17 tables in six bundles; all primary roster/name-table copies are covered. Unmatched enemy/object names in the alternate results list remain Japanese.
- Verified runtime notification lookup uses 103 roster IDs from resource 100204, table 3077 and three special table 3025 names. Checked all 626 expanded/static notice combinations per copy against the 410-unit line width, 64-byte formatted-record size and 255-character six-line widget. Maximums: 409 width, 38 encoded bytes, 233 aggregate characters. Added regression coverage for the encoded buffer limit.
- All 46 tests pass. Relocated text while preserving IDs, null slots, original string pools, format arguments and unrelated assets. Reused existing game glyphs; the lowercase j in Nanajin retains the known smaller fallback. Executable and previous menu/pause repairs are inherited. In-game rendering remains unverified; fresh boot required. See INTERMISSION_014.md and the adjacent ISO build report.
- Built and verified all 10,344 archive payloads and 133 disc files with the established Sony ISO9660/UDF metadata repair. ISO SHA-256: `3fbde2017dfa51ba72d1ba7c3bb94362c344f6d197f0c00c1c4457af3c0a66ca`.

## 0.1.13 — 2026-09-18

- Translated complete flight setup and controller-option categories, including all four flight modes, their instructions, inverted controls, unlock/reset questions, and button help. Also translated complete intermission, meeting/briefing, mission-results, both Free Mission variants, and options-root categories containing the related save actions.
- Located all 29 copies of ten selected table IDs across the archive. Reused reviewed memory-card/save-slot/shared-dialog translations in missing copies. Updated 568 entries across 23 changed tables in seven bundles; retained six already translated copies and all dynamic slot/time fields, rank codes and button symbols.
- Relocated English text into appended string pools. Raised both actual flight-help allocations from 200 to 255; other text respects the inherited 128/255 allocations. Checked flight text against the diagram boundary and source line counts. Added missing native-size game glyphs to results/options fonts while preserving original glyph pixels and metrics; no new text uses the small fallback glyphs.
- Independently reviewed all 245 new category rows, recorded terminology uncertainties, added a sourced Wing Gundam Zero Custom glossary entry and provisional Recovery Device entry. Archived four unchanged source screenshots and layout metadata. All 41 focused tests pass, including category coverage, relocation, controls/placeholders and allocation checks.
- Built with the established Sony boot-metadata repair; all 10,344 archive payloads and 133 disc files verified. SHA-256: `c6e8539a46f196b5cb715737f45d917b538d8971c54d89811eebb4811c8d2be6`. The executable, tutorial, history, speakers, controller diagrams and earlier pause/menu fixes are inherited. In-game rendering and navigation of 0.1.13 remain unverified; fresh boot required. See FLIGHT_SAVE_013.md and the ISO's adjacent JSON report for coverage and checks.

## 0.1.12 — 2026-09-18

- Translated the complete opening history crawl in resource 4010, STUF/BND text resource 3: all 39 non-null source rows, grouped into 20 reviewed headings/paragraphs, including the continuation beyond the supplied screenshot and years 058–060.
- Appended a new English string pool and reflowed the full meaning into 68 lines within the existing 200-slot index, with the final text at slot 102. Measured against the gameplay font at a 430-unit width limit. Preserved all other scene chunks, scripts, portraits, timing commands, fonts and inherited translations. Rebuilt DATA.BIN and restored Sony ISO9660/UDF boot metadata with updated file extents.
- Added an independent meaning review, sourced supplemental glossary with provisional terms explicitly marked, full readable English translation, original screenshot provenance, a dry-run builder and three regression tests. All 37 tests pass; all 10,344 archive payloads and 133 disc files verified. ISO SHA-256: `cf91a7007a100a44863d2fdfa4ee4f1e54c8b0b0b0cf870e0aaffbbbacb74f58`.
- The user stopped Computer Use with physical Escape before the new ISO could be runtime-tested. The diagnostic emulator had reached the tutorial on 0.1.11, not the translated crawl. 0.1.12 boot, crawl rendering and complete scroll duration remain pending; the 200-slot capacity is an offline format check, not proof that the original scene timing displays the last reflowed line. Fresh boot required. See OPENING_HISTORY_TRANSLATION.md for the full translation and work/output/ACE3-English-0.1.12.json for build details.

## 0.1.11 — 2026-09-18

- Fixed Japanese speaker labels for 26 glossary-backed characters, including Barrel and Faye. Normalized 36 character IDs in all eight shared gameplay name tables and 839 scene-specific labels: 1,127 translated instances across 847 tables. Scanned all 10,344 archive resources; 93 shared label IDs remain pending research/translation.
- Preserved full short names, ID ranges, null slots, portrait references and dialogue. Ten small Hikaru tables relocate into verified unused archive-sector padding with updated actor pointers and resource lengths. Other name tables keep their sizes. Disc extents, Sony boot metadata, executable, fonts, 0.1.9 capacity fixes and 0.1.10 controller textures remain unchanged.
- Added a glossary-locked manifest, dry-run builder, screenshot provenance and four regression tests. All 34 focused tests pass. The entire ISO was verified against 0.1.10 plus exactly the planned patches. SHA-256: `40267948aa2d3c011caf50751425bf0dd486c5c8baaca8dfaa1a9060de8b5279`.
- In-game verification remains pending. Boot the ISO fresh instead of loading an earlier emulator save state. See SPEAKER_NAMES_011.md for scope, remaining names and the test route.

## 0.1.10 — 2026-09-18

- Translated the complete controller-confirmation diagrams for both Shift and Select: the question and ten labels in each, 22 caption occurrences / 13 distinct strings. Located the baked images in bundle 4002056, textures 50512 and 50513. Select uses Fire / Select Menu; Shift uses Main Fire / Shift Menu. Down / Up are approved compact display variants for Descend / Ascend.
- Rendered captions with the game's own menu glyphs into the existing indexed images. Preserved controller artwork, symbols, leader lines, question icon, borders, palette bytes, texture metadata, archive offsets and executable. Inherited all 0.1.9 fixes. The four related control illustrations contain no Japanese captions to replace.
- Added translation and geometry JSON, a dry-run/preview builder, meaning review, decoded preview images, and two regression tests. All 30 focused tests pass. The builder checks the entire ISO against exactly the two planned texture replacements and records SHA-256 in the output report.
- In-game verification of 0.1.10 remains pending: Computer Use was stopped with the physical Escape key before testing the new build. Fresh boot required; do not load an older emulator save state. See CONTROLLER_DIAGRAMS_010.md.

## 0.1.9 — 2026-09-18

- Fixed the reproduced pause-screen freeze and persistent main/setup label cutoff. Live RAM showed the pause menu writing 1408 bytes of graphics commands into a 1072-byte allocation, followed by repeated DMA-transfer stalls. The old main/setup callback patch did not repair the actual layout allocations.
- Raised undersized text allocations to 128 in 2512 validated UI descriptors across 19 shared startup/gameplay bundles. Preserved larger allocations and non-text records. Restored the two ineffective callback patches to their original instructions. Text, fonts, archive sizes, file extents and Sony boot metadata are otherwise unchanged from 0.1.8.
- Fresh-boot tested in an isolated PCSX2 2.8.2 instance: Campaign/Load are complete; initial setup labels and confirmation footer are complete; the tutorial pause menu opens, resumes gameplay, and opens again. The repaired pause allocation is 14512 bytes for the same 1408-byte draw. No DMA stalls or TLB misses occurred in this route.
- Archived the user's regression screenshots, reproduced failure log, and main/setup/pause/resumed-gameplay evidence. Twenty-eight focused tests pass; every ISO byte is verified against the base plus the planned edits. Build SHA-256: `f9fbb6079caff3f83df7d9db0a646af9f23de0ae4db5d21092113b3455cd4cff`.
- This remains a partial translation. Later missions, multiplayer and unavailable tutorial submenus have not been runtime-tested. Active text widgets now use larger allocations. Use a fresh boot rather than an older emulator save state. See LAYOUT_BUFFER_FIX_019.md.

## 0.1.8 — 2026-09-18

- Translated the complete pause category: 103 slots across all eight gameplay bundles (824 instances), including the pause choices, help descriptions, map legend, options, retry/exit confirmations, game-over and versus variants, and shared controls. An independent meaning review covered all 103 rows. Preserved button glyphs and rebuilt string pools without per-string byte limits.
- Replaced undersized borrowed Latin glyphs with native 19/20-pixel game glyphs where available. Repacked the eight gameplay font atlases within the 1024x512 GS texture slot; preserved every original glyph bitmap and metrics. The pause translations require no 12-pixel fallback glyphs. Lowercase j/q and some uncommon punctuation elsewhere still lack matching native-size donors.
- Retained the 0.1.7 Sony filesystem boot repair, startup translations and tutorial translations. Verified all 10,344 archive payloads and 133 disc files. Twenty-four focused tests pass, including new pause relocation, source-preimage, review-status and icon-preservation checks.
- Built ACE3-English-0.1.8.iso and confirmed startup in an isolated PCSX2 2.8.2 profile, with a saved startup screenshot and no executable-open/TLB failure. The isolated hidden window was unavailable to the UI-control tool, so pause rendering/navigation and the repacked gameplay fonts are not yet visually verified.
- Known outstanding defects: the user-reported main/setup label truncation remains unresolved; the controller confirmation diagram and speaker names remain Japanese. This is a partial translation, not full-game completion. See PAUSE_PATCH_018.md for scope and testing.

## 0.1.7 — 2026-09-18

- Fixed the 0.1.6 pre-title black screen. Detailed PCSX2 logging showed the PS2 BIOS could not open the boot executable in the generic remastered filesystem. Restored Sony's original ISO9660/UDF 1.02 directory and volume structures, updated all 133 file locations/sizes to the translated disc's actual extents, and regenerated UDF checksums. Restored the original volume size and trailing metadata.
- Retained every game payload byte from 0.1.6, including all tutorial translations, font additions, and inherited UI patches. No translation coverage expansion in this repair. Source ISO and released 0.1.5/0.1.6 builds are preserved.
- Reproduced the failure in an isolated PCSX2 2.8.2 profile. A DVD-detection-only correction and duplicate ISO path tables still failed; neither diagnostic is released. Restoring the Sony filesystem boots to the translated startup confirmation with no TLB faults or executable-open failure.
- Added a full-disc payload comparison, ISO/UDF extent agreement checks, checksum tests, failure evidence, and a captured startup screen. Twenty focused tests pass. Startup is checked; tutorial rendering and full gameplay still need testing.

## 0.1.6 — 2026-09-18

- Located the screenshot's exact tutorial line and all four copies of its table. Indexed 16,973 distinct tagged dialogue/window/book strings across 801 tables and 68,079 stored instances, with stable source offsets/hashes rather than a Japanese script export. Legacy/unused material is retained and explicitly distinguished from verified gameplay coverage.
- Audited 278 additional distinct unreferenced string-tail candidates; 1,006 more tail occurrences match indexed strings. No speed commands were found outside DATA.BIN. Untagged and image-based dialogue remains unverified.
- Drafted and independently meaning-reviewed 880 strings in eleven 80-row batches, reading 15 context rows on each side. Recorded uncertain referents, rank conventions, stored-order anomalies, and provisional terminology. Full-game translation remains incomplete: 16,093 indexed strings are still untranslated.
- Inserted the complete tutorial category: 120 timed strings plus 18 auxiliary slots in four copies. Appended rebuilt tables to new resource storage, redirected their table pointers, and rebuilt sector-aligned DATA.BIN entries without per-string byte limits. Preserved source control codes, including the existing malformed command in row 467.
- Supplemented six 19-pixel gameplay fonts using glyphs already on the disc, preserving existing glyph records and sampled pixels. Atlas dimensions are unchanged. Added a reversible GS texture codec and an offline glyph proof. Two compact 20-pixel fonts remain unmodified, and runtime font selection still needs testing.
- Added Light Newman to the sourced glossary and preserved later terminology research as explicit proposals. Archived the tutorial screenshot unchanged and recorded provisional subtitle bounds; no in-game fit claim.
- Built ACE3-English-0.1.6.iso on the 0.1.5 changes. Fresh ISO9660/UDF filesystem records avoid the disc library's handling of Sony's padded original directory records. Verified all 10,344 archive payloads and all 133 ISO files; retained the PS2 system/license area. Original and prior released ISOs are unchanged.
- Sixteen focused tests pass. Build report, input snapshot, coverage, and pending work are recorded. The full-game task remains open; emulator boot, text capacity, subtitle timing, and the new glyphs await user testing.

## 0.1.5 — 2026-09-18

- Confirmed from three new user captures that missing Latin glyphs are fixed, but main-menu and setup labels remain truncated without an open dialog. The paused-animation hypothesis is ruled out.
- Increased text drawing capacity to 128 glyphs in the main-menu and initial-setup initialization callbacks, before buffer allocation. This covers labels, descriptions, and the cut-off confirmation footer without shortening English or changing font size.
- Added two exact, preimage-checked 20-byte executable patches. The callback still stores its original text resource and restores its original return address; unrelated menu callbacks are unchanged.
- Added an instruction-level test of original versus replacement callback tails, including branch delay slots, both resource-pointer cases, nine previous capacities, saved registers, return address, and isolated memory changes. Existing ten resource/font tests pass. Full ISO validation is recorded in the build report.
- Archived three 0.1.4 screenshots unchanged with hashes, defect bounds, observed/expected text, and test status. Kept a 0.1.4 manifest snapshot and now save the exact manifest alongside each new ISO.
- Built ACE3-English-0.1.5.iso. Translations and the existing game font atlas are unchanged from 0.1.4. In-game verification remains pending; controller-diagram captions still await insertion.

## 0.1.4 — 2026-09-18

- Fixed the font lookup gaps behind the reported question marks by aliasing 26 ASCII characters to existing glyphs, preserving original glyphs and texture.
- Expanded to 106 translation mappings and 250 string instances across both startup bundles. Every language-bearing entry in the main menu, memory-card messages, save/load UI, initial setup, and shared startup dialog tables is now covered.
- Added the setup question and help message, all related dialog titles/prompts, and adjacent save/load/format/error messages. Preserved button icons and runtime save-slot fields.
- Added complete-category, glyph-coverage, icon, line-width, and modal-line-count checks. Changed the settings action from Adjust to Set because the original font has no lowercase j.
- Repacked the font/text resources and relocated subsequent resources; each startup bundle grows by 160 bytes within its existing allocation. Ten focused tests and full bytewise ISO verification passed. All 106 mappings received a meaning review without substantive corrections.
- Archived four 0.1.3 bug screenshots unchanged with provenance, hashes, measured defect regions, and translation links. Updated screenshot references and the test guide.
- Built ACE3-English-0.1.4.iso; original and prior ISO preserved. In-game verification remains pending. Shortened setup labels behind open dialogs need a post-dialog check; no separate clipping fix is claimed. Controller-diagram captions remain pending insertion.

## 0.1.3 — 2026-09-18

- Added three settings screenshots unchanged, bringing the reference catalog to seven captures and 106 measured regions.
- Added 26 Japanese-to-English UI translations and two existing English values; the catalog now has 41 translations and seven retained English labels.
- Located the game's CP932 UI text tables inside DATA.BIN and documented exact resources, special glyph bytes, and text pointers.
- Built the first English UI test ISO with 39 mappings applied to 94 string instances across ten tables in both startup bundles. Rebuilt string pools without per-string byte truncation.
- Added a dry-run-first ISO builder, complete bytewise output verification, hashes, a build report, and a testing guide. The original ISO remains unchanged.
- Passed five focused pointer-repacking tests covering longer strings, untouched tables and glyphs, overflow rejection, malformed pointers, and missing terminators; also checked reference hashes, insertion links, document links, viewer data, and viewer script syntax.
- Decoded reference UI artwork while investigating the controller confirmation diagram. Its question and ten captions are translated in the reference files but remain Japanese in this test ISO because their resources are not yet identified.
- In-game rendering awaits user testing; PCSX2 screen access timed out and the user requested the ISO for their own test.

## 0.1.2 — 2026-09-18

- Completed the English translation of all 15 Japanese UI strings across the four supplied screenshots after checking their meanings and screen contexts.
- Retained the five existing English table headings, circle/cross control mappings, and the warning's PS2 and memory-card-slot-1 details.
- Recorded translation completion separately from pending game insertion and display testing; the accurate draft wording needed no changes.
- Added readable English screen copy and updated the reference viewer and validator to support completed translations.
- No patched game build was produced; in-game English fit and wrapping remain untested.

## 0.1.1 — 2026-09-18

- Archived four user-supplied UI screenshots unchanged, with attachment provenance and SHA-256 hashes.
- Cataloged 36 foreground UI regions with approximate coordinates, viewport bounds, observed controls, and estimated text areas.
- Added 15 English UI drafts and preserved 5 existing English column headings.
- Added a labeled browser viewer and a dry-run-first viewer builder with read-only reference validation.
- Verified original image hashes, dimensions, region bounds, translation links, viewer data consistency, and viewer JavaScript syntax.
- Kept character limits, game offsets, control-code encoding, portrait identity, and English render fit explicitly unverified. Glossary data remains at 0.1.0; no patched game build was produced.

## 0.1.0 — 2026-09-18

- Started the English glossary with 41 sourced entries: 26 characters, 8 organizations, 6 locations, and 1 technology term.
- Added 40 source records, field-level citations, continuity notes, documented spelling variants, and a 19-series coverage checklist.
- Marked 7 provisional names/labels, 5 franchise-context-only entries, and 6 unknown personality profiles explicitly.
- Added a research queue, readable index, maintenance guide, and read-only lookup/integrity tool.
- Validation passed for entry/source links, research-queue consistency, Japanese width/spacing lookup, aliases, ambiguous matches, JSON output, and rejection of invalid data.
- Kept Japanese content to short names and terms; no dialogue extraction, ISO changes, or patched game build.
