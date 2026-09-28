# Ending subtitles — 0.1.61

This local test build integrates the approved credits dialogue (0.1.57) and ending-song romaji/English lyrics (0.1.60) into the live credits. It builds on 0.1.59, retaining the approved opening lyrics. It is not a published release.

## Implementation

- 72 dialogue cues and 26 bilingual song cues use the game's two existing STUF text slots. Lyrics appear at the top; dialogue appears at the bottom.
- Add native type-0x1000/event-25 tracks to POLY clips 7–22 of resource 3823496. Append caption tracks as root siblings, preserving the original animation, camera, audio and event tracks.
- Relocate the scene text table in resources 6350, 2002350, 3200350 and 3201350. Preserve every existing text ID, null slot and string; add IDs 10001–10098.
- Restrict staff-name drawing to baselines 64–351 so names do not cross the new captions. A 168-byte loop is reassembled within the existing staff-only function at 0x0030EAD0. Font size, roll speed and all staff names remain unchanged. No executable segment or code cave is added.
- Reassemble the existing 304-byte credits draw function at 0x0030E380 to clip scrolling logos to y=64–363 and draw captions afterward at full height. Standalone images use their original bounds when the roll is inactive. This prevents the IKONOS/JSI logo section from covering the dialogue.
- The original ending audio remains intact. The MP3 is a timing reference, not replacement audio. The postcredits scene keeps its existing English dialogue.

## Timing and wording

Nine independent 12-second waveform comparisons at recording times 5, 30, 60, 100, 150, 200, 250, 280 and 310 seconds match the supplied MP3. Song time is approximately `14.554918 + 0.99994404 × recording time`. The source recording begins 157 animation frames into clip 7. Convert its 59.94 Hz presentation time to the animation's nominal 60-frame timing.

The user's subsequently supplied English lyrics agree with the draft's overall meaning and support omitting the extra *ai wo* suggested by one recognition crop. They do not resolve the sung pronunciations *idaku/daku* or *jikuu/toki*. This build uses the approved preview readings and omits review annotations from the in-game display. Original uncertainty notes remain in `work/translation/en/ending_song_060.json`.

## Validation and reproduction

Run `tools/build_credits_subtitles_patch.py` first for the dry-run plan; `--write` produces `work/output/ACE3-English-0.1.61.iso`. The builder checks caption coverage, glyphs, widths, timing, overlap, source-disc hash, original text preservation and chunk structure. It verifies all 10,344 archive payloads and all 133 disc files; after the staff-loop edit it verifies the expected executable change and every other disc file again.

Runtime testing uses a disposable copy of the user's credits state and an isolated PCSX2 profile with memory cards disabled. Because the state already caches the old ending assets, the diagnostic test obtains a block from the game's own allocator, installs the new caption data there, and invokes the native clip loader. Diagnostic callbacks are removed before visual playback. This tests the native caption tracks and staff-name layout, but does not establish that a fresh-disc run loads the enlarged ending resource successfully. Source states, RAM, diagnostic scripts and screenshots remain ignored locally.

The native playback test observed all 98 caption IDs, with none missing. Captures at approximately 10, 120 and 260 seconds confirm simultaneous lyric and dialogue events. The 120-second capture exposed scrolling-logo overlap; after applying the final draw-function change, a repeat capture confirms the logos stop above the dialogue. These checks verify event delivery and sampled layout, not a line-by-line human review of audio synchronization.

The test interface is PCSX2's [PINE implementation](https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2/PINE.cpp). The original save state and memory cards are not modified.

Use a fresh boot and a memory-card save, or a state made before the ending assets load, for final disc-path verification. Restoring the existing credits state restores its cached older code and resources.
