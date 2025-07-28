"""Tests for the Flask application."""

import json

from flask.testing import FlaskClient


def test_index_route(client: FlaskClient) -> None:
    """Test that the index route returns successfully."""
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint(client: FlaskClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "database" in data


def test_results_route(client: FlaskClient) -> None:
    """Test that the results route returns successfully."""
    response = client.get("/results")
    assert response.status_code == 200


def test_submit_guess_redirect(client: FlaskClient) -> None:
    """Test that submitting a guess redirects properly."""
    response = client.post("/submit", data={"surname": "TestSurname"})
    assert response.status_code == 302  # Redirect
    assert "/results" in response.location
