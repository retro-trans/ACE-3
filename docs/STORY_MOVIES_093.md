# Remaining story movies — 0.9.3

Integrate the existing English MP4 subtitle tracks for MOVIE003 (Axis,
48 cues) and MOVIE006 (resonance / two Earths, 11 cues). Subtitle wording,
timing and layout must match the reviewed preview ASS files exactly.
The original Japanese subtitle band is replaced within the existing frame;
the picture dimensions remain 640×448. No extra band is added.

Preserve each original frame count and rate: 30000/1001 fps for MOVIE003,
30 fps for MOVIE006. The PSS remux retains original file sizes, pack layout,
audio and every non-video packet. Video is paced to the original packet
positions and every frame receives a unique presentation timestamp. Both
outputs are fully decoded with FFmpeg's error checks, and sampled frames
are inspected before disc integration. Whole-disc comparison checks that
only these two movie extents change from test build 0.9.2.

`tools/build_remaining_movies_patch.py` plans by default. `--prepare`
creates the encoded and validated PSS files under ignored local build
storage. `--write` integrates them into a new 0.9.3 test ISO. A prepared
movie is reused only when its recorded hashes and subtitle sources match.

The original MOVIE006 short speaker label remains rendered as **Sara**;
whether the voice is Sara Kodama or Sala Tyrrell remains unresolved in the
translation notes. No full identity is asserted. Console/emulator playback
and complete human review of audio synchronization remain pending.

The opening lyrics, English prologue and live credits captions are retained.
MOVIE004/005 are short transitions with no prepared speech captions and
remain unchanged. The 0.9.1 Deployment-column fix and 0.9.2 lock-on font fix
are included. Release packaging follows `RETRO_TRANS_RELEASES.md`.
