/* Bandai FCG-1/2 (16 sub4), LZ93D50 (16 sub5), LZ93D50+24C01 (159), LZ93D50+SRAM (153, Famicom Jump II), Datach (157).
 * Includes a small 24C01/24C02 I2C EEPROM model so saves work. */
#include "../mapper.h"
#include <string.h>

/* ---- minimal I2C EEPROM (24C01: 128B/7-bit addr ; 24C02: 256B/8-bit addr) ---- */
enum { EE_IDLE, EE_ADDR, EE_WADDR, EE_READ, EE_WRITE, EE_ACK, EE_ACK_R, EE_NACK };
typedef struct { uint8_t sda, scl, out, mode, bits, addr, data; } ee_t;
/* ack9: also clock the 9th (ACK) bit of every byte (0x40 = inside the ACK slot). Without it the ACK clock of a
 * byte written to the EEPROM is sampled as the first data bit of the next one (the old behaviour, which broke
 * saves -- see test/tm_bandai_ee.c). All boards now use ack9 = true. */
static void ee_bit(ee_t *s, uint8_t *mem, bool is24c01, bool ack9, uint8_t scl, uint8_t sda) {
    uint8_t pscl = s->scl, psda = s->sda;
    s->scl = scl; s->sda = sda;
    if (pscl && scl) {              /* SDA edge while SCL high: start / stop */
        if (psda && !sda) { s->mode = EE_ADDR; s->bits = 0; s->data = 0; s->out = 1; return; }
        if (!psda && sda) { s->mode = EE_IDLE; s->out = 1; return; }
        return;
    }
    if (!pscl && scl) {             /* rising SCL: sample SDA */
        if (ack9 && (s->mode & 0x40)) return;   /* ACK clock: the master samples our ACK */
        switch (s->mode) {
        case EE_ADDR: case EE_WADDR: case EE_WRITE:
            s->data = (uint8_t)((s->data << 1) | sda);
            if (++s->bits == 8) {
                if (s->mode == EE_ADDR) {
                    if (is24c01) { s->addr = (uint8_t)(s->data >> 1); s->mode = (s->data & 1) ? EE_READ : EE_WRITE; s->bits = 0; s->data = 0; s->out = 0; s->mode |= 0x80; }
                    else if ((s->data & 0xF0) == 0xA0) { s->mode = ((s->data & 1) ? EE_READ : EE_WADDR) | 0x80; s->bits = 0; s->data = 0; s->out = 0; }
                    else { s->mode = EE_IDLE; s->out = 1; }
                } else if (s->mode == EE_WADDR) { s->addr = s->data; s->mode = EE_WRITE | 0x80; s->bits = 0; s->data = 0; s->out = 0; }
                else { mem[s->addr & (is24c01 ? 0x7F : 0xFF)] = s->data; s->addr++; s->mode = EE_WRITE | 0x80; s->bits = 0; s->data = 0; s->out = 0; }
            }
            break;
        case EE_READ:
            if (s->bits == 9) { /* 9th clock: master ACK (next byte) or NACK (done) */
                if (sda) s->mode = EE_IDLE; else { s->addr++; s->bits = 0; }
            }
            break;
        default: break;
        }
    } else if (pscl && !scl) {      /* falling SCL: drive SDA */
        if (s->mode & 0x80) { s->mode &= 0x7F; s->out = 0; /* ACK bit */ if (s->mode == EE_READ) s->bits = 0; if (ack9) s->mode |= 0x40; return; }
        s->mode &= (uint8_t)~0x40;   /* end of the ACK slot: release SDA or drive the first data bit */
        if (s->mode == EE_READ) {
            if (s->bits < 8) { s->out = (mem[s->addr & (is24c01 ? 0x7F : 0xFF)] >> (7 - s->bits)) & 1; s->bits++; }
            else { s->out = 1; s->bits = 9; }                       /* release SDA for the master's ACK */
        } else s->out = 1;
    }
}
static void eeprom_bit(bandai_state_t *s, bool is24c01, uint8_t scl, uint8_t sda) {
    ee_t e = { s->eeprom_sda, s->eeprom_scl, s->eeprom_out, s->eeprom_mode, s->eeprom_bits, s->eeprom_addr, s->eeprom_data };
    ee_bit(&e, s->eeprom_mem, is24c01, true, scl, sda);
    s->eeprom_sda = e.sda; s->eeprom_scl = e.scl; s->eeprom_out = e.out; s->eeprom_mode = e.mode;
    s->eeprom_bits = e.bits; s->eeprom_addr = e.addr; s->eeprom_data = e.data;
}

static bool bandai_has_eeprom(const cart_t *c) { return c->mapper_id == 159 || (c->mapper_id == 16 && c->submapper == 5); }
static void bandai_sync(cart_t *c) {
    bandai_state_t *s = &c->s.bandai;
    if (c->mapper_id == 153) {
        int32_t outer = (s->regs[0] & 1) << 4;   /* Famicom Jump II: 256K halves */
        cart_set_prg16k(c, 0, outer | (s->prg & 0x0F)); cart_set_prg16k(c, 1, outer | 0x0F);
        cart_set_chr8k(c, 0); cart_set_wram_6000(c, 0, true);
    } else {
        cart_set_prg16k(c, 0, s->prg & 0x0F); cart_set_prg16k(c, 1, -1);
        for (unsigned i = 0; i < 8; i++) cart_set_chr1k(c, i, s->regs[i]);
        if (c->submapper == 4 && c->mapper_id == 16) cart_unmap_6000(c);   /* FCG-1/2: registers live at $6000-$7FFF */
        else if (c->wram_size && !bandai_has_eeprom(c)) cart_set_wram_6000(c, 0, true); else cart_unmap_6000(c);
    }
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_mirroring(c, mm[s->mirroring & 3]);
}
static void bandai_init(cart_t *c) {
    bandai_state_t *s = &c->s.bandai; for (int i = 0; i < 16; i++) s->regs[i] = 0; s->prg = 0; s->mirroring = 0; s->irq_enable = false; s->irq_counter = 0;
    s->eeprom_scl = s->eeprom_sda = 1; s->eeprom_out = 1; s->eeprom_mode = EE_IDLE;
    for (int i = 0; i < 256; i++) s->eeprom_mem[i] = 0xFF;
    if (c->wram && c->wram_size >= 256 && bandai_has_eeprom(c)) { for (int i = 0; i < 256; i++) s->eeprom_mem[i] = c->wram[i]; }
    bandai_sync(c);
}
static void bandai_write(cart_t *c, uint16_t a, uint8_t v) {
    bandai_state_t *s = &c->s.bandai;
    bool fcg12 = (c->mapper_id == 16 && c->submapper == 4);
    if (fcg12 ? !(a >= 0x6000 && a < 0x8000) : (a < 0x8000 && c->submapper != 0)) return;
    switch (a & 0x0F) {
    case 0: case 1: case 2: case 3: case 4: case 5: case 6: case 7: s->regs[a & 7] = v; bandai_sync(c); break;
    case 8: s->prg = v; bandai_sync(c); break;
    case 9: s->mirroring = v & 3; bandai_sync(c); break;
    case 0xA: s->irq_enable = v & 1; cart_irq(c, false); if (!fcg12) s->irq_counter = (uint16_t)(s->regs[14] | (s->regs[15] << 8)); break;
    case 0xB: if (fcg12) s->irq_counter = (uint16_t)((s->irq_counter & 0xFF00) | v); else s->regs[14] = v; break;
    case 0xC: if (fcg12) s->irq_counter = (uint16_t)((s->irq_counter & 0x00FF) | (v << 8)); else s->regs[15] = v; break;
    case 0xD:
        if (bandai_has_eeprom(c)) { eeprom_bit(s, c->mapper_id == 159, (v >> 5) & 1, (v >> 6) & 1);
            if (c->wram && c->wram_size >= 256) for (int i = 0; i < 256; i++) c->wram[i] = s->eeprom_mem[i]; }
        break;
    }
}
static uint8_t FC_FASTCODE(bandai_read)(cart_t *c, uint16_t a, uint8_t open) {
    if (a >= 0x6000 && a < 0x8000 && bandai_has_eeprom(c)) return (uint8_t)((open & 0xEF) | (c->s.bandai.eeprom_out << 4));
    return open;
}
static void FC_FASTCODE(bandai_cycle)(cart_t *c) {
    bandai_state_t *s = &c->s.bandai;
    if (!s->irq_enable) return;
    if (s->irq_counter == 0) { cart_irq(c, true); s->irq_counter = 0xFFFF; } else s->irq_counter--;
}
const mapper_desc_t mapper_016 = { 16,  "Bandai-FCG/LZ93D50", MF_CPU_CYCLE | MF_READ_LOW | MF_WRITE_6000, bandai_init, bandai_write, bandai_read, NULL, bandai_cycle, NULL };
const mapper_desc_t mapper_159 = { 159, "Bandai-LZ93D50+24C01", MF_CPU_CYCLE | MF_READ_LOW, bandai_init, bandai_write, bandai_read, NULL, bandai_cycle, NULL };
const mapper_desc_t mapper_153 = { 153, "Bandai-LZ93D50+SRAM", MF_CPU_CYCLE, bandai_init, bandai_write, NULL, NULL, bandai_cycle, NULL };

/* ---- 157 Bandai Datach Joint ROM System (LZ93D50 + internal 24C02 + optional external 24C01 + barcode) ----
 * https://www.nesdev.org/wiki/INES_Mapper_157. Writes $8000-$FFFF (mask $800F): $8008 16 KiB PRG bank at $8000
 * ($C000 fixed to the last bank), $8009 mirroring (as mapper 16), $800A-$800C IRQ exactly as 16 sub 5,
 * $800D [DSC. ....]: SDA (bit 6, shared), SCL of the internal X24C02 (bit 5), D = direction (not needed here).
 * $8000-$8003 bit 3: SCL of the external X24C01 (CHR A13 on the sub-cartridge connector; the ASIC's PA12/PA13
 * are grounded so only registers 0-3 ever drive it -- games write the same value to all four or keep rendering
 * off, so the last write wins). $8004-$8007 have no effect. CHR: 8 KiB unbanked CHR-RAM. No PRG-RAM.
 * Reads $6000-$7FFF: bit 4 = EEPROM SDA out (both EEPROMs ANDed), bit 3 = barcode reader serial data; no card
 * is ever swiped, so it reads idle (0); other bits open bus.
 * The external X24C01 is only on Battle Rush's sub-cartridge (NES 2.0: 128 bytes PRG-NVRAM): it is present when
 * the cart has exactly 128 bytes of WRAM (saved there) or >= 384 bytes (internal at 0-255, external at 256-383).
 * Otherwise the internal EEPROM is saved in WRAM bytes 0-255 when WRAM >= 256 bytes. */
typedef struct { bandai_state_t b; ee_t in, ext; uint8_t ext_present; uint8_t ext_mem[128]; } datach_state_t;
_Static_assert(sizeof(datach_state_t) <= sizeof(((cart_t *)0)->s.raw), "datach state too large");
static void datach_save(cart_t *c) {
    datach_state_t *s = (datach_state_t *)c->s.raw;
    if (!c->wram) return;
    if (c->wram_size == 128) { memcpy(c->wram, s->ext_mem, 128); return; }
    if (c->wram_size >= 256) memcpy(c->wram, s->b.eeprom_mem, 256);
    if (c->wram_size >= 384) memcpy(c->wram + 256, s->ext_mem, 128);
}
static void datach_sync(cart_t *c) {
    datach_state_t *s = (datach_state_t *)c->s.raw;
    static const mirroring_t mm[4] = { MIRROR_V, MIRROR_H, MIRROR_1A, MIRROR_1B };
    cart_set_prg16k(c, 0, s->b.prg & 0x0F); cart_set_prg16k(c, 1, -1);
    cart_set_chr8k(c, 0);
    cart_unmap_6000(c);
    cart_set_mirroring(c, mm[s->b.mirroring & 3]);
}
static void datach_init(cart_t *c) {
    datach_state_t *s = (datach_state_t *)c->s.raw;
    memset(s, 0, sizeof *s);
    s->in.scl = s->in.sda = 1; s->in.out = 1; s->in.mode = EE_IDLE;
    s->ext.scl = 0; s->ext.sda = 1; s->ext.out = 1; s->ext.mode = EE_IDLE;   /* CHR reg 0 powers up 0: SCL low */
    memset(s->b.eeprom_mem, 0xFF, sizeof s->b.eeprom_mem); memset(s->ext_mem, 0xFF, sizeof s->ext_mem);
    s->ext_present = c->wram && (c->wram_size == 128 || c->wram_size >= 384);
    if (c->wram && c->wram_size == 128) memcpy(s->ext_mem, c->wram, 128);
    else {
        if (c->wram && c->wram_size >= 256) memcpy(s->b.eeprom_mem, c->wram, 256);
        if (c->wram && c->wram_size >= 384) memcpy(s->ext_mem, c->wram + 256, 128);
    }
    datach_sync(c);
}
static void datach_write(cart_t *c, uint16_t a, uint8_t v) {
    datach_state_t *s = (datach_state_t *)c->s.raw;
    if (a < 0x8000) return;
    switch (a & 0x0F) {
    case 0: case 1: case 2: case 3:
        if (s->ext_present) { ee_bit(&s->ext, s->ext_mem, true, true, (v >> 3) & 1, s->ext.sda); datach_save(c); }
        break;
    case 8: s->b.prg = v; datach_sync(c); break;
    case 9: s->b.mirroring = v & 3; datach_sync(c); break;
    case 0xA: s->b.irq_enable = v & 1; cart_irq(c, false); s->b.irq_counter = (uint16_t)(s->b.regs[14] | (s->b.regs[15] << 8)); break;
    case 0xB: s->b.regs[14] = v; break;
    case 0xC: s->b.regs[15] = v; break;
    case 0xD: {
        uint8_t sda = (v >> 6) & 1;
        ee_bit(&s->in, s->b.eeprom_mem, false, true, (v >> 5) & 1, sda);
        if (s->ext_present) ee_bit(&s->ext, s->ext_mem, true, true, s->ext.scl, sda);
        datach_save(c);
        break;
    }
    default: break;
    }
}
static uint8_t FC_FASTCODE(datach_read)(cart_t *c, uint16_t a, uint8_t open) {
    const datach_state_t *s = (const datach_state_t *)c->s.raw;
    if (a < 0x6000 || a >= 0x8000) return open;
    uint8_t sda = s->in.out & (s->ext_present ? s->ext.out : 1);
    return (uint8_t)((open & 0xE7) | (sda << 4) | (0u << 3) /* barcode reader idle: no card */);
}
const mapper_desc_t mapper_157 = { 157, "Bandai-Datach", MF_CPU_CYCLE | MF_READ_LOW, datach_init, datach_write, datach_read, NULL, bandai_cycle, NULL };
