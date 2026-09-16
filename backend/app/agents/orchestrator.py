from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.project import APISpec
from app.models.agent_models import (
    AgentRun, 
    GeneratedScenario, 
    MultiAgentAnalysisOutput, 
    ERDGraphOutput, 
    StateMachineOutput
)
from app.agents.llm_factory import LLMProviderFactory
from app.agents.spec_agent import SpecIntelligenceAgent
from app.agents.state_agent import StateMachineAgent
from app.agents.scenario_agent import ScenarioAgent
from app.agents.critic_agent import CriticAgent

class AgentOrchestrator:
    """
    Multi-Agent Compiler Orchestrator.
    Runs the 5-agent pipeline (Spec Agent -> State Agent -> Scenario Agent -> Critic Agent)
    using user-selected LLM provider, custom model name, and API key.
    """
    def __init__(
        self, 
        db: Session,
        provider: str = "auto",
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.db = db
        self.llm_factory = LLMProviderFactory(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            base_url=base_url
        )
        self.spec_agent = SpecIntelligenceAgent(llm_factory=self.llm_factory)
        self.state_agent = StateMachineAgent()
        self.scenario_agent = ScenarioAgent()
        self.critic_agent = CriticAgent()

    def run_pipeline(self, project_id: str) -> MultiAgentAnalysisOutput:
        # 1. Fetch active OpenAPI spec
        spec = self.db.query(APISpec).filter(APISpec.project_id == project_id).order_by(APISpec.created_at.desc()).first()
        if not spec:
            raise ValueError(f"No OpenAPI spec found for project '{project_id}'")

        normalized_spec = spec.normalized_spec

        # 2. Run Spec Intelligence Agent
        erd_graph: ERDGraphOutput = self.spec_agent.analyze(normalized_spec)
        self._record_run(project_id, "spec_agent", normalized_spec, erd_graph.model_dump())

        # 3. Run State Machine Agent for discovered entities
        state_machines: List[StateMachineOutput] = []
        for entity in erd_graph.entities:
            sm_output = self.state_agent.analyze(normalized_spec, entity)
            state_machines.append(sm_output)
            self._record_run(project_id, f"state_agent_{entity}", {"entity": entity}, sm_output.model_dump())

        # 4. Run Scenario Agent
        scenarios = self.scenario_agent.generate_scenarios(normalized_spec, erd_graph)

        # 5. Run Critic / Evaluator Agent
        is_valid, validation_issues = self.critic_agent.validate_scenarios(normalized_spec, scenarios)
        self._record_run(
            project_id, 
            "critic_agent", 
            {"scenarios_count": len(scenarios)}, 
            {"is_valid": is_valid, "issues": validation_issues}
        )

        # 6. Save generated scenarios to database
        for sc in scenarios:
            gen_sc = GeneratedScenario(
                project_id=project_id,
                title=sc.title,
                description=sc.description,
                scenario_type=sc.scenario_type,
                steps=[s.model_dump() for s in sc.steps]
            )
            self.db.add(gen_sc)
        self.db.commit()

        return MultiAgentAnalysisOutput(
            project_id=project_id,
            erd_graph=erd_graph,
            state_machines=state_machines,
            test_scenarios=scenarios
        )

    def _record_run(self, project_id: str, agent_name: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        run = AgentRun(
            project_id=project_id,
            agent_name=agent_name,
            status="COMPLETED",
            input_data=input_data,
            output_data=output_data
        )
        self.db.add(run)
        self.db.commit()
