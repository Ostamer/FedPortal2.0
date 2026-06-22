import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_httpx_response():
    """Factory for httpx.Response mocks."""

    def _make(
        status_code: int = 200,
        content: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        if json_data is not None:
            import json

            content = json.dumps(json_data).encode()
            headers = headers or {}
            headers.setdefault("content-type", "application/json")
        req = httpx.Request("GET", "https://example.com")
        return httpx.Response(
            status_code=status_code,
            content=content,
            headers=headers or {},
            request=req,
        )

    return _make


@pytest.fixture
def fake_external_api_client(mock_httpx_response):
    """ExternalApiClient with mocked internal httpx client."""
    from src.clients.fed_portal import ExternalApiClient

    client = ExternalApiClient(
        base_url="https://fed.example.com",
        api_key="test-key",
        host="fed.example.com",
    )
    client._client = MagicMock()
    return client


@pytest_asyncio.fixture
async def fake_async_session():
    """Fake SQLAlchemy async session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def fake_repo(fake_async_session):
    """SyncRecordRepository with mocked session."""
    from src.repositories.sync_record import SyncRecordRepository

    return SyncRecordRepository(fake_async_session)


@pytest.fixture
def sample_organization_payload():
    return {
        "id": 1,
        "guid": "org-guid-1",
        "name": "Test Organization",
        "short_name": "Test Org",
        "status": 0,
        "site": "https://example.com",
        "municipality_id": 10,
        "phone": "+79990000000",
        "email": "test@example.com",
        "responsible": "Ivanov",
        "OGRN": "1234567890123",
        "legal_form": "Государственное бюджетное образовательное учреждение",
        "legal_address": "Moscow",
        "actual_address": "Moscow",
        "department_id": 5,
        "subordination_id": "Муниципальное",
        "date_created": "2023-01-01",
        "is_license": True,
        "license": "lic-001",
        "serial": "ser-001",
        "accreditation_license": "acc-lic",
        "accreditation_serial": "acc-ser",
        "accreditation_date": "2023-06-01",
        "accreditation_category": "Высшая",
        "type": "Организация дополнительного образования",
        "accounting_type": "Собственная",
        "financing_normativ": False,
        "financing_result": True,
        "elibrary": False,
        "filial": False,
        "state_count": 25,
    }


@pytest.fixture
def sample_municipality_payload():
    return {
        "id": 1,
        "guid": "mun-guid-1",
        "name": "Test Municipality",
        "sort": 1,
        "okato": "12345678",
        "oktmo": "12345678",
        "kids_count": 100,
        "location_type": "Городская",
        "is_deleted": False,
    }


@pytest.fixture
def sample_department_payload():
    return {
        "id": 1,
        "name": "Test Department",
    }


@pytest.fixture
def sample_order_payload():
    return {
        "id": 1,
        "partner_id": 10,
        "program_id": 20,
        "state": "Новая",
        "birthday": "2010-05-15",
        "user_id": 100,
        "child_id": 200,
        "date_created": "2023-01-01 10:00:00",
        "date_study": "2023-09-01 09:00:00",
        "date_cancel": None,
    }


@pytest.fixture
def sample_activity_payload():
    return {
        "id": 1,
        "guid": "act-guid-1",
        "name": "Test Activity",
        "announce": "Announcement",
        "persons": ["Дети"],
        "length": 2.5,
        "length_unit": "Час",
        "partner_guid": "partner-guid",
        "state": "Опубликована",
        "disabled_access": False,
        "location": "Moscow",
        "education_form": "Очная",
        "level": "Муниципальное",
        "date_created": "2023-01-01",
        "section": "Образовательные",
        "significant_project": "Кванториум",
    }


@pytest.fixture
def sample_event_payload():
    return {
        "id": 1,
        "guid": "evt-guid-1",
        "partner_id": 10,
        "partner_guid": "partner-guid",
        "municipality_id": 5,
        "name": "Test Event",
        "state": "Опубликована",
        "age_from": 6.0,
        "age_to": 18.0,
        "rate": 1500.0,
        "location": "Moscow",
        "program_type": "Общеразвивающая",
        "section_id": "Техническое",
        "announce": "Announce",
        "description": "Description",
        "date_created": "2023-01-01",
        "duration": 1.0,
        "duration_unit": "Месяц",
        "min_persons": 5,
        "max_persons": 20,
        "levels": "Базовый",
        "education_form": "Очная",
        "certificate_required": True,
        "param1": False,
        "param2": False,
        "adaptive_type": "Адаптированная программа",
    }


@pytest.fixture
def sample_program_group_payload():
    return {
        "id": 1,
        "guid": "pg-guid-1",
        "program_guid": "prog-guid",
        "name": "Test Group",
        "age_to": 12.0,
        "age_from": 6.0,
        "size_min": 5,
        "size": 15,
        "date_begin": "2023-09-01",
        "date_end": "2024-06-01",
        "hours_year": 120,
        "cost_hour_manual": 150.0,
        "municipality_guid": "mun-guid",
    }


@pytest.fixture
def sample_certificate_payload():
    return {
        "guid": "cert-guid-1",
        "state": "Активен",
        "municipality_guid": "mun-guid",
        "child_guid": "child-guid",
        "payment_cert": True,
        "date_created": "2023-01-01",
        "external_id": 1,
    }


@pytest.fixture
def sample_program_group_financing_source_payload():
    return {
        "id": 1,
        "group_guid": "group-guid",
        "financing_source": "Бюджетное (бесплатное)",
        "financing_cost": 500.0,
    }


@pytest.fixture
def sample_parents_payload():
    return {
        "id": 1,
        "guid": "parent-guid-1",
        "param1": True,
        "is_large_family": False,
    }


@pytest.fixture
def sample_activity_order_payload():
    return {
        "id": 1,
        "state": "Новая",
        "child_guid": "child-guid-1",
        "user_guid": "parent-guid-1",
        "partner_guid": "partner-guid",
        "activity_guid": "activity-guid-1",
        "date_created": "2023-01-01 10:00:00",
    }


@pytest.fixture
def sample_kids_payload():
    return {
        "guid": "kids-guid-1",
        "parent_guid": "parent-guid-1",
        "birthday": "2015-06-15",
        "sex": "Мужской",
        "id": 1,
        "param1": True,
        "param1_state": 2,
        "param2": False,
        "param2_state": 1,
        "param3": True,
        "param4": False,
        "param5": [1, 2, 3],
        "param6": 2,
    }
