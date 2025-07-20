# hel_netfix_gui_qt.py
# SMA Coding - Helwan Linux Official Tool - Qt Edition

import sys
import subprocess
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QIcon

COMMANDS = {
    "Repair Database": "sudo pacman -D --asdeps $(pacman -Qdtq)",
    "Clear Cache": "sudo pacman -Scc",
    "Fix Corrupted Packages": "sudo pacman -Syu --overwrite '*'",
    "Update System": "sudo pacman -Syu",
    "Refresh Mirrors": "sudo reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist",
    "Reinstall Broken Packages": "sudo pacman -Qqn | xargs sudo pacman -S",
}

class NetFixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helwan Linux - NetFix Tool")
        self.setFixedSize(400, 300)

        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()

        # Create buttons for commands
        for label in COMMANDS:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, cmd=COMMANDS[label]: self.run_command(cmd))
            layout.addWidget(btn)

        # Full auto fix button
        full_fix = QPushButton("Full Auto Fix")
        full_fix.clicked.connect(self.run_all_commands)
        layout.addWidget(full_fix)

        # Help & About buttons
        hbox = QHBoxLayout()
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)
        hbox.addWidget(help_btn)
        hbox.addWidget(about_btn)
        layout.addLayout(hbox)

        # Output label
        self.output = QLabel("Ready.")
        layout.addWidget(self.output)

        self.setLayout(layout)

    def run_command(self, command):
        def task():
            self.output.setText(f"Running: {command}")
            try:
                subprocess.run(command, shell=True, check=True)
                self.output.setText("✅ Done.")
            except subprocess.CalledProcessError:
                self.output.setText("❌ Failed.")
        threading.Thread(target=task).start()

    def run_all_commands(self):
        def task():
            for name, command in COMMANDS.items():
                self.output.setText(f"Running: {name}")
                try:
                    subprocess.run(command, shell=True, check=True)
                except subprocess.CalledProcessError:
                    self.output.setText(f"❌ Failed at {name}")
                    return
            self.output.setText("✅ All tasks completed successfully.")
        threading.Thread(target=task).start()

    def show_help(self):
        help_msg = (
            "This tool provides quick fixes for Arch-based systems:\n"
            "- Repair Database: Clean unused packages.\n"
            "- Clear Cache: Remove old packages.\n"
            "- Fix Corrupted: Resolve overwrite errors.\n"
            "- Update: Sync system.\n"
            "- Refresh Mirrors: Get best servers.\n"
            "- Reinstall Broken: Fix missing packages.\n"
            "- Full Fix: Runs all above."
        )
        QMessageBox.information(self, "Help", help_msg)

    def show_about(self):
        about_text = (
            "Helwan Linux NetFix GUI\n"
            "Version 1.0\n"
            "By SMA Coding / Helwan Linux Team\n"
            "Saeed Badrelden : helwanlinux@gmail.com"
        )
        QMessageBox.information(self, "About", about_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFixApp()
    window.show()
    sys.exit(app.exec_())
