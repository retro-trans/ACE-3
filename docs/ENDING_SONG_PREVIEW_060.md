# Ending song lyric preview — 0.1.60

This is a review video for the user-supplied `02. Poem of Love.mp3`, lasting 366.84 seconds. Its title follows the filename. It does not modify the game, replace a movie, or establish synchronization with the engine-rendered credits.

The source SHA-256 is `bb8949e1376c0de9dd392345933b0cd84beab816097ba970ef952b57162b9ad4`. The original MP3 is unchanged and ignored by Git. Japanese machine transcripts and the detailed source-language review stay under ignored `work/local/ending_song_060`.

## Recognition and meaning review

Local faster-whisper large-v3-turbo and large-v3 ran Japanese transcription with beam size 5, word timestamps, four CPU threads, int8 computation, no previous-text conditioning and no voice-activity filtering. Three targeted verse checks recovered passages missed by whole-track recognition. An additional short crop produced only a hallucinated closing phrase and was rejected.

An independent meaning reviewer examined all 27 turbo rows, 33 large rows and 14 targeted-check rows together, including adjacent verses. Credits, social-media tags and thanks-for-watching hallucinations were excluded. Targeted recognition corroborated the ordinary-person line, the lose-heart phrase, the smile/listening verse and the repeated mother-planet line.

The English/romaji document contains 26 captions. Timings are a draft based on recognition segments and words. It has not received human listening verification. Wordless vocalizations are not converted into invented lyrics; gaps show `[Music]`.

## Specific review points

| Time | Question |
| --- | --- |
| 00:37 and 05:09 | Is the sung reading **idaku** or **daku**? The recognized written form permits either. |
| 02:02 | Is **ai wo** sung before **nakushita**? One targeted pass adds it; both whole-track passes omit it. The draft omits it provisionally. |
| 04:45 | Is the recognized time-and-space word sung **jikuu**, or with a special reading such as **toki**? |

These four captions carry visible review notes. First person follows the song's *boku*, and *you* follows *kimi*; neither implies gender. “My name” is a contextual inference from the surrounding recollection. The water phrase means holding/brimming with water, and *hazu* indicates expectation rather than certainty.

## Preview and reproduction

The local output folder is `work/output/0.1.60-ending-song-preview/`. It contains `Ending_Song_Romaji_English_preview.mp4`, bilingual ASS/SRT subtitles and `validation.json` with hashes and review metadata. The 1280×720 H.264/AAC presentation includes romaji above English, the supplied music, a waveform and a playback clock.

Use `tools/transcribe_song_preview.py AUDIO OUTPUT_JSON` for a dry-run transcription plan; add `--write` to run locally. Japanese output paths must be inside `work/local`. `--model large`, `--start` and `--end` support comparison crops.

Use `tools/render_song_preview.py AUDIO work/translation/en/ending_song_060.json OUTPUT_DIR` to validate captions and inspect the rendering plan. Add `--write` to create the preview. The renderer checks the source hash, review status, text fit, timing bounds and overlap; refuses to replace an existing preview; and decodes the entire completed MP4 with errors treated as failures.

User review of wording, romaji and timing is required before any future game integration. This preview is not a published game release.

The user subsequently requested integration alongside the credits conversation. Their supplied English lyrics corroborate the overall meaning and omission of the disputed extra *ai wo*, but do not resolve the two pronunciation questions. See `ENDING_SUBTITLES_061.md` for native timing and integration details.

## Validation result

The completed MP4 is 38,144,042 bytes, duration 366.84 seconds, SHA-256 `2bd6bb098827f82940ea32a51cbd21bf01f5f45941aa0e4cc3a3234ee2f97e9c`. Full audio/video decoding passed. Sampled frames at 02:05 and 04:12 show readable romaji, English and review notes without clipping or overlap. These checks do not replace listening review.
