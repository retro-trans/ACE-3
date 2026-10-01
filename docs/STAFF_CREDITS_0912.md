# Compressed credits fix — local test 0.9.12

Output: `work/output/ACE3-English-0.9.12.iso`, based on 0.9.11.

Built and whole-disc verified on 2026-10-01. Size: 4,447,076,352 bytes.
SHA-256: `1da2209c1e6a27662a785c45d0aed3307795a22ca999d7cab9d392f9ed1520df`.
Reading and decompressing resource 701349 from the finished ISO confirms the English staff rows and absence of Japanese in every nonblank table row.

## Diagnosis

The user reported Japanese staff credits after a fresh boot of 0.9.11. PCSX2's log confirms opening that exact ISO, resetting and executing the ELF, followed by saving slot 1; no save-state load appears in that boot session. Read-only inspection of that saved EE memory found the original staff table at address `0x01213360`, byte-for-byte identical to the table in compressed archive resource **701349**.

0.9.11 updated only plain scene **4350**. A raw-byte scan found no remaining programming-director heading because it did not decode compressed resources. Resource 701349 decompresses to the same 2,117,072-byte scene extent, with the same chunk positions and original table source hash. This is the missed runtime copy, not a stale-state explanation.

## Changes and checks

Transfer the translated STUF bundle from resource 4350 to the packed scene. Only four inner resources differ:

- 1: embedded 3x antialiased staff font texture.
- 2: complete ASCII font mapping and metrics.
- 3: English credits table, preserving all row IDs and blank/null rows.
- 107: the already translated closing story disclaimer image. The packed copy also lacked this earlier change.

All six other logo/image assets, nine graphics-command rows and other scene chunks remain unchanged. Preserve the original unpacked size and chunk boundaries, then recompress inside the original 1,332,912-byte archive allocation. The new encoded stream uses 1,276,568 bytes, with zero padding filling the rest. Archive offsets and disc size do not change.

The builder enumerates all 4,138 compressed headers in the archive; 701349 is the only packed resource matching the known credits scene extent. Validation checks each translated target, full ASCII font coverage, source hashes, row IDs, unchanged graphics commands, unrelated assets/chunks and exact equality after compression/decompression. Decoded scene SHA-256: `78e920653f0e91257d19083f84edbe417907371980de93fe71cfbfe4fe83bb73`.

`tools/build_staff_credits_packed_patch.py --write` creates the local test ISO and verifies every disc byte against 0.9.11 plus the intended packed-resource edit. Its matching JSON report records the final SHA-256 and verification results.

Translation references and the six explicitly authorized provisional name readings remain in `docs/STAFF_CREDITS_0911.md`. Main/HUD fonts, ending dialogue, song lyrics and timing are inherited unchanged. This is not a public release.

## Runtime status

The source of the Japanese runtime text is confirmed by the fresh-boot log and saved RAM. The corrected compressed payload is verified offline; visual playback of 0.9.12 is not yet confirmed. Boot 0.9.12 and enter the ending again to test the names, roles, font and closing notice. Do not reuse a state already inside the old credits.
