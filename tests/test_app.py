"""Tests for the Flask application."""

import json

from flask.testing import FlaskClient

from app import is_valid_surname


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
    response = client.post("/submit", data={"surname": "Zyskowicz"})
    assert response.status_code == 302  # Redirect
    assert "/results" in response.location

    def test_valid_surnames(self):
        """Test surnames that should be valid based on real data analysis."""
        valid_names = [
            "zyskowicz",  # Most common variation
            "zyskovic",  # Second most common
            "zychkowich",  # Third most common
            "zyzkowiz",  # Common variation
            "syskowicz",  # Starts with 's'
            "sylmowski",  # Starts with 's'
            "tsyskovitz",  # Starts with 't' - real variation
            "tsyskovich",  # Starts with 't' - real variation
            "chyckowic",  # Starts with 'c' - real variation
            "chychovic",  # Starts with 'c' - real variation
            "Zyskowicz",  # Capitalized
            "ZYSKOWICZ",  # All caps
        ]

        for name in valid_names:
            with self.subTest(name=name):
                assert is_valid_surname(name), f"'{name}' should be valid"

    def test_invalid_surnames(self):
        """Test surnames that should be invalid."""
        invalid_names = [
            "",  # Empty string
            "abc",  # Too short
            "test",  # Too short (now filtered out!)
            "cats",  # Too short (now filtered out!)
            "axbcdefghijklmn",  # Too long (16 chars)
            "abcdefg",  # Doesn't start with z/s/t/c
            "kononow",  # Doesn't start with z/s/t/c
            "helsinki",  # Doesn't start with z/s/t/c
            "zyskowicz123",  # Contains numbers
            "zysko-wicz",  # Contains hyphen
            "zysko wicz",  # Contains space
            "zysk@wicz",  # Contains special character
        ]

        for name in invalid_names:
            with self.subTest(name=name):
                assert not is_valid_surname(name), f"'{name}' should be invalid"


def test_submit_guess_validation_invalid_names(client: FlaskClient) -> None:
    """Test that invalid surnames are rejected."""
    invalid_surnames = [
        "123",  # Numbers only
        "Name123",  # Contains numbers
        "Name-Test",  # Contains hyphen
        "Name Test",  # Contains space
        "Name@Test",  # Contains special character
        "",  # Empty string
        " ",  # Just space
        "A",  # Too short
        "X" * 51,  # Too long
        "Korhonen",  # Doesn't start with z/s/t/c
        "Mäkinen",  # Doesn't start with z/s/t/c
        "Helsinki",  # Doesn't start with z/s/t/c
        "Yskowitz",  # Doesn't start with z/s/t/c
        "Yskowski",  # Doesn't start with z/s/t/c
        "Psychology",  # Doesn't start with z/s/t/c
        "Psywlf",  # Doesn't start with z/s/t/c
        "Boysfwik",  # Doesn't start with z/s/t/c
    ]

    for surname in invalid_surnames:
        response = client.post("/submit", data={"surname": surname})
        assert response.status_code == 302  # Should redirect back to index
        assert "/results" not in response.location
