# Password-Keeper
Outil permettant la gestion de mots de passe.

## Installation et lancement du projet

Installer les dépendances Python :

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Lancer le frontend :
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

## CI/CD GitHub Actions

Le workflow `.github/workflows/ci.yml` s'exécute sur chaque push et pull request vers `main` ou `dev`.

Il vérifie automatiquement :
- les tests unitaires FastAPI avec `pytest` ;
- la compilation de l'application Vue avec `npm run build`.

Dans un autre terminal, démarrer le frontend avec `npm run dev`.
