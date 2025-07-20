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
    QScrollArea,  # Added for scrollability
    QGroupBox     # Added for grouping buttons
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject


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
        self.setWindowTitle("Advanced Settings - Custom Commands")
        self.setGeometry(100, 100, 600, 450) # Increased size for better usability

        layout = QVBoxLayout()

        description_label = QLabel(
            "Enter custom Pacman or system commands below, one command per line.\n"
            "These commands will be executed when 'Run Custom Commands' button is pressed.\n"
            "Be cautious with custom commands as they are executed with root privileges."
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
        self.setWindowTitle("Helwan Linux - NetFix Tool")
        # Removed setFixedSize to allow resizing
        self.setMinimumSize(500, 750) # Set a minimum size, but allow user to resize beyond this

        # Initialize WorkerSignals for thread-safe updates
        self.signals = WorkerSignals()
        self.signals.result.connect(self.update_output)
        self.signals.error.connect(self.handle_error)
        self.signals.log.connect(self._log_action)
        self.signals.finished.connect(self.enable_all_buttons) # Re-enable buttons after task finishes

        # Log file path
        self.log_dir = os.path.expanduser("~/.helwanlinux")
        os.makedirs(self.log_dir, exist_ok=True) # Ensure directory exists
        self.log_file_path = os.path.join(self.log_dir, "netfix_log.txt")

        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Main layout for the widget
        main_layout = QVBoxLayout(self)

        # Create a scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True) # Make scroll area resize its widget
        
        # Widget to hold all contents inside the scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10) # Add some spacing between elements

        self.buttons = [] # List to keep track of all QPushButton widgets for enabling/disabling

        # --- PREDEFINED COMMANDS GROUP ---
        predefined_group = QGroupBox("Predefined Fixes")
        predefined_layout = QVBoxLayout()
        self.predefined_commands = COMMANDS
        for label, cmd in self.predefined_commands.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, command=cmd: self.run_command(command))
            predefined_layout.addWidget(btn)
            self.buttons.append(btn)
        predefined_group.setLayout(predefined_layout)
        content_layout.addWidget(predefined_group)

        # Full auto fix button (outside groupbox for emphasis)
        full_fix = QPushButton("Full Auto Fix (All Predefined Commands)")
        full_fix.clicked.connect(self.run_all_predefined_commands)
        full_fix.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;") # Green color
        content_layout.addWidget(full_fix)
        self.buttons.append(full_fix)

        # --- ADVANCED TOOLS GROUP ---
        advanced_group = QGroupBox("Advanced Tools")
        advanced_layout = QVBoxLayout()
        self.custom_commands_list = [] # To store commands from advanced settings

        advanced_settings_btn = QPushButton("Configure Custom Commands")
        advanced_settings_btn.clicked.connect(self.show_advanced_settings)
        advanced_layout.addWidget(advanced_settings_btn)
        self.buttons.append(advanced_settings_btn)
        
        run_custom_btn = QPushButton("Run Custom Commands")
        run_custom_btn.clicked.connect(self.run_custom_commands)
        run_custom_btn.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;") # Yellow color
        advanced_layout.addWidget(run_custom_btn)
        self.buttons.append(run_custom_btn)
        advanced_group.setLayout(advanced_layout)
        content_layout.addWidget(advanced_group)

        # --- SYSTEM SNAPSHOTS GROUP ---
        snapshot_group = QGroupBox("System Snapshots (Timeshift)")
        snapshot_layout = QVBoxLayout()

        create_snapshot_btn = QPushButton("Create System Snapshot")
        create_snapshot_btn.clicked.connect(self.create_timeshift_snapshot)
        snapshot_layout.addWidget(create_snapshot_btn)
        self.buttons.append(create_snapshot_btn)

        launch_timeshift_gui_btn = QPushButton("Launch Timeshift GUI (for Restore)")
        launch_timeshift_gui_btn.clicked.connect(self.launch_timeshift_gui)
        snapshot_layout.addWidget(launch_timeshift_gui_btn)
        self.buttons.append(launch_timeshift_gui_btn)
        snapshot_group.setLayout(snapshot_layout)
        content_layout.addWidget(snapshot_group)

        # --- NETWORK DIAGNOSTICS GROUP ---
        network_group = QGroupBox("Network Diagnostics")
        network_layout = QVBoxLayout()

        check_net_btn = QPushButton("Check Internet Connection")
        check_net_btn.clicked.connect(self.check_internet_connection)
        network_layout.addWidget(check_net_btn)
        self.buttons.append(check_net_btn)
        network_group.setLayout(network_layout)
        content_layout.addWidget(network_group)

        # --- INFORMATION GROUP ---
        info_group = QGroupBox("Information")
        info_layout = QHBoxLayout()

        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self.show_help)
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)
        info_layout.addWidget(help_btn)
        info_layout.addWidget(about_btn)
        info_group.setLayout(info_layout)
        content_layout.addWidget(info_group)
        self.buttons.extend([help_btn, about_btn])

        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area) # Add scroll area to the main layout

        # Output label (outside scroll area so it's always visible)
        self.output = QLabel("Ready.")
        self.output.setStyleSheet("font-weight: bold; padding: 5px; border: 1px solid #ccc; background-color: #f0f0f0;")
        self.output.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.output)

        self.setLayout(main_layout) # Set the main layout for the window

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
        log_entry += "-" * 50 + "\n" # Separator

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            # Fallback if logging to file fails
            print(f"Error writing to log file: {e}")

    # --- UI UPDATE SLOTS (THREAD-SAFE) ---
    def update_output(self, message):
        """Updates the main output label with a message."""
        self.output.setText(message)

    def handle_error(self, message):
        """Updates the output label with an error and shows a critical message box."""
        self.output.setText(f"❌ {message}")
        QMessageBox.critical(self, "Error", message)

    # --- COMMAND EXECUTION CORE FUNCTION ---
    def _execute_command_in_thread(self, command, action_type="GENERIC_COMMAND", display_name=None, timeout_sec=120):
        """
        Executes a shell command in a separate thread.
        Handles success, failure, timeout, and logs results.
        Shows a progress dialog for potentially long operations.
        """
        self.disable_all_buttons() # Disable buttons while a command is running

        # Determine if a progress dialog is needed
        show_progress_dialog = False
        if any(keyword in command for keyword in ["timeshift", "pacman -Syu", "pacman -Scc", "reflector"]):
            show_progress_dialog = True
        
        progress_dialog = None
        if show_progress_dialog:
            progress_dialog = QProgressDialog(f"الرجاء الانتظار: {display_name if display_name else command.split(' ')[0]}", "إلغاء", 0, 0, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setCancelButton(None) # Can add cancel functionality if needed
            progress_dialog.setMinimumDuration(0) # Show immediately
            progress_dialog.setValue(0)
            progress_dialog.show()
            QApplication.processEvents() # Update GUI to show dialog

        def task():
            cmd_to_display = display_name if display_name else command
            self.signals.result.emit(f"Running: {cmd_to_display}")
            try:
                # capture_output=True and text=True to get stdout/stderr for logging
                process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout_sec)
                self.signals.result.emit("✅ Done.")
                self.signals.log.emit(action_type, command, "SUCCESS", process.stdout)
            except subprocess.TimeoutExpired:
                error_msg = f"Command timed out after {timeout_sec} seconds: {cmd_to_display}. It took too long to complete."
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", f"Timeout expired: {command}")
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed: {cmd_to_display}. Error code: {e.returncode}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
            except FileNotFoundError:
                error_msg = f"Command '{command.split()[0]}' not found. Make sure it's installed and in your PATH."
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                self.signals.error.emit(error_msg)
                self.signals.log.emit(action_type, command, "FAILED", error_msg)
            finally:
                if progress_dialog:
                    progress_dialog.close()
                self.signals.finished.emit() # Signal that the task is complete

        threading.Thread(target=task).start()

    # --- SPECIFIC COMMAND EXECUTORS ---
    def run_command(self, command):
        # Sensitive commands that require confirmation
        sensitive_commands = [
            "sudo pacman -Syu --overwrite '*'",
            "sudo pacman -Qqn | xargs sudo pacman -S --noconfirm" # Reinstalling packages
        ]

        if command in sensitive_commands:
            confirmation_message = (
                f"أنت على وشك تنفيذ أمر حساس:\n\n{command}\n\n"
                "هذا الأمر قد يسبب مشاكل في نظامك إذا لم يتم استخدامه بشكل صحيح. هل أنت متأكد من المتابعة؟"
            )
            if not self._confirm_action("تأكيد أمر حساس", confirmation_message):
                self.signals.result.emit("تم إلغاء الأمر الحساس بواسطة المستخدم.")
                self.signals.log.emit("SINGLE_COMMAND", command, "CANCELLED", "User cancelled sensitive command.")
                return # Stop execution if user doesn't confirm
        
        # Use longer timeout for operations like system update
        timeout = 300 if "sudo pacman -Syu" in command else 120
        self._execute_command_in_thread(command, action_type="SINGLE_COMMAND", timeout_sec=timeout)

    def run_all_predefined_commands(self):
        confirmation_message = (
            "أنت على وشك تشغيل 'Full Auto Fix'. هذا سيقوم بتنفيذ عدة أوامر حساسة "
            "مثل تحديث وإعادة تثبيت الحزم. قد يستغرق هذا بعض الوقت. هل أنت متأكد من المتابعة؟"
        )
        if not self._confirm_action("تأكيد 'Full Auto Fix'", confirmation_message):
            self.signals.result.emit("تم إلغاء 'Full Auto Fix' بواسطة المستخدم.")
            self.signals.log.emit("FULL_AUTO_FIX", "All predefined commands", "CANCELLED", "User cancelled Full Auto Fix.")
            return
        
        self.disable_all_buttons() # Disable buttons while a command is running

        progress_dialog = QProgressDialog("الرجاء الانتظار: Full Auto Fix...", "إلغاء", 0, len(self.predefined_commands), self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setCancelButton(None) # No cancel for this sequence
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.show()
        QApplication.processEvents()

        def task():
            all_successful = True
            current_step = 0
            for name, command in self.predefined_commands.items():
                self.signals.result.emit(f"Running: {name}")
                progress_dialog.setLabelText(f"الرجاء الانتظار: {name}")
                progress_dialog.setValue(current_step)
                QApplication.processEvents() # Update progress dialog
                
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=300) # Longer timeout for full fix
                    self.signals.log.emit("FULL_AUTO_FIX", command, "SUCCESS", process.stdout)
                except subprocess.TimeoutExpired:
                    self.signals.result.emit(f"❌ Command '{name}' timed out. Check log.")
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Timeout expired for {name}")
                    all_successful = False
                    break
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(f"❌ Failed at {name}. Error code: {e.returncode}. Check log.")
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(f"❌ Command for '{name}' not found. Check log.")
                    self.signals.log.emit("FULL_AUTO_FIX", command, "FAILED", f"Command not found for {name}")
                    all_successful = False
                    break
                current_step += 1
            
            progress_dialog.setValue(len(self.predefined_commands)) # Set to max
            progress_dialog.close()

            if all_successful:
                self.signals.result.emit("✅ All predefined tasks completed successfully.")
            else:
                self.signals.result.emit("❌ Full Auto Fix completed with errors. Check log for details.")
            self.signals.finished.emit() # Signal that the task is complete

        threading.Thread(target=task).start()

    # --- NEW FEATURE IMPLEMENTATIONS ---

    # 2. Advanced Settings / Custom Commands
    def show_advanced_settings(self):
        """Opens a dialog for users to configure custom shell commands."""
        dialog = AdvancedSettingsDialog(self, self.custom_commands_list)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_commands_list = dialog.custom_commands
            self.signals.result.emit(f"Loaded {len(self.custom_commands_list)} custom commands.")
            self._log_action("SETTINGS", "Update custom commands", "SUCCESS", f"New custom commands: {self.custom_commands_list}")
        else:
            self.signals.result.emit("Custom command configuration cancelled.")

    def run_custom_commands(self):
        """Executes the custom commands defined by the user."""
        if not self.custom_commands_list:
            QMessageBox.warning(self, "No Custom Commands", "Please configure custom commands first in Advanced Settings.")
            self.signals.result.emit("No custom commands to run.")
            return
        
        confirmation_message = (
            "أنت على وشك تشغيل الأوامر المخصصة التي قمت بتحديدها.\n"
            "هذه الأوامر سيتم تنفيذها بامتيازات الجذر (sudo). هل أنت متأكد من المتابعة؟"
        )
        if not self._confirm_action("تأكيد الأوامر المخصصة", confirmation_message):
            self.signals.result.emit("تم إلغاء تشغيل الأوامر المخصصة.")
            self.signals.log.emit("CUSTOM_COMMANDS", "User-defined commands", "CANCELLED", "User cancelled custom commands execution.")
            return

        self.disable_all_buttons() # Disable buttons while running custom commands

        progress_dialog = QProgressDialog("الرجاء الانتظار: تشغيل الأوامر المخصصة...", "إلغاء", 0, len(self.custom_commands_list), self)
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
                self.signals.result.emit(f"Running custom command {i+1}/{len(self.custom_commands_list)}: {command}")
                progress_dialog.setLabelText(f"الرجاء الانتظار: {command}")
                progress_dialog.setValue(current_step)
                QApplication.processEvents()
                
                try:
                    process = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=120)
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "SUCCESS", process.stdout)
                except subprocess.TimeoutExpired:
                    self.signals.result.emit(f"❌ Custom command timed out: {command}. Check log.")
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Timeout expired for {command}")
                    all_successful = False
                    break
                except subprocess.CalledProcessError as e:
                    self.signals.result.emit(f"❌ Custom command failed: {command}. Error code: {e.returncode}. Check log.")
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Error: {e.stderr}\nStdout: {e.stdout}")
                    all_successful = False
                    break
                except FileNotFoundError:
                    self.signals.result.emit(f"❌ Custom command '{command.split()[0]}' not found. Check log.")
                    self.signals.log.emit("CUSTOM_COMMANDS", command, "FAILED", f"Command not found: {command}")
                    all_successful = False
                    break
                current_step += 1
            
            progress_dialog.setValue(len(self.custom_commands_list))
            progress_dialog.close()

            if all_successful:
                self.signals.result.emit("✅ All custom commands completed successfully.")
            else:
                self.signals.result.emit("❌ Custom commands completed with errors. Check log for details.")
            self.signals.finished.emit()
        threading.Thread(target=task).start()


    # 3. Rollback / Timeshift Integration
    def create_timeshift_snapshot(self):
        """
        Initiates the creation of a Timeshift system snapshot.
        Requires Timeshift to be installed.
        """
        confirmation_message = (
            "أنت على وشك إنشاء لقطة لنظامك (System Snapshot) باستخدام Timeshift.\n"
            "هذا الإجراء قد يستغرق بعض الوقت ويعتمد على حجم نظامك. هل أنت متأكد من المتابعة؟"
        )
        if not self._confirm_action("تأكيد إنشاء لقطة", confirmation_message):
            self.signals.result.emit("تم إلغاء إنشاء اللقطة بواسطة المستخدم.")
            self.signals.log.emit("SNAPSHOT_CREATE", "timeshift --create", "CANCELLED", "User cancelled snapshot creation.")
            return

        self._execute_command_in_thread(
            "sudo timeshift --create --comments 'NetFix pre-action snapshot' --yes",
            action_type="SNAPSHOT_CREATE",
            display_name="Create System Snapshot (Timeshift)",
            timeout_sec=600 # Allow more time for snapshot creation (10 minutes)
        )
        self.signals.result.emit("Creating Timeshift snapshot... This may take a while. Please do not close the app.")

    def launch_timeshift_gui(self):
        """
        Launches the Timeshift GUI for managing and restoring snapshots.
        Requires Timeshift to be installed and pkexec for privilege escalation.
        """
        self._execute_command_in_thread(
            "pkexec timeshift-launcher", # pkexec prompts for password graphically
            action_type="TIMESHAFT_GUI_LAUNCH",
            display_name="Launch Timeshift GUI",
            timeout_sec=30 # GUI launch should be quick
        )

    # 4. Check Internet Connection
    def check_internet_connection(self):
        """
        Checks internet connectivity by attempting DNS resolution and a ping test.
        """
        self.disable_all_buttons() # Disable buttons during check
        
        def task():
            self.signals.result.emit("Checking internet connection...")
            try:
                # Try to resolve a common domain like google.com (DNS test)
                socket.gethostbyname("www.google.com")
                # Then try to ping it (network connectivity test)
                # Using '-W 2' for 2 second timeout per ping, '-c 4' for 4 pings
                # Overall timeout for subprocess.run
                subprocess.run("ping -c 4 -W 2 www.google.com", shell=True, check=True, capture_output=True, text=True, timeout=15)
                self.signals.result.emit("✅ Internet connection is active.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "SUCCESS", "Internet connection is active.")
            except socket.gaierror:
                self.signals.error.emit("❌ DNS resolution failed. No internet connection or DNS issue.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", "DNS resolution failed.")
            except subprocess.TimeoutExpired:
                self.signals.error.emit("❌ Ping test timed out. Network slow or blocked by firewall.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", "Ping test timed out.")
            except subprocess.CalledProcessError as e:
                self.signals.error.emit(f"❌ Ping test failed. No internet connection, firewall blocking, or network misconfiguration. Error: {e.stderr}")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", f"Ping test failed. Error: {e.stderr}")
            except FileNotFoundError:
                self.signals.error.emit("❌ 'ping' command not found. Please ensure network utilities are installed.")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", "'ping' command not found.")
            except Exception as e:
                self.signals.error.emit(f"An unexpected error occurred during network check: {e}")
                self.signals.log.emit("NETWORK_CHECK", "Ping google.com", "FAILED", f"Unexpected error: {e}")
            finally:
                self.signals.finished.emit() # Re-enable buttons

        threading.Thread(target=task).start()


    # --- EXISTING INFO DIALOGS (Help & About) ---
    def show_help(self):
        help_msg = (
            "This tool provides quick fixes and system management for Arch-based systems:\n\n"
            "Predefined Commands:\n"
            "- Repair Database: Clean unused packages.\n"
            "- Clear Cache: Remove old packages.\n"
            "- Fix Corrupted Packages: Resolve overwrite errors.\n"
            "- Update System: Sync system and update packages.\n"
            "- Refresh Mirrors: Get best and fastest Arch Linux package servers.\n"
            "- Reinstall Broken Packages: Fix missing or broken package files.\n"
            "- Full Auto Fix: Runs all above predefined commands sequentially.\n\n"
            "Advanced Tools:\n"
            "- Configure Custom Commands: Define your own sequence of shell commands.\n"
            "- Run Custom Commands: Execute the custom commands you defined. (Use with caution!)\n\n"
            "System Snapshots (Timeshift):\n"
            "- Create System Snapshot: Creates a restore point for your system using Timeshift.\n"
            "- Launch Timeshift GUI: Opens Timeshift application to manage/restore previous snapshots.\n\n"
            "Network Diagnostics:\n"
            "- Check Internet Connection: Tests your network connectivity by checking DNS and ping.\n\n"
            "All actions are logged to ~/.helwanlinux/netfix_log.txt for review."
        )
        QMessageBox.information(self, "Help", help_msg)

    def show_about(self):
        about_text = (
            "Helwan Linux NetFix GUI\n"
            "Version 1.0 (with Advanced Features)\n"
            "By SMA Coding / Helwan Linux Team\n"
            "Saeed Badrelden : helwanlinux@gmail.com\n\n"
            "Designed to simplify system maintenance and troubleshooting for Helwan Linux.\n"
            "This tool is open source and contributions are welcome."
        )
        QMessageBox.information(self, "About", about_text)


# --- INITIAL COMMANDS DEFINITION ---
COMMANDS = {
    "Repair Database (Pacman)": "sudo pacman -D --asdeps $(pacman -Qdtq)",
    "Clear Package Cache": "sudo pacman -Scc --noconfirm", # Added --noconfirm for non-interactive
    "Fix Corrupted Packages": "sudo pacman -Syu --overwrite '*' --noconfirm", # Added --noconfirm
    "Update System": "sudo pacman -Syu --noconfirm", # Added --noconfirm
    "Refresh Mirrorlist": "sudo reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist",
    "Reinstall Broken Packages": "sudo pacman -Qqn | xargs sudo pacman -S --noconfirm", # Added --noconfirm
}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFixApp()
    window.show()
    sys.exit(app.exec_())
