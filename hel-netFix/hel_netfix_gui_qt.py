import sys
import subprocess
import threading
import os
import signal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QMessageBox, QHBoxLayout, QTextEdit, QProgressBar
)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# Final Command Configuration for Helwan Linux
COMMANDS = {
    "Repair Database": {
        "command": ["pkexec", "pacman", "-D", "--asdeps"],
        "pre_command": ["pacman", "-Qdtq"],
        "desc": "Fixing orphaned packages."
    },
    "Clear Cache": {
        "command": ["pkexec", "bash", "-c", "yes | pacman -Scc"],
        "desc": "Cleaning package cache."
    },
    "Fix Corrupted Packages": {
        "command": ["pkexec", "pacman", "-Syu", "--overwrite", "*", "--noconfirm"],
        "desc": "Overwriting corrupted files and updating."
    },
    "Update System": {
        "command": ["pkexec", "pacman", "-Syu", "--noconfirm"],
        "desc": "Standard system update."
    },
    "Refresh Mirrors": {
        "command": ["pkexec", "pacman", "-Syy", "--noconfirm"],
        "desc": "Refreshing repository databases."
    },
}

class WorkerSignals(QObject):
    output_appended = pyqtSignal(str)
    command_started = pyqtSignal(str, QPushButton)
    command_finished = pyqtSignal(str, QPushButton, bool)
    full_fix_started = pyqtSignal()
    full_fix_step_update = pyqtSignal(str, QPushButton)
    full_fix_finished = pyqtSignal(bool)

class NetFixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helwan Linux - NetFix Tool")
        self.setFixedSize(600, 650)
        self.current_process = None
        self.is_cancelled = False

        self.signals = WorkerSignals()
        self.signals.output_appended.connect(self._append_output)
        self.signals.command_started.connect(self._on_start)
        self.signals.command_finished.connect(self._on_finish)
        self.signals.full_fix_started.connect(self._on_full_start)
        self.signals.full_fix_step_update.connect(self._on_step_update)
        self.signals.full_fix_finished.connect(self._on_full_finish)

        self.init_ui()

    def init_ui(self):
        # Icon handling
        icon_name = "netfix.png"
        icon_paths = [os.path.join(os.path.dirname(__file__), icon_name), f"/usr/share/pixmaps/{icon_name}"]
        for path in icon_paths:
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break

        layout = QVBoxLayout()
        self.buttons = {}

        for label, data in COMMANDS.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, l=label, b=btn, d=data: self.run_task(l, b, d))
            layout.addWidget(btn)
            self.buttons[label] = btn

        self.full_fix_btn = QPushButton("Full Auto Fix")
        self.full_fix_btn.setStyleSheet("background-color: #2c3e50; color: white; font-weight: bold; padding: 8px;")
        self.full_fix_btn.clicked.connect(self.run_full_fix)
        layout.addWidget(self.full_fix_btn)

        self.cancel_btn = QPushButton("Stop Current Operation")
        self.cancel_btn.setStyleSheet("background-color: #c0392b; color: white;")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_task)
        layout.addWidget(self.cancel_btn)

        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 0)
        self.progressBar.hide()
        layout.addWidget(self.progressBar)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("background-color: #1a1a1a; color: #00ff41; font-family: monospace;")
        self.console.setText("Helwan Linux NetFix Ready...")
        layout.addWidget(self.console)

        self.setLayout(layout)

    def check_lock(self):
        lock = "/var/lib/pacman/db.lck"
        if os.path.exists(lock):
            self.signals.output_appended.emit("Removing database lock...")
            try:
                subprocess.run(["pkexec", "rm", lock], check=True)
                return True
            except:
                return False
        return True

    def cancel_task(self):
        if self.current_process:
            self.is_cancelled = True
            try:
                pid = self.current_process.pid
                subprocess.run(["pkexec", "kill", "-9", str(pid)], check=False)
                self.current_process.terminate()
            except:
                pass
            self.signals.output_appended.emit("\nOperation cancelled by user.")

    def _execute(self, cmd):
        if self.is_cancelled: return -1, False
        self.signals.output_appended.emit(f"\nExecuting: {' '.join(cmd)}")
        try:
            self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, preexec_fn=os.setsid)
            for line in iter(self.current_process.stdout.readline, ''):
                if self.is_cancelled: break
                self.signals.output_appended.emit(line.strip())
            rc = self.current_process.wait()
            return rc, (rc == 0 and not self.is_cancelled)
        except Exception as e:
            self.signals.output_appended.emit(f"Error: {e}")
            return -1, False

    def run_task(self, name, btn, data):
        def t():
            self.is_cancelled = False
            if not self.check_lock(): return
            self.signals.command_started.emit(name, btn)
            
            final_cmd = list(data['command'])
            if "pre_command" in data:
                res = subprocess.run(data['pre_command'], capture_output=True, text=True)
                targets = res.stdout.split()
                if not targets:
                    self.signals.output_appended.emit("System is clean. No targets found.")
                    self.signals.command_finished.emit(name, btn, True)
                    return
                final_cmd.extend(targets)

            _, success = self._execute(final_cmd)
            self.signals.command_finished.emit(name, btn, success)
        threading.Thread(target=t, daemon=True).start()

    def run_full_fix(self):
        def t():
            self.is_cancelled = False
            if not self.check_lock(): return
            self.signals.full_fix_started.emit()
            for name, data in COMMANDS.items():
                if self.is_cancelled: break
                self.signals.full_fix_step_update.emit(name, self.buttons[name])
                
                final_cmd = list(data['command'])
                if "pre_command" in data:
                    res = subprocess.run(data['pre_command'], capture_output=True, text=True)
                    targets = res.stdout.split()
                    if not targets: continue
                    final_cmd.extend(targets)
                
                _, success = self._execute(final_cmd)
                if not success: break
            self.signals.full_fix_finished.emit(not self.is_cancelled)
        threading.Thread(target=t, daemon=True).start()

    # UI Slots
    def _append_output(self, text):
        self.console.append(text)
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def _on_start(self, name, btn):
        self._toggle_ui(False)
        self.progressBar.show()

    def _on_finish(self, name, btn, success):
        self._toggle_ui(True)
        self.progressBar.hide()
        if success:
            QMessageBox.information(self, "Success", f"Task '{name}' completed successfully!")
        elif not self.is_cancelled:
            QMessageBox.critical(self, "Error", f"Task '{name}' failed. Check logs.")

    def _on_full_start(self):
        self._toggle_ui(False)
        self.progressBar.show()

    def _on_full_finish(self, success):
        self._toggle_ui(True)
        self.progressBar.hide()
        for n, b in self.buttons.items(): b.setText(n)
        if success:
            QMessageBox.information(self, "Complete", "System optimization finished successfully!")

    def _on_step_update(self, name, btn):
        btn.setText(f">> {name}")

    def _toggle_ui(self, enabled):
        for b in self.buttons.values(): b.setEnabled(enabled)
        self.full_fix_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(not enabled)
        cursor = Qt.WaitCursor if not enabled else Qt.ArrowCursor
        QApplication.setOverrideCursor(QCursor(cursor)) if not enabled else QApplication.restoreOverrideCursor()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = NetFixApp()
    win.show()
    sys.exit(app.exec_())
