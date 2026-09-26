"""Read the game's sparse CP932 font map and reuse existing Latin glyphs."""
import struct


def font_map(data):
    size = struct.unpack_from('<I', data, 4)[0]
    count, glyph_count, ranges, glyphs = struct.unpack_from('<HHII', data, 16)
    if not (data[:4] == b'\0\0\1\0' and ranges == 32 and
            ranges + count * 12 <= glyphs and glyphs + glyph_count * 24 <= size <= len(data)):
        raise ValueError('Invalid font resource')
    mapping = {}
    for i in range(count):
        first, last, index = struct.unpack_from('<III', data, ranges + i * 12)
        if first > last or index + last - first >= glyph_count:
            raise ValueError('Invalid font range')
        for code in range(first, last + 1):
            if code in mapping:
                raise ValueError('Overlapping font ranges')
            mapping[code] = index + code - first
    return mapping, glyphs, glyph_count


def codepoint(char):
    return int.from_bytes(char.encode('cp932'), 'big')


def patch_font(data):
    mapping, glyphs, glyph_count = font_map(data)
    original = dict(mapping)
    aliases = []
    for value in range(33, 127):
        if value in mapping:
            continue
        char = chr(value)
        candidate = '\u2019' if char == "'" else chr(value + 0xfee0)
        try:
            glyph = mapping.get(codepoint(candidate))
        except UnicodeEncodeError:
            continue
        if glyph is not None:
            mapping[value] = glyph
            aliases.append({'character': char, 'existing_character': candidate, 'glyph': glyph})
    ranges = []
    for code, index in sorted(mapping.items()):
        if ranges and code == ranges[-1][1] + 1 and index == ranges[-1][2] + code - ranges[-1][0]:
            ranges[-1][1] = code
        else:
            ranges.append([code, code, index])
    result = bytearray(data[:32])
    for row in ranges:
        result.extend(struct.pack('<III', *row))
    new_glyphs = len(result)
    result.extend(data[glyphs:struct.unpack_from('<I', data, 4)[0]])
    struct.pack_into('<I', result, 4, len(result))
    struct.pack_into('<H', result, 16, len(ranges))
    struct.pack_into('<I', result, 24, new_glyphs)
    rebuilt, start, count = font_map(result)
    assert all(rebuilt[key] == value for key, value in original.items())
    assert result[start:start + count * 24] == data[glyphs:glyphs + glyph_count * 24]
    return bytes(result), aliases


def measure_text(font, text):
    mapping, glyphs, _ = font_map(font)
    widths = []
    for line in text.split('\n'):
        width = 0
        for char in line:
            code = codepoint(char)
            if code not in mapping:
                raise ValueError('Font has no glyph for ' + repr(char) + ' in ' + repr(text))
            width += struct.unpack_from('<h', font, glyphs + mapping[code] * 24 + 20)[0]
        widths.append(width)
    return widths
