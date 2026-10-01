English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English movie subtitles.

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or a supported published English-prologue ISO, choose **0.9.16** (or **Latest**), and select a new output filename. The app downloads the matching patches and verifies the result.

**Manual patching:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same assets:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.9.16-movie.xdelta` |
| Published English-prologue v0.9.3 ISO | `ACE3-English-0.9.3-to-0.9.16-movie.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.9.16-movie.xdelta "ACE3 English 0.9.16.iso"
```

To upgrade from the published v0.9.3 image:

```text
xdelta3 -d -s "ACE3 English 0.9.3.iso" ACE3-English-0.9.3-to-0.9.16-movie.xdelta "ACE3 English 0.9.16.iso"
```

Both patches produce the same release image. Earlier supported English-prologue releases can upgrade through the existing intermediate patches in Retro Trans. The upgrade patch requires the exact published v0.9.3 image; local test ISOs have different checksums. Use the original disc if your image does not match.

Original Japanese ISO: 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

The exact source, output and patch hashes are in `BUILD-MANIFEST.json`. `VALIDATION.json` records patch round trips, and `SHA256SUMS.txt` covers the downloads. Retro Trans handles supported DVD CHD extraction; manual patchers require the unpacked ISO.

### What changed since v0.9.3

* **Sharper embedded fonts.** Main menu/dialogue Latin lettering uses 4x rasterization. Secondary fonts and the translated staff roll use higher-resolution lettering within their available texture space. Enemy names use a clearer bold sans-serif font. No emulator texture replacement pack is required.
* **English staff credits.** Translates 323 staff-roll text rows, including roles, organizations, song information and romanized names, with a complete English font and centered lines. Updates the compressed scene used during a fresh boot as well as its plain copy. Preserves logos, scrolling, ending dialogue and bilingual lyrics.
* **UI readability fixes.** Updates Player Sorties to native HD text, improves the Battle Stations banner, fits Comm inside its box, and fixes overlapping upgrade/limiter confirmation text. Corrects the CAUTION label's texture binding after the intermediate local font test produced a garbled header.
* **Cinematic text placement.** Moves the portrait-free cinematic speaker and dialogue 60 native pixels left, retaining their relative indent and vertical placement.
* **Wording corrections.** Uses “Thanks to your hard work fighting” in Jamil's dialogue and “fired a Deuteron Missile at us” in Hayato's Situation Report.

Includes all previous movie subtitles, opening romaji/English lyrics, simultaneous credits dialogue/song captions, subtitle timing adjustments, ending disclaimer and translation fixes. See the [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) for the individual build changes.

### Release status

**Further proofreading and full in-game playtesting are needed.** File and patch verification establishes that the intended data is included and the patches reproduce the release image; it does not certify emulator or console behavior. Fresh-boot checks remain particularly useful for the translated credits, CAUTION label/panel animation and revised cinematic placement.

Six staff-name readings are provisional: **Naoto Sawaguchi, Tomohiro Ishii, Tokuya Saito, Tomonori Nishikawa, Ryo Shin and Daiki Watanabe**. They are flagged in the [credits notes](https://github.com/retro-trans/ACE-3/blob/main/docs/STAFF_CREDITS_0911.md). Some lyric readings and the short Sara speaker label in the two-Earths movie also remain uncertain. Other image-based labels and unclassified mission variants remain outside confirmed coverage.

A Chapter 1 loading-screen hang has been reported on ARMSX2. It has not been reproduced, and whether it also happens with the original Japanese game is not yet known.

**Boot the patched ISO fresh and load a normal memory-card save.** Older save states can restore old text, fonts, coordinates and subtitle timing.

### What's included

English menus and help, Encyclopedia entries, unit/pilot names, supported mission/story/in-mission dialogue, battle shouts, meeting captions, abilities, support details, command lists and branching Situation Reports. Also includes subtitled prologue and late-game dialogue movies, bilingual opening lyrics, credits dialogue/song captions, English staff credits and the ending disclaimer. Only the English-prologue edition is supported.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Movie and audio-only ending work used local Whisper transcription and meaning review; song work also uses lyrics supplied by the project lead. Sources retain review notes and uncertainties. Human proofreading and playtesting are welcome.

### Acknowledgements

* **Project Lead:** pow
* **Playtesting:** SecondarySebs, BlackHowling | QiyoShiro

### Source code

Translation text, glossaries and tools are available in the [project repository](https://github.com/retro-trans/ACE-3). GitHub's source archives contain the repository snapshot at the release tag. Use the `.xdelta` assets to patch the game.

### Contribute

Bug reports, proofreading and playtesting are welcome at **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

No complete game images are included. Apply the patches to your own disc image.
