"""Тесты Pydantic-модели EventPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import EventPayload


class TestEventPayload:
    """Тесты модели EventPayload."""

    def test_valid_event(self, sample_event_payload):
        evt = EventPayload.model_validate(sample_event_payload)
        assert evt.id == 1
        assert evt.name == "Test Event"
        assert evt.state == "Опубликована"

    def test_missing_required_field_partner_id(self, sample_event_payload):
        data = {k: v for k, v in sample_event_payload.items() if k != "partner_id"}
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "partner_id" in str(exc_info.value)

    def test_invalid_state_value(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["state"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "state" in str(exc_info.value)

    def test_invalid_program_type(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["program_type"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "program_type" in str(exc_info.value)

    def test_invalid_section_id(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["section_id"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "section_id" in str(exc_info.value)

    def test_invalid_duration_unit(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["duration_unit"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "duration_unit" in str(exc_info.value)

    def test_invalid_levels(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["levels"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "levels" in str(exc_info.value)

    def test_invalid_education_form(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["education_form"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "education_form" in str(exc_info.value)

    def test_invalid_adaptive_type(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["adaptive_type"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            EventPayload.model_validate(data)
        assert "adaptive_type" in str(exc_info.value)

    def test_float_fields(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["age_from"] = 7.5
        data["age_to"] = 15.5
        data["rate"] = 2000.0
        data["duration"] = 2.5
        evt = EventPayload.model_validate(data)
        assert evt.age_from == 7.5
        assert evt.age_to == 15.5
        assert evt.rate == 2000.0
        assert evt.duration == 2.5

    def test_bool_fields(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["certificate_required"] = False
        data["param1"] = True
        data["param2"] = True
        evt = EventPayload.model_validate(data)
        assert evt.certificate_required is False
        assert evt.param1 is True
        assert evt.param2 is True

    def test_int_fields(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["min_persons"] = "10"
        data["max_persons"] = "25"
        evt = EventPayload.model_validate(data)
        assert evt.min_persons == 10
        assert evt.max_persons == 25

    def test_optional_location_none(self, sample_event_payload):
        data = sample_event_payload.copy()
        data["location"] = None
        data["announce"] = None
        data["description"] = None
        evt = EventPayload.model_validate(data)
        assert evt.location is None
        assert evt.announce is None
        assert evt.description is None
