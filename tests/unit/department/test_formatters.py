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

    def test_validate_missing_required_field(self, sample_department_payload):
        formatter = DepartmentFormatter()
        data = {k: v for k, v in sample_department_payload.items() if k != "name"}
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_no_mapping(self, sample_department_payload):
        formatter = DepartmentFormatter()
        result = formatter.format(sample_department_payload)
        assert result["id"] == 1
        assert result["name"] == "Test Department"
