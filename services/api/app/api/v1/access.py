from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models.auth import RoleName, User

router = APIRouter(tags=["authorization"])


@router.get("/student/profile")
async def student_profile(user: User = Depends(require_roles(RoleName.STUDENT))):
    return {"user_id": user.id, "role": user.role.name, "scope": "student"}


@router.get("/staff/queue")
async def staff_queue(user: User = Depends(require_roles(RoleName.STAFF, RoleName.DEPARTMENT_HEAD, RoleName.ADMIN))):
    return {"user_id": user.id, "role": user.role.name, "scope": "staff_or_department"}


@router.get("/department/dashboard")
async def department_dashboard(user: User = Depends(require_roles(RoleName.DEPARTMENT_HEAD, RoleName.ADMIN))):
    return {"user_id": user.id, "role": user.role.name, "scope": "department"}


@router.get("/admin/dashboard")
async def admin_dashboard(user: User = Depends(require_roles(RoleName.ADMIN))):
    return {"user_id": user.id, "role": user.role.name, "scope": "campus_wide"}
