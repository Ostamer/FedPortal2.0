"""Тесты форматировщика OrderFormatter."""
import pytest

from src.services.formatters import OrderFormatter


class TestOrderFormatter:
    """Тесты OrderFormatter."""

    def test_validate_success(self, sample_order_payload):
        formatter = OrderFormatter()
        is_valid, errors = formatter.validate(sample_order_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_state(self, sample_order_payload):
        formatter = OrderFormatter()
        data = sample_order_payload.copy()
        data["state"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_order_payload):
        formatter = OrderFormatter()
        data = sample_order_payload.copy()
        result = formatter.format(data)
        assert result["state"] == "initial"

    def test_validate_invalid_birthday(self, sample_order_payload):
        formatter = OrderFormatter()
        data = sample_order_payload.copy()
        data["birthday"] = "invalid"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None
