#include "mapper.h"
#include "audio/expaudio.h"
#include <string.h>

#define M(n) extern const mapper_desc_t mapper_##n;
M(000) M(001) M(002) M(003) M(004) M(005) M(007) M(009) M(010) M(011) M(013) M(016) M(018) M(019)
M(021) M(022) M(023) M(024) M(025) M(026) M(032) M(033) M(034) M(048) M(064) M(065) M(066) M(067) M(068) M(069)
M(070) M(071) M(072) M(073) M(075) M(076) M(078) M(079) M(080) M(082) M(085) M(086) M(087) M(088) M(089) M(092) M(093) M(094) M(095) M(097)
M(118) M(119) M(140) M(152) M(153) M(154) M(159) M(180) M(184) M(185) M(206) M(207) M(210)
#undef M

static const mapper_desc_t *const registry[] = {
    &mapper_000,&mapper_001,&mapper_002,&mapper_003,&mapper_004,&mapper_005,&mapper_007,&mapper_009,&mapper_010,&mapper_011,&mapper_013,&mapper_016,&mapper_018,&mapper_019,
    &mapper_021,&mapper_022,&mapper_023,&mapper_024,&mapper_025,&mapper_026,&mapper_032,&mapper_033,&mapper_034,&mapper_048,&mapper_064,&mapper_065,&mapper_066,&mapper_067,&mapper_068,&mapper_069,
    &mapper_070,&mapper_071,&mapper_072,&mapper_073,&mapper_075,&mapper_076,&mapper_078,&mapper_079,&mapper_080,&mapper_082,&mapper_085,&mapper_086,&mapper_087,&mapper_088,&mapper_089,&mapper_092,&mapper_093,&mapper_094,&mapper_095,&mapper_097,
    &mapper_118,&mapper_119,&mapper_140,&mapper_152,&mapper_153,&mapper_154,&mapper_159,&mapper_180,&mapper_184,&mapper_185,&mapper_206,&mapper_207,&mapper_210,
};

unsigned mapper_count(void) { return (unsigned)FC_ARRAY_LEN(registry); }
const mapper_desc_t *mapper_at(unsigned i) { return i < FC_ARRAY_LEN(registry) ? registry[i] : NULL; }
const mapper_desc_t *mapper_find(uint16_t id) {
    for (unsigned i = 0; i < FC_ARRAY_LEN(registry); i++) if (registry[i]->id == id) return registry[i];
    return NULL;
}

bool mapper_attach(cart_t *c, uint16_t id, uint8_t submapper) {
    const mapper_desc_t *m = mapper_find(id);
    if (!m) return false;
    c->mapper = m; c->mapper_id = id; c->submapper = submapper;
    memset(&c->s, 0, sizeof c->s);
    for (unsigned i = 0; i < 8; i++) { c->prg_map[i] = NULL; c->prg_wmap[i] = NULL; }
    c->chr_wmask = 0; c->irq_line = 0; c->ppu_override = NULL;
    c->has_ppu_hook = (m->flags & MF_PPU_HOOK) && m->ppu_addr;
    c->has_cpu_cycle_hook = (m->flags & MF_CPU_CYCLE) && m->cpu_cycle;
    c->has_read_hook = (m->flags & MF_READ_LOW) && m->read;
    /* default: 8K CHR page 0, mirroring from header, WRAM if present */
    if (c->chr_pages) cart_set_chr8k(c, 0);
    cart_set_mirroring(c, c->mirroring);
    if (c->wram_size) cart_set_wram_6000(c, 0, true);
    if (m->init) m->init(c);
    return true;
}
