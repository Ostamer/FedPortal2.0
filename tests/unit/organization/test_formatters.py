"""Тесты форматировщика OrganizationFormatter."""
import pytest

from src.services.formatters import OrganizationFormatter


class TestOrganizationFormatter:
    """Тесты OrganizationFormatter."""

    def test_validate_success(self, sample_organization_payload):
        formatter = OrganizationFormatter()
        is_valid, errors = formatter.validate(sample_organization_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_missing_required_field(self, sample_organization_payload):
        formatter = OrganizationFormatter()
        data = {k: v for k, v in sample_organization_payload.items() if k != "name"}
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None
        assert any(e.get("loc") == ("name",) for e in errors)

    def test_validate_invalid_status(self, sample_organization_payload):
        formatter = OrganizationFormatter()
        data = sample_organization_payload.copy()
        data["status"] = 999
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_organization_payload):
        formatter = OrganizationFormatter()
        data = sample_organization_payload.copy()
        result = formatter.format(data)
        result = result["data"]
        assert result["status"] == 0
        assert result["legal_form"] == 3
        assert result["subordination_id"] == 2
        assert result["accreditation_category"] == "high"
        assert result["type"] == 1
        assert result["accounting_type"] == "own"
