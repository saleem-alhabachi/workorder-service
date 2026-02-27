from dataclasses import dataclass
from datetime import datetime, date
import uuid
from app.domain.models import WorkOrder, WorkOrderStatus
from app.domain.ports import WorkOrderRepository

@dataclass(frozen=True)
class CreateWorkOrderInput:
    title: str
    description: str
    assignee_id: str | None = None
    due_date: date | None = None

def create_workorder(repo: WorkOrderRepository, inp: CreateWorkOrderInput) -> WorkOrder:
    now = datetime.utcnow()
    wo = WorkOrder(
        id=f"wo_{uuid.uuid4().hex}",
        title=inp.title.strip(),
        description=inp.description.strip(),
        status=WorkOrderStatus.OPEN,
        assignee_id=inp.assignee_id,
        due_date=inp.due_date,
        created_at=now,
        is_deleted=False,
    )
    return repo.create(wo)
