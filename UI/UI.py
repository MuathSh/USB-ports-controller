import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QTreeWidget, 
    QTreeWidgetItem, 
    QPushButton
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
    QTreeWidget::item:selected {
    background-color: #04395e;
    color: #ffffff;
    border-radius: 4px;
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

for dev in devices:
    item = QTreeWidgetItem(dev)
    tree.addTopLevelItem(item)


left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch= 6)
main_layout.addStretch(stretch=4)

window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())