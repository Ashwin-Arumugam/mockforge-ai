from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.models.project import Project
from app.models.mock_state import ChaosRule

router = APIRouter()

class ChaosRuleCreate(BaseModel):
    endpoint_path: str                 # e.g. "/payments"
    http_method: str = "*"             # "POST", "GET", or "*"
    failure_type: str                  # "latency", "status_code", "malformed"
    probability: float = 1.0           # 0.0 to 1.0
    config: Dict[str, Any] = {}        # e.g. {"duration_ms": 500} or {"status_code": 500}
    is_active: bool = True

class ChaosRuleOut(BaseModel):
    id: str
    project_id: str
    endpoint_path: str
    http_method: str
    failure_type: str
    probability: float
    config: Dict[str, Any]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

@router.post("/{project_id}/rules", response_model=ChaosRuleOut)
def create_chaos_rule(project_id: str, payload: ChaosRuleCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    rule = ChaosRule(
        project_id=project_id,
        endpoint_path=payload.endpoint_path,
        http_method=payload.http_method,
        failure_type=payload.failure_type,
        probability=payload.probability,
        config=payload.config,
        is_active=payload.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return ChaosRuleOut(
        id=rule.id,
        project_id=rule.project_id,
        endpoint_path=rule.endpoint_path,
        http_method=rule.http_method,
        failure_type=rule.failure_type,
        probability=float(rule.probability),
        config=rule.config,
        is_active=bool(rule.is_active)
    )

@router.get("/{project_id}/rules", response_model=List[ChaosRuleOut])
def list_chaos_rules(project_id: str, db: Session = Depends(get_db)):
    rules = db.query(ChaosRule).filter(ChaosRule.project_id == project_id).all()
    return [
        ChaosRuleOut(
            id=r.id,
            project_id=r.project_id,
            endpoint_path=r.endpoint_path,
            http_method=r.http_method,
            failure_type=r.failure_type,
            probability=float(r.probability),
            config=r.config if isinstance(r.config, dict) else {},
            is_active=bool(r.is_active)
        ) for r in rules
    ]

@router.delete("/{project_id}/rules/{rule_id}")
def delete_chaos_rule(project_id: str, rule_id: str, db: Session = Depends(get_db)):
    rule = db.query(ChaosRule).filter(ChaosRule.project_id == project_id, ChaosRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Chaos rule not found")
    db.delete(rule)
    db.commit()
    return {"message": f"Chaos rule '{rule_id}' deleted successfully"}
