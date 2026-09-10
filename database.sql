-- Database: password_keeper

-- DROP DATABASE IF EXISTS "password_keeper";

-- CREATE DATABASE "password_keeper"
--     WITH
--     OWNER = postgres
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'French_France.1252'
--     LC_CTYPE = 'French_France.1252'
--     LOCALE_PROVIDER = 'libc'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1
--     IS_TEMPLATE = False;

-- Nettoyage
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS identifiants CASCADE;
DROP TABLE IF EXISTS categories CASCADE;	
DROP TABLE IF EXISTS utilisateurs CASCADE;


-- Création de la table utilisateur
CREATE TABLE utilisateurs (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    initiales VARCHAR(10) NOT NULL,
    nom VARCHAR(50) UNIQUE NOT NULL,
    prenom VARCHAR(50) UNIQUE NOT NULL,
    pseudo VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    kdf_salt VARCHAR(32) NOT NULL,
    masterpassword VARCHAR(255) NOT NULL,
    vault_verifier VARCHAR(255)
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


-- Création de la table categories
CREATE TABLE categories (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_categorie VARCHAR(50) NOT NULL UNIQUE,
    nom VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL
);

-- Création de la table identifiants
CREATE TABLE identifiants (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    identifiant VARCHAR(100) NOT NULL,
    service VARCHAR(100) NOT NULL,
    url_service VARCHAR(100) NOT NULL,
    service_categorie VARCHAR(100) NOT NULL,
    favori BOOLEAN NOT NULL,
    mdp TEXT NOT NULL,
    mdp_force VARCHAR(100) NOT NULL,
	
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
        REFERENCES categories (nom)
);

-- Ajout de categories pour les services
INSERT INTO categories (id_categorie, nom, description) VALUES 
('email', 'Email', 'Vos identifiants email'),
('streaming', 'Streaming', 'Vos identifiants streaming'),
('social', 'Social', 'Vos identifiants sociaux'),
('developpeur', 'Developpeur', 'Vos identifiants de développement'),
('travail', 'Travail', 'Vos identifiants professionnels'),
('personel', 'Personel', 'Vos identifiants personnels');
