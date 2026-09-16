from typing import Dict, Any, List, Optional
from app.models.agent_models import ERDGraphOutput, EntityRelation
from app.agents.llm_factory import LLMProviderFactory

class SpecIntelligenceAgent:
    """
    Analyzes OpenAPI spec routes, parameter names, and schema properties to infer
    Entity-Relationship Diagrams (ERD) and foreign key linkages.
    Supports both BYOK LLM extraction (Ollama, Gemini, Groq, OpenAI) and deterministic fallback analysis.
    """
    def __init__(self, llm_factory: Optional[LLMProviderFactory] = None):
        self.llm_factory = llm_factory or LLMProviderFactory()

    def analyze(self, normalized_spec: Dict[str, Any]) -> ERDGraphOutput:
        # 1. Try LLM Provider if available
        prompt = f"Analyze this OpenAPI spec and extract all entity names and parent-child relationships:\n{normalized_spec}"
        llm_data = self.llm_factory.generate_structured_output(prompt, ERDGraphOutput)
        if llm_data and "entities" in llm_data:
            try:
                return ERDGraphOutput(**llm_data)
            except Exception:
                pass

        # 2. Deterministic Structural Fallback
        routes = normalized_spec.get("routes", [])
        schemas = normalized_spec.get("schemas", {})

        entities = list(set(r.get("entity_type") for r in routes if r.get("entity_type") != "default"))
        if not entities and schemas:
            entities = [s.lower() for s in schemas.keys()]

        relationships = []
        for route in routes:
            entity_type = route.get("entity_type", "default")
            path = route.get("path", "")
            
            # Check for path parameter parent-child relationships e.g. /users/{userId}/orders
            segments = [s for s in path.strip("/").split("/") if s]
            if len(segments) >= 3:
                parent_candidate = segments[0].lower()
                child_candidate = segments[-1].lower()
                if parent_candidate != child_candidate and (not child_candidate.startswith("{")):
                    rel = EntityRelation(
                        parent_entity=parent_candidate,
                        child_entity=child_candidate,
                        foreign_key=f"{parent_candidate.rstrip('s')}_id",
                        relation_type="one_to_many"
                    )
                    if rel not in relationships:
                        relationships.append(rel)

            # Check schema properties for foreign keys
            req_schema = route.get("request_body_schema")
            if req_schema and isinstance(req_schema, dict):
                props = req_schema.get("properties", {})
                for field_name in props.keys():
                    if (field_name.endswith("_id") or field_name.endswith("Id")) and field_name not in ["id", "_id"]:
                        parent_prefix = field_name[:-3] if field_name.endswith("_id") else field_name[:-2]
                        parent_entity = parent_prefix + "s"
                        if parent_entity != entity_type:
                            rel = EntityRelation(
                                parent_entity=parent_entity,
                                child_entity=entity_type,
                                foreign_key=field_name,
                                relation_type="one_to_many"
                            )
                            if rel not in relationships:
                                relationships.append(rel)

        return ERDGraphOutput(entities=entities, relationships=relationships)
