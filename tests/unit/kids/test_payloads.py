"""Тесты Pydantic-модели KidsPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import KidsPayload


class TestKidsPayload:
    """Тесты модели KidsPayload."""

    def test_valid_kids(self, sample_kids_payload):
        kids = KidsPayload.model_validate(sample_kids_payload)
        assert kids.guid == "kids-guid-1"
        assert kids.parent_guid == "parent-guid-1"
        assert kids.sex == "Мужской"
        assert kids.id == 1
        assert kids.param1 is True
        assert kids.param1_state == 2
        assert kids.param5 == [1, 2, 3]
        assert kids.param6 == 2

    def test_missing_required_field_guid(self, sample_kids_payload):
        data = {k: v for k, v in sample_kids_payload.items() if k != "guid"}
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "guid" in str(exc_info.value)

    def test_missing_required_field_birthday(self, sample_kids_payload):
        data = {k: v for k, v in sample_kids_payload.items() if k != "birthday"}
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "birthday" in str(exc_info.value)

    def test_invalid_sex_value(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["sex"] = "X"
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "sex" in str(exc_info.value)

    def test_valid_sex_values(self, sample_kids_payload):
        for sex_value in ["Не указан", "Мужской", "Женский"]:
            data = sample_kids_payload.copy()
            data["sex"] = sex_value
            kids = KidsPayload.model_validate(data)
            assert kids.sex == sex_value

    def test_invalid_param1_state(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param1_state"] = 99
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "param1_state" in str(exc_info.value)

    def test_invalid_param2_state(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param2_state"] = 99
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "param2_state" in str(exc_info.value)

    def test_invalid_param6(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param6"] = 99
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "param6" in str(exc_info.value)

    def test_param6_optional(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param6"] = None
        kids = KidsPayload.model_validate(data)
        assert kids.param6 is None

    def test_param6_omitted(self, sample_kids_payload):
        data = {k: v for k, v in sample_kids_payload.items() if k != "param6"}
        kids = KidsPayload.model_validate(data)
        assert kids.param6 is None

    def test_invalid_param5_not_list(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param5"] = "not a list"
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "param5" in str(exc_info.value)

    def test_invalid_param5_item_not_int(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["param5"] = [1, "two", 3]
        with pytest.raises(ValidationError) as exc_info:
            KidsPayload.model_validate(data)
        assert "param5" in str(exc_info.value)

    def test_valid_param6_values(self, sample_kids_payload):
        for param6_value in [1, 2, 3, 4]:
            data = sample_kids_payload.copy()
            data["param6"] = param6_value
            kids = KidsPayload.model_validate(data)
            assert kids.param6 == param6_value

    def test_extra_fields_allowed(self, sample_kids_payload):
        data = sample_kids_payload.copy()
        data["extra_field"] = "extra_value"
        kids = KidsPayload.model_validate(data)
        assert kids.model_extra is not None
        assert kids.model_extra.get("extra_field") == "extra_value"
