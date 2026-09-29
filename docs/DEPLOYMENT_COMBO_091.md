# Deployment team-summary captions — 0.9.1

The reported blank first column contains **Combo Attack** and **Damage**.
Both English strings are present in release 0.9.0's table 3013. In bundle
4002053, layout 9, their native-font widths are 141 and 77 units, exceeding
their respective 125.05- and 75.57-unit local text boxes. This provides a
layout explanation consistent with the blank single-line captions.

The local test build widens those boxes to 149 and 85 units. It shifts the
two column separators and adjacent values right by 74 units, leaving at
least six units between the caption boxes and separators. The level box's
right edge stays fixed; its remaining width exceeds 276 units. The numeric
damage box retains its width. All changes are baked into vertex geometry,
preserving native origins, scales, bindings, allocations, borders and text.

The builder checks the source layout hash, node types/bindings, native font
widths, clearances and allowed bytes. Its `--write` mode verifies the entire
output disc against the intended edit and release 0.9.0's SHA-256.

Run `C:/Python/python.exe tools/build_deployment_combo_labels_patch.py` for
a read-only plan; add `--write` to create the versioned local test image.

In-game rendering is not yet verified. Fresh-boot the test image and load a
normal memory-card save, then open Deployment and inspect both captions
with different teams, including a special combo showing `+ EX`. Do not use
an emulator save state containing the old layout. No public release is
created by this builder.
