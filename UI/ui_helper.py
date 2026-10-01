from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QLabel
from backend import Backend
from PyQt6.QtCore import Qt
import backend
import UI
from UI import more_form, more_title, tree

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


def refresh(tree):
    devices_list = backend.get_ds()
    get_tree(tree,devices_list)

def rm_more(current=None, previous=None):
    while more_form.rowCount() > 0:
        more_form.removeRow(0)
    more_title.hide()

#show info
def rm_more(item):
    rm_more()

    
    dev_id = item.data(0, Qt.ItemDataRole.UserRole)
    dev = backend.get_d(dev_id) if dev_id is not None else None
    if not dev:
        return

    
    type_str = dev.type.value if hasattr(dev.type, 'value') else str(dev.type)
    more_title.setText(type_str)
    more_title.show()

    
    more_form.addRow("Device ID:", QLabel(str(dev.id)))
    more_form.addRow("Device Name:", QLabel(str(dev.name)))
    more_form.addRow("Vendor ID:", QLabel(str(dev.vendor_id)))
    more_form.addRow("Model ID:", QLabel(str(dev.model_id)))
    more_form.addRow("Port State:", QLabel("Active" if dev.port.state else "Unbind"))
    more_form.addRow("Children Count:", QLabel(str(len(dev.children))))


#active
def on_active():
    item = tree.currentItem()
    if item:
        dev_id = item.data(0, Qt.ItemDataRole.UserRole)
        backend.act_d(dev_id)
        refresh(tree)
#unbind
def on_unbind():
    item = tree.currentItem()
    if item:
        dev_id = item.data(0, Qt.ItemDataRole.UserRole)
        backend.dis_d(dev_id)
        refresh(tree)