from lib.Chip8 import Chip8

chip8 = Chip8()

quit: bool = False

chip8._load_rom("./roms/a.ch8")

while not quit:
    chip8._step()
