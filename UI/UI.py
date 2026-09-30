import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QPushButton,
    QLabel,
    QFrame,
    QFormLayout


)
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

#custm button to use 
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

PROGRAM = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("usb.cntroler")
window.resize(1500, 750)

window.setStyleSheet("""
    QWidget {
        background-color: #f0fff;
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
        background-color: #lelele;
        color: #ffffff;
        padding: 4px;
        border: none;
    }
    QTreeWidget::item:selected {
    background-color: #04395e;
    color: #ffffff;
    border-radius: 4px;
    
    QLabel {
    border: none;
    background: transparent;
    color: #ffffff;
}
QLabel#detailsTitle {
    font-size: 16px;
    font-weight: bold;
    padding-bottom: 8px;
}
QFrame#detailsPanel {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
}
}

""")
active_btn = CustomButton("Active", "#2e6d7d", "#388e3c", "#1b5e20")
unbind_btn = CustomButton("Unbind", "#a81c1c", "#d32f2f", "#7f1313")

button_layout = QHBoxLayout()
button_layout.setSpacing(10) 
button_layout.addWidget(active_btn)
button_layout.addWidget(unbind_btn)

tree = QTreeWidget()
tree.setHeaderLabels(["Sys Name", "USB Name", "Device Type", "Status"])
tree.setColumnWidth(0, 80)
tree.setColumnWidth(1, 345)
tree.setColumnWidth(2, 150)
tree.setColumnWidth(3, 150)

devices = [
    ["usb1", "Kingston DataTraveler 3.0", "Storage", "Connected"],
    ["usb2", "Logitech G Pro Wireless", "Mouse", "Active"],
    ["usb3", "Razer BlackWidow V3", "Keyboard", "Active"],
    ["usb4", "SanDisk Ultra Flair", "Storage", "Disabled"],
]

device_details = {
    "usb1": {"vendor_id": "0951", "product_id": "1666", "serial": "KNG-83920", "speed": "USB 3.0 (5 Gbps)", "port": "Bus 1 Port 2"},
    "usb2": {"vendor_id": "046d", "product_id": "c547", "serial": "LGT-11245", "speed": "USB 2.0 (480 Mbps)", "port": "Bus 1 Port 3"},
    "usb3": {"vendor_id": "1532", "product_id": "025e", "serial": "RZR-55021", "speed": "USB 2.0 (480 Mbps)", "port": "Bus 1 Port 4"},
    "usb4": {"vendor_id": "0781", "product_id": "5581", "serial": "SDK-77310", "speed": "USB 3.0 (5 Gbps)", "port": "Bus 2 Port 1"},
}

for dev in devices:
    item = QTreeWidgetItem(dev)
    tree.addTopLevelItem(item)


left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

details_panel = QFrame()
details_panel.setObjectName("detailsPanel")   # lets the stylesheet target only this frame

details_layout = QVBoxLayout(details_panel)   # passing the parent sets the layout on the panel

details_title = QLabel("Select a device")
details_title.setObjectName("detailsTitle")
details_layout.addWidget(details_title)

form = QFormLayout()
lbl_Device = QLabel("-")
lbl_vendor = QLabel("-")
lbl_product = QLabel("-")
lbl_serial = QLabel("-")
lbl_speed = QLabel("-")
lbl_port = QLabel("-")

form.addRow("Device:", lbl_Device)
form.addRow("Vendor ID:", lbl_vendor)
form.addRow("Product ID:", lbl_product)
form.addRow("Serial:", lbl_serial)
form.addRow("Speed:", lbl_speed)
form.addRow("Port:", lbl_port)

details_layout.addLayout(form)
details_layout.addStretch()   

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch= 6)
main_layout.addWidget(details_panel, stretch=4)
def show_details(current, previous):
    if current is None:
        details_title.setText("Select a device")
        for lbl in (lbl_vendor, lbl_product, lbl_serial, lbl_speed, lbl_port):
            lbl.setText("-")
        return

    sys_name = current.text(0)                 # column 0 = "Sys Name"
    info = device_details.get(sys_name, {})    # {} if no extra data exists

    details_title.setText(current.text(1))     # column 1 = "USB Name"
    lbl_device.setText(info.get("Device ", "-"))
    lbl_vendor.setText(info.get("vendor_id", "-"))
    lbl_product.setText(info.get("product_id", "-"))
    lbl_serial.setText(info.get("serial", "-"))
    lbl_port.setText(info.get("port", "-"))

tree.currentItemChanged.connect(show_details)
tree.setCurrentItem(tree.topLevelItem(0))      # select the first row at startup
window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())