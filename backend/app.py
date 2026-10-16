"""Rafiq Baz API. Fictional sample profiles, personal accounts and isolated demo sessions."""
from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import re
import unicodedata
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
if __package__:
    from .auth import AuthManager
else:
    from auth import AuthManager

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = json.loads((ROOT / "shared/demo-data.json").read_text(encoding="utf-8"))
DATA["profiles"] = json.loads((ROOT / "public/data/profiles.json").read_text(encoding="utf-8"))
PROFILES = {profile["id"]: profile for profile in DATA["profiles"]}
DB_PATH = Path(os.environ.get("RB_DATABASE", str(ROOT / "backend/data/demo.sqlite3")))
INTERESTS = {"coffee", "music", "travel", "photo", "art", "hiking", "books", "cinema"}

@contextmanager
def connection():
    db = sqlite3.connect(DB_PATH, timeout=5)
    try:
        db.execute("PRAGMA foreign_keys=ON")
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connection() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL)")
        auth.initialize(db)
        db.commit()
    yield

auth = AuthManager(connection, DATA["state"])
app = FastAPI(title="Rafiq Baz · API", version="0.3.0", lifespan=lifespan)
app.include_router(auth.router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "capacitor://localhost", "http://localhost", "https://localhost"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Demo-Session", "X-RB-Client"],
    allow_credentials=True,
)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith("/api/") or request.url.path == "/runtime-config.js":
        response.headers["Cache-Control"] = "no-store"
    return response

def demo_session(request: Request, x_demo_session: Annotated[str | None, Header()] = None) -> str:
    owner = auth.owner_key(request)
    if owner:
        return owner
    try:
        return str(UUID(x_demo_session))
    except (ValueError, AttributeError) as exc:
        raise HTTPException(400, "A valid demo session UUID is required") from exc

Session = Annotated[str, Depends(demo_session)]

def state_for(db: sqlite3.Connection, session: str) -> dict:
    row = db.execute("SELECT state FROM sessions WHERE id=?", (session,)).fetchone()
    state = deepcopy(DATA["state"])
    if row:
        saved = json.loads(row[0])
        state.update(saved)
        state["me"] = {**deepcopy(DATA["state"]["me"]), **saved.get("me", {})}
        if state["me"]["bio"] == "دنبال رفاقت‌های خوب و تجربه‌های تازه. قهوه، موسیقی و سفر همیشه توی برنامه‌مه.":
            state["me"]["bio"] = DATA["state"]["me"]["bio"]
    return state

def mutate(session: str, operation) -> dict:
    with connection() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            state = state_for(db, session)
            operation(state)
            db.execute(
                "INSERT INTO sessions (id,state,updated_at) VALUES (?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at",
                (session, json.dumps(state, ensure_ascii=False), datetime.now(timezone.utc).isoformat()),
            )
            db.commit()
            return state
        except Exception:
            db.rollback()
            raise

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Action(StrictModel):
    profile_id: str = Field(max_length=40)
    kind: Literal["like", "pass", "save", "undo", "avoid", "undo_avoid"]

class Preferences(StrictModel):
    minAge: int = Field(ge=18, le=80)
    maxAge: int = Field(ge=18, le=80)
    distance: int = Field(ge=1, le=200)
    interest: str = "all"
    online: bool = False

    @model_validator(mode="after")
    def valid_range(self):
        if self.minAge > self.maxAge:
            raise ValueError("Invalid age range")
        if self.interest != "all" and self.interest not in INTERESTS:
            raise ValueError("Invalid interest")
        return self

def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).replace("ي", "ی").replace("ك", "ک")
    return re.sub(r"\s+", " ", value.replace("\u200c", " ").replace("\u200d", " ")).strip().lower()

class ProfileAttribute(StrictModel):
    key: str = Field(min_length=1, max_length=32)
    value: str = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def valid_text(self):
        self.key, self.value = self.key.strip(), self.value.strip()
        if not self.key or not self.value:
            raise ValueError("Attribute key and value cannot be blank")
        return self

class MyProfile(StrictModel):
    name: str = Field(min_length=1, max_length=40)
    age: int = Field(ge=18, le=80)
    city: str = Field(min_length=1, max_length=60)
    bio: str = Field(max_length=400)
    interests: list[str] = Field(max_length=8)
    relationshipGoal: Literal["long_term", "intentional", "exploring"] = "long_term"
    attributes: list[ProfileAttribute] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def valid_values(self):
        self.name, self.city = self.name.strip(), self.city.strip()
        if not self.name or not self.city or any(i not in INTERESTS for i in self.interests):
            raise ValueError("Invalid profile fields")
        self.interests = list(dict.fromkeys(self.interests))
        keys = [normalized(attribute.key) for attribute in self.attributes]
        if len(keys) != len(set(keys)):
            raise ValueError("Attribute keys must be unique")
        return self

class NewMessage(StrictModel):
    profile_id: str = Field(max_length=40)
    text: str = Field(min_length=1, max_length=1000)

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "preview", "version": "0.3.0"}

@app.get("/api/v1/profiles")
def profiles():
    return DATA["profiles"]

@app.get("/api/v1/state")
def get_state(session: Session):
    with connection() as db:
        return state_for(db, session)

@app.post("/api/v1/actions")
def action(body: Action, session: Session):
    if body.profile_id not in PROFILES:
        raise HTTPException(404, "Profile not found")
    def operation(state):
        profile_id = body.profile_id
        if body.kind == "like":
            if profile_id not in state["likes"]:
                state["likes"].append(profile_id)
            if PROFILES[profile_id]["likesYou"] and profile_id not in state["connections"]:
                state["connections"].append(profile_id)
        elif body.kind == "pass" and profile_id not in state["passed"]:
            state["passed"].append(profile_id)
        elif body.kind == "undo":
            state["passed"] = [p for p in state["passed"] if p != profile_id]
        elif body.kind == "avoid" and profile_id not in state["avoided"]:
            state["avoided"].append(profile_id)
        elif body.kind == "undo_avoid":
            state["avoided"] = [p for p in state["avoided"] if p != profile_id]
        elif body.kind == "save":
            if profile_id in state["saved"]:
                state["saved"].remove(profile_id)
            else:
                state["saved"].append(profile_id)
    return mutate(session, operation)

@app.post("/api/v1/preferences")
def preferences(body: Preferences, session: Session):
    return mutate(session, lambda state: state.update(preferences=body.model_dump()))

@app.post("/api/v1/me")
def my_profile(body: MyProfile, session: Session):
    def operation(state):
        state["me"].update(body.model_dump(exclude_unset=True))
    return mutate(session, operation)

@app.post("/api/v1/messages")
def send_message(body: NewMessage, session: Session):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "Message cannot be blank")
    def operation(state):
        if body.profile_id not in state["connections"]:
            raise HTTPException(403, "A mutual connection is required")
        messages = state["messages"].setdefault(body.profile_id, [])
        if len(messages) >= 500:
            raise HTTPException(429, "Demo message limit reached")
        messages.append({
            "id": str(uuid4()), "text": text, "mine": True,
            "time": datetime.now(timezone.utc).strftime("%H:%M"),
        })
    return mutate(session, operation)

@app.post("/api/v1/reset-passes")
def reset_passes(session: Session):
    return mutate(session, lambda state: state.update(passed=[]))

@app.get("/runtime-config.js")
def runtime_config():
    return Response("window.__RB_CONFIG__={mode:'api',apiBase:''};", media_type="text/javascript")

@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, "Endpoint not found")
    candidate = (DIST / path).resolve()
    if not candidate.is_relative_to(DIST.resolve()):
        raise HTTPException(404, "Not found")
    if candidate.is_file():
        headers = {"Cache-Control": "public,max-age=86400"} if path.startswith("assets/") else {}
        if path.startswith(("main-", "styles-")):
            headers = {"Cache-Control": "public,max-age=31536000,immutable"}
        return FileResponse(candidate, headers=headers)
    if "." in Path(path).name:
        raise HTTPException(404, "Asset not found")
    if (DIST / "index.html").exists():
        return FileResponse(DIST / "index.html", headers={"Cache-Control": "no-cache"})
    return JSONResponse({"detail": "Build Angular first: npm run build"}, status_code=503)
