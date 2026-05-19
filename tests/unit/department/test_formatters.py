"""Тесты форматировщика DepartmentFormatter."""
import pytest

from src.services.formatters import DepartmentFormatter


class TestDepartmentFormatter:
    """Тесты DepartmentFormatter."""

    def test_validate_success(self, sample_department_payload):
        formatter = DepartmentFormatter()
        is_valid, errors = formatter.validate(sample_department_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_location_type(self, sample_department_payload):
        formatter = DepartmentFormatter()
        data = sample_department_payload.copy()
        data["location_type"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_department_payload):
        formatter = DepartmentFormatter()
        data = sample_department_payload.copy()
        result = formatter.format(data)
        assert result["location_type"] == 1
