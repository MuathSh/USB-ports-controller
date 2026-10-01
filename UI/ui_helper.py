from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItem, QLabel
from backend import Backend
from PyQt6.QtCore import Qt
import backend
import UI

#get devicec and add to tree
def get_tree(tree: QTreeWidget, devices: list[Backend.Device]):

    tree.clear()

    for dev in devices:
        type_str = dev.type.value if hasattr(dev.type, 'value',) else str(dev.type)
        
        status_str = "Active" if dev.port.state else "Uinbind"

        item = QTreeWidgetItem([
            f"usb{dev.id}",
            dev.name,
            type_str,
            status_str
         ])
        
        item.setData(0,Qt.ItemDataRole.UserRole, dev.id)
        tree.addTopLevelItem(item)

#refresh tree
def refresh(tree):
    devices_list = backend.get_ds()
    get_tree(tree,devices_list)

def hide_more():
    pass

def show_more(item):
    hide_more()
    
    dev_id = item.data(0, Qt.ItemDataRole.UserRole)
    dev = backend.get_d(dev_id) if dev_id is not None else None
    if not dev:
        return

    more_title.setText(str(dev.type))
    more_title.show()

    more_form.addRow("Device ID:", QLabel(str(dev.id)))
    more_form.addRow("Device Name:", QLabel(str(dev.name)))
    more_form.addRow("Vendor ID:", QLabel(str(dev.vendor_id)))
    more_form.addRow("Model ID:", QLabel(str(dev.model_id)))
    more_form.addRow("Port:", QLabel(str(dev.port)))
    more_form.addRow("Children Count:", QLabel(str(len(dev.children))))

