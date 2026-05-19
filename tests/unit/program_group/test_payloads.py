"""Тесты Pydantic-модели ProgramGroupPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import ProgramGroupPayload


class TestProgramGroupPayload:
    """Тесты модели ProgramGroupPayload."""

    def test_valid_program_group(self, sample_program_group_payload):
        pg = ProgramGroupPayload.model_validate(sample_program_group_payload)
        assert pg.id == 1
        assert pg.name == "Test Group"
        assert pg.age_from == 6.0
        assert pg.age_to == 12.0

    def test_missing_required_field_program_guid(self, sample_program_group_payload):
        data = {k: v for k, v in sample_program_group_payload.items() if k != "program_guid"}
        with pytest.raises(ValidationError) as exc_info:
            ProgramGroupPayload.model_validate(data)
        assert "program_guid" in str(exc_info.value)

    def test_float_age_fields(self, sample_program_group_payload):
        data = sample_program_group_payload.copy()
        data["age_from"] = 7.5
        data["age_to"] = 13.5
        data["cost_hour_manual"] = 200.5
        pg = ProgramGroupPayload.model_validate(data)
        assert pg.age_from == 7.5
        assert pg.age_to == 13.5
        assert pg.cost_hour_manual == 200.5

    def test_int_fields(self, sample_program_group_payload):
        data = sample_program_group_payload.copy()
        data["size_min"] = "3"
        data["size"] = "12"
        data["hours_year"] = "100"
        pg = ProgramGroupPayload.model_validate(data)
        assert pg.size_min == 3
        assert pg.size == 12
        assert pg.hours_year == 100

    def test_extra_fields_allowed(self, sample_program_group_payload):
        data = sample_program_group_payload.copy()
        data["extra"] = "value"
        pg = ProgramGroupPayload.model_validate(data)
        assert pg.model_extra is not None
        assert pg.model_extra.get("extra") == "value"
