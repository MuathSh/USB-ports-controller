#ifndef MAC_IO_LIB_H
#define MAC_IO_LIB_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint64_t id;
    uint64_t port_id;

    uint32_t location_id;
    uint32_t usb_speed;

    uint16_t vendor_id;
    uint16_t product_id;

    char vendor_name[256];
    char product_name[256];

    char port_name[128];
    char port_class[128];

} MacUsbDevice;

size_t mac_scan_usb(
    MacUsbDevice *devices,
    size_t capacity
);

#endif