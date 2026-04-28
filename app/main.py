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
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8000/callback")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    logged_in = bool(request.session.get("access_token"))
    return templates.TemplateResponse(request, "home.html", {"logged_in": logged_in})


@app.get("/login")
def login():
    url = spotify.get_auth_url(redirect_uri=REDIRECT_URI)
    return RedirectResponse(url)


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
            request,
            "home.html",
            {"logged_in": True, "error": str(e)},
        )
    return templates.TemplateResponse(
        request,
        "playlist.html",
        {
            "playlist_name": playlist_name,
            "track_count": len(tracks),
            "tracks": tracks,
        },
    )


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
    except ValueError:
        return RedirectResponse("/")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Track Number", "Track Name", "Artist", "Album", "Track Length"])
    for t in tracks:
        writer.writerow([t["track_number"], t["name"], t["artist"], t["album"], t["duration"]])
    filename = re.sub(r"[^\w\s-]", "", playlist_name).strip().lower()
    filename = re.sub(r"\s+", "-", filename)
    filename = filename or "playlist"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
