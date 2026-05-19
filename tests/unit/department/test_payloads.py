"""Тесты Pydantic-модели DepartmentPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import DepartmentPayload


class TestDepartmentPayload:
    """Тесты модели DepartmentPayload."""

    def test_valid_department(self, sample_department_payload):
        dep = DepartmentPayload.model_validate(sample_department_payload)
        assert dep.id == 1
        assert dep.name == "Test Department"
        assert dep.location_type == "Городская"

    def test_missing_required_field_guid(self, sample_department_payload):
        data = {k: v for k, v in sample_department_payload.items() if k != "guid"}
        with pytest.raises(ValidationError) as exc_info:
            DepartmentPayload.model_validate(data)
        assert "guid" in str(exc_info.value)

    def test_missing_required_field_name(self, sample_department_payload):
        data = {k: v for k, v in sample_department_payload.items() if k != "name"}
        with pytest.raises(ValidationError) as exc_info:
            DepartmentPayload.model_validate(data)
        assert "name" in str(exc_info.value)

    def test_invalid_location_type(self, sample_department_payload):
        data = sample_department_payload.copy()
        data["location_type"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            DepartmentPayload.model_validate(data)
        assert "location_type" in str(exc_info.value)

    def test_optional_okato_oktmo_none(self, sample_department_payload):
        data = sample_department_payload.copy()
        data["okato"] = None
        data["oktmo"] = None
        dep = DepartmentPayload.model_validate(data)
        assert dep.okato is None
        assert dep.oktmo is None

    def test_is_deleted_bool(self, sample_department_payload):
        data = sample_department_payload.copy()
        data["is_deleted"] = True
        dep = DepartmentPayload.model_validate(data)
        assert dep.is_deleted is True
