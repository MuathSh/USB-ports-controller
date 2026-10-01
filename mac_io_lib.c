#include <string.h>

#include <IOKit/IOKitLib.h>
#include <CoreFoundation/CoreFoundation.h>

#include "mac_io_lib.h"

static void cf_string_to_c(CFStringRef value, char *buffer, size_t buffer_size)
{
    if (!value)
        return;

    CFStringGetCString(
        value,
        buffer,
        buffer_size,
        kCFStringEncodingUTF8
    );
}

size_t mac_scan_usb(MacUsbDevice *devices, size_t capacity)
{
    size_t count = 0;

    CFMutableDictionaryRef matching, properties;
    io_iterator_t iterator;
    io_service_t device;
    kern_return_t result;
    CFStringRef vendorName, productName;
    CFNumberRef vendorId, productId, locationId, usbSpeed;
    io_registry_entry_t parent;
    io_name_t parent_name, parent_class;

    MacUsbDevice *out = NULL;

    matching = IOServiceMatching("IOUSBHostDevice"); // Create a matching dictionary for USB devices

    if (!matching) {
        printf("Failed to create matching dictionary\n");
        return 0;
    }

    result = IOServiceGetMatchingServices(  // Get an iterator for all matching USB devices
        kIOMainPortDefault,                 // The default I/O Kit port
        matching,                           // The matching dictionary
        &iterator                           // The iterator to be filled with matching devices
    );

    if (result != KERN_SUCCESS) { // if the function returns 0, it means success
        printf("Failed to get USB devices\n");
        return 0;
    }

    // Iterate through all matching USB devices
    while ((device = IOIteratorNext(iterator)) != IO_OBJECT_NULL) // if device is not NULL
    {
        properties = NULL;
            
        result = IORegistryEntryCreateCFProperties(
            device,                 // Get the properties of the device
            &properties,            // The properties dictionary to be filled
            kCFAllocatorDefault,    // The default allocator
            0                       // 0 means no special options
        );

        if (result != KERN_SUCCESS || !properties) {
            IOObjectRelease(device);
            continue;   // Skip to the next device if we failed to get properties
        }

        out = NULL;

        /**
         * Initialize the output device if it exists and we haven't reached the capacity
         */
        if (devices && count < capacity) {
            out = &devices[count];
            memset(out, 0, sizeof(*out));
        }

        vendorName  = CFDictionaryGetValue(properties, CFSTR("USB Vendor Name"));    // Get the vendor name
        productName = CFDictionaryGetValue(properties, CFSTR("USB Product Name"));  // Get the product name
        vendorId    = CFDictionaryGetValue(properties, CFSTR("idVendor"));             // Get the vendor ID
        productId   = CFDictionaryGetValue(properties, CFSTR("idProduct"));           // Get the product ID
        locationId  = CFDictionaryGetValue(properties, CFSTR("locationID"));        // Get the location ID
        usbSpeed    = CFDictionaryGetValue(properties, CFSTR("USBSpeed"));           // Get the USB speed

        // Initialize the default values
        if (out) {
            strcpy(out->vendor_name, "UNKNOWN");
            strcpy(out->product_name, "UNKNOWN");

            cf_string_to_c(
                vendorName,
                out->vendor_name,
                sizeof(out->vendor_name)
            );

            cf_string_to_c(
                productName,
                out->product_name,
                sizeof(out->product_name)
            );

            if (vendorId) {     // Get the vendor ID
                CFNumberGetValue(vendorId, kCFNumberSInt16Type, &out->vendor_id);
            }
            if (productId) {    // Get the product ID
                CFNumberGetValue(productId, kCFNumberSInt16Type, &out->product_id);
            }
            if (locationId) {   // Get the location ID
                CFNumberGetValue(locationId, kCFNumberSInt32Type, &out->location_id);
            }
            if (usbSpeed) {     // Get the USB speed
                CFNumberGetValue(usbSpeed, kCFNumberSInt32Type, &out->usb_speed);
            }
            IORegistryEntryGetRegistryEntryID(device, &out->id);

            result = IORegistryEntryGetParentEntry(
                device,
                kIOServicePlane,
                &parent
            );

            if (result == KERN_SUCCESS)
            {
                /*
                 * Parent ID
                 */
                IORegistryEntryGetRegistryEntryID(parent, &out->port_id);

                /*
                 * Parent name
                 */
                if (IORegistryEntryGetName(parent, parent_name) == KERN_SUCCESS)
                {
                    strncpy(
                        out->port_name,
                        parent_name,
                        sizeof(out->port_name) - 1
                    );
                    out->port_name[sizeof(out->port_name) - 1] = '\0';
                }

                /*
                 * Parent class
                 */
                if (IOObjectGetClass(parent, parent_class) == KERN_SUCCESS)
                {
                    strncpy(
                        out->port_class,
                        parent_class,
                        sizeof(out->port_class) - 1
                    );
                    out->port_class[sizeof(out->port_class) - 1] = '\0';
                }

                IOObjectRelease(parent);
            }
        }

        count++;

        CFRelease(properties);
        IOObjectRelease(device);
    }

    IOObjectRelease(iterator);

    return count;
}
