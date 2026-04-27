# Spotify Setlist Exporter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Dockerized FastAPI web app that authenticates with Spotify, lets the user paste a playlist URL, previews tracks in a table, and downloads them as a CSV.

**Architecture:** Single FastAPI container with Jinja2 server-rendered HTML. A `spotify.py` module contains all Spotify API logic as pure functions (easily mocked in tests). `SessionMiddleware` stores the access token and last-loaded playlist ID in a signed cookie. No database.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, Jinja2, python-multipart, Requests, Starlette SessionMiddleware (bundled with FastAPI), python-dotenv, pytest, httpx

---

## File Map

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, session middleware, all route handlers |
| `app/spotify.py` | Pure functions: URL parsing, OAuth, playlist fetch |
| `app/templates/base.html` | Shared layout, nav bar, Spotify dark theme |
| `app/templates/home.html` | Login screen (logged out) or playlist input (logged in) |
| `app/templates/playlist.html` | Track table + export button |
| `app/static/style.css` | Spotify dark theme styles |
| `tests/conftest.py` | TestClient fixtures (basic + pre-authed) |
| `tests/test_spotify.py` | Unit tests for all spotify.py functions |
| `tests/test_routes.py` | Integration tests for all routes |
| `Dockerfile` | Python 3.12 slim image |
| `docker-compose.yml` | Service definition, port 8000, env_file |
| `.env.example` | Template for required env vars |
| `requirements.txt` | Python dependencies |
| `README.md` | Setup guide |

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/spotify.py`
- Create: `app/templates/base.html`
- Create: `app/templates/home.html`
- Create: `app/templates/playlist.html`
- Create: `app/static/style.css`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
jinja2==3.1.4
python-multipart==0.0.9
requests==2.32.3
itsdangerous==2.2.0
python-dotenv==1.0.1
pytest==8.3.0
httpx==0.27.0
```

- [ ] **Step 2: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
```

- [ ] **Step 4: Create `.env.example`**

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=replace_with_any_long_random_string
REDIRECT_URI=http://localhost:8000/callback
```

- [ ] **Step 5: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
.superpowers/
```

- [ ] **Step 6: Create `app/__init__.py`** (empty file)

- [ ] **Step 7: Create `app/spotify.py`** (empty file)

- [ ] **Step 8: Create minimal `app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI()
```

- [ ] **Step 9: Create stub templates**

`app/templates/base.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Setlist Exporter</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
{% block content %}{% endblock %}
</body>
</html>
```

`app/templates/home.html`:
```html
{% extends "base.html" %}
{% block content %}home{% endblock %}
```

`app/templates/playlist.html`:
```html
{% extends "base.html" %}
{% block content %}playlist{% endblock %}
```

`app/static/style.css` — create as an empty file.

- [ ] **Step 10: Create `tests/__init__.py`** (empty file)

- [ ] **Step 11: Create `tests/conftest.py`**

```python
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
```

- [ ] **Step 12: Verify the project installs cleanly**

```bash
pip install -r requirements.txt
```

Expected: All packages install with no errors.

- [ ] **Step 13: Verify Docker builds**

```bash
docker build -t setlist-exporter .
```

Expected: Build completes successfully.

- [ ] **Step 14: Commit**

```bash
git add .
git commit -m "feat: project scaffold"
```

---

### Task 2: parse_playlist_id

**Files:**
- Modify: `app/spotify.py`
- Create: `tests/test_spotify.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_spotify.py`:
```python
import pytest
from app.spotify import parse_playlist_id


def test_parse_standard_url():
    assert parse_playlist_id(
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    ) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_url_with_query_params():
    assert parse_playlist_id(
        "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123"
    ) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_invalid_url_raises():
    with pytest.raises(ValueError, match="Invalid Spotify playlist URL"):
        parse_playlist_id("https://open.spotify.com/track/123")


def test_parse_empty_raises():
    with pytest.raises(ValueError, match="Invalid Spotify playlist URL"):
        parse_playlist_id("")
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_spotify.py -v
```

Expected: `ImportError: cannot import name 'parse_playlist_id' from 'app.spotify'`

- [ ] **Step 3: Implement `parse_playlist_id` in `app/spotify.py`**

```python
from urllib.parse import urlparse


def parse_playlist_id(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "playlist":
        return parts[1]
    raise ValueError("Invalid Spotify playlist URL")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_spotify.py -v
```

Expected: 4 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/spotify.py tests/test_spotify.py
git commit -m "feat: add parse_playlist_id"
```

---

### Task 3: get_auth_url

**Files:**
- Modify: `app/spotify.py`
- Modify: `tests/test_spotify.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_spotify.py`:
```python
from urllib.parse import parse_qs, urlparse as _urlparse


def test_get_auth_url_contains_required_params(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "test_cid")
    from app.spotify import get_auth_url
    url = get_auth_url(redirect_uri="http://localhost:8000/callback")
    parsed = _urlparse(url)
    params = parse_qs(parsed.query)
    assert parsed.netloc == "accounts.spotify.com"
    assert params["client_id"] == ["test_cid"]
    assert params["response_type"] == ["code"]
    assert params["redirect_uri"] == ["http://localhost:8000/callback"]
    assert "playlist-read-private" in params["scope"][0]
    assert "playlist-read-collaborative" in params["scope"][0]
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_spotify.py::test_get_auth_url_contains_required_params -v
```

Expected: `ImportError: cannot import name 'get_auth_url'`

- [ ] **Step 3: Implement `get_auth_url` in `app/spotify.py`**

Append to `app/spotify.py`:
```python
import os
from urllib.parse import urlencode

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SCOPES = "playlist-read-private playlist-read-collaborative"


def get_auth_url(redirect_uri: str) -> str:
    params = {
        "client_id": os.environ["SPOTIFY_CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
pytest tests/test_spotify.py -v
```

Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/spotify.py tests/test_spotify.py
git commit -m "feat: add get_auth_url"
```

---

### Task 4: exchange_code

**Files:**
- Modify: `app/spotify.py`
- Modify: `tests/test_spotify.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_spotify.py`:
```python
from unittest.mock import patch, Mock


def test_exchange_code_returns_access_token(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "csecret")
    mock_resp = Mock()
    mock_resp.json.return_value = {"access_token": "tok123"}
    mock_resp.raise_for_status = Mock()
    with patch("app.spotify.requests.post", return_value=mock_resp) as mock_post:
        from app.spotify import exchange_code
        token = exchange_code(code="authcode", redirect_uri="http://localhost:8000/callback")
    assert token == "tok123"
    posted_data = mock_post.call_args[1]["data"]
    assert posted_data["grant_type"] == "authorization_code"
    assert posted_data["code"] == "authcode"


def test_exchange_code_raises_on_http_error(monkeypatch):
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "cid")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "csecret")
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
    with patch("app.spotify.requests.post", return_value=mock_resp):
        from app.spotify import exchange_code
        with pytest.raises(Exception):
            exchange_code(code="bad", redirect_uri="http://localhost:8000/callback")
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_spotify.py::test_exchange_code_returns_access_token tests/test_spotify.py::test_exchange_code_raises_on_http_error -v
```

Expected: `ImportError: cannot import name 'exchange_code'`

- [ ] **Step 3: Implement `exchange_code` in `app/spotify.py`**

Append to `app/spotify.py`:
```python
import base64
import requests

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


def exchange_code(code: str, redirect_uri: str) -> str:
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {credentials}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
pytest tests/test_spotify.py -v
```

Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/spotify.py tests/test_spotify.py
git commit -m "feat: add exchange_code"
```

---

### Task 5: get_playlist_tracks

**Files:**
- Modify: `app/spotify.py`
- Modify: `tests/test_spotify.py`

Returns `(playlist_name: str, tracks: list[dict])`. Each track dict has keys: `track_number`, `name`, `artist`, `album`, `duration`.

The first request goes to `GET /v1/playlists/{id}`, which returns `{"name": ..., "tracks": {"items": [...], "next": ...}}`. Subsequent pages follow the `next` URL and return `{"items": [...], "next": ...}`.

`track_number` is the song's position on its album (Spotify's `track_number` field), not its position in the playlist.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_spotify.py`:
```python
def _make_item(name, artist, album, track_number, duration_ms):
    return {
        "track": {
            "name": name,
            "track_number": track_number,
            "duration_ms": duration_ms,
            "artists": [{"name": artist}],
            "album": {"name": album},
        }
    }


def test_get_playlist_tracks_single_page():
    playlist_data = {
        "name": "My Playlist",
        "tracks": {
            "items": [_make_item("Song A", "Artist A", "Album A", 3, 200000)],
            "next": None,
        },
    }
    mock_resp = Mock(status_code=200)
    mock_resp.json.return_value = playlist_data
    with patch("app.spotify.requests.get", return_value=mock_resp):
        from app.spotify import get_playlist_tracks
        name, tracks = get_playlist_tracks(token="tok", playlist_id="abc")
    assert name == "My Playlist"
    assert tracks == [{
        "track_number": 3,
        "name": "Song A",
        "artist": "Artist A",
        "album": "Album A",
        "duration": "3:20",
    }]


def test_get_playlist_tracks_paginates():
    page1 = {
        "name": "Big Playlist",
        "tracks": {
            "items": [_make_item("Song A", "Artist A", "Album A", 1, 60000)],
            "next": "https://api.spotify.com/v1/playlists/abc/tracks?offset=100",
        },
    }
    page2 = {
        "items": [_make_item("Song B", "Artist B", "Album B", 2, 120000)],
        "next": None,
    }
    mock1 = Mock(status_code=200)
    mock1.json.return_value = page1
    mock2 = Mock(status_code=200)
    mock2.json.return_value = page2
    with patch("app.spotify.requests.get", side_effect=[mock1, mock2]):
        from app.spotify import get_playlist_tracks
        name, tracks = get_playlist_tracks(token="tok", playlist_id="abc")
    assert len(tracks) == 2
    assert tracks[1]["name"] == "Song B"


def test_get_playlist_tracks_raises_auth_error_on_401():
    mock_resp = Mock(status_code=401)
    with patch("app.spotify.requests.get", return_value=mock_resp):
        from app.spotify import get_playlist_tracks, SpotifyAuthError
        with pytest.raises(SpotifyAuthError):
            get_playlist_tracks(token="expired", playlist_id="abc")
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_spotify.py::test_get_playlist_tracks_single_page tests/test_spotify.py::test_get_playlist_tracks_paginates tests/test_spotify.py::test_get_playlist_tracks_raises_auth_error_on_401 -v
```

Expected: `ImportError: cannot import name 'get_playlist_tracks'`

- [ ] **Step 3: Implement `SpotifyAuthError`, `_ms_to_duration`, and `get_playlist_tracks` in `app/spotify.py`**

Append to `app/spotify.py`:
```python
SPOTIFY_API_BASE = "https://api.spotify.com/v1"


class SpotifyAuthError(Exception):
    pass


def _ms_to_duration(ms: int) -> str:
    seconds = ms // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_playlist_tracks(token: str, playlist_id: str) -> tuple[str, list[dict]]:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{SPOTIFY_API_BASE}/playlists/{playlist_id}", headers=headers)
    if response.status_code == 401:
        raise SpotifyAuthError("Spotify token expired or invalid")
    data = response.json()
    playlist_name = data["name"]
    tracks = []
    page = data["tracks"]
    while page:
        for item in page.get("items", []):
            t = item.get("track")
            if not t:
                continue
            tracks.append({
                "track_number": t["track_number"],
                "name": t["name"],
                "artist": t["artists"][0]["name"],
                "album": t["album"]["name"],
                "duration": _ms_to_duration(t["duration_ms"]),
            })
        next_url = page.get("next")
        if next_url:
            response = requests.get(next_url, headers=headers)
            if response.status_code == 401:
                raise SpotifyAuthError("Spotify token expired or invalid")
            page = response.json()
        else:
            page = None
    return playlist_name, tracks
```

- [ ] **Step 4: Run all spotify tests to confirm they pass**

```bash
pytest tests/test_spotify.py -v
```

Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/spotify.py tests/test_spotify.py
git commit -m "feat: add get_playlist_tracks"
```

---

### Task 6: GET / and GET /login routes

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/home.html`
- Create: `tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_routes.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_routes.py -v
```

Expected: Tests fail — routes return 404 or template content doesn't match.

- [ ] **Step 3: Replace `app/main.py` with the full app wiring**

```python
import csv
import io
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app import spotify

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.environ.get("SECRET_KEY", "dev-secret"))
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8000/callback")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    logged_in = bool(request.session.get("access_token"))
    return templates.TemplateResponse("home.html", {"request": request, "logged_in": logged_in})


@app.get("/login")
def login():
    url = spotify.get_auth_url(redirect_uri=REDIRECT_URI)
    return RedirectResponse(url)
```

- [ ] **Step 4: Update `app/templates/home.html`**

```html
{% extends "base.html" %}

{% block nav_extra %}
{% if logged_in %}
<form class="url-form" method="post" action="/playlist">
  <input class="url-input" type="text" name="playlist_url"
    placeholder="https://open.spotify.com/playlist/...">
  <button class="btn btn-sm" type="submit">Load</button>
</form>
{% endif %}
{% endblock %}

{% block content %}
{% if logged_in %}
<div class="hero">
  <h1>Paste a playlist link above</h1>
  <p>Load any Spotify playlist to preview and export its tracks as a CSV.</p>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
</div>
{% else %}
<div class="hero">
  <h1>Export your Spotify playlist</h1>
  <p>Paste any playlist link and download a CSV with all your tracks.</p>
  <a href="/login" class="btn">&#9654; Login with Spotify</a>
</div>
{% endif %}
{% endblock %}
```

- [ ] **Step 5: Update `app/templates/base.html`** to include the `nav_extra` block

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Setlist Exporter</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<nav>
  <span class="logo">&#9679;</span>
  <span class="wordmark">SETLIST EXPORTER</span>
  {% block nav_extra %}{% endblock %}
</nav>
{% block content %}{% endblock %}
</body>
</html>
```

- [ ] **Step 6: Run route tests to confirm they pass**

```bash
pytest tests/test_routes.py -v
```

Expected: 3 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add app/main.py app/templates/base.html app/templates/home.html tests/test_routes.py
git commit -m "feat: add home and login routes"
```

---

### Task 7: GET /callback route

**Files:**
- Modify: `app/main.py`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_routes.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_routes.py::test_callback_stores_token_and_redirects tests/test_routes.py::test_callback_with_error_param_redirects_home tests/test_routes.py::test_callback_clears_session_on_exchange_failure -v
```

Expected: 404 Not Found (route doesn't exist).

- [ ] **Step 3: Add `/callback` route to `app/main.py`**

Append to `app/main.py`:
```python
@app.get("/callback")
def callback(request: Request, code: str = None, error: str = None):
    if error or not code:
        return RedirectResponse("/")
    try:
        token = spotify.exchange_code(code=code, redirect_uri=REDIRECT_URI)
        request.session["access_token"] = token
    except Exception:
        request.session.clear()
    return RedirectResponse("/")
```

- [ ] **Step 4: Run all route tests to confirm they pass**

```bash
pytest tests/test_routes.py -v
```

Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_routes.py
git commit -m "feat: add callback route"
```

---

### Task 8: POST /playlist route

**Files:**
- Modify: `app/main.py`
- Modify: `app/templates/playlist.html`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_routes.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_routes.py::test_playlist_renders_track_table tests/test_routes.py::test_playlist_redirects_if_not_logged_in tests/test_routes.py::test_playlist_shows_error_on_invalid_url tests/test_routes.py::test_playlist_clears_session_on_auth_error -v
```

Expected: 404 Not Found (route doesn't exist).

- [ ] **Step 3: Add `/playlist` route to `app/main.py`**

Append to `app/main.py`:
```python
@app.post("/playlist", response_class=HTMLResponse)
def load_playlist(request: Request, playlist_url: str = Form(...)):
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse("/", status_code=303)
    try:
        playlist_id = spotify.parse_playlist_id(playlist_url)
        playlist_name, tracks = spotify.get_playlist_tracks(token=token, playlist_id=playlist_id)
        request.session["playlist_id"] = playlist_id
        request.session["playlist_name"] = playlist_name
    except spotify.SpotifyAuthError:
        request.session.clear()
        return RedirectResponse("/", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "logged_in": True, "error": str(e)},
        )
    return templates.TemplateResponse(
        "playlist.html",
        {
            "request": request,
            "playlist_name": playlist_name,
            "track_count": len(tracks),
            "tracks": tracks,
        },
    )
```

- [ ] **Step 4: Update `app/templates/playlist.html`**

```html
{% extends "base.html" %}

{% block nav_extra %}
<form class="url-form" method="post" action="/playlist">
  <input class="url-input" type="text" name="playlist_url"
    placeholder="https://open.spotify.com/playlist/...">
  <button class="btn btn-sm" type="submit">Load</button>
</form>
{% endblock %}

{% block content %}
<div class="playlist-header">
  <h2>{{ playlist_name }}</h2>
  <p>{{ track_count }} tracks</p>
</div>
<table class="track-table">
  <thead>
    <tr>
      <th class="track-num">#</th>
      <th>Title</th>
      <th>Artist</th>
      <th>Album</th>
      <th class="track-duration">&#9201;</th>
    </tr>
  </thead>
  <tbody>
  {% for t in tracks %}
  <tr>
    <td class="track-num">{{ t.track_number }}</td>
    <td class="track-name">{{ t.name }}</td>
    <td class="track-artist">{{ t.artist }}</td>
    <td class="track-album">{{ t.album }}</td>
    <td class="track-duration">{{ t.duration }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
<div class="export-bar">
  <a href="/export" class="btn">&#11015; Export CSV</a>
</div>
{% endblock %}
```

- [ ] **Step 5: Run all tests to confirm they pass**

```bash
pytest tests/ -v
```

Expected: All tests PASSED.

- [ ] **Step 6: Commit**

```bash
git add app/main.py app/templates/playlist.html tests/test_routes.py
git commit -m "feat: add playlist route"
```

---

### Task 9: GET /export route

**Files:**
- Modify: `app/main.py`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_routes.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm failure**

```bash
pytest tests/test_routes.py::test_export_returns_csv tests/test_routes.py::test_export_filename_uses_playlist_name tests/test_routes.py::test_export_redirects_if_no_session -v
```

Expected: 404 Not Found (route doesn't exist).

- [ ] **Step 3: Add `/export` route to `app/main.py`**

Append to `app/main.py`:
```python
@app.get("/export")
def export_csv(request: Request):
    token = request.session.get("access_token")
    playlist_id = request.session.get("playlist_id")
    playlist_name = request.session.get("playlist_name", "playlist")
    if not token or not playlist_id:
        return RedirectResponse("/")
    try:
        _, tracks = spotify.get_playlist_tracks(token=token, playlist_id=playlist_id)
    except spotify.SpotifyAuthError:
        request.session.clear()
        return RedirectResponse("/")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Track Number", "Track Name", "Artist", "Album", "Track Length"])
    for t in tracks:
        writer.writerow([t["track_number"], t["name"], t["artist"], t["album"], t["duration"]])
    filename = re.sub(r"[^\w\s-]", "", playlist_name).strip().lower()
    filename = re.sub(r"\s+", "-", filename)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
```

- [ ] **Step 4: Run all tests to confirm they pass**

```bash
pytest tests/ -v
```

Expected: All tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_routes.py
git commit -m "feat: add export route"
```

---

### Task 10: Full Spotify-like templates and CSS

**Files:**
- Modify: `app/static/style.css`
- Modify: `app/templates/base.html` (already finalized in Task 6)
- Modify: `app/templates/home.html` (already finalized in Task 6)
- Modify: `app/templates/playlist.html` (already finalized in Task 8)

No new tests — existing route tests cover template rendering. This task is purely visual.

- [ ] **Step 1: Write `app/static/style.css`**

```css
:root {
  --bg: #121212;
  --surface: #282828;
  --nav: #000000;
  --green: #1DB954;
  --text: #ffffff;
  --muted: #b3b3b3;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

nav {
  background: var(--nav);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #282828;
  position: sticky;
  top: 0;
  z-index: 10;
}

.logo { color: var(--green); font-size: 20px; }
.wordmark { font-weight: 900; letter-spacing: 2px; font-size: 13px; }

.url-form {
  flex: 1;
  display: flex;
  gap: 8px;
  max-width: 500px;
  margin-left: auto;
}

.url-input {
  flex: 1;
  background: var(--surface);
  border: none;
  border-radius: 4px;
  padding: 8px 14px;
  color: var(--text);
  font-size: 13px;
  outline: none;
}

.url-input::placeholder { color: var(--muted); }
.url-input:focus { outline: 1px solid var(--green); }

.btn {
  background: var(--green);
  color: #000;
  border: none;
  border-radius: 24px;
  padding: 10px 24px;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.btn:hover { background: #1ed760; }
.btn-sm { padding: 6px 16px; font-size: 12px; }

.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 80px 24px;
  text-align: center;
}

.hero h1 { font-size: 36px; font-weight: 900; }
.hero p { color: var(--muted); font-size: 15px; max-width: 340px; line-height: 1.5; }

.playlist-header {
  padding: 20px 24px 14px;
  border-bottom: 1px solid var(--surface);
}

.playlist-header h2 { font-size: 20px; font-weight: 700; }
.playlist-header p { color: var(--muted); font-size: 13px; margin-top: 4px; }

.track-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.track-table th {
  text-align: left;
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--surface);
}

.track-table td { padding: 10px 12px; }
.track-table tbody tr:hover { background: var(--surface); }

.track-num { color: var(--muted); width: 44px; }
.track-table tbody tr:first-child .track-num { color: var(--green); }
.track-name { font-weight: 500; }
.track-artist, .track-album { color: var(--muted); }
.track-duration { color: var(--muted); width: 60px; text-align: right; }

.export-bar {
  background: var(--surface);
  padding: 14px 24px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #333;
  position: sticky;
  bottom: 0;
}

.error {
  color: #e55;
  font-size: 13px;
  margin-top: 4px;
}
```

- [ ] **Step 2: Run all tests to confirm CSS change didn't break anything**

```bash
pytest tests/ -v
```

Expected: All tests PASSED.

- [ ] **Step 3: Commit**

```bash
git add app/static/style.css
git commit -m "feat: add Spotify dark theme CSS"
```

---

### Task 11: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

````markdown
# Spotify Setlist Exporter

Paste a Spotify playlist link, preview all tracks, and download them as a CSV.

## Setup

### 1. Create a Spotify Developer App

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Click **Create app**
3. Give it any name and description
4. Set **Redirect URI** to: `http://localhost:8000/callback`
5. Save — copy your **Client ID** and **Client Secret**

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SECRET_KEY=any_long_random_string
REDIRECT_URI=http://localhost:8000/callback
```

### 3. Run with Docker

```bash
docker-compose up
```

Open [http://localhost:8000](http://localhost:8000)

## Usage

1. Click **Login with Spotify** and authorize the app
2. Paste any Spotify playlist URL and click **Load**
3. Review the tracks in the table
4. Click **Export CSV** to download

## CSV Format

| Column | Description |
|---|---|
| Track Number | The song's position on its album |
| Track Name | Song title |
| Artist | First listed artist |
| Album | Album name |
| Track Length | Duration in m:ss |

## Development (without Docker)

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in .env
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest tests/ -v
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```
