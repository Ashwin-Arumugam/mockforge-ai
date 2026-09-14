import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SAMPLE_OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: E-Commerce Demo API
  version: 1.0.0
paths:
  /users:
    post:
      summary: Create a user
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [name, email]
              properties:
                name:
                  type: string
                email:
                  type: string
      responses:
        '201':
          description: Created
    get:
      summary: List users
      responses:
        '200':
          description: OK
  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
    delete:
      summary: Delete user by ID
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
      summary: Create an order
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                total:
                  type: number
                status:
                  type: string
      responses:
        '201':
          description: Created
  /orders/{id}:
    get:
      summary: Get order by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
    patch:
      summary: Update order status
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
      responses:
        '200':
          description: OK
"""

def test_full_mock_engine_lifecycle():
    # 1. Health check
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"

    # 2. Create project
    proj_resp = client.post("/api/v1/projects/", json={"name": "E-Commerce Project", "description": "Test E2E"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    # 3. Upload OpenAPI Spec
    spec_resp = client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": SAMPLE_OPENAPI_SPEC})
    assert spec_resp.status_code == 200
    assert spec_resp.json()["title"] == "E-Commerce Demo API"
    assert spec_resp.json()["routes_count"] == 7

    # 4. State Operation: POST /mock/{project_id}/users
    user_payload = {"name": "Alice Smith", "email": "alice@example.com"}
    create_user_resp = client.post(f"/mock/{project_id}/users", json=user_payload)
    assert create_user_resp.status_code == 201
    user_data = create_user_resp.json()
    assert "id" in user_data
    user_id = user_data["id"]
    assert user_data["name"] == "Alice Smith"

    # 5. State Operation: GET /mock/{project_id}/users/{user_id}
    get_user_resp = client.get(f"/mock/{project_id}/users/{user_id}")
    assert get_user_resp.status_code == 200
    assert get_user_resp.json()["id"] == user_id
    assert get_user_resp.json()["email"] == "alice@example.com"

    # 6. State Operation: POST /mock/{project_id}/orders
    order_payload = {"user_id": user_id, "total": 149.50, "status": "CREATED"}
    create_order_resp = client.post(f"/mock/{project_id}/orders", json=order_payload)
    assert create_order_resp.status_code == 201
    order_data = create_order_resp.json()
    assert "id" in order_data
    order_id = order_data["id"]

    # 7. State Operation: PATCH /mock/{project_id}/orders/{order_id} (Partial field update)
    patch_resp = client.patch(f"/mock/{project_id}/orders/{order_id}", json={"status": "PAID"})
    assert patch_resp.status_code == 200
    patched_data = patch_resp.json()
    assert patched_data["status"] == "PAID"
    assert patched_data["total"] == 149.50 # Preserved total!

    # 8. State Operation: DELETE /mock/{project_id}/users/{user_id}
    del_resp = client.delete(f"/mock/{project_id}/users/{user_id}")
    assert del_resp.status_code == 200

    # 9. Verify GET /mock/{project_id}/users/{user_id} returns 404
    get_deleted_resp = client.get(f"/mock/{project_id}/users/{user_id}")
    assert get_deleted_resp.status_code == 404
