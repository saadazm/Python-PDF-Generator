import json
import os

import pytest


@pytest.fixture
def isolated_keys(tmp_path, monkeypatch):
    """Points api.auth at a throwaway key store so tests never touch the
    committed api/api_keys.json (and can't leave it with dirty quota
    counters or race other tests run in parallel).
    """
    import api.auth as auth_mod

    keys_path = tmp_path / "api_keys.json"
    keys_path.write_text(json.dumps({
        "test-free-key": {
            "tier": "free",
            "quota_limit": 3,
            "quota_used": 0,
            "quota_period": None,
            "brand": None,
        },
        "test-brand-key": {
            "tier": "pro",
            "quota_limit": 100,
            "quota_used": 0,
            "quota_period": None,
            "brand": {
                "tab_fill_color": "#0B1F3A",
                "tab_text_color": "#FFFFFF",
                "logo_path": None,
            },
        },
    }))
    monkeypatch.setattr(auth_mod, "KEYS_PATH", str(keys_path))
    return keys_path


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from api.main import app

    return TestClient(app)
