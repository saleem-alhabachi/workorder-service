# app/usecases/list_workorders.py
from __future__ import annotations

from app.domain.entities import WorkOrder
from app.domain.interfaces import WorkOrderRepository


class ListWorkOrdersUseCase:
    def __init__(self, repository: WorkOrderRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[WorkOrder]:
        return await self._repository.list_all()
