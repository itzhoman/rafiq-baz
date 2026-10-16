"""Account authentication for the Python deployment; never uses demo session IDs."""
from copy import deepcopy
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator

COOKIE = "rb_account"
NONCE_COOKIE = "rb_google_challenge"
SESSION_SECONDS = 60 * 60 * 24 * 7


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @model_validator(mode="after")
    def clean_email(self):
        self.email = self.email.strip().casefold()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", self.email):
            raise ValueError("Invalid email")
        return self


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=40)
    age: int = Field(ge=18, le=80)
    city: str = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def clean_profile(self):
        self.name, self.city = self.name.strip(), self.city.strip()
        if not self.name or not self.city:
            raise ValueError("Name and city required")
        return self


class GoogleCredential(BaseModel):
    model_config = ConfigDict(extra="forbid")
    credential: str = Field(min_length=1, max_length=16000)
    age: int = Field(ge=18, le=80)
    city: str = Field(min_length=1, max_length=60)


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=67108864)
    return salt.hex() + ":" + digest.hex()


def password_matches(password: str, encoded: str) -> bool:
    salt, _digest = encoded.split(":", 1)
    return hmac.compare_digest(password_hash(password, bytes.fromhex(salt)), encoded)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthManager:
    def __init__(self, connection, default_state):
        self.connection, self.default_state = connection, default_state
        self.dummy_hash = password_hash("dummy-password-value", b"rafiq-baz-dummy!")
        self.router = APIRouter(prefix="/api/v1/auth", tags=["accounts"])
        for path, method, handler in [
            ("/status", "GET", self.status), ("/register", "POST", self.register),
            ("/login", "POST", self.login), ("/logout", "POST", self.logout),
            ("/google/challenge", "POST", self.google_challenge), ("/google", "POST", self.google),
        ]:
            self.router.add_api_route(path, handler, methods=[method])

    def initialize(self, db):
        db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                password_hash TEXT, google_sub TEXT UNIQUE, created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS account_sessions (
                token_hash TEXT PRIMARY KEY, account_id TEXT NOT NULL REFERENCES accounts(id),
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS auth_session_expiry ON account_sessions(expires_at);
            CREATE TABLE IF NOT EXISTS auth_attempts (bucket TEXT NOT NULL, at INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS auth_attempt_bucket ON auth_attempts(bucket,at);
            CREATE TABLE IF NOT EXISTS google_challenges (hash TEXT PRIMARY KEY, expires_at INTEGER NOT NULL);
        """)

    def guard(self, request: Request):
        # A custom header plus an origin allowlist prevents form/login CSRF.
        if request.headers.get("x-rb-client") != "web":
            raise HTTPException(403, "درخواست ورود معتبر نیست.")
        origin = request.headers.get("origin")
        allowed = {str(request.base_url).rstrip("/")}
        allowed.update(x.strip() for x in os.getenv("RB_ALLOWED_ORIGINS", "http://localhost:4200,http://127.0.0.1:4200").split(",") if x.strip())
        if origin and origin not in allowed:
            raise HTTPException(403, "مبدأ درخواست مجاز نیست.")

    def rate_limit(self, request: Request, identity: str = ""):
        now = int(time.time())
        address = request.client.host if request.client else "unknown"
        buckets = [token_hash("ip:" + address)]
        if identity:
            buckets.append(token_hash("identity:" + identity))
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM auth_attempts WHERE at<?", (now - 600,))
            for bucket in buckets:
                count = db.execute("SELECT count(*) FROM auth_attempts WHERE bucket=?", (bucket,)).fetchone()[0]
                if count >= 20:
                    raise HTTPException(429, "تلاش‌های زیادی انجام شد؛ چند دقیقه بعد دوباره امتحان کن.")
            db.executemany("INSERT INTO auth_attempts VALUES (?,?)", [(b, now) for b in buckets])
            db.commit()

    def current(self, request: Request):
        token = request.cookies.get(COOKIE)
        if not token:
            return None
        with self.connection() as db:
            row = db.execute(
                "SELECT a.id,a.email,a.name,a.google_sub FROM account_sessions s JOIN accounts a ON a.id=s.account_id "
                "WHERE s.token_hash=? AND s.expires_at>?", (token_hash(token), int(time.time()))
            ).fetchone()
        if not row:
            raise HTTPException(401, "نشست منقضی شده؛ دوباره وارد شو.")
        return {"id": row[0], "email": row[1], "name": row[2], "provider": "google" if row[3] else "email"}

    def owner_key(self, request: Request):
        user = self.current(request)
        if user and request.method not in ("GET", "HEAD", "OPTIONS"):
            self.guard(request)
        return "account:" + user["id"] if user else None

    def issue(self, response: Response, request: Request, user: dict):
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        with self.connection() as db:
            db.execute("DELETE FROM account_sessions WHERE expires_at<=?", (now,))
            old = request.cookies.get(COOKIE)
            if old:
                db.execute("DELETE FROM account_sessions WHERE token_hash=?", (token_hash(old),))
            db.execute("INSERT INTO account_sessions VALUES (?,?,?)", (token_hash(token), user["id"], now + SESSION_SECONDS))
            db.commit()
        response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
                            secure=os.getenv("RB_SECURE_COOKIES", "") == "1" or request.url.scheme == "https", samesite="lax", path="/")
        return {"user": user}

    def status(self, request: Request, response: Response):
        try:
            user = self.current(request)
        except HTTPException:
            user = None
            response.delete_cookie(COOKIE, path="/")
        return {"user": user, "googleClientId": os.getenv("RB_GOOGLE_CLIENT_ID", ""), "emailEnabled": True}

    def new_account(self, db, email, name, age, city, password=None, google_sub=None):
        user = {"id": str(uuid4()), "email": email, "name": name, "provider": "google" if google_sub else "email"}
        state = deepcopy(self.default_state)
        for field in ("likes", "passed", "saved", "connections", "avoided"):
            state[field] = []
        state["messages"] = {}
        state["me"].update(name=name, age=age, city=city, bio="", interests=[], attributes=[])
        db.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?)", (user["id"], email, name, password, google_sub, int(time.time())))
        db.execute("INSERT INTO sessions VALUES (?,?,?)", ("account:" + user["id"], json.dumps(state, ensure_ascii=False), str(int(time.time()))))
        return user

    def register(self, body: Registration, request: Request, response: Response):
        self.guard(request)
        self.rate_limit(request, body.email)
        encoded = password_hash(body.password)
        try:
            with self.connection() as db:
                user = self.new_account(db, body.email, body.name, body.age, body.city, password=encoded)
                db.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(409, "ایجاد حساب با این ایمیل ممکن نیست؛ ورود را امتحان کن.")
        return self.issue(response, request, user)

    def login(self, body: Credentials, request: Request, response: Response):
        self.guard(request)
        self.rate_limit(request, body.email)
        with self.connection() as db:
            row = db.execute("SELECT id,email,name,password_hash,google_sub FROM accounts WHERE email=?", (body.email,)).fetchone()
        # Do the same expensive hash even for unknown accounts.
        encoded = row[3] if row and row[3] else self.dummy_hash
        valid = password_matches(body.password, encoded)
        if not row or not row[3] or not valid:
            raise HTTPException(401, "ایمیل یا رمز عبور درست نیست.")
        return self.issue(response, request, {"id": row[0], "email": row[1], "name": row[2], "provider": "google" if row[4] else "email"})

    def logout(self, request: Request, response: Response):
        self.guard(request)
        token = request.cookies.get(COOKIE, "")
        with self.connection() as db:
            db.execute("DELETE FROM account_sessions WHERE token_hash=?", (token_hash(token),))
            db.commit()
        response.delete_cookie(COOKIE, path="/")
        return {"ok": True}

    def google_challenge(self, request: Request, response: Response):
        self.guard(request)
        self.rate_limit(request)
        if not os.getenv("RB_GOOGLE_CLIENT_ID"):
            raise HTTPException(503, "ورود گوگل هنوز توسط مدیر فعال نشده است.")
        nonce = secrets.token_urlsafe(32)
        with self.connection() as db:
            db.execute("DELETE FROM google_challenges WHERE expires_at<=?", (int(time.time()),))
            db.execute("INSERT INTO google_challenges VALUES (?,?)", (token_hash(nonce), int(time.time()) + 300))
            db.commit()
        response.set_cookie(NONCE_COOKIE, nonce, httponly=True, samesite="strict", max_age=300,
                            secure=os.getenv("RB_SECURE_COOKIES", "") == "1" or request.url.scheme == "https", path="/api/v1/auth")
        return {"nonce": nonce}

    def verify_google(self, credential, client_id):
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token
        return id_token.verify_oauth2_token(credential, GoogleRequest(), client_id)

    def google(self, body: GoogleCredential, request: Request, response: Response):
        self.guard(request)
        self.rate_limit(request)
        client_id = os.getenv("RB_GOOGLE_CLIENT_ID", "")
        if not client_id:
            raise HTTPException(503, "ورود گوگل هنوز توسط مدیر فعال نشده است.")
        try:
            claims = self.verify_google(body.credential, client_id)
        except Exception as exc:
            raise HTTPException(401, "اعتبار ورود گوگل تأیید نشد.") from exc
        nonce = request.cookies.get(NONCE_COOKIE, "")
        if not nonce or not hmac.compare_digest(str(claims.get("nonce", "")), nonce):
            raise HTTPException(401, "درخواست ورود گوگل منقضی شده است.")
        if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com") or claims.get("aud") != client_id:
            raise HTTPException(401, "اعتبار ورود گوگل تأیید نشد.")
        if not claims.get("sub") or not claims.get("email_verified") or not claims.get("email"):
            raise HTTPException(401, "گوگل ایمیل این حساب را تأیید نکرده است.")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            deleted = db.execute("DELETE FROM google_challenges WHERE hash=? AND expires_at>?", (token_hash(nonce), int(time.time()))).rowcount
            if not deleted:
                raise HTTPException(401, "درخواست ورود گوگل قبلاً استفاده شده یا منقضی شده است.")
            row = db.execute("SELECT id,email,name FROM accounts WHERE google_sub=?", (str(claims["sub"]),)).fetchone()
            if row:
                user = {"id": row[0], "email": row[1], "name": row[2], "provider": "google"}
            else:
                email = str(claims["email"]).strip().casefold()
                if db.execute("SELECT 1 FROM accounts WHERE email=?", (email,)).fetchone():
                    raise HTTPException(409, "این ایمیل قبلاً ثبت شده؛ با رمز عبور همان حساب وارد شو.")
                city = body.city.strip()
                if not city:
                    raise HTTPException(422, "شهر را وارد کن.")
                user = self.new_account(db, email, str(claims.get("name") or email.split("@")[0])[:40], body.age, city, google_sub=str(claims["sub"]))
            db.commit()
        response.delete_cookie(NONCE_COOKIE, path="/api/v1/auth")
        return self.issue(response, request, user)
