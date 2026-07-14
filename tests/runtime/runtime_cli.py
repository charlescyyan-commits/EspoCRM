"""CLI for T04 runtime harness; invoked by run-runtime-tests.ps1."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from runtime_harness import (
    EXIT_CLEANUP_INCOMPLETE, EXIT_PASS, RuntimeConfigurationError, RuntimeHarnessError, RuntimeConfig,
    CleanupEngine, FixtureRegistry, RuntimeRestClient, new_run_id, run_acl, run_smoke, run_with_cleanup, validate_run_id,
)


ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = ROOT / "temp" / "test-results"


def result_path(run_id: str) -> Path:
    return RESULTS_ROOT / f"runtime-test-{run_id}.json"


def write_result(result: dict) -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    result_path(result["runId"]).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


def build_result(run_id: str, target: str, tests: list[dict], cleanup: list[dict], failures: list[str], warnings: list[str], exit_code: int, started: str) -> dict:
    cleaned = sum(item.get("cleanupResult") == "CLEANED" for item in cleanup)
    residue = sum(item.get("cleanupResult") != "CLEANED" for item in cleanup)
    return {
        "schemaVersion": "1.0", "runId": run_id, "target": target, "targetClassification": "LOCAL_ALLOWED",
        "startedAt": started, "finishedAt": datetime.now(timezone.utc).isoformat(), "overallStatus": "PASS" if exit_code == 0 else "FAIL", "exitCode": exit_code,
        "testsPassed": sum(item.get("status") == "PASS" for item in tests), "testsFailed": sum(item.get("status") == "FAIL" for item in tests), "testsSkipped": sum(item.get("status") == "SKIPPED" for item in tests),
        "fixturesCreated": len(cleanup), "fixturesCleaned": cleaned, "residueCount": residue, "tests": tests, "cleanup": cleanup, "failures": failures, "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "smoke", "acl", "cleanup-preview", "cleanup", "all"))
    parser.add_argument("--run-id")
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    run_id = args.run_id or ""
    tests: list[dict] = []
    cleanup_records: list[dict] = []
    failures: list[str] = []
    warnings: list[str] = []
    exit_code = EXIT_PASS
    target = ""
    try:
        if args.command in {"cleanup", "cleanup-preview"} and not args.run_id:
            raise RuntimeConfigurationError("--run-id is required for cleanup commands.")
        if args.run_id:
            validate_run_id(args.run_id)
        config = RuntimeConfig.from_environment()
        target = config.base_url
        run_id = run_id or new_run_id(config.prefix)
        client = RuntimeRestClient(config)
        if args.command in {"cleanup", "cleanup-preview"}:
            registry = FixtureRegistry.load(RESULTS_ROOT / f"runtime-fixtures-{run_id}.json", run_id)
            engine = CleanupEngine(client, registry)
            if args.command == "cleanup-preview":
                tests.append({"name": "cleanup-preview", "status": "PASS", "fixtures": engine.preview()})
            else:
                cleanup_records = [item.__dict__ for item in engine.cleanup()]
                residue = engine.residue_audit()
                if residue:
                    raise RuntimeHarnessError("Residue audit found registered runtime fixtures.")
                tests.append({"name": "cleanup", "status": "PASS"})
        else:
            registry = FixtureRegistry.create(RESULTS_ROOT, run_id)
            engine = CleanupEngine(client, registry)
            if args.command == "check":
                from runtime_harness import expect_status
                expect_status("authentication", client.request("GET", "App/user"), {200})
                tests.append({"name": "environment", "status": "PASS"})
            elif args.command in {"smoke", "all"}:
                smoke_results, cleanup = run_with_cleanup(client, registry, lambda: run_smoke(client, registry, run_id))
                tests.extend(smoke_results)
                cleanup_records = [item.__dict__ for item in cleanup]
            if args.command in {"acl", "all"}:
                tests.extend(run_acl(client, run_id))
    except RuntimeHarnessError as error:
        failures.append(str(error))
        exit_code = error.exit_code
        tests.append({"name": args.command, "status": "FAIL"})
    if cleanup_records and any(item.get("cleanupResult") != "CLEANED" for item in cleanup_records):
        exit_code = EXIT_CLEANUP_INCOMPLETE
    run_id = run_id or "UNAVAILABLE"
    result = build_result(run_id, target, tests, cleanup_records, failures, warnings, exit_code, started)
    try:
        write_result(result)
    except OSError:
        return EXIT_CLEANUP_INCOMPLETE
    print(json.dumps(result, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
