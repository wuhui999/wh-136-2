from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class UserRole(str, enum.Enum):
    EXCAVATOR = "excavator"
    CURATOR = "curator"
    EXPERT = "expert"
    ADMIN = "admin"


class ArtifactStatus(str, enum.Enum):
    EXCAVATED = "出土"
    CLEANED = "清洗"
    RESTORED = "修复"
    STORED = "入库"
    EXHIBITED = "展出"


class TrenchStatus(str, enum.Enum):
    ACTIVE = "发掘中"
    PAUSED = "暂停"
    COMPLETED = "完成"
    ARCHIVED = "归档"


class AuditStatus(str, enum.Enum):
    PENDING = "待处理"
    RESOLVED = "已解决"
    REJECTED = "已驳回"


class AuditType(str, enum.Enum):
    STRATUM_CONFLICT = "层位矛盾"
    DUPLICATE_CODE = "重复编号"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    hashed_password = Column(String(200), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.EXCAVATOR)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_trenches = relationship("Trench", back_populates="responsible_user", foreign_keys="Trench.responsible_user_id")


class Trench(Base):
    __tablename__ = "trenches"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    location = Column(String(200))
    status = Column(SQLEnum(TrenchStatus), default=TrenchStatus.ACTIVE)
    responsible_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)

    responsible_user = relationship("User", back_populates="created_trenches", foreign_keys=[responsible_user_id])
    strata = relationship("Stratum", back_populates="trench", cascade="all, delete-orphan")


class Stratum(Base):
    __tablename__ = "strata"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)
    trench_id = Column(Integer, ForeignKey("trenches.id"), nullable=False)
    soil_type = Column(String(100))
    estimated_age = Column(String(100))
    photo_url = Column(String(500))
    description = Column(Text)
    depth_from = Column(Float)
    depth_to = Column(Float)
    order_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    trench = relationship("Trench", back_populates="strata")
    artifacts = relationship("Artifact", back_populates="stratum")

    __table_args__ = ()


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100))
    stratum_id = Column(Integer, ForeignKey("strata.id"), nullable=False)
    coord_x = Column(Float)
    coord_y = Column(Float)
    coord_z = Column(Float)
    status = Column(SQLEnum(ArtifactStatus), default=ArtifactStatus.EXCAVATED)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stratum = relationship("Stratum", back_populates="artifacts")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)
    audit_type = Column(SQLEnum(AuditType), nullable=False)
    status = Column(SQLEnum(AuditStatus), default=AuditStatus.PENDING)
    description = Column(Text)
    related_ids = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolution_note = Column(Text)
