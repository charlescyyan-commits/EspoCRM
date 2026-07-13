#!/usr/bin/env python3
"""Run Phase3C02.1 local API and ACL acceptance against EspoCRM."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MARKER = "[CHITU_PHASE3C02_TEST]"
ENTITY_TYPES = ("SearchStrategy", "SearchJob", "ProspectPool")
PERSONAS = (
    "Distributor",
    "Reseller",
    "Dealer",
    "3D Printer Store",
    "Print Farm",
    "Service Provider",
    "Education Supplier",
    "Dental Distributor",
    "Industrial Distributor",
)


@dataclass(frozen=True)
class ApiActor:
    name: str
    api_key_env: str


ACTORS = (
    ApiActor("admin", "C02_ADMIN_API_KEY"),
    ApiActor("manager", "C02_MANAGER_API_KEY"),
    ApiActor("sales", "C02_SALES_API_KEY"),
    ApiActor("integration", "C02_INTEGRATION_API_KEY"),
)


class AcceptanceError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query)}"

        request_body = None
        headers = {"X-Api-Key": self.api_key, "Accept": "application/json"}
        if payload is not None:
            request_body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(url, data=request_body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8")
                return response.status, json.loads(body) if body else None
        except HTTPError as error:
            body = error.read().decode("utf-8")
            try:
                parsed_body = json.loads(body) if body else None
            except json.JSONDecodeError:
                parsed_body = body
            return error.code, parsed_body


def expect_status(label: str, actual_status: int, expected_statuses: set[int]) -> None:
    if actual_status not in expected_statuses:
        raise AcceptanceError(
            f"{label}: expected {sorted(expected_statuses)}, received {actual_status}."
        )


def get_client(actor: ApiActor) -> ApiClient:
    base_url = os.environ.get("C02_API_BASE", "http://localhost:8080/api/v1")
    api_key = os.environ.get(actor.api_key_env)
    if not api_key:
        raise AcceptanceError(f"Missing required environment variable {actor.api_key_env}.")
    return ApiClient(base_url, api_key)


def current_user_id(client: ApiClient, actor_name: str) -> str:
    status, body = client.request("GET", "App/user")
    expect_status(f"{actor_name} App/user", status, {200})
    user_id = body.get("user", {}).get("id")
    if not user_id:
        raise AcceptanceError(f"{actor_name} App/user did not return a user ID.")
    return user_id


def list_records(client: ApiClient, entity_type: str) -> list[dict[str, Any]]:
    status, body = client.request("GET", entity_type, query={"maxSize": 200})
    expect_status(f"{entity_type} list", status, {200})
    return body.get("list", [])


def create_record(
    client: ApiClient,
    entity_type: str,
    payload: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    status, body = client.request("POST", entity_type, payload)
    expect_status(label, status, {200, 201})
    if not body or not body.get("id"):
        raise AcceptanceError(f"{label}: API response did not return an ID.")
    return body


def update_record(client: ApiClient, entity_type: str, record_id: str, label: str) -> None:
    status, _ = client.request("PUT", f"{entity_type}/{record_id}", {"name": f"{MARKER} updated {label}"})
    expect_status(f"{label} update", status, {200})


def read_record(client: ApiClient, entity_type: str, record_id: str, label: str) -> int:
    status, _ = client.request("GET", f"{entity_type}/{record_id}")
    if status != 200:
        raise AcceptanceError(f"{label} read: expected 200, received {status}.")
    return status


def delete_record(client: ApiClient, entity_type: str, record_id: str, label: str) -> None:
    status, _ = client.request("DELETE", f"{entity_type}/{record_id}")
    expect_status(f"{label} delete", status, {200})
    status, _ = client.request("GET", f"{entity_type}/{record_id}")
    expect_status(f"{label} post-delete GET", status, {404})


def strategy_payload(actor_name: str, user_id: str, personas: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": f"{MARKER} {actor_name} strategy",
        "product": "PlateCycler",
        "country": "Germany",
        "targetPersona": personas or ["Distributor"],
        "sourcePlan": ["DIRECTORY"],
        "status": "READY",
        "assignedUserId": user_id,
    }


def validate_actor_crud(
    actor: ApiActor,
    clients: dict[str, ApiClient],
    user_ids: dict[str, str],
    record_ids: dict[str, dict[str, list[str]]],
) -> None:
    client = clients[actor.name]
    user_id = user_ids[actor.name]

    for entity_type in ENTITY_TYPES:
        list_records(client, entity_type)

    strategy = create_record(client, "SearchStrategy", strategy_payload(actor.name, user_id), f"{actor.name} strategy create")
    strategy_id = strategy["id"]
    record_ids[actor.name]["SearchStrategy"].append(strategy_id)
    read_record(client, "SearchStrategy", strategy_id, f"{actor.name} strategy")
    update_record(client, "SearchStrategy", strategy_id, f"{actor.name} strategy")

    job = create_record(
        client,
        "SearchJob",
        {
            "name": f"{MARKER} {actor.name} job",
            "strategyId": strategy_id,
            "keyword": "3D printer distributor Germany",
            "country": "Germany",
            "source": "DIRECTORY",
            "status": "QUEUED",
            "priority": "P2",
            "assignedUserId": user_id,
        },
        f"{actor.name} job create",
    )
    job_id = job["id"]
    record_ids[actor.name]["SearchJob"].append(job_id)
    read_record(client, "SearchJob", job_id, f"{actor.name} job")
    update_record(client, "SearchJob", job_id, f"{actor.name} job")

    pool = create_record(
        client,
        "ProspectPool",
        {
            "name": f"{MARKER} {actor.name} prospect",
            "source": "DIRECTORY",
            "country": "Germany",
            "queue": "DISCOVERY",
            "status": "WAITING",
            "researchStatus": "NOT_STARTED",
            "qualificationStatus": "PENDING",
            "crmPushStatus": "NOT_READY",
            "searchJobId": job_id,
            "assignedUserId": user_id,
        },
        f"{actor.name} prospect create",
    )
    pool_id = pool["id"]
    record_ids[actor.name]["ProspectPool"].append(pool_id)
    read_record(client, "ProspectPool", pool_id, f"{actor.name} prospect")
    update_record(client, "ProspectPool", pool_id, f"{actor.name} prospect")


def validate_generate_jobs(client: ApiClient, user_id: str, record_ids: dict[str, dict[str, list[str]]]) -> str:
    strategy = create_record(
        client,
        "SearchStrategy",
        strategy_payload("admin generated", user_id, ["Distributor", "Reseller"]),
        "admin generated strategy create",
    )
    strategy_id = strategy["id"]
    record_ids["admin"]["SearchStrategy"].append(strategy_id)

    first_status, first_body = client.request("POST", "Prospecting/search-strategy/generate-jobs", {"strategyId": strategy_id})
    expect_status("generate jobs first request", first_status, {200})
    if first_body.get("generated_count") != 10 or first_body.get("existing_count") != 0:
        raise AcceptanceError(f"Unexpected first generation response: {first_body}.")

    second_status, second_body = client.request("POST", "Prospecting/search-strategy/generate-jobs", {"strategyId": strategy_id})
    expect_status("generate jobs duplicate request", second_status, {200})
    if second_body.get("generated_count") != 0 or second_body.get("existing_count") != 10:
        raise AcceptanceError(f"Unexpected duplicate generation response: {second_body}.")

    strategy_status, strategy_body = client.request("GET", f"SearchStrategy/{strategy_id}")
    expect_status("generated strategy read", strategy_status, {200})
    if strategy_body.get("generatedJobCount") != 10:
        raise AcceptanceError("Generated job count was not stable after duplicate generation.")

    jobs = [
        job
        for job in list_records(client, "SearchJob")
        if job.get("strategyId") == strategy_id
    ]
    fingerprints = [job.get("queryFingerprint") for job in jobs]
    if len(jobs) != 10 or not all(fingerprints) or len(set(fingerprints)) != 10:
        raise AcceptanceError("Generated jobs did not have ten unique non-empty fingerprints.")
    if any(job.get("status") != "QUEUED" for job in jobs):
        raise AcceptanceError("Generated jobs were not all QUEUED.")
    record_ids["admin"]["SearchJob"].extend(job["id"] for job in jobs)
    return strategy_id


def validate_boundaries(client: ApiClient, user_id: str, record_ids: dict[str, dict[str, list[str]]]) -> None:
    missing_product = strategy_payload("missing product", user_id)
    missing_product.pop("product")
    status, _ = client.request("POST", "SearchStrategy", missing_product)
    expect_status("missing product", status, {400})

    missing_country = strategy_payload("missing country", user_id)
    missing_country.pop("country")
    status, _ = client.request("POST", "SearchStrategy", missing_country)
    expect_status("missing country", status, {400})

    invalid_persona = strategy_payload("invalid persona", user_id, ["Invalid Persona"])
    status, _ = client.request("POST", "SearchStrategy", invalid_persona)
    expect_status("invalid persona strategy create", status, {400})

    maximum_strategy = create_record(
        client,
        "SearchStrategy",
        strategy_payload("maximum jobs", user_id, list(PERSONAS)),
        "maximum jobs strategy create",
    )
    record_ids["admin"]["SearchStrategy"].append(maximum_strategy["id"])
    status, _ = client.request("POST", "Prospecting/search-strategy/generate-jobs", {"strategyId": maximum_strategy["id"]})
    expect_status("maximum jobs generate", status, {400})
    maximum_strategy_jobs = [
        job
        for job in list_records(client, "SearchJob")
        if job.get("strategyId") == maximum_strategy["id"]
    ]
    if maximum_strategy_jobs:
        raise AcceptanceError("Maximum jobs rejection created partial SearchJob records.")


def validate_delete_matrix(clients: dict[str, ApiClient], record_ids: dict[str, dict[str, list[str]]]) -> None:
    for entity_type in ENTITY_TYPES:
        admin_record_id = record_ids["admin"][entity_type][0]
        delete_record(clients["admin"], entity_type, admin_record_id, f"admin {entity_type}")
        record_ids["admin"][entity_type].remove(admin_record_id)

    for actor_name in ("manager", "sales", "integration"):
        for entity_type in ENTITY_TYPES:
            record_id = record_ids[actor_name][entity_type][0]
            status, _ = clients[actor_name].request("DELETE", f"{entity_type}/{record_id}")
            expect_status(f"{actor_name} {entity_type} delete denied", status, {403})


def validate_owner_isolation(clients: dict[str, ApiClient], record_ids: dict[str, dict[str, list[str]]]) -> None:
    manager_strategy_id = record_ids["manager"]["SearchStrategy"][0]
    read_record(clients["admin"], "SearchStrategy", manager_strategy_id, "admin manager-owned strategy")
    read_record(clients["integration"], "SearchStrategy", manager_strategy_id, "integration manager-owned strategy")

    sales_status, _ = clients["sales"].request("GET", f"SearchStrategy/{manager_strategy_id}")
    if sales_status not in {403, 404}:
        raise AcceptanceError(f"Sales cross-owner strategy access was not denied: {sales_status}.")

    sales_list = list_records(clients["sales"], "SearchStrategy")
    if any(item.get("id") == manager_strategy_id for item in sales_list):
        raise AcceptanceError("Sales list exposed a manager-owned SearchStrategy.")


def run_acceptance() -> dict[str, Any]:
    clients = {actor.name: get_client(actor) for actor in ACTORS}
    user_ids = {actor_name: current_user_id(client, actor_name) for actor_name, client in clients.items()}
    record_ids = {
        actor_name: {entity_type: [] for entity_type in ENTITY_TYPES}
        for actor_name in clients
    }

    for actor in ACTORS:
        validate_actor_crud(actor, clients, user_ids, record_ids)

    generated_strategy_id = validate_generate_jobs(clients["admin"], user_ids["admin"], record_ids)
    validate_boundaries(clients["admin"], user_ids["admin"], record_ids)
    validate_delete_matrix(clients, record_ids)
    validate_owner_isolation(clients, record_ids)

    return {
        "status": "PASS",
        "generated_strategy_id": generated_strategy_id,
        "record_ids": record_ids,
        "sales_cross_owner_behavior": "ACL_DENIED_OR_HIDDEN_AFTER_ADMIN_200",
    }


def cleanup() -> dict[str, Any]:
    admin_client = get_client(ACTORS[0])
    strategies = [record for record in list_records(admin_client, "SearchStrategy") if MARKER in record.get("name", "")]
    strategy_ids = {record["id"] for record in strategies}
    jobs = list_records(admin_client, "SearchJob")
    pools = [record for record in list_records(admin_client, "ProspectPool") if MARKER in record.get("name", "")]
    job_ids = [
        record["id"]
        for record in jobs
        if MARKER in record.get("name", "") or record.get("strategyId") in strategy_ids
    ]

    deleted_ids = {"SearchStrategy": [], "SearchJob": [], "ProspectPool": []}
    for job_id in job_ids:
        delete_record(admin_client, "SearchJob", job_id, "cleanup SearchJob")
        deleted_ids["SearchJob"].append(job_id)
    for pool in pools:
        delete_record(admin_client, "ProspectPool", pool["id"], "cleanup ProspectPool")
        deleted_ids["ProspectPool"].append(pool["id"])
    for strategy in strategies:
        delete_record(admin_client, "SearchStrategy", strategy["id"], "cleanup SearchStrategy")
        deleted_ids["SearchStrategy"].append(strategy["id"])

    residual_counts = {
        "SearchStrategy": sum(MARKER in record.get("name", "") for record in list_records(admin_client, "SearchStrategy")),
        "SearchJob": sum(MARKER in record.get("name", "") for record in list_records(admin_client, "SearchJob")),
        "ProspectPool": sum(MARKER in record.get("name", "") for record in list_records(admin_client, "ProspectPool")),
    }
    if any(residual_counts.values()):
        raise AcceptanceError(f"Marker cleanup left residual records: {residual_counts}.")
    return {"status": "PASS", "deleted_ids": deleted_ids, "residual_counts": residual_counts}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true")
    arguments = parser.parse_args()
    try:
        result = cleanup() if arguments.cleanup else run_acceptance()
    except AcceptanceError as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
