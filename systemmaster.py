"""White Owl / SystemMaster utilities for Windows 10 and Windows 11."""

import base64
import ctypes
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from dataclasses import dataclass


@dataclass(frozen=True)
class Action:
    label: str
    description: str
    script: str = ""
    uri: str = ""
    admin: bool = False
    confirmation: str = ""


ACTIONS = (
    Action(
        "Open network sharing settings",
        "Configure network discovery and sharing for your trusted network.",
        script="Start-Process control.exe -ArgumentList '/name Microsoft.NetworkAndSharingCenter' -ErrorAction Stop",
    ),
    Action(
        "Open printer settings",
        "For error 0x0000011b, update both PCs and check the printer driver "
        "and sharing settings. This opens settings; it does not apply a repair.",
        uri="ms-settings:printers",
    ),
    Action(
        "Restart Print Spooler",
        "Restart the printing service. Active print jobs may be interrupted.",
        script="Restart-Service -Name Spooler -ErrorAction Stop; "
        "Get-Service -Name Spooler | Select-Object Name, Status | Out-String",
        admin=True,
    ),
    Action(
        "Open Windows Update settings",
        "Check for updates or use the pause options available on this PC.",
        uri="ms-settings:windowsupdate",
    ),
    Action(
        "Enable Windows Firewall",
        "Enable the Domain, Private and Public firewall profiles.",
        script="Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True -ErrorAction Stop",
        admin=True,
    ),
    Action(
        "Disable Windows Firewall",
        "Disable all firewall profiles. Use Enable Windows Firewall to turn them back on.",
        script="Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled False -ErrorAction Stop",
        admin=True,
        confirmation="Turn off the firewall for ALL network profiles? "
        "This removes firewall protection, including on public networks.",
    ),
    Action(
        "Disable Remote Desktop",
        "Deny incoming Remote Desktop connections without changing the RDP port.",
        script="Set-ItemProperty -LiteralPath 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server' "
        "-Name fDenyTSConnections -Type DWord -Value 1 -ErrorAction Stop",
        admin=True,
        confirmation="Disable incoming Remote Desktop connections? "
        "You may lose remote access to this PC. Organization policy can override this setting.",
    ),
    Action(
        "Open Windows Security",
        "Manage antivirus protection in Windows Security. Organization policy "
        "and Tamper Protection may restrict changes.",
        uri="ms-settings:windowsdefender",
    ),
)
ACTION_BY_LABEL = {action.label: action for action in ACTIONS}
PLACEHOLDER = "Please select an action"


class CommandError(RuntimeError):
    """A Windows operation failed; the message can be shown to the user."""


def is_admin():
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def powershell_path():
    # Sysnative lets 32-bit Python reach the native system tools on 64-bit Windows.
    system_dir = "Sysnative" if sys.maxsize <= 2**32 and os.environ.get("PROCESSOR_ARCHITEW6432") else "System32"
    return str(Path(os.environ.get("SystemRoot", r"C:\Windows")) /
               system_dir / "WindowsPowerShell" / "v1.0" / "powershell.exe")


def run_powershell(script):
    # PowerShell cmdlet errors otherwise often leave a successful process exit code.
    wrapped = (
        "$ErrorActionPreference = 'Stop'\n"
        "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)\n"
        "try {\n" + script + "\n} catch {\n"
        "[Console]::Error.WriteLine($_.Exception.Message)\nexit 1\n}\n"
    )
    encoded = base64.b64encode(wrapped.encode("utf-16-le")).decode("ascii")
    try:
        result = subprocess.run(
            [powershell_path(), "-NoLogo", "-NoProfile", "-NonInteractive",
             "-EncodedCommand", encoded],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandError("The command timed out after 90 seconds. Some changes may "
                           "already have applied; check Windows settings before retrying.") from exc
    except OSError as exc:
        raise CommandError(f"Could not start Windows PowerShell: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "No error details were returned."
        raise CommandError(f"PowerShell failed (exit {result.returncode}):\n{detail}")
    return result.stdout.strip() or "Command completed."


def execute_action(action):
    if sys.platform != "win32":
        raise CommandError("SystemMaster requires Windows 10 or Windows 11.")
    if action.admin and not is_admin():
        raise CommandError("This action requires administrator access. Close SystemMaster "
                           "and launch it with Run as administrator, then try again.")
    if action.uri:
        try:
            os.startfile(action.uri)
        except OSError as exc:
            raise CommandError(f"Could not open Windows settings: {exc}") from exc
        return "Requested Windows settings. Make the desired changes in that window."
    return run_powershell(action.script)


class SystemMasterApp:
    def __init__(self, root):
        self.root = root
        self.busy = False
        self.results = queue.Queue()
        root.title("White Owl — SystemMaster")
        root.minsize(520, 310)
        root.columnconfigure(0, weight=1)
        root.protocol("WM_DELETE_WINDOW", self.close)

        frame = ttk.Frame(root, padding=18)
        frame.grid(sticky="nsew")
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Windows 10 / 11 utilities", font=("Segoe UI", 14, "bold")).grid(sticky="w")
        privilege = "Administrator" if is_admin() else "Standard user — system changes require Run as administrator"
        ttk.Label(frame, text=privilege, wraplength=480).grid(sticky="w", pady=(6, 14))
        self.selection = tk.StringVar(root, value=PLACEHOLDER)
        self.menu = ttk.Combobox(frame, textvariable=self.selection,
                                 values=tuple(ACTION_BY_LABEL), state="readonly", width=48)
        self.menu.grid(sticky="ew")
        self.menu.bind("<<ComboboxSelected>>", self.selection_changed)
        self.description = tk.StringVar(root, value="Select an action to see what it does.")
        ttk.Label(frame, textvariable=self.description, wraplength=480).grid(sticky="w", pady=12)
        self.button = ttk.Button(frame, text="Run action", command=self.execute, state="disabled")
        self.button.grid(sticky="w")
        self.status = tk.StringVar(root, value="Ready")
        ttk.Label(frame, textvariable=self.status, wraplength=480).grid(sticky="w", pady=(12, 0))
        self.poll_id = root.after(100, self.poll_results)

    def selection_changed(self, _event=None):
        action = ACTION_BY_LABEL.get(self.selection.get())
        self.description.set(action.description if action else "Select an action to see what it does.")
        self.button.configure(state="normal" if action and not self.busy else "disabled")

    def execute(self):
        if self.busy:
            return
        action = ACTION_BY_LABEL.get(self.selection.get())
        if action is None:
            messagebox.showinfo("Select an action", "Please select an action first.", parent=self.root)
            return
        if action.admin and not is_admin():
            messagebox.showerror("Administrator access required",
                                 "Launch SystemMaster with Run as administrator to use this action.",
                                 parent=self.root)
            return
        if action.confirmation and not messagebox.askyesno("Confirm change", action.confirmation, parent=self.root):
            return
        self.busy = True
        self.menu.configure(state="disabled")
        self.button.configure(state="disabled")
        self.status.set(f"Running: {action.label}…")
        threading.Thread(target=self.worker, args=(action,), daemon=True).start()

    def worker(self, action):
        # Only the Tk main thread reads the queue and updates widgets/dialogs.
        try:
            self.results.put((True, execute_action(action)))
        except Exception as exc:
            self.results.put((False, str(exc)))

    def poll_results(self):
        try:
            success, detail = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.menu.configure(state="readonly")
            self.selection_changed()
            self.status.set("Completed" if success else "Failed — see error details")
            show = messagebox.showinfo if success else messagebox.showerror
            show("SystemMaster", detail, parent=self.root)
        self.poll_id = self.root.after(100, self.poll_results)

    def close(self):
        if self.busy:
            messagebox.showinfo("Action running", "Wait for the current action to finish before closing.", parent=self.root)
            return
        self.root.after_cancel(self.poll_id)
        self.root.destroy()


def main():
    if sys.platform != "win32":
        print("SystemMaster requires Windows 10 or Windows 11.", file=sys.stderr)
        return 1
    root = tk.Tk()
    SystemMasterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
