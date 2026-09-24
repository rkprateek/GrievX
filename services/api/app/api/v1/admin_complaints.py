import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, aliased

from app.api.deps import require_roles
from app.core.config import get_settings
from app.infrastructure.db_session import get_db
from app.infrastructure.storage import create_presigned_get_url
from app.models.auth import Department, RoleName, User
from app.models.complaint import (
    AuditLog,
    Complaint,
    ComplaintImage,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintStatusHistory,
    StaffAssignment,
)
from app.schemas.admin_complaints import AssignmentUpdate, PriorityUpdate, StatusUpdate

router = APIRouter(prefix="/admin", tags=["admin complaints"])

OPS_ROLES = (RoleName.ADMIN, RoleName.STAFF, RoleName.DEPARTMENT_HEAD)
STATUS_TRANSITIONS = {
    ComplaintStatus.SUBMITTED.value: {ComplaintStatus.ASSIGNED.value, ComplaintStatus.REJECTED.value},
    ComplaintStatus.ASSIGNED.value: {ComplaintStatus.IN_PROGRESS.value, ComplaintStatus.REJECTED.value},
    ComplaintStatus.IN_PROGRESS.value: {ComplaintStatus.RESOLVED.value, ComplaintStatus.REJECTED.value},
    ComplaintStatus.RESOLVED.value: {ComplaintStatus.CLOSED.value, ComplaintStatus.IN_PROGRESS.value},
    ComplaintStatus.CLOSED.value: set(),
    ComplaintStatus.REJECTED.value: set(),
}


def scoped_filter(user: User):
    if user.role.name == RoleName.ADMIN.value:
        return None
    if user.department_id is None:
        return Complaint.id == "__no_department_scope__"
    if user.role.name == RoleName.DEPARTMENT_HEAD.value:
        return Complaint.department_id == user.department_id
    return or_(Complaint.assigned_staff_id == user.id, Complaint.department_id == user.department_id)


def add_scope(stmt, user: User):
    condition = scoped_filter(user)
    return stmt if condition is None else stmt.where(condition)


def audit(db: AsyncSession, actor: User, action: str, complaint: Complaint, details: dict) -> None:
    db.add(
        AuditLog(
            actor_id=actor.id,
            action=action,
            resource_type="complaint",
            resource_id=complaint.id,
            details=json.dumps(details, sort_keys=True),
        )
    )


async def load_complaint(complaint_id: str, user: User, db: AsyncSession) -> Complaint:
    stmt = (
        select(Complaint)
        .options(
            selectinload(Complaint.student).selectinload(User.department),
            selectinload(Complaint.department),
            selectinload(Complaint.assigned_staff).selectinload(User.department),
            selectinload(Complaint.images),
            selectinload(Complaint.status_history),
        )
        .where(Complaint.complaint_id == complaint_id)
        .execution_options(populate_existing=True)
    )
    stmt = add_scope(stmt, user)
    complaint = await db.scalar(stmt)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


def serialize_complaint(complaint: Complaint, user: User) -> dict:
    student = complaint.student
    return {
        "id": complaint.complaint_id,
        "description": complaint.description,
        "status": complaint.status,
        "priority": complaint.priority,
        "location": {
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "label": complaint.location_label,
        },
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "department": student.department.name if student.department else None,
        } if user.role.name in {
            RoleName.ADMIN.value,
            RoleName.DEPARTMENT_HEAD.value,
            RoleName.STAFF.value,
        } else None,
        "department": (
            {"id": complaint.department.id, "name": complaint.department.name, "code": complaint.department.code}
            if complaint.department else None
        ),
        "assigned_staff": (
            {
                "id": complaint.assigned_staff.id,
                "full_name": complaint.assigned_staff.full_name,
                "email": complaint.assigned_staff.email,
                "department_id": complaint.assigned_staff.department_id,
            }
            if complaint.assigned_staff else None
        ),
        "images": [
            {
                "id": image.id,
                "filename": image.original_filename,
                "content_type": image.content_type,
                "size_bytes": image.size_bytes,
            }
            for image in complaint.images
        ],
        "history": [
            {
                "from_status": entry.from_status,
                "to_status": entry.to_status,
                "created_at": entry.created_at,
            }
            for entry in complaint.status_history
        ],
        "created_at": complaint.created_at,
        "updated_at": complaint.updated_at,
    }


@router.get("/overview")
async def dashboard_overview(
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
    condition = scoped_filter(user)
    if condition is not None:
        stmt = stmt.where(condition)
    rows = (await db.execute(stmt)).all()
    counts = {item.value: 0 for item in ComplaintStatus}
    counts.update({status_name: int(count) for status_name, count in rows})
    return {
        "total": sum(counts.values()),
        "submitted": counts[ComplaintStatus.SUBMITTED.value],
        "assigned": counts[ComplaintStatus.ASSIGNED.value],
        "in_progress": counts[ComplaintStatus.IN_PROGRESS.value],
        "resolved": counts[ComplaintStatus.RESOLVED.value],
        "closed": counts[ComplaintStatus.CLOSED.value],
        "rejected": counts[ComplaintStatus.REJECTED.value],
    }


@router.get("/complaints")
async def list_admin_complaints(
    q: str | None = Query(default=None, max_length=120),
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    department_id: int | None = Query(default=None, ge=1),
    assigned_staff_id: str | None = None,
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    student = aliased(User)
    stmt = (
        select(Complaint)
        .join(student, Complaint.student_id == student.id)
        .options(
            selectinload(Complaint.student).selectinload(User.department),
            selectinload(Complaint.department),
            selectinload(Complaint.assigned_staff).selectinload(User.department),
            selectinload(Complaint.images),
            selectinload(Complaint.status_history),
        )
    )
    stmt = add_scope(stmt, user)
    if q:
        needle = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Complaint.complaint_id.ilike(needle),
                Complaint.description.ilike(needle),
                student.full_name.ilike(needle),
                student.email.ilike(needle),
            )
        )
    if status_filter:
        if status_filter not in {item.value for item in ComplaintStatus}:
            raise HTTPException(status_code=422, detail="Invalid complaint status filter")
        stmt = stmt.where(Complaint.status == status_filter)
    if priority:
        if priority not in {item.value for item in ComplaintPriority}:
            raise HTTPException(status_code=422, detail="Invalid complaint priority filter")
        stmt = stmt.where(Complaint.priority == priority)
    if department_id is not None:
        stmt = stmt.where(Complaint.department_id == department_id)
    if assigned_staff_id:
        stmt = stmt.where(Complaint.assigned_staff_id == assigned_staff_id)

    sort_map = {
        "created_at": Complaint.created_at,
        "updated_at": Complaint.updated_at,
        "status": Complaint.status,
        "priority": Complaint.priority,
    }
    if sort not in sort_map:
        raise HTTPException(status_code=422, detail="Invalid sort field")
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=422, detail="Invalid sort order")
    stmt = stmt.order_by((asc if order == "asc" else desc)(sort_map[sort]))
    complaints = (await db.scalars(stmt)).all()
    return [serialize_complaint(item, user) for item in complaints]


@router.get("/complaints/departments")
async def list_departments(
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(Department).order_by(Department.name)
    if user.role.name != RoleName.ADMIN.value:
        if user.department_id is None:
            return []
        stmt = stmt.where(Department.id == user.department_id)
    return [
        {"id": item.id, "name": item.name, "code": item.code}
        for item in (await db.scalars(stmt)).all()
    ]


@router.get("/complaints/staff")
async def list_staff(
    department_id: int | None = Query(default=None, ge=1),
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    target_department = department_id
    if user.role.name != RoleName.ADMIN.value:
        if user.department_id is None:
            return []
        if target_department is not None and target_department != user.department_id:
            raise HTTPException(status_code=403, detail="Staff scope does not allow this department")
        target_department = user.department_id
    stmt = (
        select(User)
        .join(User.role)
        .where(User.is_active.is_(True), User.role.has(name=RoleName.STAFF.value))
        .order_by(User.full_name)
    )
    if target_department is not None:
        stmt = stmt.where(User.department_id == target_department)
    return [
        {"id": item.id, "full_name": item.full_name, "email": item.email, "department_id": item.department_id}
        for item in (await db.scalars(stmt)).all()
    ]


@router.get("/complaints/{complaint_id}")
async def complaint_detail(
    complaint_id: str,
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return serialize_complaint(await load_complaint(complaint_id, user, db), user)


@router.get("/complaints/{complaint_id}/images/{image_id}")
async def complaint_image(
    complaint_id: str,
    image_id: str,
    request: Request,
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    complaint = await load_complaint(complaint_id, user, db)
    image = await db.scalar(
        select(ComplaintImage).where(ComplaintImage.id == image_id, ComplaintImage.complaint_id == complaint.id)
    )
    if image is None:
        raise HTTPException(status_code=404, detail="Complaint image not found")
    storage_client = getattr(request.app.state, "storage_client", None)
    if storage_client is None:
        raise HTTPException(status_code=503, detail="Object storage is not available")
    url = await asyncio.to_thread(
        create_presigned_get_url,
        storage_client,
        get_settings().s3_bucket,
        image.object_key,
    )
    return {"url": url, "expires_in": 900, "content_type": image.content_type}


@router.patch("/complaints/{complaint_id}/assignment")
async def update_assignment(
    complaint_id: str,
    payload: AssignmentUpdate,
    user: User = Depends(require_roles(RoleName.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    complaint = await load_complaint(complaint_id, user, db)
    staff = None
    department_id = payload.department_id
    if payload.staff_id:
        staff = await db.scalar(
            select(User).options(selectinload(User.role)).where(User.id == payload.staff_id, User.is_active.is_(True))
        )
        if staff is None or staff.role.name != RoleName.STAFF.value:
            raise HTTPException(status_code=422, detail="Assigned user must be an active staff member")
        if staff.department_id is None:
            raise HTTPException(status_code=422, detail="Assigned staff must belong to a department")
        if department_id is None:
            department_id = staff.department_id
        if staff.department_id != department_id:
            raise HTTPException(status_code=422, detail="Staff department does not match complaint department")
    if department_id is not None and await db.get(Department, department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")

    old_department = complaint.department_id
    old_staff = complaint.assigned_staff_id
    complaint.department_id = department_id
    complaint.assigned_staff_id = staff.id if staff else None

    if complaint.assigned_staff_id and complaint.status == ComplaintStatus.SUBMITTED.value:
        old_status = complaint.status
        complaint.status = ComplaintStatus.ASSIGNED.value
        db.add(
            ComplaintStatusHistory(
                complaint_id=complaint.id,
                from_status=old_status,
                to_status=complaint.status,
                changed_by=user.id,
            )
        )

    db.add(
        StaffAssignment(
            complaint_id=complaint.id,
            staff_id=complaint.assigned_staff_id,
            assigned_by=user.id,
            department_id=department_id,
        )
    )
    audit(
        db,
        user,
        "ASSIGNMENT_CHANGED",
        complaint,
        {
            "old_department_id": old_department,
            "new_department_id": department_id,
            "old_staff_id": old_staff,
            "new_staff_id": complaint.assigned_staff_id,
        },
    )
    await db.commit()
    return serialize_complaint(await load_complaint(complaint_id, user, db), user)


@router.patch("/complaints/{complaint_id}/priority")
async def update_priority(
    complaint_id: str,
    payload: PriorityUpdate,
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    complaint = await load_complaint(complaint_id, user, db)
    if complaint.priority == payload.priority.value:
        return serialize_complaint(complaint, user)
    old_priority = complaint.priority
    complaint.priority = payload.priority.value
    audit(db, user, "PRIORITY_CHANGED", complaint, {"from": old_priority, "to": complaint.priority})
    await db.commit()
    return serialize_complaint(await load_complaint(complaint_id, user, db), user)


@router.patch("/complaints/{complaint_id}/status")
async def update_status(
    complaint_id: str,
    payload: StatusUpdate,
    user: User = Depends(require_roles(*OPS_ROLES)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    complaint = await load_complaint(complaint_id, user, db)
    old_status = complaint.status
    new_status = payload.status.value
    if old_status == new_status:
        return serialize_complaint(complaint, user)
    if new_status not in STATUS_TRANSITIONS.get(old_status, set()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invalid status transition: {old_status} -> {new_status}",
        )
    complaint.status = new_status
    db.add(
        ComplaintStatusHistory(
            complaint_id=complaint.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=user.id,
        )
    )
    audit(db, user, "STATUS_CHANGED", complaint, {"from": old_status, "to": new_status})
    await db.commit()
    return serialize_complaint(await load_complaint(complaint_id, user, db), user)
