import sdl3
import ctypes
from typing import cast

from lib.Chip8 import Chip8

chip8: Chip8 = Chip8()

chip8._load_rom("./roms/a.ch8")

sdl3.SDL_Init(cast(sdl3.SDL_InitFlags, sdl3.SDL_INIT_VIDEO))
window = sdl3.SDL_CreateWindow(
    ctypes.c_char_p(b"Chip8 Emulator"),
    ctypes.c_int(512),
    ctypes.c_int(256),
    cast(sdl3.SDL_WindowFlags, sdl3.SDL_WINDOW_RESIZABLE),
)
renderer = sdl3.SDL_CreateRenderer(window, ctypes.c_char_p(None))

texture = sdl3.SDL_CreateTexture(
    renderer,
    cast(sdl3.SDL_PixelFormat, sdl3.SDL_PIXELFORMAT_RGBA8888),
    cast(sdl3.SDL_TextureAccess, sdl3.SDL_TEXTUREACCESS_STREAMING),
    ctypes.c_int(64),
    ctypes.c_int(32),
)

pixel_buffer: bytearray = bytearray(64 * 32 * 4)
pixel_array = (ctypes.c_uint8 * len(pixel_buffer)).from_buffer(pixel_buffer)
pixel_ptr = ctypes.cast(pixel_array, ctypes.c_void_p)
event = sdl3.SDL_Event()
cycles_per_frame: int = 12
running: bool = True

halt_pc: int = 0x276

while running:
    while sdl3.SDL_PollEvent(cast(sdl3.LP_SDL_Event, event)):
        if event.type == sdl3.SDL_EVENT_QUIT:
            running = False

    for _ in range(cycles_per_frame):
        chip8._step()
        if chip8._pc == halt_pc:
            running = False
            break

    if not running:
        break

    for idx, value in enumerate(chip8._video):
        shade: int = 0xFF if value else 0x00
        o = idx * 4
        pixel_buffer[o] = shade
        pixel_buffer[o + 1] = shade
        pixel_buffer[o + 2] = shade
        pixel_buffer[o + 3] = 0xFF

    sdl3.SDL_UpdateTexture(
        texture, cast(sdl3.LP_SDL_Rect, None), pixel_ptr, ctypes.c_int(64 * 4)
    )
    sdl3.SDL_RenderClear(renderer)
    sdl3.SDL_RenderTexture(
        renderer, texture, cast(sdl3.LP_SDL_FRect, None), cast(sdl3.LP_SDL_FRect, None)
    )
    sdl3.SDL_RenderPresent(renderer)

sdl3.SDL_DestroyTexture(texture)
sdl3.SDL_DestroyRenderer(renderer)
sdl3.SDL_DestroyWindow(window)
sdl3.SDL_Quit()
