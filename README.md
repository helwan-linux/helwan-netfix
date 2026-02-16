# Helwan Linux NetFix Tool 🛠️

**NetFix** is the official system recovery and package management utility for **Helwan Linux**. It provides a robust Graphical User Interface (GUI) built with Python and PyQt5 to help users maintain, update, and repair their system without needing deep terminal knowledge.

---

## 🚀 Key Features

* **Auto-Lock Removal:** Automatically detects and removes the `db.lck` file if a previous update was interrupted.
* **Orphan Repair:** Intelligent detection of orphaned packages and fixing their installation reason.
* **Safe Cancellation:** A dedicated "Stop" button that safely terminates root processes via `pkexec` without freezing the system.
* **Forced Cleaning:** Automated cache cleaning using `yes |` pipes to avoid interactive prompts.
* **Conflict Resolution:** Fixes corrupted packages by overwriting file conflicts during updates.
* **Real-time Feedback:** A built-in terminal console and progress bar to monitor system tasks.

---

## 🛠 Commands Included

1. **Repair Database:** Searches for orphaned packages and sets them as dependencies.
2. **Clear Cache:** Removes all downloaded package files to free up disk space.
3. **Fix Corrupted Packages:** Performs a full sync and overwrites conflicting files.
4. **Update System:** Standard system-wide synchronization and upgrade.
5. **Refresh Mirrors:** Forces a fresh synchronization of the repository databases.
6. **Full Auto Fix:** Runs all the above tools sequentially in one click.

---

## 📥 Installation

### Via Helwan Package Manager (hpm)

```bash
hpm i hel-netfix
```

---

## 🛡 Security & Permissions

NetFix uses Polkit (`pkexec`) to perform administrative tasks. This ensures that only authorized users can modify system files while keeping the GUI running under a standard user for safety.

---

## 🤝 Contribution

This is a part of the Helwanian Identity project. Contributions and bug reports are welcome via the official Helwan Linux repositories.

---

**Developed by:** Helwan Linux Team
**License:** GPL
