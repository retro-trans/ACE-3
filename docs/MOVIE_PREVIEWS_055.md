# Movie previews 0.1.55

Local MP4 review artifacts only. The user requested viewing these before any game patching. No ISO, PSS, release patch or published release is modified by this workflow.

## Scope

| Source | Preview | Review status |
| --- | --- | --- |
| MOVIE001 | Opening song, romaji above English in an added bottom band | Partial Whisper lyric draft; unresolved phrases are visibly marked |
| MOVIE003 | Axis sequence, 48 English dialogue cues | Meaning reviewed against source captions and Whisper |
| MOVIE004 | Short transition | No reliable speech detected; no invented captions |
| MOVIE005 | Alternate short transition | No reliable speech detected; no invented captions |
| MOVIE006 | Resonance / two Earths sequence, 11 English dialogue cues | Meaning reviewed; short speaker name Sara remains ambiguous |

MOVIE002 is the previously translated prologue. The voices during the engine-rendered staff credits are separate from these five PSS movies and are not covered by these previews.

## Local preparation

Sources are the user's extracted PSS files under `work/build/movie_test`. `tools/prepare_movie_whisper.py` validates the Sony PCM audio header, deinterleaves the stereo blocks and writes WAV files plus local Whisper drafts under ignored `work/build/movie_previews_055`. It runs without writes by default; `--transcribe` opts into extraction and local inference.

Transcription used faster-whisper on CPU with int8 computation: small for the first pass, large-v3-turbo for comparison and large-v3 for the opening song. Japanese transcription, no speech translation mode, beam size 5, word timestamps and no previous-text conditioning were used. VAD was enabled for the first pass and disabled for the larger-model comparisons. All model inference ran locally. Large-model song results include hallucinations and are not a reliable complete lyric transcript.

English translations and romaji live in `work/translation/en/movies_055`. Each document records its review status, uncertainty and source timing. Full Japanese drafts and all source audio/video remain in ignored local folders. Whisper output is evidence, not an authoritative transcript; unsupported credits, closing phrases and other hallucinations are excluded.

## Rendering

Run `tools/render_movie_previews.py --movies MOVIE003 MOVIE004 MOVIE005 MOVIE006` with the project's Pillow-enabled Python to inspect plans. Add `--write` only after checking the plan. Use `--movies MOVIE001` for the song. Existing MP4s are never overwritten.

The renderer writes H.264/AAC MP4s, ASS and SRT subtitles, a render log and a validation report under `work/output/0.1.55-movie-previews`. Story movies retain their original 4:3 picture at 960x720 and replace the existing subtitle band. The opening picture remains intact above a new subtitle band, producing a 960x864 preview with romaji and English. Original audio is retained through AAC encoding.

Validation reports contain source and output hashes, subtitle timings, review notes and explicit `patched_into_game: false` and `user_approved: false` flags. Layout checks reject overflowing words, excessive line counts and overlapping cue times. MP4 decode checks and sampled frames are recorded separately. These checks do not certify full audiovisual timing or resolve uncertain lyrics.

## Before game integration

Review the MP4s, resolve lyric gaps and uncertain speaker identification, and obtain the user's requested preview approval. The extra lyric band is a review presentation, not a finalized in-game layout. Any later game build needs its own format, size, playback and release validation; these files are not a game release.
