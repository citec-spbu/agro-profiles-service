from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.main import app
from src.schemas.token import TokenPayloadSchema
from src.utils.token import Token


def test_profiles_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/profiles/workers/me" in paths
    assert "/api/profiles/organizations/me" in paths


def test_worker_guard_rejects_organization_role() -> None:
    payload = TokenPayloadSchema(
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(minutes=30),
        sub="worker-id",
        role="organization",
        email="org@example.com",
        org="org-id",
    )

    with pytest.raises(HTTPException) as exc:
        Token.get_worker_payload(token_payload=payload)

    assert exc.value.status_code == 403


def test_get_payload_reads_claims_without_secret_validation() -> None:
    payload = {
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow() + timedelta(minutes=30)).timestamp(),
        "sub": "user-id",
        "role": "worker",
        "email": "worker@example.com",
        "org": "org-id",
    }
    token = jwt.encode(payload, "any-secret", algorithm="HS256")

    claims = Token.get_payload(token=token)

    assert claims.sub == "user-id"
    assert claims.role == "worker"
