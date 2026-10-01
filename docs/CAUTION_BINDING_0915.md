# CAUTION rendering regression — 0.9.15

The user reported a garbled label after the 0.9.13 font change. The correct body warning still renders, while the header samples pieces of the shared UI artwork. Version 0.9.14 inherited this issue.

## Cause

The earlier implementation added a second material to the frame object, assuming that each material selected its own texture. The sprite draw routine at ELF address `0x2b45e0` resolves the first material's texture through `0x2aec40` at `0x2b4628` and emits its TEX0/TEX1 values before the material loop. The loop at `0x2b46cc` through `0x2b48d0` advances the materials without rebinding their textures. Consequently, both the five frame strips and seven font strips sampled texture 50101. The previous offline comparison did not model this restriction.

This is not evidence of a missing or corrupt HD font resource. Font and sprite lookups both use `0x2aec40`; adding a second copy of the texture would not fix this object-level binding error.

## Change

In bundles 4002050, 4002054 and 4002057, layout 35 resource 0 now has a separate label object (node 8). Frame node 2 keeps only its original five active strips on texture 50101. The label's first and only material uses the existing seven glyph strips and font texture 2000.

The nine-node table is appended to the layout and the header points to it. All existing vertex, UV, color and strip arrays retain their offsets and bytes. Existing nodes retain their original indexes, bindings and appearance; only node 2's active material count changes. No texture or executable changes are made.

Layout 35 resource 1 receives an additional animation record, linked as the frame's sibling. It shares the frame's original motion payload and has no children. The eight-record table is appended and its internal links are relocated. Original motion data and keyframes are retained. This arrangement still requires checking during panel entrance, exit and menu transitions in the emulator.

## Validation and use

`tools/build_caution_binding_patch.py` defaults to structural validation; `--write` produces the versioned local test ISO from the SHA-256-locked 0.9.14 base. It checks material bindings, node preservation, animation graph references/reachability, shared motion payload, nested bundle readback and unchanged unrelated resources. The disc builder verifies all 10,344 archive payloads and all 133 ISO files.

Output: `work/output/ACE3-English-0.9.15.iso`. The adjacent JSON records the final hash and build verification results. Metadata is in `work/ui/caution_0915/layout.json`.

Runtime rendering is not yet verified. Boot the new ISO fresh and check the memory-card warning through the Load menu. Confirm a legible CAUTION label, unchanged frame/body text and normal panel animation. The cinematic speaker/dialogue alignment from 0.9.14 is preserved.
