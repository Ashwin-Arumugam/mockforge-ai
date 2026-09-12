import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index, Float, Boolean
from app.core.database import Base

class MockRecord(Base):
    __tablename__ = "mock_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., 'users', 'orders'
    entity_id = Column(String(255), nullable=False, index=True)    # extracted ID e.g. 'usr_123'
    data = Column(JSON, nullable=False)                            # Multi-dialect generic JSON column
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_project_entity_lookup", "project_id", "entity_type", "entity_id"),
    )

class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_entity_type = Column(String(100), nullable=False, index=True) # e.g. 'users'
    parent_entity_id = Column(String(255), nullable=False, index=True)   # e.g. 'usr_123'
    child_entity_type = Column(String(100), nullable=False, index=True)  # e.g. 'orders'
    child_entity_id = Column(String(255), nullable=False, index=True)   # e.g. 'ord_456'
    foreign_key_name = Column(String(100), nullable=False)               # e.g. 'user_id'
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_parent_child_lookup", "project_id", "parent_entity_type", "parent_entity_id"),
        Index("idx_child_parent_lookup", "project_id", "child_entity_type", "child_entity_id"),
    )

class ChaosRule(Base):
    __tablename__ = "chaos_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_path = Column(String, nullable=False) # e.g. "/payments"
    http_method = Column(String(10), nullable=False, default="*") # e.g. "POST" or "*"
    failure_type = Column(String(50), nullable=False) # "latency", "status_code", "malformed"
    probability = Column(Float, nullable=False, default=1.0) # 0.0 to 1.0
    config = Column(JSON, nullable=False) # e.g. {"duration_ms": 500, "status_code": 500}
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
