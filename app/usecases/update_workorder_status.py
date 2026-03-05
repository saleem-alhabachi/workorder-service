# app/usecases/update_workorder_status.py
from __future__ import annotations

from uuid import UUID

from app.domain.entities import WorkOrder
from app.domain.enums import WorkOrderStatus
from app.domain.exceptions import InvalidStatusTransitionError
from app.domain.interfaces import WorkOrderRepository


ALLOWED_TRANSITIONS: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.PENDING: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.COMPLETED: set(),
    WorkOrderStatus.CANCELLED: set(),
}


class UpdateWorkOrderStatusUseCase:
    def __init__(self, repository: WorkOrderRepository) -> None:
        self._repository = repository

    async def execute(self, id: UUID, new_status: WorkOrderStatus) -> WorkOrder | None:
        existing = await self._repository.get_by_id(id)
        if existing is None:
            return None
        allowed = ALLOWED_TRANSITIONS.get(existing.status, set())
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Transition from {existing.status.value} to {new_status.value} is not allowed"
            )
        return await self._repository.update_status(id, new_status)
