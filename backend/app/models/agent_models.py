import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from pydantic import BaseModel, Field
from app.core.database import Base

# SQLAlchemy Models for persisting Agent outputs
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False) # e.g. "spec_agent", "state_agent"
    status = Column(String(50), nullable=False, default="COMPLETED") # "RUNNING", "COMPLETED", "FAILED"
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    reasoning_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GeneratedScenario(Base):
    __tablename__ = "generated_scenarios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(50), default="HAPPY_PATH") # "HAPPY_PATH", "NEGATIVE_PATH"
    steps = Column(JSON, nullable=False) # List of API calls & expected status codes
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Schemas for Structured Agent Communication
class EntityRelation(BaseModel):
    parent_entity: str
    child_entity: str
    foreign_key: str
    relation_type: str = "one_to_many" # "one_to_many", "one_to_one"

class ERDGraphOutput(BaseModel):
    entities: List[str]
    relationships: List[EntityRelation]

class StateTransitionRule(BaseModel):
    entity: str
    from_state: str
    to_state: str
    is_valid: bool = True
    reason: str = ""

class StateMachineOutput(BaseModel):
    entity: str
    allowed_states: List[str]
    transitions: List[StateTransitionRule]

class ScenarioStep(BaseModel):
    step_number: int
    name: str
    endpoint_path: str
    http_method: str
    payload_template: Dict[str, Any] = {}
    expected_status_code: int = 200

class ScenarioOutput(BaseModel):
    title: str
    description: str
    scenario_type: str = "HAPPY_PATH"
    steps: List[ScenarioStep]

class MultiAgentAnalysisOutput(BaseModel):
    project_id: str
    erd_graph: ERDGraphOutput
    state_machines: List[StateMachineOutput]
    test_scenarios: List[ScenarioOutput]
