from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database import get_db
from auth import get_current_user, require_roles
from models import Audit, User, UserRole, AuditStatus
from schemas import AuditCreate, AuditUpdate, AuditResponse

router = APIRouter(prefix="/api/audits", tags=["审核"])


@router.get("", response_model=List[AuditResponse])
async def list_audits(
    status: AuditStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Audit)
    if status:
        query = query.filter(Audit.status == status)
    audits = query.order_by(Audit.created_at.desc()).all()
    return audits


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    return audit


@router.post("", response_model=AuditResponse)
async def create_audit(
    audit_in: AuditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    audit = Audit(**audit_in.model_dump())
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


@router.put("/{audit_id}", response_model=AuditResponse)
async def resolve_audit(
    audit_id: int,
    audit_in: AuditUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXPERT, UserRole.ADMIN))
):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="审核记录不存在")
    if audit.status != AuditStatus.PENDING:
        raise HTTPException(status_code=400, detail="该审核已处理")
    if audit_in.status:
        audit.status = audit_in.status
    if audit_in.resolution_note:
        audit.resolution_note = audit_in.resolution_note
    audit.resolved_by = current_user.id
    audit.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(audit)
    return audit


@router.delete("/{audit_id}")
async def delete_audit(
    audit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    audit = db.query(Audit).filter(Audit.id == audit_id).first()
    if audit:
        db.delete(audit)
        db.commit()
    return {"message": "删除成功"}
