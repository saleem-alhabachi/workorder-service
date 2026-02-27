from app.domain.ports import WorkOrderRepository
from app.domain.models import WorkOrderStatus, WorkOrder
from app.domain.errors import NotFound, InvalidStatusTransition

def update_status(repo: WorkOrderRepository, workorder_id: str, new_status: WorkOrderStatus) -> WorkOrder:
    wo = repo.get(workorder_id)
    if not wo or wo.is_deleted:
        raise NotFound(f"WorkOrder not found: {workorder_id}")

    if not wo.can_transition_to(new_status):
        raise InvalidStatusTransition(str(wo.status), str(new_status))

    updated = WorkOrder(
        id=wo.id,
        title=wo.title,
        description=wo.description,
        status=new_status,
        assignee_id=wo.assignee_id,
        due_date=wo.due_date,
        created_at=wo.created_at,
        is_deleted=wo.is_deleted,
    )
    return repo.update(updated)
