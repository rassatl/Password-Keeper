from pathlib import Path
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import Request, Response
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parents[1]))
import main


def make_request(cookies: dict[str, str] | None = None) -> Request:
    cookie_header = "; ".join(f"{key}={value}" for key, value in (cookies or {}).items())
    headers = [(b"cookie", cookie_header.encode())] if cookie_header else []
    scope = {
        "type": "http",
        "headers": headers,
        "client": ("test", 0),
        "query_string": b"",
    }
    return Request(scope)


def extract_session_token(response: Response) -> str:
    set_cookie_headers = [value for key, value in response.raw_headers if key == b"set-cookie"]
    assert len(set_cookie_headers) == 1
    cookie_header = set_cookie_headers[0].decode()
    return cookie_header.split(f"{main.SESSION_COOKIE_NAME}=")[1].split(";")[0]


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
    assert response.kdf_salt

    with Session(database) as session:
        user = session.scalar(select(main.User).where(main.User.email == "alice@example.com"))

    assert user.initiales == "AD"
    assert user.kdf_salt == response.kdf_salt


def test_register_never_sees_plaintext_password_reused_as_secret(database):
    # Le serveur ne doit stocker qu'un sel KDF (public) et un hash de mot de
    # passe irréversible : jamais de clé permettant de déchiffrer les secrets.
    response = main.register(main.RegisterCredentials(
        nom="Dupont",
        prenom="Alice",
        pseudo="alice",
        email="alice@example.com",
        password="secret123",
    ))

    with Session(database) as session:
        user = session.scalar(select(main.User).where(main.User.id == response.id))

    assert not hasattr(user, "vault_key")
    assert user.password_hash != "secret123"


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
        main.Credentials(login="MYUSER", password="secret123"),
        Response(),
    )

    assert response.email == "user@example.com"
    assert response.pseudo == "myuser"


def test_login_sets_httponly_session_cookie(database):
    main.register(main.RegisterCredentials(
        nom="Session",
        prenom="User",
        pseudo="sessionuser",
        email="session@example.com",
        password="secret123",
    ))

    response = Response()
    main.login(main.Credentials(login="sessionuser", password="secret123"), response)

    set_cookie_headers = [value for key, value in response.raw_headers if key == b"set-cookie"]
    assert len(set_cookie_headers) == 1
    cookie_header = set_cookie_headers[0].decode()
    assert main.SESSION_COOKIE_NAME in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header


def test_login_creates_authenticated_session(database):
    main.register(main.RegisterCredentials(
        nom="Session",
        prenom="User",
        pseudo="sessionuser",
        email="session@example.com",
        password="secret123",
    ))

    response = Response()
    main.login(main.Credentials(login="sessionuser", password="secret123"), response)
    token = extract_session_token(response)

    authenticated_user = main.get_current_user(make_request({main.SESSION_COOKIE_NAME: token}))

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
        main.login(main.Credentials(login="myuser", password="wrong123"), Response())

    assert error.value.status_code == 401


def test_private_routes_require_authentication(database):
    with pytest.raises(Exception) as error:
        main.get_current_user(make_request())

    assert error.value.status_code == 401
    assert main.get_categories.__defaults__[0].dependency is main.get_current_user


def test_forged_token_is_rejected(database):
    with pytest.raises(Exception) as error:
        main.get_current_user(make_request({main.SESSION_COOKIE_NAME: "forged-token"}))

    assert error.value.status_code == 401


def test_expired_session_is_rejected(database):
    main.register(main.RegisterCredentials(
        nom="Expire",
        prenom="Session",
        pseudo="expired-session",
        email="expired@example.com",
        password="secret123",
    ))
    response = Response()
    main.login(main.Credentials(login="expired-session", password="secret123"), response)
    token = extract_session_token(response)

    with Session(database) as session:
        stored_session = session.scalar(select(main.UserSession))
        stored_session.date_expiration = datetime.now(timezone.utc) - timedelta(minutes=1)
        session.commit()

    with pytest.raises(Exception) as error:
        main.get_current_user(make_request({main.SESSION_COOKIE_NAME: token}))

    assert error.value.status_code == 401


def test_logout_revokes_session(database):
    main.register(main.RegisterCredentials(
        nom="Logout",
        prenom="Secure",
        pseudo="logout-user",
        email="logout@example.com",
        password="secret123",
    ))
    login_response = Response()
    main.login(main.Credentials(login="logout-user", password="secret123"), login_response)
    token = extract_session_token(login_response)

    main.logout(make_request({main.SESSION_COOKIE_NAME: token}), Response())

    with pytest.raises(Exception) as error:
        main.get_current_user(make_request({main.SESSION_COOKIE_NAME: token}))

    assert error.value.status_code == 401


def test_passwords_are_isolated_between_users(database):
    first_user = main.register(main.RegisterCredentials(
        nom="Premier",
        prenom="Alice",
        pseudo="first-user",
        email="first-user@example.com",
        password="secret123",
    ))
    second_user = main.register(main.RegisterCredentials(
        nom="Second",
        prenom="Bob",
        pseudo="second-user",
        email="second-user@example.com",
        password="secret123",
    ))

    with Session(database) as session:
        stored_first_user = session.get(main.User, first_user.id)
        stored_second_user = session.get(main.User, second_user.id)
        main.add_password_entry(main.PasswordEntryCreate(
            identifiant="first-user",
            service="First private service",
            url_service="https://first-service.example.com",
            service_categorie="Developpeur",
            favori=False,
            mdp="v1:encrypted-client-side:first-secret",
            mdp_force="Fort",
        ), stored_first_user)
        main.add_password_entry(main.PasswordEntryCreate(
            identifiant="second-user",
            service="Second private service",
            url_service="https://second-service.example.com",
            service_categorie="Developpeur",
            favori=False,
            mdp="v1:encrypted-client-side:second-secret",
            mdp_force="Fort",
        ), stored_second_user)

        first_passwords = main.get_passwords(stored_first_user)

        stored_entries = session.scalars(select(main.PasswordEntry)).all()
        first_stored_entry = next(entry for entry in stored_entries if entry.service == "First private service")

    # Le serveur ne chiffre/déchiffre plus rien lui-même : il stocke et
    # renvoie tel quel le blob chiffré côté client.
    assert [password.service for password in first_passwords] == ["First private service"]
    assert first_passwords[0].mdp == "v1:encrypted-client-side:first-secret"
    assert first_stored_entry.mdp == "v1:encrypted-client-side:first-secret"


def test_logout_without_token_does_not_create_authenticated_session(database):
    main.logout(make_request(), Response())

    with pytest.raises(Exception) as error:
        main.get_current_user(make_request())

    assert error.value.status_code == 401
