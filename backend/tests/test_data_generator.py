import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.mock_engine.data_generator import SyntheticDataGenerator

client = TestClient(app)

CHAT_COMPLETION_SCHEMA = {
    "type": "object",
    "required": ["messages"],
    "properties": {
        "model": {"type": "string", "default": "gpt-4o-mini"},
        "messages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["role", "content"],
                "properties": {
                    "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                    "content": {"type": "string"}
                }
            }
        }
    }
}

def test_synthetic_data_generator():
    # 1. Generate payload from schema
    payload1 = SyntheticDataGenerator.generate_payload(CHAT_COMPLETION_SCHEMA)
    payload2 = SyntheticDataGenerator.generate_payload(CHAT_COMPLETION_SCHEMA)

    # Verify required 'messages' field is populated
    assert "messages" in payload1
    assert isinstance(payload1["messages"], list)
    assert len(payload1["messages"]) > 0
    assert payload1["messages"][0]["role"] in ["system", "user", "assistant"]

    # Verify data uniqueness
    assert payload1["messages"][0]["content"] != payload2["messages"][0]["content"]

def test_auto_fill_missing_fields_in_mock_router():
    # Create project & upload Chat Completion spec
    proj_resp = client.post("/api/v1/projects/", json={"name": "Auto Fill Test Project"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    spec = """
openapi: 3.0.0
info: { title: Auto Fill API, version: 1.0.0 }
paths:
  /v1/chat/completions:
    post:
      summary: Chat Completion
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [messages]
              properties:
                messages:
                  type: array
                  items:
                    type: object
                    required: [role, content]
                    properties:
                      role: { type: string, enum: [system, user, assistant] }
                      content: { type: string }
      responses:
        '200': { description: OK }
"""
    client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": spec})

    # Send empty payload {} to POST /v1/chat/completions -> Expect Auto-Fill to populate 'messages' and return 200/201!
    resp = client.post(f"/mock/{project_id}/v1/chat/completions", json={})
    assert resp.status_code == 200 or resp.status_code == 201
    res_json = resp.json()
    assert "messages" in res_json
