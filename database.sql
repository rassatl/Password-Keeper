
-- Nettoyage
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS identifiants CASCADE;
DROP TABLE IF EXISTS password_categories CASCADE;	
DROP TABLE IF EXISTS utilisateurs CASCADE;


-- Création de la table utilisateur
CREATE TABLE utilisateurs (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    initiales VARCHAR(10) NOT NULL,
    nom VARCHAR(50) UNIQUE NOT NULL,
    prenom VARCHAR(50) UNIQUE NOT NULL,
    pseudo VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    vault_key VARCHAR(255) NOT NULL,
    masterpassword VARCHAR(255) NOT NULL
);

-- Création de la table sessions
CREATE TABLE sessions (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INT NOT NULL,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    date_expiration TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id)
        REFERENCES utilisateurs (id)
        ON DELETE CASCADE
);


-- Création de la table password_categories
CREATE TABLE password_categories (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

-- Création de la table identifiants
CREATE TABLE identifiants (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    service VARCHAR(100) NOT NULL,
    service_categorie VARCHAR(100) NOT NULL,
    mdp TEXT NOT NULL,
	
    -- Cette contrainte relie l'identifiant à un utilisateur précis.
    -- ON DELETE CASCADE supprime les mots de passe si l'utilisateur supprime son compte.
    CONSTRAINT fk_utilisateur
        FOREIGN KEY (utilisateur_id)
        REFERENCES utilisateurs (id)
        ON DELETE CASCADE,
	
    -- Cette contrainte relie l'identifiant à un utilisateur précis.
    -- ON DELETE CASCADE supprime les mots de passe si l'utilisateur supprime son compte.
    CONSTRAINT fk_service 
        FOREIGN KEY (service_categorie)
        REFERENCES password_categories (nom)
);

-- Ajout de categories pour les services
INSERT INTO password_categories (nom) VALUES 
('Email'),
('Streaming'),
('Social'),
('Developer');
