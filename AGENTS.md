** Organize folder like this **
work - work folder
    output - contains the file for testing (iso, zip, etc...)
    glossary - contains the one or many json files for glossary
    ui - contains screenshot of actual UI element ingame with label on screenshot if possible, contains files (json,py,...) describe the coordinate, width and height, id and other attributes
    translation/<language code> - contains the target translation of ui element or dialogues or anything that need translation
docs - documents
tools - any tools help with translation

** SOME RULES **
- Avoid contains extensive Japanese scripts (UI elements is fine)
- Identified each build with version 0.x.y (start at 0.1.0)
- Always write change log
- If user told you to remember anything write it down here, make sure to ask user if the new one conflict with old one

** REMEMBER **
- Publish only the English prologue edition. The user discontinued the non-movie / Original prologue patches on 2026-09-26, including older release downloads. Keep the README and release instructions focused on the supported edition; retain withdrawn identities only where needed for catalog integrity.
- Every new release must work with [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools). Follow `docs/RETRO_TRANS_RELEASES.md` and the current upstream release standard: include the canonical manifest, validation report, checksums and all listed patches; decode-verify every patch and pass the upstream release validator before publishing. Verify catalog registration and automatic patch routing after publishing before considering the release complete. Preserve stable game/edition identities and never overwrite published patches with different bytes.
