from enum import Enum

from pydantic import BaseModel, Field


class PriorityValue(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class StatusValue(str, Enum):
    SUBMITTED = "SUBMITTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class AssignmentUpdate(BaseModel):
    department_id: int | None = Field(default=None, ge=1)
    staff_id: str | None = None


class PriorityUpdate(BaseModel):
    priority: PriorityValue


class StatusUpdate(BaseModel):
    status: StatusValue


class DepartmentOption(BaseModel):
    id: int
    name: str
    code: str


class StaffOption(BaseModel):
    id: str
    full_name: str
    email: str
    department_id: int | None


class ComplaintListQuery(BaseModel):
    q: str | None = None
