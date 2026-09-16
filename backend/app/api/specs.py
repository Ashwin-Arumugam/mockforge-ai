from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.project import Project, APISpec
from app.spec_parser.parser import OpenAPIParser
from app.agents.spec_agent import SpecIntelligenceAgent

router = APIRouter()

@router.post("/{project_id}/upload")
def upload_spec(project_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    raw_spec = payload.get("raw_spec")
    if not raw_spec:
        raise HTTPException(status_code=400, detail="Missing 'raw_spec' in payload")

    try:
        parser = OpenAPIParser(raw_spec)
        normalized = parser.parse()
        erd_graph = SpecIntelligenceAgent().analyze(normalized).model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OpenAPI Spec: {str(e)}")

    api_spec = APISpec(
        project_id=project_id,
        raw_spec=raw_spec,
        normalized_spec=normalized
    )
    db.add(api_spec)
    db.commit()
    db.refresh(api_spec)

    return {
        "id": api_spec.id,
        "project_id": api_spec.project_id,
        "title": normalized.get("info", {}).get("title", "API Spec"),
        "version": normalized.get("info", {}).get("version", "1.0.0"),
        "routes_count": len(normalized.get("routes", [])),
        "entities_discovered": list(set(r.get("entity_type") for r in normalized.get("routes", []) if r.get("entity_type") != "default")),
        "erd_graph": erd_graph
    }

@router.get("/{project_id}/active")
def get_active_spec(project_id: str, db: Session = Depends(get_db)):
    api_spec = db.query(APISpec).filter(APISpec.project_id == project_id).order_by(APISpec.created_at.desc()).first()
    if not api_spec:
        raise HTTPException(status_code=404, detail=f"No active spec found for project '{project_id}'")

    normalized = api_spec.normalized_spec or {}
    erd_graph = SpecIntelligenceAgent().analyze(normalized).model_dump()

    return {
        "id": api_spec.id,
        "project_id": api_spec.project_id,
        "raw_spec": api_spec.raw_spec,
        "normalized_spec": normalized,
        "erd_graph": erd_graph,
        "created_at": api_spec.created_at.isoformat()
    }
