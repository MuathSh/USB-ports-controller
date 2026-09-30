import sys
import os
from collections import deque
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
    QFormLayout,
    QProgressBar
)
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF

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

# ----- Speed chart for network devices -----
class SpeedChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(100)
        self.download = deque(maxlen=60)
        self.upload = deque(maxlen=60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        painter.setPen(QPen(QColor("#3c3c3c")))
        for x in range(0, w, 20):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 20):
            painter.drawLine(0, y, w, y)

        top = max(list(self.download) + list(self.upload) + [1]) * 1.2
        for data, color in [(self.download, "#3b82f6"), (self.upload, "#22c55e")]:
            points = []
            for i, value in enumerate(data):
                x = w - (len(data) - i) * w / 60
                y = h - value / top * h
                points.append(QPointF(x, y))
            painter.setPen(QPen(QColor(color), 2))
            painter.drawPolyline(QPolygonF(points))

def read_file(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""

def size_text(num):
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"

def find_network():
    if not os.path.exists("/sys/class/net"):
        return None
    for name in sorted(os.listdir("/sys/class/net")):
        if name != "lo" and read_file(f"/sys/class/net/{name}/operstate") == "up":
            return name
    return None

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
    ["usb5", "Realtek Wi-Fi Adaptor", "Network", "Active"],
]

device_details = {
    "usb1": {"vendor_id": "0951", "product_id": "1666", "serial": "KNG-83920", "speed": "USB 3.0 (5 Gbps)", "port": "Bus 1 Port 2"},
    "usb2": {"vendor_id": "046d", "product_id": "c547", "serial": "LGT-11245", "speed": "USB 2.0 (480 Mbps)", "port": "Bus 1 Port 3"},
    "usb3": {"vendor_id": "1532", "product_id": "025e", "serial": "RZR-55021", "speed": "USB 2.0 (480 Mbps)", "port": "Bus 1 Port 4"},
    "usb4": {"vendor_id": "0781", "product_id": "5581", "serial": "SDK-77310", "speed": "USB 3.0 (5 Gbps)", "port": "Bus 2 Port 1"},
    "usb5": {"vendor_id": "0bda", "product_id": "b812", "serial": "RTL-40982", "speed": "USB 2.0 (480 Mbps)", "port": "Bus 1 Port 5"},
}

# ----- Extra info shown on double click -----
device_extra = {
    "usb1": {"Mount Point": "/media/usb", "File System": "vfat", "Capacity": "28.9 GB", "Used": "11.2 GB", "Free": "17.7 GB"},
    "usb2": {"Connection": "Wireless", "Polling Rate": "1000 Hz", "Battery": "82%"},
    "usb3": {"Connection": "Wired", "Polling Rate": "1000 Hz", "Battery": "-"},
    "usb4": {"Mount Point": "-", "File System": "-", "Capacity": "57.3 GB", "Used": "-", "Free": "-"},
    "usb5": {"Interface": find_network(), "Download": "-", "Upload": "-", "Received": "-", "Sent": "-"},
}

storage_used = {"usb1": 39}

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
lbl_device = QLabel("-")
lbl_vendor = QLabel("-")
lbl_product = QLabel("-")
lbl_serial = QLabel("-")
lbl_speed = QLabel("-")
lbl_port = QLabel("-")

form.addRow("Device:", lbl_device)
form.addRow("Vendor ID:", lbl_vendor)
form.addRow("Product ID:", lbl_product)
form.addRow("Serial:", lbl_serial)
form.addRow("Speed:", lbl_speed)
form.addRow("Port:", lbl_port)

details_layout.addLayout(form)

more_title = QLabel()
more_title.setObjectName("detailsTitle")
more_form = QFormLayout()

usage_bar = QProgressBar()
usage_bar.setTextVisible(False)
usage_bar.setStyleSheet("""
    QProgressBar { background-color: #3c3c3c; border: none; border-radius: 3px; max-height: 6px; }
    QProgressBar::chunk { background-color: #3b82f6; border-radius: 3px; }
""")

speed_label = QLabel()
speed_label.setStyleSheet("color: #4ade80;")
speed_chart = SpeedChart()

details_layout.addWidget(more_title)
details_layout.addLayout(more_form)
details_layout.addWidget(usage_bar)
details_layout.addWidget(speed_label)
details_layout.addWidget(speed_chart)

more_labels = {}
network = None
last_bytes = None
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

def hide_more(current=None, previous=None):
    global network
    network = None
    while more_form.rowCount() > 0:
        more_form.removeRow(0)
    more_title.hide()
    usage_bar.hide()
    speed_label.hide()
    speed_chart.hide()

def show_more(item):
    global network, last_bytes, more_labels
    hide_more()
    sys_name = item.text(0)
    dev_type = item.text(2)

    if dev_type in ["Mouse", "Keyboard"]:
        more_title.setText("Input")
    else:
        more_title.setText(dev_type)
    more_title.show()

    more_labels = {}
    for key, value in device_extra.get(sys_name, {}).items():
        lbl = QLabel(str(value))
        more_form.addRow(key + ":", lbl)
        more_labels[key] = lbl

    if sys_name in storage_used:
        usage_bar.setValue(storage_used[sys_name])
        usage_bar.show()

    if dev_type == "Network":
        network = device_extra[sys_name]["Interface"]
        last_bytes = None
        speed_chart.download.clear()
        speed_chart.upload.clear()
        speed_label.setText("")
        speed_label.show()
        speed_chart.show()

def update_speed():
    global last_bytes
    if network is None:
        return
    folder = f"/sys/class/net/{network}/statistics/"
    received = int(read_file(folder + "rx_bytes") or 0)
    sent = int(read_file(folder + "tx_bytes") or 0)
    more_labels["Received"].setText(size_text(received))
    more_labels["Sent"].setText(size_text(sent))
    if last_bytes is not None:
        download = received - last_bytes[0]
        upload = sent - last_bytes[1]
        more_labels["Download"].setText(size_text(download) + "/s")
        more_labels["Upload"].setText(size_text(upload) + "/s")
        speed_label.setText(f"↓ {size_text(download)}/s   ↑ {size_text(upload)}/s")
        speed_chart.download.append(download)
        speed_chart.upload.append(upload)
        speed_chart.update()
    last_bytes = (received, sent)

tree.currentItemChanged.connect(hide_more)
tree.itemDoubleClicked.connect(show_more)
hide_more()

timer = QTimer()
timer.timeout.connect(update_speed)
timer.start(1000)
window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())