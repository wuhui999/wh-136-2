from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from auth import get_current_user, require_roles
from models import Artifact, Stratum, User, UserRole, ArtifactStatus, Audit, AuditType, AuditStatus
from schemas import ArtifactCreate, ArtifactUpdate, ArtifactResponse, StratumResponse, ArtifactListResponse

router = APIRouter(prefix="/api/artifacts", tags=["出土物"])

STATUS_FLOW = {
    ArtifactStatus.EXCAVATED: [ArtifactStatus.CLEANED],
    ArtifactStatus.CLEANED: [ArtifactStatus.RESTORED, ArtifactStatus.STORED],
    ArtifactStatus.RESTORED: [ArtifactStatus.STORED, ArtifactStatus.EXHIBITED],
    ArtifactStatus.STORED: [ArtifactStatus.EXHIBITED],
    ArtifactStatus.EXHIBITED: [ArtifactStatus.STORED],
}


def check_status_transition(old_status: ArtifactStatus, new_status: ArtifactStatus, user_role: UserRole) -> bool:
    if old_status == new_status:
        return True
    if new_status not in STATUS_FLOW.get(old_status, []):
        return False
    if new_status == ArtifactStatus.CLEANED and user_role not in [UserRole.CURATOR, UserRole.ADMIN]:
        return False
    if new_status == ArtifactStatus.RESTORED and user_role not in [UserRole.CURATOR, UserRole.ADMIN]:
        return False
    if new_status in [ArtifactStatus.STORED, ArtifactStatus.EXHIBITED] and user_role not in [UserRole.CURATOR, UserRole.ADMIN]:
        return False
    return True


@router.get("", response_model=ArtifactListResponse)
async def list_artifacts(
    stratum_id: int = None,
    status: ArtifactStatus = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Artifact)
    if stratum_id:
        query = query.filter(Artifact.stratum_id == stratum_id)
    if status:
        query = query.filter(Artifact.status == status)
    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            (Artifact.code.ilike(keyword_pattern)) |
            (Artifact.category.ilike(keyword_pattern))
        )
    total = query.count()
    offset = (page - 1) * page_size
    artifacts = query.order_by(Artifact.created_at.desc()).offset(offset).limit(page_size).all()
    return ArtifactListResponse(
        items=artifacts,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="出土物不存在")
    return artifact


def check_duplicate_code(db: Session, code: str, exclude_id: int = None):
    query = db.query(Artifact).filter(Artifact.code == code)
    if exclude_id:
        query = query.filter(Artifact.id != exclude_id)
    existing = query.first()
    if existing:
        audit = Audit(
            audit_type=AuditType.DUPLICATE_CODE,
            description=f"出土物编号 {code} 重复，已存在编号: {existing.id}",
            related_ids=f"{exclude_id or 'new'},{existing.id}",
            status=AuditStatus.PENDING
        )
        db.add(audit)
        return True
    return False


@router.post("", response_model=ArtifactResponse)
async def create_artifact(
    artifact_in: ArtifactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXCAVATOR, UserRole.ADMIN))
):
    stratum = db.query(Stratum).filter(Stratum.id == artifact_in.stratum_id).first()
    if not stratum:
        raise HTTPException(status_code=400, detail="所属地层不存在")
    check_duplicate_code(db, artifact_in.code)
    existing = db.query(Artifact).filter(Artifact.code == artifact_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="出土物编号已存在，全局编号必须唯一")
    artifact = Artifact(**artifact_in.model_dump())
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.put("/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: int,
    artifact_in: ArtifactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="出土物不存在")
    if artifact_in.code and artifact_in.code != artifact.code:
        check_duplicate_code(db, artifact_in.code, exclude_id=artifact_id)
        existing = db.query(Artifact).filter(Artifact.code == artifact_in.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="出土物编号已存在，全局编号必须唯一")
    if artifact_in.status and artifact_in.status != artifact.status:
        if not check_status_transition(artifact.status, artifact_in.status, current_user.role):
            raise HTTPException(
                status_code=400,
                detail=f"状态流转不允许: {artifact.status.value} -> {artifact_in.status.value}，或权限不足"
            )
    if artifact_in.stratum_id and artifact_in.stratum_id != artifact.stratum_id:
        stratum = db.query(Stratum).filter(Stratum.id == artifact_in.stratum_id).first()
        if not stratum:
            raise HTTPException(status_code=400, detail="所属地层不存在")
    for key, value in artifact_in.model_dump(exclude_unset=True).items():
        setattr(artifact, key, value)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="出土物不存在")
    db.delete(artifact)
    db.commit()
    return {"message": "删除成功"}
