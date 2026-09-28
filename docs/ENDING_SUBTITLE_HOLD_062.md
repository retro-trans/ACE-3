# Ending subtitle hold — 0.1.62

The user requested that subtitles remain visible for at least another 0.5 seconds unless the next line plays immediately. This local test build extends both credits tracks: dialogue and romaji/English song lyrics.

For each cue, the new display end is the earlier of its original timed end plus 0.5 seconds and the next cue's start minus two native frames. The two-frame margin preserves the existing text-slot turnover and prevents a held caption from blocking the next line. The last cue on each track gets the full extension. Cue starts, wording, music, voices and layout do not change.

All 98 native caption events are checked against their original timing. Ninety duration fields change; fourteen cues cannot receive the full hold because another line follows sooner, including eight immediately adjacent cues whose existing durations are retained. Dialogue and lyrics are capped independently, so one track does not interrupt the other.

Run `C:/Python/python.exe tools/build_credits_hold_patch.py` to inspect the plan, then add `--write` to create `work/output/ACE3-English-0.1.62.iso` from 0.1.61. The builder checks source identity, caption coverage, encoded float timing and same-track overlap, then compares every output byte against the expected duration-only edits. It preserves 0.1.61. The JSON alongside the ISO records every cue's old and new display end and the final SHA-256.

The previous build's native event playback was tested. This duration-only revision has not been replayed in the emulator, and fresh-disc ending loading remains unverified as described in `ENDING_SUBTITLES_061.md`. A state saved during the credits retains old in-memory timings; load from before the ending assets instead to test the new disc timings. No public release is created.
