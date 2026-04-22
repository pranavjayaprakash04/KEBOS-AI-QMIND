from fastapi.testclient import TestClient
from job_manager.api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/job_manager")

client = TestClient(app)

def test_schedule_stub():
    response = client.post("/job_manager/schedule", json={"job_type": "test", "payload": {}})
    assert response.status_code == 200
    assert response.json()["status"] == "success"
