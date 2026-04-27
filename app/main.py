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
    return templates.TemplateResponse("home.html", {"request": request, "logged_in": logged_in})


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
