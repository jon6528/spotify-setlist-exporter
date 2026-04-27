import os
import pytest
from fastapi.testclient import TestClient

# Set env vars before importing the app so SessionMiddleware picks them up
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test-client-id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("REDIRECT_URI", "http://localhost:8000/callback")

from app.main import app


@pytest.fixture
def client():
    with TestClient(app, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def authed_client(monkeypatch):
    monkeypatch.setattr("app.spotify.exchange_code", lambda code, redirect_uri: "test_token")
    with TestClient(app, base_url="http://testserver") as c:
        c.get("/callback", params={"code": "testcode"}, follow_redirects=False)
        yield c
