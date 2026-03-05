# app/domain/enums.py
from __future__ import annotations

from enum import Enum


class WorkOrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Role(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
