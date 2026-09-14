import re
import json
from typing import Dict, Any, Optional, List, Tuple
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import APISpec, Project
from app.mock_engine.state_engine import StateEngine
from app.mock_engine.validator import PayloadValidator
from app.mock_engine.data_generator import SyntheticDataGenerator
from app.chaos.middleware import ChaosEngine

router = APIRouter()

def match_route(normalized_routes: List[Dict[str, Any]], request_path: str, http_method: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, str]]:
    """
    Matches an incoming request path & method against normalized OpenAPI routes.
    Extracts dynamic path parameters (e.g. /users/{id} -> {'id': 'usr_123'}).
    """
    clean_path = "/" + request_path.strip("/")
    if clean_path == "/":
        clean_path = ""

    for route in normalized_routes:
        if route["method"].upper() != http_method.upper():
            continue

        route_path = route["path"]
        # Convert OpenAPI path template (e.g. /users/{id}) to Regex (e.g. ^/users/(?P<id>[^/]+)$)
        pattern_str = "^" + re.sub(r'\{([^}]+)\}', r'(?P<\1>[^/]+)', route_path) + "$"
        match = re.match(pattern_str, clean_path)

        if match:
            path_params = match.groupdict()
            return route, path_params

    return None, {}

@router.api_route("/mock/{project_id}/{subpath:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def handle_mock_request(project_id: str, subpath: str, request: Request, db: Session = Depends(get_db)):
    """
    Dynamic Wildcard Catch-All Mock Router.
    Evaluates incoming request URL against project's OpenAPI spec in real-time
    without requiring server restarts or dynamic route re-registration.
    """
    http_method = request.method.upper()

    if http_method == "OPTIONS":
        return Response(status_code=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        })

    # Evaluate Chaos Injection Rules
    clean_subpath = "/" + subpath.strip("/")
    should_interrupt, chaos_response = await ChaosEngine.evaluate_chaos(db, project_id, clean_subpath, http_method)
    if should_interrupt and chaos_response:
        return chaos_response

    # 1. Fetch active API spec for project
    api_spec = db.query(APISpec).filter(APISpec.project_id == project_id).order_by(APISpec.created_at.desc()).first()
    if not api_spec:
        raise HTTPException(status_code=404, detail=f"No active OpenAPI spec found for project '{project_id}'")

    normalized_spec = api_spec.normalized_spec or {}
    routes = normalized_spec.get("routes", [])

    # 2. Match request path against spec routes
    matched_route, path_params = match_route(routes, clean_subpath, http_method)

    if not matched_route:
        # Fallback for unmapped dynamic endpoints: allow basic state operations
        entity_type = clean_subpath.strip("/").split("/")[0] or "default"
        matched_route = {
            "path": clean_subpath,
            "method": http_method,
            "entity_type": entity_type,
            "request_body_schema": None,
            "parameters": []
        }

    # 3. Extract and auto-complete JSON payload with Synthetic Mock Data
    payload = {}
    if http_method in ["POST", "PUT", "PATCH"]:
        try:
            body_bytes = await request.body()
            if body_bytes:
                payload = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            payload = {}

        # Auto-fill missing required schema properties using SyntheticDataGenerator
        req_schema = matched_route.get("request_body_schema")
        if req_schema and isinstance(req_schema, dict):
            synthetic_defaults = SyntheticDataGenerator.generate_payload(req_schema)
            # Merge: user-provided values override synthetic defaults
            for k, v in synthetic_defaults.items():
                if k not in payload or payload[k] is None or payload[k] == "":
                    payload[k] = v

        # Automatic Security Context & User ID Resolution:
        # Extract user identity from Authorization Bearer header or X-User-Id header
        auth_header = request.headers.get("Authorization", "")
        x_user_header = request.headers.get("X-User-Id", "")
        extracted_user_id = None

        if auth_header and auth_header.startswith("Bearer "):
            extracted_user_id = auth_header.split("Bearer ")[1].strip()
        elif x_user_header:
            extracted_user_id = x_user_header.strip()

        # If user_id field is present in payload or schema, auto-bind to active identity
        schema_props = req_schema.get("properties", {}) if (req_schema and isinstance(req_schema, dict)) else {}
        if "user_id" in payload or "user_id" in schema_props:
            current_val = str(payload.get("user_id", ""))
            if not current_val or current_val in ["user_1", "usr_demo_1", "PASTE_USER_ID"]:
                if extracted_user_id:
                    payload["user_id"] = extracted_user_id
                else:
                    # Query active DB state for the most recently registered user
                    recent_user = db.query(MockRecord).filter(
                        MockRecord.project_id == project_id,
                        MockRecord.entity_type == "users"
                    ).order_by(MockRecord.created_at.desc()).first()
                    if recent_user:
                        payload["user_id"] = recent_user.entity_id

    # 4. Validate Payload against Schema if applicable
    req_schema = matched_route.get("request_body_schema")
    if req_schema and http_method in ["POST", "PUT", "PATCH"]:
        is_valid, validation_errors = PayloadValidator.validate_payload(payload, req_schema)
        if not is_valid:
            return Response(
                content=json.dumps({
                    "error": "Bad Request",
                    "detail": f"Schema validation error: {validation_errors}"
                }),
                status_code=400,
                media_type="application/json"
            )

    # 5. Delegate to State Engine
    state_engine = StateEngine(db, project_id)
    entity_type = matched_route.get("entity_type", "default")
    query_params = dict(request.query_params)
    resp_schema = matched_route.get("response_schema")

    # State Dispatcher
    if http_method == "POST":
        # Synthesize OpenAPI compliant response object (assistant answers, vector arrays, execution status)
        response_payload = SyntheticDataGenerator.generate_response_payload(resp_schema, payload, entity_type)

        created, err_msg = state_engine.create_record(entity_type, response_payload, validate_fk=True)
        if err_msg:
            return Response(
                content=json.dumps({"error": "Unprocessable Entity", "detail": err_msg}),
                status_code=422,
                media_type="application/json"
            )
        status_code = 200 if (resp_schema or "chat.completion" in str(response_payload)) else 201
        return Response(content=json.dumps(created), status_code=status_code, media_type="application/json")

    elif http_method == "GET":
        path_segments = [s for s in clean_subpath.strip("/").split("/") if s]

        # 1) Nested parent-child path e.g. /users/usr_123/orders (path_segments: ['users', 'usr_123', 'orders'])
        if len(path_segments) >= 3 and path_params:
            parent_type = path_segments[0].lower()
            parent_id = list(path_params.values())[0]
            records = state_engine.list_records(entity_type, query_params, parent_filter=(parent_type, parent_id))
            return Response(content=json.dumps(records), status_code=200, media_type="application/json")

        # 2) Single record GET by ID e.g. /users/usr_123 (path_segments: ['users', 'usr_123'])
        elif len(path_segments) == 2 and path_params:
            entity_id = list(path_params.values())[0]
            record = state_engine.get_record_by_id(entity_type, entity_id)
            if not record:
                return Response(
                    content=json.dumps({"error": f"Entity '{entity_type}' with ID '{entity_id}' not found"}),
                    status_code=404,
                    media_type="application/json"
                )
            return Response(content=json.dumps(record), status_code=200, media_type="application/json")

        # 3) Collection GET e.g. /users (path_segments: ['users'])
        else:
            records = state_engine.list_records(entity_type, query_params)
            return Response(content=json.dumps(records), status_code=200, media_type="application/json")

    elif http_method == "PUT":
        entity_id = list(path_params.values())[-1] if path_params else state_engine.extract_entity_id(payload, entity_type)
        updated, created = state_engine.put_record(entity_type, entity_id, payload)
        status_code = 201 if created else 200
        return Response(content=json.dumps(updated), status_code=status_code, media_type="application/json")

    elif http_method == "PATCH":
        entity_id = list(path_params.values())[-1] if path_params else state_engine.extract_entity_id(payload, entity_type)
        patched = state_engine.patch_record(entity_type, entity_id, payload)
        if not patched:
            return Response(
                content=json.dumps({"error": f"Entity '{entity_type}' with ID '{entity_id}' not found"}),
                status_code=404,
                media_type="application/json"
            )
        return Response(content=json.dumps(patched), status_code=200, media_type="application/json")

    elif http_method == "DELETE":
        entity_id = list(path_params.values())[-1] if path_params else "default"
        deleted = state_engine.delete_record(entity_type, entity_id)
        if not deleted:
            return Response(
                content=json.dumps({"error": f"Entity '{entity_type}' with ID '{entity_id}' not found"}),
                status_code=404,
                media_type="application/json"
            )
        return Response(content=json.dumps({"message": f"Entity '{entity_id}' deleted successfully"}), status_code=200, media_type="application/json")

    return Response(content=json.dumps({"message": "OK"}), status_code=200, media_type="application/json")
