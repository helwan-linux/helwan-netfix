# hel_netfix_gui_qt.py
# SMA Coding - Helwan Linux Official Tool - Qt Edition

import sys
import subprocess
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QMessageBox, QHBoxLayout, QTextEdit, QProgressBar
)
from PyQt5.QtGui import QIcon, QTextCursor, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# Use pkexec instead of sudo directly to request graphical privileges.
# Note: pkexec usually requires correct Polkit policies to work smoothly.
# If pkexec doesn't work, you might need to install a tool like `lxqt-policykit` or `gnome-polkit`
# or use an alternative like gksu/kdesu (if installed) or run the script itself with sudo.
COMMANDS = {
    "Repair Database": "pkexec pacman -D --asdeps $(pacman -Qdtq)",
    "Clear Cache": "pkexec pacman -Scc --noconfirm", # Added --noconfirm
    "Fix Corrupted Packages": "pkexec pacman -Syu --overwrite '*' --noconfirm", # Added --noconfirm
    "Update System": "pkexec pacman -Syu --noconfirm", # Added --noconfirm
	#"Refresh Mirrors": "pkexec bash -c \"reflector --latest 10 --protocol https --sort rate --connection-timeout 20 --country Germany,France,Italy,Turkey,Sweden,Netherlands --save /etc/pacman.d/mirrorlist\"",    #"Refresh Mirrors": "pkexec bash -c \"reflector --latest 10 --protocol https --sort rate --save /etc/pacman.d/mirrorlist\"",
    "Refresh Mirrors": "pkexec pacman -Syy --noconfirm",
    #"Reinstall Broken Packages": "pkexec bash -c \"pacman -S --noconfirm $(pacman -Qqn)\"",
    #"Test Output": "ls -l /", # New command for testing output
}

# Intermediate class for sending signals from a Thread to the GUI Thread
class WorkerSignals(QObject):
    output_appended = pyqtSignal(str) # Signal to append text to the output area (GUI)
    command_started = pyqtSignal(str, QPushButton) # Signal for a command start (command name and button)
    command_finished = pyqtSignal(str, QPushButton, bool) # Signal for a command finish (original name, button, success status)
    full_fix_started = pyqtSignal() # Signal for the start of full auto fix
    full_fix_finished = pyqtSignal(bool) # Signal for the end of full auto fix (success status)

class NetFixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helwan Linux - NetFix Tool")
        self.setFixedSize(600, 550) # Increased window size to accommodate output area and progress bar

        # Initialize signal object
        self.signals = WorkerSignals()
        # Connect output_appended signal to the slot that updates QTextEdit
        self.signals.output_appended.connect(self._append_output_to_text_edit)
        self.signals.command_started.connect(self._on_command_started)
        self.signals.command_finished.connect(self._on_command_finished)
        self.signals.full_fix_started.connect(self._on_full_fix_started)
        self.signals.full_fix_finished.connect(self._on_full_fix_finished)

        # Load icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Warning message if icon not found
            print(f"Warning: Icon file not found at {icon_path}")

        layout = QVBoxLayout()

        self.buttons = {} # Dictionary to store buttons by their original labels
        # Create buttons for commands
        for label in COMMANDS:
            btn = QPushButton(label)
            # Pass the button object itself to the run_command function
            btn.clicked.connect(lambda _, cmd=COMMANDS[label], lbl=label, button=btn: self.run_command(cmd, lbl, button))
            layout.addWidget(btn)
            self.buttons[label] = btn # Store the button

        # Full auto fix button
        self.full_fix_btn = QPushButton("Full Auto Fix")
        self.full_fix_btn.clicked.connect(self.run_all_commands)
        layout.addWidget(self.full_fix_btn)

        # Help & About buttons
        hbox = QHBoxLayout()
        self.help_btn = QPushButton("Help")
        self.help_btn.clicked.connect(self.show_help)
        self.about_btn = QPushButton("About")
        self.about_btn.clicked.connect(self.show_about)
        hbox.addWidget(self.help_btn)
        hbox.addWidget(self.about_btn)
        layout.addLayout(hbox)

        # Progress Bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setTextVisible(False) # Hide percentage text
        self.progressBar.setRange(0, 0) # Set progress bar to "indeterminate" mode
        self.progressBar.hide() # Hide progress bar initially
        layout.addWidget(self.progressBar)

        # Output TextEdit for detailed output
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setText("Ready.")
        layout.addWidget(self.output_text_edit)

        self.setLayout(layout)

    # Function to control enabling/disabling of all main UI buttons
    def set_ui_enabled(self, enabled):
        for btn_name, btn_obj in self.buttons.items():
            btn_obj.setEnabled(enabled)
        self.full_fix_btn.setEnabled(enabled)
        self.help_btn.setEnabled(enabled)
        self.about_btn.setEnabled(enabled)
        if enabled:
            QApplication.restoreOverrideCursor() # Restore default mouse cursor
        else:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor)) # Change mouse cursor to wait cursor

    # This function is the slot called via the signal to append output
    def _append_output_to_text_edit(self, text):
        self.output_text_edit.append(text)
        # Scroll to the bottom automatically
        self.output_text_edit.verticalScrollBar().setValue(self.output_text_edit.verticalScrollBar().maximum())

    def _on_command_started(self, command_name, button):
        self.set_ui_enabled(False) # Disable the entire UI
        button.setText(f"Processing: {command_name}...")
        button.setEnabled(False) # Explicitly disable the button itself for confirmation
        self.progressBar.show() # Show the progress bar

    def _on_command_finished(self, original_name, button, success):
        button.setText(original_name) # Restore original button text
        self.set_ui_enabled(True) # Re-enable the entire UI
        self.progressBar.hide() # Hide the progress bar
        # Add a success/failure message to GUI output
        if success:
            self._append_output_to_text_edit("✅ Command finished successfully.")
        else:
            self._append_output_to_text_edit("❌ Command failed.")

    def _on_full_fix_started(self):
        self.set_ui_enabled(False)
        self.full_fix_btn.setText("Running Full Fix...")
        self.full_fix_btn.setEnabled(False)
        self.progressBar.show() # Show the progress bar

    def _on_full_fix_finished(self, success):
        self.full_fix_btn.setText("Full Auto Fix")
        self.set_ui_enabled(True)
        self.progressBar.hide() # Hide the progress bar
        if success:
            self._append_output_to_text_edit("\n✅ All Full Auto Fix tasks completed successfully.")
        else:
            self._append_output_to_text_edit("\n❌ Full Auto Fix aborted due to an error.")


    def run_command(self, command, name="", button=None):
        def task():
            self.signals.command_started.emit(name, button) # Emit signal that command has started
            self.signals.output_appended.emit(f"\n--- Running: {name if name else command} ---")
            print(f"\n--- Running: {name if name else command} ---") # Print to terminal

            success = False
            try:
                # Using Popen to get live output
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

                # Read stdout line by line
                for line in iter(process.stdout.readline, ''):
                    self.signals.output_appended.emit(line.strip())
                    print(line.strip()) # Print to terminal

                # Read stderr line by line (after stdout is exhausted or if stderr is used)
                for line in iter(process.stderr.readline, ''):
                    self.signals.output_appended.emit(f"ERROR: {line.strip()}")
                    print(f"ERROR: {line.strip()}") # Print to terminal

                process.stdout.close()
                process.stderr.close()
                return_code = process.wait() # Wait for the process to terminate

                if return_code != 0:
                    self.signals.output_appended.emit(f"❌ Command exited with error code: {return_code}")
                    print(f"❌ Command exited with error code: {return_code}")
                    success = False
                else:
                    success = True

            except FileNotFoundError:
                self.signals.output_appended.emit("❌ Error: Command or a part of it not found. Make sure 'pkexec' and other tools are installed and in PATH.")
                print("❌ Error: Command or a part of it not found. Make sure 'pkexec' and other tools are installed in PATH.")
                success = False
            except Exception as e: # Catch any other unexpected errors
                self.signals.output_appended.emit(f"❌ An unexpected error occurred: {e}")
                print(f"❌ An unexpected error occurred: {e}")
                success = False

            self.signals.output_appended.emit("--- Command Finished ---")
            print("--- Command Finished ---")
            self.signals.command_finished.emit(name, button, success) # Emit signal that command has finished with success status
        threading.Thread(target=task).start()

    def run_all_commands(self):
        def task():
            self.signals.full_fix_started.emit() # Emit signal that full fix has started
            self.signals.output_appended.emit("\n--- Starting Full Auto Fix ---")
            print("\n--- Starting Full Auto Fix ---")

            # Store original texts of buttons to restore them later
            original_button_texts = {name: self.buttons[name].text() for name in COMMANDS}
            all_commands_successful = True

            for name, command in COMMANDS.items():
                current_button = self.buttons[name]
                self.signals.output_appended.emit(f"\nRunning: {name}")
                print(f"\nRunning: {name}")
                # Update individual button status (even during full fix)
                self.signals.command_started.emit(name, current_button) # This will hide progress bar if it's already shown, then show it again.

                command_success = False
                try:
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

                    for line in iter(process.stdout.readline, ''):
                        self.signals.output_appended.emit(line.strip())
                        print(line.strip())

                    for line in iter(process.stderr.readline, ''):
                        self.signals.output_appended.emit(f"ERROR: {line.strip()}")
                        print(f"ERROR: {line.strip()}")

                    process.stdout.close()
                    process.stderr.close()
                    return_code = process.wait()

                    if return_code != 0:
                        self.signals.output_appended.emit(f"❌ Command exited with error code: {return_code}")
                        print(f"❌ Command exited with error code: {return_code}")
                        command_success = False
                    else:
                        command_success = True

                except FileNotFoundError:
                    self.signals.output_appended.emit(f"❌ Error: Command '{name}' or a part of it not found. Check installation.")
                    print(f"❌ Error: Command '{name}' or a part of it not found. Check installation.")
                    command_success = False
                except Exception as e:
                    self.signals.output_appended.emit(f"❌ An unexpected error occurred during {name}: {e}")
                    print(f"❌ An unexpected error occurred during {name}: {e}")
                    command_success = False

                if not command_success:
                    all_commands_successful = False
                    self.signals.output_appended.emit(f"--- Full Auto Fix Aborted due to {name} failure ---")
                    print(f"--- Full Auto Fix Aborted due to {name} failure ---")
                    # Restore button text and hide progress bar if failed here
                    self.signals.command_finished.emit(original_button_texts[name], current_button, command_success)
                    self.signals.full_fix_finished.emit(all_commands_successful) # Signal that full fix has finished (with failure)
                    return

                # Restore button text after each successful command (for visibility during Full Fix)
                self.signals.command_finished.emit(original_button_texts[name], current_button, command_success)


            self.signals.output_appended.emit("\n✅ All Full Auto Fix tasks completed successfully.")
            print("\n✅ All Full Auto Fix tasks completed successfully.")
            self.signals.output_appended.emit("--- Full Auto Fix Finished ---")
            print("--- Full Auto Fix Finished ---")
            self.signals.full_fix_finished.emit(all_commands_successful) # Signal that full fix has finished (with success)
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
