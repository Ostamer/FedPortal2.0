"""Тесты форматировщика ProgramGroupFormatter."""
import pytest

from src.services.formatters import ProgramGroupFormatter


class TestProgramGroupFormatter:
    """Тесты ProgramGroupFormatter."""

    def test_validate_success(self, sample_program_group_payload):
        formatter = ProgramGroupFormatter()
        is_valid, errors = formatter.validate(sample_program_group_payload)
        assert is_valid is True
        assert errors is None

    def test_format_no_mapping(self, sample_program_group_payload):
        formatter = ProgramGroupFormatter()
        data = sample_program_group_payload.copy()
        result = formatter.format(data)
        assert result["name"] == "Test Group"
        assert "age_from" in result
