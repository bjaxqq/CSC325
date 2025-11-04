

CREATE TABLE Candy (
    candy_id INT AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    candy_count INT NULL,
    PRIMARY KEY (candy_id)
);

CREATE TABLE Egg (
    egg_id INT AUTO_INCREMENT,
    distance_km DECIMAL(4,1) NOT NULL,
    PRIMARY KEY (egg_id)
);

CREATE TABLE Pokemon (
    pokemon_id INT AUTO_INCREMENT,
    num VARCHAR(5),
    name VARCHAR(50) NOT NULL,
    img_url VARCHAR(255),
    height_m DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    spawn_chance DECIMAL(5,3),
    avg_spawns DECIMAL(5,2),
    spawn_time TIME,
    candy_id INT,
    egg_id INT,
    PRIMARY KEY (pokemon_id),
    FOREIGN KEY (candy_id) REFERENCES Candy(candy_id),
    FOREIGN KEY (egg_id) REFERENCES Egg(egg_id)
);

CREATE TABLE Type (
    type_id INT AUTO_INCREMENT,
    type_name VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY (type_id)
);

CREATE TABLE PokemonType (
    pokemon_id INT NOT NULL,
    type_id INT NOT NULL,
    PRIMARY KEY (pokemon_id, type_id),
    FOREIGN KEY (pokemon_id) REFERENCES Pokemon(pokemon_id),
    FOREIGN KEY (type_id) REFERENCES Type(type_id)
);

CREATE TABLE Weakness (
    weakness_id INT AUTO_INCREMENT,
    weakness_name VARCHAR(30) NOT NULL UNIQUE,
    PRIMARY KEY (weakness_id)
);

CREATE TABLE PokemonWeakness (
    pokemon_id INT NOT NULL,
    weakness_id INT NOT NULL,
    PRIMARY KEY (pokemon_id, weakness_id),
    FOREIGN KEY (pokemon_id) REFERENCES Pokemon(pokemon_id),
    FOREIGN KEY (weakness_id) REFERENCES Weakness(weakness_id)
);

CREATE TABLE Evolution (
    evolution_id INT AUTO_INCREMENT,
    from_pokemon_id INT NOT NULL,
    to_pokemon_id INT NOT NULL,
    PRIMARY KEY (evolution_id),
    FOREIGN KEY (from_pokemon_id) REFERENCES Pokemon(pokemon_id),
    FOREIGN KEY (to_pokemon_id) REFERENCES Pokemon(pokemon_id)
);
