"""
Pydantic-модели payload'ов для валидации данных перед отправкой во внешнее API.

Каждая модель отражает контракт конкретной сущности и даёт детальные
ValidationError вместо грубой ручной проверки.
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from src.mappings.activity import (
    ACTIVITY_EDUCATION_FORM_MAP,
    ACTIVITY_LEVEL_MAP,
    ACTIVITY_LENGTH_UNIT_MAP,
    ACTIVITY_PERSONS_MAP,
    ACTIVITY_SECTION_MAP,
    ACTIVITY_SIGNIFICANT_PROJECT_MAP,
    ACTIVITY_STATE_MAP,
)
from src.mappings.activity_order import ACTIVITY_ORDER_STATE_MAP
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
from src.mappings.kids import (
    KIDS_SEX_MAP,
    KIDS_PARAM1_STATE_MAP,
    KIDS_PARAM2_STATE_MAP,
    KIDS_PARAM6_MAP,
)


class OrganizationPayload(BaseModel):
    """Модель организации (unit / organization)."""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    name: str
    short_name: str
    status: int
    site: Optional[str]
    municipality_id: int
    phone: Optional[str]
    email: Optional[str]
    responsible: Optional[str]
    OGRN: str
    legal_form: Optional[str]
    legal_address: Optional[str]
    actual_address: Optional[str]
    department_id: int
    subordination_id: Optional[str]
    date_created: str
    is_license: bool
    license: Optional[str]
    serial: Optional[str]
    accreditation_license: Optional[str]
    accreditation_serial: Optional[str]
    accreditation_date: Optional[str]
    accreditation_category: Optional[str]
    type: str
    accounting_type: str
    financing_normativ: bool
    financing_result: bool
    elibrary: bool
    filial: bool
    state_count: int

    @field_validator('status')
    @classmethod
    def _validate_status(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in ORGANIZATION_STATUS_MAP:
            raise ValueError(f'invalid status: {v}')
        return v

    @field_validator('legal_form')
    @classmethod
    def _validate_legal_form(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORGANIZATION_LEGAL_FORM_MAP:
            raise ValueError(f'invalid legal_form: {v}')
        return v

    @field_validator('subordination_id')
    @classmethod
    def _validate_subordination(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORGANIZATION_SUBORDINATION_MAP:
            raise ValueError(f'invalid subordination_id: {v}')
        return v

    @field_validator('accreditation_category')
    @classmethod
    def _validate_accreditation_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORGANIZATION_ACCREDITATION_CATEGORY_MAP:
            raise ValueError(f'invalid accreditation_category: {v}')
        return v

    @field_validator('type')
    @classmethod
    def _validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORGANIZATION_TYPE_MAP:
            raise ValueError(f'invalid type: {v}')
        return v

    @field_validator('accounting_type')
    @classmethod
    def _validate_accounting_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORGANIZATION_ACCOUNTING_TYPE_MAP:
            raise ValueError(f'invalid accounting_type: {v}')
        return v


class MunicipalityPayload(BaseModel):
    """Модель муниципалитета (municipality)"""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    name: str
    sort: int
    okato: Optional[str]
    oktmo: Optional[str]
    kids_count: int
    location_type: str
    is_deleted: bool

    @field_validator('location_type')
    @classmethod
    def _validate_location_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in DEPARTMENT_LOCATION_TYPE_MAP:
            raise ValueError(f'invalid location_type: {v}')
        return v


class DepartmentPayload(BaseModel):
    """Модель department (id, name)."""

    model_config = ConfigDict(extra='allow')

    id: int
    name: str


class KidsPayload(BaseModel):
    """Модель ребенка (kids)."""

    model_config = ConfigDict(extra='allow')

    guid: str
    parent_guid: Optional[str] = None
    birthday: str
    sex: str
    id: int
    param1: bool
    param1_state: Optional[int] = None
    param2: bool
    param2_state: Optional[int] = None
    param3: bool
    param4: bool
    param5: Optional[list[int]] = []
    param6: Optional[int] = None

    @field_validator('sex')
    @classmethod
    def _validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in KIDS_SEX_MAP:
            raise ValueError(f'invalid sex: {v}')
        return v

    @field_validator('param1_state')
    @classmethod
    def _validate_param1_state(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in KIDS_PARAM1_STATE_MAP:
            raise ValueError(f'invalid param1_state: {v}')
        return v

    @field_validator('param2_state')
    @classmethod
    def _validate_param2_state(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in KIDS_PARAM2_STATE_MAP:
            raise ValueError(f'invalid param2_state: {v}')
        return v

    @field_validator('param6')
    @classmethod
    def _validate_param6(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in KIDS_PARAM6_MAP:
            raise ValueError(f'invalid param6: {v}')
        return v

    @field_validator('param5')
    @classmethod
    def _validate_param5(cls, v: Optional[list]) -> Optional[list[int]]:
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('param5 must be a list')
            for item in v:
                if not isinstance(item, int):
                    raise ValueError(f'param5 item must be int, got {type(item)}')
        return v


class OrderPayload(BaseModel):
    """Модель заявки (declaration)."""

    model_config = ConfigDict(extra='allow')

    id: int
    partner_id: int
    program_id: int
    state: str
    birthday: Optional[str]
    user_id: int
    child_id: int
    date_created: Optional[str]
    date_study: Optional[str] = None
    date_cancel: Optional[str] = None

    @field_validator('birthday')
    @classmethod
    def _validate_birthday(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != '' and not re.match(r'^\d{4}-\d{2}-\d{2}$', str(v)):
            raise ValueError('invalid date format, expected YYYY-MM-DD')
        return v

    @field_validator('date_created', 'date_study', 'date_cancel')
    @classmethod
    def _validate_datetime(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != '' and not re.match(
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', str(v)
        ):
            raise ValueError('invalid datetime format, expected YYYY-MM-DD HH:MM:SS')
        return v

    @field_validator('state')
    @classmethod
    def _validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ORDER_STATE_MAP:
            raise ValueError(f'invalid state: {v}')
        return v


class ActivityPayload(BaseModel):
    """Модель мероприятия."""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    name: str
    announce: Optional[str]
    persons: Optional[list] = None
    length: Optional[float] = None
    length_unit: str
    partner_guid: str
    state: str
    disabled_access: bool
    location: Optional[str]
    education_form: str
    level: str
    date_created: str
    section: str
    significant_project: Optional[str] = None

    @field_validator('persons')
    @classmethod
    def _validate_persons(cls, v: Optional[list]) -> Optional[list]:
        if v is None:
            return v
        for i in v:
            if i is not None and i not in ACTIVITY_PERSONS_MAP:
                raise ValueError(f'invalid persons: {v}')
        return v

    @field_validator('state')
    @classmethod
    def _validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_STATE_MAP:
            raise ValueError(f'invalid state: {v}')
        return v

    @field_validator('length_unit')
    @classmethod
    def _validate_length_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_LENGTH_UNIT_MAP:
            raise ValueError(f'invalid length_unit: {v}')
        return v

    @field_validator('education_form')
    @classmethod
    def _validate_education_form(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_EDUCATION_FORM_MAP:
            raise ValueError(f'invalid education_form: {v}')
        return v

    @field_validator('level')
    @classmethod
    def _validate_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_LEVEL_MAP:
            raise ValueError(f'invalid level: {v}')
        return v

    @field_validator('section')
    @classmethod
    def _validate_section(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_SECTION_MAP:
            raise ValueError(f'invalid section: {v}')
        return v

    @field_validator('significant_project')
    @classmethod
    def _validate_significant_project(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_SIGNIFICANT_PROJECT_MAP:
            raise ValueError(f'invalid significant_project: {v}')
        return v


class EventPayload(BaseModel):
    """Модель программы (event)."""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    partner_id: int
    partner_guid: str
    municipality_id: Optional[int] = None
    name: str
    state: str
    age_from: float
    age_to: float
    rate: float
    location: Optional[str]
    program_type: str
    section_id: Optional[str] = None
    announce: Optional[str]
    description: Optional[str]
    date_created: Optional[str] = None
    duration: float
    duration_unit: str
    min_persons: int
    max_persons: int
    levels: Optional[str] = None
    education_form: Optional[str] = None
    certificate_required: bool
    param1: bool
    param2: bool
    adaptive_type: Optional[str] = None

    @field_validator('state')
    @classmethod
    def _validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_STATE_MAP:
            raise ValueError(f'invalid state: {v}')
        return v

    @field_validator('program_type')
    @classmethod
    def _validate_program_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_PROGRAM_TYPE_MAP:
            raise ValueError(f'invalid program_type: {v}')
        return v

    @field_validator('section_id')
    @classmethod
    def _validate_section_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_SECTION_ID_MAP:
            raise ValueError(f'invalid section_id: {v}')
        return v

    @field_validator('duration_unit')
    @classmethod
    def _validate_duration_unit(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_DURATION_UNIT_MAP:
            raise ValueError(f'invalid duration_unit: {v}')
        return v

    @field_validator('levels')
    @classmethod
    def _validate_levels(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_LEVELS_MAP:
            raise ValueError(f'invalid levels: {v}')
        return v

    @field_validator('education_form')
    @classmethod
    def _validate_education_form(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_EDUCATION_FORM_MAP:
            raise ValueError(f'invalid education_form: {v}')
        return v

    @field_validator('adaptive_type')
    @classmethod
    def _validate_adaptive_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in EVENT_ADAPTIVE_TYPE_MAP:
            raise ValueError(f'invalid adaptive_type: {v}')
        return v


class ProgramGroupPayload(BaseModel):
    """Модель группы программ (program-group)."""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    program_guid: Optional[str] = None
    name: str
    age_to: float
    age_from: float
    size_min: int
    size: int
    date_begin: Optional[str] = None
    date_end: Optional[str] = None
    hours_year: int
    cost_hour_manual: float
    municipality_guid: Optional[str] = None


class CertificatePayload(BaseModel):
    """Модель сертификата (certificate)."""

    model_config = ConfigDict(extra='allow')

    guid: str
    state: Optional[str]
    municipality_guid: Optional[str] = None
    child_guid: Optional[str] = None
    payment_cert: bool
    date_created: str
    external_id: int
    # Старый интеграционный сервис эти поля не отправлял — на портале опциональны.
    denomination: Optional[int] = None
    volume: Optional[int] = None
    profile_id: Optional[int] = None

    @field_validator('state')
    @classmethod
    def _validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CERTIFICATE_STATE_MAP:
            raise ValueError(f'invalid state: {v}')
        return v


class ProgramGroupFinancingSourcePayload(BaseModel):
    """Модель источника финансирования группы (program-group-financing-source)."""

    model_config = ConfigDict(extra='allow')

    id: int
    group_guid: str
    # По ТЗ — одиночный код источника финансирования (Справочник 15).
    financing_source: Optional[str] = None
    financing_cost: float

    @field_validator('financing_source')
    @classmethod
    def _validate_financing_source(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in PROGRAM_GROUP_FINANCING_SOURCE_MAP:
            raise ValueError(f'invalid financing_source: {v}')
        return v


class ParentsPayload(BaseModel):
    """Модель родителей (parents)."""

    model_config = ConfigDict(extra='allow')

    id: int
    guid: str
    param1: bool
    is_large_family: bool


class ActivityOrderPayload(BaseModel):
    """Модель заявки на мероприятие (activity-order)."""

    model_config = ConfigDict(extra='allow')

    id: int
    state: str
    child_guid: str
    user_guid: Optional[str] = None
    partner_guid: str
    activity_guid: str
    date_created: Optional[str] = None

    @field_validator('state')
    @classmethod
    def _validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ACTIVITY_ORDER_STATE_MAP:
            raise ValueError(f'invalid state: {v}')
        return v
