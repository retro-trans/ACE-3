English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English prologue subtitles.

### Apply

**The easiest way:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO or supported previous English-prologue ISO, choose **0.1.42** (or **Latest**) as the target, choose a new output filename, and click **Patch**. The app downloads the matching patch and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use one of these commands.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.1.42-movie.xdelta` |
| Published English-prologue v0.1.35 ISO | `ACE3-English-0.1.35-to-0.1.42-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.42-movie.xdelta "ACE3 English 0.1.42.iso"
```

**Upgrade from v0.1.35:**

```text
xdelta3 -d -s "ACE3 English 0.1.35 movie.iso" ACE3-English-0.1.35-to-0.1.42-movie.xdelta "ACE3 English 0.1.42.iso"
```

Use your actual filenames. The full patch requires your original Japanese disc image; the upgrade requires the exact published English-prologue v0.1.35 output. Local test images may differ. Do not disable source checks if a checksum mismatch appears. Both patches produce the same output.

The original Japanese ISO is 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Output: 4,455,411,712 bytes; SHA-256 `c72752b32b5982b63ef8c5db5f171090469e3aad94999245cace2cb760565353`. Exact source hashes are in `BUILD-MANIFEST.json`; `VALIDATION.json` records successful patch round trips, and `SHA256SUMS.txt` covers download integrity.

Retro Trans supports unpacking DVD CHD images before patching. Other patchers require the unpacked ISO. Use the latest Retro Trans app to refresh catalogs containing withdrawn patches.

### What changed since v0.1.35

* **More gameplay text translated.** Covers abilities, support details, unit command lists, shared action instructions and pause-map names.
* **Remaining names and confirmations translated.** Includes model and Results names and shared Yes/No prompts.
* **Pause objectives aligned.** Separates overlapping Victory/Defeat headings from their objectives.
* **Communication text fits.** Fits overflowing messages into three lines so linked terms such as Londo Bell remain visible.
* **Encyclopedia pagination fixed.** Restores text lost between pages while preserving wording and glossary links.
* **Warnings and options completed.** Completes the memory-card operation warnings and fits long option labels.
* **Labels clarified.** Uses **Purchasable**, **Combo scene**, **Comm messages**, **Camera Movement** and **Situation Report**.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) contains further detail. The build verifies all 10,344 archive payloads and all 133 disc files. Both remaining patches were decoded and compared with their intended ISO by size and SHA-256. Download checksums and exact source/output identities are provided in `SHA256SUMS.txt` and `BUILD-MANIFEST.json`; `VALIDATION.json` records successful patch round trips.

The Retro Trans packaging update adds those three metadata files. The remaining xdelta files and resulting English prologue image are unchanged. Release images preserve the original file order, with DATA.BIN enlarged and later files moved accordingly; their hashes differ from local test builds.

### Release status

**In-game confirmation is still pending for this release.** The recent layout and pagination fixes passed automated checks but still need fresh-boot testing. Patch verification does not establish full-game playability.

Some image-based labels, including Player Sorties and the "battle stations" briefing banner, and the burned-in subtitles of two late-game movies remain Japanese.

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain executable data and text from the previous build.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, mission text, story and in-mission dialogue, battle shouts, meeting captions, abilities, support details and command lists. English prologue subtitles are included. A full patch and matching v0.1.35 upgrade are provided.

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
