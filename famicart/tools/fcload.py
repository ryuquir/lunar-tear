#!/usr/bin/env python3
"""Talk to a running famicart over USB-CDC: upload a ROM in place, reset, or jump to BOOTSEL.

  fcload.py /dev/ttyACM0 info
  fcload.py /dev/ttyACM0 load game.nes        # upload .nes into the flash slot and reboot the cartridge
  fcload.py /dev/ttyACM0 profile game.uf2     # (re)write only the 48-byte profile taken from a rom2uf2 output
  fcload.py /dev/ttyACM0 reset | bootsel

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
    if cmd == 'info':
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
