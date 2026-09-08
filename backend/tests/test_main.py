from pathlib import Path
import sys

import pytest
from cryptography.fernet import Fernet
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[1]))
import main


@pytest.fixture()
def database(monkeypatch):
    monkeypatch.setenv("VAULT_ENCRYPTION_KEY", Fernet.generate_key().decode())
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(main, "engine", test_engine)
    main.Base.metadata.create_all(test_engine)
    yield test_engine


def test_password_hash_round_trip():
    password_hash = main.hash_password("secret123")

    assert main.verify_password("secret123", password_hash)
    assert not main.verify_password("wrong-password", password_hash)


def test_user_vault_key_encrypts_and_decrypts_password(database):
    user = main.register(main.RegisterCredentials(
        nom="Dupont",
        prenom="Alice",
        pseudo="alice",
        email="alice@example.com",
        password="secret123",
    ))

    with Session(database) as session:
        stored_user = session.scalar(select(main.User).where(main.User.id == user.id))
        encrypted = main.encrypt_vault_password("service-secret", stored_user)

    assert encrypted != "service-secret"
    assert main.decrypt_vault_password(encrypted, stored_user) == "service-secret"


def test_register_returns_user_profile(database):
    response = main.register(
        main.RegisterCredentials(
            nom="Dupont",
            prenom="Alice",
            pseudo="alice",
            email="Alice@Example.com",
            password="secret123",
        )
    )

    assert response.email == "alice@example.com"
    assert response.pseudo == "alice"
    assert response.nom == "Dupont"
    assert response.prenom == "Alice"

    with Session(database) as session:
        user = session.scalar(select(main.User).where(main.User.email == "alice@example.com"))

    assert user.initiales == "AD"


def test_pseudo_must_be_unique(database):
    payload = main.RegisterCredentials(
        nom="Premier",
        prenom="Compte",
        pseudo="keeper",
        email="first@example.com",
        password="secret123",
    )
    main.register(payload)

    with pytest.raises(Exception) as error:
        main.register(main.RegisterCredentials(
            nom="Second",
            prenom="Compte",
            pseudo="keeper",
            email="second@example.com",
            password="secret123",
        ))

    assert error.value.status_code == 409
    assert error.value.detail == "Ce pseudo est déjà utilisé."


def test_login_with_pseudo(database):
    main.register(
        main.RegisterCredentials(
            nom="Martin",
            prenom="Marc",
            pseudo="myuser",
            email="user@example.com",
            password="secret123",
        )
    )

    response = main.login(
        main.Credentials(login="MYUSER", password="secret123")
    )

    assert response.email == "user@example.com"
    assert response.pseudo == "myuser"


def test_login_creates_authenticated_session(database):
    main.register(main.RegisterCredentials(
        nom="Session",
        prenom="User",
        pseudo="sessionuser",
        email="session@example.com",
        password="secret123",
    ))

    response = main.login(main.Credentials(login="sessionuser", password="secret123"))
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=response.session_token)
    authenticated_user = main.get_current_user(credentials)

    assert response.session_token
    assert authenticated_user.email == "session@example.com"


def test_login_rejects_wrong_password(database):
    main.register(
        main.RegisterCredentials(
            nom="Martin",
            prenom="Marc",
            pseudo="myuser",
            email="user@example.com",
            password="secret123",
        )
    )

    with pytest.raises(Exception) as error:
        main.login(main.Credentials(login="myuser", password="wrong123"))

    assert error.value.status_code == 401