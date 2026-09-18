import re
import yaml
import json
from typing import Dict, Any, List, Optional

class OpenAPIParser:
    def __init__(self, raw_spec: str):
        self.raw_spec = raw_spec
        self.spec_dict = self._parse_to_dict(raw_spec)
        self.resolved_spec = self._resolve_refs(self.spec_dict)

    def _parse_to_dict(self, raw_spec: str) -> Dict[str, Any]:
        """Parses YAML or JSON raw spec content into a dictionary."""
        try:
            return json.loads(raw_spec)
        except Exception:
            try:
                return yaml.safe_load(raw_spec)
            except Exception as e:
                raise ValueError(f"Failed to parse OpenAPI spec as JSON or YAML: {str(e)}")

    def _resolve_refs(self, spec: Any) -> Any:
        """Recursively resolves internal $ref pointers within the spec dictionary."""
        if isinstance(spec, dict):
            if "$ref" in spec and isinstance(spec["$ref"], str):
                ref_path = spec["$ref"]
                if ref_path.startswith("#/"):
                    resolved = self._get_ref_target(self.spec_dict, ref_path[2:].split("/"))
                    # Preserve additional keys if any, merged with resolved schema
                    if isinstance(resolved, dict):
                        merged = resolved.copy()
                        for k, v in spec.items():
                            if k != "$ref":
                                merged[k] = self._resolve_refs(v)
                        return merged
                    return resolved
            return {k: self._resolve_refs(v) for k, v in spec.items()}
        elif isinstance(spec, list):
            return [self._resolve_refs(item) for item in spec]
        return spec

    def _get_ref_target(self, root: Dict[str, Any], path_segments: List[str]) -> Any:
        curr = root
        for seg in path_segments:
            if isinstance(curr, dict) and seg in curr:
                curr = curr[seg]
            else:
                return {} # Fallback if ref target missing
        return curr

    def parse(self) -> Dict[str, Any]:
        return self.normalize()

    def normalize(self) -> Dict[str, Any]:
        """
        Normalizes the OpenAPI spec into a standardized dictionary:
        - info: title, version, description
        - routes: list of normalized route objects
        - entities: discovered schemas/entities
        """
        if not isinstance(self.resolved_spec, dict) or "paths" not in self.resolved_spec:
            raise ValueError(
                "Uploaded file is a Machine Learning configuration file (e.g. YOLOv8 training config), "
                "not an OpenAPI 3.x REST API specification containing 'paths:'. "
                "Please upload a valid REST API specification (YAML/JSON with 'paths:' section)."
            )

        info = self.resolved_spec.get("info", {})
        paths = self.resolved_spec.get("paths", {})
        components = self.resolved_spec.get("components", {})
        schemas = components.get("schemas", {})

        normalized_routes = []
        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            
            # Extract path-level parameters
            path_params = path_item.get("parameters", [])

            for method in ["get", "post", "put", "patch", "delete", "options", "head"]:
                if method in path_item:
                    op = path_item[method]
                    if not isinstance(op, dict):
                        continue

                    # Merge operation and path parameters
                    op_params = path_params + op.get("parameters", [])

                    # Extract request body schema if present
                    req_body_schema = None
                    req_body = op.get("requestBody", {})
                    if isinstance(req_body, dict):
                        content = req_body.get("content", {})
                        if "application/json" in content:
                            req_body_schema = content["application/json"].get("schema")

                    # Extract 2xx response schema
                    resp_schema = None
                    responses = op.get("responses", {})
                    for status_code in ["200", "201", "202", "204", "default"]:
                        if status_code in responses:
                            resp_content = responses[status_code].get("content", {})
                            if "application/json" in resp_content:
                                resp_schema = resp_content["application/json"].get("schema")
                                break

                    # Infer entity type from path e.g. /users/{id} -> 'users'
                    entity_type = self._infer_entity_type(path_str)

                    route_obj = {
                        "path": path_str,
                        "method": method.upper(),
                        "operation_id": op.get("operationId"),
                        "summary": op.get("summary", ""),
                        "parameters": op_params,
                        "request_body_schema": req_body_schema,
                        "response_schema": resp_schema,
                        "entity_type": entity_type
                    }
                    normalized_routes.append(route_obj)

        return {
            "info": {
                "title": info.get("title", "Untitled Spec"),
                "version": info.get("version", "1.0.0"),
                "description": info.get("description", "")
            },
            "routes": normalized_routes,
            "schemas": schemas
        }

    def _infer_entity_type(self, path: str) -> str:
        """Helper to extract primary entity collection name from path (e.g. /users/{id}/orders -> 'orders')"""
        segments = [s for s in path.strip("/").split("/") if s]
        # Filter out parameter variables like {id} or {userId}
        non_param_segments = [s for s in segments if not (s.startswith("{") and s.endswith("}"))]
        if non_param_segments:
            return non_param_segments[-1].lower()
        return "default"
