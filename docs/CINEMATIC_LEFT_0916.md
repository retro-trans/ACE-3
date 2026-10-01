# Cinematic alignment adjustment — 0.9.16

The user requested a 60-pixel leftward shift instead of 90. Relative to the original 640-wide coordinate frame, the speaker now starts at X 60 (originally 120) and the dialogue at X 76 (originally 136).

Compared with 0.9.15, both move 30 native pixels to the right. Their native signed X values change from -290 to -260 and -274 to -244. Y remains 145 and 165; the dialogue retains its 16-pixel indent.

`tools/build_cinematic_60px_patch.py` reuses the coordinate scanner and verification from `build_cinematic_left_patch.py`. It updates two signed 16-bit fields in resource 1 of configuration 102006 and its identical copy at container 103000 offset 0x102000. All other disc bytes, including the 0.9.15 CAUTION correction, are preserved.

Run with `--write` to create `work/output/ACE3-English-0.9.16.iso`. The adjacent JSON contains the final checksum and whole-disc verification result. Coordinate metadata is in `work/ui/cinematic_left_0916/layout.json`. This is a local test build; use a fresh boot because save states can retain old coordinates.
