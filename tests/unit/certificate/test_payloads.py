"""Тесты Pydantic-модели CertificatePayload."""
import pytest
from pydantic import ValidationError

from src.schemas.payloads import CertificatePayload


class TestCertificatePayload:
    """Тесты модели CertificatePayload."""

    def test_valid_certificate(self, sample_certificate_payload):
        cert = CertificatePayload.model_validate(sample_certificate_payload)
        assert cert.guid == "cert-guid-1"
        assert cert.state == "Активен"
        assert cert.payment_cert is True

    def test_missing_required_field_guid(self, sample_certificate_payload):
        data = {k: v for k, v in sample_certificate_payload.items() if k != "guid"}
        with pytest.raises(ValidationError) as exc_info:
            CertificatePayload.model_validate(data)
        assert "guid" in str(exc_info.value)

    def test_child_guid_optional(self, sample_certificate_payload):
        # child_guid опционален: ребёнок может быть без портфолио обучающегося.
        data = {k: v for k, v in sample_certificate_payload.items() if k != "child_guid"}
        cert = CertificatePayload.model_validate(data)
        assert cert.child_guid is None

    def test_invalid_state_value(self, sample_certificate_payload):
        data = sample_certificate_payload.copy()
        data["state"] = "Unknown"
        with pytest.raises(ValidationError) as exc_info:
            CertificatePayload.model_validate(data)
        assert "state" in str(exc_info.value)

    def test_state_none_allowed(self, sample_certificate_payload):
        data = sample_certificate_payload.copy()
        data["state"] = None
        cert = CertificatePayload.model_validate(data)
        assert cert.state is None

    def test_int_fields(self, sample_certificate_payload):
        data = sample_certificate_payload.copy()
        data["denomination"] = "500"
        data["volume"] = "5"
        data["external_id"] = "10"
        data["profile_id"] = "20"
        cert = CertificatePayload.model_validate(data)
        assert cert.denomination == 500
        assert cert.volume == 5
        assert cert.external_id == 10
        assert cert.profile_id == 20

    def test_bool_payment_cert(self, sample_certificate_payload):
        data = sample_certificate_payload.copy()
        data["payment_cert"] = False
        cert = CertificatePayload.model_validate(data)
        assert cert.payment_cert is False
