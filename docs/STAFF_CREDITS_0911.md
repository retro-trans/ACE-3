# English staff credits — local test 0.9.11

**Superseded for in-game credits testing by 0.9.12.** A fresh-boot report showed that 0.9.11 changed only the plain scene; the game loads the compressed twin, which remained Japanese. See `docs/STAFF_CREDITS_0912.md`. The translation, font design, references and provisional-name notes below remain applicable, but 0.9.11 did not complete runtime integration.

Output: `work/output/ACE3-English-0.9.11.iso`, based on 0.9.10.
This build integrates the credits translation and a sharper embedded font.

Built and whole-disc verified on 2026-10-01. Size: 4,447,076,352 bytes.
SHA-256: `b0a48f3d4f3b1c82c720cfdefe4bc54e599852f8e6e8b207b7658de0121bb8ee`.
Verification report: `work/output/ACE3-English-0.9.11.json`.

## Coverage and rendering

The roll contains 323 English text rows and nine retained graphics-command rows. All 781 text slots, including blank/null rows, retain their original IDs and positions in the sequence. Staff roles, organizations, song information and cast names are covered. Logo images and their commands are unchanged.

The dedicated staff font now contains all 95 printable ASCII characters, using Times New Roman rasterized at 3x with antialiasing and a dark outline. The texture remains 512x512 with the original graphics-memory address, palette and byte allocation. The complete ASCII set at 4x would exceed that allocation. The font is embedded in the ISO; no PCSX2 texture pack is required. A fullwidth whitespace alias preserves the original blank row. Unused Japanese glyphs are removed only from this dedicated staff font.

Translated lines are measured and centered at x=320 in the native 640-wide frame. The original x=90 origin, 21-pixel line height, scroll speed and row spacing are retained. Decoded-font previews under `work/ui/staff_credits_0911` demonstrate the actual generated glyphs and horizontal layout; they are reconstructed previews, not emulator screenshots.

## Provisional personal-name readings

The user explicitly authorized provisional romanizations for these six unverified readings on 2026-10-01. They are included in the game as listed below and must not be described as verified spellings.

| Text ID | Provisional spelling | Credit area |
| --- | --- | --- |
| 177 | Naoto Sawaguchi | Event scripting |
| 179 | Tomohiro Ishii | Event scripting |
| 184 | Tokuya Saito | Character logic |
| 186 | Tomonori Nishikawa | Character logic |
| 427 | Ryo Shin | Burning Publishers |
| 434 | Daiki Watanabe | Burning Production |

The translation JSON records per-row source hashes and verification status. Source Japanese is read from the user's disc rather than exported as a duplicate script.

## References and corrections

Most personal-name spellings were matched against the [MobyGames PS2 credit list](https://www.mobygames.com/game/59035/another-centurys-episode-3-the-final/credits/ps2/), checked against the disc's original names and roles. Role labels were translated from the original disc.

That list attributes three entries to different people. These were corrected using the actual disc spelling and additional references:

- ID 487: Go Aoba, not Takeshi Aono. [Name reference](https://www.excite.co.jp/news/dictionary/person/PE046e0afa3ceda69a2388e34473f779752d3e463c/).
- ID 537: Kaori Nazuka, not Shiho Nagoshi. [Name reference](https://www.mobygames.com/person/206799/kaori-nazuka/).
- ID 659: Kojiro Taniguchi, not Keijiro Taniguchi. [Reading index](https://www.eventernote.com/actors/initial/た).

Hideki Tachibana's reading was cross-checked against [another game's QA credits](https://www.mobygames.com/game/76099/enkaku-sosa-shinjitsu-e-no-23-hiai/credits/psp/). ID 496 uses the established actor spelling Naoya Uchida despite a variant final kanji on the disc. Romanizations use ASCII without macrons for consistency with the patch.

## Build and validation

`tools/build_staff_credits_patch.py` plans and previews by default; `--write` creates the versioned ISO without overwriting an existing output. The only disc edit is resource 4350's STUF payload, rebuilt within its original extent. Its texture, font and text table change; all other bundle assets and disc bytes are checked against the source.

The builder checks source hashes, the actual roll-start event geometry/font mode/speed, complete target coverage, ASCII coverage, glyph bounds and non-overlap, texture encode/decode equality, line widths/centering, color-command preservation, blank/null slots, graphics commands, resource read-back and the chunk chain. Its write pass verifies every disc byte against the base plus the planned edit and records SHA-256 in the matching output JSON.

Ending dialogue, bilingual song lyrics, timing tracks and the existing caption-safe scroll region remain unchanged. Main/menu/HUD fonts and the Player Sorties change from 0.9.10 are preserved.

In-game playback is not yet verified. Boot this ISO and reach the ending before testing; loading a state captured during the credits can restore the old text and font from memory. Check the beginning, dense cast list, long company names, logos and simultaneous song/dialogue captions. No public release is published by this local build.
