# Cinematic speaker/dialogue alignment — 0.9.14

The user's Hayato screenshot shows the portrait-free cinematic dialogue starting far into the lower black band. Move both the speaker and body 90 native units left, retaining their 16-unit indent and all vertical placement.

| Text | Previous frame X | New frame X | Native signed X |
| --- | ---: | ---: | ---: |
| Speaker | 120 | 30 | -200 to -290 |
| Dialogue | 136 | 46 | -184 to -274 |

The frame is 640 units wide. The cinematic renderer at `0x233c50` loads the speaker X/Y from offsets 2/4 and body X/Y from offsets 0x22/0x24 of two 32-byte records. The matrix centers X at 320. Those records reside in resource 1 of bundle 102006. Its exact copy also occurs at offset 0x102000 in container 103000. A read-only inspection of the user's saved EE memory confirmed the original parameter values: the runtime pointer at 0x405404 led to speaker (-200,145) and body (-184,165).

`tools/build_cinematic_left_patch.py` changes only these two signed 16-bit X fields in both copies. It validates the source configuration hash, table header/records and four renderer load instructions, scans every plain archive payload for copies, and checks all compressed headers for matching configuration/container extents. It changes no font, script, executable, movie, portrait layout, timing or credit data.

Run without arguments to inspect the plan. `--write` creates `work/output/ACE3-English-0.9.14.iso` from 0.9.13 and compares every output byte against the base plus exactly the four planned edits. Metadata is saved in `work/ui/cinematic_left_0914/layout.json` and the ISO's adjacent JSON report. This is a local test; fresh-boot runtime rendering remains unverified. A save state made after loading the old configuration can retain its previous coordinates.
