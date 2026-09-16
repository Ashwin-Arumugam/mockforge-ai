from typing import Dict, Any, List
from app.models.agent_models import StateMachineOutput, StateTransitionRule

class StateMachineAgent:
    """
    Analyzes entity lifecycle states, status enums, and transition semantics.
    Infers valid state transition graphs and invalid state guards.
    """
    def analyze(self, normalized_spec: Dict[str, Any], entity_type: str) -> StateMachineOutput:
        routes = normalized_spec.get("routes", [])
        schemas = normalized_spec.get("schemas", {})

        allowed_states = []

        # Find status enums in schemas or route properties
        for route in routes:
            if route.get("entity_type") == entity_type:
                req_schema = route.get("request_body_schema")
                if req_schema and isinstance(req_schema, dict):
                    props = req_schema.get("properties", {})
                    if "status" in props and isinstance(props["status"], dict):
                        enums = props["status"].get("enum", [])
                        if enums:
                            allowed_states = [str(e).upper() for e in enums]
                            break

        if not allowed_states:
            # Common domain defaults if enum not explicitly declared
            if entity_type in ["orders", "order"]:
                allowed_states = ["CREATED", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"]
            elif entity_type in ["users", "user"]:
                allowed_states = ["PENDING", "ACTIVE", "SUSPENDED"]
            else:
                allowed_states = ["DRAFT", "ACTIVE", "ARCHIVED"]

        # Build valid forward transitions
        transitions = []
        for i in range(len(allowed_states) - 1):
            if allowed_states[i] != "CANCELLED":
                transitions.append(StateTransitionRule(
                    entity=entity_type,
                    from_state=allowed_states[i],
                    to_state=allowed_states[i+1],
                    is_valid=True,
                    reason="Sequential lifecycle progression"
                ))

        # Build invalid backward transitions (guard rules)
        if "DELIVERED" in allowed_states and "CREATED" in allowed_states:
            transitions.append(StateTransitionRule(
                entity=entity_type,
                from_state="DELIVERED",
                to_state="CREATED",
                is_valid=False,
                reason="Cannot revert delivered entity back to created"
            ))

        if "CANCELLED" in allowed_states and "SHIPPED" in allowed_states:
            transitions.append(StateTransitionRule(
                entity=entity_type,
                from_state="CANCELLED",
                to_state="SHIPPED",
                is_valid=False,
                reason="Cannot ship a cancelled order"
            ))

        return StateMachineOutput(
            entity=entity_type,
            allowed_states=allowed_states,
            transitions=transitions
        )
