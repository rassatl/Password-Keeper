from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).parents[1]))
import main


@pytest.fixture()
def database(monkeypatch):
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


def test_register_returns_user_with_pseudo_and_email(database):
    response = main.register(
        main.RegisterCredentials(email="Alice@Example.com", pseudo="Alice", password="secret123")
    )

    assert response.email == "alice@example.com"
    assert response.pseudo == "alice"


def test_pseudo_must_be_unique(database):
    payload = main.RegisterCredentials(email="first@example.com", pseudo="keeper", password="secret123")
    main.register(payload)

    with pytest.raises(Exception) as error:
        main.register(main.RegisterCredentials(email="second@example.com", pseudo="keeper", password="secret123"))

    assert error.value.status_code == 409
    assert error.value.detail == "Ce pseudo est déjà utilisé."


def test_login_with_pseudo(database):
    main.register(
        main.RegisterCredentials(email="user@example.com", pseudo="myuser", password="secret123")
    )

    response = main.login(
        main.Credentials(pseudo="MYUSER", password="secret123")
    )

    assert response.email == "user@example.com"
    assert response.pseudo == "myuser"


def test_login_rejects_wrong_password(database):
    main.register(
        main.RegisterCredentials(email="user@example.com", pseudo="myuser", password="secret123")
    )

    with pytest.raises(Exception) as error:
        main.login(main.Credentials(pseudo="myuser", password="wrong123"))

    assert error.value.status_code == 401