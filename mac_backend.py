from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from backend import Backend


class MacBackend(Backend):

    def __init__(self):
        self.devices = []
        self.ports = []

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
        pass

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