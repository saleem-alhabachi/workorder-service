from typing import Iterable, Optional
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.domain.ports import WorkOrderRepository
from app.domain.models import WorkOrder, WorkOrderStatus
from .sqlalchemy_models import WorkOrderRow

def row_to_domain(r: WorkOrderRow) -> WorkOrder:
    return WorkOrder(
        id=r.id,
        title=r.title,
        description=r.description,
        status=WorkOrderStatus(r.status),
        assignee_id=r.assignee_id,
        due_date=r.due_date,
        created_at=r.created_at,
        is_deleted=r.is_deleted,
    )

class SQLAlchemyWorkOrderRepository(WorkOrderRepository):
    def __init__(self, db: Session):
        self.db = db

    def create(self, wo: WorkOrder) -> WorkOrder:
        r = WorkOrderRow(
            id=wo.id,
            title=wo.title,
            description=wo.description,
            status=wo.status.value,
            assignee_id=wo.assignee_id,
            due_date=wo.due_date,
            created_at=wo.created_at,
            is_deleted=wo.is_deleted,
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return row_to_domain(r)

    def get(self, workorder_id: str) -> Optional[WorkOrder]:
        r = self.db.get(WorkOrderRow, workorder_id)
        return row_to_domain(r) if r else None

    def list(
        self,
        status: Optional[WorkOrderStatus] = None,
        assignee_id: Optional[str] = None,
        due_from: Optional[date] = None,
        due_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Iterable[WorkOrder]:
        stmt = select(WorkOrderRow).where(WorkOrderRow.is_deleted == False)  # noqa: E712
        if status:
            stmt = stmt.where(WorkOrderRow.status == status.value)
        if assignee_id:
            stmt = stmt.where(WorkOrderRow.assignee_id == assignee_id)
        if due_from:
            stmt = stmt.where(WorkOrderRow.due_date >= due_from)
        if due_to:
            stmt = stmt.where(WorkOrderRow.due_date <= due_to)
        stmt = stmt.order_by(WorkOrderRow.created_at.desc()).limit(limit).offset(offset)
        rows = self.db.execute(stmt).scalars().all()
        return [row_to_domain(r) for r in rows]

    def update(self, wo: WorkOrder) -> WorkOrder:
        r = self.db.get(WorkOrderRow, wo.id)
        if not r:
            return wo
        r.status = wo.status.value
        r.title = wo.title
        r.description = wo.description
        r.assignee_id = wo.assignee_id
        r.due_date = wo.due_date
        r.is_deleted = wo.is_deleted
        self.db.commit()
        self.db.refresh(r)
        return row_to_domain(r)
