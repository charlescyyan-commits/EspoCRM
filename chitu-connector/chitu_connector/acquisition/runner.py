"""Single-job CLI runner using the deterministic fake provider only."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
import sys
from time import monotonic
from typing import Any, Callable, Mapping, Sequence

from .espo_repository import EspoAcquisitionRepository
from .fake_provider import DeterministicFakeProvider
from .models import JobExecutionResult, PersistenceError
from .worker import AcquisitionWorker, AcquisitionStore


EXIT_SUCCESS = 0
EXIT_UNEXPECTED = 1
EXIT_INPUT_OR_CONFIG = 2
EXIT_NOT_CLAIMED = 3
EXIT_PROVIDER_FAILURE = 4
EXIT_ESPO_FAILURE = 5
EXIT_PARTIAL_OR_UNCERTAIN = 6


@dataclass(frozen=True, slots=True)
class RunnerConfig:
    base_url: str
    api_key: str
    timeout_seconds: float
    verify_tls: bool


def main(
    argv: Sequence[str] | None = None,
    *,
    repository_factory: Callable[[RunnerConfig], AcquisitionStore] | None = None,
    provider_factory: Callable[[], DeterministicFakeProvider] = DeterministicFakeProvider,
    environ: Mapping[str, str] | None = None,
    stdout: Any = None,
    stderr: Any = None,
) -> int:
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    if args.command != "run-job" or not args.job_id.strip():
        return _emit_error(stdout, args.output if hasattr(args, "output") else "json", "INVALID_ARGUMENT", "run-job requires --job-id")
    if args.provider != "fake":
        return _emit_error(stdout, args.output, "INVALID_ARGUMENT", "only provider 'fake' is supported")

    started = monotonic()
    try:
        config = load_config(environ or os.environ)
    except ValueError as error:
        return _emit_error(stdout, args.output, "CONFIG_ERROR", str(error), duration_ms=_duration_ms(started))

    try:
        repository = (repository_factory or _default_repository_factory)(config)
        fetch = getattr(repository, "fetch_search_job", None)
        if not callable(fetch):
            raise PersistenceError("ESPO_READ_ERROR", "Acquisition repository cannot fetch SearchJob", retryable=False)
        initial_job = fetch(args.job_id)
        if initial_job is None:
            return _emit_result(stdout, args.output, _not_claimed(args.job_id, "JOB_NOT_FOUND", None, duration_ms=_duration_ms(started)), EXIT_NOT_CLAIMED)
        initial_status = _optional_text(initial_job.get("status"))
        if initial_status != "QUEUED":
            return _emit_result(stdout, args.output, _not_claimed(args.job_id, "JOB_NOT_QUEUED", initial_status, duration_ms=_duration_ms(started)), EXIT_NOT_CLAIMED)
        result = AcquisitionWorker(repository, provider_factory()).execute_job(args.job_id)
        payload = result_payload(result, duration_ms=_duration_ms(started))
        exit_code = exit_code_for(result)
    except PersistenceError as error:
        return _emit_error(stdout, args.output, error.code, error.safe_message, retryable=error.retryable, exit_code=EXIT_ESPO_FAILURE, duration_ms=_duration_ms(started))
    except Exception as error:
        return _emit_error(stdout, args.output, "UNEXPECTED_ERROR", f"Unexpected {type(error).__name__}", exit_code=EXIT_UNEXPECTED, duration_ms=_duration_ms(started))
    return _emit_result(stdout, args.output, payload, exit_code)


def load_config(environ: Mapping[str, str]) -> RunnerConfig:
    base_url = _required(environ, "ESPOCRM_BASE_URL")
    api_key = _required(environ, "ESPOCRM_API_KEY")
    try:
        timeout_seconds = float(environ.get("ESPOCRM_TIMEOUT", "30"))
    except ValueError as error:
        raise ValueError("ESPOCRM_TIMEOUT must be a positive number") from error
    if timeout_seconds <= 0:
        raise ValueError("ESPOCRM_TIMEOUT must be a positive number")
    verify_value = environ.get("ESPOCRM_VERIFY_TLS", "true").strip().casefold()
    if verify_value not in {"1", "0", "true", "false", "yes", "no"}:
        raise ValueError("ESPOCRM_VERIFY_TLS must be true or false")
    return RunnerConfig(base_url.rstrip("/"), api_key, timeout_seconds, verify_value in {"1", "true", "yes"})


def result_payload(result: JobExecutionResult, *, duration_ms: int) -> dict[str, Any]:
    data = asdict(result)
    return {
        "jobId": data["job_id"],
        "status": data["status"],
        "claimed": data["claimed"],
        "previousStatus": data["previous_status"],
        "finalStatus": data["final_status"],
        "provider": data["provider"],
        "resultCount": data["result_count"],
        "insertedCount": data["inserted_count"],
        "duplicateCount": data["duplicate_count"],
        "rejectedCount": data["rejected_count"],
        "retryable": data["retryable"],
        "partialPersistence": data["partial_persistence"],
        "finalStatusUncertain": data["final_status_uncertain"],
        "failureStage": data["failure_stage"],
        "errorCode": data["error_code"],
        "errorSummary": _safe_summary(data["error_summary"]),
        "durationMs": duration_ms,
    }


def exit_code_for(result: JobExecutionResult) -> int:
    if result.status == "COMPLETED":
        return EXIT_SUCCESS
    if result.status == "NOT_CLAIMED":
        return EXIT_NOT_CLAIMED
    if result.partial_persistence or result.final_status_uncertain:
        return EXIT_PARTIAL_OR_UNCERTAIN
    if result.failure_stage == "PROVIDER":
        return EXIT_PROVIDER_FAILURE
    if result.failure_stage in {"CLAIM", "PERSISTENCE", "COMPLETION", "DEDUPLICATION"} or result.claim_failed:
        return EXIT_ESPO_FAILURE
    return EXIT_UNEXPECTED


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m chitu_connector.acquisition.runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_job = subparsers.add_parser("run-job")
    run_job.add_argument("--job-id", required=True)
    run_job.add_argument("--provider", default="fake")
    run_job.add_argument("--output", choices=("json", "human"), default="json")
    return parser


def _default_repository_factory(config: RunnerConfig) -> EspoAcquisitionRepository:
    return EspoAcquisitionRepository(
        config.base_url,
        config.api_key,
        timeout_seconds=config.timeout_seconds,
        verify_tls=config.verify_tls,
    )


def _not_claimed(job_id: str, code: str, status: str | None, *, duration_ms: int) -> dict[str, Any]:
    return {
        "jobId": job_id,
        "status": "NOT_CLAIMED",
        "claimed": False,
        "previousStatus": status,
        "finalStatus": status,
        "provider": "DETERMINISTIC_FAKE",
        "resultCount": 0,
        "insertedCount": 0,
        "duplicateCount": 0,
        "rejectedCount": 0,
        "retryable": None,
        "partialPersistence": False,
        "finalStatusUncertain": False,
        "failureStage": "CLAIM",
        "errorCode": code,
        "errorSummary": None,
        "durationMs": duration_ms,
    }


def _emit_error(
    stdout: Any,
    output: str,
    code: str,
    summary: str,
    *,
    retryable: bool | None = None,
    exit_code: int = EXIT_INPUT_OR_CONFIG,
    duration_ms: int = 0,
) -> int:
    return _emit_result(stdout, output, {
        "jobId": None,
        "status": "ERROR",
        "claimed": False,
        "previousStatus": None,
        "finalStatus": None,
        "provider": None,
        "resultCount": 0,
        "insertedCount": 0,
        "duplicateCount": 0,
        "rejectedCount": 0,
        "retryable": retryable,
        "partialPersistence": False,
        "finalStatusUncertain": False,
        "failureStage": None,
        "errorCode": code,
        "errorSummary": _safe_summary(summary),
        "durationMs": duration_ms,
    }, exit_code)


def _emit_result(stdout: Any, output: str, payload: Mapping[str, Any], exit_code: int) -> int:
    if output == "human":
        stdout.write(
            f"job={payload['jobId'] or '-'} status={payload['status']} claimed={payload['claimed']} "
            f"exitCode={exit_code} error={payload['errorCode'] or '-'}\n"
        )
    else:
        stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    return exit_code


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _safe_summary(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    summary = " ".join(value.split())[:240]
    if any(marker in summary.casefold() for marker in ("authorization", "api key", "api_key", "bearer ", "token=", "secret", "password")):
        return "Sensitive error details suppressed"
    return summary or None


def _duration_ms(started: float) -> int:
    return max(0, round((monotonic() - started) * 1000))


if __name__ == "__main__":
    raise SystemExit(main())
