# app/usecases/create_workorder.py
from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.entities import WorkOrder
from app.domain.enums import WorkOrderStatus
from app.domain.interfaces import WorkOrderRepository


class CreateWorkOrderUseCase:
    def __init__(self, repository: WorkOrderRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        title: str,
        description: str,
        created_by: str,
        id: UUID | None = None,
    ) -> WorkOrder:
        now = datetime.now(timezone.utc)
        workorder = WorkOrder(
            id=id or uuid4(),
            title=title,
            description=description,
            status=WorkOrderStatus.PENDING,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create(workorder)
