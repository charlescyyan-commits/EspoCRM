"""Phase3C20 WP0.3 ADR-C20 boundary guards.

Static offline guards for prohibited patterns. WP1.1 may add an isolated
AIPlatform namespace skeleton, but no provider runtime is introduced here.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTENSION = ROOT / "crm-extension"
PHP_ROOT = EXTENSION / "files"
CUSTOM_ESPO = PHP_ROOT / "custom" / "Espo"
MODULES = CUSTOM_ESPO / "Modules"
AI_PLATFORM = MODULES / "AIPlatform"
PROSPECTING = MODULES / "Prospecting"
SELECT_ROOT = PROSPECTING / "Classes" / "Select"
CLIENT_DEFS = PROSPECTING / "Resources" / "metadata" / "clientDefs"
ENTITY_DEFS = PROSPECTING / "Resources" / "metadata" / "entityDefs"
SCOPES = PROSPECTING / "Resources" / "metadata" / "scopes"

PROVIDER_HOST_MARKERS = (
    "api.openai.com",
    "api.anthropic.com",
    "api.deepseek.com",
    "api.moonshot.cn",
    "apify.com",
    "serper.dev",
    "api.hunter.io",
    "api.apollo.io",
    "generativelanguage.googleapis.com",
)

PHP_EGRESS_PATTERNS = (
    re.compile(r"\bcurl_init\s*\("),
    re.compile(r"\bcurl_exec\s*\("),
    re.compile(r"\bfile_get_contents\s*\(\s*['\"]https?://", re.IGNORECASE),
    re.compile(r"\bfsockopen\s*\("),
    re.compile(r"\bstream_socket_client\s*\("),
    re.compile(r"\bGuzzleHttp\\"),
    re.compile(r"\bnew\s+\\?GuzzleHttp\\Client\b"),
)

SCORING_FORBIDDEN_PATH_GLOBS = (
    "*AIScore*",
    "*CanonicalScore*",
    "*AiScore*",
)

SCORING_FORBIDDEN_CODE = (
    re.compile(r"\bclass\s+AIScore\b"),
    re.compile(r"\bcomputeCanonicalScore\b"),
    re.compile(r"\bcalculateCanonicalScore\b"),
    re.compile(r"\bmutateCanonicalScore\b"),
    re.compile(r"['\"]canonical_score['\"]\s*=>"),
    re.compile(r"->set\(\s*['\"]canonical_score['\"]"),
    re.compile(r"update_record\(\s*['\"]canonical_score['\"]"),
)

LIFECYCLE_MUTATION_FROM_AI = (
    re.compile(r"AIQualificationInsight.*(ProspectPool|Lead|qualificationStatus|peQualification)", re.IGNORECASE | re.DOTALL),
    re.compile(r"(ProspectPool|Lead).*AIQualificationInsight.*(set|saveEntity|transition)", re.IGNORECASE | re.DOTALL),
)

QUEUE_AUTHORITY_MARKERS = (
    "AIQualificationInsight",
    "c20AiQualification",
    "aiQualificationInsight",
)


def iter_php_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.php") if path.is_file())


def iter_text_files(root: Path, suffixes: set[str]) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in suffixes
    )


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class Phase3C20WP0BoundaryGuardTests(unittest.TestCase):
    """ADR-C20 prohibited-pattern guards (WP0.3)."""

    # ------------------------------------------------------------------
    # 1. Provider egress boundary
    # ------------------------------------------------------------------

    def test_php_runtime_has_no_direct_provider_egress(self) -> None:
        violations: list[str] = []
        for path in iter_php_files(PHP_ROOT):
            text = read(path)
            relative = path.relative_to(ROOT).as_posix()
            for pattern in PHP_EGRESS_PATTERNS:
                if pattern.search(text):
                    violations.append(f"{relative}: matches {pattern.pattern}")
            lowered = text.casefold()
            for host in PROVIDER_HOST_MARKERS:
                if host.casefold() in lowered:
                    violations.append(f"{relative}: provider host marker {host!r}")
        self.assertEqual(
            violations,
            [],
            msg="PHP must not call external AI/provider APIs directly; egress is connector-only.\n"
            + "\n".join(violations),
        )

    def test_connector_remains_sole_documented_egress_owner(self) -> None:
        # An approved WP1.1 namespace may now exist; connector providers remain
        # the sole documented egress owner.
        connector_providers = (
            ROOT
            / "chitu-connector"
            / "chitu_connector"
            / "acquisition"
            / "providers"
        )
        self.assertTrue(connector_providers.is_dir())
        self.assertTrue((connector_providers / "base.py").is_file())

    # ------------------------------------------------------------------
    # 2. Scoring ownership boundary
    # ------------------------------------------------------------------

    def test_no_aiscore_entity_or_artifacts(self) -> None:
        offenders: list[str] = []
        for pattern in SCORING_FORBIDDEN_PATH_GLOBS:
            for path in EXTENSION.rglob(pattern):
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [], msg="AIScore / CanonicalScore CRM artifacts are forbidden")

    def test_crm_php_does_not_mutate_or_compute_canonical_score(self) -> None:
        violations: list[str] = []
        for path in iter_php_files(PHP_ROOT):
            text = read(path)
            relative = path.relative_to(ROOT).as_posix()
            for pattern in SCORING_FORBIDDEN_CODE:
                if pattern.search(text):
                    violations.append(f"{relative}: matches {pattern.pattern}")
        self.assertEqual(
            violations,
            [],
            msg="CRM must not create authoritative AI scoring or mutate canonical_score.\n"
            + "\n".join(violations),
        )

    def test_no_aiscore_scope_or_entity_defs(self) -> None:
        for folder in (ENTITY_DEFS, SCOPES):
            if not folder.is_dir():
                continue
            for path in folder.glob("*Score*.json"):
                self.assertNotIn(
                    "aiscore",
                    path.stem.casefold(),
                    msg=f"Forbidden score scope/entityDefs artifact: {path}",
                )
            self.assertFalse((folder / "AIScore.json").exists())

    # ------------------------------------------------------------------
    # 3. Lifecycle ownership boundary
    # ------------------------------------------------------------------

    def test_no_ai_qualification_insight_lifecycle_writer(self) -> None:
        insight_paths = list(EXTENSION.rglob("*AIQualificationInsight*"))
        self.assertEqual(
            insight_paths,
            [],
            msg="AIQualificationInsight must not exist yet; lifecycle mutation via insight is forbidden",
        )

    def test_ai_related_surfaces_cannot_mutate_prospect_lifecycle(self) -> None:
        """Guard: no AI* service/controller may write ProspectPool/Lead lifecycle fields."""
        violations: list[str] = []
        ai_named = [
            path
            for path in iter_text_files(PHP_ROOT, {".php", ".js", ".json"})
            if path.name.startswith("AI")
            or "AIQualification" in path.as_posix()
            or "AIPlatform" in path.as_posix()
            or "AIScore" in path.as_posix()
            or "AIJob" in path.as_posix()
        ]
        lifecycle_markers = (
            "ProspectPool",
            "qualificationStatus",
            "peQualification",
            "pipelineStage",
        )
        for path in ai_named:
            text = read(path)
            relative = path.relative_to(ROOT).as_posix()
            if "AIQualificationInsight" in text and any(marker in text for marker in lifecycle_markers):
                if re.search(r"->set\(|saveEntity\(|transition\(", text):
                    violations.append(relative)
            for pattern in LIFECYCLE_MUTATION_FROM_AI:
                if pattern.search(text):
                    violations.append(f"{relative}: lifecycle coupling pattern")
        self.assertEqual(violations, [])

    def test_prospecting_transition_owners_do_not_read_ai_qualification_insight(self) -> None:
        transition_services = (
            PROSPECTING / "Services" / "SendExecutionTransitionService.php",
            PROSPECTING / "Services" / "ReplyTriageService.php",
            PROSPECTING / "Services" / "QuoteTransitionService.php",
            PROSPECTING / "Services" / "ApprovalService.php",
        )
        for path in transition_services:
            with self.subTest(service=path.name):
                self.assertTrue(path.is_file(), msg=f"Missing transition owner: {path}")
                text = read(path)
                self.assertNotIn("AIQualificationInsight", text)
                self.assertNotIn("AIScore", text)

    # ------------------------------------------------------------------
    # 4. Queue authority boundary
    # ------------------------------------------------------------------

    def test_ai_qualification_insight_is_not_primary_filter_authority(self) -> None:
        violations: list[str] = []
        if SELECT_ROOT.is_dir():
            for path in SELECT_ROOT.rglob("*.php"):
                if "PrimaryFilters" not in path.parts:
                    continue
                text = read(path)
                for marker in QUEUE_AUTHORITY_MARKERS:
                    if marker in text:
                        violations.append(f"{path.relative_to(ROOT).as_posix()}: {marker}")
            # Also reject a dedicated Select/AIQualificationInsight tree.
            insight_select = SELECT_ROOT / "AIQualificationInsight"
            if insight_select.exists():
                violations.append(insight_select.relative_to(ROOT).as_posix())
        if CLIENT_DEFS.is_dir():
            for path in CLIENT_DEFS.glob("*.json"):
                text = read(path)
                for marker in QUEUE_AUTHORITY_MARKERS:
                    if marker in text:
                        violations.append(f"{path.relative_to(ROOT).as_posix()}: {marker}")
        self.assertEqual(
            violations,
            [],
            msg="AIQualificationInsight must not become PrimaryFilter or queue ranking authority.\n"
            + "\n".join(violations),
        )

    def test_no_c20_ai_queue_filter_class_names(self) -> None:
        if not SELECT_ROOT.is_dir():
            self.skipTest("Prospecting Select tree missing")
        forbidden_names = (
            "C20AiQualification",
            "AiQualificationInsight",
            "AIQualificationQueue",
            "C20FailedAiInsight",
        )
        found = [
            path.relative_to(ROOT).as_posix()
            for path in SELECT_ROOT.rglob("*.php")
            if path.stem in forbidden_names
        ]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
