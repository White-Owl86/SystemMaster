import base64
import subprocess
import threading
import tkinter as tk
import unittest
from unittest.mock import patch

import systemmaster as sm


class CommandTests(unittest.TestCase):
    @patch.object(sm.subprocess, "run")
    def test_success_uses_encoded_script_and_captures_unicode(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "چاپگر آماده است\n", "")
        self.assertEqual(sm.run_powershell("Get-Service Spooler"), "چاپگر آماده است")
        args, kwargs = run.call_args
        command = args[0]
        script = base64.b64decode(command[-1]).decode("utf-16-le")
        self.assertIn("Get-Service Spooler", script)
        self.assertIn("$ErrorActionPreference = 'Stop'", script)
        self.assertIn("exit 1", script)
        self.assertIn("-NoProfile", command)
        self.assertIn("-NonInteractive", command)
        self.assertFalse(kwargs.get("shell", False))
        self.assertEqual(kwargs["encoding"], "utf-8")
        self.assertEqual(kwargs["timeout"], 90)

    @patch.object(sm.subprocess, "run")
    def test_failed_commands_report_stderr_stdout_or_exit_code(self, run):
        for stdout, stderr, expected in [("", "Access denied", "Access denied"),
                                         ("Service missing", "", "Service missing"),
                                         ("", "", "exit 5")]:
            with self.subTest(expected=expected):
                run.return_value = subprocess.CompletedProcess([], 5, stdout, stderr)
                with self.assertRaisesRegex(sm.CommandError, expected):
                    sm.run_powershell("Restart-Service Spooler")

    @patch.object(sm.subprocess, "run", side_effect=FileNotFoundError("missing"))
    def test_missing_powershell(self, _run):
        with self.assertRaisesRegex(sm.CommandError, "Could not start"):
            sm.run_powershell("Get-Service")

    @patch.object(sm.subprocess, "run", side_effect=subprocess.TimeoutExpired("powershell", 90))
    def test_timeout_explains_possible_partial_changes(self, _run):
        with self.assertRaisesRegex(sm.CommandError, "Some changes may already have applied"):
            sm.run_powershell("Restart-Service Spooler")

    @patch.object(sm.sys, "platform", "linux")
    @patch.object(sm, "run_powershell")
    def test_non_windows_rejected_before_execution(self, run):
        with self.assertRaisesRegex(sm.CommandError, "requires Windows"):
            sm.execute_action(sm.ACTIONS[0])
        run.assert_not_called()

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm, "is_admin", return_value=False)
    @patch.object(sm, "run_powershell")
    def test_admin_required_before_mutation(self, run, _admin):
        with self.assertRaisesRegex(sm.CommandError, "administrator access"):
            sm.execute_action(sm.ACTION_BY_LABEL["Restart Print Spooler"])
        run.assert_not_called()

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm, "is_admin", return_value=True)
    @patch.object(sm, "run_powershell", return_value="Running")
    def test_admin_action_runs(self, run, _admin):
        action = sm.ACTION_BY_LABEL["Restart Print Spooler"]
        self.assertEqual(sm.execute_action(action), "Running")
        run.assert_called_once_with(action.script)

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm, "is_admin", return_value=False)
    @patch.object(sm.security_controls, "set_protections")
    def test_security_action_requires_admin(self, change, _admin):
        with self.assertRaisesRegex(sm.CommandError, "administrator access"):
            sm.execute_action(sm.ACTION_BY_LABEL["Disable Defender protections + firewall"])
        change.assert_not_called()

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm, "is_admin", return_value=True)
    @patch.object(sm.security_controls, "set_protections", return_value="Verified")
    def test_security_action_dispatches_requested_state(self, change, _admin):
        for label, enabled in (("Disable Defender protections + firewall", False),
                               ("Enable Defender protections + firewall", True)):
            self.assertEqual(sm.execute_action(sm.ACTION_BY_LABEL[label]), "Verified")
            change.assert_called_with(enabled, sm.run_powershell)

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm.os, "startfile", create=True)
    @patch.object(sm, "is_admin", return_value=False)
    def test_settings_work_without_admin(self, _admin, startfile):
        for action in sm.ACTIONS:
            if action.uri:
                self.assertIn("Requested Windows settings", sm.execute_action(action))
                startfile.assert_called_with(action.uri)

    @patch.object(sm.sys, "platform", "win32")
    @patch.object(sm.os, "startfile", create=True, side_effect=OSError("URI unavailable"))
    def test_settings_launch_failure(self, _startfile):
        with self.assertRaisesRegex(sm.CommandError, "URI unavailable"):
            sm.execute_action(sm.ACTION_BY_LABEL["Open printer settings"])

    @patch.dict(sm.os.environ, {"SystemRoot": "C:/Windows", "PROCESSOR_ARCHITEW6432": "AMD64"})
    def test_native_powershell_for_32_bit_python(self):
        with patch.object(sm.sys, "maxsize", 2**31 - 1):
            self.assertIn("Sysnative", sm.powershell_path())
        with patch.object(sm.sys, "maxsize", 2**63 - 1):
            self.assertIn("System32", sm.powershell_path())


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = sm.SystemMasterApp(self.root)

    def tearDown(self):
        self.root.after_cancel(self.app.poll_id)
        # Drain Tk theme events before destroying this test's interpreter.
        self.root.update_idletasks()
        self.root.destroy()

    def select(self, label):
        self.app.selection.set(label)
        self.app.selection_changed()

    @patch.object(sm.messagebox, "showinfo")
    @patch.object(sm.threading, "Thread")
    def test_empty_selection_does_not_start_command(self, thread, info):
        self.assertEqual(str(self.app.button["state"]), "disabled")
        self.app.execute()
        thread.assert_not_called()
        info.assert_called_once()

    @patch.object(sm.messagebox, "showerror")
    @patch.object(sm, "is_admin", return_value=False)
    @patch.object(sm.threading, "Thread")
    def test_admin_denial_in_gui(self, thread, _admin, error):
        self.select("Restart Print Spooler")
        self.app.execute()
        thread.assert_not_called()
        self.assertFalse(self.app.busy)
        error.assert_called_once()

    @patch.object(sm.messagebox, "askyesno", return_value=False)
    @patch.object(sm, "is_admin", return_value=True)
    @patch.object(sm.threading, "Thread")
    def test_cancel_dangerous_action(self, thread, _admin, confirm):
        for label in ("Disable Windows Firewall", "Disable Defender protections + firewall"):
            self.select(label)
            self.app.execute()
            self.assertEqual(confirm.call_args.kwargs["default"], sm.messagebox.NO)
        thread.assert_not_called()
        self.assertFalse(self.app.busy)

    @patch.object(sm, "is_admin", return_value=True)
    @patch.object(sm.threading, "Thread")
    def test_warning_precedes_security_worker(self, thread, _admin):
        def confirm(*args, **kwargs):
            thread.assert_not_called()
            self.assertFalse(self.app.busy)
            self.assertIn("ALL firewall profiles", args[1])
            self.assertIn("malware", args[1])
            self.assertEqual(kwargs["default"], sm.messagebox.NO)
            return True

        with patch.object(sm.messagebox, "askyesno", side_effect=confirm):
            self.select("Disable Defender protections + firewall")
            self.app.execute()
        thread.assert_called_once()
        self.assertTrue(self.app.busy)

    @patch.object(sm.messagebox, "showinfo")
    @patch.object(sm.threading, "Thread")
    def test_duplicate_execution_and_close_blocked_while_running(self, thread, info):
        self.select("Open printer settings")
        self.app.execute()
        self.app.execute()
        self.app.close()
        thread.assert_called_once()
        info.assert_called_once()
        self.assertTrue(self.app.busy)
        self.assertEqual(str(self.app.menu["state"]), "disabled")

    @patch.object(sm.messagebox, "showerror")
    @patch.object(sm, "execute_action", side_effect=sm.CommandError("Access denied"))
    def test_worker_failure_is_displayed_on_main_thread_and_allows_retry(self, _execute, error):
        self.select("Open printer settings")
        self.app.busy = True
        worker = threading.Thread(target=self.app.worker, args=(sm.ACTIONS[0],))
        worker.start()
        worker.join(timeout=2)
        self.assertFalse(worker.is_alive())
        error.assert_not_called()
        self.root.after_cancel(self.app.poll_id)
        self.app.poll_results()
        error.assert_called_once_with("SystemMaster", "Access denied", parent=self.root)
        self.assertFalse(self.app.busy)
        self.assertEqual(str(self.app.button["state"]), "normal")
        self.assertEqual(str(self.app.menu["state"]), "readonly")

    @patch.object(sm.messagebox, "showinfo")
    def test_ui_events_continue_during_background_command(self, info):
        release = threading.Event()
        started = threading.Event()
        finished = threading.Event()
        events = []

        def slow_action(_action):
            started.set()
            release.wait(timeout=2)
            finished.set()
            return "Settings requested"

        with patch.object(sm, "execute_action", side_effect=slow_action):
            try:
                self.select("Open printer settings")
                self.app.execute()
                self.assertTrue(started.wait(timeout=1))
                self.root.after_idle(lambda: events.append("responsive"))
                self.root.update()
                self.assertEqual(events, ["responsive"])
                self.assertTrue(self.app.busy)
            finally:
                release.set()
                self.assertTrue(finished.wait(timeout=2))
            result = self.app.results.get(timeout=2)
            self.app.results.put(result)
            self.root.after_cancel(self.app.poll_id)
            self.app.poll_results()
        self.assertFalse(self.app.busy)
        info.assert_called_once_with("SystemMaster", "Settings requested", parent=self.root)


if __name__ == "__main__":
    unittest.main()
