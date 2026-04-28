# Spotify Setlist Exporter — Design Spec

**Date:** 2026-04-27

## Overview

A Dockerized web application that lets a user paste a Spotify playlist link, preview all tracks in a table, and download them as a CSV file. The UI mirrors Spotify's dark aesthetic (black/dark grey backgrounds, green accents).

---

## Architecture

Single Docker container running a Python FastAPI application. No database, no external cache. The access token is stored in an encrypted session cookie (server-side secret key).

```
Docker Container (port 8000)
├── FastAPI app
│   ├── GET  /           → Home page (login or playlist input)
│   ├── GET  /login      → Redirect to Spotify OAuth authorize URL
│   ├── GET  /callback   → Exchange code for access token, store in session
│   ├── POST /playlist   → Fetch tracks from Spotify API, render table
│   └── GET  /export     → Generate and stream CSV download
├── Jinja2 HTML templates
└── Static CSS (Spotify dark theme)
```

**Environment variables (required):**
| Variable | Purpose |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify Developer App client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify Developer App client secret |
| `SECRET_KEY` | Random string used to sign session cookies |

---

## User Flow

1. User opens `http://localhost:8000`
2. If not authenticated → landing page with "Login with Spotify" button
3. Click Login → redirect to Spotify OAuth consent screen (scope: `playlist-read-private`, `playlist-read-collaborative`)
4. Spotify redirects to `/callback` → app exchanges code for access token → stored in session cookie → redirect to home
5. User pastes a Spotify playlist URL into the input field and submits
   - Accepts: `https://open.spotify.com/playlist/{id}` (with or without query params)
6. App fetches all tracks via Spotify API (paginated, 100 per page)
7. Track table renders: `#`, `Title`, `Artist`, `Album`, `Length`
8. User clicks "Export CSV" → browser downloads `{playlist-name}.csv`

---

## UI Design

**Spotify dark theme throughout:**
- Background: `#121212`
- Surface: `#282828`
- Nav bar: `#000000`
- Accent / interactive: `#1DB954` (Spotify green)
- Primary text: `#ffffff`
- Secondary text: `#b3b3b3`

**Screen 1 — Home (logged out):**
- Black top nav bar with green logo dot and "SETLIST EXPORTER" wordmark
- Centered card: headline, one-line description, "Login with Spotify" button (green, pill-shaped)

**Screen 2 — Playlist view (logged in):**
- Top nav bar with playlist URL input field and "Load" button inline
- Playlist name and track count shown below nav
- Track table with columns: `#` (album track number), `Title`, `Artist`, `Album`, `⏱`
  - Alternating row highlight on hover
  - Track number shown in green for the first/active row
- Fixed bottom bar with "Export CSV" button (green, right-aligned)

---

## Spotify API Integration

- **Auth flow:** Authorization Code Flow (not PKCE — server-side app)
- **Scopes:** `playlist-read-private playlist-read-collaborative`
- **Token expiry:** Spotify access tokens expire after 1 hour. On any Spotify API 401 response, the app clears the session and redirects the user to `/login`.
- **Playlist fetch:** `GET /v1/playlists/{id}/tracks` — paginated, offset-based, 100 items per page. App loops until all pages are fetched.
- **Export data:** After a successful playlist load, the playlist ID is stored in the session. `/export` reads the ID from the session, re-fetches all tracks from Spotify, and streams the CSV. No track data is stored server-side between requests.
- **Fields extracted per track:**
  - Track number (the track's position on its album, from Spotify's `track_number` field — e.g., track 5 of 12)
  - Track name
  - Artist name (first artist if multiple)
  - Album name
  - Duration (converted from milliseconds to `m:ss`)

---

## CSV Output

Standard comma-separated, UTF-8 encoded, with header row.

```
Track Number,Track Name,Artist,Album,Track Length
6,Blinding Lights,The Weeknd,After Hours,3:20
2,Levitating,Dua Lipa,Future Nostalgia,3:23
```

`Track Number` is the song's position on its album (e.g., "Blinding Lights" is track 6 on *After Hours*). Rows are ordered by their position in the playlist.

- Filename: `{playlist-name}.csv` (lowercased, spaces replaced with hyphens)
- Delivered as a file download (`Content-Disposition: attachment`)

---

## Docker Setup

**Files:**
- `Dockerfile` — Python 3.12 slim, installs dependencies, runs `uvicorn`
- `docker-compose.yml` — maps port 8000, reads env vars from `.env` file
- `.env.example` — template with the three required variables
- `README.md` — step-by-step: create Spotify Developer App, set redirect URI to `http://localhost:8000/callback`, copy env vars, run `docker-compose up`

**Start the app:**
```bash
cp .env.example .env
# Fill in .env with your Spotify credentials
docker-compose up
```

---

## Project Structure

```
/
├── app/
│   ├── main.py          # FastAPI app, routes
│   ├── spotify.py       # Spotify API client (OAuth + playlist fetching)
│   ├── templates/
│   │   ├── base.html    # Shared layout, CSS variables
│   │   ├── home.html    # Login / playlist input page
│   │   └── playlist.html# Track table + export button
│   └── static/
│       └── style.css    # Spotify dark theme styles
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## Out of Scope

- Exporting multiple playlists at once
- Saving export history
- User accounts or persistent storage
- Playback or audio features
- Mobile-specific layout optimizations
