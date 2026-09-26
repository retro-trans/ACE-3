# Menu drawing capacity — 0.1.5

**Superseded by 0.1.9:** increasing this capacity did not resolve Campai/Loa because the patched callback did not reach the actual main-menu allocations. Version 0.1.9 removes these hooks and repairs the UI layout descriptors. Full labels and pause/resume have now been verified from a fresh boot; see [the actual allocation fix](TECHNICAL.md). The historical instruction-level tests below did not establish correct callback selection.

The user's 0.1.4 captures show Campaign as “Campai,” Load as “Loa,” Initial Setup as “Init,” Confirm as “Co,” and similarly incomplete settings values. The truncation persists on an unobscured settings screen. Missing-letter question marks are gone. This separates the remaining drawing-capacity problem from the corrected font lookup.

## Evidence in SLPS_257.84

- Main-menu text binding at virtual address `0x2faa20` loads resource 36 (table 3036) and binds menu choices using `0x1b60c0`.
- Initial-setup text binding at `0x306f90` loads resource 65 (table 3065), binding the title, labels, difficulty/control values, descriptions, and automatic-altitude label.
- Their text initialization callbacks are `0x2fab70` and `0x307150`. Both finish by setting the widget's text resource through `0x2b6f10`.
- Text-state initialization at `0x2b6358` reads the widget's capacity from descriptor offset `0x62`, supplies 32 when zero, and stores it as a byte at text-state offset `0x1b`.
- Drawing-buffer initialization at `0x2b63a0` reads that byte with `lbu` and calls `0x1aece0` before allocating the buffer. The size calculation is `(7 * capacity + 11) * 16` for nonzero capacity.
- Other existing callbacks already override this byte through `0x2b6fb0`. The new patch uses that same field, before allocation, specifically in the two translated menus.

## Patch

Two five-instruction tails are replaced at `0x2fac34` and `0x30721c`. The helper being inlined is also checked byte-for-byte. Addresses are mapped through the ELF program header; the patcher does not assume ISO addresses from the virtual address alone.

```asm
ld    ra, 0x40(sp)       # restore the callback's saved return address
lw    v1, 0x98(s0)       # widget's existing text-state pointer
sw    s2, 0x20(v1)       # same resource-pointer store as the old helper
addiu a0, zero, 128
sb    a0, 0x1b(v1)       # capacity before drawing-buffer allocation
```

Execution falls through into the original saved-register restoration and return. The early exit for non-text widgets is unchanged. No new code section, atlas, glyph artwork, font metric, translation wording, or global buffer-size override is introduced.

128 is within the field's unsigned-byte range and accommodates every current target string in tables 3036 and 3065, including the complete multi-line control description. The build rejects a future target longer than this capacity. The relevant buffer size is 14,512 bytes per text widget at capacity 128; this increases menu memory use. Actual boot and navigation still need the user's emulator test.

## Verification and limits

`tools/test_ui_capacity.py` executes the actual original and replacement instruction sequences in a small bounded MIPS interpreter. It covers both callbacks, existing/new resource pointers, nine previous capacities, call/branch delay slots, saved return address, callee-saved registers, and all memory bytes. Only the intended capacity byte differs after both paths reach the original epilogue. This is a callback-tail test, not a complete PS2 emulator or a rendering test.

The original resource/font tests remain in place. The ISO builder validates all bytes against the original plus the planned patches and records hashes. The new ISO contains the four existing 0.1.4 archive patches plus the two executable patches. It retains the original image size and file extents.

The source captures and measured defects are in the 0.1.4 regression report (local artifact). The controller diagram's Japanese question and captions remain a separate, previously documented insertion task.
