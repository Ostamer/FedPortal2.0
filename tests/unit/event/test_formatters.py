"""Тесты форматировщика EventFormatter."""
import pytest

from src.services.formatters import EventFormatter


class TestEventFormatter:
    """Тесты EventFormatter."""

    def test_validate_success(self, sample_event_payload):
        formatter = EventFormatter()
        is_valid, errors = formatter.validate(sample_event_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_state(self, sample_event_payload):
        formatter = EventFormatter()
        data = sample_event_payload.copy()
        data["state"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_validate_invalid_program_type(self, sample_event_payload):
        formatter = EventFormatter()
        data = sample_event_payload.copy()
        data["program_type"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_event_payload):
        formatter = EventFormatter()
        data = sample_event_payload.copy()
        result = formatter.format(data)
        assert result["state"] == 3
        assert result["program_type"] == 1
        assert result["section_id"] == 173
        assert result["duration_unit"] == 5
        assert result["levels"] == 2
        assert result["education_form"] == "FULL_TIME"
        assert result["adaptive_type"] == 1
