#pragma once
/* USB-CDC command channel (115200 8N1 over the Pico's USB / the board's USB-C).
 * Text commands, one per line:
 *   INFO                 -> prints the detection result and bus statistics
 *   RESET                -> reboots the cartridge MCU (watchdog); the console must be reset too
 *   BOOTSEL              -> reboots into the UF2 mass-storage bootloader
 *   LOAD <bytes> [crc32] -> receive a raw .nes image (binary follows) into the flash ROM slot, then reboot
 *   PROFILE <hex>        -> write a cart_profile_t (48 bytes, hex) in front of the image, then reboot
 */
void usb_cmd_init(void);
void usb_cmd_poll(void);   /* call from the main loop */
void usb_cmd_print_info(void);   /* provided by main.c */
