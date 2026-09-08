import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy import String, create_engine, select
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
    initiales: Mapped[str] = mapped_column(String(10), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    prenom: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    pseudo: Mapped[str | None] = mapped_column(String(50), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column("masterpassword", String(255))


class PasswordEntry(Base):
    __tablename__ = "identifiants"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(index=True)
    service: Mapped[str] = mapped_column(String(100))
    login_ou_email: Mapped[str] = mapped_column(String(255))
    mdp: Mapped[str] = mapped_column(String(255))


class Credentials(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class RegisterCredentials(BaseModel):
    nom: str = Field(min_length=1, max_length=50)
    prenom: str = Field(min_length=1, max_length=50)
    pseudo: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    initiales: str
    email: str
    nom: str
    prenom: str
    pseudo: str | None

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
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
    return UserResponse(
        id=user.id,
        initiales=user.initiales,
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        pseudo=user.pseudo,
    )


@app.get("/api/health")
def health_check() -> dict[str, str]:
    with Session(engine) as session:
        session.execute(select(1))
    return {"status": "ok", "database": "connected"}


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: RegisterCredentials) -> UserResponse:
    nom = credentials.nom.strip()
    prenom = credentials.prenom.strip()
    pseudo = credentials.pseudo.strip().lower()
    email = normalize_email(credentials.email)
    with Session(engine) as session:
        if session.scalar(select(User).where(User.email == email)):
            raise HTTPException(status_code=409, detail="Un compte existe déjà avec cette adresse e-mail.")
        if session.scalar(select(User).where(User.pseudo == pseudo)):
            raise HTTPException(status_code=409, detail="Ce pseudo est déjà utilisé.")
        user = User(
            initiales=f"{prenom[0]}{nom[0]}".upper(),
            nom=nom,
            prenom=prenom,
            pseudo=pseudo,
            email=email,
            password_hash=hash_password(credentials.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user_response(user)


@app.post("/api/auth/login", response_model=UserResponse)
def login(credentials: Credentials) -> UserResponse:
    identifier = credentials.login.strip().lower()
    with Session(engine) as session:
        user = session.scalar(select(User).where((User.pseudo == identifier) | (User.email == identifier)))
        if user is None or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Adresse e-mail ou mot de passe incorrect.")
        return user_response(user)

@app.get("/api/passwords")
def get_passwords(user_id: int = Query(..., gt=0)) -> list[dict[str, str | int]]:
    with Session(engine) as session:
        entries = session.scalars(
            select(PasswordEntry)
            .where(PasswordEntry.utilisateur_id == user_id)
            .order_by(PasswordEntry.service)
        ).all()
        return [
            {
                "id": entry.id,
                "service": entry.service,
                "login_ou_email": entry.login_ou_email,
                "mdp": entry.mdp,
            }
            for entry in entries
        ]