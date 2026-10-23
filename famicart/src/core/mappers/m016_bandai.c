/* Bandai FCG-1/2 (16 sub4), LZ93D50 (16 sub5), LZ93D50+24C01 (159), LZ93D50+SRAM (153, Famicom Jump II).
 * Includes a small 24C01/24C02 I2C EEPROM model so saves work. */
#include "../mapper.h"

/* ---- minimal I2C EEPROM (24C01: 128B/7-bit addr ; 24C02: 256B/8-bit addr) ---- */
enum { EE_IDLE, EE_ADDR, EE_WADDR, EE_READ, EE_WRITE, EE_ACK, EE_ACK_R, EE_NACK };
static void eeprom_bit(bandai_state_t *s, bool is24c01, uint8_t scl, uint8_t sda) {
    uint8_t pscl = s->eeprom_scl, psda = s->eeprom_sda;
    s->eeprom_scl = scl; s->eeprom_sda = sda;
    if (pscl && scl) {              /* SDA edge while SCL high: start / stop */
        if (psda && !sda) { s->eeprom_mode = EE_ADDR; s->eeprom_bits = 0; s->eeprom_data = 0; s->eeprom_out = 1; return; }
        if (!psda && sda) { s->eeprom_mode = EE_IDLE; s->eeprom_out = 1; return; }
        return;
    }
    if (!pscl && scl) {             /* rising SCL: sample SDA */
        switch (s->eeprom_mode) {
        case EE_ADDR: case EE_WADDR: case EE_WRITE:
            s->eeprom_data = (uint8_t)((s->eeprom_data << 1) | sda);
            if (++s->eeprom_bits == 8) {
                if (s->eeprom_mode == EE_ADDR) {
                    if (is24c01) { s->eeprom_addr = (uint8_t)(s->eeprom_data >> 1); s->eeprom_mode = (s->eeprom_data & 1) ? EE_READ : EE_WRITE; s->eeprom_bits = 0; s->eeprom_data = 0; s->eeprom_out = 0; s->eeprom_mode |= 0x80; }
                    else if ((s->eeprom_data & 0xF0) == 0xA0) { s->eeprom_mode = ((s->eeprom_data & 1) ? EE_READ : EE_WADDR) | 0x80; s->eeprom_bits = 0; s->eeprom_data = 0; s->eeprom_out = 0; }
                    else { s->eeprom_mode = EE_IDLE; s->eeprom_out = 1; }
                } else if (s->eeprom_mode == EE_WADDR) { s->eeprom_addr = s->eeprom_data; s->eeprom_mode = EE_WRITE | 0x80; s->eeprom_bits = 0; s->eeprom_data = 0; s->eeprom_out = 0; }
                else { s->eeprom_mem[s->eeprom_addr & (is24c01 ? 0x7F : 0xFF)] = s->eeprom_data; s->eeprom_addr++; s->eeprom_mode = EE_WRITE | 0x80; s->eeprom_bits = 0; s->eeprom_data = 0; s->eeprom_out = 0; }
            }
            break;
        case EE_READ:
            if (s->eeprom_bits == 8) { /* master ACK/NACK */
                if (sda) s->eeprom_mode = EE_IDLE; else { s->eeprom_addr++; s->eeprom_bits = 0; }
            }
            break;
        default: break;
        }
    } else if (pscl && !scl) {      /* falling SCL: drive SDA */
        if (s->eeprom_mode & 0x80) { s->eeprom_mode &= 0x7F; s->eeprom_out = 0; /* ACK bit */ if (s->eeprom_mode == EE_READ) s->eeprom_bits = 0; return; }
        if (s->eeprom_mode == EE_READ) {
            if (s->eeprom_bits < 8) { s->eeprom_out = (s->eeprom_mem[s->eeprom_addr & (is24c01 ? 0x7F : 0xFF)] >> (7 - s->eeprom_bits)) & 1; s->eeprom_bits++; }
            else s->eeprom_out = 1;
        } else s->eeprom_out = 1;
    }
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
static uint8_t bandai_read(cart_t *c, uint16_t a, uint8_t open) {
    if (a >= 0x6000 && a < 0x8000 && bandai_has_eeprom(c)) return (uint8_t)((open & 0xEF) | (c->s.bandai.eeprom_out << 4));
    return open;
}
static void bandai_cycle(cart_t *c) {
    bandai_state_t *s = &c->s.bandai;
    if (!s->irq_enable) return;
    if (s->irq_counter == 0) { cart_irq(c, true); s->irq_counter = 0xFFFF; } else s->irq_counter--;
}
const mapper_desc_t mapper_016 = { 16,  "Bandai-FCG/LZ93D50", MF_CPU_CYCLE | MF_READ_LOW | MF_WRITE_6000, bandai_init, bandai_write, bandai_read, NULL, bandai_cycle };
const mapper_desc_t mapper_159 = { 159, "Bandai-LZ93D50+24C01", MF_CPU_CYCLE | MF_READ_LOW, bandai_init, bandai_write, bandai_read, NULL, bandai_cycle };
const mapper_desc_t mapper_153 = { 153, "Bandai-LZ93D50+SRAM", MF_CPU_CYCLE, bandai_init, bandai_write, NULL, NULL, bandai_cycle };
