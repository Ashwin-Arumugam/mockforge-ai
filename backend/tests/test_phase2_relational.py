import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

RELATIONAL_OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Relational E-Commerce API
  version: 1.0.0
paths:
  /users:
    post:
      summary: Create user
      responses:
        '201':
          description: Created
  /users/{id}:
    get:
      summary: Get user
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
      summary: Delete user
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
  /users/{userId}/orders:
    get:
      summary: Get orders belonging to user
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
  /orders:
    post:
      summary: Create order
      responses:
        '201':
          description: Created
    get:
      summary: List all orders
      responses:
        '200':
          description: OK
"""

def test_phase2_relational_engine():
    # 1. Create project & Upload relational spec
    proj_resp = client.post("/api/v1/projects/", json={"name": "Relational Project"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    spec_resp = client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": RELATIONAL_OPENAPI_SPEC})
    assert spec_resp.status_code == 200

    # 2. Try creating an Order referencing a NON-EXISTENT user_id -> Expect 422 Unprocessable Entity
    invalid_order_resp = client.post(f"/mock/{project_id}/orders", json={"user_id": "non_existent_user_99", "total": 49.99})
    assert invalid_order_resp.status_code == 422
    assert "Foreign Key Error" in invalid_order_resp.json()["detail"]

    # 3. Create two valid Users: Alice and Bob
    user1_resp = client.post(f"/mock/{project_id}/users", json={"name": "Alice"})
    assert user1_resp.status_code == 201
    user1_id = user1_resp.json()["id"]

    user2_resp = client.post(f"/mock/{project_id}/users", json={"name": "Bob"})
    assert user2_resp.status_code == 201
    user2_id = user2_resp.json()["id"]

    # 4. Create two Orders for Alice and one Order for Bob
    order1_resp = client.post(f"/mock/{project_id}/orders", json={"user_id": user1_id, "item": "Laptop", "total": 1200.00})
    assert order1_resp.status_code == 201

    order2_resp = client.post(f"/mock/{project_id}/orders", json={"user_id": user1_id, "item": "Mouse", "total": 25.00})
    assert order2_resp.status_code == 201

    order3_resp = client.post(f"/mock/{project_id}/orders", json={"user_id": user2_id, "item": "Keyboard", "total": 75.00})
    assert order3_resp.status_code == 201

    # 5. Query nested relational path GET /users/{user1_id}/orders -> Expect 2 orders for Alice
    alice_orders_resp = client.get(f"/mock/{project_id}/users/{user1_id}/orders")
    assert alice_orders_resp.status_code == 200
    alice_orders = alice_orders_resp.json()
    assert len(alice_orders) == 2
    items = [o["item"] for o in alice_orders]
    assert "Laptop" in items and "Mouse" in items

    # 6. Query nested relational path GET /users/{user2_id}/orders -> Expect 1 order for Bob
    bob_orders_resp = client.get(f"/mock/{project_id}/users/{user2_id}/orders")
    assert bob_orders_resp.status_code == 200
    bob_orders = bob_orders_resp.json()
    assert len(bob_orders) == 1
    assert bob_orders[0]["item"] == "Keyboard"

    # 7. Delete user1 (Alice)
    del_user_resp = client.delete(f"/mock/{project_id}/users/{user1_id}")
    assert del_user_resp.status_code == 200

    # 8. Query nested relational path GET /users/{user1_id}/orders after deletion -> Expect 0 orders
    alice_orders_deleted_resp = client.get(f"/mock/{project_id}/users/{user1_id}/orders")
    assert alice_orders_deleted_resp.status_code == 200
    assert len(alice_orders_deleted_resp.json()) == 0
