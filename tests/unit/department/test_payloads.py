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

    def test_missing_required_field_id(self, sample_department_payload):
        data = {k: v for k, v in sample_department_payload.items() if k != "id"}
        with pytest.raises(ValidationError) as exc_info:
            DepartmentPayload.model_validate(data)
        assert "id" in str(exc_info.value)

    def test_missing_required_field_name(self, sample_department_payload):
        data = {k: v for k, v in sample_department_payload.items() if k != "name"}
        with pytest.raises(ValidationError) as exc_info:
            DepartmentPayload.model_validate(data)
        assert "name" in str(exc_info.value)

    def test_extra_fields_allowed(self, sample_department_payload):
        data = sample_department_payload.copy()
        data["extra_field"] = "extra_value"
        dep = DepartmentPayload.model_validate(data)
        assert dep.model_extra is not None
        assert dep.model_extra.get("extra_field") == "extra_value"
