from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.models.project import Project
from app.models.agent_models import AgentRun, GeneratedScenario, MultiAgentAnalysisOutput
from app.agents.orchestrator import AgentOrchestrator

router = APIRouter()

class AgentAnalysisRequest(BaseModel):
    provider: str = "auto"              # "ollama", "gemini", "groq", "openai", "auto"
    api_key: Optional[str] = None       # Optional user API key
    model_name: Optional[str] = None    # Custom model name e.g. "gemini-1.5-pro", "gpt-4o", "llama3.3:70b"
    base_url: Optional[str] = None      # Custom endpoint URL e.g. "http://localhost:11434/v1"

@router.post("/{project_id}/analyze")
def trigger_agent_analysis(project_id: str, payload: Optional[AgentAnalysisRequest] = None, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    req = payload or AgentAnalysisRequest()

    try:
        orchestrator = AgentOrchestrator(
            db=db,
            provider=req.provider,
            api_key=req.api_key,
            model_name=req.model_name,
            base_url=req.base_url
        )
        result = orchestrator.run_pipeline(project_id)
        return {
            "status": "COMPLETED",
            "project_id": project_id,
            "provider_used": orchestrator.llm_factory.provider,
            "model_used": orchestrator.llm_factory.model_name,
            "erd_entities": result.erd_graph.entities,
            "relationships_count": len(result.erd_graph.relationships),
            "state_machines_count": len(result.state_machines),
            "scenarios_generated": len(result.test_scenarios),
            "scenarios": [s.model_dump() for s in result.test_scenarios]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")

@router.get("/{project_id}/scenarios")
def list_generated_scenarios(project_id: str, db: Session = Depends(get_db)):
    scenarios = db.query(GeneratedScenario).filter(GeneratedScenario.project_id == project_id).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "scenario_type": s.scenario_type,
            "steps": s.steps,
            "created_at": s.created_at.isoformat()
        } for s in scenarios
    ]

@router.get("/{project_id}/runs")
def list_agent_runs(project_id: str, db: Session = Depends(get_db)):
    runs = db.query(AgentRun).filter(AgentRun.project_id == project_id).all()
    return [
        {
            "id": r.id,
            "agent_name": r.agent_name,
            "status": r.status,
            "output_data": r.output_data,
            "created_at": r.created_at.isoformat()
        } for r in runs
    ]
