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

    def test_format_yes_no_mapping(self, sample_parents_payload):
        # По ТЗ param1/is_large_family уходят строками "Y"/"N".
        formatter = ParentsFormatter()
        data = sample_parents_payload.copy()  # param1=True, is_large_family=False
        result = formatter.format(data)
        result = result["data"]
        assert result["guid"] == "parent-guid-1"
        assert result["param1"] == "Y"
        assert result["is_large_family"] == "N"
