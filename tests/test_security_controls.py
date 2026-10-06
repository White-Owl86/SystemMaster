import copy
import json
import unittest
from unittest.mock import Mock, patch

import security_controls as security


def defender_state(enabled=True, tamper=False):
    return {
        "Status": {
            "IsTamperProtected": tamper,
            "RealTimeProtectionEnabled": enabled,
            "BehaviorMonitorEnabled": enabled,
            "IoavProtectionEnabled": enabled,
        },
        "Preferences": {
            "DisableRealtimeMonitoring": not enabled,
            "DisableBehaviorMonitoring": not enabled,
            "DisableIOAVProtection": not enabled,
            "DisableScriptScanning": not enabled,
        },
    }


class WindowsFixture:
    """Model the JSON boundary, including silently ignored policy-controlled writes."""

    def __init__(self, enabled=True):
        self.defender = defender_state(enabled)
        self.firewall = {name: enabled for name in ("Domain", "Private", "Public")}
        self.calls = []
        self.ignore_defender = False
        self.ignore_script_scanning = False
        self.lock_public_profile = False
        self.fail_firewall = False
        self.fail_defender = False

    def __call__(self, script):
        self.calls.append(script)
        if script == security.READ_DEFENDER:
            return json.dumps(self.defender)
        if script == security.READ_FIREWALL:
            return json.dumps([{"Name": name, "Enabled": str(value)} for name, value in self.firewall.items()])
        if script.startswith("Set-MpPreference "):
            if self.fail_defender:
                raise RuntimeError("Defender access denied")
            if not self.ignore_defender:
                for name in self.defender["Preferences"]:
                    if name == "DisableScriptScanning" and self.ignore_script_scanning:
                        continue
                    if f"-{name} $true" in script:
                        self.defender["Preferences"][name] = True
                    elif f"-{name} $false" in script:
                        self.defender["Preferences"][name] = False
                for status, preference in (
                    ("RealTimeProtectionEnabled", "DisableRealtimeMonitoring"),
                    ("BehaviorMonitorEnabled", "DisableBehaviorMonitoring"),
                    ("IoavProtectionEnabled", "DisableIOAVProtection"),
                ):
                    self.defender["Status"][status] = not self.defender["Preferences"][preference]
            return ""
        if script.startswith("Set-NetFirewallProfile "):
            if self.fail_firewall:
                raise RuntimeError("Firewall access denied")
            for profile in self.firewall:
                if profile != "Public" or not self.lock_public_profile:
                    self.firewall[profile] = "-Enabled $true" in script
            return ""
        raise AssertionError(f"Unexpected PowerShell operation: {script}")

    def writes(self):
        return [call for call in self.calls if call.startswith("Set-")]


class SecurityTests(unittest.TestCase):
    def setUp(self):
        sleeper = patch.object(security.time, "sleep")
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def test_disable_verifies_all_scopes(self):
        windows = WindowsFixture()
        result = security.set_protections(False, windows)
        self.assertIn("Verified:", result)
        self.assertIn("Defender remains installed", result)
        self.assertTrue(security.defender_matches(windows.defender, False))
        self.assertFalse(any(windows.firewall.values()))
        self.assertEqual(len(windows.writes()), 2)

    def test_enable_restores_all_scopes(self):
        windows = WindowsFixture(enabled=False)
        self.assertIn("Verified:", security.set_protections(True, windows))
        self.assertTrue(security.defender_matches(windows.defender, True))
        self.assertTrue(all(windows.firewall.values()))

    def test_tamper_protection_or_unknown_status_prevents_any_write(self):
        for tamper in (True, None, "False"):
            with self.subTest(tamper=tamper):
                windows = WindowsFixture()
                windows.defender["Status"]["IsTamperProtected"] = tamper
                with self.assertRaisesRegex(security.SecurityControlError, "No settings were changed"):
                    security.set_protections(False, windows)
                self.assertEqual(windows.writes(), [])

    def test_unreadable_defender_prevents_any_write(self):
        windows = WindowsFixture()
        windows.defender["Status"].pop("RealTimeProtectionEnabled")
        with self.assertRaisesRegex(security.SecurityControlError, "incomplete or invalid"):
            security.set_protections(False, windows)
        self.assertEqual(windows.writes(), [])

    def test_missing_firewall_profile_prevents_any_write(self):
        windows = WindowsFixture()
        windows.firewall.pop("Public")
        with self.assertRaisesRegex(security.SecurityControlError, "incomplete or invalid"):
            security.set_protections(False, windows)
        self.assertEqual(windows.writes(), [])

    def test_ignored_defender_changes_do_not_disable_firewall(self):
        windows = WindowsFixture()
        windows.ignore_defender = True
        with self.assertRaisesRegex(security.SecurityControlError, "Some settings may have changed"):
            security.set_protections(False, windows)
        self.assertTrue(all(windows.firewall.values()))
        self.assertEqual(len(windows.writes()), 1)
        self.assertTrue(windows.writes()[0].startswith("Set-MpPreference "))

    def test_partial_firewall_change_is_not_success(self):
        windows = WindowsFixture()
        windows.lock_public_profile = True
        with self.assertRaisesRegex(security.SecurityControlError, "Not all effective firewall profiles"):
            security.set_protections(False, windows)
        self.assertTrue(windows.firewall["Public"])
        self.assertFalse(windows.firewall["Private"])

    def test_script_scanning_change_must_also_be_verified(self):
        windows = WindowsFixture()
        windows.ignore_script_scanning = True
        with self.assertRaisesRegex(security.SecurityControlError, "Defender did not reach"):
            security.set_protections(False, windows)
        self.assertTrue(all(windows.firewall.values()))

    def test_enable_attempts_defender_even_if_firewall_fails(self):
        windows = WindowsFixture(enabled=False)
        windows.fail_firewall = True
        with self.assertRaisesRegex(security.SecurityControlError, "Firewall: Firewall access denied"):
            security.set_protections(True, windows)
        self.assertTrue(security.defender_matches(windows.defender, True))

    def test_enable_attempts_firewall_even_if_defender_fails(self):
        windows = WindowsFixture(enabled=False)
        windows.fail_defender = True
        with self.assertRaisesRegex(security.SecurityControlError, "Defender: Defender access denied"):
            security.set_protections(True, windows)
        self.assertTrue(all(windows.firewall.values()))

    def test_invalid_or_ambiguous_json_is_not_treated_as_disabled(self):
        for raw in ("", "null", "[]", "{}", "not JSON"):
            with self.subTest(raw=raw):
                with self.assertRaises(security.SecurityControlError):
                    security.read_defender(Mock(return_value=raw))
                with self.assertRaises(security.SecurityControlError):
                    security.read_firewall(Mock(return_value=raw))
        invalid = defender_state()
        invalid["Status"]["RealTimeProtectionEnabled"] = "False"
        with self.assertRaises(security.SecurityControlError):
            security.read_defender(Mock(return_value=json.dumps(invalid)))

    def test_verification_waits_for_delayed_defender_state(self):
        run = Mock(side_effect=["", json.dumps(defender_state()), json.dumps(defender_state(False))])
        security.change_defender(False, run)
        self.assertEqual(run.call_count, 3)
        security.time.sleep.assert_called_once_with(0.5)

    def test_preferences_alone_do_not_prove_protection_disabled(self):
        state = defender_state(False)
        for key in security.DEFENDER_STATUS:
            with self.subTest(key=key):
                mismatch = copy.deepcopy(state)
                mismatch["Status"][key] = True
                self.assertFalse(security.defender_matches(mismatch, False))

    def test_standalone_firewall_verifies_effective_policy(self):
        windows = WindowsFixture()
        windows.lock_public_profile = True
        with self.assertRaisesRegex(security.SecurityControlError, "Some profiles may have changed"):
            security.set_firewall(False, windows)

    def test_defender_reenabled_during_firewall_change_is_failure(self):
        windows = WindowsFixture()

        def run(script):
            result = windows(script)
            if script.startswith("Set-NetFirewallProfile "):
                windows.defender = defender_state(True)
            return result

        with self.assertRaisesRegex(security.SecurityControlError, "Defender was re-enabled"):
            security.set_protections(False, run)


if __name__ == "__main__":
    unittest.main()
