# Pokédex Database and Visualization Dashboard

This project normalizes First-Generation Pokédex JSON dataset and visualizes key metrics using a Dash application connected to an AWS RDS MySQL instance.

## Project Summary

| Component | Description | Technologies |
| :--: | :--: | :--: |
| **Data Source** | Public Pokémon Go Pokedex JSON dataset (151 Pokémon) | JSON |
| **Database** | Fully normalized, 8-table relational schema hosted on AWS RDS | MySQL, AWS RDS |
| **Ingestion Script** | Python script to create the schema, parse JSON, and populate all tables while enforcing referential integrity | Python (pymysql, json) |
| **Visualization** | Interactive dashboard providing dynamic access to Pokémon data | Python (Dash, Plotly, pandas, SQLAlchemy) |

## Database Normalization and Schema

The original nested JSON data was normalized up to Third Normal Form (3NF) to ensure data integrity and avoid redundancy.  

The final schema consists of 8 tables enforcing complex many-to-many relationships, as illustrated in the presentation:

- Core Tables: Pokemon, Candy, Egg, Type, Weakness, Evolution
- Junction Tables: PokemonType, PokemonWeakness

### Schema Highlight (Evolution Fix)

The Evolution table was specifically designed with the final visualization in mind and includes a cost column to store the required candy count to trigger the evolution, fulfilling the Key Performance Indicator (KPI) requirement:

```sql
CREATE TABLE Evolution (
    evolution_id INT AUTO_INCREMENT,
    from_pokemon_id INT NOT NULL,
    to_pokemon_id INT NOT NULL,
    cost INT NULL,
    PRIMARY KEY (evolution_id),
    FOREIGN KEY (from_pokemon_id) REFERENCES Pokemon(pokemon_id),
    FOREIGN KEY (to_pokemon_id) REFERENCES Pokemon(pokemon_id)
);
```

## Dashboard Visualization

The Python/Dash application presents 5 interactive components that update dynamically based on the selected Pokémon:  

1. Profile Card: Displays the Pokémon image, name, and Pokédex number
2. Key Stats (KPIs): Shows atomic numerical data (Height, Weight, Egg Distance, Evolution Candy Cost)  
3. Type Composition (Pie Chart): Visualizes the Pokémon's type(s)  
4. Type Distribution (Bar Chart): Displays the total count of Pokémon for each type in the database  
5. Evolution Path (Flow Chart): Shows the full evolutionary chain from the root form through all intermediate stages, complete with images and arrows  

## Setup and Execution

To run the full project:

### Database Setup

1. Open `milestone2-pokedex-database.py`
2. Fill in the host, user, and password fields in the get_connection() function to point to your AWS RDS MySQL instance
3. Run `python milestone2-pokedex-database.py` to create the pokedex_db, set up all 8 tables, and populate them with the parsed data from pokedex.json, including all KPI and cost data

### Dashboard Launch

1. Make sure all Python libraries are installed using our `requirements.txt` file:

```bash
pip install -r requirements.txt
```

2. Run the main dashboard script:

```bash
python milestone3-pokedex-dashboard.py
```

3. Access the dashboard in your web browser at http://127.0.0.1:8050/

## Contributions

This final project was created by:

[Shawn Acheampong (shawnachie)](https://github.com/shawnachie)  
[Brooks Jackson (bjaxqq)](https://github.com/bjaxqq)  
[Eric May (ericmay33)](https://github.com/ericmay33)