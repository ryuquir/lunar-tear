#include "reve_link.h"
#include <string.h>

void rl_dec_init(rl_dec_t *d) { memset(d, 0, sizeof *d); }

/* data symbols still expected after the start symbol, by command */
static uint8_t cmd_need(uint8_t cmd) {
    switch (cmd) {
    case RL_SEQ_W: return 1; case RL_PPU_ADDR: return 2; case RL_PPU_DATA: return 1; case RL_CPU_READ: return 2;
    case RL_POLL: return 1; case RL_LOAD: return 2; case RL_BULK_ADDR: return 3; case RL_BULK: return 1; case RL_COMMAND: return 2;
    default: return 0xFF;
    }
}

bool rl_dec_feed(rl_dec_t *d, uint16_t sym, rl_event_t *ev) {
    ev->kind = RL_EV_NONE;
    if (sym & RL_START) {
        if (d->need || d->load_len || d->bulk_left) d->bad++;          /* previous frame cut short */
        d->load_len = 0; d->bulk_left = 0; d->have = 0; d->sym0 = sym;
        if (!(sym & RL_CMD)) { d->type = 0xF0; d->need = 2; return false; }   /* CPU write */
        d->type = sym & 0xFF; d->need = cmd_need(d->type);
        if (d->need == 0xFF) { d->need = 0; d->bad++; ev->kind = RL_EV_BAD; return true; }
        return false;
    }
    uint8_t v = sym & 0xFF;
    if (d->load_len) {                                                /* LOAD payload */
        if (d->load_fill < RL_LOAD_MAX) d->load[d->load_fill] = v;
        if (++d->load_fill == d->load_len) { d->load_len = 0; ev->kind = RL_EV_LOAD; return true; }
        return false;
    }
    if (d->bulk_left) {                                               /* BULK payload */
        d->bulk_left--; ev->kind = RL_EV_BULK_BYTE; ev->data = v; ev->off = d->bulk_off++; return true;
    }
    if (!d->need) { d->bad++; return false; }                         /* stray data symbol */
    d->b[d->have++] = v;
    if (--d->need) return false;
    switch (d->type) {
    case 0xF0: ev->kind = RL_EV_WRITE; ev->addr = (uint16_t)(((d->sym0 & 0xFF) << 8) | d->b[0]); ev->data = d->b[1]; d->last_waddr = ev->addr; return true;
    case RL_SEQ_W: ev->kind = RL_EV_WRITE; ev->addr = ++d->last_waddr; ev->data = d->b[0]; return true;
    case RL_PPU_ADDR: ev->kind = RL_EV_PPU_ADDR; ev->addr = (uint16_t)(((d->b[0] & 0x3F) << 8) | d->b[1]); ev->arg = (d->b[0] >> 6) & 1; return true;
    case RL_PPU_DATA: ev->kind = RL_EV_PPU_DATA; ev->data = d->b[0]; return true;
    case RL_CPU_READ: ev->kind = RL_EV_READ; ev->addr = (uint16_t)((d->b[0] << 8) | d->b[1]); return true;
    case RL_POLL: ev->kind = RL_EV_POLL; ev->arg = d->b[0]; return true;
    case RL_LOAD: d->load_len = (uint16_t)(d->b[0] | (d->b[1] << 8)); d->load_fill = 0;
                  if (d->load_len == 0 || d->load_len > RL_LOAD_MAX) { d->load_len = 0; d->bad++; ev->kind = RL_EV_BAD; return true; }
                  return false;
    case RL_BULK_ADDR: d->bulk_off = (uint32_t)d->b[0] | ((uint32_t)d->b[1] << 8) | ((uint32_t)d->b[2] << 16); ev->kind = RL_EV_BULK_ADDR; ev->off = d->bulk_off; return true;
    case RL_BULK: d->bulk_left = (uint16_t)(d->b[0] + 1); return false;
    case RL_COMMAND: ev->kind = RL_EV_COMMAND; ev->data = d->b[0]; ev->arg = d->b[1]; return true;
    }
    return false;
}
