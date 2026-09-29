English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English movie subtitles.

### Apply

**The easiest way:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or supported published English-prologue ISO, choose **0.9.3** (or **Latest**), select a new output filename, and click **Patch**. The app downloads the matching patches and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use the appropriate command below.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.9.3-movie.xdelta` |
| Published English-prologue v0.9.0 ISO | `ACE3-English-0.9.0-to-0.9.3-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.9.3-movie.xdelta "ACE3 English 0.9.3.iso"
```

**Upgrade from v0.9.0:**

```text
xdelta3 -d -s "ACE3 English 0.9.0.iso" ACE3-English-0.9.0-to-0.9.3-movie.xdelta "ACE3 English 0.9.3.iso"
```

Use your actual filenames. Both patches produce the same output. Earlier published v0.1.35, v0.1.42, v0.1.47 and v0.1.65 English-prologue images can upgrade through the existing intermediate patches using Retro Trans. For manual patching, use the original disc or the exact published v0.9.0 image. Do not disable source checks on a checksum mismatch.

Original Japanese ISO: 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Release output: 4,455,596,032 bytes; SHA-256 `e8a5173150f3c44017adb652aee4798696d3e6ab1ebf86d4bc611b800d53b02b`.

Exact source and patch identities are in `BUILD-MANIFEST.json`. `VALIDATION.json` records patch round trips, and `SHA256SUMS.txt` covers download integrity. Retro Trans supports unpacking DVD CHD images before patching; other patchers require the unpacked ISO.

### What changed since v0.9.0

* **Two missing movies subtitled.** Integrates the prepared English subtitles for the Axis sequence (48 cues) and the resonance / two-Earths sequence (11 cues). Retains the reviewed preview layout and timing, original audio, frame counts and frame rates.
* **Enemy names readable.** Completes the separate lock-on HUD font in all eight gameplay copies. Fixes names such as **Monsuno type10**, which appeared as question marks because most English letters were missing from that font.
* **Deployment captions restored.** Widens the first column for **Combo Attack** and **Damage**, moving the separators and values right so the captions fit.
* **Earlier translations retained.** Includes the English prologue, compact opening romaji/English lyrics, simultaneous credits dialogue/song captions, ending subtitle holds, ending disclaimer and previous text and layout fixes.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) has further details. The release image matches all 133 game files from local build 0.9.3. Full and upgrade patches are decoded and verified against the complete release output.

### Release status

**This exact release still needs full in-game playtesting.** Both new movie remuxes pass decoding checks and preserve every non-video packet, including the original audio. The HUD font preserves all 242 original glyphs and supports printable English characters. Disc checks verify the intended changes; they do not certify emulator or console playback.

Fresh-boot checks are still needed for the two new movies, the enemy-name font and Deployment captions. Earlier credits testing observed all 98 caption cues in a disposable saved-state test; fresh-disc loading of the enlarged ending resources and later timing changes remain unverified. Some lyric readings and one short **Sara** speaker label in the two-Earths movie remain uncertain. Other image-based labels and unclassified mission variants remain outside confirmed coverage.

A Chapter 1 loading-screen hang has been reported on ARMSX2. It has not been reproduced, and whether it also occurs with the original Japanese game is not yet known.

Boot the patched ISO fresh and load a normal memory-card save. Save states made during affected scenes retain old executable data, resources, fonts and subtitle timings.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, supported mission/story/in-mission dialogue, battle shouts, meeting captions, abilities, support details, command lists and branching Situation Reports. Includes English subtitles for the prologue and both late-game dialogue movies, bilingual opening lyrics, credits dialogue/song captions and the ending disclaimer. A full patch and matching v0.9.0 upgrade are provided.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Movie and audio-only ending work used local Whisper transcription and meaning review; the opening also uses lyrics supplied by the user. Translation sources retain review notes and uncertainties. Further proofreading and playtesting are welcome.

### Acknowledgements

* **Project Lead:** pow
* **Playtesting:** SecondarySebs, BlackHowling | QiyoShiro

### Source code

Translation text, glossaries and editing tools are available in the [project repository](https://github.com/retro-trans/ACE-3). GitHub's **Source code (zip)** and **Source code (tar.gz)** downloads contain the repository snapshot at the release tag. Use the `.xdelta` assets to patch the game.

### Contribute

Bug reports, proofreading and playtesting are welcome:

**[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**

---

No complete game images are included. Apply the patches to your own Japanese disc image.
