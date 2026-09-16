import time
import httpx

BASE_URL = "http://127.0.0.1:8000"

def benchmark():
    # 1. Create project & upload spec
    r1 = httpx.post(f"{BASE_URL}/api/v1/projects/", json={"name": "Latency Benchmark"})
    project_id = r1.json()["id"]

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
    httpx.post(f"{BASE_URL}/api/v1/specs/{project_id}/upload", json={"raw_spec": spec})

    # Benchmark GET /health (100 requests)
    times_health = []
    for _ in range(100):
        t0 = time.perf_counter()
        httpx.get(f"{BASE_URL}/health")
        times_health.append((time.perf_counter() - t0) * 1000.0)

    # Benchmark POST /mock/{project_id}/users (50 creates)
    times_post = []
    for i in range(50):
        t0 = time.perf_counter()
        httpx.post(f"{BASE_URL}/mock/{project_id}/users", json={"name": f"User {i}", "email": f"user{i}@test.com"})
        times_post.append((time.perf_counter() - t0) * 1000.0)

    # Benchmark GET /mock/{project_id}/users (100 reads)
    times_get = []
    for _ in range(100):
        t0 = time.perf_counter()
        httpx.get(f"{BASE_URL}/mock/{project_id}/users")
        times_get.append((time.perf_counter() - t0) * 1000.0)

    avg_health = sum(times_health) / len(times_health)
    avg_post = sum(times_post) / len(times_post)
    avg_get = sum(times_get) / len(times_get)

    print("================ LATENCY BENCHMARK RESULTS ================")
    print(f"1. Health Check Endpoint (GET /health):       {avg_health:.2f} ms (Avg)")
    print(f"2. Mock POST Entity Creation (POST /users):   {avg_post:.2f} ms (Avg)")
    print(f"3. Mock GET State Retrieval (GET /users):     {avg_get:.2f} ms (Avg)")
    print("==========================================================")

if __name__ == "__main__":
    benchmark()
