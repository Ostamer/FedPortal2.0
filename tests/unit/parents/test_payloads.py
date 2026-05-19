"""Тесты Pydantic-модели ParentsPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import ParentsPayload


class TestParentsPayload:
    """Тесты модели ParentsPayload."""

    def test_valid_parents(self, sample_parents_payload):
        parents = ParentsPayload.model_validate(sample_parents_payload)
        assert parents.id == 1
        assert parents.guid == "parent-guid-1"
        assert parents.param1 is True
        assert parents.is_large_family is False

    def test_missing_required_field_guid(self, sample_parents_payload):
        data = {k: v for k, v in sample_parents_payload.items() if k != "guid"}
        with pytest.raises(ValidationError) as exc_info:
            ParentsPayload.model_validate(data)
        assert "guid" in str(exc_info.value)

    def test_bool_fields(self, sample_parents_payload):
        data = sample_parents_payload.copy()
        data["param1"] = False
        data["is_large_family"] = True
        parents = ParentsPayload.model_validate(data)
        assert parents.param1 is False
        assert parents.is_large_family is True

    def test_extra_fields_allowed(self, sample_parents_payload):
        data = sample_parents_payload.copy()
        data["extra_field"] = "extra"
        parents = ParentsPayload.model_validate(data)
        assert parents.model_extra is not None
        assert parents.model_extra.get("extra_field") == "extra"
