# app/domain/entities.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import WorkOrderStatus


@dataclass(frozen=True)
class WorkOrder:
    id: UUID
    title: str
    description: str
    status: WorkOrderStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
