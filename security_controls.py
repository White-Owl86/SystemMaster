"""Supported Defender/Firewall controls, with verification of effective state."""

import json
import time


class SecurityControlError(RuntimeError):
    pass


DEFENDER_STATUS = (
    "RealTimeProtectionEnabled",
    "BehaviorMonitorEnabled",
    "IoavProtectionEnabled",
)
DEFENDER_PREFERENCES = (
    "DisableRealtimeMonitoring",
    "DisableBehaviorMonitoring",
    "DisableIOAVProtection",
    "DisableScriptScanning",
)
PROFILES = {"Domain", "Private", "Public"}
READ_DEFENDER = """
$status = Get-MpComputerStatus -ErrorAction Stop
$preferences = Get-MpPreference -ErrorAction Stop
@{
    Status = $status | Select-Object IsTamperProtected, RealTimeProtectionEnabled, BehaviorMonitorEnabled, IoavProtectionEnabled
    Preferences = $preferences | Select-Object DisableRealtimeMonitoring, DisableBehaviorMonitoring, DisableIOAVProtection, DisableScriptScanning
} | ConvertTo-Json -Depth 3 -Compress
"""
READ_FIREWALL = """
@(Get-NetFirewallProfile -PolicyStore ActiveStore -ErrorAction Stop | ForEach-Object {
    @{ Name = $_.Name; Enabled = $_.Enabled.ToString() }
}) | ConvertTo-Json -Compress
"""


def read_defender(run):
    try:
        state = json.loads(run(READ_DEFENDER))
        for key in DEFENDER_STATUS:
            if type(state["Status"][key]) is not bool:
                raise ValueError(f"Unknown Defender status: {key}")
        for key in DEFENDER_PREFERENCES:
            if type(state["Preferences"][key]) is not bool:
                raise ValueError(f"Unknown Defender preference: {key}")
        return state
    except (ValueError, TypeError, KeyError) as exc:
        raise SecurityControlError("Windows returned incomplete or invalid Defender status.") from exc


def read_firewall(run):
    try:
        rows = json.loads(run(READ_FIREWALL))
        if not isinstance(rows, list) or len(rows) != 3:
            raise ValueError("Expected three firewall profiles")
        state = {}
        for row in rows:
            if row["Enabled"] not in ("True", "False"):
                raise ValueError("Unknown effective firewall setting")
            state[row["Name"]] = row["Enabled"] == "True"
        if set(state) != PROFILES:
            raise ValueError("Missing firewall profile")
        return state
    except (ValueError, TypeError, KeyError) as exc:
        raise SecurityControlError("Windows returned incomplete or invalid firewall status.") from exc


def defender_matches(state, enabled):
    return (all(state["Status"][key] is enabled for key in DEFENDER_STATUS)
            and all(state["Preferences"][key] is (not enabled) for key in DEFENDER_PREFERENCES))


def change_defender(enabled, run):
    value = "$false" if enabled else "$true"
    flags = " ".join(f"-{name} {value}" for name in DEFENDER_PREFERENCES)
    run(f"Set-MpPreference {flags} -ErrorAction Stop")
    # Defender can report its previous state briefly after changing preferences.
    for attempt in range(5):
        state = read_defender(run)
        if defender_matches(state, enabled):
            return
        if attempt < 4:
            time.sleep(0.5)
    raise SecurityControlError(
        "Defender did not reach the requested state. Tamper Protection or organization "
        "policy may have blocked the change. Check Windows Security."
    )


def change_firewall(enabled, run):
    value = "$true" if enabled else "$false"
    run(f"Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled {value} -ErrorAction Stop")
    for attempt in range(5):
        if all(value is enabled for value in read_firewall(run).values()):
            return
        if attempt < 4:
            time.sleep(0.5)
    raise SecurityControlError(
        "Not all effective firewall profiles reached the requested state. "
        "Organization policy may override local settings."
    )


def set_firewall(enabled, run):
    try:
        change_firewall(enabled, run)
    except RuntimeError as exc:
        raise SecurityControlError(
            f"Firewall change could not be verified. Some profiles may have changed.\n{exc}"
        ) from exc
    return "All three effective firewall profiles are " + ("enabled." if enabled else "disabled.")


def set_protections(enabled, run):
    if not enabled:
        # Preflight before any writes. Missing Tamper Protection information is not consent.
        state = read_defender(run)
        if state["Status"].get("IsTamperProtected") is not False:
            raise SecurityControlError(
                "Tamper Protection is enabled or its status is unavailable. No settings "
                "were changed. Check Windows Security or contact your administrator."
            )
        read_firewall(run)
        try:
            # Do not disable the firewall if Defender cannot be disabled and verified.
            change_defender(False, run)
            change_firewall(False, run)
            if not defender_matches(read_defender(run), False):
                raise SecurityControlError("Defender was re-enabled while the action was running.")
        except RuntimeError as exc:
            raise SecurityControlError(
                "Could not complete disabling protections. Some settings may have changed. "
                "Use 'Enable Defender protections + firewall' and check Windows Security.\n"
                f"Details: {exc}"
            ) from exc
        return (
            "Verified: Defender real-time, behavior and downloaded-file protection are off; "
            "script scanning is configured off; all three firewall profiles are off.\n\n"
            "Defender remains installed. Scheduled/manual scans and other security features "
            "are not disabled. Windows or organization policy may turn protection back on."
        )

    # Attempt both restorations even if one provider is unavailable or policy-controlled.
    failures = []
    for name, change in (("Firewall", change_firewall), ("Defender", change_defender)):
        try:
            change(True, run)
        except RuntimeError as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        raise SecurityControlError(
            "Protection could not be fully enabled. Some settings may have changed. "
            "Check Windows Security.\n" + "\n".join(failures)
        )
    return (
        "Verified: Defender real-time, behavior and downloaded-file protection are on; "
        "script scanning is configured on; all three firewall profiles are on."
    )
