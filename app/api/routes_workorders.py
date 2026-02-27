from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.domain.models import WorkOrderStatus
from app.domain.errors import NotFound, InvalidStatusTransition
from app.infrastructure.db.repositories import SQLAlchemyWorkOrderRepository
from app.usecases.create_workorder import create_workorder, CreateWorkOrderInput
from app.usecases.get_workorder import get_workorder
from app.usecases.list_workorders import list_workorders, ListWorkOrdersInput
from app.usecases.update_status import update_status

router = APIRouter(prefix="/api/v1/workorders", tags=["workorders"])

class CreateWorkOrderRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    assignee_id: str | None = Field(default=None, max_length=64)
    due_date: date | None = None

class WorkOrderResponse(BaseModel):
    id: str
    title: str
    description: str
    status: WorkOrderStatus
    assignee_id: str | None
    due_date: date | None
    created_at: datetime

class UpdateStatusRequest(BaseModel):
    status: WorkOrderStatus

def to_response(wo) -> WorkOrderResponse:
    return WorkOrderResponse(
        id=wo.id,
        title=wo.title,
        description=wo.description,
        status=wo.status,
        assignee_id=wo.assignee_id,
        due_date=wo.due_date,
        created_at=wo.created_at,
    )

@router.post("", response_model=WorkOrderResponse, status_code=201, dependencies=[Depends(require_role("editor"))])
def create(req: CreateWorkOrderRequest, db: Session = Depends(get_db)):
    repo = SQLAlchemyWorkOrderRepository(db)
    wo = create_workorder(repo, CreateWorkOrderInput(**req.model_dump()))
    return to_response(wo)

@router.get("", response_model=list[WorkOrderResponse], dependencies=[Depends(require_role("viewer"))])
def list_(
    db: Session = Depends(get_db),
    status: WorkOrderStatus | None = Query(default=None),
    assignee_id: str | None = Query(default=None),
    due_from: date | None = Query(default=None),
    due_to: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    repo = SQLAlchemyWorkOrderRepository(db)
    items = list_workorders(repo, ListWorkOrdersInput(status, assignee_id, due_from, due_to, limit, offset))
    return [to_response(x) for x in items]

@router.get("/{workorder_id}", response_model=WorkOrderResponse, dependencies=[Depends(require_role("viewer"))])
def get_(workorder_id: str, db: Session = Depends(get_db)):
    repo = SQLAlchemyWorkOrderRepository(db)
    try:
        return to_response(get_workorder(repo, workorder_id))
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{workorder_id}/status", response_model=WorkOrderResponse, dependencies=[Depends(require_role("editor"))])
def patch_status(workorder_id: str, req: UpdateStatusRequest, db: Session = Depends(get_db)):
    repo = SQLAlchemyWorkOrderRepository(db)
    try:
        return to_response(update_status(repo, workorder_id, req.status))
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStatusTransition as e:
        raise HTTPException(status_code=409, detail=str(e))
