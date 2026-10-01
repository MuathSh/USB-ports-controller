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

        # Stable IDs for this backend instance, not persisted across runs.
        self._device_ids = {}    # InstanceId -> application ID
        self._instance_ids = {}  # application ID -> InstanceId

        self.cfgmgr.CM_Get_Device_ID_Size.argtypes = [
            ctypes.POINTER(wintypes.ULONG),
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Get_Device_ID_Size.restype = wintypes.ULONG

        self.cfgmgr.CM_Get_Device_IDW.argtypes = [
            wintypes.DWORD,
            wintypes.LPWSTR,
            wintypes.ULONG,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Get_Device_IDW.restype = wintypes.ULONG

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
       
        for device in self.devices:
            if device.id == id:
                return device
        return None

    def get_p(self, id):
    
        for port in self.ports:
            if port.id == id:
                return port
        return None

    def get_ds(self):
    
        results = self._scan_usb()
        devices = []

        for item in results:
            port = Backend.Port(
                id=-1,
                name="Unmapped port",
                state=False,
                type=Backend.PortType.UNKNOWN,
            )
            device = Backend.Device(
                id=item["id"],
                name=item["name"],
                port=port,
                vendor_id=0,
                model_id=0,
                type=Backend.DeviceType.UNKNOWN,
            )
            devices.append(device)

        self.devices = devices
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
                    if error == 259:
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

                instance_id = self._get_registry_id(entry).upper()

                if instance_id not in self._device_ids:
                    device_id = len(self._device_ids) + 1
                    self._device_ids[instance_id] = device_id
                    self._instance_ids[device_id] = instance_id

                devices.append({
                    "id": self._device_ids[instance_id],
                    "instance_id": instance_id,
                    "dev_inst": entry.DevInst,
                    "name": name,
                })
        finally:
            self.setupapi.SetupDiDestroyDeviceInfoList(handle)

        return devices

    def _get_properties(self, entry):
        pass

    def _get_registry_id(self, entry):
        """Read the Windows device instance ID from a device information entry."""
        size = wintypes.ULONG()
        result = self.cfgmgr.CM_Get_Device_ID_Size(
            ctypes.byref(size), entry.DevInst, 0
        )
        if result != 0:
            raise RuntimeError(
                f"Cannot read device ID size: CONFIGRET={result}"
            )

        buffer = ctypes.create_unicode_buffer(size.value + 1)
        result = self.cfgmgr.CM_Get_Device_IDW(
            entry.DevInst, buffer, len(buffer), 0
        )
        if result != 0:
            raise RuntimeError(
                f"Cannot read device ID: CONFIGRET={result}"
            )

        return buffer.value

    def _get_children(self, entry):
        pass


if __name__ == "__main__":
    backend = WindowsBackend()
    devices = backend.get_ds()

    print(f"USB devices found: {len(devices)}")
    for device in devices:
        print(f"USB device: {device.id} | {device.name}")
        print(f"Instance ID: {backend._instance_ids[device.id]}")
        
    if not devices:
        print("No USB devices found.")
