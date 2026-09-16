import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "ecommerce_spec.yaml")

def test_verify_with_real_yaml_file():
    # 1. Read real YAML file from disk
    assert os.path.exists(FIXTURE_PATH)
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        yaml_content = f.read()

    # 2. Create Project
    proj_resp = client.post("/api/v1/projects/", json={"name": "PetStore YAML Verification"})
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    # 3. Upload real YAML file
    spec_resp = client.post(f"/api/v1/specs/{project_id}/upload", json={"raw_spec": yaml_content})
    assert spec_resp.status_code == 200
    assert spec_resp.json()["title"] == "PetStore & E-Commerce Integration API"
    assert spec_resp.json()["version"] == "1.2.0"
    assert spec_resp.json()["routes_count"] == 5

    # 4. Test Auto-Fill Synthetic Data: POST /pets without required 'category' field
    invalid_pet = {"name": "Buddy"} # missing 'category'
    auto_fill_resp = client.post(f"/mock/{project_id}/pets", json=invalid_pet)
    assert auto_fill_resp.status_code == 201
    assert "category" in auto_fill_resp.json()
    assert auto_fill_resp.json()["name"] == "Buddy"

    # 5. Create Valid Pet: POST /pets
    valid_pet = {"name": "Buddy", "category": "Dogs", "status": "available"}
    create_pet_resp = client.post(f"/mock/{project_id}/pets", json=valid_pet)
    assert create_pet_resp.status_code == 201
    pet_data = create_pet_resp.json()
    assert "id" in pet_data
    pet_id = pet_data["id"]
    assert pet_data["name"] == "Buddy"

    # 6. Read Pet: GET /pets/{petId}
    get_pet_resp = client.get(f"/mock/{project_id}/pets/{pet_id}")
    assert get_pet_resp.status_code == 200
    assert get_pet_resp.json()["category"] == "Dogs"

    # 7. Delete Pet: DELETE /pets/{petId}
    del_pet_resp = client.delete(f"/mock/{project_id}/pets/{pet_id}")
    assert del_pet_resp.status_code == 200

    # 8. Verify Absence: GET /pets/{petId} returns 404
    get_absent_resp = client.get(f"/mock/{project_id}/pets/{pet_id}")
    assert get_absent_resp.status_code == 404
