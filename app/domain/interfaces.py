# app/domain/interfaces.py
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import WorkOrder
from app.domain.enums import WorkOrderStatus


class WorkOrderRepository(ABC):
    @abstractmethod
    async def create(self, workorder: WorkOrder) -> WorkOrder:
        ...

    @abstractmethod
    async def get_by_id(self, id: UUID) -> WorkOrder | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[WorkOrder]:
        ...

    @abstractmethod
    async def update_status(self, id: UUID, status: WorkOrderStatus) -> WorkOrder | None:
        ...
