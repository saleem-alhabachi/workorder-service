from dataclasses import dataclass
from datetime import datetime, date
from enum import StrEnum

class WorkOrderStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"

ALLOWED_TRANSITIONS = {
    WorkOrderStatus.OPEN: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.DONE, WorkOrderStatus.CANCELLED},
    WorkOrderStatus.DONE: set(),
    WorkOrderStatus.CANCELLED: set(),
}

@dataclass(frozen=True)
class WorkOrder:
    id: str
    title: str
    description: str
    status: WorkOrderStatus
    assignee_id: str | None
    due_date: date | None
    created_at: datetime
    is_deleted: bool = False

    def can_transition_to(self, new_status: WorkOrderStatus) -> bool:
        return new_status in ALLOWED_TRANSITIONS[self.status]
