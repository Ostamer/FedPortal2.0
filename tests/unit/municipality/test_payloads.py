"""Тесты Pydantic-модели MunicipalityPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import MunicipalityPayload


class TestMunicipalityPayload:
    """Тесты модели MunicipalityPayload."""

    def test_valid_municipality(self, sample_municipality_payload):
        mun = MunicipalityPayload.model_validate(sample_municipality_payload)
        assert mun.id == 1
        assert mun.name == "Test Municipality"
        assert mun.location_type == "Городская"

    def test_missing_required_field_guid(self, sample_municipality_payload):
        data = {k: v for k, v in sample_municipality_payload.items() if k != "guid"}
        with pytest.raises(ValidationError) as exc_info:
            MunicipalityPayload.model_validate(data)
        assert "guid" in str(exc_info.value)

    def test_missing_required_field_name(self, sample_municipality_payload):
        data = {k: v for k, v in sample_municipality_payload.items() if k != "name"}
        with pytest.raises(ValidationError) as exc_info:
            MunicipalityPayload.model_validate(data)
        assert "name" in str(exc_info.value)

    def test_invalid_location_type(self, sample_municipality_payload):
        data = sample_municipality_payload.copy()
        data["location_type"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            MunicipalityPayload.model_validate(data)
        assert "location_type" in str(exc_info.value)

    def test_optional_okato_oktmo_none(self, sample_municipality_payload):
        data = sample_municipality_payload.copy()
        data["okato"] = None
        data["oktmo"] = None
        mun = MunicipalityPayload.model_validate(data)
        assert mun.okato is None
        assert mun.oktmo is None

    def test_is_deleted_bool(self, sample_municipality_payload):
        data = sample_municipality_payload.copy()
        data["is_deleted"] = True
        mun = MunicipalityPayload.model_validate(data)
        assert mun.is_deleted is True
