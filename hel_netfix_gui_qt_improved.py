# hel_netfix_gui_qt_improved.py
# SMA Coding - Helwan Linux Official Tool - Qt Edition (Improved)

import sys
import subprocess
import threading
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QMessageBox, QHBoxLayout, QTextEdit, QProgressBar
)
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, pyqtSignal, QObject

# ====================================================================
# تم تغيير بنية الأوامر لتقليل الاعتماد على shell=True
# تم استخدام قوائم (lists) بدلاً من سلاسل (strings) حيث أمكن
# ====================================================================
COMMANDS = {
    # الأمر المعقد (Repair Database): يتم تنفيذه على مرحلتين لتجنب shell=True
    "Repair Database": {
        "command": ["pkexec", "pacman", "-D", "--asdeps"],
        "pre_command": ["pacman", "-Qdtq"], # الأمر الذي يوفر المدخلات
        "desc": "Cleaning orphaned packages (pacman -D --asdeps $(pacman -Qdtq))"
    },
    # الأوامر البسيطة: استخدام قائمة بدلاً من سلسلة
    "Clear Cache": {
        "command": ["pkexec", "pacman", "-Scc", "--noconfirm"],
        "desc": "Clearing all cached packages."
    },
    "Fix Corrupted Packages": {
        "command": ["pkexec", "pacman", "-Syu", "--overwrite", "*", "--noconfirm"],
        "desc": "Full update and fixing file conflicts."
    },
    "Update System": {
        "command": ["pkexec", "pacman", "-Syu", "--noconfirm"],
        "desc": "Synchronizing and updating the entire system."
    },
    "Refresh Mirrors": {
        "command": ["pkexec", "pacman", "-Syy", "--noconfirm"],
        "desc": "Forcing database resynchronization."
    },
}

# Intermediate class for sending signals from a Thread to the GUI Thread
class WorkerSignals(QObject):
    output_appended = pyqtSignal(str)
    command_started = pyqtSignal(str, QPushButton)
    command_finished = pyqtSignal(str, QPushButton, bool)
    full_fix_started = pyqtSignal()
    full_fix_step_update = pyqtSignal(str, QPushButton) # جديد: لتحديث خطوة أثناء Full Fix
    full_fix_finished = pyqtSignal(bool)

class NetFixApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Helwan Linux - NetFix Tool (Improved)")
        self.setFixedSize(600, 550)

        self.signals = WorkerSignals()
        self.signals.output_appended.connect(self._append_output_to_text_edit)
        self.signals.command_started.connect(self._on_command_started)
        self.signals.command_finished.connect(self._on_command_finished)
        self.signals.full_fix_started.connect(self._on_full_fix_started)
        self.signals.full_fix_step_update.connect(self._on_full_fix_step_update) # جديد
        self.signals.full_fix_finished.connect(self._on_full_fix_finished)

        self.initialize_ui()

    def initialize_ui(self):
        # Load icon (as before)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netfix.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}")

        layout = QVBoxLayout()
        self.buttons = {}

        # Create buttons for commands
        for label, data in COMMANDS.items():
            btn = QPushButton(label)
            # تم تمرير قاموس البيانات (data) بدلاً من الأمر مباشرة
            btn.clicked.connect(lambda _, lbl=label, button=btn, cmd_data=data: self.run_command(lbl, button, cmd_data))
            layout.addWidget(btn)
            self.buttons[label] = btn

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
        self.progressBar.setTextVisible(False)
        self.progressBar.setRange(0, 0)
        self.progressBar.hide()
        layout.addWidget(self.progressBar)

        # Output TextEdit
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
            QApplication.restoreOverrideCursor()
        else:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

    def _append_output_to_text_edit(self, text):
        self.output_text_edit.append(text)
        self.output_text_edit.verticalScrollBar().setValue(self.output_text_edit.verticalScrollBar().maximum())

    # ====================================================================
    # إدارة حالة الواجهة الرسومية (Slots)
    # ====================================================================

    def _on_command_started(self, command_name, button):
        # تعطيل الواجهة بالكامل لتشغيل أمر واحد
        self.set_ui_enabled(False)
        button.setText(f"Processing: {command_name}...")
        button.setEnabled(False)
        self.progressBar.show()

    def _on_command_finished(self, original_name, button, success):
        # إعادة تمكين الواجهة بعد انتهاء أمر واحد
        button.setText(original_name)
        self.set_ui_enabled(True)
        self.progressBar.hide()
        if success:
            self._append_output_to_text_edit("✅ Command finished successfully.")
        else:
            self._append_output_to_text_edit("❌ Command failed.")

    def _on_full_fix_started(self):
        self.set_ui_enabled(False)
        self.full_fix_btn.setText("Running Full Fix...")
        self.full_fix_btn.setEnabled(False)
        self.progressBar.show()

    def _on_full_fix_step_update(self, name, current_button):
        # تحديث زر الخطوة الحالية وإظهار اسم الأمر
        for btn_obj in self.buttons.values():
            btn_obj.setEnabled(False) # إبقاء كل الأزرار الأخرى معطلة
        current_button.setText(f"➡️ Running: {name}...")
        current_button.setEnabled(False) # تعطيل زر الأمر نفسه

    def _on_full_fix_finished(self, success):
        # إعادة تمكين الواجهة بالكامل بعد انتهاء كل العمليات
        self.full_fix_btn.setText("Full Auto Fix")
        self.set_ui_enabled(True)
        self.progressBar.hide()
        # استعادة نصوص الأزرار بعد انتهاء Full Fix
        for name, btn in self.buttons.items():
            btn.setText(name)

        if success:
            self._append_output_to_text_edit("\n✅ All Full Auto Fix tasks completed successfully.")
        else:
            self._append_output_to_text_edit("\n❌ Full Auto Fix aborted due to an error.")

    # ====================================================================
    # تنفيذ الأوامر (المنطق الجديد)
    # ====================================================================

    def _execute_subprocess(self, full_command, is_shell=False):
        """
        دالة مساعدة لتنفيذ أمر فرعي وقراءة مخرجاته.
        تعود بـ (return_code, success_status)
        """
        self.signals.output_appended.emit(f"Running: {' '.join(full_command) if not is_shell else full_command}")
        print(f"Running: {' '.join(full_command) if not is_shell else full_command}")

        success = False
        return_code = -1

        try:
            # استخدام Popen مع shell=False للقوائم (الأكثر أمانًا)
            process = subprocess.Popen(full_command, shell=is_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

            # قراءة المخرجات الحية
            for line in iter(process.stdout.readline, ''):
                self.signals.output_appended.emit(line.strip())
            
            # قراءة الأخطاء (إذا كانت stderr غير فارغة)
            error_lines = []
            for line in iter(process.stderr.readline, ''):
                error_lines.append(line.strip())
                self.signals.output_appended.emit(f"ERROR: {line.strip()}")

            process.stdout.close()
            process.stderr.close()
            return_code = process.wait()

            # التحقق من رمز العودة
            if return_code != 0:
                self.signals.output_appended.emit(f"❌ Command exited with error code: {return_code}")
                success = False
            else:
                success = True

            return return_code, success, error_lines

        except FileNotFoundError:
            self.signals.output_appended.emit("❌ Error: Command or a tool not found. Check installation and PATH.")
            return -1, False, []
        except Exception as e:
            self.signals.output_appended.emit(f"❌ An unexpected error occurred: {e}")
            return -1, False, []

    def run_command(self, name, button, cmd_data):
        """تنفيذ أمر واحد بأسلوب آمن في خيط منفصل."""
        def task():
            self.signals.command_started.emit(name, button)
            self.signals.output_appended.emit(f"\n--- Starting: {name} ({cmd_data['desc']}) ---")
            
            main_command = cmd_data['command']
            pre_command = cmd_data.get('pre_command')
            final_success = False
            
            try:
                # 1. المرحلة التمهيدية (Pre-Command) لأوامر مثل 'Repair Database'
                if pre_command:
                    self.signals.output_appended.emit(f"--- Running Pre-Command: {' '.join(pre_command)} ---")
                    pre_code, pre_success, pre_output = self._execute_subprocess(pre_command)
                    
                    if not pre_success:
                        self.signals.output_appended.emit("❌ Pre-command failed. Aborting main command.")
                        final_success = False
                        return # إنهاء الـ task
                    
                    # استخدم الأخطاء (stderr) كمدخل للأمر الرئيسي لـ pacman -D
                    if name == "Repair Database" and pre_output:
                        # إعداد الأمر الرئيسي باستخدام مخرجات الأمر التمهيدي
                        full_command = main_command + pre_output 
                    else:
                        # لا يوجد حزم يتيمة لإزالتها، يعتبر نجاحًا
                        self.signals.output_appended.emit("✅ No items found by pre-command. Skipping main command.")
                        final_success = True
                        return

                else:
                    # 2. المرحلة الرئيسية للأوامر البسيطة
                    full_command = main_command

                # 3. تنفيذ الأمر الرئيسي
                if full_command:
                    self.signals.output_appended.emit(f"--- Running Main Command: {' '.join(full_command)} ---")
                    main_code, main_success, _ = self._execute_subprocess(full_command)
                    final_success = main_success

            except Exception as e:
                self.signals.output_appended.emit(f"❌ Critical Error during execution: {e}")
                final_success = False
            
            self.signals.output_appended.emit("--- Command Finished ---")
            self.signals.command_finished.emit(name, button, final_success)

        threading.Thread(target=task).start()

    def run_all_commands(self):
        """تنفيذ جميع الأوامر بالتسلسل."""
        def task():
            self.signals.full_fix_started.emit()
            self.signals.output_appended.emit("\n--- Starting Full Auto Fix Sequence ---")

            all_commands_successful = True
            
            # لتخزين نصوص الأزرار الأصلية
            original_button_texts = {name: self.buttons[name].text() for name in COMMANDS}

            for name, cmd_data in COMMANDS.items():
                current_button = self.buttons[name]
                
                # 1. إشارة تحديث الخطوة
                self.signals.full_fix_step_update.emit(name, current_button)
                self.signals.output_appended.emit(f"\n--- Running: {name} ({cmd_data['desc']}) ---")
                
                command_success = False
                main_command = cmd_data['command']
                pre_command = cmd_data.get('pre_command')

                # ********* تنفيذ المنطق المُحسّن هنا *********
                try:
                    full_command = None
                    # 1. المرحلة التمهيدية
                    if pre_command:
                        self.signals.output_appended.emit(f"--- Running Pre-Command: {' '.join(pre_command)} ---")
                        pre_code, pre_success, pre_output = self._execute_subprocess(pre_command)

                        if not pre_success and pre_code != 1: # كود 1 مقبول عادةً لـ Qdtq إذا لم توجد حزم يتيمة
                            command_success = False
                            raise Exception("Pre-command failed.")

                        if name == "Repair Database" and pre_output:
                            full_command = main_command + pre_output
                        elif not pre_output:
                            # لا يوجد شيء لتنظيفه/إصلاحه، نعتبره نجاحًا ونستمر
                            command_success = True
                            self.signals.output_appended.emit("✅ Pre-command found no issues. Skipping main step.")
                            
                    else:
                        full_command = main_command

                    # 2. تنفيذ الأمر الرئيسي (إذا كان هناك أمر لتنفيذه)
                    if full_command:
                        self.signals.output_appended.emit(f"--- Running Main Command: {' '.join(full_command)} ---")
                        main_code, main_success, _ = self._execute_subprocess(full_command)
                        command_success = main_success
                        
                except Exception as e:
                    self.signals.output_appended.emit(f"❌ Error during {name}: {e}")
                    command_success = False
                # ********* نهاية تنفيذ المنطق المُحسّن *********

                if not command_success:
                    all_commands_successful = False
                    self.signals.output_appended.emit(f"\n--- Full Auto Fix Aborted due to {name} failure ---")
                    
                    # استعادة نص الزر وحالة الواجهة
                    current_button.setText(original_button_texts[name])
                    self.signals.full_fix_finished.emit(all_commands_successful)
                    return # إنهاء الـ task بالكامل

            self.signals.output_appended.emit("\n✅ All Full Auto Fix tasks completed successfully.")
            self.signals.output_appended.emit("--- Full Auto Fix Finished ---")
            self.signals.full_fix_finished.emit(all_commands_successful)

        threading.Thread(target=task).start()

    def show_help(self):
        help_msg = (
            "This tool provides quick fixes for Arch-based systems:\n"
            "- Repair Database: Clean unused packages (Orphans).\n"
            "- Clear Cache: Remove old package files to save disk space.\n"
            "- Fix Corrupted: Full update with file overwrite to fix conflicts.\n"
            "- Update: Synchronize system packages.\n"
            "- Refresh Mirrors: Force resynchronization of local database.\n"
            "- Full Fix: Runs all above in order, stopping on the first failure."
        )
        QMessageBox.information(self, "Help", help_msg)

    def show_about(self):
        about_text = (
            "Helwan Linux NetFix GUI (Improved)\n"
            "Version 1.1\n"
            "By SMA Coding / Helwan Linux Team\n"
            "Saeed Badrelden : helwanlinux@gmail.com"
        )
        QMessageBox.information(self, "About", about_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetFixApp()
    window.show()
    sys.exit(app.exec_())