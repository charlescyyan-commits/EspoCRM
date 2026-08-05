"""DP-WP2 controlled navigation baseline preparation.

Replaces the pinned EspoCRM default 29-item ``config.tabList`` with the exact
``phase3c19-ia-v1`` 19-item definition.  It does not recover the ledger, invoke
the navigation adapter, invent navigation success markers, or touch ACL,
dashboards, migrations, Railway, hooks, AfterInstall, or CRM business data.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from scripts.dp_wp1_installation_foundation import (
    InstallationLockError,
    InstallationState,
    JsonFileInstallationLedger,
    LedgerCorruptionError,
    RecoveryDisposition,
    ReleaseIdentity,
)
from scripts.dp_wp2_ledger_interaction import (
    LedgerInteractionLockError,
    ProvisioningLedgerInteraction,
)
from scripts.dp_wp2_phase_adapters import navigation_provisioning as navigation

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DEFINITION = ROOT / "deployment" / "navigation" / "phase3c17_navigation.json"
DEFAULT_LEDGER = ROOT / "temp" / "dp-wp1-registration-evidence" / "installation-ledger.json"

PINNED_INSTALLATION_ID = "installation-501688a00ef4b8e5ee083c1d"
PINNED_IDENTITY = ReleaseIdentity(
    "Chitu Prospecting Integration",
    "1.9.13-alpha",
    "9ff763f5f517d14f7e0e8c15dca0c846febe471cc1d78c599ef02b8476ee2649",
    "6ef712134f581a12a18da5c98691884e73388b78",
)
PINNED_BEFORE_SHA256 = "cd0179f6d0e0e2964076994197cd956a62ac1d0c7eccc92f051cde1d559bde8d"
EXPECTED_POSTCONDITION_SHA256 = (
    "fe0c9ed6a84492c1e600c807d5df3c934e2d1192455ed743c14081b67dac86e0"
)
BASELINE_STEP_ID = "baseline:navigation_default_to_phase3c19_ia_v1"
NAVIGATION_STEP_ID = navigation.DURABLE_STEP_ID
REQUIRED_MODULES = navigation.REQUIRED_MODULES

NavigationItem = navigation.NavigationItem


class TabListSurface(Protocol):
    """Bounded host navigation surface; ``config.tabList`` only."""

    write_count: int
    business_data_touched: bool

    def read_top_level(self) -> list[NavigationItem]:
        """Return the current top-level navigation list."""

    def write_top_level(self, items: list[NavigationItem]) -> None:
        """Replace the top-level navigation list with the exact target."""


@dataclass(frozen=True)
class RegistrationProof:
    """Read-only extension/module proof; never triggers install or rebuild."""

    extension_registered: bool
    available_modules: frozenset[str]


@dataclass(frozen=True)
class StructuredDiff:
    """Identity/position-only diff; contains no secrets or business payloads."""

    removed: tuple[str, ...]
    added: tuple[str, ...]
    reordered: tuple[str, ...]
    before_count: int
    after_count: int


@dataclass(frozen=True)
class BaselinePreparationResult:
    """Redacted administrative result for one explicit baseline attempt."""

    success: bool
    failure_code: str | None
    installation_id: str | None
    state: InstallationState | None
    recovery_disposition: RecoveryDisposition | None
    before_checksum: str | None
    after_checksum: str | None
    target_source_checksum: str | None
    target_canonical_checksum: str | None
    postcondition_checksum: str | None
    diff: StructuredDiff | None
    write_count: int
    business_data_touched: bool
    baseline_step_outcome: str | None
    idempotent_noop: bool = False


@dataclass
class InMemoryTabListSurface:
    """Deterministic fixture surface for focused tests."""

    items: list[NavigationItem] = field(default_factory=list)
    write_count: int = 0
    business_data_touched: bool = False

    def __post_init__(self) -> None:
        self.items = [self._copy(item) for item in self.items]

    def read_top_level(self) -> list[NavigationItem]:
        return [self._copy(item) for item in self.items]

    def write_top_level(self, items: list[NavigationItem]) -> None:
        self.write_count += 1
        self.items = [self._copy(item) for item in items]

    @staticmethod
    def _copy(item: NavigationItem) -> NavigationItem:
        if isinstance(item, dict):
            return dict(item)
        return item


class NavigationBaselinePreparation:
    """Explicit, lock-scoped baseline preparation for the pinned default layout."""

    def __init__(
        self,
        ledger_interaction: ProvisioningLedgerInteraction,
        surface: TabListSurface,
        registration_proof: RegistrationProof,
        definition_path: Path = DEFAULT_DEFINITION,
        *,
        expected_installation_id: str = PINNED_INSTALLATION_ID,
        expected_identity: ReleaseIdentity = PINNED_IDENTITY,
        pinned_before_sha256: str = PINNED_BEFORE_SHA256,
    ) -> None:
        self._ledger = ledger_interaction
        self._surface = surface
        self._registration = registration_proof
        self._definition_path = definition_path
        self._expected_installation_id = expected_installation_id
        self._expected_identity = expected_identity
        self._pinned_before_sha256 = pinned_before_sha256

    def prepare(self) -> BaselinePreparationResult:
        """Perform one explicit baseline preparation attempt."""

        try:
            with self._ledger.locked():
                return self._prepare_locked()
        except (InstallationLockError, LedgerInteractionLockError):
            return self._rejected("LEDGER_LOCK_UNAVAILABLE")
        except LedgerCorruptionError:
            return self._rejected("LEDGER_CORRUPT")

    def _prepare_locked(self) -> BaselinePreparationResult:
        recovery = self._ledger.recover(self._expected_identity)
        if recovery.disposition != RecoveryDisposition.FAILED_PRESERVED:
            return self._rejected(
                "LEDGER_STATE_INVALID",
                recovery.disposition,
                recovery.record.state if recovery.record else None,
                recovery.record.installation_id if recovery.record else None,
            )
        record = recovery.record
        assert record is not None
        if record.state != InstallationState.FAILED:
            return self._fail_closed(record, "LEDGER_STATE_INVALID", wrote=False)
        if record.installation_id != self._expected_installation_id:
            return self._fail_closed(record, "IDENTITY_MISMATCH", wrote=False)
        if record.identity != self._expected_identity:
            return self._fail_closed(record, "IDENTITY_MISMATCH", wrote=False)
        if not self._has_failed_navigation_step(record.events):
            return self._fail_closed(record, "NAVIGATION_FAILURE_EVIDENCE_ABSENT", wrote=False)

        if (
            not self._registration.extension_registered
            or not REQUIRED_MODULES.issubset(self._registration.available_modules)
        ):
            return self._fail_closed(record, "NAVIGATION_DEPENDENCY_UNAVAILABLE", wrote=False)

        try:
            target, source_sha, canonical_sha = self._load_target()
        except _PreparationFailure as error:
            return self._fail_closed(record, error.code, wrote=False)

        postcondition_sha = navigation.sha256_hex(navigation.canonical_json_bytes(target))
        if (
            source_sha != navigation.SOURCE_BYTE_SHA256
            or canonical_sha != navigation.CANONICAL_DEFINITION_SHA256
            or postcondition_sha != EXPECTED_POSTCONDITION_SHA256
        ):
            return self._fail_closed(record, "NAVIGATION_DEFINITION_MISMATCH", wrote=False)

        try:
            before = self._normalize_list(self._surface.read_top_level())
        except ValueError:
            return self._fail_closed(record, "NAVIGATION_BASELINE_UNRECOGNIZED", wrote=False)

        before_checksum = navigation.sha256_hex(navigation.canonical_json_bytes(before))
        if before_checksum == postcondition_sha:
            return self._idempotent_success(
                record,
                before_checksum=before_checksum,
                after_checksum=before_checksum,
                source_sha=source_sha,
                canonical_sha=canonical_sha,
                postcondition_sha=postcondition_sha,
                before=before,
                target=target,
            )

        if before_checksum != self._pinned_before_sha256:
            return self._fail_closed(
                record,
                "BASELINE_CHECKSUM_MISMATCH",
                wrote=False,
                before_checksum=before_checksum,
                source_sha=source_sha,
                canonical_sha=canonical_sha,
                postcondition_sha=postcondition_sha,
                diff=self._diff(before, target),
            )

        diff = self._diff(before, target)
        self._surface.write_top_level(target)
        try:
            after = self._normalize_list(self._surface.read_top_level())
        except ValueError:
            updated = self._ledger.record_step_result(
                self._expected_identity,
                record.installation_id,
                BASELINE_STEP_ID,
                "failed",
            )
            return self._result(
                False,
                "NAVIGATION_READBACK_MISMATCH",
                updated,
                recovery.disposition,
                before_checksum,
                None,
                source_sha,
                canonical_sha,
                postcondition_sha,
                diff,
                False,
            )

        after_checksum = navigation.sha256_hex(navigation.canonical_json_bytes(after))
        if after != target or after_checksum != postcondition_sha:
            updated = self._ledger.record_step_result(
                self._expected_identity,
                record.installation_id,
                BASELINE_STEP_ID,
                "failed",
            )
            return self._result(
                False,
                "NAVIGATION_READBACK_MISMATCH",
                updated,
                recovery.disposition,
                before_checksum,
                after_checksum,
                source_sha,
                canonical_sha,
                postcondition_sha,
                diff,
                False,
            )

        updated = self._ledger.record_step_result(
            self._expected_identity,
            record.installation_id,
            BASELINE_STEP_ID,
            "succeeded",
        )
        assert updated.state == InstallationState.FAILED
        return self._result(
            True,
            None,
            updated,
            recovery.disposition,
            before_checksum,
            after_checksum,
            source_sha,
            canonical_sha,
            postcondition_sha,
            diff,
            False,
            baseline_step_outcome="succeeded",
        )

    def _idempotent_success(
        self,
        record,
        *,
        before_checksum: str,
        after_checksum: str,
        source_sha: str,
        canonical_sha: str,
        postcondition_sha: str,
        before: list[NavigationItem],
        target: list[NavigationItem],
    ) -> BaselinePreparationResult:
        if self._has_succeeded_baseline_step(record.events):
            return self._result(
                True,
                None,
                record,
                RecoveryDisposition.FAILED_PRESERVED,
                before_checksum,
                after_checksum,
                source_sha,
                canonical_sha,
                postcondition_sha,
                self._diff(before, target),
                True,
                baseline_step_outcome="succeeded",
            )
        updated = self._ledger.record_step_result(
            self._expected_identity,
            record.installation_id,
            BASELINE_STEP_ID,
            "succeeded",
        )
        assert updated.state == InstallationState.FAILED
        return self._result(
            True,
            None,
            updated,
            RecoveryDisposition.FAILED_PRESERVED,
            before_checksum,
            after_checksum,
            source_sha,
            canonical_sha,
            postcondition_sha,
            self._diff(before, target),
            True,
            baseline_step_outcome="succeeded",
        )

    def _load_target(self) -> tuple[list[NavigationItem], str, str]:
        try:
            raw = self._definition_path.read_bytes()
        except OSError as error:
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH") from error
        source_sha = navigation.sha256_hex(raw)
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH") from error
        if not isinstance(document, dict):
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH")
        if document.get("schemaVersion") != 1:
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH")
        if document.get("navigationVersion") != navigation.NAVIGATION_VERSION:
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH")
        canonical_sha = navigation.sha256_hex(navigation.canonical_json_bytes(document))
        top_level = document.get("topLevelOrder")
        if not isinstance(top_level, list):
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH")
        try:
            items = self._normalize_list(top_level)
        except ValueError as error:
            raise _PreparationFailure("NAVIGATION_DEFINITION_MISMATCH") from error
        return items, source_sha, canonical_sha

    @staticmethod
    def _normalize_list(items: list[object]) -> list[NavigationItem]:
        return [navigation.normalize_navigation_item(item) for item in items]

    @staticmethod
    def _format_identity(item: NavigationItem) -> str:
        identity = navigation.item_identity(item)
        if identity[0] == "module":
            return f"module:{identity[1]}"
        return f"divider:{identity[1]}:{identity[2]}"

    @classmethod
    def _diff(
        cls, before: list[NavigationItem], after: list[NavigationItem]
    ) -> StructuredDiff:
        before_ids = [cls._format_identity(item) for item in before]
        after_ids = [cls._format_identity(item) for item in after]
        before_set = set(before_ids)
        after_set = set(after_ids)
        removed = tuple(sorted(before_set - after_set))
        added = tuple(sorted(after_set - before_set))
        shared = before_set & after_set
        reordered = tuple(
            sorted(
                item
                for item in shared
                if before_ids.index(item) != after_ids.index(item)
            )
        )
        return StructuredDiff(
            removed=removed,
            added=added,
            reordered=reordered,
            before_count=len(before),
            after_count=len(after),
        )

    @staticmethod
    def _has_failed_navigation_step(events) -> bool:
        return any(
            event.kind == "step"
            and event.value == NAVIGATION_STEP_ID
            and event.outcome == "failed"
            for event in events
        )

    @staticmethod
    def _has_succeeded_baseline_step(events) -> bool:
        return any(
            event.kind == "step"
            and event.value == BASELINE_STEP_ID
            and event.outcome == "succeeded"
            for event in events
        )

    def _fail_closed(
        self,
        record,
        code: str,
        *,
        wrote: bool,
        before_checksum: str | None = None,
        source_sha: str | None = None,
        canonical_sha: str | None = None,
        postcondition_sha: str | None = None,
        diff: StructuredDiff | None = None,
    ) -> BaselinePreparationResult:
        updated = record
        baseline_outcome = None
        if wrote:
            updated = self._ledger.record_step_result(
                self._expected_identity,
                record.installation_id,
                BASELINE_STEP_ID,
                "failed",
            )
            baseline_outcome = "failed"
        return self._result(
            False,
            code,
            updated,
            RecoveryDisposition.FAILED_PRESERVED,
            before_checksum,
            None,
            source_sha,
            canonical_sha,
            postcondition_sha,
            diff,
            False,
            baseline_step_outcome=baseline_outcome,
        )

    def _result(
        self,
        success: bool,
        failure_code: str | None,
        record,
        disposition: RecoveryDisposition | None,
        before_checksum: str | None,
        after_checksum: str | None,
        source_sha: str | None,
        canonical_sha: str | None,
        postcondition_sha: str | None,
        diff: StructuredDiff | None,
        idempotent_noop: bool,
        baseline_step_outcome: str | None = None,
    ) -> BaselinePreparationResult:
        return BaselinePreparationResult(
            success=success,
            failure_code=failure_code,
            installation_id=record.installation_id if record else None,
            state=record.state if record else None,
            recovery_disposition=disposition,
            before_checksum=before_checksum,
            after_checksum=after_checksum,
            target_source_checksum=source_sha,
            target_canonical_checksum=canonical_sha,
            postcondition_checksum=postcondition_sha,
            diff=diff,
            write_count=self._surface.write_count,
            business_data_touched=self._surface.business_data_touched,
            baseline_step_outcome=baseline_step_outcome
            if baseline_step_outcome is not None
            else ("succeeded" if success else None),
            idempotent_noop=idempotent_noop,
        )

    @staticmethod
    def _rejected(
        failure_code: str,
        disposition: RecoveryDisposition | None = None,
        state: InstallationState | None = None,
        installation_id: str | None = None,
    ) -> BaselinePreparationResult:
        return BaselinePreparationResult(
            success=False,
            failure_code=failure_code,
            installation_id=installation_id,
            state=state,
            recovery_disposition=disposition,
            before_checksum=None,
            after_checksum=None,
            target_source_checksum=None,
            target_canonical_checksum=None,
            postcondition_checksum=None,
            diff=None,
            write_count=0,
            business_data_touched=False,
            baseline_step_outcome=None,
        )


class _PreparationFailure(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def coerce_host_tab_list(items: list[object]) -> list[NavigationItem]:
    """Normalize host tabList, coercing null divider text to empty string."""

    coerced: list[object] = []
    for item in items:
        if isinstance(item, dict) and item.get("type") == "divider":
            coerced.append(
                {
                    "type": "divider",
                    "id": str(item.get("id") or ""),
                    "text": item["text"] if isinstance(item.get("text"), str) else "",
                }
            )
        else:
            coerced.append(item)
    return [navigation.normalize_navigation_item(item) for item in coerced]


@dataclass
class DockerTabListSurface:
    """EspoCRM ``config.tabList`` bridge via reviewed temporary PHP surface."""

    container: str = "espocrm-c25-staging-espocrm-1"
    surface_php: str = "/tmp/tablist_surface.php"
    write_count: int = 0
    business_data_touched: bool = False

    def read_top_level(self) -> list[NavigationItem]:
        self._docker(
            [
                "exec",
                self.container,
                "php",
                self.surface_php,
                "read",
                "/tmp/dp_wp2_tablist_read.json",
            ]
        )
        local = ROOT / "temp" / "dp-wp2-navigation-runtime" / "tablist_read.json"
        local.parent.mkdir(parents=True, exist_ok=True)
        self._docker(["cp", f"{self.container}:/tmp/dp_wp2_tablist_read.json", str(local)])
        items = json.loads(local.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            raise RuntimeError("tabList read did not return a list")
        return coerce_host_tab_list(items)

    def write_top_level(self, items: list[NavigationItem]) -> None:
        payload = ROOT / "temp" / "dp-wp2-navigation-runtime" / "baseline_write_payload.json"
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text(
            json.dumps(items, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        self._docker(["cp", str(payload), f"{self.container}:/tmp/dp_wp2_baseline_write.json"])
        self._docker(
            [
                "exec",
                self.container,
                "php",
                self.surface_php,
                "write",
                "/tmp/dp_wp2_baseline_write.json",
            ]
        )
        self.write_count += 1

    @staticmethod
    def _docker(args: list[str]) -> str:
        completed = subprocess.run(
            ["docker", *args],
            check=True,
            capture_output=True,
        )
        stdout = completed.stdout.decode("utf-8", errors="strict") if completed.stdout else ""
        return stdout.strip()


def read_only_registration_proof(container: str = "espocrm-c25-staging-espocrm-1") -> RegistrationProof:
    """Collect read-only extension/module proof from staging."""

    listing = subprocess.run(
        ["docker", "exec", container, "php", "command.php", "extension", "--list"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    registered = (
        "Chitu Prospecting Integration" in listing
        and "1.9.13-alpha" in listing
        and "Installed: yes" in listing
    )
    probe = ROOT / "temp" / "dp-wp2-navigation-runtime" / "probe_navigation.php"
    if probe.exists():
        subprocess.run(
            ["docker", "cp", str(probe), f"{container}:/tmp/probe_navigation.php"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["docker", "exec", container, "php", "/tmp/probe_navigation.php"],
            check=True,
            capture_output=True,
            text=True,
        )
        local = ROOT / "temp" / "dp-wp2-navigation-runtime" / "dp_wp2_nav_probe_live.json"
        subprocess.run(
            ["docker", "cp", f"{container}:/tmp/dp_wp2_nav_probe.json", str(local)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(local.read_text(encoding="utf-8"))
        modules = frozenset(
            name
            for name, info in payload.get("modules", {}).items()
            if info.get("present") is True
        )
    else:
        modules = frozenset()
    return RegistrationProof(extension_registered=registered, available_modules=modules)


def main() -> int:
    """Explicit operator entrypoint for one controlled baseline preparation run."""

    ledger = JsonFileInstallationLedger(DEFAULT_LEDGER)
    surface = DockerTabListSurface()
    proof = read_only_registration_proof()
    runner = NavigationBaselinePreparation(
        ProvisioningLedgerInteraction(ledger),
        surface,
        proof,
    )
    result = runner.prepare()
    print(
        json.dumps(
            {
                "success": result.success,
                "failure_code": result.failure_code,
                "state": None if result.state is None else result.state.value,
                "before_checksum": result.before_checksum,
                "after_checksum": result.after_checksum,
                "postcondition_checksum": result.postcondition_checksum,
                "write_count": result.write_count,
                "idempotent_noop": result.idempotent_noop,
                "baseline_step_outcome": result.baseline_step_outcome,
                "business_data_touched": result.business_data_touched,
                "diff": None
                if result.diff is None
                else {
                    "before_count": result.diff.before_count,
                    "after_count": result.diff.after_count,
                    "removed_count": len(result.diff.removed),
                    "added_count": len(result.diff.added),
                    "reordered_count": len(result.diff.reordered),
                    "removed": list(result.diff.removed),
                    "added": list(result.diff.added),
                    "reordered": list(result.diff.reordered),
                },
            },
            indent=2,
        )
    )
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
