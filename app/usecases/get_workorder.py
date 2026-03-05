# app/usecases/get_workorder.py
from __future__ import annotations

from uuid import UUID

from app.domain.entities import WorkOrder
from app.domain.interfaces import WorkOrderRepository


class GetWorkOrderUseCase:
    def __init__(self, repository: WorkOrderRepository) -> None:
        self._repository = repository

    async def execute(self, id: UUID) -> WorkOrder | None:
        return await self._repository.get_by_id(id)
