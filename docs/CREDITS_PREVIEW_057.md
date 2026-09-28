# Credits dialogue preview 0.1.57

This is an MP4 review artifact, not a game patch or release. The user requested a subtitled preview before integration.

The source is a new native PCSX2 recording restored from the user's earlier slot-2 state, using an isolated profile and the local 0.1.54 disc. Both memory-card slots were disabled. The original state and its local copy have matching SHA-256 hashes after capture. State files, source recordings, audio and Japanese recognition drafts remain in ignored local folders.

The capture is 356.44 seconds long. It recovers the complete opening question that was clipped in the 0.1.56 capture. Local Whisper large-v3-turbo supplies the initial transcript; local large-v3 checks short omitted or unclear sections. An independent meaning pass checks the surrounding dialogue. This is machine-audio transcription with meaning review, not a human listening verification; uncertainties are recorded in the English JSON.

English captions occupy a new band beneath the intact 640x480 picture. The postcredits scene's existing English captions are retained without duplicate overlays. The scrolling Japanese staff names are not replaced. A Japanese story disclaimer cached in the restored state also remains in the capture; that texture is outside this dialogue-preview task.

- Translation: `work/translation/en/credits_057.json`
- MP4, ASS, SRT and validation report: `work/output/0.1.57-credits-preview/`
- Local capture and recognition drafts: `work/local/credits_057/`
- Reproducible tools: `tools/transcribe_credits_preview.py`, `tools/render_credits_preview.py` (dry-run by default)

Do not integrate this preview into the game before the user reviews it. The credits are an engine-rendered sequence; a separate in-game subtitle implementation will be needed.

The user subsequently approved integration of both the credits dialogue and ending-song lyrics. The native implementation and its validation scope are documented in `ENDING_SUBTITLES_061.md`.
