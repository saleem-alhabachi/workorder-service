# app/api/v1/workorders.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_workorder_repository, require_editor, require_viewer
from app.core.security import User
from app.domain.entities import WorkOrder
from app.domain.enums import WorkOrderStatus
from app.domain.exceptions import InvalidStatusTransitionError
from app.domain.interfaces import WorkOrderRepository
from app.usecases.create_workorder import CreateWorkOrderUseCase
from app.usecases.get_workorder import GetWorkOrderUseCase
from app.usecases.list_workorders import ListWorkOrdersUseCase
from app.usecases.update_workorder_status import UpdateWorkOrderStatusUseCase
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/workorders", tags=["workorders"])


class CreateWorkOrderRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)


class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=False)

    id: UUID
    title: str
    description: str
    status: str
    created_by: str
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, entity: WorkOrder) -> "WorkOrderResponse":
        return cls(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            status=entity.status.value,
            created_by=entity.created_by,
            created_at=entity.created_at.isoformat(),
            updated_at=entity.updated_at.isoformat(),
        )


class UpdateStatusRequest(BaseModel):
    status: WorkOrderStatus


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkOrderResponse,
)
async def create_workorder(
    body: CreateWorkOrderRequest,
    user: User = Depends(require_editor),
    repository: WorkOrderRepository = Depends(get_workorder_repository),
) -> WorkOrderResponse:
    use_case = CreateWorkOrderUseCase(repository)
    workorder = await use_case.execute(
        title=body.title,
        description=body.description,
        created_by=user.sub,
    )
    return WorkOrderResponse.from_entity(workorder)


@router.get("", response_model=list[WorkOrderResponse])
async def list_workorders(
    user: User = Depends(require_viewer),
    repository: WorkOrderRepository = Depends(get_workorder_repository),
) -> list[WorkOrderResponse]:
    use_case = ListWorkOrdersUseCase(repository)
    workorders = await use_case.execute()
    return [WorkOrderResponse.from_entity(wo) for wo in workorders]


@router.get("/{workorder_id}", response_model=WorkOrderResponse)
async def get_workorder(
    workorder_id: UUID,
    user: User = Depends(require_viewer),
    repository: WorkOrderRepository = Depends(get_workorder_repository),
) -> WorkOrderResponse:
    use_case = GetWorkOrderUseCase(repository)
    workorder = await use_case.execute(workorder_id)
    if workorder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    return WorkOrderResponse.from_entity(workorder)


@router.patch("/{workorder_id}/status", response_model=WorkOrderResponse)
async def update_workorder_status(
    workorder_id: UUID,
    body: UpdateStatusRequest,
    user: User = Depends(require_editor),
    repository: WorkOrderRepository = Depends(get_workorder_repository),
) -> WorkOrderResponse:
    use_case = UpdateWorkOrderStatusUseCase(repository)
    try:
        workorder = await use_case.execute(workorder_id, body.status)
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        ) from e
    if workorder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work order not found",
        )
    return WorkOrderResponse.from_entity(workorder)
