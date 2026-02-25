"""
Tests for the Mergington High School extracurricular activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ──────────────────────────────────────────────
# GET /activities
# ──────────────────────────────────────────────

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9


def test_get_activities_each_has_required_keys():
    response = client.get("/activities")
    for name, details in response.json().items():
        assert "description" in details, f"{name} missing 'description'"
        assert "schedule" in details, f"{name} missing 'schedule'"
        assert "max_participants" in details, f"{name} missing 'max_participants'"
        assert "participants" in details, f"{name} missing 'participants'"


# ──────────────────────────────────────────────
# POST /activities/{activity_name}/signup
# ──────────────────────────────────────────────

def test_signup_success():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "newstudent@mergington.edu"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Signed up newstudent@mergington.edu for Chess Club"}


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_duplicate_returns_400():
    email = "duplicate@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "ghost@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


# ──────────────────────────────────────────────
# DELETE /activities/{activity_name}/signup
# ──────────────────────────────────────────────

def test_unregister_success():
    # Use a participant that is pre-seeded in Chess Club
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "michael@mergington.edu"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered michael@mergington.edu from Chess Club"}


def test_unregister_removes_participant():
    email = "michael@mergington.edu"
    client.delete("/activities/Chess Club/signup", params={"email": email})
    response = client.get("/activities")
    participants = response.json()["Chess Club"]["participants"]
    assert email not in participants


def test_unregister_non_participant_returns_404():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "nobody@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "ghost@mergington.edu"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
