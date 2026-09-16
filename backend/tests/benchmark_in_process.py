import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def benchmark_in_process():
    # Create project & spec in memory
    proj_resp = client.post("/api/v1/projects/", json={"name": "InProcess Latency Benchmark"})
    project_id = proj_resp.json()["id"]

    spec = """
openapi: 3.0.0
info: { title: Benchmark, version: 1.0.0 }
paths:
  /users:
    post:
      summary: Create User
      responses: { '201': { description: Created } }
    get:
      summary: List Users
      responses: { '200': { description: OK } }
"""
    client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": spec})

    # Benchmark 100 in-process GET /health calls
    health_times = []
    for _ in range(100):
        t0 = time.perf_counter()
        client.get("/health")
        health_times.append((time.perf_counter() - t0) * 1000.0)

    # Benchmark 50 in-process POST /users calls
    post_times = []
    for i in range(50):
        t0 = time.perf_counter()
        client.post(f"/mock/{project_id}/users", json={"name": f"User {i}", "email": f"user{i}@test.com"})
        post_times.append((time.perf_counter() - t0) * 1000.0)

    # Benchmark 100 in-process GET /users calls
    get_times = []
    for _ in range(100):
        t0 = time.perf_counter()
        client.get(f"/mock/{project_id}/users")
        get_times.append((time.perf_counter() - t0) * 1000.0)

    avg_health = sum(health_times) / len(health_times)
    avg_post = sum(post_times) / len(post_times)
    avg_get = sum(get_times) / len(get_times)

    print("================ IN-PROCESS ENGINE LATENCY ================")
    print(f"1. Health Check (ASGI Dispatch):              {avg_health:.2f} ms")
    print(f"2. Mock POST Entity Creation & DB Persist:   {avg_post:.2f} ms")
    print(f"3. Mock GET State Retrieval & DB Lookup:      {avg_get:.2f} ms")
    print("==========================================================")

if __name__ == "__main__":
    benchmark_in_process()
