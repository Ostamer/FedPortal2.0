"""Тесты форматировщика MunicipalityFormatter."""
import pytest

from src.services.formatters import MunicipalityFormatter


class TestMunicipalityFormatter:
    """Тесты MunicipalityFormatter."""

    def test_validate_success(self, sample_municipality_payload):
        formatter = MunicipalityFormatter()
        is_valid, errors = formatter.validate(sample_municipality_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_missing_required_field(self, sample_municipality_payload):
        formatter = MunicipalityFormatter()
        data = {k: v for k, v in sample_municipality_payload.items() if k != "name"}
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_validate_invalid_location_type(self, sample_municipality_payload):
        formatter = MunicipalityFormatter()
        data = sample_municipality_payload.copy()
        data["location_type"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_municipality_payload):
        formatter = MunicipalityFormatter()
        result = formatter.format(sample_municipality_payload)
        result = result["data"]
        assert result["location_type"] == 1
        assert result["is_deleted"] == "N"
