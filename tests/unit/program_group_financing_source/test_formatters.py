"""Тесты форматировщика ProgramGroupFinancingSourceFormatter."""
import pytest

from src.services.formatters import ProgramGroupFinancingSourceFormatter


class TestProgramGroupFinancingSourceFormatter:
    """Тесты ProgramGroupFinancingSourceFormatter."""

    def test_validate_success(self, sample_program_group_financing_source_payload):
        formatter = ProgramGroupFinancingSourceFormatter()
        is_valid, errors = formatter.validate(sample_program_group_financing_source_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_financing_source(self, sample_program_group_financing_source_payload):
        formatter = ProgramGroupFinancingSourceFormatter()
        data = sample_program_group_financing_source_payload.copy()
        data["financing_source"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_program_group_financing_source_payload):
        formatter = ProgramGroupFinancingSourceFormatter()
        data = sample_program_group_financing_source_payload.copy()
        result = formatter.format(data)
        assert result["financing_source"] == 1
