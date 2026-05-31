"""
Форматировщики данных для различных сущностей.

Каждый форматировщик отвечает за:
- валидацию входных данных через Pydantic-модели (validate)
- преобразование в формат внешнего API (format)
"""

from typing import Any, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError

from src.config.logging import get_logger
from src.mappings.activity import (
    ACTIVITY_EDUCATION_FORM_MAP,
    ACTIVITY_LEVEL_MAP,
    ACTIVITY_LENGTH_UNIT_MAP,
    ACTIVITY_PERSONS_MAP,
    ACTIVITY_SECTION_MAP,
    ACTIVITY_SIGNIFICANT_PROJECT_MAP,
    ACTIVITY_STATE_MAP,
)
from src.mappings.certificate import CERTIFICATE_STATE_MAP
from src.mappings.department import DEPARTMENT_LOCATION_TYPE_MAP
from src.mappings.event import (
    EVENT_ADAPTIVE_TYPE_MAP,
    EVENT_DURATION_UNIT_MAP,
    EVENT_EDUCATION_FORM_MAP,
    EVENT_LEVELS_MAP,
    EVENT_PROGRAM_TYPE_MAP,
    EVENT_SECTION_ID_MAP,
    EVENT_STATE_MAP,
)
from src.mappings.order import ORDER_STATE_MAP
from src.mappings.organization import (
    ORGANIZATION_ACCREDITATION_CATEGORY_MAP,
    ORGANIZATION_ACCOUNTING_TYPE_MAP,
    ORGANIZATION_LEGAL_FORM_MAP,
    ORGANIZATION_STATUS_MAP,
    ORGANIZATION_SUBORDINATION_MAP,
    ORGANIZATION_TYPE_MAP,
)
from src.mappings.program_group_financing_source import (
    PROGRAM_GROUP_FINANCING_SOURCE_MAP,
)
from src.schemas.payloads import (
    ActivityPayload,
    CertificatePayload,
    DepartmentPayload,
    EventPayload,
    OrderPayload,
    OrganizationPayload,
    ParentsPayload,
    ProgramGroupFinancingSourcePayload,
    ProgramGroupPayload,
)

logger = get_logger(__name__)


class BaseFormatter:
    """Базовый класс форматировщика с общей логикой валидации и форматирования."""

    REQUIRED_FIELDS: List[str] = []
    BOOL_FIELDS: List[str] = []
    INT_FIELDS: List[str] = []
    FLOAT_FIELDS: List[str] = []
    MAP_FIELDS: Dict[str, Dict[str, Any]] = {}
    PAYLOAD_MODEL: Type[BaseModel] | None = None

    def validate(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
        """Проверить данные через Pydantic-модель или fallback на ручную проверку.

        Returns:
            Кортеж (is_valid, errors). При успехе errors=None.
        """
        if not isinstance(data, dict):
            logger.warning(
                f"{self._get_log_name()}_validation_failed",
                reason="not_a_dict",
            )
            return False, [{"field": "<root>", "reason": "not_a_dict"}]

        if self.PAYLOAD_MODEL is not None:
            try:
                self.PAYLOAD_MODEL.model_validate(data)
                return True, None
            except ValidationError as exc:
                errors = exc.errors(include_url=False)
                logger.warning(
                    f"{self._get_log_name()}_validation_failed",
                    errors=errors,
                )
                return False, errors

        # Fallback ручная проверка (для обратной совместимости)
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                logger.warning(
                    f"{self._get_log_name()}_validation_failed",
                    field=field,
                    reason="missing",
                )
                return False, [{"field": field, "reason": "missing"}]

        for field, mapping in self.MAP_FIELDS.items():
            if field in data and data[field] is not None:
                if data[field] not in mapping:
                    logger.warning(
                        f"{self._get_log_name()}_validation_failed",
                        field=field,
                        value=data[field],
                        reason="invalid_value",
                    )
                    return False, [
                        {
                            "field": field,
                            "reason": "invalid_value",
                            "value": data[field],
                        }
                    ]

        return True, None

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразовать данные для отправки во внешнее API."""
        if self.PAYLOAD_MODEL is not None:
            model = self.PAYLOAD_MODEL.model_validate(data)
            data = model.model_dump(mode='json')

        if self.PAYLOAD_MODEL is None:
            # Fallback ручная коэрция типов для классов без Pydantic-модели
            self._convert_bool_fields(data)
            self._convert_int_fields(data)
            self._convert_float_fields(data)

        self._apply_mapping(data)
        logger.debug('formatter_result', formatter=self._get_log_name(), data=data)
        return {'data': data}

    def _apply_mapping(self, data: Dict[str, Any]) -> None:
        """Применить маппинг к полям."""
        for field, mapping in self.MAP_FIELDS.items():
            if field in data and data[field] is not None:
                if isinstance(data[field], list):
                    data[field] = [
                        mapping[item] for item in data[field] if item in mapping
                    ]
                else:
                    data[field] = mapping[data[field]]

    def _convert_bool_fields(self, data: Dict[str, Any]) -> None:
        """Привести булевы поля к bool."""
        for field in self.BOOL_FIELDS:
            if field in data and data[field] is not None:
                data[field] = self._parse_bool(data[field])

    def _convert_int_fields(self, data: Dict[str, Any]) -> None:
        """Привести числовые поля к int."""
        for field in self.INT_FIELDS:
            if field in data and data[field] is not None:
                data[field] = int(data[field])

    def _convert_float_fields(self, data: Dict[str, Any]) -> None:
        """Привести числовые поля к float."""
        for field in self.FLOAT_FIELDS:
            if field in data and data[field] is not None:
                data[field] = float(data[field])

    @staticmethod
    def _parse_bool(value: Any) -> bool:
        """Привести значение к bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def _get_log_name(self) -> str:
        """Получить имя для логгирования из названия класса."""
        return self.__class__.__name__.replace("Formatter", "").lower()


class OrganizationFormatter(BaseFormatter):
    """Форматировщик для организаций."""

    PAYLOAD_MODEL = OrganizationPayload
    MAP_FIELDS = {
        "status": ORGANIZATION_STATUS_MAP,
        "legal_form": ORGANIZATION_LEGAL_FORM_MAP,
        "subordination_id": ORGANIZATION_SUBORDINATION_MAP,
        "accreditation_category": ORGANIZATION_ACCREDITATION_CATEGORY_MAP,
        "type": ORGANIZATION_TYPE_MAP,
        "accounting_type": ORGANIZATION_ACCOUNTING_TYPE_MAP,
    }


class DepartmentFormatter(BaseFormatter):
    """Форматировщик для муниципалитетов (municipality)."""

    PAYLOAD_MODEL = DepartmentPayload
    MAP_FIELDS = {"location_type": DEPARTMENT_LOCATION_TYPE_MAP}


class OrderFormatter(BaseFormatter):
    """Форматировщик для заявок (declaration)."""

    PAYLOAD_MODEL = OrderPayload
    MAP_FIELDS = {"state": ORDER_STATE_MAP}


class ActivityFormatter(BaseFormatter):
    """Форматировщик для мероприятий (activity)."""

    PAYLOAD_MODEL = ActivityPayload
    MAP_FIELDS = {
        "state": ACTIVITY_STATE_MAP,
        "education_form": ACTIVITY_EDUCATION_FORM_MAP,
        "level": ACTIVITY_LEVEL_MAP,
        "persons": ACTIVITY_PERSONS_MAP,
        "section": ACTIVITY_SECTION_MAP,
        "length_unit": ACTIVITY_LENGTH_UNIT_MAP,
        "significant_project": ACTIVITY_SIGNIFICANT_PROJECT_MAP,
    }


class EventFormatter(BaseFormatter):
    """Форматировщик для программ (event)."""

    PAYLOAD_MODEL = EventPayload
    MAP_FIELDS = {
        "state": EVENT_STATE_MAP,
        "levels": EVENT_LEVELS_MAP,
        "program_type": EVENT_PROGRAM_TYPE_MAP,
        "adaptive_type": EVENT_ADAPTIVE_TYPE_MAP,
        "section_id": EVENT_SECTION_ID_MAP,
        "duration_unit": EVENT_DURATION_UNIT_MAP,
        "education_form": EVENT_EDUCATION_FORM_MAP,
    }


class ProgramGroupFormatter(BaseFormatter):
    """Форматировщик для групп программ (program-group)."""

    PAYLOAD_MODEL = ProgramGroupPayload
    MAP_FIELDS = {}


class CertificateFormatter(BaseFormatter):
    """Форматировщик для сертификатов (certificate)."""

    PAYLOAD_MODEL = CertificatePayload
    MAP_FIELDS = {"state": CERTIFICATE_STATE_MAP}


class ProgramGroupFinancingSourceFormatter(BaseFormatter):
    """Форматировщик для источников финансирования групп."""

    PAYLOAD_MODEL = ProgramGroupFinancingSourcePayload
    MAP_FIELDS = {"financing_source": PROGRAM_GROUP_FINANCING_SOURCE_MAP}


class ParentsFormatter(BaseFormatter):
    """Форматировщик для родителей (parents)."""

    PAYLOAD_MODEL = ParentsPayload
    MAP_FIELDS = {}
