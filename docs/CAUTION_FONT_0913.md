# CAUTION label — local test 0.9.13

Built on 2026-10-01: `work/output/ACE3-English-0.9.13.iso`, 4,447,076,352 bytes. SHA-256: `cb62b115d750ba4fa534c3e69e6979c37452fd67c1048e99c337a174726c659c`. All 10,344 archive payloads and 133 disc files passed verification. Runtime rendering is not yet verified.

The user reported that CAUTION still looked blurry beside the sharper memory-card warning text. It is an image inside the shared 128x128 interface atlas (resource 50101), not a string rendered by the upgraded font.

**Superseded:** The user reported a garbled header. The renderer binds only the first material's texture for this object, so the second material below did not select the font atlas. See [the 0.9.15 correction](CAUTION_BINDING_0915.md). The original offline comparison was insufficient to verify runtime rendering.

The attempted fix changes layout 35, mesh node 2, in menu bundles 4002050, 4002054 and 4002057. Its fourth quad strip was the old CAUTION label. Preserve the five frame/marker strips using texture 50101 and replace the caption with seven quads using glyph UVs from font 2500 / texture 2000. This reuses the embedded HD serif letters and their existing graphics-memory allocation. Each bundle's own font is consulted; their atlas layouts are not assumed identical.

The new cell height is 16 native units, positioned beside the original marker with a small horizontal gap. Character bearings, widths and advances come from the existing menu font. No font, palette, texture, warning text, card-operation behavior or other widget is changed. The old label geometry remains inert in the resource but is removed from the active strip list.

Validation covers the source layout hash, old caption indices, preserved frame strips, complete glyph coverage, new material/strip descriptors, vertex/UV/color bounds, unchanged original layout bytes outside the mesh pointers/counts, and preservation of every other bundle resource. No compressed archive header has a decoded size matching any of the three source menu bundles. The disc builder also verifies every archive payload and disc file.

`tools/build_caution_hd_patch.py` produces the decoded-font comparison and layout metadata by default; `--write` builds `work/output/ACE3-English-0.9.13.iso` from 0.9.12. Reconstructed previews are not emulator captures. The native rendering of the new font-atlas material remains pending a fresh-boot check of the memory-card warning panel. Existing credits, dialogue and song fixes are inherited.
