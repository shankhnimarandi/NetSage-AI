import os
import sys
import pytest

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

@pytest.fixture
def client():
    """Configures and returns a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_index_route_get(client):
    """Test that the home page loads successfully via GET request."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"NetSage" in response.data or b"Diagnosis" in response.data

def test_analytics_route_get(client):
    """Test that the analytics dashboard loads successfully via GET request."""
    response = client.get("/analytics")
    assert response.status_code == 200