import ctypes
import re
import logging
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

        self.last_error = ""
        self.devices = []
        self.ports = []

        # Stable IDs for this backend instance, not persisted across runs.
        self._device_ids = {}    # InstanceId -> application ID
        self._instance_ids = {}  # application ID -> InstanceId

        # Same idea for ports (USB hubs / root hubs).
        self._port_ids = {}           # InstanceId -> port ID
        self._port_instance_ids = {}  # port ID -> InstanceId

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
        HUB = "hub"
        HID = "hid"
        COMPOSITE = "composite"
        AUDIO = "audio"
        BLUETOOTH = "bluetooth"
        UNKNOWN = "unknown"

    class PortType(Enum):
        USB = "usb"
        PCI = "pci"
        SATA = "sata"
        NET = "net"
        UNKNOWN = "unknown"

    @dataclass
    class Port:
        id: int
        name: str
        driver: str
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
        path: str
        children: list["Backend.Device"] = field(default_factory=list)

    def get_d(self, id, subsystem='usb'):

        for device in self.devices:
            if device.id == id:
                return device
        return None

    def get_p(self, id):

        for port in self.ports:
            if port.id == id:
                return port
        return None

    def get_ds(self, subsystem='usb'):

        results = self._scan_usb()
        devices = []

        for item in results:
            port = Backend.Port(
                id=-1,
                # UI compatibility: this object exposes DEVICE status;
                # it is not a mapped physical hub (id stays -1).
                name="USB device status",
                driver=item["service"],
                state=self.get_device_status(item["id"]) == "Active",
                type=Backend.PortType.USB,
            )
            device = Backend.Device(
                id=item["id"],
                name=item["name"],
                port=port,
                vendor_id=self._usb_id(item["instance_id"], "VID"),
                model_id=self._usb_id(item["instance_id"], "PID"),
                type=self._classify_device(item),
                path=item["instance_id"],
            )
            devices.append(device)

        self.devices = devices
        return list(self.devices)

    def get_ps(self):
        """Get ports. A port here is a USB hub / root hub node."""
        results = self._scan_usb()
        ports = []

        for item in results:
            instance_id = item["instance_id"]
            is_hub = (
                instance_id.startswith("USB\\ROOT_HUB")
                or "hub" in item["name"].lower()
            )
            if not is_hub:
                continue

            if instance_id not in self._port_ids:
                port_id = len(self._port_ids) + 1
                self._port_ids[instance_id] = port_id
                self._port_instance_ids[port_id] = instance_id

            ports.append(
                Backend.Port(
                    id=self._port_ids[instance_id],
                    name=item["name"],
                    driver=item["service"],
                    state=self.get_device_status(item["id"]) == "Active",
                    type=Backend.PortType.USB,
                )
            )

        self.ports = ports
        return list(self.ports)

    def refresh(self):
        """Refresh the backend state (devices and ports)."""
        self.get_ds()
        self.get_ps()

    def _resolve_device_target(self, target):
        """Accept the instance path sent by the UI, or a legacy numeric ID."""
        if isinstance(target, str):
            instance_id = target.upper()
            if instance_id in self._device_ids:
                return instance_id
            if target.isdecimal():
                target = int(target)
            else:
                raise ValueError(f"Unknown device path: {target}")
        instance_id = self._instance_ids.get(target)
        if instance_id is None:
            raise ValueError(f"Unknown device ID: {target}")
        return instance_id

    def _set_device_enabled(self, target, enabled):
        """Return the boolean expected by the existing UI click handlers."""
        self.last_error = ""
        try:
            instance_id = self._resolve_device_target(target)
            if enabled:
                self._enable_devnode(instance_id)
            else:
                self._disable_devnode(instance_id)
        except (OSError, RuntimeError, ValueError, TypeError) as error:
            self.last_error = str(error)
            logging.getLogger(__name__).error("%s", self.last_error)
            return False
        # The UI refreshes after True; get_ds reads Windows status afresh.
        return True

    def dis_d(self, id):
        """Disable by instance path (UI) or numeric ID."""
        return self._set_device_enabled(id, False)

    def act_d(self, id):
        """Enable by instance path (UI) or numeric ID."""
        return self._set_device_enabled(id, True)

    def dis_p(self, id):
        """Disable port by id (also disables everything under it)."""
        port = self.get_p(id)
        if port is None:
            raise ValueError(f"Port {id} not found")

        instance_id = self._port_instance_ids.get(id)
        if instance_id is None:
            raise ValueError(f"No instance ID for port {id}")

        self._disable_devnode(instance_id)
        port.state = False

    def act_p(self, id):
        """Activate (enable) port by id."""
        port = self.get_p(id)
        if port is None:
            raise ValueError(f"Port {id} not found")

        instance_id = self._port_instance_ids.get(id)
        if instance_id is None:
            raise ValueError(f"No instance ID for port {id}")

        self._enable_devnode(instance_id)
        port.state = True

    def get_device_status(self, id):
        """Read device status independently of the placeholder port mapping."""
        instance_id = self._instance_ids.get(id)
        if instance_id is None:
            raise ValueError(f"No instance ID for device {id}")
        self.cfgmgr.CM_Get_DevNode_Status.argtypes = [
            ctypes.POINTER(wintypes.ULONG),
            ctypes.POINTER(wintypes.ULONG),
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Get_DevNode_Status.restype = wintypes.ULONG
        status = wintypes.ULONG()
        problem = wintypes.ULONG()
        dev_inst = self._locate_devnode(instance_id)
        result = self.cfgmgr.CM_Get_DevNode_Status(
            ctypes.byref(status), ctypes.byref(problem), dev_inst, 0
        )
        if result != 0:
            raise RuntimeError(f"Cannot read device status: CONFIGRET={result}")
        if status.value & 0x00000400:  # DN_HAS_PROBLEM
            if problem.value == 22:  # CM_PROB_DISABLED
                return "Disabled"
            return f"Problem ({problem.value})"
        if status.value & 0x00000008:  # DN_STARTED
            return "Active"
        return "Not started"

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

                name = (self._read_text_property(handle, entry, 12)
                        or self._read_text_property(handle, entry, 0)
                        or "Unknown USB device")
                device_class = self._read_text_property(handle, entry, 7)
                service = self._read_text_property(handle, entry, 4)
                compatible_ids = self._read_text_property(handle, entry, 2)

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
                    "device_class": device_class,
                    "service": service,
                    "compatible_ids": compatible_ids,
                })
        finally:
            self.setupapi.SetupDiDestroyDeviceInfoList(handle)

        return devices

    def _locate_devnode(self, instance_id):
        """Find the DevInst handle for an instance ID."""
        self.cfgmgr.CM_Locate_DevNodeW.argtypes = [
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPCWSTR,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Locate_DevNodeW.restype = wintypes.ULONG

        dev_inst = wintypes.DWORD()
        result = self.cfgmgr.CM_Locate_DevNodeW(
            ctypes.byref(dev_inst), instance_id, 0  # CM_LOCATE_DEVNODE_NORMAL
        )
        if result != 0:
            raise RuntimeError(
                f"Cannot locate device node: CONFIGRET={result}"
            )
        return dev_inst.value

    def _enable_devnode(self, instance_id):
        """Enable a device node by its instance ID (requires Administrator)."""
        self._require_admin()
        self.cfgmgr.CM_Enable_DevNode.argtypes = [
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Enable_DevNode.restype = wintypes.ULONG

        dev_inst = self._locate_devnode(instance_id)
        result = self.cfgmgr.CM_Enable_DevNode(dev_inst, 0)
        if result != 0:
            self._raise_operation_error("enable", result)

    def _disable_devnode(self, instance_id):
        """Disable a device node by its instance ID (requires Administrator)."""
        self._require_admin()
        self.cfgmgr.CM_Disable_DevNode.argtypes = [
            wintypes.DWORD,
            wintypes.ULONG,
        ]
        self.cfgmgr.CM_Disable_DevNode.restype = wintypes.ULONG

        dev_inst = self._locate_devnode(instance_id)
        result = self.cfgmgr.CM_Disable_DevNode(dev_inst, 0)  # 0 = not persistent
        if result != 0:
            self._raise_operation_error("disable", result)

    @staticmethod
    def _require_admin():
        shell32 = ctypes.WinDLL("shell32.dll", use_last_error=True)
        shell32.IsUserAnAdmin.argtypes = []
        shell32.IsUserAnAdmin.restype = wintypes.BOOL
        if not shell32.IsUserAnAdmin():
            raise PermissionError(
                "Administrator rights are required. Close this program, open "
                "PowerShell using Run as administrator, then run python ui.py "
                "from your project folder."
            )

    @staticmethod
    def _raise_operation_error(operation, result):
        if result == 0x33:  # CR_ACCESS_DENIED (51 decimal)
            raise PermissionError(
                f"Cannot {operation} device: CR_ACCESS_DENIED (CONFIGRET=51). "
                "Windows denied access even though this process is elevated. "
                "Check device permissions or administrator policies."
            )
        raise RuntimeError(f"Cannot {operation} device: CONFIGRET={result} (0x{result:08X})")

    @staticmethod
    def _usb_id(instance_id, key):
        match = re.search(r"(?:^|[\\&])" + key + r"_([0-9A-F]{4})(?:[&\\]|$)", instance_id, re.I)
        return int(match.group(1), 16) if match else 0

    def _read_text_property(self, handle, entry, property_id):
        """Read REG_SZ or all strings in REG_MULTI_SZ, including compatible IDs."""
        required = wintypes.DWORD()
        registry_type = wintypes.DWORD()
        for _ in range(3):
            buffer = ctypes.create_unicode_buffer(
                max(1, (required.value + ctypes.sizeof(ctypes.c_wchar) - 1)
                    // ctypes.sizeof(ctypes.c_wchar))
            )
            success = self.setupapi.SetupDiGetDeviceRegistryPropertyW(
                handle, ctypes.byref(entry), property_id,
                ctypes.byref(registry_type), buffer, ctypes.sizeof(buffer),
                ctypes.byref(required),
            )
            if success:
                if registry_type.value not in (1, 7):  # REG_SZ, REG_MULTI_SZ
                    return ""
                return " ".join(part for part in buffer[:].split("\0") if part)
            error = ctypes.get_last_error()
            if error == 13:  # ERROR_INVALID_DATA: property not present
                return ""
            if error != 122:  # ERROR_INSUFFICIENT_BUFFER
                raise ctypes.WinError(error)
        raise RuntimeError(f"Device property {property_id} kept changing size")

    def _classify_device(self, item):
        """Classify from Windows metadata, not localized device names."""
        kind = self.DeviceType
        device_class = item.get("device_class", "").lower()
        service = item.get("service", "").lower()
        compatible = item.get("compatible_ids", "").lower()
        instance = item.get("instance_id", "").upper()
        classes = {
            "camera": kind.CAMERA, "image": kind.CAMERA,
            "keyboard": kind.KEYBOARD, "mouse": kind.MOUSE,
            "diskdrive": kind.STORAGE, "cdrom": kind.STORAGE,
            "net": kind.NETWORK, "bluetooth": kind.BLUETOOTH,
        }
        if device_class in classes:
            return classes[device_class]
        if service in ("kbdhid", "kbdclass"):
            return kind.KEYBOARD
        if service in ("mouhid", "mouclass"):
            return kind.MOUSE
        if service in ("usbstor", "uaspstor"):
            return kind.STORAGE
        if service == "usbvideo":
            return kind.CAMERA
        if service in ("usbaudio", "usbaudio2"):
            return kind.AUDIO
        if service in ("bthusb",):
            return kind.BLUETOOTH
        if service in ("usbhub", "usbhub3") or instance.startswith("USB\\ROOT_HUB"):
            return kind.HUB
        if service == "usbccgp":
            return kind.COMPOSITE
        if "class_03&subclass_01&prot_01" in compatible:
            return kind.KEYBOARD
        if "class_03&subclass_01&prot_02" in compatible:
            return kind.MOUSE
        usb_classes = {"01": kind.AUDIO, "03": kind.HID, "08": kind.STORAGE,
                       "09": kind.HUB, "0e": kind.CAMERA}
        for class_id in re.findall(r"usb\\class_([0-9a-f]{2})(?=[&\s]|$)", compatible):
            if class_id in usb_classes:
                return usb_classes[class_id]
        if device_class == "hidclass":
            return kind.HID
        return kind.UNKNOWN

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
        print(f"Port: {device.port.id} | {device.port.name} | {device.port.state}")
        print(f"Vendor ID: {device.vendor_id} | Model ID: {device.model_id}")
    if not devices:
        print("No USB devices found.")