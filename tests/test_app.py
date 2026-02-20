"""
Unit tests for the High School Management System API using the AAA pattern
(Arrange-Act-Assert)
"""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Fixture: Create a TestClient for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture: Reset activities to initial state before and after each test"""
    # Store original state
    original_activities = copy.deepcopy(activities)
    
    yield  # Test runs here
    
    # Restore original state
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all(self, client, reset_activities):
        """Test that GET /activities returns all 9 activities"""
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Debate Team" in data
    
    def test_get_activities_includes_required_fields(self, client, reset_activities):
        """Test that activities have all required fields"""
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(set(activity_data.keys()))
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
    
    def test_get_activities_participant_structure(self, client, reset_activities):
        """Test that participants are stored as expected"""
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        chess_club = data.get("Chess Club")
        assert chess_club is not None
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Chess Club"
        new_email = "test_student@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert new_email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test signup fails for student already signed up"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_invalid_activity(self, client, reset_activities):
        """Test signup fails for non-existent activity"""
        # Arrange
        activity_name = "Non-Existent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test same student can signup for multiple activities"""
        # Arrange
        email = "multi_student@mergington.edu"
        
        # Act
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestDeleteParticipant:
    """Tests for POST /activities/{activity_name}/delete-participant endpoint"""
    
    def test_delete_participant_success(self, client, reset_activities):
        """Test successful removal of a participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/delete-participant",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_delete_nonexistent_participant(self, client, reset_activities):
        """Test deletion fails for student not in activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/delete-participant",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_delete_invalid_activity(self, client, reset_activities):
        """Test deletion fails for non-existent activity"""
        # Arrange
        activity_name = "Non-Existent Activity"
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/delete-participant",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_delete_then_signup_same_student(self, client, reset_activities):
        """Test student can signup after being removed"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - Delete
        delete_response = client.post(
            f"/activities/{activity_name}/delete-participant",
            params={"email": email}
        )
        
        # Act - Signup again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert delete_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
