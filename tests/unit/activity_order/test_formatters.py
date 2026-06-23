"""Тесты форматировщика ActivityOrderFormatter."""
import pytest

from src.services.formatters import ActivityOrderFormatter


class TestActivityOrderFormatter:
    """Тесты ActivityOrderFormatter."""

    def test_validate_success(self, sample_activity_order_payload):
        formatter = ActivityOrderFormatter()
        is_valid, errors = formatter.validate(sample_activity_order_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_state(self, sample_activity_order_payload):
        formatter = ActivityOrderFormatter()
        data = sample_activity_order_payload.copy()
        data["state"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_activity_order_payload):
        formatter = ActivityOrderFormatter()
        data = sample_activity_order_payload.copy()
        result = formatter.format(data)
        result = result["data"]
        assert result["state"] == "initial"
