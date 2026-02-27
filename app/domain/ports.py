from abc import ABC, abstractmethod
from typing import Iterable, Optional
from datetime import date
from .models import WorkOrder, WorkOrderStatus

class WorkOrderRepository(ABC):
    @abstractmethod
    def create(self, wo: WorkOrder) -> WorkOrder: ...

    @abstractmethod
    def get(self, workorder_id: str) -> Optional[WorkOrder]: ...

    @abstractmethod
    def list(
        self,
        status: Optional[WorkOrderStatus] = None,
        assignee_id: Optional[str] = None,
        due_from: Optional[date] = None,
        due_to: Optional[date] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Iterable[WorkOrder]: ...

    @abstractmethod
    def update(self, wo: WorkOrder) -> WorkOrder: ...
