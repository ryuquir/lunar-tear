/* Expansion-audio synthesis: VRC6, MMC5 (pulse+PCM), Sunsoft 5B, Namco 163, FDS, VRC7 (OPLL).
 * All chips run from the latched register files in expaudio.c and are rendered per output sample
 * at `rate` Hz with fixed-point phase accumulators. Accuracy target: "sounds right", not cycle-exact. */
#include "expaudio.h"
#include "../profile.h"
#include <string.h>
#include <math.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define CPU_HZ 1789773.0
extern uint8_t expaudio_regs_vrc6[16], expaudio_regs_vrc7[64], expaudio_regs_mmc5[24], expaudio_regs_n163[128], expaudio_regs_s5b[16], expaudio_regs_fds[16];
extern uint8_t expaudio_chip_mask(void);
extern int expaudio_chip_volume(uint8_t chip);
static uint32_t rate = 48000;
static double cps;   /* CPU cycles per output sample */

/* ------------------------------------------------------------------ VRC6 */
static struct { uint32_t ph[3]; uint8_t saw_acc, saw_step; } v6;
static int vrc6_sample(void) {
    const uint8_t *r = expaudio_regs_vrc6;
    if (r[3] & 1) return 0;                               /* halt */
    unsigned shift = (r[3] & 4) ? 8 : (r[3] & 2) ? 4 : 0; /* frequency scaling */
    int out = 0;
    for (int ch = 0; ch < 2; ch++) {
        const uint8_t *c = r + ch * 4 + ((ch == 0) ? 0 : 0);
        uint8_t ctl = expaudio_regs_vrc6[ch * 4 + 0 + (ch ? 0 : 0)];
        (void)c; (void)ctl;
    }
    /* pulse 1: $9000-9002 (regs 0..2), pulse 2: $A000-A002 (regs 4..6), saw: $B000-B002 (regs 8..10) */
    for (int ch = 0; ch < 2; ch++) {
        const uint8_t *c = r + ch * 4;
        if (!(c[2] & 0x80)) continue;
        unsigned period = ((c[1] | ((c[2] & 0x0F) << 8)) >> shift) + 1;
        uint32_t inc = (uint32_t)(cps / period * 65536.0 / 16.0);   /* 16 duty steps per period */
        v6.ph[ch] += inc;
        unsigned step = (v6.ph[ch] >> 16) & 15;
        unsigned duty = (c[0] >> 4) & 7;
        bool high = (c[0] & 0x80) || step <= duty;
        if (high) out += c[0] & 15;
    }
    { const uint8_t *c = r + 8;
      if (c[2] & 0x80) {
        unsigned period = ((c[1] | ((c[2] & 0x0F) << 8)) >> shift) + 1;
        uint32_t inc = (uint32_t)(cps / period * 65536.0 / 14.0);   /* accumulator clocks every 2 periods -> 7 steps over 14 */
        uint32_t before = v6.ph[2] >> 16; v6.ph[2] += inc; uint32_t after = v6.ph[2] >> 16;
        for (uint32_t k = before; k < after; k++) {
            if ((k & 1) == 0) { v6.saw_step++; if (v6.saw_step >= 7) { v6.saw_step = 0; v6.saw_acc = 0; } else v6.saw_acc += c[0] & 0x3F; }
        }
        out += v6.saw_acc >> 3;
      } }
    return out * 256;   /* 0..(15+15+31)*256 */
}

/* ------------------------------------------------------------------ MMC5 pulse + PCM */
static struct { uint32_t ph[2]; uint8_t env_vol[2], env_div[2], env_start[2]; uint8_t len[2]; double frame_acc; } m5;
static const uint8_t duty_tbl[4][8] = { {0,1,0,0,0,0,0,0}, {0,1,1,0,0,0,0,0}, {0,1,1,1,1,0,0,0}, {1,0,0,1,1,1,1,1} };
static const uint8_t len_tbl[32] = { 10,254,20,2,40,4,80,6,160,8,60,10,14,12,26,14,12,16,24,18,48,20,96,22,192,24,72,26,16,28,32,30 };
static int mmc5_sample(void) {
    uint8_t *r = expaudio_regs_mmc5; int out = 0;
    /* quarter-frame clock ~240 Hz for envelopes/length (approximation of the MMC5 frame sequencer) */
    m5.frame_acc += 240.0 / rate;
    bool qf = false; if (m5.frame_acc >= 1.0) { m5.frame_acc -= 1.0; qf = true; }
    for (int ch = 0; ch < 2; ch++) {
        uint8_t *c = r + ch * 4; bool en = (r[0x15] >> ch) & 1;
        if (c[3] & 0x80) { c[3] &= 0x7F; m5.len[ch] = len_tbl[c[3] >> 3]; m5.env_start[ch] = 1; m5.ph[ch] = 0; }  /* $5003/$5007 write side effect latched via bit7 marker */
        if (!en) m5.len[ch] = 0;
        if (qf) {
            if (m5.env_start[ch]) { m5.env_start[ch] = 0; m5.env_vol[ch] = 15; m5.env_div[ch] = c[0] & 15; }
            else if (m5.env_div[ch] == 0) { m5.env_div[ch] = c[0] & 15; if (m5.env_vol[ch]) m5.env_vol[ch]--; else if (c[0] & 0x20) m5.env_vol[ch] = 15; }
            else m5.env_div[ch]--;
            static uint8_t half; if ((half ^= 1) == 0 && !(c[0] & 0x20) && m5.len[ch]) m5.len[ch]--;
        }
        unsigned period = c[2] | ((c[3] & 7) << 8);
        if (!en || m5.len[ch] == 0 || period < 8) continue;
        uint32_t inc = (uint32_t)(cps / (16.0 * (period + 1)) * 65536.0 * 8.0);
        m5.ph[ch] += inc;
        unsigned vol = (c[0] & 0x10) ? (c[0] & 15) : m5.env_vol[ch];
        if (duty_tbl[c[0] >> 6][(m5.ph[ch] >> 16) & 7]) out += vol;
    }
    out *= 256;
    if (!(r[0x10] & 1)) out += ((int)r[0x11] - 128) * 32;   /* PCM write mode: $5011 8-bit sample */
    return out;
}

/* ------------------------------------------------------------------ Sunsoft 5B (YM2149 subset) */
static struct { uint32_t ph[3]; uint32_t nph; uint32_t lfsr; uint32_t eph; int estep; uint8_t ehold, ealt, eatt; } s5;
static const uint16_t ay_vol[32] = { 0,0,6,9,12,16,21,26,33,40,50,61,75,91,112,135,165,200,244,296,360,436,530,643,781,948,1150,1397,1697,2060,2500,3030 };
static int s5b_sample(void) {
    const uint8_t *r = expaudio_regs_s5b; int out = 0;
    if (!s5.lfsr) s5.lfsr = 1;
    /* noise */
    unsigned np = (r[6] & 0x1F) + 1; uint32_t ninc = (uint32_t)(cps / (32.0 * np) * 65536.0);
    uint32_t nb = s5.nph >> 16; s5.nph += ninc;
    for (uint32_t k = nb; k < (s5.nph >> 16); k++) { uint32_t bit = (s5.lfsr ^ (s5.lfsr >> 3)) & 1; s5.lfsr = (s5.lfsr >> 1) | (bit << 16); }
    bool noise_hi = s5.lfsr & 1;
    /* envelope: 16-bit period, shapes per reg 13 */
    unsigned ep = (r[11] | (r[12] << 8)); if (!ep) ep = 1;
    uint32_t einc = (uint32_t)(cps / (32.0 * ep) * 65536.0);
    uint32_t eb = s5.eph >> 16; s5.eph += einc;
    uint8_t shape = r[13] & 15; bool cont = shape & 8, att = shape & 4, alt = shape & 2, hold = shape & 1;
    for (uint32_t k = eb; k < (s5.eph >> 16); k++) {
        if (s5.ehold) break;
        s5.estep++;
        if (s5.estep > 31) {
            if (!cont || hold) { s5.ehold = 1; s5.estep = 31; if (!cont || (alt ^ hold)) s5.eatt ^= 1; }
            else { s5.estep = 0; if (alt) s5.eatt ^= 1; }
        }
    }
    int evol = s5.eatt ^ att ? s5.estep : 31 - s5.estep; if (s5.ehold && !cont) evol = 0;
    for (int ch = 0; ch < 3; ch++) {
        unsigned p = (r[ch * 2] | ((r[ch * 2 + 1] & 15) << 8)); if (!p) p = 1;
        uint32_t inc = (uint32_t)(cps / (32.0 * p) * 65536.0);
        s5.ph[ch] += inc;
        bool tone = (s5.ph[ch] >> 16) & 1;
        bool tone_en = !((r[7] >> ch) & 1), noise_en = !((r[7] >> (ch + 3)) & 1);
        bool on = (tone || !tone_en) && (noise_hi || !noise_en);
        if (!on) continue;
        unsigned v = (r[8 + ch] & 0x10) ? evol : ((r[8 + ch] & 15) * 2 + 1);
        out += ay_vol[v & 31];
    }
    return out * 2;   /* ~0..18000 */
}

/* ------------------------------------------------------------------ Namco 163 */
static struct { uint32_t ph[8]; } n1;
static int n163_sample(void) {
    const uint8_t *ram = expaudio_regs_n163;
    unsigned nch = ((ram[0x7F] >> 4) & 7) + 1;
    int out = 0;
    for (unsigned i = 8 - nch; i < 8; i++) {
        const uint8_t *c = ram + 0x40 + i * 8;
        uint32_t freq = c[0] | (c[2] << 8) | ((c[4] & 3) << 16);
        unsigned len = 256 - (c[4] & 0xFC); if (!len) len = 256;
        unsigned vol = c[7] & 15;
        /* each channel is clocked once per 15*nch cycles with phase += freq (24-bit phase, 16 fractional bits) */
        uint64_t ph = n1.ph[i] + (uint64_t)(freq * cps / (15.0 * nch));
        uint32_t maxph = (uint32_t)len << 16; if (maxph) ph %= maxph;
        n1.ph[i] = (uint32_t)ph;
        unsigned idx = ((ph >> 16) + c[6]) & 0xFF;
        int s = (ram[idx >> 1] >> ((idx & 1) * 4)) & 15;
        out += (s - 8) * (int)vol;
    }
    return out * 128 / (int)nch;   /* max ±15360 with one channel */
}

/* ------------------------------------------------------------------ FDS */
extern uint8_t expaudio_fds_wave[64], expaudio_fds_mod[32];
static struct { uint32_t ph, mph; int8_t mod_counter; uint8_t vol_gain, mod_gain; double vol_acc, mod_acc; } fd;
static int fds_sample(void) {
    const uint8_t *r = expaudio_regs_fds;   /* $4080..$408F */
    if (r[0x09] & 0x80) return 0;           /* wave write enable: output held */
    bool halt_env = r[0x03] & 0x40, halt_mod = r[0x07] & 0x80, halt_all = r[0x03] & 0x80;
    unsigned env_speed = r[0x0A] ? r[0x0A] : 1;
    /* envelopes */
    if (!halt_env) {
        double step = cps / (8.0 * env_speed);
        if (!(r[0x00] & 0x80)) { fd.vol_acc += step / ((r[0x00] & 0x3F) + 1); while (fd.vol_acc >= 1) { fd.vol_acc -= 1; if (r[0x00] & 0x40) { if (fd.vol_gain < 32) fd.vol_gain++; } else if (fd.vol_gain) fd.vol_gain--; } }
        else fd.vol_gain = r[0x00] & 0x3F;
        if (!(r[0x04] & 0x80)) { fd.mod_acc += step / ((r[0x04] & 0x3F) + 1); while (fd.mod_acc >= 1) { fd.mod_acc -= 1; if (r[0x04] & 0x40) { if (fd.mod_gain < 32) fd.mod_gain++; } else if (fd.mod_gain) fd.mod_gain--; } }
        else fd.mod_gain = r[0x04] & 0x3F;
    } else { if (r[0x00] & 0x80) fd.vol_gain = r[0x00] & 0x3F; if (r[0x04] & 0x80) fd.mod_gain = r[0x04] & 0x3F; }
    /* modulator */
    unsigned mfreq = r[0x06] | ((r[0x07] & 0x0F) << 8);
    int mod = 0;
    if (!halt_mod && mfreq) {
        uint32_t before = fd.mph >> 16; fd.mph += (uint32_t)(mfreq * cps);   /* 16.16 of a 65536-step cycle, table index = top 5 bits */
        for (uint32_t k = before >> 11; k < (fd.mph >> 16) >> 11; k++) {
            static const int8_t mtab[8] = { 0, 1, 2, 4, 0, -4, -2, -1 };
            uint8_t m = expaudio_fds_mod[k & 31];
            if (m == 4) fd.mod_counter = 0; else { fd.mod_counter += mtab[m]; if (fd.mod_counter >= 64) fd.mod_counter -= 128; if (fd.mod_counter < -64) fd.mod_counter += 128; }
        }
        int temp = fd.mod_counter * (int)(fd.mod_gain > 32 ? 32 : fd.mod_gain);
        int rem = temp & 0x0F; temp >>= 4; if (rem > 0 && !(temp & 0x80)) temp += (fd.mod_counter < 0) ? -1 : 2;
        if (temp >= 192) temp -= 256; else if (temp < -64) temp += 256;
        mod = temp;
    }
    unsigned freq = r[0x02] | ((r[0x03] & 0x0F) << 8);
    if (halt_all || !freq) return 0;
    int f = (int)freq + ((int)freq * mod) / 64; if (f < 0) f = 0;
    fd.ph += (uint32_t)(f * cps);       /* 16.16 over 65536 -> 64-entry table index = top 6 bits */
    unsigned idx = (fd.ph >> 26) & 63;
    int s = expaudio_fds_wave[idx] - 32;
    int gain = fd.vol_gain > 32 ? 32 : fd.vol_gain;
    static const int master[4] = { 36, 24, 18, 14 };   /* $4089 master volume: 2/2, 2/3, 2/4, 2/5 */
    return s * gain * master[r[0x09] & 3] / 4;
}

/* ------------------------------------------------------------------ VRC7 (YM2413 subset, 6 ch, 2-op) */
#define OPLL_RATE 49716.0
static const uint8_t vrc7_patches[16][8] = {
    {0,0,0,0,0,0,0,0},
    {0x03,0x21,0x05,0x06,0xE8,0x81,0x42,0x27}, {0x13,0x41,0x14,0x0D,0xD8,0xF6,0x23,0x12}, {0x11,0x11,0x08,0x08,0xFA,0xB2,0x20,0x12},
    {0x31,0x61,0x0C,0x07,0xA8,0x64,0x61,0x27}, {0x32,0x21,0x1E,0x06,0xE1,0x76,0x01,0x28}, {0x02,0x01,0x06,0x00,0xA3,0xE2,0xF4,0xF4},
    {0x21,0x61,0x1D,0x07,0x82,0x81,0x11,0x07}, {0x23,0x21,0x22,0x17,0xA2,0x72,0x01,0x17}, {0x35,0x11,0x25,0x00,0x40,0x73,0x72,0x01},
    {0xB5,0x01,0x0F,0x0F,0xA8,0xA5,0x51,0x02}, {0x17,0xC1,0x24,0x07,0xF8,0xF8,0x22,0x12}, {0x71,0x23,0x11,0x06,0x65,0x74,0x18,0x16},
    {0x01,0x02,0xD3,0x05,0xC9,0x95,0x03,0x02}, {0x61,0x63,0x0C,0x00,0x94,0xC0,0x33,0xF6}, {0x21,0x72,0x0D,0x00,0xC1,0xD5,0x56,0x06},
};
static const uint8_t ml_tab[16] = { 1,2,4,6,8,10,12,14,16,18,20,20,24,24,30,30 };   /* x0.5 */
static const uint8_t ksl_tab[16] = { 0,24,32,37,40,43,45,47,48,50,51,52,53,54,55,56 }; /* dB*2 for fnum>>5 at block 7 */
typedef struct { uint32_t ph; int32_t eg; uint8_t state; int32_t out, out_prev; } op_t;   /* eg: attenuation 0..(127<<16) in 0.375 dB units */
static struct { op_t op[6][2]; uint8_t key[6]; uint32_t am_ph, vib_ph; int16_t sin_tab[1024]; int32_t exp_tab[256]; bool init; } v7;
enum { EG_OFF, EG_ATT, EG_DEC, EG_SUS, EG_REL };
static void vrc7_init(void) {
    for (int i = 0; i < 1024; i++) v7.sin_tab[i] = (int16_t)(sin(i * 2 * M_PI / 1024) * 4095);
    v7.init = true;
}
static double eg_rate(int R, int rks) { /* attenuation change per native sample for rate R (0-15) incl. key scaling (0.375 dB units) */
    if (R == 0) return 0;
    int rv = R * 4 + rks; if (rv > 63) rv = 63;
    /* OPLL decay from 0 to 48 dB takes about 2.3 s at rv=4 and halves every 4 rate steps */
    double seconds = 2.3 * pow(2.0, -(rv - 4) / 4.0);
    return 128.0 / (seconds * OPLL_RATE);
}
static int vrc7_sample(void) {
    if (!v7.init) vrc7_init();
    const uint8_t *r = expaudio_regs_vrc7;
    double native_per_sample = OPLL_RATE / rate;
    v7.am_ph += (uint32_t)(3.7 / rate * 4294967296.0); v7.vib_ph += (uint32_t)(6.4 / rate * 4294967296.0);
    int am = (int)((1.0 - cos(v7.am_ph / 4294967296.0 * 2 * M_PI)) * 0.5 * 4.8 / 0.375);  /* 0..~13 units (4.8 dB) */
    double vib = sin(v7.vib_ph / 4294967296.0 * 2 * M_PI) * 0.07;                             /* ±7 cents-ish on fnum */
    int out = 0;
    for (int ch = 0; ch < 6; ch++) {
        unsigned fnum = r[0x10 + ch] | ((r[0x20 + ch] & 1) << 8);
        unsigned block = (r[0x20 + ch] >> 1) & 7;
        bool key = r[0x20 + ch] & 0x10, sus = r[0x20 + ch] & 0x20;
        unsigned inst = r[0x30 + ch] >> 4, vol = r[0x30 + ch] & 15;
        const uint8_t *p = inst ? vrc7_patches[inst] : r;   /* inst 0 = custom patch in $00-$07 */
        op_t *m = &v7.op[ch][0], *c = &v7.op[ch][1];
        /* key on/off */
        if (key && !v7.key[ch]) { for (int o = 0; o < 2; o++) { v7.op[ch][o].state = EG_ATT; v7.op[ch][o].ph = 0; } }
        if (!key && v7.key[ch]) { for (int o = 0; o < 2; o++) if (v7.op[ch][o].state != EG_OFF) v7.op[ch][o].state = EG_REL; }
        v7.key[ch] = key;
        int rks = (block << 1) | (fnum >> 8); /* key scale rate (KSR) base */
        int chan_out = 0, mod_out = 0;
        for (int o = 0; o < 2; o++) {
            op_t *op = o ? c : m;
            uint8_t b0 = p[o], b2 = p[2 + o], b4 = p[4 + o], b6 = p[6 + o];
            bool am_en = b0 & 0x80, vib_en = b0 & 0x40, egt = b0 & 0x20, ksr = b0 & 0x10; unsigned ml = b0 & 15;
            unsigned ksl = b2 >> 6, tl = o ? 0 : (b2 & 0x3F);
            unsigned ar = b4 >> 4, dr = b4 & 15, sl = b6 >> 4, rr = b6 & 15;
            bool rect = p[3] & (o ? 0x10 : 0x08);
            unsigned fb = p[3] & 7;
            /* phase */
            double f = fnum * (1.0 + (vib_en ? vib : 0.0));
            double inc = f * ml_tab[ml] / 2.0 * (double)(1 << block) / (1 << 19) * OPLL_RATE;   /* Hz */
            op->ph += (uint32_t)(inc / rate * 4294967296.0);
            /* envelope (attenuation units of 0.375 dB, 16 fractional bits) */
            int ks = ksr ? rks : (rks >> 2);
            double step = native_per_sample * 65536.0;
            switch (op->state) {
            case EG_ATT: { double rt = eg_rate(ar, ks); if (ar == 15) op->eg = 0; else op->eg -= (int32_t)(rt * step * (op->eg / (128.0 * 65536) + 0.1) * 6);
                           if (op->eg <= 0) { op->eg = 0; op->state = EG_DEC; } break; }
            case EG_DEC: { op->eg += (int32_t)(eg_rate(dr, ks) * step); int slv = (sl == 15 ? 127 : sl * 8) << 16; if (op->eg >= slv) { op->eg = slv; op->state = EG_SUS; } break; }
            case EG_SUS: if (!egt) op->eg += (int32_t)(eg_rate(rr, ks) * step); break;
            case EG_REL: op->eg += (int32_t)(eg_rate(sus ? 5 : (egt ? rr : 7), ks) * step); break;
            default: op->eg = 127 << 16; break;
            }
            if (op->eg >= (127 << 16)) { op->eg = 127 << 16; if (op->state == EG_REL) op->state = EG_OFF; }
            /* total attenuation */
            int att = op->eg >> 16;                                   /* 0..127 */
            att += o ? vol * 8 : tl * 2;                              /* carrier volume 3 dB steps, modulator TL 0.75 dB */
            if (ksl) { int k = ksl_tab[fnum >> 5] - 8 * (7 - block); if (k > 0) att += (k * 2) >> (3 - ksl); }
            if (am_en) att += am;
            if (att > 127) att = 127;
            /* waveform */
            uint32_t ph = op->ph;
            if (o == 0 && fb) ph += (uint32_t)(((m->out + m->out_prev) / 2) * (1 << (fb + 5)));
            if (o == 1) ph += (uint32_t)(mod_out * 1024);
            int s = v7.sin_tab[(ph >> 22) & 1023];
            if (rect && s < 0) s = 0;
            int level = (int)(s * pow(10.0, -att * 0.375 / 20.0));
            if (o == 0) { m->out_prev = m->out; m->out = level; mod_out = level; }
            else chan_out = level;
        }
        if (c->state != EG_OFF) out += chan_out;
    }
    return out * 2;
}

/* ------------------------------------------------------------------ mixer */
void expaudio_set_rate(uint32_t hz) { rate = hz ? hz : 48000; cps = CPU_HZ / rate; }
void expaudio_render(int16_t *buf, unsigned n) {
    if (!cps) expaudio_set_rate(rate);
    uint8_t mask = expaudio_chip_mask();
    for (unsigned i = 0; i < n; i++) {
        int32_t acc = 0;
        if (mask & (1u << AUDIO_VRC6)) acc += vrc6_sample() * expaudio_chip_volume(AUDIO_VRC6) / 128;
        if (mask & (1u << AUDIO_MMC5)) acc += mmc5_sample() * expaudio_chip_volume(AUDIO_MMC5) / 128;
        if (mask & (1u << AUDIO_S5B))  acc += s5b_sample()  * expaudio_chip_volume(AUDIO_S5B) / 128;
        if (mask & (1u << AUDIO_N163)) acc += n163_sample() * expaudio_chip_volume(AUDIO_N163) / 128;
        if (mask & (1u << AUDIO_FDS))  acc += fds_sample()  * expaudio_chip_volume(AUDIO_FDS) / 128;
        if (mask & (1u << AUDIO_VRC7)) acc += vrc7_sample() * expaudio_chip_volume(AUDIO_VRC7) / 128;
        if (acc > 32767) acc = 32767; else if (acc < -32768) acc = -32768;
        buf[i] = (int16_t)acc;
    }
}
