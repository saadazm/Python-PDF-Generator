"""API-key auth with a per-key monthly quota (billing foundation).

Keys are stored in a JSON file for simplicity. This is fine for a small,
single-process deployment (e.g. one VPS) but the read-modify-write below
is not safe under concurrent requests from multiple worker processes —
move to SQLite or a real database before scaling past one uvicorn worker.

Wiring an actual paid plan (Stripe Checkout + webhooks to raise
quota_limit / rotate keys) is a follow-up that needs your own Stripe
account; this module only enforces whatever limits are already recorded.
"""
import json
import os
from datetime import date

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

KEYS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _load_keys():
    with open(KEYS_PATH) as f:
        return json.load(f)


def _save_keys(keys):
    with open(KEYS_PATH, "w") as f:
        json.dump(keys, f, indent=2)


def _current_period():
    return date.today().strftime("%Y-%m")


def _resolve_record(keys, api_key):
    record = keys.get(api_key)
    if record is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    period = _current_period()
    if record.get("quota_period") != period:
        record["quota_period"] = period
        record["quota_used"] = 0
    return record


def get_api_key_record(api_key: str = Security(_api_key_header)):
    """FastAPI dependency: validates the API key and charges 1 unit of quota.

    Used by single-document endpoints where the cost (one PDF) is known
    upfront.
    """
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")

    keys = _load_keys()
    record = _resolve_record(keys, api_key)

    if record["quota_used"] >= record["quota_limit"]:
        keys[api_key] = record
        _save_keys(keys)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Monthly quota of {record['quota_limit']} PDFs exceeded for the '{record['tier']}' tier. Upgrade your plan.",
        )

    record["quota_used"] += 1
    keys[api_key] = record
    _save_keys(keys)
    return {"key": api_key, **record}


def require_api_key(api_key: str = Security(_api_key_header)) -> str:
    """FastAPI dependency: validates the API key but does not charge quota.

    For endpoints whose cost isn't known until the request body is read
    (e.g. a CSV batch of N rows) -- call charge_quota() once N is known.
    """
    if not api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")

    keys = _load_keys()
    _resolve_record(keys, api_key)
    _save_keys(keys)
    return api_key


def charge_quota(api_key: str, amount: int) -> dict:
    """Atomically checks and charges `amount` units against the key's quota."""
    keys = _load_keys()
    record = _resolve_record(keys, api_key)

    if record["quota_used"] + amount > record["quota_limit"]:
        keys[api_key] = record
        _save_keys(keys)
        remaining = max(record["quota_limit"] - record["quota_used"], 0)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"This request needs {amount} PDFs but only {remaining} remain this month on the '{record['tier']}' tier.",
        )

    record["quota_used"] += amount
    keys[api_key] = record
    _save_keys(keys)
    return {"key": api_key, **record}
