import uuid
from datetime import date, datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.organizations import router as organizations_router
from src.api.workers import router as workers_router
from src.schemas.organization import OrganizationRequestSchema, OrganizationResponseSchema
from src.schemas.token import TokenPayloadSchema
from src.schemas.worker import WorkerRequestSchema, WorkerResponseSchema
from src.services.organizations_service import OrganizationsService
from src.services.workers_service import WorkersService
from src.utils.token import Token


class FakeWorkersService:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    @staticmethod
    def _profile(user_id: uuid.UUID) -> WorkerResponseSchema:
        return WorkerResponseSchema(
            id=uuid.uuid4(),
            user_id=user_id,
            name="Иван",
            surname="Иванов",
            patronymic="Иванович",
            date_of_birth=date(1990, 1, 1),
            phone_number="+79990000000",
        )

    async def create_worker(self, user_id: uuid.UUID, schema: WorkerRequestSchema):
        self.calls.append(("create_worker", user_id, schema.name))
        return self._profile(user_id)

    async def read_worker(self, user_id: uuid.UUID):
        self.calls.append(("read_worker", user_id))
        return self._profile(user_id)

    async def update_worker(self, user_id: uuid.UUID, schema: WorkerRequestSchema):
        self.calls.append(("update_worker", user_id, schema.name))

    async def delete_worker(self, user_id: uuid.UUID):
        self.calls.append(("delete_worker", user_id))


class FakeOrganizationsService:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    @staticmethod
    def _profile(user_id: uuid.UUID) -> OrganizationResponseSchema:
        return OrganizationResponseSchema(
            id=uuid.uuid4(),
            user_id=user_id,
            name="ООО Тест",
            description="desc",
            city="Москва",
            inn="7700000000",
            phone_number="+79990000001",
            website="https://example.com",
        )

    async def create_organization(self, user_id: uuid.UUID, schema: OrganizationRequestSchema):
        self.calls.append(("create_organization", user_id, schema.name))
        return self._profile(user_id)

    async def read_organization(self, user_id: uuid.UUID):
        self.calls.append(("read_organization", user_id))
        return self._profile(user_id)

    async def update_organization(self, user_id: uuid.UUID, schema: OrganizationRequestSchema):
        self.calls.append(("update_organization", user_id, schema.name))

    async def delete_organization(self, user_id: uuid.UUID):
        self.calls.append(("delete_organization", user_id))


def _payload(role: str, sub: str | None = None, org: str | None = None) -> TokenPayloadSchema:
    subject = sub or str(uuid.uuid4())
    return TokenPayloadSchema(
        iat=datetime.utcnow(),
        exp=datetime.utcnow() + timedelta(minutes=30),
        sub=subject,
        role=role,
        email="user@example.com",
        org=org or subject,
    )


def _build_client(
    workers_service: FakeWorkersService,
    organizations_service: FakeOrganizationsService,
) -> TestClient:
    app = FastAPI()
    app.include_router(organizations_router)
    app.include_router(workers_router)
    app.dependency_overrides[WorkersService] = lambda: workers_service
    app.dependency_overrides[OrganizationsService] = lambda: organizations_service
    app.dependency_overrides[Token.get_payload] = lambda: _payload("worker")
    app.dependency_overrides[Token.get_worker_payload] = lambda: _payload("worker")
    app.dependency_overrides[Token.get_organization_payload] = lambda: _payload("organization")
    return TestClient(app)


def test_profiles_endpoints_positive_paths() -> None:
    workers_service = FakeWorkersService()
    organizations_service = FakeOrganizationsService()
    client = _build_client(workers_service, organizations_service)

    worker_payload = {
        "name": "Иван",
        "surname": "Иванов",
        "patronymic": "Иванович",
        "date_of_birth": "1990-01-01",
        "phone_number": "+79990000000",
    }
    org_payload = {
        "name": "ООО Тест",
        "description": "desc",
        "city": "Москва",
        "inn": "7700000000",
        "phone_number": "+79990000001",
        "website": "https://example.com",
    }

    assert client.post("/api/profiles/workers", json=worker_payload).status_code == 201
    assert client.get("/api/profiles/workers/me").status_code == 200
    assert client.get("/api/profiles/workers", params={"user_id": str(uuid.uuid4())}).status_code == 200
    assert client.put("/api/profiles/workers/me", json=worker_payload).status_code == 204
    assert client.delete("/api/profiles/workers/me").status_code == 204

    assert client.post("/api/profiles/organizations", json=org_payload).status_code == 201
    assert client.get("/api/profiles/organizations/me").status_code == 200
    assert client.get("/api/profiles/organizations", params={"user_id": str(uuid.uuid4())}).status_code == 200
    assert client.put("/api/profiles/organizations/me", json=org_payload).status_code == 204
    assert client.delete("/api/profiles/organizations/me").status_code == 204

    worker_called = {call[0] for call in workers_service.calls}
    org_called = {call[0] for call in organizations_service.calls}
    assert worker_called == {"create_worker", "read_worker", "update_worker", "delete_worker"}
    assert org_called == {
        "create_organization",
        "read_organization",
        "update_organization",
        "delete_organization",
    }


def test_profiles_negative_validation() -> None:
    workers_service = FakeWorkersService()
    organizations_service = FakeOrganizationsService()
    client = _build_client(workers_service, organizations_service)

    response = client.post(
        "/api/profiles/workers",
        json={
            "name": "Иван",
            "surname": "Иванов",
            "patronymic": "Иванович",
            "date_of_birth": "invalid-date",
            "phone_number": "+79990000000",
        },
    )
    assert response.status_code == 422


def test_profiles_get_worker_requires_uuid_query() -> None:
    workers_service = FakeWorkersService()
    organizations_service = FakeOrganizationsService()
    client = _build_client(workers_service, organizations_service)

    response = client.get("/api/profiles/workers", params={"user_id": "not-a-uuid"})
    assert response.status_code == 422


def test_profiles_get_organization_requires_uuid_query() -> None:
    workers_service = FakeWorkersService()
    organizations_service = FakeOrganizationsService()
    client = _build_client(workers_service, organizations_service)

    response = client.get("/api/profiles/organizations", params={"user_id": "bad-uuid"})
    assert response.status_code == 422
