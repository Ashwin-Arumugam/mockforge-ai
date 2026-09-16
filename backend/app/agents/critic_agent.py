import re
from typing import Dict, Any, List, Tuple
from app.models.agent_models import ScenarioOutput

class CriticAgent:
    """
    Quality Gatekeeper Agent.
    Cross-validates agent-generated test scenarios against the OpenAPI specification
    to guarantee zero hallucination of paths, methods, or parameters.
    """
    def validate_scenarios(self, normalized_spec: Dict[str, Any], scenarios: List[ScenarioOutput]) -> Tuple[bool, List[str]]:
        routes = normalized_spec.get("routes", [])
        issues = []

        valid_route_tuples = set((r["path"], r["method"].upper()) for r in routes)

        for scenario in scenarios:
            for step in scenario.steps:
                # Check path & method validity
                step_method = step.http_method.upper()
                step_path = step.endpoint_path

                # Match parameterized path e.g. /users/{id}
                matched = False
                for r_path, r_method in valid_route_tuples:
                    if r_method == step_method:
                        pattern = "^" + re.sub(r'\{([^}]+)\}', r'[^/]+', r_path) + "$"
                        if re.match(pattern, step_path) or r_path == step_path:
                            matched = True
                            break

                if not matched:
                    issues.append(
                        f"Hallucination Error in scenario '{scenario.title}' (Step {step.step_number}): "
                        f"Endpoint {step_method} '{step_path}' does not exist in OpenAPI spec."
                    )

        is_valid = len(issues) == 0
        return is_valid, issues
