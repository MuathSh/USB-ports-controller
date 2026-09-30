import sys
import os
import shutil
from collections import deque
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QPushButton,
    QHeaderView,
    QLabel,
    QFrame,
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


class SpeedChart(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(80)
        self.download = deque(maxlen=60)
        self.upload = deque(maxlen=60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        painter.setPen(QPen(QColor("#2a2a2f")))
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


devices = [
    ["usb1", "Kingston DataTraveler 3.0", "Storage", "Connected"],
    ["usb2", "Logitech G Pro Wireless", "Mouse", "Active"],
    ["usb3", "Razer BlackWidow V3", "Keyboard", "Active"],
    ["usb4", "SanDisk Ultra Flair", "Storage", "Disabled"],
    ["usb5", "Realtek RTL8812BU Wi-Fi Adapter", "Network", "Active"],
]

for dev in devices:
    item = QTreeWidgetItem(dev)
    tree.addTopLevelItem(item)

device_info = {
    "usb1": {"sys": "usb1", "name": "Kingston DataTraveler 3.0", "type": "Storage", "status": "Connected",
     "vendor": "0x0951", "product": "0x1666", "driver": "usb-storage", "speed": "5 Gbps",
     "power": "504mA", "port": "2-1", "mount": "/media/usb",
     "info": {"Mount Point": "/media/usb", "File System": "vfat", "Capacity": "28.9 GB",
              "Used": "11.2 GB", "Free": "17.7 GB"}, "used_percent": 39},
    "usb2": {"sys": "usb2", "name": "Logitech G Pro Wireless", "type": "Mouse", "status": "Active",
     "vendor": "0x046d", "product": "0xc539", "driver": "usbhid", "speed": "12 Mbps",
     "power": "98mA", "port": "1-2",
     "info": {"Connection": "Wireless", "Polling Rate": "1000 Hz", "Battery": "82%"}},
    "usb3": {"sys": "usb3", "name": "Razer BlackWidow V3", "type": "Keyboard", "status": "Active",
     "vendor": "0x1532", "product": "0x024e", "driver": "usbhid", "speed": "12 Mbps",
     "power": "500mA", "port": "1-3",
     "info": {"Connection": "Wired", "Polling Rate": "1000 Hz", "Battery": "-"}},
    "usb4": {"sys": "usb4", "name": "SanDisk Ultra Flair", "type": "Storage", "status": "Disabled",
     "vendor": "0x0781", "product": "0x5591", "driver": "-", "speed": "5 Gbps",
     "power": "896mA", "port": "2-2",
     "info": {"Mount Point": "-", "File System": "-", "Capacity": "57.3 GB", "Used": "-", "Free": "-"}},
    "usb5": {"sys": "usb5", "name": "Realtek RTL8812BU Wi-Fi Adapter", "type": "Network", "status": "Active",
     "vendor": "0x0bda", "product": "0xb812", "driver": "rtw88_8822bu", "speed": "480 Mbps",
     "power": "500mA", "port": "1-4", "interface": find_network()},
}

inspector = QFrame()
inspector.setObjectName("inspector")
inspector.setStyleSheet("""
    QWidget {
        background: transparent;
        border: none;
        color: #e4e4e7;
        font-size: 13px;
    }
    #inspector {
        background-color: #1c1c1f;
        border: 1px solid #2a2a2f;
        border-radius: 8px;
    }
    #box {
        background-color: #18181b;
        border: 1px solid #2a2a2f;
        border-radius: 6px;
    }
    #row {
        border-bottom: 1px solid #26262b;
    }
    #icon {
        background-color: #111827;
        border: 1px solid #1e3a8a;
        border-radius: 6px;
        font-size: 22px;
    }
    #small_title {
        color: #9ca3af;
        font-size: 11px;
        font-weight: bold;
    }
    #key {
        color: #9ca3af;
    }
    #value {
        font-family: monospace;
    }
    #live {
        color: #4ade80;
        font-family: monospace;
        font-size: 11px;
    }
    #badge {
        color: #60a5fa;
        background-color: #172554;
        border: 1px solid #3b82f6;
        border-radius: 3px;
        padding: 1px 6px;
        font-family: monospace;
        font-size: 11px;
    }
    QProgressBar {
        background-color: #27272a;
        border-radius: 3px;
        max-height: 6px;
    }
    QProgressBar::chunk {
        background-color: #3b82f6;
        border-radius: 3px;
    }
""")

title = QLabel("☰  Device Inspector")
title.setStyleSheet("font-weight: bold; font-size: 14px;")
badge = QLabel()
badge.setObjectName("badge")
close_btn = QPushButton("✕")
close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
close_btn.clicked.connect(inspector.hide)

title_layout = QHBoxLayout()
title_layout.addWidget(title)
title_layout.addStretch()
title_layout.addWidget(badge)
title_layout.addWidget(close_btn)

card = QFrame()
card.setObjectName("box")
icon_label = QLabel()
icon_label.setObjectName("icon")
icon_label.setFixedSize(46, 46)
icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
name_label = QLabel()
name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
type_label = QLabel()
type_label.setStyleSheet("color: #6b7280; font-size: 11px;")
card_text = QVBoxLayout()
card_text.addWidget(name_label)
card_text.addWidget(type_label)
card_layout = QHBoxLayout(card)
card_layout.setContentsMargins(12, 12, 12, 12)
card_layout.addWidget(icon_label)
card_layout.addLayout(card_text, stretch=1)

hardware_title = QLabel("HARDWARE PROPERTIES")
hardware_title.setObjectName("small_title")
hardware_box = QFrame()
hardware_box.setObjectName("box")
hardware_layout = QVBoxLayout(hardware_box)
hardware_layout.setContentsMargins(0, 0, 0, 0)
hardware_layout.setSpacing(0)

extra_title = QLabel()
extra_title.setObjectName("small_title")
extra_box = QFrame()
extra_box.setObjectName("box")
extra_layout = QVBoxLayout(extra_box)
extra_layout.setContentsMargins(0, 0, 0, 0)
extra_layout.setSpacing(0)
usage_bar = QProgressBar()
usage_bar.setTextVisible(False)

chart_title = QLabel("<span style='color:#3b82f6'>●</span> DOWNLOAD  <span style='color:#22c55e'>●</span> UPLOAD")
chart_title.setObjectName("small_title")
live_label = QLabel()
live_label.setObjectName("live")
chart_title_layout = QHBoxLayout()
chart_title_layout.addWidget(chart_title)
chart_title_layout.addStretch()
chart_title_layout.addWidget(live_label)
chart_box = QFrame()
chart_box.setObjectName("box")
chart_layout = QVBoxLayout(chart_box)
chart = SpeedChart()
chart_layout.addWidget(chart)

inspector_layout = QVBoxLayout(inspector)
inspector_layout.setContentsMargins(14, 14, 14, 14)
inspector_layout.setSpacing(10)
inspector_layout.addLayout(title_layout)
inspector_layout.addWidget(card)
inspector_layout.addWidget(hardware_title)
inspector_layout.addWidget(hardware_box)
inspector_layout.addWidget(extra_title)
inspector_layout.addWidget(extra_box)
inspector_layout.addWidget(usage_bar)
inspector_layout.addLayout(chart_title_layout)
inspector_layout.addWidget(chart_box)
inspector_layout.addStretch()
inspector.hide()

extra_labels = {}
current_device = None
last_bytes = None


def fill_box(layout, data):
    while layout.count():
        layout.takeAt(0).widget().deleteLater()
    labels = {}
    for key, value in data.items():
        row = QFrame()
        row.setObjectName("row")
        row.setFixedHeight(30)
        key_label = QLabel(key + ":")
        key_label.setObjectName("key")
        value_label = QLabel(str(value))
        value_label.setObjectName("value")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 0, 10, 0)
        row_layout.addWidget(key_label)
        row_layout.addStretch()
        row_layout.addWidget(value_label)
        layout.addWidget(row)
        labels[key] = value_label
    return labels


def show_card(dev):
    if dev["type"] == "Storage":
        icon_label.setText("💾")
    elif dev["type"] == "Mouse":
        icon_label.setText("🖱")
    elif dev["type"] == "Keyboard":
        icon_label.setText("⌨")
    elif dev["type"] == "Network":
        icon_label.setText("📶")
    else:
        icon_label.setText("🔌")
    name_label.setText(dev["name"])
    type_label.setText(dev["type"] + " · " + dev["status"])
    badge.setText(dev["sys"])


def show_hardware(item):
    global current_device
    dev = device_info[item.text(0)]
    current_device = None
    show_card(dev)

    fill_box(hardware_layout, {
        "Vendor ID": dev["vendor"],
        "Product ID": dev["product"],
        "Driver": dev["driver"],
        "Bus Speed": dev["speed"],
        "Max Power": dev["power"],
        "Port Path": dev["port"],
    })

    hardware_title.show()
    hardware_box.show()
    extra_title.hide()
    extra_box.hide()
    usage_bar.hide()
    chart_title.hide()
    live_label.hide()
    chart_box.hide()
    inspector.show()


def show_details(item):
    global current_device, last_bytes, extra_labels
    show_hardware(item)
    dev = device_info[item.text(0)]
    current_device = dev
    last_bytes = None

    if dev["type"] == "Network":
        iface = dev["interface"] or "-"
        speed = read_file(f"/sys/class/net/{iface}/speed")
        if speed.isdigit():
            speed = speed + " Mbps"
        else:
            speed = "-"
        info = {"Interface": iface, "Link Speed": speed, "Download": "-", "Upload": "-",
                "Received": "-", "Sent": "-"}
    else:
        info = dict(dev["info"])

    if dev["type"] == "Storage" and os.path.exists(dev.get("mount", "")):
        disk = shutil.disk_usage(dev["mount"])
        info["Capacity"] = size_text(disk.total)
        info["Used"] = size_text(disk.used)
        info["Free"] = size_text(disk.free)
        dev["used_percent"] = disk.used / disk.total * 100

    if dev["type"] in ["Mouse", "Keyboard"]:
        extra_title.setText("INPUT")
    else:
        extra_title.setText(dev["type"].upper())
    extra_labels = fill_box(extra_layout, info)

    extra_title.show()
    extra_box.show()

    usage_bar.setVisible("used_percent" in dev)
    usage_bar.setValue(int(dev.get("used_percent", 0)))

    is_network = dev["type"] == "Network"
    chart.download.clear()
    chart.upload.clear()
    live_label.setText("")
    chart_title.setVisible(is_network)
    live_label.setVisible(is_network)
    chart_box.setVisible(is_network)
    inspector.show()


def update_speed():
    global last_bytes
    if current_device is None or not current_device.get("interface") or not inspector.isVisible():
        return
    folder = f"/sys/class/net/{current_device['interface']}/statistics/"
    received = int(read_file(folder + "rx_bytes") or 0)
    sent = int(read_file(folder + "tx_bytes") or 0)
    extra_labels["Received"].setText(size_text(received))
    extra_labels["Sent"].setText(size_text(sent))
    if last_bytes is not None:
        download = received - last_bytes[0]
        upload = sent - last_bytes[1]
        extra_labels["Download"].setText(size_text(download) + "/s")
        extra_labels["Upload"].setText(size_text(upload) + "/s")
        live_label.setText(f"↓ {size_text(download)}/s  ↑ {size_text(upload)}/s")
        chart.download.append(download)
        chart.upload.append(upload)
        chart.update()
    last_bytes = (received, sent)


tree.itemClicked.connect(show_hardware)
tree.itemDoubleClicked.connect(show_details)

timer = QTimer()
timer.timeout.connect(update_speed)
timer.start(1000)


left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch= 6)

right_panel = QWidget()
right_panel.setStyleSheet("border: none;")
right_layout = QVBoxLayout(right_panel)
right_layout.addWidget(inspector)
main_layout.addWidget(right_panel, stretch=4)

window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())