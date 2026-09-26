English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), with a choice of the original prologue movie or English prologue subtitles. Both editions translate the game text.

### Apply

**The easiest way:** Download [Retro Trans](https://github.com/retro-trans/retro-trans-tools) from its Releases page. To apply this older release, use **Apply xdelta**, select your source ISO and one of the patches below, choose a new output filename, and click **Patch**. The **Automatic** tab offers cataloged releases and upgrades; it does not offer v0.1.35 as an installation target.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO as the original file and the appropriate patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use one of the commands below.

You need your own Japanese disc image or the matching published English v0.1.33 image for an upgrade. Full patches are alternatives; do not apply them on top of each other. The text and movie upgrade patches require their matching source editions.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO; keep the original prologue | `ACE3-English-0.1.35.xdelta` |
| Original Japanese ISO; use English prologue subtitles | `ACE3-English-0.1.35-movie.xdelta` |
| Published English v0.1.33 text ISO | `ACE3-English-0.1.33-to-0.1.35.xdelta` |
| Published English v0.1.33 movie ISO | `ACE3-English-0.1.33-to-0.1.35-movie.xdelta` |

**Original prologue edition:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.35.xdelta "ACE3 English 0.1.35.iso"
```

**English prologue edition:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.35-movie.xdelta "ACE3 English 0.1.35 movie.iso"
```

**Already on the v0.1.33 text edition?** Use its upgrade patch:

```text
xdelta3 -d -s "ACE3 English 0.1.33.iso" ACE3-English-0.1.33-to-0.1.35.xdelta "ACE3 English 0.1.35.iso"
```

**Already on the v0.1.33 movie edition?** Use its upgrade patch:

```text
xdelta3 -d -s "ACE3 English 0.1.33 movie.iso" ACE3-English-0.1.33-to-0.1.35-movie.xdelta "ACE3 English 0.1.35 movie.iso"
```

Use your actual source filename in these commands. Manual xdelta patching requires the unpacked ISO, not a compressed CHD.

If the patcher reports a checksum mismatch, check your source edition and version against the details below. Do not disable source verification. Upgrade patches require the exact published v0.1.33 outputs; local test builds may have different bytes. Full and upgrade patches produce identical v0.1.35 output within each edition.

<details>
<summary>Source and output ISO details</summary>

The original Japanese ISO is **4,447,076,352 bytes**, with SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

The upgrade patches require discs made with the matching published v0.1.33 patches, sized **4,451,299,328** or **4,452,253,696 bytes**. Size alone does not verify a source image; retain the patcher's source checks.

Both v0.1.35 outputs are **4,452,986,880 bytes**.

| Output edition | SHA-256 |
| --- | --- |
| Original prologue | `15f69e6ca194b8f8a58ca8e0cc84b54e946923b1efe732345015a81443f61da3` |
| English prologue | `db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c` |

</details>

### What changed since v0.1.33

* **Pilot battle shouts translated.** Covers 101 shout tables and 4,256 lines across the units.
* **Unit and pilot labels translated.** Includes the labels stored with each unit.
* **Encyclopedia series names translated.** Adds the English series names beneath entries.
* **Kids Munt corrected.** Replaces the on-disc "Kizz Munt" name.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) contains further detail. The patches are larger than v0.1.33's because the 111 unit models containing the shouts also have compressed copies that needed to be recompressed. Builds are verified offline against archive payloads and disc files; compare the patched ISO with the output hashes above.

### Release status

**The battle shouts and original-layout release discs still need fresh-boot testing.** Offline verification does not establish full-game playability. Please report problems with a screenshot and the mission or screen where they occur.

Ability names, the "battle stations" briefing banner and the burned-in subtitles of two late-game movies remain Japanese in this release. The original-prologue edition also retains the Japanese prologue movie.

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain executable data and text from the previous build.

### What's included

English menus, options and help; Encyclopedia entries; unit and pilot names; mission titles and secret goals; the opening history crawl; Global Meetings, briefings and Situation Archive conversations; hangar and in-mission dialogue and HUD alerts for all 35 mission slots across both story routes; meeting-picture captions; and pilot battle shouts. The movie edition additionally includes English prologue subtitles. Full patches and matching v0.1.33 upgrades are provided for both editions.

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
