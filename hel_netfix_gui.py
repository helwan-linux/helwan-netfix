# hel_netfix_gui.py
# SMA Coding - Helwan Linux Official Tool
# Version: 1.0 Final GTK Edition

import gi
import subprocess
import threading
import os # Import os module for path manipulation

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

COMMANDS = {
    "Repair Database": ["sudo", "pacman", "-D", "--asdeps", "$(pacman -Qdtq)"],
    "Clear Cache": ["sudo", "pacman", "-Scc"],
    "Fix Corrupted Packages": ["sudo", "pacman", "-Syu", "--overwrite", "'*'"],
    "Update System": ["sudo", "pacman", "-Syu"],
    "Refresh Mirrors": ["sudo", "reflector", "--latest", "10", "--protocol", "https", "--sort", "rate", "--save", "/etc/pacman.d/mirrorlist"],
    "Reinstall Broken Packages": ["sudo", "pacman", "-Qqn", "|", "xargs", "sudo", "pacman", "-S"],
}

class NetFixApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Helwan Linux - NetFix Tool")
        self.set_border_width(10)
        self.set_default_size(400, 300)

        # Set window icon
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, "netfix.png") # Make sure 'netfix.png' is in the same directory

        try:
            self.set_icon_from_file(icon_path)
        except Exception as e:
            print(f"Failed to load icon: {e}")
            # You can add more robust error handling here if needed

        vbox = Gtk.VBox(spacing=10)
        self.add(vbox)

        for label in COMMANDS:
            button = Gtk.Button(label=label)
            button.connect("clicked", self.run_command, COMMANDS[label])
            vbox.pack_start(button, True, True, 0)

        full_fix = Gtk.Button(label="Full Auto Fix")
        full_fix.connect("clicked", self.run_all_commands)
        vbox.pack_start(full_fix, True, True, 0)

        hbox = Gtk.HBox(spacing=10)
        help_btn = Gtk.Button(label="Help")
        help_btn.connect("clicked", self.show_help)
        about_btn = Gtk.Button(label="About")
        about_btn.connect("clicked", self.show_about)
        hbox.pack_start(help_btn, True, True, 0)
        hbox.pack_start(about_btn, True, True, 0)
        vbox.pack_end(hbox, False, False, 0)

        self.output = Gtk.Label(label="Ready.")
        vbox.pack_end(self.output, False, False, 10)

    def run_command(self, widget, command):
        def task():
            try:
                self.output.set_text(f"Running: {' '.join(command)}")
                subprocess.run(" ".join(command), shell=True, check=True)
                self.output.set_text("✅ Done.")
            except subprocess.CalledProcessError:
                self.output.set_text("❌ Failed.")

        threading.Thread(target=task).start()

    def run_all_commands(self, widget):
        def task():
            for name, command in COMMANDS.items():
                self.output.set_text(f"Running: {name}")
                try:
                    subprocess.run(" ".join(command), shell=True, check=True)
                except subprocess.CalledProcessError:
                    self.output.set_text(f"❌ Failed at {name}")
                    return
            self.output.set_text("✅ All tasks completed successfully.")

        threading.Thread(target=task).start()

    def show_help(self, widget):
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
        self.show_dialog("Help", help_msg)

    def show_about(self, widget):
        about_text = (
            "Helwan Linux NetFix GUI\n"
            "Version 1.0\n"
            "By SMA Coding / Helwan Linux Team\n"
            "Saeed Badrelden : helwanlinux@gmail.com\n"
        )
        self.show_dialog("About", about_text)

    def show_dialog(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    app = NetFixApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
