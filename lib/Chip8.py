class Chip8:
    def __init__(self):
        self._memory: bytearray = bytearray(4096)
        self._registers: list[int] = [0] * 16
        self._stack: list[int] = []
        self._pc: int = 0x200
        self._index: int = 0
        self._sp: int = 0
        self._delay_timer: int = 0
        self._sound_timer: int = 0
        self._keypad: list[int] = [0] * 16
        self._video: bytearray = bytearray(64 * 32)
        self._opcode: int = 0
        self._dispatch = [
            (0x00FF, 0x00E0, self._op_00E0),  # CLS
            (0x00FF, 0x00EE, self._op_00EE),  # RET
            (0xF000, 0x1000, self._op_1NNN),  # JP addr
            (0xF000, 0x2000, self._op_2NNN),  # CALL addr
            (0xF000, 0x3000, self._op_3XKK),  # SE Vx, byte
            (0xF000, 0x4000, self._op_4XKK),  # SNE Vx, byte
            (0xF000, 0x5000, self._op_5XY0),  # SE Vx, Vy
        ]

    def _load_rom(self, path: str) -> None:
        START_ADDRESS: int = 0x200
        with open(path, "rb") as f:
            n = f.readinto(memoryview(self._memory)[START_ADDRESS:])
        print(f"Read {n} bytes into memory starting from 0x{START_ADDRESS:x}.")

    def _step(self) -> None:
        op = self._memory[self._pc] << 8 | self._memory[self._pc + 1]
        for mask, value, fn in self._dispatch:
            if (op & mask) == value:
                print(f"Executing {fn.__name__} with op {op:x}")
                fn(op)
                # TODO: add return here to not traverse entire dispatch table

    def _op_00E0(self, op: int) -> None:  # CLS
        self._video = bytearray(64 * 32)

    def _op_00EE(self, op: int) -> None:  # RET
        self._sp -= 1
        self._pc = self._stack[self._sp]

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
            self._pc += 2

    def _op_4XKK(self, op: int) -> None:  # SNE Vx, byte
        reg = (op & 0x0F00) >> 8
        value = op & 0x00FF
        if self._registers[reg] != value:
            self._pc += 2

    def _op_5XY0(self, op: int) -> None:  # SE Vx, Vy
        reg_x = (op & 0x0F00) >> 8
        reg_y = (op & 0x00F0) >> 4
        if self._registers[reg_x] == self._registers[reg_y]:
            self._pc += 2
