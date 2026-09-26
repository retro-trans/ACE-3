"""Supplement sparse game fonts with glyphs from the game's complete font.

No system font or generated artwork is used. Original glyphs and their sampled
pixels are preserved. GS address layout reference:
https://github.com/PCSX2/pcsx2/blob/master/pcsx2/GS/GSTables.cpp
"""
import struct
from build_ui_patch import require, u32
from ui_font import font_map, patch_font


def address4(x, y, width):
    page = y // 128 * (width // 128) + x // 128
    bx, by = x // 32 % 4, y // 16 % 8
    block = (bx & 1) * 2 + (bx & 2) * 4 + (by & 1) + (by & 2) * 2 + (by & 4) * 4
    column = ((x & 1) << 3) | ((x & 2) << 4) | ((((x >> 2) ^ (y >> 1) ^ (y >> 2)) & 1) << 6)
    column |= ((x & 24) >> 2) | ((y & 1) << 4) | ((y & 2) >> 1) | ((y & 4) << 5) | ((y & 8) << 5)
    return page * 16384 + block * 512 + column


def address32(x, y, width):
    page = y // 32 * (width // 64) + x // 64
    bx, by = x // 8 % 8, y // 8 % 4
    block = (bx & 1) + (bx & 2) * 2 + (bx & 4) * 4 + (by & 1) * 2 + (by & 2) * 4
    column = (x & 1) + (x & 6) * 2 + (y & 1) * 2 + (y & 6) * 8
    return (page * 2048 + block * 64 + column) * 4


def texture_pixels(texture):
    tex0 = struct.unpack_from('<Q', texture, 16)[0]
    width, height = 1 << ((tex0 >> 26) & 15), 1 << ((tex0 >> 30) & 15)
    length = u32(texture, 4)
    require((tex0 >> 20) & 63 == 20 and length == width * height // 2, 'Expected PSMT4 atlas')
    raw = texture[32:32 + length]
    if u32(texture, 12) == 0:
        pixels = bytes(v for byte in raw for v in (byte & 15, byte >> 4))
    else:
        require(u32(texture, 12) == 1, 'Unknown atlas transfer format')
        vram = bytearray(length)
        transfer_width = width // 2
        for y in range(height // 4):
            for x in range(transfer_width):
                target = address32(x, y, transfer_width)
                source = (y * transfer_width + x) * 4
                vram[target:target + 4] = raw[source:source + 4]
        pixels = bytearray(width * height)
        for y in range(height):
            for x in range(width):
                address = address4(x, y, width)
                pixels[y * width + x] = (vram[address // 2] >> ((address & 1) * 4)) & 15
    return width, height, pixels


def encode_pixels(texture, pixels):
    width, height, _ = texture_pixels(texture)
    raw = bytearray(width * height // 2)
    if u32(texture, 12) == 0:
        for i in range(len(raw)):
            raw[i] = pixels[i * 2] | pixels[i * 2 + 1] << 4
    else:
        vram = bytearray(len(raw))
        for y in range(height):
            for x in range(width):
                address = address4(x, y, width)
                vram[address // 2] |= pixels[y * width + x] << ((address & 1) * 4)
        transfer_width = width // 2
        for y in range(height // 4):
            for x in range(transfer_width):
                source = address32(x, y, transfer_width)
                target = (y * transfer_width + x) * 4
                raw[target:target + 4] = vram[source:source + 4]
    return texture[:32] + raw + texture[32 + len(raw):]


def complete_font(font, texture, donor_font, donor_texture):
    aliased, aliases = patch_font(font)
    mapping, glyph_start, count = font_map(aliased)
    donor_map, donor_start, _ = font_map(donor_font)
    width, height, original_pixels = texture_pixels(texture)
    dw, dh, donor_pixels = texture_pixels(donor_texture)
    occupied = bytearray(width * height)
    records = bytearray(aliased[glyph_start:glyph_start + count * 24])
    for i in range(count):
        left, top, right, bottom = struct.unpack_from('<4f', records, i * 24)
        x0, y0, x1, y1 = round(left * width), round(top * height), round(right * width), round(bottom * height)
        for y in range(max(0, y0 - 1), min(height, y1 + 1)):
            for x in range(max(0, x0 - 1), min(width, x1 + 1)):
                occupied[y * width + x] = 1
    protected = bytes(occupied)
    pixels = bytearray(original_pixels)
    palette = texture[32 + u32(texture, 4):u32(texture, 0)]
    donor_palette = donor_texture[32 + u32(donor_texture, 4):u32(donor_texture, 0)]
    require(len(palette) == len(donor_palette) == 64, 'Expected 16-color palettes')
    colors = [tuple(palette[i:i + 4]) for i in range(0, 64, 4)]
    remap = []
    for i in range(16):
        color = tuple(donor_palette[i * 4:i * 4 + 4])
        remap.append(min(range(16), key=lambda j: sum((a - b) ** 2 for a, b in zip(color, colors[j]))))
    additions = []
    for code in range(32, 127):
        if code in mapping:
            continue
        require(code in donor_map, 'Original complete font lacks ASCII glyph')
        glyph = struct.unpack_from('<4f4h', donor_font, donor_start + donor_map[code] * 24)
        left, top, right, bottom = glyph[:4]
        sx, sy = round(left * dw), round(top * dh)
        gw, gh = round(right * dw) - sx, round(bottom * dh) - sy
        require(gw > 0 and gh > 0, 'Empty donor rectangle')
        position = None
        for y in range(height - gh - 1, -1, -1):
            for x in range(1, width - gw):
                if all(not any(occupied[(y + dy) * width + x - 1:(y + dy) * width + x + gw + 1]) for dy in range(gh + 1)):
                    position = x, y
                    break
            if position:
                break
        require(position is not None, 'No unused atlas space; refusing to overwrite original glyphs')
        x, y = position
        for dy in range(gh):
            for dx in range(gw):
                pixels[(y + dy) * width + x + dx] = remap[donor_pixels[(sy + dy) * dw + sx + dx]]
        for dy in range(gh + 1):
            occupied[(y + dy) * width + x - 1:(y + dy) * width + x + gw + 1] = b'\1' * (gw + 2)
        scale = u32(font, 8) / u32(donor_font, 8)
        metrics = tuple(round(value * scale) for value in glyph[4:7]) + (glyph[7],)
        mapping[code] = count + len(additions)
        records.extend(struct.pack('<4f4h', x / width, y / height, (x + gw) / width, (y + gh) / height, *metrics))
        additions.append({'character': chr(code), 'source_glyph': donor_map[code], 'rectangle': [x, y, gw, gh], 'metrics': metrics})
    ranges = []
    for code, index in sorted(mapping.items()):
        if ranges and code == ranges[-1][1] + 1 and index == ranges[-1][2] + code - ranges[-1][0]:
            ranges[-1][1] = code
        else:
            ranges.append([code, code, index])
    output = bytearray(aliased[:32])
    for row in ranges:
        output.extend(struct.pack('<3I', *row))
    new_start = len(output)
    output.extend(records)
    struct.pack_into('<I', output, 4, len(output))
    struct.pack_into('<HH', output, 16, len(ranges), count + len(additions))
    struct.pack_into('<I', output, 24, new_start)
    require(all(not protected[i] or value == original_pixels[i] for i, value in enumerate(pixels)), 'Original glyph pixels changed')
    new_texture = encode_pixels(texture, pixels)
    require(texture_pixels(new_texture)[2] == pixels, 'Texture round-trip failed')
    require(font_map(output)[0] == mapping, 'Font round-trip failed')
    return bytes(output), bytes(new_texture), {'aliases': aliases, 'copied_glyphs': additions, 'source': 'Original DATA.BIN resources 35/36'}
