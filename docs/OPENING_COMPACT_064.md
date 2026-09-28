# Compact opening subtitles — 0.1.64

The user approved the 0.1.63 MP4 and requested game integration. This build replaces the opening video in 0.1.62 with the approved layout, preserving the ending dialogue and song-caption timing changes.

All 19 bilingual cues use the exact subtitle script from the preview: Georgia at native sizes 14 and 15, romaji at y=390, English at y=408, with an outline and light shadow. The original 640x448 picture is retained without the previous added subtitle band or reduction in picture size. Wording and timing match the approved opening preview.

`tools/build_opening_compact_patch.py` runs without writes by default. After inspecting the dry run, `--prepare` encodes and verifies the native MPEG-2/PSS movie; `--write` creates `work/output/ACE3-English-0.1.64.iso` from 0.1.62. Prepared media and extracted verification frames remain in ignored `work/build/opening_064`.

Validation requires an exact match to the approved ASS script and translation hash, the original movie hash, 4,980 distinct frame timestamps spaced at 3,000 ticks, preservation of every non-video packet, full video decoding and exact whole-disc comparison against the single intended movie replacement. The source and destination disc hashes are recorded beside the ISO. Original movie audio is preserved byte-for-byte. The game-format output is sampled visually at 65 and 125 seconds.

This is a local test build, not a public release. Native emulator playback of the newly encoded opening is not yet verified. The earlier ending-load limitations remain unchanged.
