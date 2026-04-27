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


def test_callback_stores_token_and_redirects(client, monkeypatch):
    monkeypatch.setattr("app.spotify.exchange_code", lambda code, redirect_uri: "my_token")
    resp = client.get("/callback", params={"code": "authcode"}, follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/"
    resp2 = client.get("/")
    assert 'action="/playlist"' in resp2.text


def test_callback_with_error_param_redirects_home(client):
    resp = client.get("/callback", params={"error": "access_denied"}, follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/"


def test_callback_clears_session_on_exchange_failure(client, monkeypatch):
    def bad_exchange(code, redirect_uri):
        raise Exception("token exchange failed")

    monkeypatch.setattr("app.spotify.exchange_code", bad_exchange)
    client.get("/callback", params={"code": "bad_code"}, follow_redirects=False)
    resp = client.get("/")
    assert "Login with Spotify" in resp.text
