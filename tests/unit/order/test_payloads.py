"""Тесты Pydantic-модели OrderPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import OrderPayload


class TestOrderPayload:
    """Тесты модели OrderPayload."""

    def test_valid_order(self, sample_order_payload):
        order = OrderPayload.model_validate(sample_order_payload)
        assert order.id == 1
        assert order.state == "Новая"
        assert order.date_cancel is None

    def test_missing_required_field_partner_id(self, sample_order_payload):
        data = {k: v for k, v in sample_order_payload.items() if k != "partner_id"}
        with pytest.raises(ValidationError) as exc_info:
            OrderPayload.model_validate(data)
        assert "partner_id" in str(exc_info.value)

    def test_invalid_state_value(self, sample_order_payload):
        data = sample_order_payload.copy()
        data["state"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            OrderPayload.model_validate(data)
        assert "state" in str(exc_info.value)

    def test_invalid_birthday_format(self, sample_order_payload):
        data = sample_order_payload.copy()
        data["birthday"] = "15.05.2010"
        with pytest.raises(ValidationError) as exc_info:
            OrderPayload.model_validate(data)
        assert "birthday" in str(exc_info.value)

    def test_invalid_date_created_format(self, sample_order_payload):
        data = sample_order_payload.copy()
        data["date_created"] = "2023-01-01"
        with pytest.raises(ValidationError) as exc_info:
            OrderPayload.model_validate(data)
        assert "date_created" in str(exc_info.value)

    def test_empty_birthday_allowed(self, sample_order_payload):
        data = sample_order_payload.copy()
        data["birthday"] = ""
        order = OrderPayload.model_validate(data)
        assert order.birthday == ""

    def test_date_cancel_none_allowed(self, sample_order_payload):
        data = sample_order_payload.copy()
        data["date_cancel"] = None
        order = OrderPayload.model_validate(data)
        assert order.date_cancel is None
