from typing import Dict, Any, List
from app.models.agent_models import ScenarioOutput, ScenarioStep, ERDGraphOutput

class ScenarioAgent:
    """
    Synthesizes multi-step user journey integration test scripts (Happy Path & Negative Flows)
    based on OpenAPI spec endpoints and ERD relationships.
    """
    def generate_scenarios(self, normalized_spec: Dict[str, Any], erd_graph: ERDGraphOutput) -> List[ScenarioOutput]:
        routes = normalized_spec.get("routes", [])
        scenarios = []

        # Find key CRUD endpoints
        post_user_route = next((r for r in routes if r["method"] == "POST" and r["entity_type"] == "users"), None)
        get_user_route = next((r for r in routes if r["method"] == "GET" and r["entity_type"] == "users" and "{" in r["path"]), None)
        post_order_route = next((r for r in routes if r["method"] == "POST" and r["entity_type"] == "orders"), None)
        patch_order_route = next((r for r in routes if r["method"] == "PATCH" and r["entity_type"] == "orders"), None)

        if post_user_route or post_order_route:
            steps = []
            step_count = 1

            if post_user_route:
                steps.append(ScenarioStep(
                    step_number=step_count,
                    name="Register Customer User",
                    endpoint_path=post_user_route["path"],
                    http_method="POST",
                    payload_template={"name": "Test Customer", "email": "test@example.com"},
                    expected_status_code=201
                ))
                step_count += 1

            if get_user_route:
                steps.append(ScenarioStep(
                    step_number=step_count,
                    name="Fetch Created Customer",
                    endpoint_path=get_user_route["path"],
                    http_method="GET",
                    payload_template={},
                    expected_status_code=200
                ))
                step_count += 1

            if post_order_route:
                steps.append(ScenarioStep(
                    step_number=step_count,
                    name="Create Customer Order",
                    endpoint_path=post_order_route["path"],
                    http_method="POST",
                    payload_template={"user_id": "{user_id}", "total": 99.99, "status": "CREATED"},
                    expected_status_code=201
                ))
                step_count += 1

            if patch_order_route:
                steps.append(ScenarioStep(
                    step_number=step_count,
                    name="Update Order Status to PAID",
                    endpoint_path=patch_order_route["path"],
                    http_method="PATCH",
                    payload_template={"status": "PAID"},
                    expected_status_code=200
                ))

            if steps:
                scenarios.append(ScenarioOutput(
                    title="End-to-End Customer Purchase Journey",
                    description="Automated multi-step flow creating user, placing order, and verifying state transitions",
                    scenario_type="HAPPY_PATH",
                    steps=steps
                ))

        # Negative scenario: Invalid Foreign Key Order
        if post_order_route:
            scenarios.append(ScenarioOutput(
                title="Orphan Order Rejection Journey",
                description="Verifies system rejects orders with non-existent foreign keys",
                scenario_type="NEGATIVE_PATH",
                steps=[
                    ScenarioStep(
                        step_number=1,
                        name="Attempt Order for Missing User",
                        endpoint_path=post_order_route["path"],
                        http_method="POST",
                        payload_template={"user_id": "non_existent_usr_999", "total": 49.99},
                        expected_status_code=422
                    )
                ]
            ))

        return scenarios
