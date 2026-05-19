"""Тесты форматировщика ParentsFormatter."""
import pytest

from src.services.formatters import ParentsFormatter


class TestParentsFormatter:
    """Тесты ParentsFormatter."""

    def test_validate_success(self, sample_parents_payload):
        formatter = ParentsFormatter()
        is_valid, errors = formatter.validate(sample_parents_payload)
        assert is_valid is True
        assert errors is None

    def test_format_no_mapping(self, sample_parents_payload):
        formatter = ParentsFormatter()
        data = sample_parents_payload.copy()
        result = formatter.format(data)
        assert result["guid"] == "parent-guid-1"
        assert result["param1"] is True
