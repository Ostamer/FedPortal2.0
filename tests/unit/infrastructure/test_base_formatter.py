"""Тесты базового форматировщика BaseFormatter."""
import pytest

from src.services.formatters import BaseFormatter


class TestBaseFormatter:
    """Тесты базового форматировщика."""

    def test_validate_not_dict_returns_false(self):
        formatter = BaseFormatter()
        is_valid, errors = formatter.validate("not a dict")
        assert is_valid is False
        assert errors is not None
        assert errors[0]["reason"] == "not_a_dict"

    def test_format_without_model_and_no_fields(self):
        formatter = BaseFormatter()
        data = {"foo": "bar"}
        assert formatter.format(data) == {"foo": "bar"}

    def test_convert_bool_fields(self):
        class BoolFormatter(BaseFormatter):
            BOOL_FIELDS = ["flag"]

        formatter = BoolFormatter()
        data = {"flag": "true"}
        formatter._convert_bool_fields(data)
        assert data["flag"] is True

    def test_convert_int_fields(self):
        class IntFormatter(BaseFormatter):
            INT_FIELDS = ["count"]

        formatter = IntFormatter()
        data = {"count": "42"}
        formatter._convert_int_fields(data)
        assert data["count"] == 42

    def test_convert_float_fields(self):
        class FloatFormatter(BaseFormatter):
            FLOAT_FIELDS = ["rate"]

        formatter = FloatFormatter()
        data = {"rate": "3.14"}
        formatter._convert_float_fields(data)
        assert data["rate"] == 3.14
