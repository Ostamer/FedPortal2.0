"""Типы сущностей синхронизации (значения совпадают с enum в PostgreSQL)."""
import enum


class EntityType(str, enum.Enum):
    ORGANIZATION = 'organization'
    DEPARTMENT = 'department'
    ORDER = 'order'
    EVENT = 'event'
    ACTIVITY = 'activity'
    PROGRAM_GROUP = 'program-group'
    CERTIFICATE = 'certificate'
    PROGRAM_GROUP_FINANCING_SOURCE = 'program-group-financing-source'
    PARENTS = 'parents'


class SyncSource(str, enum.Enum):
    MAIN_QUEUE = 'main_queue'
    DLQ_RETRY = 'dlq_retry'
    MANUAL = 'manual'
