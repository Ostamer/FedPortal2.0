"""Тесты форматировщика KidsFormatter."""
import pytest

from src.services.formatters import KidsFormatter


class TestKidsFormatter:
    """Тесты KidsFormatter."""

    def test_validate_success(self, sample_kids_payload):
        formatter = KidsFormatter()
        is_valid, errors = formatter.validate(sample_kids_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_missing_required_field(self, sample_kids_payload):
        formatter = KidsFormatter()
        data = {k: v for k, v in sample_kids_payload.items() if k != "guid"}
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_validate_invalid_sex(self, sample_kids_payload):
        formatter = KidsFormatter()
        data = sample_kids_payload.copy()
        data["sex"] = "X"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_kids_payload):
        formatter = KidsFormatter()
        result = formatter.format(sample_kids_payload)
        result = result["data"]
        assert result["sex"] == "M"
        assert result["param1_state"] == 2
        assert result["param2_state"] == 1
        assert result["param6"] == 2
        # По ТЗ param1..param4 уходят строками "Y"/"N".
        assert result["param1"] == "Y"   # sample param1=True
        assert result["param2"] == "N"   # sample param2=False
        assert result["param3"] == "Y"   # sample param3=True
        assert result["param4"] == "N"   # sample param4=False

    def test_format_without_param6(self, sample_kids_payload):
        formatter = KidsFormatter()
        data = sample_kids_payload.copy()
        data["param6"] = None
        result = formatter.format(data)
        result = result["data"]
        assert "param6" not in result or result["param6"] is None
