from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QTreeWidgetItem
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

