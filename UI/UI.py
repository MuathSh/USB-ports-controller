import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QTreeWidget, 
    QPushButton,
    QHeaderView,
    QLabel,
    QFormLayout,
    QFrame,
    QTreeWidgetItem
)
from PyQt6.QtCore import Qt

from linux_backend import LinuxBackend

def get_tree(tree: QTreeWidget, devices: list):
    tree.clear()
    for dev in devices:
        type_str = dev.type.value if hasattr(dev.type, 'value') else str(dev.type)
        status_str = "Active" if dev.port.state else "Unbind"

        item = QTreeWidgetItem([
            f"usb{dev.id}",
            str(dev.name),
            type_str,
            status_str
        ])
        
        item.setData(0, Qt.ItemDataRole.UserRole, dev)
        tree.addTopLevelItem(item)

def clear_details(more_form: QFormLayout, more_title: QLabel):
    while more_form.rowCount() > 0:
        more_form.removeRow(0)

def show_details(item, more_form: QFormLayout, more_title: QLabel):
    clear_details(more_form, more_title)
    
    if not item:
        more_title.setText("Device Details")
        return

    dev = item.data(0, Qt.ItemDataRole.UserRole)
    if not dev:
        more_title.setText("Device Details")
        return

    type_str = dev.type.value if hasattr(dev.type, 'value') else str(dev.type)
    more_title.setText(f"Device Details: {type_str}")

    more_form.addRow("Device ID:", QLabel(str(dev.id)))
    more_form.addRow("Device Name:", QLabel(str(dev.name)))
    more_form.addRow("Vendor ID:", QLabel(str(dev.vendor_id)))
    more_form.addRow("Model ID:", QLabel(str(dev.model_id)))
    more_form.addRow("Port State:", QLabel("Active" if dev.port.state else "Unbind"))
    more_form.addRow("Path:", QLabel(str(dev.path)))
    more_form.addRow("Children Count:", QLabel(str(len(dev.children))))

backend_obj = LinuxBackend()

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("usb.cntroler")
window.setMinimumSize(1500, 750)

window.setStyleSheet("""
    QWidget {
        background-color: #1e1e1e;
        border: 2px solid #3c3c3c;
        border-radius: 12px;
    }
    QTreeWidget {
        background-color: #252526;
        border: 1px solid #3c3c3c;
        border-radius: 8px;
        color: #ffffff;
    }
    QHeaderView::section {
        background-color: #333333;
        color: #ffffff;
        padding: 4px;
        border: none;
    }
    QLabel {
        color: #ffffff;
    }
""")

class CustomButton(QPushButton):
    def __init__(self, text, bg_color, hover_color, pressed_color):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ 
                background-color: {hover_color}; 
            }}
            QPushButton:pressed {{ 
                background-color: {pressed_color}; 
            }}
        """)

active_btn = CustomButton("Active", "#2e7d32", "#388e3c", "#1b5e20")
unbind_btn = CustomButton("Unbind", "#a81c1c", "#d32f2f", "#7f1313")

button_layout = QHBoxLayout()
button_layout.setSpacing(10) 
button_layout.addWidget(active_btn)
button_layout.addWidget(unbind_btn)

tree = QTreeWidget()
tree.setHeaderLabels(["Sys Name", "USB Name", "Device Type", "Status"])
tree.setRootIsDecorated(False)
tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

header = tree.header()
header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
tree.setColumnWidth(0, 90)
header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
tree.setColumnWidth(2, 130)
header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
tree.setColumnWidth(3, 100)

left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

details_panel = QFrame()
details_panel.setObjectName("detailsPanel")
details_panel.setStyleSheet("QFrame#detailsPanel { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 10px; }")

details_layout = QVBoxLayout(details_panel)

more_title = QLabel("Device Details")
more_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")

more_form = QFormLayout()

details_layout.addWidget(more_title)
details_layout.addLayout(more_form)
details_layout.addStretch()

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch=6)
main_layout.addWidget(details_panel, stretch=4)

window.setLayout(main_layout)

devices_list = backend_obj.get_ds()
get_tree(tree, devices_list)

tree.currentItemChanged.connect(lambda current, previous: show_details(current, more_form, more_title))

window.show()
sys.exit(app.exec())