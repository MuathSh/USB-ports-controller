import pyudev
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum

import backend
from backend import Backend


class LinuxBackend(Backend):

    def __init__(self):
        self.Context = pyudev.Context()

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
        BLUETOOTH = "bluetooth"
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
        path: str
        children: list["Backend.Device"] = field(default_factory=list)

    def create_device(self, id):
        device = None
        try:
            device = pyudev.Devices.from_name(self.Context, subsystem='usb', sys_name=id)
        except pyudev._errors.DeviceNotFoundByNameError:
            try:
                device = pyudev.Devices.from_path(self.Context, id)
            except pyudev._errors.DeviceNotFoundAtPathError:
                print("Device not found")
                return None

        # Get vendor+model combined name.
        vendor = device.get('ID_VENDOR_FROM_DATABASE') or device.get('ID_VENDOR') or ''
        model = device.get('ID_MODEL_FROM_DATABASE') or device.get('ID_MODEL') or ''
        full_name = f"{vendor} {model}".strip()

        # Convert subsystem name into lower and compare it.
        subsystem_lower = str(device.subsystem).lower()
        try:
            port_type = Backend.PortType(subsystem_lower)
        except ValueError:
            port_type = Backend.PortType.UNKNOWN

        return Backend.Device(
            id=int(device.sys_number),
            name=full_name,
            port=Backend.Port(
                device.get('ID_PATH'),
                device.get('ID_USB_VENDOR'),
                False if not device.driver else True,
                port_type
            ),
            vendor_id=device.get('ID_USB_VENDOR_ID'),
            model_id=device.get('ID_MODEL_ID'),
            type=Backend.DeviceType.UNKNOWN,
            path=device.sys_path,
            children=[self.create_device(child.sys_path) for child in device.children]
        )

    def get_d(self, id):
        """
        Get specific device by id
        """
        return self.create_device(id)


    def get_p(self, id):
        """
        Get specific port by id
        """
        pass

    def get_ds(self):
        """
        Get all devices
        """
        pass

    def get_ps(self):
        """
        Get all ports
        """
        pass

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

    def _scan_usb(self):
        pass

    def _get_properties(self, entry):
        pass

    def _get_registry_id(self, entry):
        pass

    def _get_children(self, entry):
        pass


lcx = LinuxBackend()
print(lcx.get_d('usb3'))
