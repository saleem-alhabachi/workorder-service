from app.domain.ports import WorkOrderRepository
from app.domain.errors import NotFound

def get_workorder(repo: WorkOrderRepository, workorder_id: str):
    wo = repo.get(workorder_id)
    if not wo or wo.is_deleted:
        raise NotFound(f"WorkOrder not found: {workorder_id}")
    return wo
