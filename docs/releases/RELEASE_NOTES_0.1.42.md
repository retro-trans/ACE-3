English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), with a choice of the original prologue movie or English prologue subtitles. Both editions translate the game text.

### Apply

**The easiest way:** Download [Retro Trans](https://github.com/retro-trans/retro-trans-tools) from its Releases page. Click **Refresh catalog**, open **Automatic**, and select your source game image. For an original Japanese disc, choose **Original prologue** or **English prologue** in the **Binary** list. Choose **0.1.42** as the target for this release, select a new output filename, and click **Patch**. **Latest** selects the newest compatible release. The app downloads the matching patch and verifies the result.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO as the original file and the appropriate patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use one of the commands below.

You need your own Japanese disc image or the matching published English v0.1.35 image for an upgrade. Full patches are alternatives; do not apply them on top of each other. The text and movie upgrade patches require their matching source editions.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO; keep the original prologue | `ACE3-English-0.1.42.xdelta` |
| Original Japanese ISO; use English prologue subtitles | `ACE3-English-0.1.42-movie.xdelta` |
| Published English v0.1.35 text ISO | `ACE3-English-0.1.35-to-0.1.42.xdelta` |
| Published English v0.1.35 movie ISO | `ACE3-English-0.1.35-to-0.1.42-movie.xdelta` |

**Original prologue edition:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.42.xdelta "ACE3 English 0.1.42.iso"
```

**English prologue edition:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.42-movie.xdelta "ACE3 English 0.1.42 movie.iso"
```

**Already on the v0.1.35 text edition?** Use its upgrade patch:

```text
xdelta3 -d -s "ACE3 English 0.1.35.iso" ACE3-English-0.1.35-to-0.1.42.xdelta "ACE3 English 0.1.42.iso"
```

**Already on the v0.1.35 movie edition?** Use its upgrade patch:

```text
xdelta3 -d -s "ACE3 English 0.1.35 movie.iso" ACE3-English-0.1.35-to-0.1.42-movie.xdelta "ACE3 English 0.1.42 movie.iso"
```

Use your actual source filename in these commands. For a supported DVD `.chd`, Retro Trans handles unpacking before patching. Other patchers need the unpacked ISO; do not apply an ISO patch directly to the compressed CHD.

If the patcher reports a checksum mismatch, check your source edition and version against the details below. Do not disable source verification. Upgrade patches require the exact published v0.1.35 outputs; local test builds may have different bytes. Full and upgrade patches produce identical v0.1.42 output within each edition.

<details>
<summary>Source and output ISO hashes</summary>

| Required source | Bytes | SHA-256 |
| --- | ---: | --- |
| Original Japanese ISO | 4,447,076,352 | `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705` |
| Published v0.1.35 text ISO | 4,452,986,880 | `15f69e6ca194b8f8a58ca8e0cc84b54e946923b1efe732345015a81443f61da3` |
| Published v0.1.35 movie ISO | 4,452,986,880 | `db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c` |

Both v0.1.42 outputs are **4,455,411,712 bytes**.

| Output edition | SHA-256 |
| --- | --- |
| Original prologue | `ad9dffa95cf8b8144c13d25c014d73992574c6f50ce4518661ac9c2be486557d` |
| English prologue | `c72752b32b5982b63ef8c5db5f171090469e3aad94999245cace2cb760565353` |

</details>

### What changed since v0.1.35

* **More gameplay text translated.** Covers abilities, support details, unit command lists, shared action instructions and pause-map names.
* **Remaining names and confirmations translated.** Includes model and Results names and shared Yes/No prompts.
* **Pause objectives aligned.** Separates overlapping Victory/Defeat headings from their objectives.
* **Communication text fits.** Fits overflowing messages into three lines so linked terms such as Londo Bell remain visible.
* **Encyclopedia pagination fixed.** Restores text lost between pages while preserving wording and glossary links.
* **Warnings and options completed.** Completes the memory-card operation warnings and fits long option labels.
* **Labels clarified.** Uses **Purchasable**, **Combo scene**, **Comm messages**, **Camera Movement** and **Situation Report**.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) contains further detail. The build verifies all 10,344 archive payloads and all 133 disc files. All four patches were decoded and compared with their intended ISO by size and SHA-256. Download checksums and exact source/output identities are provided in `SHA256SUMS.txt` and `BUILD-MANIFEST.json`; `VALIDATION.json` records successful patch round trips.

The Retro Trans packaging update adds those three metadata files. The existing xdelta files and resulting game images are unchanged. Release images preserve the original file order, with DATA.BIN enlarged and later files moved accordingly; their hashes differ from local test builds.

### Release status

**In-game confirmation is still pending for this release.** The recent layout and pagination fixes passed automated checks but still need fresh-boot testing. Patch verification does not establish full-game playability.

Some image-based labels, including Player Sorties and the "battle stations" briefing banner, and the burned-in subtitles of two late-game movies remain Japanese. The original-prologue edition also retains the Japanese prologue movie.

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain executable data and text from the previous build.

### What's included

English menus and help, Encyclopedia entries, unit and pilot names, mission text, story and in-mission dialogue, battle shouts, meeting captions, abilities, support details and command lists. The movie edition additionally includes English prologue subtitles. Full patches and matching v0.1.35 upgrades are provided for both editions; the editions differ only in the prologue movie data.

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
