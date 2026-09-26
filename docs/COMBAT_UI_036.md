# Combat UI translation — 0.1.36

Based on 0.1.35. This pass covers the four user screenshots: support details, abilities, pause-map names, and unit command lists, including other entries in those categories.

Recommended local test image: 0.1.36 with the existing English prologue movie (local build). Text-only variant (local build). The movie-inclusive disc passed whole-disc comparison: only MOVIE002 differs from the verified text build. SHA-256: `0c8e8088a9ed4499d0f3071c76b627b52114a16432346bfadb1ea07a88a5a170`.

## Coverage

- Table 3079: all 338 non-null rows — 43 abilities, 25 stock developer description stubs, 90 support names, 90 categories, and 90 activation conditions. Four menu copies updated.
- Nested table 3049: all 104 unit command lists, 1,966 rows represented by 432 distinct source strings. Both menu copies updated. Blank rows and the fullwidth dash placeholder remain intact.
- Tables 3023/3020: 136 shared action and controller-input rows reviewed, including repeated presses and hold modifiers. Existing button glyphs remain unchanged.
- Tables 3061–3063: 191 unit, projectile/object, and ship labels reviewed. Existing `MLRS` needs no change.
- Scene-specific pause-map names: 168 distinct Japanese names reviewed; the builder also preserves unknown-name placeholders as `???`. All matching singleton tables in the four mission-resource families are patched, including training/free-battle resources.
- Original model copies: command-list and unit-title chunks are translated together with their compressed twins. A legacy Nirvash spec2 spelling is matched to the existing unit glossary.

Examples include **Glider**, **Spin Laser Sword**, **Single-Target Attack**, **Player hit by a combo**, **Nadesico B**, **Missile Pod**, **Steel Wire**, **Ion Bullet Rifle**, and **Laser Edge**. The JSON files contain the exact display wording.

## Meaning and naming review

Independent review files accompany the three translation files under `work/translation/en`. Review corrections restore Cannon in the focused Triple Mega Sonic weapon, use Earth Escape Technique, and align Berkt, Rushrod, Ark Rifle, and Seven Swell with the project glossary. Justice's command context resolves the ownership of Bassel.

Some game-original Romanizations remain provisional. The unused action category `Throw Melee Attack` could also mean Slow; no record in the 104 command-definition tables uses it. The [Akurasu support list](https://akurasu.net/wiki/Another_Century%27s_Episode_3%3A_The_Final/Support_Skills) uses Slit Wafer while its [mech database](https://akurasu.net/wiki/Another_Century%27s_Episode_3%3A_The_Final/Mech_Database) uses Slit Waver. This build consistently retains Slit Wafer, matching the source and the support list. Fan-reference spellings are not certified as official localizations.

## Layout and data integrity

The command tables have a zero first header word rather than the ordinary 65536; the builder preserves that format. Shared menu tables receive new string pools. Embedded scene/model tables are repacked inside their existing extents with IDs and null slots preserved. Consecutive index ranges and duplicate strings are coalesced; the existing, reverse-engineered compact singleton layout is used where needed. Scene script offsets and model chunk boundaries do not move.

Widths are checked with both menu and gameplay fonts. Support fields use a 280-unit limit and commands 410; longer names use explicit abbreviations with full meanings retained in the translation records. This pass changes no executable code or font textures.

Build command: `python tools/build_combat_ui_patch.py --inspect-draft` for inspection, then `python tools/build_combat_ui_patch.py --write`. `tools/test_combat_ui_patch.py` checks zero-format tables, null slots, overflow rejection, complete built-disc command/support coverage, and unchanged bytes outside scene/model text extents. The builder also verifies compressed twins and every archive payload/disc file.

## In-game check

The text ISO passed all 10,344 archive payload checks, all 133 disc-file checks, eight combat-UI tests, and four boot-metadata regression tests. Its SHA-256 is `5ce1cde7eeb0dc53d8c83c2224742cc70d8d628b6b1e57b0bfc3d67c55543fc8`. The saved build report records 416 changed resources, including 111 compressed twins; 1,999 scene label instances were patched across the mission-resource copies. Build-input hashes match the manifest.

Boot the new ISO fresh and load a normal memory-card save. Old emulator save states can retain previous text resources. The user controls navigation.

1. Select Dragonar-1 Custom as player and ally. Check Glider and all three support fields.
2. Browse other allies, especially units with long support names and AP activation thresholds.
3. In Mission 02, open Pause → Map Info and select the mothership. Check Nadesico B.
4. Open Ixbrau's Command List and scroll through all weapons and follow-ups. Check button glyphs and hold instructions.
5. Return to play, finish the mission, and check that briefing-to-hangar navigation still works.

Runtime rendering and transitions are not certified by offline checks. The separate baked Japanese **Player Sorties** sprite in the statistics panel remains unchanged, as do unrelated baked-image text and the two outstanding movie subtitle tracks.
