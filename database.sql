DROP TABLE IF EXISTS identifiants CASCADE;
DROP TABLE IF EXISTS utilisateurs CASCADE;

CREATE TABLE utilisateurs (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    initiales VARCHAR(10) NOT NULL,
    nom VARCHAR(50) UNIQUE NOT NULL,
    prenom VARCHAR(50) UNIQUE NOT NULL,
    pseudo VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    masterpassword VARCHAR(255) NOT NULL
);

CREATE TABLE identifiants (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id INT NOT NULL,
    service VARCHAR(100) NOT NULL,
    login_ou_email VARCHAR(255) NOT NULL,
    mdp TEXT NOT NULL,
    CONSTRAINT fk_utilisateur
        FOREIGN KEY (utilisateur_id)
        REFERENCES utilisateurs (id)
        ON DELETE CASCADE
);