# app/infrastructure/repository.py
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WorkOrder
from app.domain.enums import WorkOrderStatus
from app.domain.interfaces import WorkOrderRepository
from app.infrastructure.models import WorkOrderModel


def _row_to_entity(row: WorkOrderModel) -> WorkOrder:
    return WorkOrder(
        id=row.id,
        title=row.title,
        description=row.description,
        status=WorkOrderStatus(row.status),
        created_by=row.created_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyWorkOrderRepository(WorkOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workorder: WorkOrder) -> WorkOrder:
        row = WorkOrderModel(
            id=workorder.id,
            title=workorder.title,
            description=workorder.description,
            status=workorder.status.value,
            created_by=workorder.created_by,
            created_at=workorder.created_at,
            updated_at=workorder.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _row_to_entity(row)

    async def get_by_id(self, id: UUID) -> WorkOrder | None:
        result = await self._session.execute(
            select(WorkOrderModel).where(WorkOrderModel.id == id)
        )
        row = result.scalar_one_or_none()
        return _row_to_entity(row) if row else None

    async def list_all(self) -> list[WorkOrder]:
        result = await self._session.execute(
            select(WorkOrderModel).order_by(WorkOrderModel.created_at.desc())
        )
        rows = result.scalars().all()
        return [_row_to_entity(r) for r in rows]

    async def update_status(self, id: UUID, status: WorkOrderStatus) -> WorkOrder | None:
        result = await self._session.execute(
            select(WorkOrderModel).where(WorkOrderModel.id == id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = status.value
        from datetime import datetime, timezone

        row.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(row)
        return _row_to_entity(row)
