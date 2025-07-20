# hel_netfix_gui_qt.py
# SMA Coding - Helwan Linux Official Tool - Qt Edition

import sys
import subprocess
import threading
import os
import datetime # Added for logging timestamps
import socket # Added for network check

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QMessageBox, QHBoxLayout, QDialog, QTextEdit, QDialogButtonBox,
    QStackedWidget # Could be useful for advanced settings, but QDialog is simpler for now
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject # Added for safer UI updates from threads

# --- SIGNAL CLASS FOR THREAD-SAFE UI UPDATES ---
class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str)
    log = pyqtSignal(str, str, str, str) # type, command, status, output

# --- ADVANCED SETTINGS DIALOG ---
class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None, initial_commands=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings - Custom Commands")
        self.setGeometry(100, 100, 600, 450) # Increased size for better usability

        layout = QVBoxLayout()

        description_label = QLabel(
            "Enter custom Pacman or system commands below, one command per line.\n"
            "These commands will be executed when 'Run Custom Commands' button is pressed."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        self.commands_text_edit = QTextEdit()
        self.commands_text_edit.setPlaceholderText(
            "Example:\n"
            "sudo pacman -Syu --noconfirm\n"
            "sudo pacman -Qdtq\n"
            "echo 'Custom command executed!'"
        )
        if initial_commands:
            self.commands_text_edit.setText("\n".join(initial_commands))
        
        layout.addWidget(self.commands_text_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.custom_commands = []

    def accept(self):
        raw_text = self.commands_text_edit.toPlainText()
        self.custom_commands = [cmd.strip() for cmd in raw_text.split('\n') if cmd.strip()]
        super().accept()

# --- MAIN APPLICATION CLASS ---
class NetFixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helwan Linux - NetFix Tool")
        self.setFixedSize(500, 600) # Adjusted size to accommodate more buttons

        # Initialize WorkerSignals for thread-safe updates
        self.signals = WorkerSignals()
        self.signals.result.connect(self.update_output)
        self.signals.error.connect(self.handle_error)
        self.signals.log.connect(self._log_action)

        # Log file path
        self.log_dir = os.path.expanduser("~/.helwanlinux")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file_path = os.path.join(self.log_dir, "netfix_log.txt")

        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout()
        layout.setSpacing(10) # Add some spacing between elements

        # Create buttons for predefined commands
        self.predefined_commands = COMMANDS # Store original COMMANDS for reference
        for label in self.predefined_commands:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, cmd=self.predefined_commands[label]: self.run_command(cmd))
            layout.addWidget(btn)

        # Full auto fix button
        full_fix = QPushButton("Full Auto Fix (All Predefined Commands)")
        full_fix.clicked.connect(self.run_all_predefined_commands)
        full_fix.setStyleSheet("background-color: #28a745; color: white;") # Green color
        layout.addWidget(full_fix)

        # --- NEW FEATURES BUTTONS ---

        # Advanced Settings & Run Custom Commands
        layout.addSpacing(15)
        advanced_label = QLabel("--- Advanced Tools ---")
        advanced_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(advanced_label)

        self.custom_commands_list = [] # To store commands from advanced settings

        advanced_settings_btn = QPushButton("Configure Custom Commands")
        advanced_settings_btn.clicked.connect(self.show_advanced_settings)
        layout.addWidget(advanced_settings_btn)
        
        run_custom_btn = QPushButton("Run Custom Commands")
        run_custom_btn.clicked.connect(self.run_custom_commands)
        run_custom_btn.setStyleSheet("background-color: #ffc107; color: black;") # Yellow color
        layout.addWidget(run_custom_btn)


        # Rollback / Snapshot Buttons
        layout.addSpacing(15)
        snapshot_label = QLabel("--- System Snapshots (Timeshift) ---")
        snapshot_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(snapshot_label)

        create_snapshot_btn = QPushButton("Create System Snapshot")
        create_snapshot_btn.clicked.connect(self.create_timeshift_snapshot)
        layout.addWidget(create_snapshot_btn)

        launch_timeshift_gui_btn = QPushButton("Launch Timeshift GUI (for Restore)")
        launch_timeshift_gui_btn.clicked.connect(self.launch_timeshift_gui)
        layout.addWidget(launch_timeshift_gui_btn)

        # Network Check
        layout.addSpacing(15)
        network_label = QLabel("--- Network Diagnostics ---")
        network_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(network_label)

        check_net_btn = QPushButton("Check Internet Connection")
        check_net_btn.clicked.connect(self.check_internet_connection)
        layout.addWidget(check_net_btn)

        # Help & About buttons
        layout.addSpacing(15)
        info_label = QLabel("--- Information ---")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

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
        self.output.setStyleSheet("font-weight: bold;")
        self.output.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.output)

        self.setLayout(layout)

    # --- LOGGING FUNCTION ---
    def _log_action(self, action_type, command, status, output=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{action_type}] Command: '{command}' | Status: {status}\n"
        if output:
            log_entry += f"Output:\n{output}\n"
        log_entry += "-" * 50 + "\n" # Separator

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Fallback if logging to file fails
            print(f"Error writing to log file: {e}")

    # --- UI UPDATE SLOTS (THREAD-SAFE) ---
    def update_output(self, message):
        self.output.setText(message)

    def handle_error(self, message):
        self.output.setText(f"❌ {message}")
        QMessageBox.critical(self, "Error", message)

    # --- COMMAND EXECUTION FUNCTIONS ---
    def _execute_command_in_thread(self, command, action_type="GENERIC_COMMAND", display_name=None):
        def task():
            cmd_to_display = display_name if display_name else command
            self.signals.result.emit(f"Running: {cmd_to_display}")
            try:
                # capture_output=True and text=True to get stdout/stderr for logging
                process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                self.signals.result.emit("✅ Done.")
                self.signals.log.emit(action_type, command, "SUCCESS", process.stdout)
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed: {cmd_to_display}. Error code: {e.returncode}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
            except FileNotFoundError:
                error_msg = f"Command '{command.split()[0]}' not found."
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
        
        threading.Thread(target=task).start()

    def run_command(self, command):
        self._execute_command_in_thread(command, action_type="SINGLE_COMMAND")

    def run_all_predefined_commands(self):
        def task():
            all_successful = True
            for name, command in self.predefined_commands.items():
                self.signals.result.emit(f"Running: {name}")
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    self.signals.log.emit("FULL_AUTO_FIX", command, "SUCCESS", process.stdout)
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(f"❌ Failed at {name}. Check log.")
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(f"❌ Command for '{name}' not found. Check log.")
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Command not found for {name}")
                    all_successful = False
                    break
            
            if all_successful:
                self.signals.result.emit("✅ All predefined tasks completed successfully.")
            else:
                self.signals.result.emit("❌ Full Auto Fix completed with errors. Check log for details.")
        threading.Thread(target=task).start()

    # --- NEW FEATURE IMPLEMENTATIONS ---

    # 2. Advanced Settings / Custom Commands
    def show_advanced_settings(self):
        dialog = AdvancedSettingsDialog(self, self.custom_commands_list)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_commands_list = dialog.custom_commands
            self.signals.result.emit(f"Loaded {len(self.custom_commands_list)} custom commands.")
            self._log_action("SETTINGS", "Update custom commands", "SUCCESS", f"New custom commands: {self.custom_commands_list}")
        else:
            self.signals.result.emit("Custom command configuration cancelled.")

    def run_custom_commands(self):
        if not self.custom_commands_list:
            QMessageBox.warning(self, "No Custom Commands", "Please configure custom commands first in Advanced Settings.")
            self.signals.result.emit("No custom commands to run.")
            return

        def task():
            all_successful = True
            for i, command in enumerate(self.custom_commands_list):
                self.signals.result.emit(f"Running custom command {i+1}/{len(self.custom_commands_list)}: {command}")
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "SUCCESS", process.stdout)
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(f"❌ Custom command failed: {command}. Check log.")
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(f"❌ Custom command '{command.split()[0]}' not found. Check log.")
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Command not found: {command}")
                    all_successful = False
                    break
            
            if all_successful:
                self.signals.result.emit("✅ All custom commands completed successfully.")
            else:
                self.signals.result.emit("❌ Custom commands completed with errors. Check log for details.")
        threading.Thread(target=task).start()

    # 3. Rollback / Timeshift Integration
    def create_timeshift_snapshot(self):
        self._execute_command_in_thread(
            "sudo timeshift --create --comments 'NetFix pre-action snapshot' --yes",
            action_type="SNAPSHOT_CREATE",
            display_name="Create System Snapshot (Timeshift)"
        )
        self.signals.result.emit("Creating Timeshift snapshot... This may take a while.")

    def launch_timeshift_gui(self):
        # Using pkexec for GUI apps that need root privileges
        # User will be prompted for password by pkexec
        self._execute_command_in_thread(
            "pkexec timeshift-launcher",
            action_type="TIMESHAFT_GUI_LAUNCH",
            display_name="Launch Timeshift GUI"
        )

    # 4. Check Internet Connection
    def check_internet_connection(self):
        def task():
            self.signals.result.emit("Checking internet connection...")
            try:
                # Try to resolve a common domain like google.com
                socket.gethostbyname("www.google.com")
                # Then try to ping it
                subprocess.run("ping -c 4 www.google.com", shell=True, check=True, capture_output=True, text=True)
                self.signals.result.emit("✅ Internet connection is active.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "SUCCESS", "Internet connection is active.")
            except socket.gaierror:
                self.signals.error.emit("❌ DNS resolution failed. No internet connection or DNS issue.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", "DNS resolution failed.")
            except subprocess.CalledProcessError as e:
                self.signals.error.emit(f"❌ Ping test failed. No internet connection or firewall blocking. Error: {e.stderr}")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", f"Ping test failed. Error: {e.stderr}")
            except FileNotFoundError:
                self.signals.error.emit("❌ 'ping' command not found. Please ensure network utilities are installed.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", "'ping' command not found.")
            except Exception as e:
                self.signals.error.emit(f"An unexpected error occurred during network check: {e}")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", f"Unexpected error: {e}")
        threading.Thread(target=task).start()

    # --- EXISTING COMMANDS (UNCHANGED FUNCTIONALITY, ONLY MOVED) ---
    def show_help(self):
        help_msg = (
            "This tool provides quick fixes and system management for Arch-based systems:\n\n"
            "Predefined Commands:\n"
            "- Repair Database: Clean unused packages.\n"
            "- Clear Cache: Remove old packages.\n"
            "- Fix Corrupted: Resolve overwrite errors.\n"
            "- Update: Sync system.\n"
            "- Refresh Mirrors: Get best servers.\n"
            "- Reinstall Broken: Fix missing packages.\n"
            "- Full Auto Fix: Runs all above commands sequentially.\n\n"
            "Advanced Tools:\n"
            "- Configure Custom Commands: Define your own sequence of commands.\n"
            "- Run Custom Commands: Execute the commands you defined.\n\n"
            "System Snapshots (Timeshift):\n"
            "- Create System Snapshot: Creates a restore point for your system.\n"
            "- Launch Timeshift GUI: Opens Timeshift application to manage/restore snapshots.\n\n"
            "Network Diagnostics:\n"
            "- Check Internet Connection: Tests your network connectivity.\n\n"
            "All actions are logged to ~/.helwanlinux/netfix_log.txt for review."
        )
        QMessageBox.information(self, "Help", help_msg)

    def show_about(self):
        about_text = (
            "Helwan Linux NetFix GUI\n"
            "Version 1.0 (with Advanced Features)\n"
            "By SMA Coding / Helwan Linux Team\n"
            "Saeed Badrelden : helwanlinux@gmail.com\n\n"
            "Designed to simplify system maintenance and troubleshooting for Helwan Linux."
        )
        QMessageBox.information(self, "About", about_text)

# --- INITIAL COMMANDS DEFINITION ---
COMMANDS = {
    "Repair Database": "sudo pacman -D --asdeps $(pacman -Qdtq)",
    "Clear Cache": "sudo pacman -Scc",
    "Fix Corrupted Packages": "sudo pacman -Syu --overwrite '*'",
    "Update System": "sudo pacman -Syu",
    "Refresh Mirrors": "sudo reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist",
    "Reinstall Broken Packages": "sudo pacman -Qqn | xargs sudo pacman -S",
}

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFixApp()
    window.show()
    sys.exit(app.exec_())
