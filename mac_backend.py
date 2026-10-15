import ctypes
import os
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from backend import Backend


class MacUsbDevice(ctypes.Structure):
    # Must match MacUsbDevice in mac_io_lib.h (same order, same types)
    _fields_ = [
        ("id", ctypes.c_uint64),
        ("port_id", ctypes.c_uint64),

        ("location_id", ctypes.c_uint32),
        ("usb_speed", ctypes.c_uint32),

        ("vendor_id", ctypes.c_uint16),
        ("product_id", ctypes.c_uint16),

        ("vendor_name", ctypes.c_char * 256),
        ("product_name", ctypes.c_char * 256),

        ("port_name", ctypes.c_char * 128),
        ("port_class", ctypes.c_char * 128),
    ]

class MacBackend(Backend):

    def __init__(self):
        self.devices = []
        self.ports = []

        lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libmac_io.dylib")
        self.mac_io = ctypes.CDLL(lib_path)

        self.mac_io.mac_scan_usb.argtypes = [
            ctypes.POINTER(MacUsbDevice),
            ctypes.c_size_t,
        ]
        self.mac_io.mac_scan_usb.restype = ctypes.c_size_t

        self._refresh_usb()

    class DeviceType(Enum):
        CAMERA = "camera"
        KEYBOARD = "keyboard"
        MOUSE = "mouse"
        STORAGE = "storage"
        NETWORK = "network"
        UNKNOWN = "unknown"


    class PortType(Enum):
        USB = "usb"
        PCIE = "pcie"
        SATA = "sata"
        UNKNOWN = "unknown"

    @dataclass
    class Port:
        id: int
        name: str
        state: bool
        type: "Backend.PortType"

    @dataclass
    class Device:
        id: int
        name: str
        port: "Backend.Port"
        vendor_id: int
        model_id: int
        type: "Backend.DeviceType"
        children: list["Backend.Device"] = field(default_factory=list)

    @dataclass
    class UsbPort(Port):
        gen: str
        speed: int

    def get_d(self, id):
        """
        Get specific device by id
        """
        self._refresh_usb()
        for device in self.devices:
            if device.id == id:
                return device
        return None

    def get_p(self, id):
        """
        Get specific port by id
        """
        self._refresh_usb()
        for port in self.ports:
            if port.id == id:
                return port
        return None

    def get_ds(self):
        """
        Get all devices
        """
        self._refresh_usb()
        return self.devices.copy()

    def get_ps(self):
        """
        Get all ports
        """
        self._refresh_usb()
        return self.ports.copy()

    def dis_d(self, id):
        """
        Disable device by id
        """
        pass

    def act_d(self, id):
        """
        Activate device by id
        """
        pass

    def dis_p(self, id):
        """
        Disable port by id
        """
        pass

    def act_p(self, id):
        """
        Activate port by id
        """
        pass

    def refresh(self):
        """
        Refresh the backend state
        """
        pass

    def _mac_scan_usb(self):
        """
        Scan USB devices through libmac_io.dylib
        """
        # Count the number of devices
        count = self.mac_io.mac_scan_usb(None, 0)

        if count == 0:
            return []

        buffer = (MacUsbDevice * count)()
        filled = self.mac_io.mac_scan_usb(buffer, count)

        return list(buffer[:min(count, filled)])

    def _refresh_usb(self):
        raw_devices = self._mac_scan_usb()

        self.devices.clear()
        self.ports.clear()

        ports_by_id = {}

        for raw in raw_devices:
            # Create the port only once
            if raw.port_id not in ports_by_id:
                port = self.UsbPort(
                    id=raw.port_id,
                    name=raw.port_name.decode("utf-8", errors="replace"),
                    state=True,
                    type=self.PortType.USB,
                    gen="UNKNOWN",  # Temporary unknown value
                    speed=raw.usb_speed,
                )

                ports_by_id[raw.port_id] = port
                self.ports.append(port)

            device = self.Device(
                id=raw.id,
                name=raw.product_name.decode("utf-8", errors="replace"),
                port=ports_by_id[raw.port_id],
                vendor_id=raw.vendor_id,
                model_id=raw.product_id,

                # We haven't classified devices yet
                type=self.DeviceType.UNKNOWN,
            )

            self.devices.append(device)

    def _debug_usb_scan(self):
        devices = self._mac_scan_usb()

        for d in devices:
            print(
                f"""
ID:          {d.id}
Port ID:     {d.port_id}
Location:    0x{d.location_id:x}
USB Speed:   {d.usb_speed}

Vendor:      {d.vendor_name.decode("utf-8")}
Vendor ID:   0x{d.vendor_id:04x}

Product:     {d.product_name.decode("utf-8")}
Product ID:  0x{d.product_id:04x}

Port Name:   {d.port_name.decode("utf-8")}
Port Class:  {d.port_class.decode("utf-8")}
"""
            )

if __name__ == "__main__":
    backend = MacBackend()
    backend._debug_usb_scan()
