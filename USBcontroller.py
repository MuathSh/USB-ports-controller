import os
import sys
import pyudev
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeWidget, 
                             QTreeWidgetItem, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QColor, QBrush

class DeviceSignal(QObject):
    device_changed = pyqtSignal(str, dict)

class USBOnlyControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Ports Manager")
        self.resize(750, 480)

        self.context = pyudev.Context()
        self.signals = DeviceSignal()
        self.signals.device_changed.connect(self.handle_device_event)

        self.selected_sys_name = None
        self.selected_sys_path = None
        self.selected_driver = None

        self.init_ui()
        self.populate_tree()
        self.start_monitoring()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        self.status_label = QLabel("Select a device to monitor")
        self.status_label.setStyleSheet("padding: 8px; font-weight: bold; background-color: #1e1e2e; color: #cdd6f4; border-radius: 5px;")
        main_layout.addWidget(self.status_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Sys Name", "USB Name", "Device Type", "Status"])
        self.tree.setColumnWidth(0, 80)
        self.tree.setColumnWidth(1, 345)
        self.tree.setColumnWidth(2, 150)

        self.tree.itemClicked.connect(self.on_item_selected)
        main_layout.addWidget(self.tree)

        control_layout = QHBoxLayout()

        self.btn_disable = QPushButton("Unbind device")
        self.btn_disable.setStyleSheet("background-color: #981102; color: white; padding: 10px; font-weight: bold;")
        self.btn_disable.clicked.connect(self.disable_device_driver)
        control_layout.addWidget(self.btn_disable)

        self.btn_enable = QPushButton("Bind device")
        self.btn_enable.setStyleSheet("background-color: #03873a; color: white; padding: 10px; font-weight: bold;")
        self.btn_enable.clicked.connect(self.enable_device_driver)
        control_layout.addWidget(self.btn_enable)

        main_layout.addLayout(control_layout)
        self.setCentralWidget(central_widget)

    def get_friendly_usb_name(self, device):
        vendor = device.get('ID_VENDOR_FROM_DATABASE') or device.get('ID_VENDOR') or ''
        model = device.get('ID_MODEL_FROM_DATABASE') or device.get('ID_MODEL') or ''
        
        full_name = f"{vendor} {model}".strip()
        if full_name:
            return full_name
        return device.sys_name

    def populate_tree(self):
        self.tree.clear()

        for device in self.context.list_devices(subsystem='usb'):
            if device.device_type == 'usb_interface':
                continue
            if device.sys_name in ['3-1', '3-2']:
                dev_type = "External USB device" 
            else:
                dev_type = "Internal USB device"
            friendly_name = self.get_friendly_usb_name(device)

            status = "Active"
            if not device.driver:   
                status = "Unbound"

            item = QTreeWidgetItem(self.tree, [
                device.sys_name,
                friendly_name,
                dev_type,
                status
            ])

            if status == "Unbound":
                item.setForeground(3, QBrush(QColor("#E91A03")))
            else:
                item.setForeground(3, QBrush(QColor("#03c554")))

            item.setData(0, Qt.ItemDataRole.UserRole, device.sys_path)
            item.setData(0, Qt.ItemDataRole.UserRole + 1, device.driver or "usb")
            item.setData(0, Qt.ItemDataRole.UserRole + 2, device.sys_name)

        self.tree.expandAll()

    def on_item_selected(self, item, column):
        self.selected_sys_path = item.data(0, Qt.ItemDataRole.UserRole)
        self.selected_driver = item.data(0, Qt.ItemDataRole.UserRole + 1)
        self.selected_sys_name = item.data(0, Qt.ItemDataRole.UserRole + 2)
        
        if self.selected_sys_name:
            self.status_label.setText(f"Selected: {item.text(1)} [{self.selected_sys_name}]")

    def _write_sysfs(self, path, value):
        try:
            with open(path, 'w') as f:
                f.write(value)
            return True
        except PermissionError:
            QMessageBox.critical(self, "Permission Error", "Permission denied. need to run with sudo to modify USB state.")
            return False
        except Exception as e:
            QMessageBox.warning(self, "Warning", "Device already bound")
            return False

    def disable_device_driver(self):
        if not self.selected_sys_path or not self.selected_sys_name:
            QMessageBox.information(self, "Warning", "select a device first")
            return
        
        driver_path = f"{self.selected_sys_path}/driver/unbind"
        
        if os.path.exists(driver_path):
            if self._write_sysfs(driver_path, self.selected_sys_name):
                self.status_label.setText(f"USB Port has been unbound: {self.selected_sys_name}")
        else:
            QMessageBox.information(self, "Warning", "Device already unbound")

    def enable_device_driver(self):
        if not self.selected_sys_path or not self.selected_sys_name:
            QMessageBox.information(self, "Warning", "select a device first.")
            return
        
        driver_name = self.selected_driver or 'usb'
        driver_bind_path = f"/sys/bus/usb/drivers/{driver_name}/bind"
        
        if os.path.exists(driver_bind_path):
            if self._write_sysfs(driver_bind_path, self.selected_sys_name):
                self.status_label.setText(f"USB has been rebound: {self.selected_sys_name}")
        else:
            fallback_path = "/sys/bus/usb/drivers/usb/bind"
            if os.path.exists(fallback_path):
                self._write_sysfs(fallback_path, self.selected_sys_name)

    def start_monitoring(self):
        monitor = pyudev.Monitor.from_netlink(self.context)
        monitor.filter_by(subsystem='usb')
        
        def callback(device):
            dev_data = {'sys_name': device.sys_name}
            self.signals.device_changed.emit(device.action or "unknown", dev_data)

        self.observer = pyudev.MonitorObserver(monitor, callback=callback)
        self.observer.start()

    def handle_device_event(self, action, dev):
        if action in ['add', 'remove', 'bind', 'unbind']:
            self.populate_tree()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = USBOnlyControlApp()
    window.show()
    sys.exit(app.exec())