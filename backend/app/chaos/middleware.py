import random
import asyncio
import json
from typing import Optional, Dict, Any, Tuple
from fastapi import Response
from sqlalchemy.orm import Session
from app.models.mock_state import ChaosRule

class ChaosEngine:
    @staticmethod
    async def evaluate_chaos(
        db: Session, 
        project_id: str, 
        request_path: str, 
        http_method: str
    ) -> Tuple[bool, Optional[Response]]:
        """
        Evaluates active chaos rules for a given project and endpoint.
        Returns (was_interrupted_with_response, optional_chaos_response).
        """
        clean_path = "/" + request_path.strip("/")
        
        # Query active rules for this project
        rules = db.query(ChaosRule).filter(
            ChaosRule.project_id == project_id,
            ChaosRule.is_active == True
        ).all()

        for rule in rules:
            # Match endpoint path (exact or path prefix e.g. /payments)
            rule_path = "/" + rule.endpoint_path.strip("/")
            if not clean_path.startswith(rule_path) and clean_path != rule_path:
                continue

            # Match HTTP method ('*' matches all methods)
            if rule.http_method != "*" and rule.http_method.upper() != http_method.upper():
                continue

            # Roll probability check (e.g., probability = 0.50 means 50% chance)
            prob = float(rule.probability) if isinstance(rule.probability, (int, float, str)) else 1.0
            if random.random() > prob:
                continue

            # Failure Type Dispatcher
            failure_type = rule.failure_type.lower()
            config = rule.config if isinstance(rule.config, dict) else {}

            if failure_type == "latency":
                delay_ms = config.get("duration_ms", 500)
                await asyncio.sleep(delay_ms / 1000.0)
                return False, None # Continue request execution after latency delay

            elif failure_type == "status_code":
                status_code = config.get("status_code", 500)
                error_msg = config.get("message", f"Chaos Injected Failure ({status_code})")
                response = Response(
                    content=json.dumps({
                        "error": "Chaos Failure Injected",
                        "status_code": status_code,
                        "detail": error_msg,
                        "chaos_rule_id": rule.id
                    }),
                    status_code=status_code,
                    media_type="application/json"
                )
                return True, response

            elif failure_type == "malformed":
                corrupted_body = config.get("payload", "{ 'corrupted_json': [unclosed_string... }")
                response = Response(
                    content=corrupted_body,
                    status_code=200,
                    media_type="application/json"
                )
                return True, response

        return False, None
