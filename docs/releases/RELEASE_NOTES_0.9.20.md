English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English movie subtitles.

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or a supported published English-prologue ISO, choose **0.9.20** (or **Latest**), and select a new output filename. The app downloads the matching patches and verifies the result.

**Manual patching:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same assets:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.9.20-movie.xdelta` |
| Published English-prologue v0.9.16 ISO | `ACE3-English-0.9.16-to-0.9.20-movie.xdelta` |

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.9.20-movie.xdelta "ACE3 English 0.9.20.iso"
```

To upgrade from the published v0.9.16 image:

```text
xdelta3 -d -s "ACE3 English 0.9.16.iso" ACE3-English-0.9.16-to-0.9.20-movie.xdelta "ACE3 English 0.9.20.iso"
```

Both patches produce the same release image. Earlier supported English-prologue releases can upgrade through the existing intermediate patches in Retro Trans. The upgrade patch requires the exact published v0.9.16 image; local test ISOs have different checksums. Use the original disc if your image does not match.

Original Japanese ISO: 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Release output: 4,455,671,808 bytes; SHA-256 `b3e34f1c424b13eb87afdb6f04b17efd68c470ccd840b2bf7748fd660ab65004`.

The exact source, output and patch hashes are in `BUILD-MANIFEST.json`. `VALIDATION.json` records patch round trips, and `SHA256SUMS.txt` covers the downloads. Retro Trans handles supported DVD CHD extraction; manual patchers require the unpacked ISO.

### What changed since v0.9.16

* **Extra Missions 3 and 4:** Translate the missed dialogue, reinforcement warnings, kill-count messages, return-point objectives and results. Covers 51 unique text rows across eight resource copies, including Benkei's “That's the spirit! Keep taking them down!”
* **Deployment:** Change the overlapping Player Sorties caption to **Sorties**, using the standard caption cell so the count remains readable.
* **Game options:** Give labels, choices and arrows more room. Correct the native-position behavior that defeated the initial spacing adjustment. The project lead confirmed the revised menu in the 0.9.20 test build.

Retains all previous translations, embedded HD fonts, English staff credits, movie subtitles, opening romaji/English lyrics, credits dialogue/song captions, cinematic positioning and UI fixes. See the [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md).

### Release status

**Further proofreading and full in-game playtesting are needed.** File and patch verification establishes that the intended data is included and the patches reproduce the release image; it does not certify emulator or console behavior. The Game-options spacing has been confirmed by the project lead. Extra Mission text, the Sorties counter layout and other routes still benefit from further in-game testing.

Six staff-name readings are provisional: **Naoto Sawaguchi, Tomohiro Ishii, Tokuya Saito, Tomonori Nishikawa, Ryo Shin and Daiki Watanabe**. They are flagged in the [credits notes](https://github.com/retro-trans/ACE-3/blob/main/docs/STAFF_CREDITS_0911.md). Some lyric readings and the short Sara speaker label in the two-Earths movie also remain uncertain. Other image-based labels and unclassified mission variants remain outside confirmed coverage.

A Chapter 1 loading-screen hang has been reported on ARMSX2. It has not been reproduced, and whether it also happens with the original Japanese game is not yet known.

**Boot the patched ISO fresh and load a normal memory-card save.** Older save states can restore old text, fonts, coordinates and subtitle timing.

### What's included

English menus and help, Encyclopedia entries, unit/pilot names, supported mission/story/in-mission dialogue, including the corrected Extra Missions 3 and 4, battle shouts, meeting captions, abilities, support details, command lists and branching Situation Reports. Also includes subtitled prologue and late-game dialogue movies, bilingual opening lyrics, credits dialogue/song captions, English staff credits and the ending disclaimer. Only the English-prologue edition is supported.

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
