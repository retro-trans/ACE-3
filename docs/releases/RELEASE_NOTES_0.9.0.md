English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English prologue subtitles.

### Apply

**The easiest way:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or supported published English-prologue ISO, choose **0.9.0** (or **Latest**), select a new output filename, and click **Patch**. The app downloads the matching patches and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use the appropriate command below.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.9.0-movie.xdelta` |
| Published English-prologue v0.1.65 ISO | `ACE3-English-0.1.65-to-0.9.0-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.9.0-movie.xdelta "ACE3 English 0.9.0.iso"
```

**Upgrade from v0.1.65:**

```text
xdelta3 -d -s "ACE3 English 0.1.65.iso" ACE3-English-0.1.65-to-0.9.0-movie.xdelta "ACE3 English 0.9.0.iso"
```

Use your actual filenames. Both patches produce the same output. Earlier published v0.1.35, v0.1.42 and v0.1.47 English-prologue images can upgrade through the existing intermediate patches using Retro Trans. For manual patching, use the original disc or the exact published v0.1.65 image. Do not disable source checks on a checksum mismatch.

Original Japanese ISO: 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Release output: 4,455,581,696 bytes; SHA-256 `68b7fc22f7cde93b453223af0d45ca4e040be40f0edb263acc128f354e1e37d1`.

Exact source and patch identities are in `BUILD-MANIFEST.json`. `VALIDATION.json` records patch round trips, and `SHA256SUMS.txt` covers download integrity. Retro Trans supports unpacking DVD CHD images before patching; other patchers require the unpacked ISO.

### What changed since v0.1.65

* **New version number: 0.9.0.** Packages the latest fixes from local builds 0.1.66–0.1.68 under the requested release version.
* **Empty ally slots translated.** Replaces the remaining Japanese “none” placeholder with **None** in all four shared copies used by the deployment confirmation.
* **Briefing alert translated.** Replaces the image-based alert with **BATTLE STATIONS** in all three briefing copies. The English text fits between the existing animated brackets.
* **Parameters gauge spacing repaired.** Moves all 42 affected fill layers directly through their geometry so the placement does not depend on widget origins that are reset in-game. Covers Deployment, Unit Upgrades and the two recruitment layouts; preserves labels and value bindings.
* **Previous translation and subtitles retained.** Keeps English prologue subtitles, compact opening romaji/English lyrics inside the CG, simultaneous credits dialogue/song captions, the longer subtitle holds, and earlier menu, dialogue and layout fixes.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) has further details. All 133 game files match local build 0.1.68. Full and upgrade patches are decoded and verified against the complete release output, with canonical Retro Trans metadata and checksums supplied below.

### Release status

**This exact release still needs full in-game playtesting.** The latest fixes passed whole-disc byte checks and full/upgrade patch round trips. The new briefing banner animation and Parameters gauge rendering still need fresh in-game confirmation. Earlier movie decoding checks remain applicable because those movie files are unchanged. The native credits test observed all 98 caption cues and checked simultaneous lyrics/dialogue plus logo clearance in a disposable saved-state test. Fresh-disc loading of the enlarged ending resources, the later 0.5-second hold revision and final opening playback have not been verified in the emulator. Some lyric pronunciation/timing uncertainties remain documented in the translation sources.

The two late-game CG movies still have their original Japanese subtitles; their English MP4 previews are not integrated in this release. Some other image-based labels and unclassified mission variants remain outside the confirmed translation coverage. The new version number is not a claim of complete coverage.

Boot the patched ISO fresh and load a normal memory-card save. Save states made during the affected scenes retain old executable data, resources and subtitle timings.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, supported mission/story/in-mission dialogue, battle shouts, meeting captions, abilities, support details, command lists and branching Situation Reports. English prologue subtitles, bilingual opening lyrics, credits dialogue/song captions and the ending disclaimer are included. A full patch and matching v0.1.65 upgrade are provided.

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
