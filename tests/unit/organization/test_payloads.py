"""Тесты Pydantic-модели OrganizationPayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import OrganizationPayload


class TestOrganizationPayload:
    """Тесты модели OrganizationPayload."""

    def test_valid_organization(self, sample_organization_payload):
        org = OrganizationPayload.model_validate(sample_organization_payload)
        assert org.id == 1
        assert org.name == "Test Organization"
        assert org.status == 0
        assert org.is_license is True
        assert org.legal_form == "Государственное бюджетное образовательное учреждение"

    def test_missing_required_field_id(self, sample_organization_payload):
        data = {k: v for k, v in sample_organization_payload.items() if k != "id"}
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "id" in str(exc_info.value)

    def test_missing_required_field_name(self, sample_organization_payload):
        data = {k: v for k, v in sample_organization_payload.items() if k != "name"}
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "name" in str(exc_info.value)

    def test_optional_fields_can_be_none(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["site"] = None
        data["phone"] = None
        data["email"] = None
        data["license"] = None
        data["serial"] = None
        data["accreditation_license"] = None
        data["accreditation_serial"] = None
        data["accreditation_date"] = None
        data["legal_address"] = None
        data["actual_address"] = None
        data["responsible"] = None
        org = OrganizationPayload.model_validate(data)
        assert org.site is None
        assert org.phone is None

    def test_invalid_status_value(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["status"] = 999
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "status" in str(exc_info.value)

    def test_invalid_legal_form_value(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["legal_form"] = "Unknown Form"
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "legal_form" in str(exc_info.value)

    def test_invalid_subordination_id(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["subordination_id"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "subordination_id" in str(exc_info.value)

    def test_invalid_accreditation_category(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["accreditation_category"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "accreditation_category" in str(exc_info.value)

    def test_invalid_type_value(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["type"] = "Unknown Type"
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "type" in str(exc_info.value)

    def test_invalid_accounting_type(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["accounting_type"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            OrganizationPayload.model_validate(data)
        assert "accounting_type" in str(exc_info.value)

    def test_extra_fields_allowed(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["extra_field"] = "extra_value"
        org = OrganizationPayload.model_validate(data)
        assert org.model_extra is not None
        assert org.model_extra.get("extra_field") == "extra_value"

    def test_bool_fields_parsing(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["is_license"] = True
        data["financing_normativ"] = False
        org = OrganizationPayload.model_validate(data)
        assert org.is_license is True
        assert org.financing_normativ is False

    def test_int_fields_parsing(self, sample_organization_payload):
        data = sample_organization_payload.copy()
        data["state_count"] = "30"
        org = OrganizationPayload.model_validate(data)
        assert org.state_count == 30
