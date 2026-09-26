English fan translation of **Another Century's Episode 3: The Final** for PS2 (**SLPS-25784**), including English prologue subtitles.

### Apply

**The easiest way:** Use **Apply xdelta** in [Retro Trans](https://github.com/retro-trans/retro-trans-tools) for this older release, selecting your source ISO and one of the patches below. Its **Automatic** tab offers newer cataloged releases and upgrades.

**Other ways:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) accepts the same `.xdelta` files. Select your unpacked ISO and the matching patch.

**Command line:** Get [xdelta3 here](https://github.com/jmacd/xdelta), then use one of these commands.

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO | `ACE3-English-0.1.35-movie.xdelta` |
| Published English-prologue v0.1.33 ISO | `ACE3-English-0.1.33-to-0.1.35-movie.xdelta` |

**Original Japanese disc:**

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.35-movie.xdelta "ACE3 English 0.1.35.iso"
```

**Upgrade from v0.1.33:**

```text
xdelta3 -d -s "ACE3 English 0.1.33 movie.iso" ACE3-English-0.1.33-to-0.1.35-movie.xdelta "ACE3 English 0.1.35.iso"
```

Use your actual filenames. The full patch requires your original Japanese disc image; the upgrade requires the exact published English-prologue v0.1.33 output. Local test images may differ. Do not disable source checks if a checksum mismatch appears. Both patches produce the same output.

The original Japanese ISO is 4,447,076,352 bytes; SHA-256 `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705`.

Output: 4,452,986,880 bytes; SHA-256 `db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c`. The upgrade requires the published v0.1.33 English-prologue image. Manual patchers require an unpacked ISO.

### What changed since v0.1.33

* **Pilot battle shouts translated.** Covers 101 shout tables and 4,256 lines across the units.
* **Unit and pilot labels translated.** Includes the labels stored with each unit.
* **Encyclopedia series names translated.** Adds the English series names beneath entries.
* **Kids Munt corrected.** Replaces the on-disc "Kizz Munt" name.

The [changelog](https://github.com/retro-trans/ACE-3/blob/main/docs/CHANGELOG.md) contains further detail. The patches are larger than v0.1.33's because the 111 unit models containing the shouts also have compressed copies that needed to be recompressed. Builds are verified offline against archive payloads and disc files; compare the patched ISO with the output hashes above.

### Release status

**The battle shouts and original-layout release discs still need fresh-boot testing.** Offline verification does not establish full-game playability. Please report problems with a screenshot and the mission or screen where they occur.

Ability names, the "battle stations" briefing banner and the burned-in subtitles of two late-game movies remain Japanese in this release.

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain executable data and text from the previous build.

### What's included

English menus, options and help; Encyclopedia entries; unit and pilot names; mission titles and secret goals; the opening history crawl; Global Meetings, briefings and Situation Archive conversations; hangar and in-mission dialogue and HUD alerts for all 35 mission slots across both story routes; meeting-picture captions; and pilot battle shouts. English prologue subtitles are included. A full patch and matching v0.1.33 upgrade are provided.

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
