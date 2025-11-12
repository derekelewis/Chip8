import random


SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
START_ADDRESS = 0x200
FONTSET_START_ADDRESS = 0x50
FONTSET_CHAR_BYTES = 5
FONTSET: tuple[int, ...] = (
    0xF0,
    0x90,
    0x90,
    0x90,
    0xF0,  # 0
    0x20,
    0x60,
    0x20,
    0x20,
    0x70,  # 1
    0xF0,
    0x10,
    0xF0,
    0x80,
    0xF0,  # 2
    0xF0,
    0x10,
    0xF0,
    0x10,
    0xF0,  # 3
    0x90,
    0x90,
    0xF0,
    0x10,
    0x10,  # 4
    0xF0,
    0x80,
    0xF0,
    0x10,
    0xF0,  # 5
    0xF0,
    0x80,
    0xF0,
    0x90,
    0xF0,  # 6
    0xF0,
    0x10,
    0x20,
    0x40,
    0x40,  # 7
    0xF0,
    0x90,
    0xF0,
    0x90,
    0xF0,  # 8
    0xF0,
    0x90,
    0xF0,
    0x10,
    0xF0,  # 9
    0xF0,
    0x90,
    0xF0,
    0x90,
    0x90,  # A
    0xE0,
    0x90,
    0xE0,
    0x90,
    0xE0,  # B
    0xF0,
    0x80,
    0x80,
    0x80,
    0xF0,  # C
    0xE0,
    0x90,
    0x90,
    0x90,
    0xE0,  # D
    0xF0,
    0x80,
    0xF0,
    0x80,
    0xF0,  # E
    0xF0,
    0x80,
    0xF0,
    0x80,
    0x80,  # F
)


class Chip8:
    def __init__(self):
        self._memory: bytearray = bytearray(4096)
        self._registers: list[int] = [0] * 16
        self._stack: list[int] = []
        self._pc: int = START_ADDRESS
        self._index: int = 0
        self._sp: int = 0
        self._delay_timer: int = 0
        self._sound_timer: int = 0
        self._keypad: list[int] = [0] * 16
        self._video: bytearray = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)
        self._opcode: int = 0
        self._dispatch = [
            # (mask, value, fn)
            (0xFFFF, 0x00E0, self._op_00E0),  # CLS
            (0xFFFF, 0x00EE, self._op_00EE),  # RET
            (0xF000, 0x0000, self._op_0NNN),  # SYS addr (ignored)
            (0xF000, 0x1000, self._op_1NNN),  # JP addr
            (0xF000, 0x2000, self._op_2NNN),  # CALL addr
            (0xF000, 0x3000, self._op_3XKK),  # SE Vx, byte
            (0xF000, 0x4000, self._op_4XKK),  # SNE Vx, byte
            (0xF000, 0x5000, self._op_5XY0),  # SE Vx, Vy
            (0xF000, 0x6000, self._op_6XKK),  # LD Vx, byte
            (0xF000, 0x7000, self._op_7XKK),  # ADD Vx, byte
            (0xF00F, 0x8000, self._op_8XY0),  # LD Vx, Vy
            (0xF00F, 0x8001, self._op_8XY1),  # OR Vx, Vy
            (0xF00F, 0x8002, self._op_8XY2),  # AND Vx, Vy
            (0xF00F, 0x8003, self._op_8XY3),  # XOR Vx, Vy
            (0xF00F, 0x8004, self._op_8XY4),  # ADD Vx, Vy
            (0xF00F, 0x8005, self._op_8XY5),  # SUB Vx, Vy
            (0xF00F, 0x8006, self._op_8XY6),  # SHR Vx {, Vy}
            (0xF00F, 0x8007, self._op_8XY7),  # SUBN Vx, Vy
            (0xF00F, 0x800E, self._op_8XYE),  # SHL Vx {, Vy}
            (0xF00F, 0x9000, self._op_9XY0),  # SNE Vx, Vy
            (0xF000, 0xA000, self._op_ANNN),  # LD I, addr
            (0xF000, 0xB000, self._op_BNNN),  # JP V0, addr
            (0xF000, 0xC000, self._op_CXKK),  # RND Vx, byte
            (0xF000, 0xD000, self._op_DXYN),  # DRW Vx, Vy, nibble
            (0xF0FF, 0xE09E, self._op_EX9E),  # SKP Vx
            (0xF0FF, 0xE0A1, self._op_EXA1),  # SKNP Vx
            (0xF0FF, 0xF007, self._op_FX07),  # LD Vx, DT
            (0xF0FF, 0xF00A, self._op_FX0A),  # LD Vx, K
            (0xF0FF, 0xF015, self._op_FX15),  # LD DT, Vx
            (0xF0FF, 0xF018, self._op_FX18),  # LD ST, Vx
            (0xF0FF, 0xF01E, self._op_FX1E),  # ADD I, Vx
            (0xF0FF, 0xF029, self._op_FX29),  # LD F, Vx
            (0xF0FF, 0xF033, self._op_FX33),  # LD B, Vx
            (0xF0FF, 0xF055, self._op_FX55),  # LD [I], Vx
            (0xF0FF, 0xF065, self._op_FX65),  # LD Vx, [I]
        ]
        self._load_fontset()

    def _load_fontset(self) -> None:
        for offset, value in enumerate(FONTSET):
            self._memory[FONTSET_START_ADDRESS + offset] = value

    def _load_rom(self, path: str) -> None:
        with open(path, "rb") as f:
            n = f.readinto(memoryview(self._memory)[START_ADDRESS:])
        print(f"Read {n} bytes into memory starting from 0x{START_ADDRESS:03x}.")

    def _step(self) -> None:
        op = self._memory[self._pc] << 8 | self._memory[self._pc + 1]
        self._opcode = op
        self._pc = (self._pc + 2) & 0x0FFF
        for mask, value, fn in self._dispatch:
            if (op & mask) == value:
                print(f"Executing {fn.__name__} with op {op:x}")
                fn(op)
                if self._delay_timer > 0:
                    self._delay_timer -= 1
                if self._sound_timer > 0:
                    self._sound_timer -= 1
                return
        raise ValueError(f"Unknown opcode 0x{op:04X}")

    def _op_00E0(self, op: int) -> None:  # CLS
        self._video = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)

    def _op_00EE(self, op: int) -> None:  # RET
        if not self._stack:
            raise RuntimeError("Stack underflow on RET")
        self._sp = max(0, self._sp - 1)
        self._pc = self._stack.pop()

    def _op_0NNN(self, op: int) -> None:  # SYS addr (ignored)
        # Original CHIP-8 on the COSMAC VIP would jump into RCA 1802 code.
        # Modern interpreters treat this as a NOP, so we do nothing.
        return

    def _op_1NNN(self, op: int) -> None:  # JP addr
        self._pc = op & 0x0FFF

    def _op_2NNN(self, op: int) -> None:  # CALL addr
        self._sp += 1
        self._stack.append(self._pc)
        self._pc = op & 0x0FFF

    def _op_3XKK(self, op: int) -> None:  # SE Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        if self._registers[reg] == value:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_4XKK(self, op: int) -> None:  # SNE Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        if self._registers[reg] != value:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_5XY0(self, op: int) -> None:  # SE Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        if self._registers[reg_x] == self._registers[reg_y]:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_6XKK(self, op: int) -> None:  # LD Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        self._registers[reg] = value & 0xFF

    def _op_7XKK(self, op: int) -> None:  # ADD Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        self._registers[reg] = (self._registers[reg] + value) & 0xFF

    def _op_8XY0(self, op: int) -> None:  # LD Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        self._registers[reg_x] = self._registers[reg_y]

    def _op_8XY1(self, op: int) -> None:  # OR Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        self._registers[reg_x] |= self._registers[reg_y]

    def _op_8XY2(self, op: int) -> None:  # AND Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        self._registers[reg_x] &= self._registers[reg_y]

    def _op_8XY3(self, op: int) -> None:  # XOR Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        self._registers[reg_x] ^= self._registers[reg_y]

    def _op_8XY4(self, op: int) -> None:  # ADD Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        total = self._registers[reg_x] + self._registers[reg_y]
        self._registers[0xF] = 1 if total > 0xFF else 0
        self._registers[reg_x] = total & 0xFF

    def _op_8XY5(self, op: int) -> None:  # SUB Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        vx = self._registers[reg_x]
        vy = self._registers[reg_y]
        self._registers[0xF] = 1 if vx >= vy else 0
        self._registers[reg_x] = (vx - vy) & 0xFF

    def _op_8XY6(self, op: int) -> None:  # SHR Vx {, Vy}
        reg_x = (op & 0x0F00) >> 8
        value = self._registers[reg_x]
        self._registers[0xF] = value & 0x01
        self._registers[reg_x] = (value >> 1) & 0xFF

    def _op_8XY7(self, op: int) -> None:  # SUBN Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        vx = self._registers[reg_x]
        vy = self._registers[reg_y]
        self._registers[0xF] = 1 if vy >= vx else 0
        self._registers[reg_x] = (vy - vx) & 0xFF

    def _op_8XYE(self, op: int) -> None:  # SHL Vx {, Vy}
        reg_x = (op & 0x0F00) >> 8
        value = self._registers[reg_x]
        self._registers[0xF] = (value >> 7) & 0x01
        self._registers[reg_x] = (value << 1) & 0xFF

    def _op_9XY0(self, op: int) -> None:  # SNE Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        if self._registers[reg_x] != self._registers[reg_y]:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_ANNN(self, op: int) -> None:  # LD I, addr
        self._index = op & 0x0FFF

    def _op_BNNN(self, op: int) -> None:  # JP V0, addr
        addr = op & 0x0FFF
        self._pc = (addr + self._registers[0]) & 0x0FFF

    def _op_CXKK(self, op: int) -> None:  # RND Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        self._registers[reg] = random.getrandbits(8) & value

    def _op_DXYN(self, op: int) -> None:  # DRW Vx, Vy, nibble
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        height = op & 0x000F
        x_pos = self._registers[reg_x] % SCREEN_WIDTH
        y_pos = self._registers[reg_y] % SCREEN_HEIGHT
        self._registers[0xF] = 0

        for row in range(height):
            sprite = self._memory[self._index + row]
            for col in range(8):
                if sprite & (0x80 >> col):
                    x = (x_pos + col) % SCREEN_WIDTH
                    y = (y_pos + row) % SCREEN_HEIGHT
                    idx = x + y * SCREEN_WIDTH
                    if self._video[idx]:
                        self._registers[0xF] = 1
                    self._video[idx] ^= 1

    def _op_EX9E(self, op: int) -> None:  # SKP Vx
        reg = (op & 0x0F00) >> 8
        key = self._registers[reg] & 0x0F
        if self._keypad[key]:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_EXA1(self, op: int) -> None:  # SKNP Vx
        reg = (op & 0x0F00) >> 8
        key = self._registers[reg] & 0x0F
        if not self._keypad[key]:
            self._pc = (self._pc + 2) & 0x0FFF

    def _op_FX07(self, op: int) -> None:  # LD Vx, DT
        reg = (op & 0x0F00) >> 8
        self._registers[reg] = self._delay_timer

    def _op_FX0A(self, op: int) -> None:  # LD Vx, K
        reg = (op & 0x0F00) >> 8
        pressed = next((idx for idx, state in enumerate(self._keypad) if state), None)
        if pressed is None:
            self._pc = (self._pc - 2) & 0x0FFF
            return
        self._registers[reg] = pressed

    def _op_FX15(self, op: int) -> None:  # LD DT, Vx
        reg = (op & 0x0F00) >> 8
        self._delay_timer = self._registers[reg] & 0xFF

    def _op_FX18(self, op: int) -> None:  # LD ST, Vx
        reg = (op & 0x0F00) >> 8
        self._sound_timer = self._registers[reg] & 0xFF

    def _op_FX1E(self, op: int) -> None:  # ADD I, Vx
        reg = (op & 0x0F00) >> 8
        result = self._index + self._registers[reg]
        self._registers[0xF] = 1 if result > 0x0FFF else 0
        self._index = result & 0x0FFF

    def _op_FX29(self, op: int) -> None:  # LD F, Vx
        reg = (op & 0x0F00) >> 8
        digit = self._registers[reg] & 0x0F
        self._index = FONTSET_START_ADDRESS + digit * FONTSET_CHAR_BYTES

    def _op_FX33(self, op: int) -> None:  # LD B, Vx
        reg = (op & 0x0F00) >> 8
        value = self._registers[reg]
        self._memory[self._index] = value // 100
        self._memory[self._index + 1] = (value // 10) % 10
        self._memory[self._index + 2] = value % 10

    def _op_FX55(self, op: int) -> None:  # LD [I], Vx
        reg = (op & 0x0F00) >> 8
        for offset in range(reg + 1):
            self._memory[self._index + offset] = self._registers[offset]
        self._index = (self._index + reg + 1) & 0x0FFF

    def _op_FX65(self, op: int) -> None:  # LD Vx, [I]
        reg = (op & 0x0F00) >> 8
        for offset in range(reg + 1):
            self._registers[offset] = self._memory[self._index + offset]
        self._index = (self._index + reg + 1) & 0x0FFF
