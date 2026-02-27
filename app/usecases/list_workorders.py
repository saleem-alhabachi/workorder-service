from dataclasses import dataclass
from datetime import date
from app.domain.models import WorkOrderStatus
from app.domain.ports import WorkOrderRepository

@dataclass(frozen=True)
class ListWorkOrdersInput:
    status: WorkOrderStatus | None = None
    assignee_id: str | None = None
    due_from: date | None = None
    due_to: date | None = None
    limit: int = 50
    offset: int = 0

def list_workorders(repo: WorkOrderRepository, inp: ListWorkOrdersInput):
    return list(
        repo.list(
            status=inp.status,
            assignee_id=inp.assignee_id,
            due_from=inp.due_from,
            due_to=inp.due_to,
            limit=inp.limit,
            offset=inp.offset,
        )
    )
