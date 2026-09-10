# Password-Keeper
Outil permettant la gestion de mots de passe.

## Installation et lancement du projet

Installer les dépendances Python :

Dans un terminal, démarrer le backend avec les commandes suivantes :

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Dans un autre terminal, démarrer le frontend avec :

```bash
npm run dev
```

Lancer les tests backend :
```bash
pytest backend/tests
```

Démarrer l'API depuis la racine du projet :

```bash
uvicorn backend.main:app --reload
```

L'API est disponible sur `http://localhost:8000` et sa documentation sur `http://localhost:8000/docs`.

Pour lancer les tests backend :

```bash
pytest backend/tests
```

## Tests backend

Les tests se trouvent dans `backend/tests/test_main.py` :

| Test | Ce qui est vérifié |
|------|---------------------|
| `test_password_hash_round_trip` | Un mot de passe haché peut être vérifié avec le bon mot de passe et rejeté avec un mauvais |
| `test_register_returns_user_profile` | L'inscription crée un utilisateur (email normalisé, initiales, sel KDF) et renvoie son profil |
| `test_register_never_sees_plaintext_password_reused_as_secret` | Le serveur ne stocke jamais le mot de passe en clair, seulement un hash et un sel KDF |
| `test_pseudo_must_be_unique` | L'inscription avec un pseudo déjà utilisé renvoie une erreur 409 |
| `test_login_with_pseudo` | La connexion fonctionne avec le pseudo (insensible à la casse) |
| `test_login_sets_httponly_session_cookie` | La connexion pose un cookie de session `HttpOnly` et `Secure` |
| `test_login_creates_authenticated_session` | Le token de session obtenu après connexion permet de récupérer l'utilisateur authentifié |
| `test_login_rejects_wrong_password` | La connexion avec un mauvais mot de passe renvoie une erreur 401 |
| `test_private_routes_require_authentication` | Les routes privées exigent une authentification (401 sans session) |
| `test_forged_token_is_rejected` | Un token de session forgé/invalide est rejeté (401) |
| `test_expired_session_is_rejected` | Une session expirée est rejetée (401) |
| `test_logout_revokes_session` | La déconnexion révoque la session : le token n'est plus valide ensuite |
| `test_passwords_are_isolated_between_users` | Les mots de passe d'un utilisateur ne sont pas visibles par un autre, et le blob chiffré est stocké tel quel côté serveur |
| `test_logout_without_token_does_not_create_authenticated_session` | Se déconnecter sans être connecté ne crée pas de session authentifiée |

## Lancement avec Docker (Partie généré avec IA, fonctionnelle => je l'ai testé)

Le projet peut aussi être lancé entièrement avec Docker (base de données PostgreSQL, API FastAPI et frontend Vue) via `docker-compose.yml` :

```bash
cp .env.example .env   # si vous n'avez pas encore de .env
docker compose up --build
```

Cela démarre 3 services :

| Service | Rôle | Accès |
|---------|------|-------|
| `db` | PostgreSQL, initialisé avec `database.sql` (schéma + catégories par défaut) | `localhost:5432` |
| `backend` | API FastAPI (uvicorn) | joignable uniquement depuis le réseau Docker interne (`backend:8000`) |
| `web` | Build de prod du frontend Vue servi par nginx, qui fait aussi reverse proxy `/api` vers `backend` | `https://localhost:8443` |

Ouvrir **https://localhost:8443** dans le navigateur (certificat auto-signé généré au build de l'image, comme en dev avec `@vitejs/plugin-basic-ssl` : le navigateur affichera un avertissement à accepter). Le frontend et l'API étant servis sous la même origine, les cookies de session `Secure`/`HttpOnly` fonctionnent sans configuration CORS supplémentaire.

Les données PostgreSQL sont persistées dans le volume Docker `pgdata`. Pour repartir d'une base vide :

```bash
docker compose down -v
```

## CI/CD GitHub Actions

Le workflow `.github/workflows/ci.yml` s'exécute sur chaque push et pull request vers `main` ou `dev_cdc_serigne`.

Il vérifie automatiquement :
- les tests unitaires FastAPI avec `pytest` ;
- la compilation de l'application Vue avec `npm run build`.

