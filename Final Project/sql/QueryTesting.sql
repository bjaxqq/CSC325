USE pokedex_db;

SELECT 
    p.pokemon_id, p.num, p.name, 
    p.height_m, p.weight_kg, 
    e.distance_km AS egg_distance,
    evo.cost AS evolution_cost
FROM Pokemon p
LEFT JOIN Egg e ON p.egg_id = e.egg_id
LEFT JOIN Evolution evo ON p.pokemon_id = evo.from_pokemon_id
WHERE p.name = 'Charizard';

SELECT 
    t.type_name, 
    COUNT(pt.pokemon_id) AS type_count
FROM Type t 
JOIN PokemonType pt ON t.type_id = pt.type_id
GROUP BY t.type_name
ORDER BY type_count DESC;

SELECT 
    p_from.name AS from_pokemon, 
    p_to.name AS to_pokemon, 
    e.cost AS candy_cost_required
FROM Evolution e
JOIN Pokemon p_from ON e.from_pokemon_id = p_from.pokemon_id
JOIN Pokemon p_to ON e.to_pokemon_id = p_to.pokemon_id
WHERE p_from.name IN ('Bulbasaur', 'Ivysaur');

SELECT w.weakness_name
FROM Pokemon p
JOIN PokemonWeakness pw ON p.pokemon_id = pw.pokemon_id
JOIN Weakness w ON pw.weakness_id = w.weakness_id
WHERE p.name = 'Charizard';