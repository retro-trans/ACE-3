import io
import struct
import unittest

from repair_disc_boot import dvd_root_plan, apply_changes, verify_exact_delta
from build_ui_patch import iso_files
from repair_disc_layout import fix_udf_checksum


def directory_record(name, lba, size, directory=True):
    length = 33 + len(name) + (len(name) % 2 == 0)
    result = bytearray(length)
    result[0] = length
    struct.pack_into('<I', result, 2, lba)
    struct.pack_into('>I', result, 6, lba)
    struct.pack_into('<I', result, 10, size)
    struct.pack_into('>I', result, 14, size)
    result[25] = 2 if directory else 0
    result[28:32] = b'\x01\0\0\x01'
    result[32] = len(name)
    result[33:33 + len(name)] = name
    return result


def sample_disc():
    disc = bytearray(23 * 2048)
    disc[16 * 2048:16 * 2048 + 7] = b'\x01CD001\x01'
    disc[16 * 2048 + 156:16 * 2048 + 190] = directory_record(b'\0', 20, 2048)
    root = (directory_record(b'\0', 20, 2048) + directory_record(b'\1', 20, 2048) +
            directory_record(b'IOP', 21, 2048) + directory_record(b'GAME.ELF;1', 22, 4, False))
    child = directory_record(b'\0', 21, 2048) + directory_record(b'\1', 20, 2048)
    disc[20 * 2048:20 * 2048 + len(root)] = root
    disc[21 * 2048:21 * 2048 + len(child)] = child
    disc[22 * 2048:22 * 2048 + 4] = b'ELF!'
    return bytes(disc), len(root)


class DiscBootTests(unittest.TestCase):
    def test_udf_crc_uses_only_declared_body_and_refreshes_tag_checksum(self):
        # CRC-16/XMODEM's public check vector; trailing sector padding excluded.
        data = bytearray(2048)
        struct.pack_into('<HH', data, 0, 261, 2)
        struct.pack_into('<H', data, 10, 9)
        data[16:25] = b'123456789'
        data[25:] = b'X' * (len(data) - 25)
        fix_udf_checksum(data)
        self.assertEqual(struct.unpack_from('<H', data, 8)[0], 0x31c3)
        self.assertEqual(data[4], (sum(data[:4]) + sum(data[5:16])) & 255)

    def test_root_all_references_and_payload_preserved(self):
        original, length = sample_disc()
        target = io.BytesIO(original)
        changes, info = dvd_root_plan(target)
        self.assertEqual(info['pcsx2_image_type_before'], 'CD')
        self.assertEqual(info['new_root_length'], length)
        self.assertEqual(len(changes), 4)
        apply_changes(target, changes)
        self.assertEqual(iso_files(io.BytesIO(original)), iso_files(target))
        self.assertEqual(target.getvalue()[22 * 2048:], original[22 * 2048:])
        remaining, info = dvd_root_plan(target)
        self.assertEqual(remaining, [])
        self.assertEqual(info['pcsx2_image_type_before'], 'DVD')
        verify_exact_delta(io.BytesIO(original), target, changes)
        target.seek(22 * 2048)
        target.write(b'BAD!')
        with self.assertRaisesRegex(ValueError, 'Unexpected disc change'):
            verify_exact_delta(io.BytesIO(original), target, changes)

    def test_nonzero_padding_is_not_discarded(self):
        original, length = sample_disc()
        bad = bytearray(original)
        bad[20 * 2048 + length + 16] = 1
        with self.assertRaisesRegex(ValueError, 'Nonzero directory sector padding'):
            dvd_root_plan(io.BytesIO(bad))

    def test_inconsistent_parent_reference_rejected(self):
        original, _ = sample_disc()
        bad = bytearray(original)
        bad[21 * 2048 + 34:21 * 2048 + 68] = directory_record(b'\1', 20, 100)
        with self.assertRaisesRegex(ValueError, 'Inconsistent root directory size'):
            dvd_root_plan(io.BytesIO(bad))


if __name__ == '__main__':
    unittest.main()
