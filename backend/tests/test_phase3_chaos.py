import time
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

CHAOS_OPENAPI_SPEC = """
openapi: 3.0.0
info:
  title: Chaos Resilience API
  version: 1.0.0
paths:
  /payments:
    post:
      summary: Process Payment
      responses:
        '200':
          description: Payment Processed
  /orders:
    post:
      summary: Create Order
      responses:
        '201':
          description: Order Created
  /checkout:
    post:
      summary: Checkout
      responses:
        '200':
          description: Checkout OK
"""

def test_phase3_chaos_engineering():
    # 1. Create project & upload spec
    proj_resp = client.post("/api/v1/projects/", json={"name": "Chaos Test Project"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    spec_resp = client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": CHAOS_OPENAPI_SPEC})
    assert spec_resp.status_code == 200

    # 2. Add Status Code Chaos Rule: Inject 500 error on /payments
    rule500_resp = client.post(
        f"/api/v1/chaos/{project_id}/rules",
        json={
            "endpoint_path": "/payments",
            "http_method": "POST",
            "failure_type": "status_code",
            "probability": 1.0,
            "config": {"status_code": 500, "message": "Payment Processor Unavailable"}
        }
    )
    assert rule500_resp.status_code == 200
    rule500_id = rule500_resp.json()["id"]

    # 3. Call POST /mock/{project_id}/payments -> Expect 500 Chaos Failure
    payment_resp = client.post(f"/mock/{project_id}/payments", json={"amount": 100})
    assert payment_resp.status_code == 500
    assert payment_resp.json()["error"] == "Chaos Failure Injected"
    assert payment_resp.json()["detail"] == "Payment Processor Unavailable"

    # 4. Add Latency Chaos Rule: Inject 300ms delay on /orders
    rule_delay_resp = client.post(
        f"/api/v1/chaos/{project_id}/rules",
        json={
            "endpoint_path": "/orders",
            "http_method": "POST",
            "failure_type": "latency",
            "probability": 1.0,
            "config": {"duration_ms": 300}
        }
    )
    assert rule_delay_resp.status_code == 200

    start_time = time.time()
    order_resp = client.post(f"/mock/{project_id}/orders", json={"item": "Widget"})
    elapsed_ms = (time.time() - start_time) * 1000.0

    assert order_resp.status_code == 201
    assert elapsed_ms >= 250 # Measured latency delay injected!

    # 5. Add Malformed Body Chaos Rule on /checkout
    rule_malformed_resp = client.post(
        f"/api/v1/chaos/{project_id}/rules",
        json={
            "endpoint_path": "/checkout",
            "http_method": "POST",
            "failure_type": "malformed",
            "probability": 1.0,
            "config": {"payload": "{ 'corrupted_json': [unclosed_string... }"}
        }
    )
    assert rule_malformed_resp.status_code == 200

    checkout_resp = client.post(f"/mock/{project_id}/checkout", json={})
    assert checkout_resp.status_code == 200
    assert "corrupted_json" in checkout_resp.text

    # 6. Delete Chaos Rule 500 and verify normal payment calls resume
    del_rule_resp = client.delete(f"/api/v1/chaos/{project_id}/rules/{rule500_id}")
    assert del_rule_resp.status_code == 200

    normal_payment_resp = client.post(f"/mock/{project_id}/payments", json={"amount": 100})
    assert normal_payment_resp.status_code == 200 or normal_payment_resp.status_code == 201
