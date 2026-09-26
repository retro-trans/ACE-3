"""Expand text drawing capacity in the two translated menu initialization callbacks.

Addresses refer to SLPS_257.84's loaded ELF segment, not ISO offsets.
The original callback tail calls the resource-pointer setter and then restores ra.
The replacement performs the same pointer store inline, restores ra, sets capacity,
and falls through to the unchanged register-restoration epilogue.
"""
import struct

CAPACITY = 128
SITES = (
    {'id': 'main_menu', 'va': 0x2fac34, 'epilogue': 0x2fac48,
     'words': (0x0200202d, 0x0c0adbC4, 0x0240282d, 0x1000ffdb, 0)},
    {'id': 'initial_setup', 'va': 0x30721c, 'epilogue': 0x307230,
     'words': (0x0200202d, 0x0c0adbC4, 0x0240282d, 0x1000ffdb, 0)},
)


def replacement():
    # ld ra,0x40(sp); lw v1,0x98(s0); sw s2,0x20(v1);
    # addiu a0,zero,128; sb a0,0x1b(v1)
    return struct.pack('<5I', 0xdfbf0040, 0x8e030098, 0xac720020, 0x24040000 | CAPACITY, 0xa064001b)


def plan_capacity(elf, iso_base):
    if elf[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('Expected little-endian ELF32')
    phoff = struct.unpack_from('<I', elf, 28)[0]
    phsize, phcount = struct.unpack_from('<HH', elf, 42)
    segments = [struct.unpack_from('<8I', elf, phoff + i * phsize) for i in range(phcount)]
    patches = []
    # Verify the exact helper being inlined: set widget->text_state->resource.
    helper = bytes.fromhex('9800848c2000838c0200651000000000200085ac0800e0030000000000000000')
    def file_offset(va, length):
        for kind, offset, start, _, filesz, _, _, _ in segments:
            if kind == 1 and start <= va and va + length <= start + filesz:
                return offset + va - start
        raise ValueError('Patch outside a file-backed ELF segment')
    helper_offset = file_offset(0x2b6f10, len(helper))
    if elf[helper_offset:helper_offset + len(helper)] != helper:
        raise ValueError('Text resource setter differs from the inspected executable')
    for site in SITES:
        before = struct.pack('<5I', *site['words'])
        offset = file_offset(site['va'], len(before))
        if elf[offset:offset + len(before)] != before:
            raise ValueError('Menu callback preimage mismatch: ' + site['id'] + ': ' + elf[offset:offset + len(before)].hex())
        patches.append({'kind': 'menu_capacity', 'menu': site['id'], 'offset': iso_base + offset,
                        'virtual_address': site['va'], 'capacity_glyphs': CAPACITY,
                        'before': before, 'after': replacement()})
    return patches
