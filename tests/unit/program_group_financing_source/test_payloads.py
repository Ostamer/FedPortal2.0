"""Тесты Pydantic-модели ProgramGroupFinancingSourcePayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import ProgramGroupFinancingSourcePayload


class TestProgramGroupFinancingSourcePayload:
    """Тесты модели ProgramGroupFinancingSourcePayload."""

    def test_valid_pgfs(self, sample_program_group_financing_source_payload):
        pgfs = ProgramGroupFinancingSourcePayload.model_validate(
            sample_program_group_financing_source_payload
        )
        assert pgfs.id == 1
        assert pgfs.financing_source == "Бюджетное (бесплатное)"
        assert pgfs.financing_cost == 500.0

    def test_missing_required_field_group_guid(self, sample_program_group_financing_source_payload):
        data = {k: v for k, v in sample_program_group_financing_source_payload.items() if k != "group_guid"}
        with pytest.raises(ValidationError) as exc_info:
            ProgramGroupFinancingSourcePayload.model_validate(data)
        assert "group_guid" in str(exc_info.value)

    def test_invalid_financing_source(self, sample_program_group_financing_source_payload):
        data = sample_program_group_financing_source_payload.copy()
        data["financing_source"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ProgramGroupFinancingSourcePayload.model_validate(data)
        assert "financing_source" in str(exc_info.value)

    def test_float_financing_cost(self, sample_program_group_financing_source_payload):
        data = sample_program_group_financing_source_payload.copy()
        data["financing_cost"] = 750.5
        pgfs = ProgramGroupFinancingSourcePayload.model_validate(data)
        assert pgfs.financing_cost == 750.5
