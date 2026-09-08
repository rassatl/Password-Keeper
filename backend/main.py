import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, String, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:rassatl@localhost:5432/password_keeper",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    pseudo: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column("masterpassword", String(255))


class Credentials(BaseModel):
    pseudo: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class RegisterCredentials(Credentials):
    email: str = Field(min_length=3, max_length=255)


class UserResponse(BaseModel):
    id: int
    email: str
    pseudo: str | None


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_inspector = inspect(engine)
    if not database_inspector.has_table("utilisateurs"):
        Base.metadata.create_all(engine)
    else:
        with engine.begin() as connection:
            columns = {column["name"] for column in database_inspector.get_columns("utilisateurs")}
            if "pseudo" not in columns:
                connection.execute(text("ALTER TABLE utilisateurs ADD COLUMN pseudo VARCHAR(50) UNIQUE"))
    yield
    engine.dispose()


app = FastAPI(title="Password Keeper API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", maxsplit=1)
        salt = bytes.fromhex(salt_hex)
    except (ValueError, TypeError):
        return False

    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return hmac.compare_digest(digest.hex(), digest_hex)


def user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, pseudo=user.pseudo)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    with Session(engine) as session:
        session.execute(select(1))
    return {"status": "ok", "database": "connected"}


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: RegisterCredentials) -> UserResponse:
    email = normalize_email(credentials.email)
    pseudo = credentials.pseudo.strip().lower()
    with Session(engine) as session:
        if session.scalar(select(User).where(User.email == email)):
            raise HTTPException(status_code=409, detail="Un compte existe déjà avec cette adresse e-mail.")
        if session.scalar(select(User).where(User.pseudo == pseudo)):
            raise HTTPException(status_code=409, detail="Ce pseudo est déjà utilisé.")
        user = User(email=email, pseudo=pseudo, password_hash=hash_password(credentials.password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user_response(user)


@app.post("/api/auth/login", response_model=UserResponse)
def login(credentials: Credentials) -> UserResponse:
    identifier = credentials.pseudo.strip().lower()
    with Session(engine) as session:
        user = session.scalar(select(User).where((User.pseudo == identifier) | (User.email == identifier)))
        if user is None or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Adresse e-mail ou mot de passe incorrect.")
        return user_response(user)
