English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English prologue subtitles.

### Apply

**The easiest way:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or supported previous English-prologue ISO, choose **0.1.47** (or **Latest**) as the target, choose a new output filename, and click **Patch**. The app downloads the matching patch and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use one of these commands.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.1.47-movie.xdelta` |
| Published English-prologue v0.1.42 ISO | `ACE3-English-0.1.42-to-0.1.47-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.47-movie.xdelta "ACE3 English 0.1.47.iso"
```

**Upgrade from v0.1.42:**

```text
xdelta3 -d -s "ACE3 English 0.1.42 movie.iso" ACE3-English-0.1.42-to-0.1.47-movie.xdelta "ACE3 English 0.1.47.iso"
```

Use your actual filenames. The full patch requires your original Japanese disc image; the upgrade requires the exact published English-prologue v0.1.42 output. Local test images may differ. Do not disable source checks if a checksum mismatch appears. Both patches produce the same output.

The original Japanese ISO is 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Output: 4,455,428,096 bytes; SHA-256 `b86f9a52d2b8bfae419d5a7d7bd48d59665787b3e6393e3722d9dc757129aa8e`. Exact source hashes are in `BUILD-MANIFEST.json`; `VALIDATION.json` records successful patch round trips, and `SHA256SUMS.txt` covers download integrity.

Retro Trans supports unpacking DVD CHD images before patching. Other patchers require the unpacked ISO. Use the latest Retro Trans app to refresh catalogs containing withdrawn patches.

### What changed since v0.1.42

* **Branching Situation Reports translated.** Adds 142 title/dialogue rows across 16 missed report resources, including Federation Movements, Shirahime and the Hojo Army. Preserves scene commands, glossary links, route conditions and images, with dialogue fitted to three lines.
* **Stat panels corrected.** Translates the image-based Player Sorties caption. Fits Parameters, Consec. Sorties and the six stat labels in Deployment, Unit Upgrades and recruitment panels; moves the upgrade heading clear of the border.
* **Game option names clarified.** Uses **Lock-On Info**, **Lock-On Priority** and **Ingame Comm**, with adjusted text boxes for the previously missing labels.
* **Briefing headings fitted.** Uses **Victory** and **Defeat** beside the objectives so both headings fit their column.
* **Nu Gundam capitalization corrected.** Updates 40 stored name/dialogue occurrences, including the HWS variant, and the translation glossary.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) contains further detail. The report audit found no remaining Japanese in the active text rows of 156 window resources and the 40 previously supported mission resources. That audit does not cover every unknown resource format, unclassified mission variant or image-based caption.

Release images preserve the original file order for smaller patches. All 133 disc files were verified against the test build before packaging. Their ISO hashes differ from local test builds.

### Release status

**The recent fixes still need in-game confirmation.** Translation, layout and disc checks passed, but this exact release has not been fully playtested. Patch verification does not establish full-game playability.

Some image-based labels, including the "battle stations" briefing banner, and the burned-in subtitles of two late-game movies remain Japanese.

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain executable data and text from the previous build.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, mission text, story and in-mission dialogue, battle shouts, meeting captions, abilities, support details and command lists, plus the branching Situation Reports added in this release. English prologue subtitles are included. A full patch and matching v0.1.42 upgrade are provided.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Translation sources retain review notes and open questions; further proofreading and playtesting are welcome.

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
