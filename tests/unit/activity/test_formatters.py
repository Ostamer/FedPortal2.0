"""Тесты форматировщика ActivityFormatter."""
import pytest

from src.services.formatters import ActivityFormatter


class TestActivityFormatter:
    """Тесты ActivityFormatter."""

    def test_validate_success(self, sample_activity_payload):
        formatter = ActivityFormatter()
        is_valid, errors = formatter.validate(sample_activity_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_state(self, sample_activity_payload):
        formatter = ActivityFormatter()
        data = sample_activity_payload.copy()
        data["state"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_validate_invalid_persons(self, sample_activity_payload):
        formatter = ActivityFormatter()
        data = sample_activity_payload.copy()
        data["persons"] = ["Unknown"]
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_activity_payload):
        formatter = ActivityFormatter()
        data = sample_activity_payload.copy()
        result = formatter.format(data)
        assert result["state"] == 3
        assert result["education_form"] == "FULL_TIME"
        assert result["level"] == "MUN"
        assert result["section"] == 3
        assert result["length_unit"] == 2
        assert result["significant_project"] == 1
        assert result["persons"] == ["CHILD"]
