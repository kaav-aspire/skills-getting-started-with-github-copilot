"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture
def setup_activities(client):
    """Reset activities to initial state before each test"""
    # The app starts with initial activities, so this just ensures a fresh state
    yield
    # No cleanup needed as app recreates activities on each test run


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Tennis Club" in data
        assert "Debate Club" in data
        
    def test_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_for_activity(self, client):
        """Test signing up a student for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        
    def test_signup_verification(self, client):
        """Test that signup actually adds the participant"""
        email = "testuser@mergington.edu"
        client.post(f"/activities/Tennis Club/signup?email={email}")
        
        activities = client.get("/activities").json()
        assert email in activities["Tennis Club"]["participants"]
        
    def test_signup_duplicate_activity(self, client):
        """Test that a student cannot sign up for multiple activities"""
        email = "student@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Basketball Team/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Tennis Club/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post("/activities/Nonexistent Club/signup?email=test@mergington.edu")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_participant(self, client):
        """Test unregistering a participant from an activity"""
        # First, sign up
        email = "unregister_test@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
    def test_unregister_verification(self, client):
        """Test that unregister actually removes the participant"""
        email = "verify_unregister@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Robotics Club/signup?email={email}")
        
        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities["Robotics Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Robotics Club/unregister?email={email}")
        
        # Verify removal
        activities = client.get("/activities").json()
        assert email not in activities["Robotics Club"]["participants"]
        
    def test_unregister_nonexistent_participant(self, client):
        """Test unregistering a participant who is not in the activity"""
        response = client.delete(
            "/activities/Drama Club/unregister?email=notinactivity@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
        
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestInitialData:
    """Tests for the initial activity data"""

    def test_initial_participants_count(self, client):
        """Test that initial participants are set correctly"""
        activities = client.get("/activities").json()
        
        assert "james@mergington.edu" in activities["Basketball Team"]["participants"]
        assert "sarah@mergington.edu" in activities["Tennis Club"]["participants"]
        assert len(activities["Debate Club"]["participants"]) == 2
        
    def test_max_participants(self, client):
        """Test that max_participants are set correctly"""
        activities = client.get("/activities").json()
        
        assert activities["Basketball Team"]["max_participants"] == 15
        assert activities["Tennis Club"]["max_participants"] == 10
        assert activities["Debate Club"]["max_participants"] == 25


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
