import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AGENT_OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Multi-Agent E-Commerce API
  version: 1.0.0
paths:
  /users:
    post:
      summary: Register customer
      responses:
        '201':
          description: Created
  /users/{id}:
    get:
      summary: Get customer
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
  /orders:
    post:
      summary: Place order
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                status:
                  type: string
                  enum: [CREATED, PAID, SHIPPED, DELIVERED, CANCELLED]
      responses:
        '201':
          description: Created
  /orders/{id}:
    patch:
      summary: Update order status
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
"""

def test_phase4_multi_agent_compiler():
    # 1. Create project & upload spec
    proj_resp = client.post("/api/v1/projects/", json={"name": "Multi-Agent Project"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    spec_resp = client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": AGENT_OPENAPI_SPEC})
    assert spec_resp.status_code == 200

    # 2. Trigger Multi-Agent Pipeline Analysis
    analyze_resp = client.post(f"/api/v1/agents/{project_id}/analyze")
    assert analyze_resp.status_code == 200
    analysis = analyze_resp.json()

    assert analysis["status"] == "COMPLETED"
    assert "users" in analysis["erd_entities"] and "orders" in analysis["erd_entities"]
    assert analysis["scenarios_generated"] >= 1

    # 3. Fetch Generated Scenarios from DB via GET /api/v1/agents/{project_id}/scenarios
    scenarios_resp = client.get(f"/api/v1/agents/{project_id}/scenarios")
    assert scenarios_resp.status_code == 200
    scenarios = scenarios_resp.json()
    assert len(scenarios) >= 1
    titles = [s["title"] for s in scenarios]
    assert "End-to-End Customer Purchase Journey" in titles

    # 4. Fetch Agent Execution Runs via GET /api/v1/agents/{project_id}/runs
    runs_resp = client.get(f"/api/v1/agents/{project_id}/runs")
    assert runs_resp.status_code == 200
    runs = runs_resp.json()
    agent_names = [r["agent_name"] for r in runs]
    assert "spec_agent" in agent_names
    assert "critic_agent" in agent_names
