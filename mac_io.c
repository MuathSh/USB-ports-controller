#include <stdio.h>
#include <string.h>
#include <IOKit/IOKitLib.h>
#include <CoreFoundation/CoreFoundation.h>

int main(void)
{
    CFMutableDictionaryRef matching, properties;
    io_iterator_t iterator;
    io_service_t device;
    kern_return_t result;
    CFStringRef vendorName, productName;
    CFNumberRef vendorId, productId, locationId, usbSpeed;
    io_registry_entry_t parent;
    io_name_t parent_name, parent_class;

    char vendor_buf[256], product_buf[256];
    int vendor_id, product_id, location_id, usb_speed;

    matching = IOServiceMatching("IOUSBHostDevice"); // Create a matching dictionary for USB devices

    if (!matching) {
        printf("Failed to create matching dictionary\n");
        return 1;
    }

    result = IOServiceGetMatchingServices(  // Get an iterator for all matching USB devices
        kIOMainPortDefault,                 // The default I/O Kit port
        matching,                           // The matching dictionary
        &iterator                           // The iterator to be filled with matching devices
    );

    if (result != KERN_SUCCESS) { // if the function returns 0, it means success
        printf("Failed to get USB devices\n");
        return 1;
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

        vendorName  = CFDictionaryGetValue(properties, CFSTR("USB Vendor Name"));    // Get the vendor name
        productName = CFDictionaryGetValue(properties, CFSTR("USB Product Name"));  // Get the product name
        vendorId    = CFDictionaryGetValue(properties, CFSTR("idVendor"));             // Get the vendor ID
        productId   = CFDictionaryGetValue(properties, CFSTR("idProduct"));           // Get the product ID
        locationId  = CFDictionaryGetValue(properties, CFSTR("locationID"));        // Get the location ID
        usbSpeed    = CFDictionaryGetValue(properties, CFSTR("USBSpeed"));           // Get the USB speed

        // Initialize the default values
        strcpy(vendor_buf, "UNKNOWN");
        strcpy(product_buf, "UNKNOWN");
        vendor_id = 0;
        product_id = 0;
        location_id = 0;
        usb_speed = 0;

        if (vendorName) {   // Get the vendor Name
            CFStringGetCString(vendorName, vendor_buf, sizeof(vendor_buf), kCFStringEncodingUTF8);
        }
        if (productName) {  // Get the product Name
            CFStringGetCString(productName, product_buf, sizeof(product_buf), kCFStringEncodingUTF8);
        }
        if (vendorId) {     // Get the vendor ID
            CFNumberGetValue(vendorId, kCFNumberIntType, &vendor_id);
        }
        if (productId) {    // Get the product ID
            CFNumberGetValue(productId, kCFNumberIntType, &product_id);
        }
        if (locationId) {   // Get the location ID
            CFNumberGetValue(locationId, kCFNumberIntType, &location_id);
        }
        if (usbSpeed) {     // Get the USB speed
            CFNumberGetValue(usbSpeed, kCFNumberIntType, &usb_speed);
        }

        printf(
            "\n====== Device: %s ======\n"
            "%-12s %-25s | %-12s 0x%04x\n"
            "%-12s %-25s | %-12s 0x%04x\n"
            "%-12s 0x%-23x | %-12s %d\n",
            product_buf,
            "Vendor:",   vendor_buf,  "Vendor ID:",  vendor_id,
            "Product:",  product_buf, "Product ID:", product_id,
            "Location:", location_id, "USB Speed:",  usb_speed
        );

        result = IORegistryEntryGetParentEntry(
            device,
            kIOServicePlane,
            &parent
        );

        if (result == KERN_SUCCESS)
        {
            if (IORegistryEntryGetName(parent, parent_name) == KERN_SUCCESS)
            {
                IOObjectGetClass(parent, parent_class);

                printf(
                    "Parent: %s | Class: %s\n",
                    parent_name,
                    parent_class
                );
            }

            IOObjectRelease(parent);
        }

        CFRelease(properties);
        IOObjectRelease(device);
    }

    IOObjectRelease(iterator);

    return 0;
}
