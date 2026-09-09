import hashlib
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import unicodedata

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, String, create_engine, delete, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

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
    vault_key: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column("masterpassword", String(255))


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    date_expiration: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class PasswordEntry(Base):
    __tablename__ = "identifiants"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilisateur_id: Mapped[int] = mapped_column(index=True)
    identifiant: Mapped[str] = mapped_column(String(100))
    service: Mapped[str] = mapped_column(String(100))
    url_service: Mapped[str] = mapped_column(String(100))
    service_categorie: Mapped[str] = mapped_column(String(100))
    favori: Mapped[bool] = mapped_column()
    mdp: Mapped[str] = mapped_column(String(255))
    mdp_force: Mapped[str] = mapped_column(String(100))

class PasswordCategory(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_categorie: Mapped[str] = mapped_column(String(50), unique=True)
    nom: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str] = mapped_column(String(255))

class Credentials(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

class RegisterCredentials(BaseModel):
    nom: str = Field(min_length=1, max_length=50)
    prenom: str = Field(min_length=1, max_length=50)
    pseudo: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)

class PasswordCategoryCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=255)

class PasswordCategoryResponse(BaseModel):
    id: int
    id_categorie: str
    nom: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=255)

class PasswordEntryResponse(BaseModel):
    id: int
    identifiant: str
    service: str
    url_service: str
    service_categorie: str
    favori: bool
    mdp: str
    mdp_force: str

class PasswordEntryCreate(BaseModel):
    identifiant: str = Field(min_length=1, max_length=100)
    service: str = Field(min_length=1, max_length=100)
    url_service: str = Field(min_length=1, max_length=100)
    service_categorie: str = Field(min_length=1, max_length=100)
    favori: bool
    mdp: str = Field(min_length=1)
    mdp_force: str = Field(min_length=1, max_length=100)

class UserResponse(BaseModel):
    id: int
    initiales: str
    email: str
    nom: str
    prenom: str
    pseudo: str | None


class LoginResponse(UserResponse):
    session_token: str

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

session_scheme = HTTPBearer(auto_error=False)
session_duration = timedelta(minutes=30)

def normalize_email(email: str) -> str:
    return email.strip().lower()

def hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
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


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(session: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    session.add(UserSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        date_expiration=datetime.now(timezone.utc) + session_duration,
    ))
    session.commit()
    return raw_token

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(session_scheme),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authentification requise.")

    with Session(engine) as session:
        stored_session = session.scalar(
            select(UserSession).where(UserSession.token_hash == hash_session_token(credentials.credentials))
        )
        date_expiration = stored_session.date_expiration if stored_session else None
        if date_expiration is not None and date_expiration.tzinfo is None:
            date_expiration = date_expiration.replace(tzinfo=timezone.utc)
        if stored_session is None or date_expiration <= datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session invalide ou expirée.")
        user = session.get(User, stored_session.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
        return user

def get_vault_cipher() -> Fernet:
    encryption_key = os.getenv("VAULT_ENCRYPTION_KEY")
    if not encryption_key:
        raise HTTPException(status_code=503, detail="VAULT_ENCRYPTION_KEY n'est pas configurée.")
    try:
        return Fernet(encryption_key.encode())
    except ValueError as error:
        raise HTTPException(status_code=500, detail="VAULT_ENCRYPTION_KEY est invalide.") from error


def create_user_vault_key() -> str:
    user_key = Fernet.generate_key()
    return get_vault_cipher().encrypt(user_key).decode()


def get_user_vault_cipher(user: User) -> Fernet:
    try:
        user_key = get_vault_cipher().decrypt(user.vault_key.encode())
        return Fernet(user_key)
    except InvalidToken as error:
        raise HTTPException(status_code=500, detail="Impossible de déchiffrer la clé du coffre.") from error


def encrypt_vault_password(password: str, user: User) -> str:
    return get_user_vault_cipher(user).encrypt(password.encode()).decode()


def decrypt_vault_password(password: str, user: User) -> str:
    if not password.startswith("gAAAA"):
        return password
    try:
        return get_user_vault_cipher(user).decrypt(password.encode()).decode()
    except InvalidToken as error:
        raise HTTPException(status_code=500, detail="Impossible de déchiffrer ce mot de passe.") from error

def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        initiales=user.initiales,
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        pseudo=user.pseudo,
    )

def generate_category_id(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    return name

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
            vault_key=create_user_vault_key(),
            password_hash=hash_password(credentials.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user_response(user)

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: Credentials) -> LoginResponse:
    identifier = credentials.login.strip().lower()
    with Session(engine) as session:
        user = session.scalar(select(User).where((User.pseudo == identifier) | (User.email == identifier)))
        if user is None or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Adresse e-mail ou mot de passe incorrect.")
        session_token = create_session(session, user)
        return LoginResponse(**user_response(user).model_dump(), session_token=session_token)


@app.post("/api/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(session_scheme)) -> dict[str, str]:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        with Session(engine) as session:
            session.execute(delete(UserSession).where(
                UserSession.token_hash == hash_session_token(credentials.credentials)
            ))
            session.commit()
    return {"status": "ok"}

@app.get("/api/passwords")
def get_passwords(user: User = Depends(get_current_user)) -> list[PasswordEntryResponse]:
    with Session(engine) as session:
        entries = session.scalars(
            select(PasswordEntry)
            .where(PasswordEntry.utilisateur_id == user.id)
            .order_by(PasswordEntry.service)
        ).all()
        return [
            PasswordEntryResponse(
                id=entry.id,
                identifiant=entry.identifiant,
                url_service=entry.url_service,
                service=entry.service,
                service_categorie=entry.service_categorie,
                favori=entry.favori,
                mdp=decrypt_vault_password(entry.mdp, user),
                mdp_force=entry.mdp_force
            )
            for entry in entries
        ]
    
@app.post("/api/passwords", response_model=PasswordEntryResponse, status_code=status.HTTP_201_CREATED)
def add_password_entry(entry: PasswordEntryCreate, user: User = Depends(get_current_user)) -> PasswordEntryResponse:
    with Session(engine) as session:
        password_entry = PasswordEntry(
            **entry.model_dump(),
            utilisateur_id=user.id,
        )
        password_entry.mdp = encrypt_vault_password(entry.mdp, user)
        session.add(password_entry)
        session.commit()
        session.refresh(password_entry)
        return PasswordEntryResponse(
            id=password_entry.id,
            identifiant=password_entry.identifiant,
            url_service=password_entry.url_service,
            service=password_entry.service,
            service_categorie=password_entry.service_categorie,
            favori=password_entry.favori,
            mdp=decrypt_vault_password(password_entry.mdp, user),
            mdp_force=password_entry.mdp_force
        )

@app.put("/api/passwords/{entry_id}", response_model=PasswordEntryResponse)
def update_password_entry(entry_id: int, entry: PasswordEntryCreate, user: User = Depends(get_current_user)) -> PasswordEntryResponse:
    with Session(engine) as session:
        password_entry = session.get(PasswordEntry, entry_id)
        if password_entry is None or password_entry.utilisateur_id != user.id:
            raise HTTPException(status_code=404, detail="Identifiant introuvable.")
        for field, value in entry.model_dump().items():
            setattr(password_entry, field, value)
        password_entry.mdp = encrypt_vault_password(entry.mdp, user)
        session.commit()
        session.refresh(password_entry)
        return PasswordEntryResponse(
            id=password_entry.id,
            identifiant=password_entry.identifiant,
            url_service=password_entry.url_service,
            service=password_entry.service,
            service_categorie=password_entry.service_categorie,
            favori=password_entry.favori,
            mdp=decrypt_vault_password(password_entry.mdp, user),
            mdp_force=password_entry.mdp_force
        )

@app.get("/api/categories", response_model=list[PasswordCategoryResponse])
def get_categories(user: User = Depends(get_current_user)) -> list[PasswordCategoryResponse]:
    with Session(engine) as session:
        categories = session.scalars(select(PasswordCategory).order_by(PasswordCategory.nom)).all()
        return [
            PasswordCategoryResponse(id=category.id, id_categorie=category.id_categorie, nom=category.nom, description=category.description)
            for category in categories
        ]
    
@app.post("/api/categories", response_model=PasswordCategoryResponse, status_code=status.HTTP_201_CREATED)
def add_category(category: PasswordCategoryCreate, user: User = Depends(get_current_user)) -> PasswordCategoryResponse:
    nom = category.nom.strip()
    description = category.description.strip()
    id_categorie = generate_category_id(nom)

    if not id_categorie:
        raise HTTPException(
            status_code=400,
            detail="Le nom de la catégorie ne permet pas de créer un identifiant valide."
        )

    with Session(engine) as session:

        existing_id = session.scalar(
            select(PasswordCategory).where(
                PasswordCategory.id_categorie == id_categorie
            )
        )

        if existing_id:
            raise HTTPException(
                status_code=409,
                detail="Une catégorie avec ce nom existe déjà."
            )

        existing_name = session.scalar(
            select(PasswordCategory).where(
                PasswordCategory.nom == nom
            )
        )

        if existing_name:
            raise HTTPException(
                status_code=409,
                detail="Une catégorie avec ce nom existe déjà."
            )

        new_category = PasswordCategory(
            id_categorie=id_categorie,
            nom=nom,
            description=description,
        )

        session.add(new_category)
        session.commit()
        session.refresh(new_category)

        return PasswordCategoryResponse(
            id=new_category.id,
            id_categorie=new_category.id_categorie,
            nom=new_category.nom,
            description=new_category.description,
        )