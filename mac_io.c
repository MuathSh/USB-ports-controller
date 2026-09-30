#include <stdio.h>
#include <IOKit/IOKitLib.h>

int main(void)
{
    CFMutableDictionaryRef matching;
    io_iterator_t iterator;
    io_service_t device;
    kern_return_t result;
    io_name_t name;

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
        // Get the name of the device
        if (IORegistryEntryGetName(device, name) == KERN_SUCCESS) { // if the function returns 0, it means success
            printf("%s\n", name);
        }

        IOObjectRelease(device); // free
    }

    IOObjectRelease(iterator);

    return 0;
}
