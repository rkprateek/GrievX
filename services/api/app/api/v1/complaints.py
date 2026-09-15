import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_roles
from app.core.config import get_settings
from app.infrastructure.db_session import get_db
from app.infrastructure.storage import delete_object, upload_bytes
from app.models.auth import RoleName, User
from app.models.complaint import Complaint, ComplaintImage, ComplaintStatus, ComplaintStatusHistory

router = APIRouter(prefix="/complaints", tags=["complaints"])

ALLOWED_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_DESCRIPTION_LENGTH = 5000
MIN_DESCRIPTION_LENGTH = 10


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise HTTPException(status_code=422, detail="Invalid campus location coordinates")


def validate_description(description: str) -> str:
    value = description.strip()
    if len(value) < MIN_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=422, detail="Description must be at least 10 characters")
    if len(value) > MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=422, detail="Description must not exceed 5000 characters")
    return value


async def read_and_validate_image(image: UploadFile) -> tuple[bytes, str, str]:
    settings = get_settings()
    content_type = image.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, and WebP images are allowed")

    data = await image.read(settings.max_complaint_image_size_bytes + 1)
    if len(data) > settings.max_complaint_image_size_bytes:
        raise HTTPException(status_code=413, detail="Image exceeds the maximum allowed size")

    try:
        with Image.open(__import__("io").BytesIO(data)) as verified:
            detected_format = (verified.format or "").upper()
            if detected_format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=415, detail="Unsupported image format")
            verified.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=415, detail="Uploaded file is not a valid image")

    expected_format = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[content_type]
    if detected_format != expected_format:
        raise HTTPException(status_code=415, detail="Image content does not match its declared type")
    return data, content_type, ALLOWED_TYPES[content_type]


def complaint_response(complaint: Complaint) -> dict:
    return {
        "id": complaint.complaint_id,
        "status": complaint.status,
        "description": complaint.description,
        "location": {
            "latitude": complaint.latitude,
            "longitude": complaint.longitude,
            "label": complaint.location_label,
        },
        "images": [
            {
                "id": image.id,
                "object_key": image.object_key,
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_complaint(
    description: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    location_label: str | None = Form(None),
    image: UploadFile | None = File(None),
    user: User = Depends(require_roles(RoleName.STUDENT)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    description = validate_description(description)
    validate_coordinates(latitude, longitude)
    if location_label is not None:
        location_label = location_label.strip()[:255] or None

    image_data = None
    content_type = None
    extension = None
    if image is not None:
        image_data, content_type, extension = await read_and_validate_image(image)

    complaint_uuid = str(uuid4())
    complaint_id = f"GRV-{complaint_uuid.replace('-', '')[:12].upper()}"
    object_key = f"complaints/{complaint_uuid}/{uuid4()}.{extension}" if image_data else None
    settings = get_settings()
    storage_client = getattr(db, "_grievx_storage_client", None)
    if image_data and storage_client is None:
        storage_client = getattr(db.bind, "_grievx_storage_client", None) if db.bind else None
    if image_data and storage_client is None:
        raise HTTPException(status_code=503, detail="Object storage is not available")

    if image_data:
        await asyncio.to_thread(upload_bytes, storage_client, settings.s3_bucket, object_key, image_data, content_type)

    complaint = Complaint(
        id=complaint_uuid,
        complaint_id=complaint_id,
        student_id=user.id,
        description=description,
        latitude=latitude,
        longitude=longitude,
        location_label=location_label,
        status=ComplaintStatus.SUBMITTED.value,
    )
    db.add(complaint)
    db.add(ComplaintStatusHistory(
        complaint_id=complaint_uuid,
        from_status=None,
        to_status=ComplaintStatus.SUBMITTED.value,
        changed_by=user.id,
    ))
    if image_data:
        db.add(ComplaintImage(
            complaint_id=complaint_uuid,
            object_key=object_key,
            original_filename=image.filename,
            content_type=content_type,
            size_bytes=len(image_data),
        ))
    try:
        await db.commit()
        await db.refresh(complaint)
        result = await db.scalar(
            select(Complaint).where(Complaint.id == complaint_uuid)
        )
        return complaint_response(result or complaint)
    except Exception:
        await db.rollback()
        if image_data:
            await asyncio.to_thread(delete_object, storage_client, settings.s3_bucket, object_key)
        raise


async def get_student_complaint(complaint_id: str, user: User, db: AsyncSession) -> Complaint:
    complaint = await db.scalar(
        select(Complaint)
        .where(Complaint.complaint_id == complaint_id, Complaint.student_id == user.id)
    )
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    await db.refresh(complaint, ["images", "status_history"])
    return complaint


@router.get("")
async def list_complaints(
    user: User = Depends(require_roles(RoleName.STUDENT)),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    result = await db.scalars(
        select(Complaint).where(Complaint.student_id == user.id).order_by(Complaint.created_at.desc())
    )
    complaints = list(result.all())
    return [complaint_response(complaint) for complaint in complaints]


@router.get("/{complaint_id}")
async def get_complaint(
    complaint_id: str,
    user: User = Depends(require_roles(RoleName.STUDENT)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    complaint = await get_student_complaint(complaint_id, user, db)
    return complaint_response(complaint)
