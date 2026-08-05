"""DP-WP2 Stage-2 navigation_provisioning report-only adapter.

Implements the ratified navigation target contract as a ReportOnlyPhaseAdapter.
It never advances lifecycle state, never calls AfterInstall/hooks/migrations,
and never mutates ACL, roles, teams, dashboards, Railway, or CRM business data.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from scripts.dp_wp1_installation_foundation import ReleaseIdentity
from scripts.dp_wp2_phase_adapter_contract import (
    IdempotencyContract,
    IdempotencyMode,
    PhaseAdapterInput,
    PhaseAdapterOutput,
    PhaseOutcome,
    PhasePostcondition,
    RedactedFailure,
)

PHASE_NAME = "navigation_provisioning"
POSTCONDITION_NAME = "navigation_state_matches_definition"
DURABLE_STEP_ID = (
    "adapter:navigation_provisioning:postcondition:navigation_state_matches_definition"
)
NAVIGATION_VERSION = "phase3c19-ia-v1"
SOURCE_BYTE_SHA256 = "ad0eb26d685be89695551ef968833e81ada660affecd618ed0bd3b39b0056a9e"
CANONICAL_DEFINITION_SHA256 = (
    "bfd9319e53dfb9e05ac5ef851965fd1853424984853668e51c6e8e344960d9d6"
)
IDEMPOTENCY_KEY = (
    f"navigation:{NAVIGATION_VERSION}:{CANONICAL_DEFINITION_SHA256}"
)
REQUIRED_MODULES = frozenset(
    {"ProspectingDashboard", "ProspectingSearch", "DraftApproval"}
)

NavigationItem = str | dict[str, str]


@dataclass(frozen=True)
class NavigationDependencyEvidence:
    """Release-bound DP-WP1 registration/metadata proof consumed by the adapter."""

    installation_id: str
    identity: ReleaseIdentity
    extension_registered: bool
    available_modules: frozenset[str]
    ledger_state: str


class NavigationSurface(Protocol):
    """Bounded top-level navigation configuration surface (no business data)."""

    def read_top_level(self) -> list[NavigationItem]:
        """Return the current top-level navigation list."""

    def write_top_level(self, items: list[NavigationItem]) -> None:
        """Replace the top-level navigation list with the exact target."""


class InMemoryNavigationSurface:
    """Deterministic test/runtime fixture surface; stores navigation items only."""

    def __init__(self, items: list[NavigationItem] | None = None) -> None:
        self._items = [self._copy_item(item) for item in (items or [])]
        self.write_count = 0
        self.business_data_touched = False

    def read_top_level(self) -> list[NavigationItem]:
        return [self._copy_item(item) for item in self._items]

    def write_top_level(self, items: list[NavigationItem]) -> None:
        self.write_count += 1
        self._items = [self._copy_item(item) for item in items]

    @staticmethod
    def _copy_item(item: NavigationItem) -> NavigationItem:
        if isinstance(item, dict):
            return dict(item)
        return item


def navigation_idempotency_contract() -> IdempotencyContract:
    """Return the ratified idempotency contract for this adapter."""

    return IdempotencyContract(
        key=IDEMPOTENCY_KEY,
        mode=IdempotencyMode.REVALIDATE_AND_NOOP,
    )


def canonical_json_bytes(value: object) -> bytes:
    """Serialize with recursive Unicode key order and literal UTF-8 characters."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize_navigation_item(item: object) -> NavigationItem:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        if item.get("type") != "divider":
            raise ValueError("unsupported navigation item")
        divider_id = item.get("id")
        text = item.get("text")
        if not isinstance(divider_id, str) or not isinstance(text, str):
            raise ValueError("divider requires id and text")
        return {"type": "divider", "id": divider_id, "text": text}
    raise ValueError("unsupported navigation item type")


def item_identity(item: NavigationItem) -> tuple[object, ...]:
    if isinstance(item, str):
        return ("module", item)
    return ("divider", item["id"], item["text"])


class NavigationProvisioningAdapter:
    """Report-only navigation provisioning adapter for DP-WP2 Stage-2."""

    def __init__(
        self,
        surface: NavigationSurface,
        definition_path: Path,
        dependency_evidence: NavigationDependencyEvidence,
    ) -> None:
        self._surface = surface
        self._definition_path = definition_path
        self._dependency_evidence = dependency_evidence

    def report(self, request: PhaseAdapterInput) -> PhaseAdapterOutput:
        """Apply or revalidate navigation; never advance lifecycle state."""

        failure = self._validate_request(request)
        if failure is not None:
            return self._failed(request, failure)

        try:
            target = self._load_and_verify_target()
        except _AdapterFailure as error:
            return self._failed(request, error.failure)

        dependency_failure = self._dependency_failure(request)
        if dependency_failure is not None:
            return self._failed(request, dependency_failure)

        current = [normalize_navigation_item(item) for item in self._surface.read_top_level()]
        if current == target:
            return self._succeeded(request, target)

        if not self._is_recognized_baseline(current, target):
            return self._failed(
                request,
                RedactedFailure(
                    "NAVIGATION_BASELINE_UNRECOGNIZED",
                    "current navigation is outside the approved bounded baseline",
                ),
            )

        module_failure = self._module_availability_failure(target)
        if module_failure is not None:
            return self._failed(request, module_failure)

        self._surface.write_top_level(target)
        readback = [normalize_navigation_item(item) for item in self._surface.read_top_level()]
        if readback != target:
            return self._failed(
                request,
                RedactedFailure(
                    "NAVIGATION_READBACK_MISMATCH",
                    "navigation read-back does not match the approved target",
                ),
            )
        return self._succeeded(request, readback)

    def _validate_request(self, request: PhaseAdapterInput) -> RedactedFailure | None:
        if request.phase_name != PHASE_NAME:
            return RedactedFailure(
                "NAVIGATION_DEFINITION_MISMATCH",
                "phase name is not navigation_provisioning",
            )
        expected = navigation_idempotency_contract()
        if request.idempotency != expected:
            return RedactedFailure(
                "NAVIGATION_DEFINITION_MISMATCH",
                "navigation idempotency contract does not match the ratified target",
            )
        return None

    def _load_and_verify_target(self) -> list[NavigationItem]:
        try:
            raw = self._definition_path.read_bytes()
        except OSError as error:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation target definition cannot be read",
                )
            ) from error

        if sha256_hex(raw) != SOURCE_BYTE_SHA256:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation source-byte checksum does not match the ratified contract",
                )
            )

        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation target definition is not valid JSON",
                )
            ) from error

        if not isinstance(document, dict):
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation target definition root must be an object",
                )
            )
        if document.get("schemaVersion") != 1:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation schemaVersion is not the ratified value",
                )
            )
        if document.get("navigationVersion") != NAVIGATION_VERSION:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigationVersion is not the ratified value",
                )
            )
        if sha256_hex(canonical_json_bytes(document)) != CANONICAL_DEFINITION_SHA256:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation canonical checksum does not match the ratified contract",
                )
            )

        top_level = document.get("topLevelOrder")
        if not isinstance(top_level, list):
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation topLevelOrder must be an array",
                )
            )
        try:
            return [normalize_navigation_item(item) for item in top_level]
        except ValueError as error:
            raise _AdapterFailure(
                RedactedFailure(
                    "NAVIGATION_DEFINITION_MISMATCH",
                    "navigation topLevelOrder contains an unsupported item",
                )
            ) from error

    def _dependency_failure(self, request: PhaseAdapterInput) -> RedactedFailure | None:
        evidence = self._dependency_evidence
        if (
            evidence.installation_id != request.installation_id
            or evidence.identity != request.identity
            or evidence.ledger_state != "REGISTERED"
            or not evidence.extension_registered
            or not REQUIRED_MODULES.issubset(evidence.available_modules)
        ):
            return RedactedFailure(
                "NAVIGATION_DEPENDENCY_UNAVAILABLE",
                "DP-WP1 registration or module availability evidence is incomplete",
            )
        return None

    def _module_availability_failure(
        self, target: list[NavigationItem]
    ) -> RedactedFailure | None:
        required = {
            item for item in target if isinstance(item, str) and item in REQUIRED_MODULES
        }
        if not required.issubset(self._dependency_evidence.available_modules):
            return RedactedFailure(
                "NAVIGATION_MODULE_UNAVAILABLE",
                "an allowlisted extension navigation module is unavailable",
            )
        return None

    @staticmethod
    def _is_recognized_baseline(
        current: list[NavigationItem], target: list[NavigationItem]
    ) -> bool:
        if len(current) != len(target):
            return False
        current_ids = sorted(item_identity(item) for item in current)
        target_ids = sorted(item_identity(item) for item in target)
        return current_ids == target_ids

    def _succeeded(
        self, request: PhaseAdapterInput, items: list[NavigationItem]
    ) -> PhaseAdapterOutput:
        evidence = f"sha256:{sha256_hex(canonical_json_bytes(items))}"
        return PhaseAdapterOutput(
            installation_id=request.installation_id,
            identity=request.identity,
            phase_name=request.phase_name,
            idempotency=request.idempotency,
            outcome=PhaseOutcome.SUCCEEDED,
            postcondition=PhasePostcondition(
                name=POSTCONDITION_NAME,
                satisfied=True,
                evidence=evidence,
            ),
        )

    @staticmethod
    def _failed(
        request: PhaseAdapterInput, failure: RedactedFailure
    ) -> PhaseAdapterOutput:
        return PhaseAdapterOutput(
            installation_id=request.installation_id,
            identity=request.identity,
            phase_name=request.phase_name,
            idempotency=request.idempotency,
            outcome=PhaseOutcome.FAILED,
            postcondition=PhasePostcondition(
                name=POSTCONDITION_NAME,
                satisfied=False,
                evidence="sha256:unsatisfied",
            ),
            failure=failure,
        )


class _AdapterFailure(Exception):
    def __init__(self, failure: RedactedFailure) -> None:
        super().__init__(failure.code)
        self.failure = failure
