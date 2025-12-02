import pandas as pd
from sqlalchemy import create_engine, text
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import os 
import sys 
from collections import deque 

DB_HOST = ""
DB_USER = ""
DB_PASS = "" 
DB_NAME = "pokedex_db"

class PokedexDataFetcher:
    def __init__(self):
        self.engine = None

        try:
            host = os.environ.get("DB_HOST", DB_HOST)
            user = os.environ.get("DB_USER", DB_USER)
            password = os.environ.get("DB_PASS", DB_PASS)
            name = os.environ.get("DB_NAME", DB_NAME)

            db_url = f"mysql+pymysql://{user}:{password}@{host}:3306/{name}"
            self.engine = create_engine(db_url)
            
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))

            print("Database connection successful.")
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.engine = None

    def execute_query(self, sql, params=None):
        if not self.engine:
            return pd.DataFrame()
        try:
            return pd.read_sql(text(sql), self.engine, params=params)
        except Exception as e:
            print(f"Database query error: {e}")
            return pd.DataFrame()

    def fetch_all_pokemon_names(self):
        sql = "SELECT name FROM Pokemon ORDER BY pokemon_id"
        df = self.execute_query(sql)
        return df['name'].tolist()

    def fetch_evolution_chain(self, start_name):
        chain = deque()
        seen_names = set()
        root_name = start_name
        current_name = start_name

        while True:
            params = {'p_name': current_name}
            sql_prev = """
                SELECT prev_poke.name AS prev_evolution_name
                FROM Pokemon current_poke
                JOIN Evolution e ON current_poke.pokemon_id = e.to_pokemon_id
                JOIN Pokemon prev_poke ON e.from_pokemon_id = prev_poke.pokemon_id
                WHERE current_poke.name = :p_name
            """
            df_prev = self.execute_query(sql_prev, params)
            if df_prev.empty or df_prev.iloc[0]['prev_evolution_name'] in seen_names:
                break
            
            root_name = df_prev.iloc[0]['prev_evolution_name']
            current_name = root_name
            seen_names.add(root_name)

        chain_list = []
        name_set = set()
        queue = deque([root_name])

        while queue:
            name = queue.popleft()
            
            if name in name_set:
                continue

            name_set.add(name)
            data = self.fetch_pokemon_data(name)

            if data:
                chain_list.append({
                    'name': data['name'], 
                    'num': data['num'], 
                    'img_url': data['img_url'], 
                    'is_current': data['name'] == start_name
                })
                
                params = {'p_name': data['name']}

                sql_next = """
                    SELECT next_poke.name AS next_evolution_name
                    FROM Pokemon current_poke
                    JOIN Evolution e ON current_poke.pokemon_id = e.from_pokemon_id
                    JOIN Pokemon next_poke ON e.to_pokemon_id = next_poke.pokemon_id
                    WHERE current_poke.name = :p_name
                """

                df_next = self.execute_query(sql_next, params)

                for index, row in df_next.iterrows():
                    queue.append(row['next_evolution_name'])

        return chain_list

    def fetch_pokemon_data(self, name):
        if not self.engine or not name:
            return None
            
        params = {'p_name': name}

        sql_core_kpi = """
            SELECT 
                p.pokemon_id, p.num, p.name, 
                COALESCE(p.height_m, 'N/A') AS height_m, 
                COALESCE(p.weight_kg, 'N/A') AS weight_kg, 
                COALESCE(p.candy_id, 'N/A') AS candy_count, 
                COALESCE(p.egg_distance_km, 'N/A') AS egg_distance_km, 
                COALESCE(p.img_url, 'https://via.placeholder.com/200?text=No+Image') AS img_url 
            FROM Pokemon p 
            WHERE p.name = :p_name
        """

        sql_types = """
            SELECT t.type_name
            FROM Pokemon p JOIN PokemonType pt ON p.pokemon_id = pt.pokemon_id
            JOIN Type t ON pt.type_id = t.type_id
            WHERE p.name = :p_name
        """

        sql_weaknesses = """
            SELECT w.weakness_name
            FROM Pokemon p JOIN PokemonWeakness pw ON p.pokemon_id = pw.pokemon_id
            JOIN Weakness w ON pw.weakness_id = w.weakness_id
            WHERE p.name = :p_name
        """

        sql_type_counts = """
            SELECT 
                t.type_name,
                COUNT(pt.pokemon_id) AS type_count
            FROM Type t 
            JOIN PokemonType pt ON t.type_id = pt.type_id
            GROUP BY t.type_name
            ORDER BY type_count DESC
        """

        sql_candy_cost = """
            SELECT COALESCE(e.cost, 'N/A') AS evolution_cost
            FROM Pokemon p
            LEFT JOIN Evolution e ON p.pokemon_id = e.from_pokemon_id
            WHERE p.name = :p_name
            LIMIT 1
        """

        df_core_kpi = self.execute_query(sql_core_kpi, params)

        if df_core_kpi.empty: return None

        core_data = df_core_kpi.iloc[0].to_dict()

        types = self.execute_query(sql_types, params)['type_name'].tolist()
        weaknesses = self.execute_query(sql_weaknesses, params)['weakness_name'].tolist()
        df_type_counts = self.execute_query(sql_type_counts)
        
        df_candy_cost = self.execute_query(sql_candy_cost, params)
        evolution_cost = df_candy_cost.iloc[0]['evolution_cost'] if not df_candy_cost.empty else 'N/A'

        return {
            "name": core_data['name'],
            "num": f"#{core_data['num']}",
            "img_url": core_data['img_url'],
            "height": core_data['height_m'],
            "weight": core_data['weight_kg'],
            "egg_distance": core_data['egg_distance_km'],
            "candy_count": evolution_cost, 
            "types": types,
            "weaknesses": weaknesses,
            "weakness_counts_df": df_type_counts
        }

pokedex_fetcher = PokedexDataFetcher()
ALL_POKEMON_NAMES = pokedex_fetcher.fetch_all_pokemon_names()
DEFAULT_POKEMON = 'Pikachu' if 'Pikachu' in ALL_POKEMON_NAMES else (ALL_POKEMON_NAMES[0] if ALL_POKEMON_NAMES else None)

def create_evolution_flow_elements(data_fetcher, current_name):
    chain = data_fetcher.fetch_evolution_chain(current_name)
    elements = []
    
    def evo_box(item):
        return html.Div([
            html.Img(src=item['img_url'], className='evo-img'),
            html.Div(item['name'], className='evo-name'),
            html.Div(item['num'], className='evo-num')
        ], className=f"evo-box {'current-evo' if item['is_current'] else ''}")

    for i, item in enumerate(chain):
        elements.append(evo_box(item))

        if i < len(chain) - 1:
            elements.append(html.Div(className='evo-arrow'))

    if not elements:
        return html.Div(f"{current_name} has no recorded evolutions.", style={'padding': '20px'})
        
    return html.Div(elements, className='evolution-flow-container')


app = Dash(__name__, suppress_callback_exceptions=True)

POKEDEX_COLORS = {
    'background': '#25292E', 
    'header': '#D54F4F',     
    'card_bg': '#FFFFFF',    
    'text': '#333333',
    'kpi_accent': '#4592C4'  
}

TYPE_COLORS = {
    'NORMAL': '#AAAA99', 'FIGHTING': '#BA5545', 'FLYING': '#A890F0',
    'POISON': '#A040A0', 'GROUND': '#E0C068', 'ROCK': '#B8A038',
    'BUG': '#A8B820', 'GHOST': '#705898', 'STEEL': '#B8B8D0',
    'FIRE': '#FF4422', 'WATER': '#4592C4', 'GRASS': '#78C850',
    'ELECTRIC': '#F8D030', 'PSYCHIC': '#F85888', 'ICE': '#98D8D8',
    'DRAGON': '#7038F8', 'DARK': '#705848', 'FAIRY': '#EE99AC'
}

app.layout = html.Div(
    children=[
        html.Div([
            html.H1("Pokédex Database Visualization", style={'textAlign': 'center', 'margin': '10px 0', 'color': POKEDEX_COLORS['card_bg']}),
            dcc.Dropdown(
                id='pokemon-dropdown',
                options=[{'label': name, 'value': name} for name in ALL_POKEMON_NAMES],
                value=DEFAULT_POKEMON,
                placeholder="Search for a Pokémon...",
                style={'width': '50%', 'margin': '0 auto', 'color': POKEDEX_COLORS['text']}
            ),
        ], style={'textAlign': 'center', 'padding': '15px', 'backgroundColor': POKEDEX_COLORS['header'], 'border': f'3px solid {POKEDEX_COLORS["kpi_accent"]}', 'marginBottom': '20px'}),

        html.Div([
            html.Div([
                html.H3("Profile", className='section-title'),
                html.Img(id='pokemon-image', style={'width': '100%', 'height': 'auto', 'maxWidth': '200px', 'margin': '0 auto', 'paddingTop': '10px'}),
                html.P(id='pokemon-name-num', style={'textAlign': 'center', 'fontSize': '1.2em', 'fontWeight': 'bold', 'paddingTop': '10px'})
            ], className='card', style={'width': '25%', 'height': '380px', 'textAlign': 'center'}),

            html.Div([
                html.H3("Key Stats (KPIs)", className='section-title'),
                html.Div(id='kpi-container', className='kpi-grid')
            ], className='card', style={'width': '25%', 'height': '380px'}),
            
            html.Div([
                html.H3("Type Composition", className='section-title'),
                dcc.Graph(id='type-pie-chart', config={'displayModeBar': False})
            ], className='card', style={'width': '45%', 'height': '380px'}),

        ], className='row-container'),

        html.Div([
            html.Div([
                html.H3("Type Distribution", className='section-title'),
                dcc.Graph(id='weakness-bar-chart', config={'displayModeBar': False})
            ], className='card', style={'width': '45%'}),
            
            html.Div([
                html.H3("Evolution Path", className='section-title'),
                html.Div(id='evolution-flow-container') 
            ], className='card', style={'width': '55%', 'minHeight': '350px', 'align-items': 'center'}),
            
        ], className='row-container'),

    ], 
    style={
        'maxWidth': '1200px', 
        'margin': '0 auto', 
        'fontFamily': 'sans-serif', 
        'backgroundColor': POKEDEX_COLORS['background'], 
        'padding': '0',
        '--card-background': POKEDEX_COLORS['card_bg'],
        '--kpi-color': POKEDEX_COLORS['kpi_accent'],
        '--header-color': POKEDEX_COLORS['header']
    }, 
    className='pokedex-dashboard-layout'
)

@app.callback(
    [
        Output('pokemon-image', 'src'),
        Output('pokemon-name-num', 'children'),
        Output('kpi-container', 'children'),
        Output('type-pie-chart', 'figure'),
        Output('weakness-bar-chart', 'figure'),
        Output('evolution-flow-container', 'children')
    ],
    [Input('pokemon-dropdown', 'value')]
)
def update_dashboard(selected_name):
    if not selected_name or not ALL_POKEMON_NAMES:
        return (
            "https://via.placeholder.com/200?text=Select+Pokemon", 
            "Select a Pokémon", 
            [html.P("N/A")]*4, go.Figure(), go.Figure(), html.Div("N/A")
        )
        
    data = pokedex_fetcher.fetch_pokemon_data(selected_name)
    
    if not data:
        return (
            "https://via.placeholder.com/200?text=Error", 
            f"Error: {selected_name} not found or data missing.", 
            [html.P("Data Error")]*4, go.Figure(), go.Figure(), html.Div("Error")
        )

    def kpi_box(label, value, unit):
        value_str = str(value)
        unit_str = unit if value_str not in ('N/A', '0', '0.0') else ''
        return html.Div([
            html.Div(label, className='kpi-label'),
            html.Div(f"{value_str} {unit_str}", className='kpi-value')
        ], className='kpi-box')

    kpis = [
        kpi_box("HEIGHT", data['height'], "m"),
        kpi_box("WEIGHT", data['weight'], "kg"),
        kpi_box("EGG DISTANCE", data['egg_distance'], "km"),
        kpi_box("CANDY COUNT", data['candy_count'], "units")
    ]
    
    types_df = pd.DataFrame({
        'Type': data['types'], 
        'Proportion': [100/len(data['types'])] * len(data['types'])
    })
    
    pie_fig = px.pie(
        types_df, 
        values='Proportion', 
        names='Type', 
        hole=.5, 
        color='Type',
        color_discrete_map={t: TYPE_COLORS.get(t.upper(), '#6C7A89') for t in data['types']}
    )

    pie_fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0}, 
        showlegend=True, 
        plot_bgcolor=POKEDEX_COLORS['card_bg'], 
        paper_bgcolor=POKEDEX_COLORS['card_bg'],
        uniformtext_minsize=12, 
        uniformtext_mode='hide'
    )
    
    type_counts_df = data['weakness_counts_df'] 
    
    def get_bar_colors(type_name, weaknesses_list):
        if type_name in weaknesses_list:
            return TYPE_COLORS.get(type_name.upper(), POKEDEX_COLORS['header']) 
        return '#BBBBBB' 

    colors = [get_bar_colors(t, data['weaknesses']) for t in type_counts_df['type_name']]
    
    bar_fig = go.Figure(data=[
        go.Bar(
            x=type_counts_df['type_name'], 
            y=type_counts_df['type_count'], 
            marker_color=colors,
            name="Type Count"
        )
    ])
    
    bar_fig.update_layout(
        title='Color = Weakness',
        xaxis_title="Pokémon Type", 
        yaxis_title="# Pokémon with this Type", 
        margin={"t":40,"b":80,"l":50,"r":10}, 
        plot_bgcolor=POKEDEX_COLORS['card_bg'], 
        paper_bgcolor=POKEDEX_COLORS['card_bg'],
        height=300,
        xaxis={'categoryorder':'total descending', 'tickangle': -45}
    )
    
    evolution_flow_elements = create_evolution_flow_elements(pokedex_fetcher, selected_name)

    return (
        data['img_url'],
        f"{data['name']} | {data['num']}",
        kpis,
        pie_fig,
        bar_fig,
        evolution_flow_elements
    )

app.index_string = ''' 
<!DOCTYPE html>
<html>
    <head>
        <title>Pokédex Database Visualization</title>
        <style>
            html, body { 
                margin: 0; 
                padding: 0; 
                height: 100%; 
                width: 100%;
                overflow-x: hidden; 
            }
            
            .pokedex-dashboard-layout { 
                background-color: #25292E !important; 
                padding: 20px; 
                min-height: 100vh; 
                box-sizing: border-box; 
            }
            
            .card { 
                background-color: #FFFFFF; 
                padding: 15px; 
                margin: 10px; 
                border-radius: 4px; 
                box-shadow: 0 0 10px 3px rgba(0, 0, 0, 0.4); 
                border: 2px solid #4592C4; 
                display: flex; 
                flex-direction: column;
                box-sizing: border-box;
                flex-grow: 1;
            }
            .row-container { display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 20px; }
            .section-title { 
                border-bottom: 2px solid #D54F4F; 
                padding-bottom: 5px; 
                margin-top: 0; 
                color: #333333; 
                font-size: 1.1em;
            }
            
            .kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; height: 100%; }
            .kpi-box { 
                background-color: #F0F0F0; 
                border: 1px solid #CCC; 
                padding: 10px; 
                text-align: center; 
                border-radius: 3px; 
                display: flex; 
                flex-direction: column; 
                justify-content: center; 
            }
            .kpi-label { font-size: 0.8em; color: #333333; font-weight: bold; }
            .kpi-value { font-size: 1.5em; font-weight: bold; color: #4592C4; margin-top: 5px; } 
            
            .evolution-flow-container { 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                padding: 10px; 
                height: 100%; 
                overflow-x: auto; 
            }
            .evo-box { 
                min-width: 140px; 
                border: 2px solid #D54F4F; 
                border-radius: 4px;
                padding: 5px;
                text-align: center;
                margin: 0 15px; 
                background-color: #f7f7f7;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            }
            .current-evo { 
                border-color: #4592C4; 
                border-width: 4px; 
                background-color: #e5f0ff; 
            }
            .evo-img { 
                width: 100px; 
                height: auto;
                display: block;
                margin: 0 auto;
            }
            .evo-arrow { 
                display: flex;
                align-items: center;
                justify-content: center;
                color: #D54F4F;
                font-size: 2.5em;
                width: 20px; 
                position: relative;
            }
            .evo-arrow::after {
                content: '→'; 
                position: absolute;
                line-height: 1; 
            }
            .evo-name { font-weight: bold; font-size: 0.9em; line-height: 1.2; }
            .evo-num { font-size: 0.7em; color: #555; }
            
            .modebar-btn[data-title='Connect to Cloud'] {
                display: none !important;
            }

        </style>
        
        <script>
            window.addEventListener('load', function() {
                var cloudButton = document.querySelector('.modebar-btn[data-title="Connect to Cloud"]');
                if (cloudButton) {
                    cloudButton.style.display = 'none';
                }
            });
        </script>

        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    print("\nRunning Dash application...")
    print("Access the dashboard at: http://127.0.0.1:8050/")
    
    app.run(debug=True)