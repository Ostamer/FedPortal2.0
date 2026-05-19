"""Тесты Pydantic-модели ActivityPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import ActivityPayload


class TestActivityPayload:
    """Тесты модели ActivityPayload."""

    def test_valid_activity(self, sample_activity_payload):
        act = ActivityPayload.model_validate(sample_activity_payload)
        assert act.id == 1
        assert act.name == "Test Activity"
        assert act.state == "Опубликована"

    def test_missing_required_field_partner_guid(self, sample_activity_payload):
        data = {k: v for k, v in sample_activity_payload.items() if k != "partner_guid"}
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "partner_guid" in str(exc_info.value)

    def test_invalid_state_value(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["state"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "state" in str(exc_info.value)

    def test_invalid_education_form(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["education_form"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "education_form" in str(exc_info.value)

    def test_invalid_level(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["level"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "level" in str(exc_info.value)

    def test_invalid_section(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["section"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "section" in str(exc_info.value)

    def test_invalid_length_unit(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["length_unit"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "length_unit" in str(exc_info.value)

    def test_invalid_significant_project(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["significant_project"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "significant_project" in str(exc_info.value)

    def test_invalid_persons_value(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["persons"] = ["Unknown"]
        with pytest.raises(ValidationError) as exc_info:
            ActivityPayload.model_validate(data)
        assert "persons" in str(exc_info.value)

    def test_persons_none_allowed(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["persons"] = None
        act = ActivityPayload.model_validate(data)
        assert act.persons is None

    def test_length_float(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["length"] = 3.5
        act = ActivityPayload.model_validate(data)
        assert act.length == 3.5

    def test_disabled_access_bool(self, sample_activity_payload):
        data = sample_activity_payload.copy()
        data["disabled_access"] = True
        act = ActivityPayload.model_validate(data)
        assert act.disabled_access is True
