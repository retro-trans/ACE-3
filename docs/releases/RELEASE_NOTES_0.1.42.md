# ACE3 English 0.1.42

English fan translation of *Another Century's Episode 3: The Final* (PS2, SLPS-25784).

## Changes since 0.1.35

- Translate abilities, support details, unit command lists, shared action instructions and pause-map names.
- Translate remaining model/Results names and shared confirmation prompts, including Yes/No.
- Separate overlapping Victory/Defeat headings from their objectives in the pause menu.
- Fit overflowing communication text into three lines so linked terms such as Londo Bell remain visible.
- Fix missing text between Encyclopedia pages while preserving all wording and glossary links.
- Complete the memory-card operation warnings and fit long option labels.
- Rename labels to **Purchasable**, **Combo scene**, **Comm messages**, **Camera Movement** and **Situation Report**.

## Automatic patching with Retro Trans

Open [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest), click **Refresh catalog**,
and use **Automatic** to select your original Japanese ISO or matching published 0.1.35 ISO. For an original
disc, choose **Original prologue** or **English prologue** in the **Binary** list, leave **Target** on **Latest**,
and choose a new output filename. Both editions translate the game text; English prologue also translates the
opening movie subtitles. The tool selects, downloads and verifies the appropriate patch.

The 2026-09-26 packaging update adds `BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt`.
All four existing xdelta files and their resulting game images are unchanged.

## Choose one patch

| File | Required source | Result |
| --- | --- | --- |
| `ACE3-English-0.1.42.xdelta` | Original Japanese ISO | English text; original prologue movie |
| `ACE3-English-0.1.42-movie.xdelta` | Original Japanese ISO | English text and English prologue subtitles |
| `ACE3-English-0.1.35-to-0.1.42.xdelta` | Published 0.1.35 text ISO | English text; original prologue movie |
| `ACE3-English-0.1.35-to-0.1.42-movie.xdelta` | Published 0.1.35 movie ISO | English text and English prologue subtitles |

Full patches are alternatives; do not apply them on top of each other. Update patches require the matching
published 0.1.35 edition, not a local test ISO. If unsure, use a full patch with your original disc dump.

Apply with xdelta3 or Delta Patcher. For example, for the full movie edition:

```text
xdelta3 -d -s "Another Century's Episode 3 - The Final (Japan).iso" ACE3-English-0.1.42-movie.xdelta ACE3-English-0.1.42.iso
```

Boot the patched ISO fresh in PCSX2 and load a normal memory-card save. Older save states retain old text in memory.

## Verification and known limitations

The build verifies all 10,344 archive payloads and all 133 disc files. Release patches are decoded and compared
with the intended ISO by size and SHA-256. The text and movie editions differ only in the prologue movie data.
This release has not yet been tested in-game; the recent layout and pagination fixes still need runtime confirmation.

Some image-based labels (including Player Sorties and the "battle stations" briefing banner) and the burned-in
subtitles of two late-game movies remain Japanese. The text edition also retains the original prologue movie.

The release disc retains the original file order, with DATA.BIN enlarged and later files moved accordingly.
Its hash differs from the local test build. Patch checksums and exact input/output hashes are supplied in the
attached SHA256SUMS file and manifest.

## Required source ISO hashes

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| Original Japanese ISO | 4,447,076,352 | `5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705` |
| Published 0.1.35 text ISO | 4,452,986,880 | `15f69e6ca194b8f8a58ca8e0cc84b54e946923b1efe732345015a81443f61da3` |
| Published 0.1.35 movie ISO | 4,452,986,880 | `db226b8474d3b7f833eff553d78743f7f78d20d2cb3cd78e75a67a67a901d70c` |

## Resulting 0.1.42 ISO hashes

Both editions are **4,455,411,712 bytes**. Full and update patches produce identical output for the same edition.

| Edition | SHA-256 |
| --- | --- |
| Text | `ad9dffa95cf8b8144c13d25c014d73992574c6f50ce4518661ac9c2be486557d` |
| English prologue | `c72752b32b5982b63ef8c5db5f171090469e3aad94999245cace2cb760565353` |
