import pyudev
import sys
import json
import os
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from pyudev import Device

import backend
from backend import Backend


class LinuxBackend(Backend):

    def __init__(self,cache_file="driver_cache.json"):
        self.Context = pyudev.Context()
        self.cache_file = cache_file

    def _load_cache(self):
        """Load the driver cache from the JSON file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self, cache_data):
        """Save the driver cache to the JSON file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=4)
        except Exception as e:
            print(f"Failed to save driver cache to file: {e}")

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
        type: str
        children: list["Backend.Device"] = field(default_factory=list)

    def _pyudev_get_device(self,id,subsystem='usb'):
        try:
            return pyudev.Devices.from_name(self.Context, subsystem=subsystem, sys_name=id)
        except pyudev._errors.DeviceNotFoundByNameError:
            try:
                return pyudev.Devices.from_path(self.Context, id)
            except pyudev._errors.DeviceNotFoundAtPathError:
                print("Device not found")
                return None


    def create_device(self, id=None, device=None, subsystem='usb'):
        if device is None and id is not None:
            device = self._pyudev_get_device(id,subsystem)

        # Get vendor+model combined name.
        vendor = device.get('ID_VENDOR_FROM_DATABASE') or device.get('ID_VENDOR') or ''
        model = device.get('ID_MODEL_FROM_DATABASE') or device.get('ID_MODEL') or ''
        full_name = f"{vendor} {model}".strip()

        # Convert subsystem name into lower and compare it.
        bus_id_lower = str(device.get('ID_BUS')).lower() or str(device.subsystem).lower()
        try:
            port_type = Backend.PortType(bus_id_lower)
        except ValueError:
            port_type = Backend.PortType.UNKNOWN

        # Universal vendor and model ID lookups
        vendor_id = device.get('ID_VENDOR_ID') or device.get('PCI_VENDOR_ID') or ''
        model_id = device.get('ID_MODEL_ID') or device.get('PCI_DEVICE_ID') or ''

        # Detect device type
        if device.get('ID_INPUT_KEYBOARD') == '1':
            device_type = Backend.DeviceType.KEYBOARD

        elif device.get('ID_INPUT_MOUSE') == '1':
            device_type = Backend.DeviceType.MOUSE

        elif device.subsystem == 'net':
            device_type = Backend.DeviceType.NETWORK

        elif device.subsystem == 'block':
            device_type = Backend.DeviceType.STORAGE

        elif device.subsystem == 'video4linux':
            device_type = Backend.DeviceType.CAMERA

        else:
            device_type = Backend.DeviceType.UNKNOWN

        driver = device.driver or device.get('ID_NET_DRIVER')
        return Backend.Device(
            id=device.sys_name,
            name=full_name,
            port=Backend.Port(
                id=device.get('ID_PATH'),
                name=device.subsystem,
                driver=driver,
                state=bool(device.driver),
                type=port_type
            ),
            vendor_id=vendor_id,
            model_id=model_id,
            path=device.sys_path,
            type=device.get('DEVTYPE'),
            children=[self.create_device(child.sys_path) for child in device.children]
        )

    def create_port(self,id=None, port=None, subsystem='usb'):
        if port is None and id is not None:
            port = self._pyudev_get_device(id,subsystem)

        # Convert subsystem name into lower and compare it.
        subsystem_lower = str(port.subsystem).lower()
        try:
            port_type = Backend.PortType(subsystem_lower)
        except ValueError:
            port_type = Backend.PortType.UNKNOWN

        return Backend.Port(
            port.get('ID_PATH'),
            port.get('ID_USB_VENDOR'),
            False if not port.driver else True,
            port_type
        )
    def get_d(self, id, subsystem='usb'):
        """ Get specific device by id """
        return self.create_device(id, subsystem=subsystem)


    def get_p(self, id):
        """ Get specific port by id """
        return self.create_port(id)

    def get_ds(self,subsystem='usb'):
        """ Get all devices """
        devices = []
        for device in self.Context.list_devices(subsystem=subsystem):
            devices.append(self.create_device(device=device))
        return devices


    def get_ps(self):
        """ Get all ports """
        ports = []
        for port in self.Context.list_devices(subsystem='usb'):
            ports.append(self.create_port(port=port))
        return ports

    def dis_d(self, id):
        """ Disable device by id """
        device = self._pyudev_get_device(id)
        # if not device:
        #     print(f"Device not found: {device_id}")
        #     return False

        sys_path = str(device.get('ID_BUS')).lower() or str(device.subsystem).lower()
        bus_name = device.sys_name
        driver = device.driver

        if not driver:
            print(f"No active driver found to unbind for {bus_name}")
            return False

        bus_type = 'pci' if 'pci' in sys_path else 'usb' if 'usb' in sys_path else None
        if not bus_type:
            print(f"Unsupported bus type for path: {sys_path}")
            return False

        # 1. Save mapping to file cache BEFORE unbinding wipes the driver property
        cache = self._load_cache()
        cache[bus_name] = driver
        self._save_cache(cache)

        # 2. Perform the unbind operation
        unbind_path = f"/sys/bus/{bus_type}/drivers/{driver}/unbind"
        try:
            with open(unbind_path, 'w') as f:
                f.write(bus_name)
            print(f"Successfully unbound driver '{driver}' from {bus_name} (Persisted to {self.cache_file})")
            return True
        except PermissionError:
            print("Permission denied: Root privileges (sudo) required.")
            return False
        except Exception as e:
            print(f"Failed to unbind {bus_name}: {e}")
            return False


    def act_d(self, id):
        """
        Activate device by id
        """
        device = self._pyudev_get_device(id)
        # if not device:
        #     print(f"Device not found: {device_id}")
        #     return False

        sys_path = str(device.get('ID_BUS')).lower() or str(device.subsystem).lower()
        bus_name = device.sys_name

        # Check active properties first, fall back to file cache if empty
        driver = device.driver
        if not driver:
            cache = self._load_cache()
            driver = cache.get(bus_name)

        bus_type = 'pci' if 'pci' in sys_path else 'usb' if 'usb' in sys_path else None
        if not bus_type:
            print(f"Unsupported bus type for path: {sys_path}")
            return False

        if not driver:
            if bus_type == 'pci':
                probe_path = "/sys/bus/pci/drivers_probe"
                with open(probe_path, 'w') as f:
                    f.write(bus_name)
                print(f"Successfully probed and bound PCI device {bus_name}")
                return True
            else:
                print(f"Cannot bind {bus_name}: Driver unknown and not found in storage cache.")
                return False

        bind_path = f"/sys/bus/{bus_type}/drivers/{driver}/bind"
        try:
            with open(bind_path, 'w') as f:
                f.write(bus_name)
            print(f"Successfully bound driver '{driver}' to {bus_name}")

            # Clean up the cache entry once successfully rebound
            cache = self._load_cache()
            if bus_name in cache:
                del cache[bus_name]
                self._save_cache(cache)

            return True
        except PermissionError:
            print("Permission denied: Root privileges (sudo) required.")
            return False
        except Exception as e:
            print(f"Failed to bind {bus_name}: {e}")
            return False

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

    # def _scan_usb(self):
    #     pass
    #
    # def _get_properties(self, entry):
    #     pass
    #
    # def _get_registry_id(self, entry):
    #     pass
    #
    # def _get_children(self, entry):
    #     pass


# lcx = LinuxBackend()
# for d in lcx.get_ds():
#     print(d)
# for n in lcx.get_ds(subsystem='net'):
#     print(n)
# lcx.act_d('/sys/devices/pci0000:00/0000:00:14.0/usb3/3-9')
# print(lcx.get_d(id='usb3'))
