import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_valid_ticket():
    ticket = "I need assistance resetting my password for the library portal. It keeps saying invalid credentials."
    print(f"Testing classification with text: '{ticket}'")
    response = client.post("/classify/ticket", json={"ticket_text": ticket})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "IT Support"  # Should be normalized to canonical "IT Support"

def test_too_short():
    ticket = "Hi"
    print(f"Testing too short text: '{ticket}'")
    response = client.post("/classify/ticket", json={"ticket_text": ticket})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 422

def test_whitespace_only():
    ticket = "          "
    print(f"Testing whitespace-only text: '{ticket}' (length={len(ticket)})")
    response = client.post("/classify/ticket", json={"ticket_text": ticket})
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # Should be rejected with 422 Unprocessable Entity by the custom Pydantic validator, not 503!
    assert response.status_code == 422
    assert "ticket_text must contain at least 10 non-whitespace characters" in response.json()["detail"][0]["msg"]

if __name__ == "__main__":
    try:
        test_valid_ticket()
        print("-" * 40)
        test_too_short()
        print("-" * 40)
        test_whitespace_only()
        print("\nAll endpoint tests passed successfully!")
    except AssertionError as exc:
        print(f"\n[FAIL] Assertion failed: {exc}")
        sys.exit(1)
