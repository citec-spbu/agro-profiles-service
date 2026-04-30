import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.organizations import router as organizations_router
from src.api.workers import router as workers_router
from src.schemas.token import TokenPayloadSchema
from src.services.organizations_service import OrganizationsService
from src.services.workers_service import WorkersService
from src.utils.token import Token
from tests.test_api_business import FakeOrganizationsService, FakeWorkersService


def _payload(role: str) -> TokenPayloadSchema:
    sub = str(uuid.uuid4())
    return TokenPayloadSchema(
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(minutes=30),
        sub=sub,
        role=role,
        email="user@example.com",
        org=sub,
    )


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(organizations_router)
    app.include_router(workers_router)
    app.dependency_overrides[WorkersService] = lambda: FakeWorkersService()
    app.dependency_overrides[OrganizationsService] = lambda: FakeOrganizationsService()
    app.dependency_overrides[Token.get_payload] = lambda: _payload("worker")
    app.dependency_overrides[Token.get_worker_payload] = lambda: _payload("worker")
    app.dependency_overrides[Token.get_organization_payload] = lambda: _payload("organization")
    return TestClient(app)


VALID_WORKER = {
    "name": "Иван",
    "surname": "Иванов",
    "patronymic": "Иванович",
    "date_of_birth": "1990-01-01",
    "phone_number": "+79990000000",
}
VALID_ORG = {
    "name": "ООО Тест",
    "description": "desc",
    "city": "Москва",
    "inn": "7700000000",
    "phone_number": "+79990000001",
    "website": "https://example.com",
}


@pytest.mark.parametrize(
    ("method", "path", "json_body", "query", "expected_status"),
    [
        ("post", "/api/profiles/workers", VALID_WORKER, None, 201),
        ("post", "/api/profiles/workers", {**VALID_WORKER, "date_of_birth": "bad-date"}, None, 422),
        ("post", "/api/profiles/workers", {"name": "Иван"}, None, 422),
        ("get", "/api/profiles/workers/me", None, None, 200),
        ("get", "/api/profiles/workers", None, {"user_id": str(uuid.uuid4())}, 200),
        ("get", "/api/profiles/workers", None, {"user_id": "bad-uuid"}, 422),
        ("put", "/api/profiles/workers/me", VALID_WORKER, None, 204),
        ("put", "/api/profiles/workers/me", {"name": "Иван"}, None, 422),
        ("delete", "/api/profiles/workers/me", None, None, 204),
        ("post", "/api/profiles/organizations", VALID_ORG, None, 201),
        ("post", "/api/profiles/organizations", {"name": "ООО Тест"}, None, 422),
        ("get", "/api/profiles/organizations/me", None, None, 200),
        ("get", "/api/profiles/organizations", None, {"user_id": str(uuid.uuid4())}, 200),
        ("get", "/api/profiles/organizations", None, {"user_id": "bad-uuid"}, 422),
        ("put", "/api/profiles/organizations/me", VALID_ORG, None, 204),
        ("put", "/api/profiles/organizations/me", {"name": "ООО Тест"}, None, 422),
        ("delete", "/api/profiles/organizations/me", None, None, 204),
        ("post", "/api/profiles/organizations", {**VALID_ORG, "city": "X" * 100}, None, 422),
        ("post", "/api/profiles/workers", {**VALID_WORKER, "name": "X" * 200}, None, 422),
        ("post", "/api/profiles/workers", {**VALID_WORKER, "phone_number": "X" * 100}, None, 422),
    ],
)
def test_profiles_validation_matrix(
    method: str,
    path: str,
    json_body: dict | None,
    query: dict | None,
    expected_status: int,
) -> None:
    client = _client()
    response = client.request(method.upper(), path, json=json_body, params=query)
    assert response.status_code == expected_status
