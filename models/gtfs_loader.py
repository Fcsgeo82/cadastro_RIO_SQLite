import os
import zipfile
import pandas as pd
import streamlit as st
from datetime import datetime

GTFS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "gtfs")

def get_latest_gtfs_path():
    """Retorna o caminho do arquivo .zip mais recente na pasta data/gtfs."""
    if not os.path.exists(GTFS_DIR):
        os.makedirs(GTFS_DIR)
        return None
    
    files = [os.path.join(GTFS_DIR, f) for f in os.listdir(GTFS_DIR) if f.endswith(".zip")]
    if not files:
        return None
    
    # Retorna o arquivo com a data de modificação mais recente
    return max(files, key=os.path.getmtime)

@st.cache_data(ttl=3600, show_spinner="Carregando rotas do GTFS...")
def get_all_gtfs_routes():
    """Retorna um set com todas as rotas (route_short_name) do GTFS mais recente."""
    gtfs_path = get_latest_gtfs_path()
    if not gtfs_path:
        return set()
    try:
        with zipfile.ZipFile(gtfs_path, 'r') as z:
            with z.open('routes.txt') as f:
                routes = pd.read_csv(f, dtype={'route_short_name': str})
            return set(routes['route_short_name'].dropna().unique())
    except Exception as e:
        print(f"Erro ao ler rotas do GTFS: {e}")
        return set()

@st.cache_data(ttl=3600, show_spinner="Carregando dados GTFS...")
def load_gtfs_data(numero_linha: str):
    """
    Carrega dados de shape e horários para uma linha específica do GTFS mais recente.
    numero_linha deve bater com route_short_name.
    """
    gtfs_path = get_latest_gtfs_path()
    if not gtfs_path:
        return None

    try:
        with zipfile.ZipFile(gtfs_path, 'r') as z:
            # 1. Encontrar o route_id
            with z.open('routes.txt') as f:
                routes = pd.read_csv(f, dtype={'route_id': str, 'route_short_name': str})
            
            route = routes[routes['route_short_name'] == str(numero_linha)]
            if route.empty:
                return None
            
            route_id = route.iloc[0]['route_id']
            
            # 2. Carregar Trips para pegar shape_id e service_id
            with z.open('trips.txt') as f:
                trips = pd.read_csv(f, dtype={'route_id': str, 'trip_id': str, 'shape_id': str, 'service_id': str})
            
            route_trips = trips[trips['route_id'] == route_id]
            if route_trips.empty:
                return None
            
            # 3. Carregar Shapes (Geometria)
            shape_ids = route_trips['shape_id'].unique()
            shapes_df = pd.DataFrame()
            if 'shapes.txt' in z.namelist():
                with z.open('shapes.txt') as f:
                    all_shapes = pd.read_csv(f, dtype={'shape_id': str})
                    shapes_df = all_shapes[all_shapes['shape_id'].isin(shape_ids)]
            
            # 4. Carregar Horários (Timetable) e Stops
            # Precisamos de stop_times, stops e calendar
            with z.open('stop_times.txt') as f:
                stop_times = pd.read_csv(f, usecols=['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'], 
                                         dtype={'trip_id': str, 'stop_id': str})
            
            with z.open('stops.txt') as f:
                stops = pd.read_csv(f, dtype={'stop_id': str})
            
            # Merge stop_times com stops para ter nomes
            stop_times = stop_times.merge(stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']], on='stop_id', how='left')
            
            # Filtrar stop_times pelas trips da nossa rota
            route_stop_times = stop_times[stop_times['trip_id'].isin(route_trips['trip_id'])]
            
            # Merge com trips para ter service_id e direction_id
            timetable = route_stop_times.merge(route_trips[['trip_id', 'service_id', 'direction_id', 'trip_headsign']], on='trip_id')
            
            # 5. Carregar Calendar (para saber dias da semana)
            calendar_df = pd.DataFrame()
            if 'calendar.txt' in z.namelist():
                with z.open('calendar.txt') as f:
                    calendar_df = pd.read_csv(f, dtype={'service_id': str})

            # 6. Mapeamento de Shapes por Sentido (para o mapa)
            # Pegamos um shape_id representativo por direction_id
            shape_direction_map = route_trips[['shape_id', 'direction_id', 'trip_headsign']].drop_duplicates('shape_id')

            return {
                "route_info": route.iloc[0].to_dict(),
                "shapes": shapes_df,
                "timetable": timetable,
                "calendar": calendar_df,
                "shape_directions": shape_direction_map,
                "filename": os.path.basename(gtfs_path)
            }

    except Exception as e:
        print(f"Erro ao ler GTFS: {e}")
        return None

def processar_quadro_horario(gtfs_data):
    """
    Processa o timetable bruto para um formato legível de quadro de horários (partidas).
    Geralmente pegamos a primeira parada de cada trip (stop_sequence == 1).
    """
    if gtfs_data is None:
        return pd.DataFrame()
    
    df = gtfs_data["timetable"]
    # Pegar apenas a primeira parada (partida)
    partidas = df[df['stop_sequence'] == 1].copy()
    
    # Se tiver calendar, podemos traduzir service_id para "Dia Útil", "Sábado", "Domingo"
    if not gtfs_data["calendar"].empty:
        cal = gtfs_data["calendar"]
        def identificar_dia(row):
            if row['monday'] == 1 and row['friday'] == 1: return "Dia Útil"
            if row['saturday'] == 1: return "Sábado"
            if row['sunday'] == 1: return "Domingo"
            return "Especial/Outro"
        
        cal['tipo_dia'] = cal.apply(identificar_dia, axis=1)
        partidas = partidas.merge(cal[['service_id', 'tipo_dia']], on='service_id', how='left')
    else:
        partidas['tipo_dia'] = partidas['service_id']

    # Ordenar por sentido e hora
    partidas = partidas.sort_values(by=['direction_id', 'departure_time'])
    
    return partidas[['direction_id', 'trip_headsign', 'departure_time', 'tipo_dia']]
