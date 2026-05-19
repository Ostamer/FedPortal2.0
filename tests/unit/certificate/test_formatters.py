"""Тесты форматировщика CertificateFormatter."""
import pytest

from src.services.formatters import CertificateFormatter


class TestCertificateFormatter:
    """Тесты CertificateFormatter."""

    def test_validate_success(self, sample_certificate_payload):
        formatter = CertificateFormatter()
        is_valid, errors = formatter.validate(sample_certificate_payload)
        assert is_valid is True
        assert errors is None

    def test_validate_invalid_state(self, sample_certificate_payload):
        formatter = CertificateFormatter()
        data = sample_certificate_payload.copy()
        data["state"] = "Unknown"
        is_valid, errors = formatter.validate(data)
        assert is_valid is False
        assert errors is not None

    def test_format_applies_mapping(self, sample_certificate_payload):
        formatter = CertificateFormatter()
        data = sample_certificate_payload.copy()
        result = formatter.format(data)
        assert result["state"] == "initial"

    def test_validate_state_none(self, sample_certificate_payload):
        formatter = CertificateFormatter()
        data = sample_certificate_payload.copy()
        data["state"] = None
        is_valid, errors = formatter.validate(data)
        assert is_valid is True
        assert errors is None
