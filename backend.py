from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class Backend(ABC):

    class DeviceType(Enum):
        CAMERA = "camera"
        KEYBOARD = "keyboard"
        MOUSE = "mouse"
        STORAGE = "storage"
        NETWORK = "network"
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
        path: str
        children: list["Backend.Device"] = field(default_factory=list)

    @abstractmethod
    def get_d(self, id, subsystem='usb'):
        """
        Get specific device by id
        """
        pass

    @abstractmethod
    def get_p(self, id):
        """
        Get specific port by id
        """
        pass

    @abstractmethod
    def get_ds(self, subsystem='usb'):
        """
        Get all devices
        """
        pass

    @abstractmethod
    def get_ps(self):
        """
        Get all ports
        """
        pass

    @abstractmethod
    def dis_d(self, id):
        """
        Disable device by id
        """
        pass

    @abstractmethod
    def act_d(self, id):
        """
        Activate device by id
        """
        pass

    @abstractmethod
    def dis_p(self, id):
        """
        Disable port by id
        """
        pass

    @abstractmethod
    def act_p(self, id):
        """
        Activate port by id
        """
        pass

    @abstractmethod
    def refresh(self):
        """
        Refresh the backend state
        """
        pass
