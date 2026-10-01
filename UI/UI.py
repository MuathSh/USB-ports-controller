import sys
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
    QFormLayout,
    QFrame
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
]

for dev in devices:
    item = QTreeWidgetItem(dev)
    tree.addTopLevelItem(item)


left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

details_panel = QFrame()
details_panel.setObjectName("detailsPanel")

details_layout = QVBoxLayout(details_panel)

more_title = QLabel()
more_title.setObjectName("detailsTitle")

more_form = QFormLayout()

details_layout.addWidget(more_title)
details_layout.addLayout(more_form)
details_layout.addStretch()

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch=6)
main_layout.addWidget(details_panel, stretch=4)


window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())

