from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user, require_roles
from models import Trench, User, UserRole, TrenchStatus, Audit, AuditType, AuditStatus, Stratum
from schemas import TrenchCreate, TrenchUpdate, TrenchResponse

router = APIRouter(prefix="/api/trenches", tags=["探方"])


@router.get("", response_model=List[TrenchResponse])
async def list_trenches(
    status: TrenchStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Trench)
    if status:
        query = query.filter(Trench.status == status)
    trenches = query.all()
    result = []
    for t in trenches:
        resp = TrenchResponse.model_validate(t)
        resp.strata_count = len(t.strata)
        resp.responsible_user = t.responsible_user
        result.append(resp)
    return result


@router.get("/{trench_id}", response_model=TrenchResponse)
async def get_trench(
    trench_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trench = db.query(Trench).filter(Trench.id == trench_id).first()
    if not trench:
        raise HTTPException(status_code=404, detail="探方不存在")
    resp = TrenchResponse.model_validate(trench)
    resp.strata_count = len(trench.strata)
    resp.responsible_user = trench.responsible_user
    return resp


@router.post("", response_model=TrenchResponse)
async def create_trench(
    trench_in: TrenchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXCAVATOR, UserRole.ADMIN))
):
    existing = db.query(Trench).filter(Trench.code == trench_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="探方编号已存在")
    trench = Trench(**trench_in.model_dump())
    db.add(trench)
    db.commit()
    db.refresh(trench)
    resp = TrenchResponse.model_validate(trench)
    resp.strata_count = 0
    resp.responsible_user = trench.responsible_user
    return resp


@router.put("/{trench_id}", response_model=TrenchResponse)
async def update_trench(
    trench_id: int,
    trench_in: TrenchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXCAVATOR, UserRole.ADMIN))
):
    trench = db.query(Trench).filter(Trench.id == trench_id).first()
    if not trench:
        raise HTTPException(status_code=404, detail="探方不存在")
    if trench_in.code and trench_in.code != trench.code:
        existing = db.query(Trench).filter(Trench.code == trench_in.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="探方编号已存在")
    for key, value in trench_in.model_dump(exclude_unset=True).items():
        setattr(trench, key, value)
    db.commit()
    db.refresh(trench)
    resp = TrenchResponse.model_validate(trench)
    resp.strata_count = len(trench.strata)
    resp.responsible_user = trench.responsible_user
    return resp


@router.delete("/{trench_id}")
async def delete_trench(
    trench_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    trench = db.query(Trench).filter(Trench.id == trench_id).first()
    if not trench:
        raise HTTPException(status_code=404, detail="探方不存在")
    for stratum in trench.strata:
        if len(stratum.artifacts) > 0:
            raise HTTPException(status_code=400, detail=f"地层 {stratum.code} 下有关联出土物，无法删除探方")
    pending_audits = db.query(Audit).filter(
        Audit.related_ids.like(f"%{trench_id}%"),
        Audit.status == AuditStatus.PENDING
    ).count()
    if pending_audits > 0:
        raise HTTPException(status_code=400, detail="存在待处理审核，无法删除")
    db.delete(trench)
    db.commit()
    return {"message": "删除成功"}
