# hel_netfix_gui_qt.py
# SMA Coding - Helwan Linux Official Tool - Qt Edition

import sys
import subprocess
import threading
import os
import datetime
import socket

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QMessageBox, QHBoxLayout, QDialog, QTextEdit, QDialogButtonBox,
    QProgressDialog,
    QScrollArea,
    QGroupBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject


# --- LOCALIZED STRINGS (FOR UI DISPLAY ONLY) ---
# All user-facing strings are defined here.
# Note: As per the last request, all these strings are now in English.
UI_STRINGS = {
    "app_title": "Helwan Linux - NetFix Tool",
    "about_title": "About",
    "help_title": "Help",
    "advanced_settings_dialog_title": "Advanced Settings - Custom Commands",
    "advanced_settings_description": (
        "Enter custom Pacman or system commands below, one command per line.\n"
        "These commands will be executed when the 'Run Custom Commands' button is pressed.\n"
        "Be careful with custom commands as they are executed with root privileges."
    ),
    "custom_commands_placeholder": (
        "Example:\n"
        "sudo pacman -Syu --noconfirm\n"
        "sudo pacman -Qdtq\n"
        "echo 'Custom command executed!'"
    ),
    "predefined_group_title": "Predefined Fixes",
    "full_auto_fix_button_text": "Full Auto Fix (All Predefined Commands)",
    "advanced_tools_group_title": "Advanced Tools",
    "configure_custom_commands_button_text": "Configure Custom Commands",
    "run_custom_commands_button_text": "Run Custom Commands",
    "snapshot_group_title": "System Snapshots (Timeshift)",
    "create_snapshot_button_text": "Create System Snapshot",
    "launch_timeshift_gui_button_text": "Launch Timeshift GUI (for Restore)",
    "network_diagnostics_group_title": "Network Diagnostics",
    "check_internet_button_text": "Check Internet Connection",
    "info_group_title": "Information",
    "help_button_text": "Help",
    "about_button_text": "About",
    "initial_status_message": "Ready.",
    "error_dialog_title": "Error",
    "running_status_prefix": "Running: ",
    "success_message": "✅ Success.",
    "timeout_error_prefix": "Command timed out after ",
    "timeout_error_suffix_seconds": " seconds: ",
    "long_operation_timeout_suffix": ". Took too long to complete.",
    "command_failed_prefix": "Failed: ",
    "command_failed_suffix_code": ". Error code: ",
    "command_not_found_prefix": "Command '",
    "command_not_found_suffix": "' not found. Ensure it is installed and in your PATH.",
    "unexpected_error_prefix": "An unexpected error occurred: ",
    "sensitive_command_confirm_title": "Confirm Sensitive Command",
    "sensitive_command_confirm_message_prefix": "You are about to execute a sensitive command:\n\n",
    "sensitive_command_confirm_message_suffix": "\n\nThis command may cause system issues if not used correctly. Are you sure you want to proceed?",
    "sensitive_command_cancelled": "Sensitive command cancelled by user.",
    "full_auto_fix_confirm_title": "Confirm 'Full Auto Fix'",
    "full_auto_fix_confirm_message": (
        "You are about to run 'Full Auto Fix'. This will execute several sensitive commands "
        "like updating and reinstalling packages. This may take some time. Are you sure you want to proceed?"
    ),
    "full_auto_fix_cancelled": "'Full Auto Fix' cancelled by user.",
    "full_auto_fix_progress_message": "Please wait: Full Auto Fix...",
    "full_auto_fix_timeout_check_log": ". Check log.",
    "full_auto_fix_failed_prefix": "❌ Failed in ",
    "full_auto_fix_failed_suffix_code": ". Error code: ",
    "full_auto_fix_command_not_found_prefix": "❌ Command for '",
    "full_auto_fix_command_not_found_suffix": "' not found. Check log.",
    "full_auto_fix_success": "✅ All predefined tasks completed successfully. Your system's stability is a reflection of the efforts of open-source pioneers.",
    "full_auto_fix_error_summary": "❌ Full Auto Fix completed with errors. Check log for details.",
    "no_custom_commands_warning_title": "No Custom Commands",
    "no_custom_commands_warning_message": "Please configure custom commands first in Advanced Settings.",
    "no_custom_commands_status": "No custom commands to run.",
    "custom_commands_loaded_prefix": "Loaded ",
    "custom_commands_loaded_suffix": " custom command(s).",
    "custom_commands_config_cancelled": "Custom commands configuration cancelled.",
    "custom_commands_confirm_title": "Confirm Custom Commands",
    "custom_commands_confirm_message": (
        "You are about to run the custom commands you defined.\n"
        "These commands will be executed with root privileges (sudo). Are you sure you want to proceed?"
    ),
    "custom_commands_cancelled": "Custom commands execution cancelled.",
    "custom_commands_progress_message": "Please wait: Running Custom Commands...",
    "custom_commands_running_prefix": "Running custom command ",
    "custom_commands_running_middle": "/",
    "custom_commands_running_suffix": ": ",
    "custom_commands_timeout_prefix": "❌ Custom command timed out: ",
    "custom_commands_timeout_suffix": ". Check log.",
    "custom_commands_failed_prefix": "❌ Custom command failed: ",
    "custom_commands_failed_suffix_code": ". Error code: ",
    "custom_commands_cmd_not_found_prefix": "❌ Custom command '",
    "custom_commands_cmd_not_found_suffix": "' not found. Check log.",
    "custom_commands_success": "✅ All custom commands completed successfully.",
    "custom_commands_error_summary": "❌ Custom commands completed with errors. Check log for details.",
    "create_snapshot_confirm_title": "Confirm Snapshot Creation",
    "create_snapshot_confirm_message": (
        "You are about to create a System Snapshot using Timeshift.\n"
        "This action may take some time and depends on your system size. Are you sure you want to proceed?"
    ),
    "create_snapshot_cancelled": "Snapshot creation cancelled by user.",
    "create_snapshot_progress_message": "Please wait: Creating Timeshift Snapshot...",
    "timeshift_gui_launch_progress": "Please wait: Launching Timeshift GUI...",
    "timeshift_gui_launch_message": "Launching Timeshift GUI. You may need to enter your password.",
    "check_internet_progress": "Please wait: Checking Internet Connection...",
    "internet_connected": "✅ Connected to the Internet.",
    "internet_not_connected": "❌ Not connected to the Internet. (DNS or Ping failed).",
    "internet_check_error": "❌ An error occurred while checking internet connection: ",
    "help_content": (
        "Welcome to Helwan Linux NetFix Tool!\n\n"
        "This tool is designed to simplify common system maintenance and troubleshooting tasks.\n\n"
        "Key Features:\n"
        "- Predefined Fixes: A set of common commands to fix package issues, clear cache, and update the system.\n"
        "- Full Auto Fix: Executes all predefined fixes in one step.\n"
        "- Custom Commands: Configure and run your own commands (with root privileges).\n"
        "- System Snapshots (Timeshift): Create system snapshots for rollback in case of issues, or launch Timeshift GUI for restoration.\n"
        "- Network Diagnostics: Check your internet connection.\n\n"
        "All actions are logged to ~/.helwanlinux/netfix_log.txt for review."
    ),
    "about_content": (
        "Helwan Linux NetFix GUI\n"
        "Version 1.0 (with Advanced Features)\n"
        "By SMA Coding / Helwan Linux Team\n"
        "Saeed Badrelden : helwanlinux@gmail.com\n\n"
        "Designed to simplify system maintenance and troubleshooting for Helwan Linux.\n"
        "This tool is open source and contributions are welcome.\n\n"
        # Linus Torvalds tribute
        "In tribute and appreciation of Linus Torvalds' contributions.\n"
        "Linus Torvalds is the mastermind behind the Linux kernel, the foundational component\n"
        "upon which powerful and stable operating systems like Helwan Linux are built.\n"
        "Thanks to his vision and hard work, open-source software has become a cornerstone of the digital world.\n"
        "This program aims to contribute to the stability and reliability of your system,\n"
        "drawing inspiration from the spirit of perseverance and excellence Linus established in the software world."
    )
}


# --- SIGNAL CLASS FOR THREAD-SAFE UI UPDATES ---
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished: No data
    error:    str (Error message)
    result:   str (Message for status/output label)
    log:      str, str, str, str (action_type, command, status, output for logging)
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(str)
    log = pyqtSignal(str, str, str, str)


# --- ADVANCED SETTINGS DIALOG ---
class AdvancedSettingsDialog(QDialog):
    """
    Dialog for configuring custom commands.
    Allows users to input multi-line commands.
    """
    def __init__(self, parent=None, initial_commands=None):
        super().__init__(parent)
        self.setWindowTitle(UI_STRINGS["advanced_settings_dialog_title"])
        self.setGeometry(100, 100, 600, 450)

        layout = QVBoxLayout()

        description_label = QLabel(UI_STRINGS["advanced_settings_description"])
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        self.commands_text_edit = QTextEdit()
        self.commands_text_edit.setPlaceholderText(UI_STRINGS["custom_commands_placeholder"])
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
        """
        Processes the input text when the OK button is pressed.
        Strips whitespace and filters empty lines.
        """
        raw_text = self.commands_text_edit.toPlainText()
        self.custom_commands = [cmd.strip() for cmd in raw_text.split('\n') if cmd.strip()]
        super().accept()


# --- MAIN APPLICATION CLASS ---
class NetFixApp(QWidget):
    """
    Main application window for the Helwan Linux NetFix Tool.
    Manages UI, command execution, logging, and new features.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(UI_STRINGS["app_title"])
        self.setMinimumSize(500, 750)

        # Initialize WorkerSignals for thread-safe updates
        self.signals = WorkerSignals()
        self.signals.result.connect(self.update_output)
        self.signals.error.connect(self.handle_error)
        self.signals.log.connect(self._log_action)
        self.signals.finished.connect(self.enable_all_buttons)

        # Log file path
        self.log_dir = os.path.expanduser("~/.helwanlinux")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file_path = os.path.join(self.log_dir, "netfix_log.txt")

        # Load icon (Assuming netfix.png is in the same directory as the script)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Main layout for the widget
        main_layout = QVBoxLayout(self)

        # Create a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        
        # Widget to hold all contents inside the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)

        self.buttons = [] # List to keep track of all buttons for enable/disable operations

        # --- PREDEFINED COMMANDS GROUP ---
        predefined_group = QGroupBox(UI_STRINGS["predefined_group_title"])
        predefined_layout = QVBoxLayout()
        # COMMANDS dictionary is defined globally at the end of the file
        self.predefined_commands = COMMANDS 
        for label, cmd in self.predefined_commands.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, command=cmd: self.run_command(command))
            predefined_layout.addWidget(btn)
            self.buttons.append(btn)
        predefined_group.setLayout(predefined_layout)
        content_layout.addWidget(predefined_group)

        # Full auto fix button
        full_fix_btn = QPushButton(UI_STRINGS["full_auto_fix_button_text"])
        full_fix_btn.clicked.connect(self.run_all_predefined_commands)
        full_fix_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        content_layout.addWidget(full_fix_btn)
        self.buttons.append(full_fix_btn)

        # --- ADVANCED TOOLS GROUP ---
        advanced_group = QGroupBox(UI_STRINGS["advanced_tools_group_title"])
        advanced_layout = QVBoxLayout()
        self.custom_commands_list = []

        advanced_settings_btn = QPushButton(UI_STRINGS["configure_custom_commands_button_text"])
        advanced_settings_btn.clicked.connect(self.show_advanced_settings)
        advanced_layout.addWidget(advanced_settings_btn)
        self.buttons.append(advanced_settings_btn)
        
        run_custom_btn = QPushButton(UI_STRINGS["run_custom_commands_button_text"])
        run_custom_btn.clicked.connect(self.run_custom_commands)
        run_custom_btn.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;")
        advanced_layout.addWidget(run_custom_btn)
        self.buttons.append(run_custom_btn)
        advanced_group.setLayout(advanced_layout)
        content_layout.addWidget(advanced_group)

        # --- SYSTEM SNAPSHOTS GROUP ---
        snapshot_group = QGroupBox(UI_STRINGS["snapshot_group_title"])
        snapshot_layout = QVBoxLayout()

        create_snapshot_btn = QPushButton(UI_STRINGS["create_snapshot_button_text"])
        create_snapshot_btn.clicked.connect(self.create_timeshift_snapshot)
        snapshot_layout.addWidget(create_snapshot_btn)
        self.buttons.append(create_snapshot_btn)

        launch_timeshift_gui_btn = QPushButton(UI_STRINGS["launch_timeshift_gui_button_text"])
        launch_timeshift_gui_btn.clicked.connect(self.launch_timeshift_gui)
        snapshot_layout.addWidget(launch_timeshift_gui_btn)
        self.buttons.append(launch_timeshift_gui_btn)
        snapshot_group.setLayout(snapshot_layout)
        content_layout.addWidget(snapshot_group)

        # --- NETWORK DIAGNOSTICS GROUP ---
        network_group = QGroupBox(UI_STRINGS["network_diagnostics_group_title"])
        network_layout = QVBoxLayout()

        check_net_btn = QPushButton(UI_STRINGS["check_internet_button_text"])
        check_net_btn.clicked.connect(self.check_internet_connection)
        network_layout.addWidget(check_net_btn)
        self.buttons.append(check_net_btn)
        network_group.setLayout(network_layout)
        content_layout.addWidget(network_group)

        # --- INFORMATION GROUP ---
        info_group = QGroupBox(UI_STRINGS["info_group_title"])
        info_layout = QHBoxLayout()

        help_btn = QPushButton(UI_STRINGS["help_button_text"])
        help_btn.clicked.connect(self.show_help)
        about_btn = QPushButton(UI_STRINGS["about_button_text"])
        about_btn.clicked.connect(self.show_about)
        info_layout.addWidget(help_btn)
        info_layout.addWidget(about_btn)
        info_group.setLayout(info_layout)
        content_layout.addWidget(info_group)
        self.buttons.extend([help_btn, about_btn])

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        # Output label (outside scroll area so it's always visible)
        self.output = QLabel(UI_STRINGS["initial_status_message"]) # Initial status
        self.output.setStyleSheet("font-weight: bold; padding: 5px; border: 1px solid #ccc; background-color: #f0f0f0;")
        self.output.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.output)

        self.setLayout(main_layout)

    # --- UI STATE MANAGEMENT ---
    def disable_all_buttons(self):
        """Disables all action buttons in the GUI."""
        for btn in self.buttons:
            btn.setEnabled(False)

    def enable_all_buttons(self):
        """Enables all action buttons in the GUI."""
        for btn in self.buttons:
            btn.setEnabled(True)

    # --- CONFIRMATION DIALOG ---
    def _confirm_action(self, title, message):
        """Displays a confirmation dialog for sensitive actions."""
        reply = QMessageBox.question(self, title, message,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    # --- LOGGING FUNCTION ---
    def _log_action(self, action_type, command, status, output=""):
        """Writes an entry to the log file with timestamp and details."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{action_type}] Command: '{command}' | Status: {status}\n"
        if output:
            log_entry += f"Output:\n{output}\n"
        log_entry += "-" * 50 + "\n"

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {e}")

    # --- UI UPDATE SLOTS (THREAD-SAFE) ---
    def update_output(self, message):
        """Updates the main output label with a message."""
        self.output.setText(message)

    def handle_error(self, message):
        """Updates the output label with an error and shows a critical message box."""
        self.output.setText(f"❌ {message}")
        QMessageBox.critical(self, UI_STRINGS["error_dialog_title"], message)

    # --- COMMAND EXECUTION CORE FUNCTION ---
    def _execute_command_in_thread(self, command, action_type="GENERIC_COMMAND", display_name=None, timeout_sec=120):
        """
        Executes a shell command in a separate thread.
        Handles success, failure, timeout, and logs results.
        Shows a progress dialog for potentially long operations.
        """
        self.disable_all_buttons()

        show_progress_dialog = False
        if any(keyword in command for keyword in ["timeshift", "pacman -Syu", "pacman -Scc", "reflector"]):
            show_progress_dialog = True
        
        progress_dialog = None
        if show_progress_dialog:
            progress_dialog = QProgressDialog(
                f"{UI_STRINGS['running_status_prefix']}{display_name if display_name else command.split(' ')[0]}",
                "Cancel", 0, 0, self # "Cancel" button text is not user-facing if hidden
            )
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setCancelButton(None) # Hide cancel button for critical ops
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.show()
            QApplication.processEvents() # Ensure dialog is shown immediately

        def task():
            cmd_to_display = display_name if display_name else command
            self.signals.result.emit(f"{UI_STRINGS['running_status_prefix']}{cmd_to_display}")
            try:
                process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout_sec)
                self.signals.result.emit(UI_STRINGS["success_message"])
                self.signals.log.emit(action_type, command, "SUCCESS", process.stdout)
            except subprocess.TimeoutExpired:
                error_msg = (
                    f"{UI_STRINGS['timeout_error_prefix']}{timeout_sec}"
                    f"{UI_STRINGS['timeout_error_suffix_seconds']}{cmd_to_display}"
                    f"{UI_STRINGS['long_operation_timeout_suffix']}"
                )
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", f"Timeout expired: {command}")
            except subprocess.CalledProcessError as e:
                error_msg = (
                    f"{UI_STRINGS['command_failed_prefix']}{cmd_to_display}"
                    f"{UI_STRINGS['command_failed_suffix_code']}{e.returncode}"
                )
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
            except FileNotFoundError:
                error_msg = (
                    f"{UI_STRINGS['command_not_found_prefix']}{command.split()[0]}"
                    f"{UI_STRINGS['command_not_found_suffix']}"
                )
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
            except Exception as e:
                error_msg = f"{UI_STRINGS['unexpected_error_prefix']}{e}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
            finally:
                if progress_dialog:
                    progress_dialog.close()
                self.signals.finished.emit()

        threading.Thread(target=task).start()

    # --- SPECIFIC COMMAND EXECUTORS ---
    def run_command(self, command):
        """Runs a single command with confirmation for sensitive ones."""
        sensitive_commands = [
            "sudo pacman -Syu --overwrite '*'",
            "sudo pacman -Qqn | xargs sudo pacman -S --noconfirm"
        ]

        if command in sensitive_commands:
            confirmation_message = (
                f"{UI_STRINGS['sensitive_command_confirm_message_prefix']}{command}"
                f"{UI_STRINGS['sensitive_command_confirm_message_suffix']}"
            )
            if not self._confirm_action(UI_STRINGS["sensitive_command_confirm_title"], confirmation_message):
                self.signals.result.emit(UI_STRINGS["sensitive_command_cancelled"])
                self.signals.log.emit("SINGLE_COMMAND", command, "CANCELLED", "User cancelled sensitive command.")
                return
        
        timeout = 300 if "sudo pacman -Syu" in command else 120
        self._execute_command_in_thread(command, action_type="SINGLE_COMMAND", timeout_sec=timeout)

    def run_all_predefined_commands(self):
        """Executes all predefined commands sequentially."""
        confirmation_message = UI_STRINGS["full_auto_fix_confirm_message"]
        if not self._confirm_action(UI_STRINGS["full_auto_fix_confirm_title"], confirmation_message):
            self.signals.result.emit(UI_STRINGS["full_auto_fix_cancelled"])
            self.signals.log.emit("FULL_AUTO_FIX", "All predefined commands", "CANCELLED", "User cancelled Full Auto Fix.")
            return
        
        self.disable_all_buttons()

        progress_dialog = QProgressDialog(
            UI_STRINGS["full_auto_fix_progress_message"],
            "Cancel", 0, len(self.predefined_commands), self
        )
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()

        def task():
            all_successful = True
            current_step = 0
            for name, command in self.predefined_commands.items():
                self.signals.result.emit(f"{UI_STRINGS['running_status_prefix']}{name}")
                progress_dialog.setLabelText(f"{UI_STRINGS['full_auto_fix_progress_message'].split(':')[0]}: {name}")
                progress_dialog.setValue(current_step)
                QApplication.processEvents()
                
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=300)
                    self.signals.log.emit("FULL_AUTO_FIX", command, "SUCCESS", process.stdout)
                except subprocess.TimeoutExpired:
                    self.signals.result.emit(
                        f"❌ {UI_STRINGS['timeout_error_prefix']}'{name}'{UI_STRINGS['full_auto_fix_timeout_check_log']}"
                    )
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Timeout expired for {name}")
                    all_successful = False
                    break
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(
                        f"{UI_STRINGS['full_auto_fix_failed_prefix']}{name}"
                        f"{UI_STRINGS['full_auto_fix_failed_suffix_code']}{e.returncode}"
                        f"{UI_STRINGS['full_auto_fix_timeout_check_log']}"
                    )
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(
                        f"{UI_STRINGS['full_auto_fix_command_not_found_prefix']}{name}"
                        f"{UI_STRINGS['full_auto_fix_command_not_found_suffix']}"
                    )
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Command not found for {name}")
                    all_successful = False
                    break
                current_step += 1
            
            progress_dialog.setValue(len(self.predefined_commands))
            progress_dialog.close()

            if all_successful:
                self.signals.result.emit(UI_STRINGS["full_auto_fix_success"])
            else:
                self.signals.result.emit(UI_STRINGS["full_auto_fix_error_summary"])
            self.signals.finished.emit()

        threading.Thread(target=task).start()

    # --- NEW FEATURE IMPLEMENTATIONS ---

    # 2. Advanced Settings / Custom Commands
    def show_advanced_settings(self):
        """Opens a dialog for users to configure custom shell commands."""
        dialog = AdvancedSettingsDialog(self, self.custom_commands_list)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_commands_list = dialog.custom_commands
            self.signals.result.emit(
                f"{UI_STRINGS['custom_commands_loaded_prefix']}{len(self.custom_commands_list)}"
                f"{UI_STRINGS['custom_commands_loaded_suffix']}"
            )
            self._log_action("SETTINGS", "Update custom commands", "SUCCESS", f"New custom commands: {self.custom_commands_list}")
        else:
            self.signals.result.emit(UI_STRINGS["custom_commands_config_cancelled"])

    def run_custom_commands(self):
        """Executes the custom commands defined by the user."""
        if not self.custom_commands_list:
            QMessageBox.warning(self, UI_STRINGS["no_custom_commands_warning_title"], UI_STRINGS["no_custom_commands_warning_message"])
            self.signals.result.emit(UI_STRINGS["no_custom_commands_status"])
            return
        
        confirmation_message = UI_STRINGS["custom_commands_confirm_message"]
        if not self._confirm_action(UI_STRINGS["custom_commands_confirm_title"], confirmation_message):
            self.signals.result.emit(UI_STRINGS["custom_commands_cancelled"])
            self.signals.log.emit("CUSTOM_COMMANDS", "User-defined commands", "CANCELLED", "User cancelled custom commands execution.")
            return

        self.disable_all_buttons()

        progress_dialog = QProgressDialog(
            UI_STRINGS["custom_commands_progress_message"],
            "Cancel", 0, len(self.custom_commands_list), self
        )
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()

        def task():
            all_successful = True
            current_step = 0
            for i, command in enumerate(self.custom_commands_list):
                self.signals.result.emit(
                    f"{UI_STRINGS['custom_commands_running_prefix']}{i+1}"
                    f"{UI_STRINGS['custom_commands_running_middle']}{len(self.custom_commands_list)}"
                    f"{UI_STRINGS['custom_commands_running_suffix']}{command}"
                )
                progress_dialog.setLabelText(f"{UI_STRINGS['custom_commands_progress_message'].split(':')[0]}: {command}")
                progress_dialog.setValue(current_step)
                QApplication.processEvents()
                
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=120)
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "SUCCESS", process.stdout)
                except subprocess.TimeoutExpired:
                    self.signals.result.emit(
                        f"{UI_STRINGS['custom_commands_timeout_prefix']}{command}"
                        f"{UI_STRINGS['custom_commands_timeout_suffix']}"
                    )
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Timeout expired for {command}")
                    all_successful = False
                    break
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(
                        f"{UI_STRINGS['custom_commands_failed_prefix']}{command}"
                        f"{UI_STRINGS['custom_commands_failed_suffix_code']}{e.returncode}"
                        f"{UI_STRINGS['custom_commands_timeout_suffix']}" # Use timeout suffix for consistency in check log
                    )
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(
                        f"{UI_STRINGS['custom_commands_cmd_not_found_prefix']}{command.split()[0]}"
                        f"{UI_STRINGS['custom_commands_cmd_not_found_suffix']}"
                    )
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Command not found: {command}")
                    all_successful = False
                    break
                current_step += 1
            
            progress_dialog.setValue(len(self.custom_commands_list))
            progress_dialog.close()

            if all_successful:
                self.signals.result.emit(UI_STRINGS["custom_commands_success"])
            else:
                self.signals.result.emit(UI_STRINGS["custom_commands_error_summary"])
            self.signals.finished.emit()
        threading.Thread(target=task).start()


    # 3. Rollback / Timeshift Integration
    def create_timeshift_snapshot(self):
        """
        Initiates the creation of a Timeshift system snapshot.
        Requires Timeshift to be installed.
        """
        confirmation_message = UI_STRINGS["create_snapshot_confirm_message"]
        if not self._confirm_action(UI_STRINGS["create_snapshot_confirm_title"], confirmation_message):
            self.signals.result.emit(UI_STRINGS["create_snapshot_cancelled"])
            self.signals.log.emit("SNAPSHOT_CREATE", "timeshift --create", "CANCELLED", "User cancelled snapshot.")
            return

        self._execute_command_in_thread(
            "sudo timeshift --create",
            action_type="SNAPSHOT_CREATE",
            display_name=UI_STRINGS["create_snapshot_button_text"],
            timeout_sec=600 # Snapshots can take a long time
        )

    def launch_timeshift_gui(self):
        """
        Launches the Timeshift GUI for restoration and other operations.
        Requires Timeshift to be installed.
        """
        self.signals.result.emit(UI_STRINGS["timeshift_gui_launch_progress"])
        self.disable_all_buttons()

        def task():
            try:
                # Use 'pkexec' to prompt for graphical password if not already root
                # This ensures Timeshift GUI opens with necessary permissions
                subprocess.run("pkexec timeshift-launcher", shell=True, check=True, text=True)
                self.signals.result.emit(UI_STRINGS["timeshift_gui_launch_message"])
                self.signals.log.emit("LAUNCH_TIMESHIFT_GUI", "pkexec timeshift-launcher", "SUCCESS", "Timeshift GUI launched.")
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to launch Timeshift GUI. Error: {e.stderr}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit("LAUNCH_TIMESHIFT_GUI", "pkexec timeshift-launcher", "FAILED", error_msg)
            except FileNotFoundError:
                error_msg = "Timeshift or pkexec command not found. Please ensure Timeshift is installed."
                self.signals.error.emit(error_msg)
                self.signals.log.emit("LAUNCH_TIMESHIFT_GUI", "pkexec timeshift-launcher", "FAILED", error_msg)
            finally:
                self.signals.finished.emit()

        threading.Thread(target=task).start()


    # 4. Network Diagnostics
    def check_internet_connection(self):
        """
        Checks internet connectivity by attempting to resolve a domain
        and ping a well-known IP address.
        """
        self.signals.result.emit(UI_STRINGS["check_internet_progress"])
        self.disable_all_buttons()

        def task():
            try:
                # Try to resolve a common domain name
                socket.gethostbyname("www.google.com")
                # Try to ping a reliable server (Google's public DNS)
                subprocess.run(["ping", "-c", "1", "8.8.8.8"], check=True, capture_output=True, text=True, timeout=10)
                self.signals.result.emit(UI_STRINGS["internet_connected"])
                self.signals.log.emit("NETWORK_DIAGNOSTICS", "Internet Check", "SUCCESS", "Connected")
            except (socket.gaierror, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                self.signals.result.emit(UI_STRINGS["internet_not_connected"])
                self.signals.log.emit("NETWORK_DIAGNOSTICS", "Internet Check", "FAILED", f"Error: {e}")
            except Exception as e:
                self.signals.result.emit(f"{UI_STRINGS['internet_check_error']}{e}")
                self.signals.log.emit("NETWORK_DIAGNOSTICS", "Internet Check", "FAILED", f"Unexpected error: {e}")
            finally:
                self.signals.finished.emit()

        threading.Thread(target=task).start()

    # --- HELP AND ABOUT DIALOGS ---
    def show_help(self):
        """Displays help information about the application."""
        QMessageBox.information(self, UI_STRINGS["help_title"], UI_STRINGS["help_content"])

    def show_about(self):
        """Displays information about the application and Linus Torvalds tribute."""
        QMessageBox.information(self, UI_STRINGS["about_title"], UI_STRINGS["about_content"])


# --- INITIAL COMMANDS DEFINITION ---
COMMANDS = {
    "Repair Database (Pacman)": "sudo pacman -D --asdeps $(pacman -Qdtq)",
    "Clear Package Cache": "sudo pacman -Scc --noconfirm", # Added --noconfirm for non-interactive
    "Fix Corrupted Packages": "sudo pacman -Syu --overwrite '*' --noconfirm", # Added --noconfirm
    "Update System": "sudo pacman -Syu --noconfirm", # Added --noconfirm
    "Refresh Mirrorlist": "sudo reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist",
    "Reinstall Broken Packages": "sudo pacman -Qqn | xargs sudo pacman -S --noconfirm", # Added --noconfirm
    "Remove Orphan Packages": "sudo pacman -Rns $(pacman -Qtdq --unrequired --unneeded 2>/dev/null) --noconfirm", # Added --noconfirm
    "Clean Journal Logs": "sudo journalctl --vacuum-time=1w", # Clean logs older than 1 week
    "Rebuild Initramfs": "sudo mkinitcpio -P", # Rebuild initramfs for all kernels
    "Check Filesystem Errors": "sudo fsck -Af", # Check all filesystems (requires unmounting, which might be tricky in live system)
    "Resync Pacman Database": "sudo pacman -Syy --noconfirm" # Added --noconfirm
}


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFixApp()
    window.show()
    sys.exit(app.exec_())
