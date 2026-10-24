#!/usr/bin/env python3
"""Talk to a running famicart over USB-CDC: upload a ROM in place, reset, or jump to BOOTSEL.

  fcload.py /dev/ttyACM0 info
  fcload.py /dev/ttyACM0 load game.nes        # upload .nes into the flash slot and reboot the cartridge
  fcload.py /dev/ttyACM0 profile game.uf2     # (re)write only the 48-byte profile taken from a rom2uf2 output
  fcload.py /dev/ttyACM0 reset | bootsel

rev D (U1 "PRG mapper" port; do these with the cartridge OUT of the console, USB powered):
  fcload.py /dev/ttyACM0 lib                   # list the ROM library in the external flashes
  fcload.py /dev/ttyACM0 libadd game.nes [name]# program PRG/CHR into the external flashes, add a library entry, boot it
  fcload.py /dev/ttyACM0 libsel 3              # boot library slot 3 from now on
  fcload.py /dev/ttyACM0 libdel 3
  fcload.py /dev/ttyACM0 bootbank              # (once per board) program the boot stub into the top PRG bank
  fcload.py /dev/ttyACM0 flashid | wramdump

Requires pyserial (pip install pyserial). After `load`, press RESET on the Famicom: the cartridge
bus is released during the flash write, so the running game is interrupted.
"""
import sys, zlib, time
try:
    import serial
except ImportError:
    sys.exit('pip install pyserial')

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    port, cmd = sys.argv[1], sys.argv[2]
    s = serial.Serial(port, 115200, timeout=3)
    time.sleep(0.2); s.reset_input_buffer()
    def say(line): s.write((line + '\n').encode()); s.flush()
    def expect(prefix, timeout=5):
        t0 = time.time()
        while time.time() - t0 < timeout:
            l = s.readline().decode(errors='replace').strip()
            if l: print('<', l)
            if l.startswith(prefix) or l.startswith('ERR'): return l
        return ''
    if cmd in ('lib', 'bootbank', 'flashid', 'wramdump'):
        say(cmd.upper()); t0 = time.time()
        while time.time() - t0 < (120 if cmd == 'bootbank' else 10):
            l = s.readline().decode(errors='replace').rstrip()
            if l: print('<', l)
            if l.startswith('OK') or l.startswith('ERR'): break
    elif cmd in ('libsel', 'libdel'):
        say(f'{cmd.upper()} {int(sys.argv[3])}'); print(expect('OK'))
    elif cmd == 'libadd':
        data = open(sys.argv[3], 'rb').read()
        name = sys.argv[4] if len(sys.argv) > 4 else sys.argv[3].rsplit('/', 1)[-1][:40]
        if data[:4] != b'NES\x1a': sys.exit('rev D needs an iNES / NES 2.0 header (add one with rom2uf2.py --header)')
        hdr = data[:16]; off = 16 + (512 if hdr[6] & 4 else 0)
        nes2 = (hdr[7] & 0x0C) == 0x08
        prg = (((hdr[9] & 0x0F) << 8 | hdr[4]) if nes2 else hdr[4]) * 16384
        chr_ = (((hdr[9] >> 4) << 8 | hdr[5]) if nes2 else hdr[5]) * 8192
        body = data[off:off + prg + chr_]
        if len(body) != prg + chr_: sys.exit('truncated image')
        say(f'LIBADD {prg} {chr_} {name}')
        if not expect('READY').startswith('READY'): sys.exit('device not ready')
        s.write(hdr); s.flush()
        t0 = time.time()
        for i in range(0, len(body), 4096):
            s.write(body[i:i + 4096]); s.flush()
            while s.in_waiting: sys.stdout.write(s.read(s.in_waiting).decode(errors='replace')); sys.stdout.flush()
        print(f'\nsent {len(body)} bytes in {time.time() - t0:.1f}s; programming/verifying...')
        s.timeout = 600; print(expect('OK', 600))
    elif cmd == 'info':
        say('INFO'); time.sleep(0.5); print(s.read(s.in_waiting or 1).decode(errors='replace'))
    elif cmd in ('reset', 'bootsel'):
        say(cmd.upper()); print(expect('OK'))
    elif cmd == 'load':
        data = open(sys.argv[3], 'rb').read()
        crc = zlib.crc32(data) & 0xFFFFFFFF
        say(f'LOAD {len(data)} {crc:08X}')
        if not expect('READY').startswith('READY'): sys.exit('device not ready')
        for i in range(0, len(data), 4096):
            s.write(data[i:i + 4096]); s.flush()
            sys.stdout.write(f'\r{i + 4096 if i + 4096 < len(data) else len(data)}/{len(data)}'); sys.stdout.flush()
        print(); print(expect('OK', timeout=30))
    elif cmd == 'profile':
        uf2 = open(sys.argv[3], 'rb').read()
        hdr = uf2[32:32 + 48]           # first UF2 block payload starts with the profile
        say('PROFILE ' + hdr.hex()); print(expect('OK'))
    else:
        sys.exit(__doc__)

if __name__ == '__main__':
    main()
