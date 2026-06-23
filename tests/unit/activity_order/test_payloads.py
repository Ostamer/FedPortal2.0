"""Тесты Pydantic-модели ActivityOrderPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import ActivityOrderPayload


class TestActivityOrderPayload:
    """Тесты модели ActivityOrderPayload."""

    def test_valid_activity_order(self, sample_activity_order_payload):
        order = ActivityOrderPayload.model_validate(sample_activity_order_payload)
        assert order.id == 1
        assert order.state == "Новая"
        assert order.activity_guid == "activity-guid-1"

    def test_missing_required_field_partner_guid(self, sample_activity_order_payload):
        data = {
            k: v for k, v in sample_activity_order_payload.items()
            if k != "partner_guid"
        }
        with pytest.raises(ValidationError) as exc_info:
            ActivityOrderPayload.model_validate(data)
        assert "partner_guid" in str(exc_info.value)

    def test_missing_required_field_child_guid(self, sample_activity_order_payload):
        data = {
            k: v for k, v in sample_activity_order_payload.items()
            if k != "child_guid"
        }
        with pytest.raises(ValidationError) as exc_info:
            ActivityOrderPayload.model_validate(data)
        assert "child_guid" in str(exc_info.value)

    def test_invalid_state_value(self, sample_activity_order_payload):
        data = sample_activity_order_payload.copy()
        data["state"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            ActivityOrderPayload.model_validate(data)
        assert "state" in str(exc_info.value)

    def test_user_guid_optional(self, sample_activity_order_payload):
        data = {
            k: v for k, v in sample_activity_order_payload.items()
            if k != "user_guid"
        }
        order = ActivityOrderPayload.model_validate(data)
        assert order.user_guid is None
