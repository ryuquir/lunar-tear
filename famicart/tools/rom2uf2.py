#!/usr/bin/env python3
"""Convert a .nes (or headerless) ROM image into a UF2 file that drops onto the RP2040's
USB mass-storage bootloader and lands in the firmware's ROM slot.

  rom2uf2.py game.nes -o game.uf2
  rom2uf2.py game.nes -o game.uf2 --mapper 5 --audio vrc7:exclusive --audio mmc5
  rom2uf2.py game.nes -o game.uf2 --audio vrc6@0xC000       # relocate VRC6 registers to $C000-$F003

The output contains a 256-byte cartridge profile followed by the image (see src/core/profile.h).
Without any override the profile still records "auto" for every field, so the firmware's own
detection (DB -> NES 2.0 -> iNES -> heuristic) decides. Use --raw to omit the profile entirely.
"""
import argparse, struct, sys, zlib

UF2_MAGIC0, UF2_MAGIC1, UF2_MAGIC_END = 0x0A324655, 0x9E5D5157, 0x0AB16F30
FAMILY = {'rp2040': 0xE48BFF56, 'rp2350': 0xE48BFF59}   # rp2350 arm-s
XIP_BASE = 0x10000000
ROM_SLOT = 0x00040000
PROFILE_MAGIC, PROFILE_VERSION = 0x50434346, 1
AUDIO = {'none': 0, 'vrc6': 1, 'vrc7': 2, 'mmc5': 3, 'n163': 4, 's5b': 5, 'fds': 6}

def crc32(b): return zlib.crc32(b) & 0xFFFFFFFF

def build_profile(args):
    # struct cart_profile_t (little endian):
    # u32 magic; u8 version; u8 flags; u16 mapper; u8 submapper; u8 mirroring; u8 wram_kb; u8 chr_ram_kb;
    # profile_audio_t audio[4] {u8 chip; u8 exclusive; u16 base}; u8 audio_volume[4]; u8 reserved[12]; u32 crc
    flags = 0
    if args.mapper is not None: flags |= 0x01
    if args.no_audio: flags |= 0x02
    if args.pal: flags |= 0x04
    mapper = args.mapper if args.mapper is not None else 0xFFFF
    sub = args.submapper if args.submapper is not None else 0xFF
    mirror = {'h': 0, 'v': 1, '4': 2, '1': 3}[args.mirroring] if args.mirroring else 0xFF
    wram = args.wram_kb if args.wram_kb is not None else 0xFF
    chrram = args.chr_ram_kb if args.chr_ram_kb is not None else 0xFF
    body = struct.pack('<IBBHBBBB', PROFILE_MAGIC, PROFILE_VERSION, flags, mapper, sub, mirror, wram, chrram)
    slots = []
    for spec in (args.audio or [])[:4]:
        name, _, rest = spec.partition(':')
        base = 0
        if '@' in name: name, b = name.split('@', 1); base = int(b, 0)
        exclusive = 1 if 'exclusive' in rest else 0
        if name not in AUDIO: sys.exit(f'unknown audio chip {name!r}; choose from {", ".join(AUDIO)}')
        slots.append((AUDIO[name], exclusive, base))
    while len(slots) < 4: slots.append((0, 0, 0))
    for chip, ex, base in slots: body += struct.pack('<BBH', chip, ex, base)
    vols = (args.volume or [128] * 4) + [128] * 4
    body += bytes(min(255, max(0, v)) for v in vols[:4])
    body += bytes(12)
    body += struct.pack('<I', crc32(body))
    assert len(body) == 48, len(body)
    return body + bytes(256 - len(body))

def to_uf2(data, base_addr, family):
    blocks = (len(data) + 255) // 256
    out = bytearray()
    for i in range(blocks):
        chunk = data[i * 256:(i + 1) * 256].ljust(256, b'\x00')
        hdr = struct.pack('<IIIIIIII', UF2_MAGIC0, UF2_MAGIC1, 0x00002000, base_addr + i * 256, 256, i, blocks, family)
        out += hdr + chunk + bytes(476 - 256) + struct.pack('<I', UF2_MAGIC_END)
    return bytes(out)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rom'); ap.add_argument('-o', '--out', required=True)
    ap.add_argument('--family', choices=FAMILY, default='rp2040')
    ap.add_argument('--slot', type=lambda x: int(x, 0), default=ROM_SLOT, help='flash offset of the ROM slot (default 0x40000)')
    ap.add_argument('--raw', action='store_true', help='no profile header; burn the image as-is')
    ap.add_argument('--mapper', type=int); ap.add_argument('--submapper', type=int)
    ap.add_argument('--mirroring', choices=['h', 'v', '4', '1'])
    ap.add_argument('--wram-kb', type=int); ap.add_argument('--chr-ram-kb', type=int)
    ap.add_argument('--audio', action='append', help='chip[@base][:exclusive], e.g. vrc7:exclusive, vrc6@0xC000, mmc5')
    ap.add_argument('--volume', type=int, action='append', help='per-audio-slot volume 0..255 (128 nominal)')
    ap.add_argument('--no-audio', action='store_true'); ap.add_argument('--pal', action='store_true')
    a = ap.parse_args()
    img = open(a.rom, 'rb').read()
    if img[:4] == b'NES\x1a':
        prg, chr_ = img[4] * 16384, img[5] * 8192
        if (img[7] & 0x0C) == 0x08: prg = (((img[9] & 0x0F) << 8) | img[4]) * 16384; chr_ = (((img[9] >> 4) << 8) | img[5]) * 8192
        off = 16 + (512 if img[6] & 4 else 0)
        print(f'iNES/NES2.0: mapper {((img[6] >> 4) | (img[7] & 0xF0)) + (((img[8] & 0x0F) << 8) if (img[7] & 0x0C) == 0x08 else 0)}, PRG {prg // 1024}K, CHR {chr_ // 1024}K, PRG+CHR CRC32 {crc32(img[off:off + prg + chr_]):08X}')
    else:
        print(f'headerless image, {len(img)} bytes, CRC32 {crc32(img):08X} (firmware will try the database, then size heuristics)')
    payload = (b'' if a.raw else build_profile(a)) + img
    open(a.out, 'wb').write(to_uf2(payload, XIP_BASE + a.slot, FAMILY[a.family]))
    print(f'wrote {a.out}: {len(payload)} bytes -> flash 0x{XIP_BASE + a.slot:08X} ({"raw" if a.raw else "profile+image"})')

if __name__ == '__main__':
    main()
