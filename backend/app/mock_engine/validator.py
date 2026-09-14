from typing import Dict, Any, Tuple, Optional
from jsonschema import validate, ValidationError

class PayloadValidator:
    @staticmethod
    def validate_payload(payload: Dict[str, Any], schema: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
        """
        Validates request JSON payload against an OpenAPI JSON Schema.
        Returns (is_valid, error_message).
        """
        if not schema or not isinstance(schema, dict):
            return True, None # No schema defined, allow request

        try:
            validate(instance=payload, schema=schema)
            return True, None
        except ValidationError as ve:
            return False, f"Schema validation error: {ve.message} (path: {'/'.join(str(p) for p in ve.path)})"
        except Exception as e:
            return True, None # Fallback for non-standard schema constructs
