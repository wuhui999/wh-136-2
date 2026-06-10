from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, ArtifactStatus, TrenchStatus, AuditStatus, AuditType


class Token(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: UserRole = UserRole.EXCAVATOR


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


Token.model_rebuild()


class TrenchBase(BaseModel):
    code: str
    location: Optional[str] = None
    status: TrenchStatus = TrenchStatus.ACTIVE
    description: Optional[str] = None
    responsible_user_id: Optional[int] = None


class TrenchCreate(TrenchBase):
    pass


class TrenchUpdate(BaseModel):
    code: Optional[str] = None
    location: Optional[str] = None
    status: Optional[TrenchStatus] = None
    description: Optional[str] = None
    responsible_user_id: Optional[int] = None


class TrenchResponse(TrenchBase):
    id: int
    created_at: datetime
    strata_count: Optional[int] = 0
    responsible_user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class StratumBase(BaseModel):
    code: str
    trench_id: int
    soil_type: Optional[str] = None
    estimated_age: Optional[str] = None
    photo_url: Optional[str] = None
    description: Optional[str] = None
    depth_from: Optional[float] = None
    depth_to: Optional[float] = None
    order_index: Optional[int] = None


class StratumCreate(StratumBase):
    pass


class StratumUpdate(BaseModel):
    code: Optional[str] = None
    soil_type: Optional[str] = None
    estimated_age: Optional[str] = None
    photo_url: Optional[str] = None
    description: Optional[str] = None
    depth_from: Optional[float] = None
    depth_to: Optional[float] = None
    order_index: Optional[int] = None


class StratumResponse(StratumBase):
    id: int
    created_at: datetime
    artifacts_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ArtifactBase(BaseModel):
    code: str
    category: Optional[str] = None
    stratum_id: int
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    coord_z: Optional[float] = None
    status: ArtifactStatus = ArtifactStatus.EXCAVATED
    description: Optional[str] = None


class ArtifactCreate(ArtifactBase):
    pass


class ArtifactUpdate(BaseModel):
    code: Optional[str] = None
    category: Optional[str] = None
    stratum_id: Optional[int] = None
    coord_x: Optional[float] = None
    coord_y: Optional[float] = None
    coord_z: Optional[float] = None
    status: Optional[ArtifactStatus] = None
    description: Optional[str] = None


class ArtifactResponse(ArtifactBase):
    id: int
    created_at: datetime
    updated_at: datetime
    stratum: Optional[StratumResponse] = None

    class Config:
        from_attributes = True


class AuditBase(BaseModel):
    audit_type: AuditType
    description: Optional[str] = None
    related_ids: Optional[str] = None


class AuditCreate(AuditBase):
    pass


class AuditUpdate(BaseModel):
    status: Optional[AuditStatus] = None
    resolution_note: Optional[str] = None


class AuditResponse(AuditBase):
    id: int
    status: AuditStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_note: Optional[str] = None

    class Config:
        from_attributes = True


class RelationNode(BaseModel):
    id: str
    label: str
    type: str
    data: Optional[dict] = None


class RelationEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class RelationGraph(BaseModel):
    nodes: List[RelationNode]
    edges: List[RelationEdge]
