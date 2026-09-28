English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English prologue subtitles.

### Apply

**The easiest way:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or supported published English-prologue ISO, choose **0.1.65** (or **Latest**), select a new output filename, and click **Patch**. The app downloads the matching patches and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use the appropriate command below.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.1.65-movie.xdelta` |
| Published English-prologue v0.1.47 ISO | `ACE3-English-0.1.47-to-0.1.65-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.65-movie.xdelta "ACE3 English 0.1.65.iso"
```

**Upgrade from v0.1.47:**

```text
xdelta3 -d -s "ACE3 English 0.1.47.iso" ACE3-English-0.1.47-to-0.1.65-movie.xdelta "ACE3 English 0.1.65.iso"
```

Use your actual filenames. Both patches produce the same output. Earlier published v0.1.35 and v0.1.42 English-prologue images can upgrade through the existing intermediate patches using Retro Trans. Local test images, including 0.1.64, have different binary identities; use the original disc or the exact published v0.1.47 image for these downloads. Do not disable source checks on a checksum mismatch.

Original Japanese ISO: 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Release output: 4,455,581,696 bytes; SHA-256 `b8d7f75e714eb2a0575bf9b7d79030bdc7859a75552b4560bb13e166f633486a`.

Exact source and patch identities are in `BUILD-MANIFEST.json`. `VALIDATION.json` records patch round trips, and `SHA256SUMS.txt` covers download integrity. Retro Trans supports unpacking DVD CHD images before patching; other patchers require the unpacked ISO.

### What changed since v0.1.47

* **Opening lyrics inside the CG.** Adds 19 approved romaji/English lyric cues in a compact two-line layout inside the full picture. Original movie audio is preserved.
* **Credits conversation and song subtitles.** Adds 72 English dialogue cues and 26 romaji/English lyric cues to the live credits. Lyrics appear at the top and dialogue at the bottom; scrolling staff names and logos stay clear of the captions.
* **Longer ending subtitle holds.** Keeps captions visible for 0.5 seconds after a line ends, unless the next line follows sooner.
* **Missing ending comm dialogue translated.** Covers 17 timed lines and the quit prompt in four copies of the previously missed sequence, including Jamil's “Everyone...! Well done!”
* **Ending story disclaimer translated.** Replaces the image-based disclaimer after the credits with English.
* **Menu and stat layout fixes.** Widens Game and Controls caption columns, restores missing option labels, separates long choices such as Flight Rev. and Invert X/Y, and widens Intermission buttons for Combat Records. Moves stat gauges clear of their captions and uses Streak for consecutive sorties.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) has further details. This release packages the approved 0.1.64 content in the original disc's file order for smaller patches. All 133 game files match that build; the release has its own 0.1.65 identity because its disc layout differs.

### Release status

**This exact release still needs full in-game playtesting.** Movie decoding, disc checks and full/upgrade patch round trips are verified. The native credits test observed all 98 caption cues and checked simultaneous lyrics/dialogue plus logo clearance in a disposable saved-state test. Fresh-disc loading of the enlarged ending resources, the later 0.5-second hold revision and final opening playback have not been verified in the emulator. Some lyric pronunciation/timing uncertainties remain documented in the translation sources.

The two late-game CG movies still have their original Japanese subtitles; their English MP4 previews are not integrated in this release. Some image-based labels, including the battle-stations briefing banner, and unclassified mission variants remain outside the confirmed translation coverage.

Boot the patched ISO fresh and load a normal memory-card save. Save states made during the affected scenes retain old executable data, resources and subtitle timings.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, supported mission/story/in-mission dialogue, battle shouts, meeting captions, abilities, support details, command lists and branching Situation Reports. English prologue subtitles, bilingual opening lyrics, credits dialogue/song captions and the ending disclaimer are included. A full patch and matching v0.1.47 upgrade are provided.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Audio-only ending dialogue and lyrics used local Whisper transcription and meaning review; the opening also uses lyrics supplied by the user. Translation sources retain review notes and uncertainties. Further proofreading and playtesting are welcome.

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
