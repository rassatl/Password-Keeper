
-- Nettoyage
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
    masterpassword VARCHAR(255) NOT NULL
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
    login_ou_email VARCHAR(255) NOT NULL,
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

-- 1. Ajout de deux utilisateurs (les ID 1 et 2 seront générés automatiquement)
-- Note : Les mots de passe ici simulent des versions "hachées" pour l'exemple
INSERT INTO utilisateurs (email, initiales, nom, prenom, pseudo, masterpassword) VALUES 
('alice.dupont@exemple.fr', 'AD', 'alice', 'dupont', 'aloulou', '$2y$10$FauxHashTresLongPourExempleAlice12345'),
('marc.martin@exemple.fr', 'MM', 'marc', 'martin', 'marquis', '$2y$10$FauxHashTresLongPourExempleMarc98765');

-- 2. Ajout de categories pour les services
INSERT INTO password_categories (nom) VALUES 
('Email'),
('Streaming'),
('Social'),
('Developer');

-- 3. Ajout de mots de passe pour Alice (utilisateur_id = 1)
INSERT INTO identifiants (utilisateur_id, service, service_categorie, login_ou_email, mdp) VALUES 
(1, 'Netflix', 'Streaming', 'alice.dupont@exemple.fr', 'N3tfl!x_4lice_2026'),
(1, 'Gmail', 'Email', 'alice.dupont@gmail.com', 'M0nP4ssW0rdB3ton!'),
(1, 'Amazon', 'Streaming', 'alice.dupont@exemple.fr', 'Amz_Achats_Secret77');

-- 3. Ajout de mots de passe pour Marc (utilisateur_id = 2)
INSERT INTO identifiants (utilisateur_id, service, service_categorie, login_ou_email, mdp) VALUES 
(2, 'Spotify', 'Streaming', 'marcmartin_music', 'MusiqU3_M4rc!!'),
(2, 'GitHub', 'Developer', 'marc.dev.martin', 'G1tHub_C0d3r_99');