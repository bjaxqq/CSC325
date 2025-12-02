import pymysql
import json
import re

def get_connection():
    return pymysql.connect(
        host="", 
        port=3306,
        user="",
        password="",
        database=None,
        autocommit=True
    )

def setup_db(cur):
    print("Setting up database...")

    cur.execute("CREATE DATABASE IF NOT EXISTS pokedex_db;")
    cur.execute("USE pokedex_db;")

    tables = ["PokemonWeakness", "PokemonType", "Evolution", "Weakness", "Type", "Pokemon", "Candy", "Egg"]

    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table};")

    cur.execute("""
        CREATE TABLE Candy (
            candy_id INT AUTO_INCREMENT,
            name VARCHAR(50) NOT NULL,
            candy_count INT NULL,
            PRIMARY KEY (candy_id)
        );
    """)

    cur.execute("""
        CREATE TABLE Egg (
            egg_id INT AUTO_INCREMENT,
            distance_km DECIMAL(4,1) NOT NULL,
            PRIMARY KEY (egg_id)
        );
    """)

    cur.execute("""
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
    """)

    cur.execute("""
        CREATE TABLE Type (
            type_id INT AUTO_INCREMENT,
            type_name VARCHAR(30) NOT NULL UNIQUE,
            PRIMARY KEY (type_id)
        );
    """)

    cur.execute("""
        CREATE TABLE PokemonType (
            pokemon_id INT NOT NULL,
            type_id INT NOT NULL,
            PRIMARY KEY (pokemon_id, type_id),
            FOREIGN KEY (pokemon_id) REFERENCES Pokemon(pokemon_id),
            FOREIGN KEY (type_id) REFERENCES Type(type_id)
        );
    """)

    cur.execute("""
        CREATE TABLE Weakness (
            weakness_id INT AUTO_INCREMENT,
            weakness_name VARCHAR(30) NOT NULL UNIQUE,
            PRIMARY KEY (weakness_id)
        );
    """)

    cur.execute("""
        CREATE TABLE PokemonWeakness (
            pokemon_id INT NOT NULL,
            weakness_id INT NOT NULL,
            PRIMARY KEY (pokemon_id, weakness_id),
            FOREIGN KEY (pokemon_id) REFERENCES Pokemon(pokemon_id),
            FOREIGN KEY (weakness_id) REFERENCES Weakness(weakness_id)
        );
    """)

    cur.execute("""
        CREATE TABLE Evolution (
            evolution_id INT AUTO_INCREMENT,
            from_pokemon_id INT NOT NULL,
            to_pokemon_id INT NOT NULL,
            cost INT NULL, 
            PRIMARY KEY (evolution_id),
            FOREIGN KEY (from_pokemon_id) REFERENCES Pokemon(pokemon_id),
            FOREIGN KEY (to_pokemon_id) REFERENCES Pokemon(pokemon_id)
        );
    """)

    print("Database and tables created.")

def parse_json(filename):
    f = open(filename, "r", encoding="utf-8")
    data = json.load(f)
    f.close()
    return data["pokemon"]

def clean_name(name):
    return re.sub(r'\s*\(.*\)\s*|[♂♀]', '', name).strip()


def insert_data(cur, pokemon_list):
    candy_map = {}
    egg_map = {}
    type_map = {}
    weak_map = {}
    poke_map = {}
    evolution_cost_data = {} 

    for p in pokemon_list:
        candy_id = None

        if "candy" in p and p["candy"]:
            name = p["candy"]

            if name not in candy_map:
                cur.execute("INSERT INTO Candy (name, candy_count) VALUES (%s, %s)", (name, p.get("candy_count")))
                cur.execute("SELECT LAST_INSERT_ID()")
                candy_id = cur.fetchone()[0]
                candy_map[name] = candy_id
            else:
                candy_id = candy_map[name]

        egg_id = None
        egg_str = p.get("egg", "Unknown")

        if egg_str and "km" in egg_str:
            distance = float(egg_str.split()[0])

            if distance not in egg_map:
                cur.execute("INSERT INTO Egg (distance_km) VALUES (%s)", (distance,))
                cur.execute("SELECT LAST_INSERT_ID()")
                egg_id = cur.fetchone()[0]
                egg_map[distance] = egg_id
            else:
                egg_id = egg_map[distance]

        height = float(p["height"].split()[0])
        weight = float(p["weight"].split()[0])
        
        if "candy_count" in p and p.get("candy_count") is not None:
            evolution_cost_data[p["name"]] = p["candy_count"]

        cur.execute("""
            INSERT INTO Pokemon (num, name, img_url, height_m, weight_kg, spawn_chance, avg_spawns, spawn_time, candy_id, egg_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """, 
            (p["num"], p["name"], p["img"], height, weight, p["spawn_chance"], p["avg_spawns"], p["spawn_time"], candy_id, egg_id))

        cur.execute("SELECT LAST_INSERT_ID()")
        pokemon_id = cur.fetchone()[0]
        poke_map[p["num"]] = pokemon_id

        for t in p["type"]:
            if t not in type_map:
                cur.execute("INSERT INTO Type (type_name) VALUES (%s)", (t,))
                cur.execute("SELECT LAST_INSERT_ID()")
                type_map[t] = cur.fetchone()[0]
            cur.execute("INSERT INTO PokemonType (pokemon_id, type_id) VALUES (%s, %s)", (pokemon_id, type_map[t]))

        for w in p["weaknesses"]:
            if w not in weak_map:
                cur.execute("INSERT INTO Weakness (weakness_name) VALUES (%s)", (w,))
                cur.execute("SELECT LAST_INSERT_ID()")
                weak_map[w] = cur.fetchone()[0]
            cur.execute("INSERT INTO PokemonWeakness (pokemon_id, weakness_id) VALUES (%s, %s)", (pokemon_id, weak_map[w]))

    for p in pokemon_list:
        from_num = p["num"]
        from_id = poke_map[from_num]
        
        if "next_evolution" in p:
            for evo in p["next_evolution"]:
                to_id = poke_map.get(evo["num"])
                if to_id:
                    cur.execute("INSERT INTO Evolution (from_pokemon_id, to_pokemon_id) VALUES (%s, %s)", (from_id, to_id))

    for p in pokemon_list:
        current_poke_name = p["name"]
        current_poke_id = poke_map[p["num"]]
        
        if "candy_count" in p and p.get("candy_count") is not None and "next_evolution" in p:
            cost = p["candy_count"]
            
            cur.execute("""
                UPDATE Evolution 
                SET cost = %s 
                WHERE from_pokemon_id = %s
            """, (cost, current_poke_id))


if __name__ == "__main__":
    cnx = get_connection()
    cur = cnx.cursor()

    print("Connected to AWS instance.")
    setup_db(cur)

    print("Parsing and inserting data into database...")
    data = parse_json("pokedex.json")
    insert_data(cur, data)

    cnx.commit()
    cur.close()
    cnx.close()
    print("Connection closed.")