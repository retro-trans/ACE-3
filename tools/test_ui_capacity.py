"""Execute the original and patched callback tails in a bounded MIPS interpreter.

This tests the actual instruction bytes (including call/branch delay slots),
saved return address, resource pointer store, and drawing capacity field.
It is not an emulator boot or a test of the complete UI renderer.
"""
import struct
import unittest
from ui_capacity import SITES, replacement, CAPACITY


class TinyMips:
    def __init__(self, code, memory, registers):
        self.code = code
        self.memory = bytearray(memory)
        self.registers = list(registers)

    def step(self, pc, delay=False):
        w = self.code[pc]
        op, rs, rt, rd, fn = w >> 26, (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, w & 63
        imm = (w & 65535) - (65536 if w & 32768 else 0)
        r = self.registers
        address = r[rs] + imm
        target = None
        if w == 0:
            pass
        elif op == 0 and fn == 0x2d:  # daddu / move
            r[rd] = (r[rs] + r[rt]) & ((1 << 64) - 1)
        elif op == 0 and fn == 8:  # jr
            target = r[rs]
        elif op == 3:  # jal
            r[31] = pc + 8
            target = ((pc + 4) & 0xf0000000) | ((w & 0x3ffffff) << 2)
        elif op in (4, 5):
            taken = (r[rs] == r[rt]) if op == 4 else (r[rs] != r[rt])
            target = pc + 4 + imm * 4 if taken else pc + 8
        elif op == 9:
            r[rt] = (r[rs] + imm) & 0xffffffff
        elif op in (0x23, 0x37):
            r[rt] = struct.unpack_from('<I' if op == 0x23 else '<Q', self.memory, address)[0]
        elif op == 0x2b:
            struct.pack_into('<I', self.memory, address, r[rt] & 0xffffffff)
        elif op == 0x28:
            self.memory[address] = r[rt] & 255
        else:
            raise AssertionError('Unexpected instruction ' + hex(w))
        r[0] = 0
        if target is not None:
            assert not delay, 'Branch in a delay slot'
            self.step(pc + 4, delay=True)
            return target
        return pc + 4

    def run(self, start, stop):
        pc = start
        for _ in range(40):
            if pc == stop:
                return
            pc = self.step(pc)
        raise AssertionError('Callback tail did not reach its original epilogue')


class CapacityTests(unittest.TestCase):
    def test_original_and_replacement_preserve_callback_state(self):
        helper = (0x8c840098, 0x8c830020, 0x10650002, 0, 0xac850020, 0x03e00008, 0, 0)
        for site in SITES:
            for old_limit in (2, 3, 4, 6, 17, 32, 64, 94, 128):
                for old_pointer in (0, 0xabc):
                    with self.subTest(menu=site['id'], old_limit=old_limit, old_pointer=old_pointer):
                        memory = bytearray(4096)
                        regs = [0] * 32
                        regs[16], regs[18], regs[29], regs[31] = 0x100, 0xabc, 0x800, 0x123456
                        struct.pack_into('<I', memory, 0x198, 0x400)
                        struct.pack_into('<I', memory, 0x420, old_pointer)
                        struct.pack_into('<Q', memory, 0x840, 0x765432)
                        memory[0x41b] = old_limit
                        code = {site['va'] + i * 4: w for i, w in enumerate(site['words'])}
                        code.update({0x2b6f10 + i * 4: w for i, w in enumerate(helper)})
                        # The original jump goes to a branch whose delay slot restores ra.
                        target = site['va'] + 16 - 37 * 4
                        branch = 0x10000000 | (((site['epilogue'] - target - 4) // 4) & 65535)
                        code.update({target: branch, target + 4: 0xdfbf0040})
                        original = TinyMips(code, memory, regs)
                        original.run(site['va'], site['epilogue'])
                        changed_code = {site['va'] + i * 4: w for i, w in enumerate(struct.unpack('<5I', replacement()))}
                        changed = TinyMips(changed_code, memory, regs)
                        changed.run(site['va'], site['epilogue'])
                        expected = bytearray(original.memory)
                        expected[0x41b] = CAPACITY
                        self.assertEqual(changed.memory, expected)
                        self.assertEqual(changed.registers[31], 0x765432)
                        for reg in list(range(16, 24)) + [28, 29, 30, 31]:
                            self.assertEqual(changed.registers[reg], original.registers[reg])

    def test_character_budget_includes_whole_setup_descriptions(self):
        self.assertGreaterEqual(CAPACITY, len('This control scheme lets you select weapons instantly.\nRecommended for first-time players.'))
        self.assertLessEqual(CAPACITY, 255)  # Capacity is read with lbu before allocation.
        self.assertEqual((7 * CAPACITY + 11) * 16, 14512)


if __name__ == '__main__':
    unittest.main()
