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
    QPushButton {
        background-color: #007acc;
        color: white;
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #0098ff;
    }
""")

active_btn = QPushButton("Active")
unbind_btn = QPushButton("Unbind")

button_layout = QHBoxLayout()
button_layout.addWidget(active_btn)
button_layout.addWidget(unbind_btn)
button_layout.addStretch()

tree = QTreeWidget()
tree.setHeaderLabels(["Sys Name", "USB Name", "Device Type", "Status"])
tree.setColumnWidth(0, 80)
tree.setColumnWidth(1, 345)
tree.setColumnWidth(2, 150)
tree.setColumnWidth(3, 150)



left_layout = QVBoxLayout()
left_layout.addWidget(tree, stretch=1)
left_layout.addLayout(button_layout)

main_layout = QHBoxLayout()
main_layout.addLayout(left_layout, stretch= 6)
main_layout.addStretch(stretch=4)

window.setLayout(main_layout)

window.show()
sys.exit(PROGRAM.exec())