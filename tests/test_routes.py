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


from app import spotify as _spotify

MOCK_TRACKS = [
    {
        "track_number": 6,
        "name": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "duration": "3:20",
    }
]


def test_playlist_renders_track_table(authed_client, monkeypatch):
    monkeypatch.setattr("app.spotify.parse_playlist_id", lambda url: "playlist123")
    monkeypatch.setattr(
        "app.spotify.get_playlist_tracks",
        lambda token, playlist_id: ("Today's Top Hits", MOCK_TRACKS),
    )
    resp = authed_client.post(
        "/playlist",
        data={"playlist_url": "https://open.spotify.com/playlist/playlist123"},
    )
    assert resp.status_code == 200
    assert "Blinding Lights" in resp.text
    assert "The Weeknd" in resp.text
    assert "After Hours" in resp.text


def test_playlist_redirects_if_not_logged_in(client):
    resp = client.post(
        "/playlist",
        data={"playlist_url": "https://open.spotify.com/playlist/abc"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)


def test_playlist_shows_error_on_invalid_url(authed_client, monkeypatch):
    def bad_parse(url):
        raise ValueError("Invalid Spotify playlist URL")

    monkeypatch.setattr("app.spotify.parse_playlist_id", bad_parse)
    resp = authed_client.post(
        "/playlist", data={"playlist_url": "https://example.com/not-spotify"}
    )
    assert resp.status_code == 200
    assert "Invalid Spotify playlist URL" in resp.text


def test_playlist_clears_session_on_auth_error(authed_client, monkeypatch):
    monkeypatch.setattr("app.spotify.parse_playlist_id", lambda url: "abc")

    def expired(token, playlist_id):
        raise _spotify.SpotifyAuthError("expired")

    monkeypatch.setattr("app.spotify.get_playlist_tracks", expired)
    resp = authed_client.post(
        "/playlist",
        data={"playlist_url": "https://open.spotify.com/playlist/abc"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303, 307)


def _load_playlist(authed_client, monkeypatch):
    monkeypatch.setattr("app.spotify.parse_playlist_id", lambda url: "abc123")
    monkeypatch.setattr(
        "app.spotify.get_playlist_tracks",
        lambda token, playlist_id: ("My Jams", MOCK_TRACKS),
    )
    authed_client.post(
        "/playlist", data={"playlist_url": "https://open.spotify.com/playlist/abc123"}
    )


def test_export_returns_csv(authed_client, monkeypatch):
    _load_playlist(authed_client, monkeypatch)
    monkeypatch.setattr(
        "app.spotify.get_playlist_tracks",
        lambda token, playlist_id: ("My Jams", MOCK_TRACKS),
    )
    resp = authed_client.get("/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "Track Number,Track Name,Artist,Album,Track Length" in resp.text
    assert "Blinding Lights" in resp.text
    assert "6" in resp.text


def test_export_filename_uses_playlist_name(authed_client, monkeypatch):
    _load_playlist(authed_client, monkeypatch)
    monkeypatch.setattr(
        "app.spotify.get_playlist_tracks",
        lambda token, playlist_id: ("My Jams", MOCK_TRACKS),
    )
    resp = authed_client.get("/export")
    assert "my-jams.csv" in resp.headers.get("content-disposition", "")


def test_export_redirects_if_no_session(client):
    resp = client.get("/export", follow_redirects=False)
    assert resp.status_code in (302, 307)
