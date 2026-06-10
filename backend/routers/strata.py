from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user, require_roles
from models import Stratum, Trench, User, UserRole, Artifact, Audit, AuditType, AuditStatus
from schemas import StratumCreate, StratumUpdate, StratumResponse

router = APIRouter(prefix="/api/strata", tags=["地层"])


@router.get("", response_model=List[StratumResponse])
async def list_strata(
    trench_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Stratum)
    if trench_id:
        query = query.filter(Stratum.trench_id == trench_id)
    strata = query.order_by(Stratum.order_index.asc().nullslast()).all()
    result = []
    for s in strata:
        resp = StratumResponse.model_validate(s)
        resp.artifacts_count = len(s.artifacts)
        result.append(resp)
    return result


@router.get("/{stratum_id}", response_model=StratumResponse)
async def get_stratum(
    stratum_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stratum = db.query(Stratum).filter(Stratum.id == stratum_id).first()
    if not stratum:
        raise HTTPException(status_code=404, detail="地层不存在")
    resp = StratumResponse.model_validate(stratum)
    resp.artifacts_count = len(stratum.artifacts)
    return resp


def check_stratum_conflict(db: Session, stratum_in: StratumCreate, exclude_id: int = None):
    trench = db.query(Trench).filter(Trench.id == stratum_in.trench_id).first()
    if not trench:
        return
    existing = db.query(Stratum).filter(
        Stratum.trench_id == stratum_in.trench_id,
        Stratum.code == stratum_in.code
    )
    if exclude_id:
        existing = existing.filter(Stratum.id != exclude_id)
    if existing.first():
        return
    if stratum_in.order_index is not None:
        conflict = db.query(Stratum).filter(
            Stratum.trench_id == stratum_in.trench_id,
            Stratum.order_index == stratum_in.order_index
        )
        if exclude_id:
            conflict = conflict.filter(Stratum.id != exclude_id)
        conflict_item = conflict.first()
        if conflict_item:
            audit = Audit(
                audit_type=AuditType.STRATUM_CONFLICT,
                description=f"探方 {trench.code} 中地层 {stratum_in.code} 与 {conflict_item.code} 层位序号(order_index)相同，存在层位关系矛盾",
                related_ids=f"{exclude_id or 'new'},{conflict_item.id}",
                status=AuditStatus.PENDING
            )
            db.add(audit)


@router.post("", response_model=StratumResponse)
async def create_stratum(
    stratum_in: StratumCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXCAVATOR, UserRole.ADMIN))
):
    trench = db.query(Trench).filter(Trench.id == stratum_in.trench_id).first()
    if not trench:
        raise HTTPException(status_code=400, detail="所属探方不存在")
    same_code = db.query(Stratum).filter(
        Stratum.trench_id == stratum_in.trench_id,
        Stratum.code == stratum_in.code
    ).first()
    if same_code:
        raise HTTPException(status_code=400, detail="同一探方内层位号不能重复")
    check_stratum_conflict(db, stratum_in)
    stratum = Stratum(**stratum_in.model_dump())
    db.add(stratum)
    db.commit()
    db.refresh(stratum)
    resp = StratumResponse.model_validate(stratum)
    resp.artifacts_count = 0
    return resp


@router.put("/{stratum_id}", response_model=StratumResponse)
async def update_stratum(
    stratum_id: int,
    stratum_in: StratumUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.EXCAVATOR, UserRole.ADMIN))
):
    stratum = db.query(Stratum).filter(Stratum.id == stratum_id).first()
    if not stratum:
        raise HTTPException(status_code=404, detail="地层不存在")
    if stratum_in.code and stratum_in.code != stratum.code:
        same_code = db.query(Stratum).filter(
            Stratum.trench_id == stratum.trench_id,
            Stratum.code == stratum_in.code
        ).first()
        if same_code:
            raise HTTPException(status_code=400, detail="同一探方内层位号不能重复")
    temp_data = StratumCreate(
        code=stratum_in.code or stratum.code,
        trench_id=stratum.trench_id,
        order_index=stratum_in.order_index if stratum_in.order_index is not None else stratum.order_index
    )
    check_stratum_conflict(db, temp_data, exclude_id=stratum_id)
    for key, value in stratum_in.model_dump(exclude_unset=True).items():
        setattr(stratum, key, value)
    db.commit()
    db.refresh(stratum)
    resp = StratumResponse.model_validate(stratum)
    resp.artifacts_count = len(stratum.artifacts)
    return resp


@router.delete("/{stratum_id}")
async def delete_stratum(
    stratum_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    stratum = db.query(Stratum).filter(Stratum.id == stratum_id).first()
    if not stratum:
        raise HTTPException(status_code=404, detail="地层不存在")
    artifact_count = db.query(Artifact).filter(Artifact.stratum_id == stratum_id).count()
    if artifact_count > 0:
        raise HTTPException(status_code=400, detail=f"该地层下有关联 {artifact_count} 件出土物，无法删除，请先处理关联出土物")
    pending_audits = db.query(Audit).filter(
        Audit.related_ids.like(f"%{stratum_id}%"),
        Audit.status == AuditStatus.PENDING
    ).count()
    if pending_audits > 0:
        raise HTTPException(status_code=400, detail="存在待处理审核，无法删除")
    db.delete(stratum)
    db.commit()
    return {"message": "删除成功"}
