import pytest


def test_home_logged_out_shows_login_button(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Login with Spotify" in resp.text


def test_home_logged_in_shows_playlist_form(authed_client):
    resp = authed_client.get("/")
    assert resp.status_code == 200
    assert 'action="/playlist"' in resp.text


def test_login_redirects_to_spotify(client, monkeypatch):
    monkeypatch.setattr(
        "app.spotify.get_auth_url",
        lambda redirect_uri: "https://accounts.spotify.com/authorize?test=1",
    )
    resp = client.get("/login", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "accounts.spotify.com" in resp.headers["location"]
