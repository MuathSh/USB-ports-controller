import ctypes
from ctypes import wintypes
from dataclasses import dataclass, field
from enum import Enum
from itertools import count

from backend import Backend


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.c_void_p),
    ]


class WindowsBackend(Backend):
    def __init__(self):
        self.setupapi = ctypes.WinDLL("setupapi.dll", use_last_error=True)
        self.cfgmgr = ctypes.WinDLL("cfgmgr32.dll", use_last_error=True)

        self.devices = []
        self.ports = []

        self.setupapi.SetupDiGetClassDevsW.argtypes = [
            ctypes.POINTER(GUID),
            wintypes.LPCWSTR,
            wintypes.HWND,
            wintypes.DWORD,
        ]
        self.setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE

        self.setupapi.SetupDiEnumDeviceInfo.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(SP_DEVINFO_DATA),
        ]
        self.setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL

        self.setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]
        self.setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL

        self.setupapi.SetupDiGetDeviceRegistryPropertyW.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(SP_DEVINFO_DATA),
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.setupapi.SetupDiGetDeviceRegistryPropertyW.restype = wintypes.BOOL

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

    def get_d(self, id):
        """Get specific stored device by id."""
        for device in self.devices:
            if device.id == id:
                return device
        return None

    def get_p(self, id):
        """Get specific stored port by id."""
        for port in self.ports:
            if port.id == id:
                return port
        return None

    def get_ds(self):
        """Get stored devices; scan results are not converted to Device yet."""
        return list(self.devices)

    def get_ps(self):
        """Get stored ports; physical port enumeration is not implemented yet."""
        return list(self.ports)

    def dis_d(self, id):
        """Disable device by id (not implemented yet)."""
        pass

    def act_d(self, id):
        """Activate device by id (not implemented yet)."""
        pass

    def dis_p(self, id):
        """Disable port by id (not implemented yet)."""
        pass

    def act_p(self, id):
        """Activate port by id (not implemented yet)."""
        pass

    def _scan_usb(self):
       
        handle = self.setupapi.SetupDiGetClassDevsW(None, "USB", None, 0x06)

        if handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())

        devices = []
        try:
            for index in count():
                entry = SP_DEVINFO_DATA()
                entry.cbSize = ctypes.sizeof(entry)

                if not self.setupapi.SetupDiEnumDeviceInfo(
                    handle, index, ctypes.byref(entry)
                ):
                    error = ctypes.get_last_error()
                    if error == 259:  # ERROR_NO_MORE_ITEMS
                        break
                    raise ctypes.WinError(error)

                name = "Unknown USB device"

                for property_id in (12, 0):
                    required = wintypes.DWORD()
                    success = self.setupapi.SetupDiGetDeviceRegistryPropertyW(
                        handle, ctypes.byref(entry), property_id,
                        None, None, 0, ctypes.byref(required),
                    )

                    if not success:
                        error = ctypes.get_last_error()
                        if error == 13:  
                            continue
                        if error != 122:  
                            raise ctypes.WinError(error)

                    buffer = ctypes.create_unicode_buffer(
                        required.value // ctypes.sizeof(ctypes.c_wchar) + 1
                    )

                    if not self.setupapi.SetupDiGetDeviceRegistryPropertyW(
                        handle, ctypes.byref(entry), property_id,
                        None, buffer, ctypes.sizeof(buffer), None,
                    ):
                        raise ctypes.WinError(ctypes.get_last_error())

                    if buffer.value:
                        name = buffer.value
                        break

                devices.append({"dev_inst": entry.DevInst, "name": name})
        finally:
            self.setupapi.SetupDiDestroyDeviceInfoList(handle)

        return devices

    def _get_properties(self, entry):
        pass

    def _get_registry_id(self, entry):
        pass

    def _get_children(self, entry):
        pass


if __name__ == "__main__":
    backend = WindowsBackend()
    devices = backend._scan_usb()

    print(f"USB devices found: {len(devices)}")
    for device in devices:
        print(f"USB device: {device['dev_inst']} | {device['name']}")

    if not devices:
        print("No USB devices found.")
