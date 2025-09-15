"""
popular_routes.py

Build block-to-block travel time graphs by hour and weekday and stimulate possible multi-stop 
tourist routes and compute total travel times.

Author: eknar31
Date: 2025-03-21
"""

import pandas as pd
import networkx as nx


# ========== CONFIGURATION ========== #

# Input file path
TAXI_BLOCKS_CSV = "output/manhattan_taxi_blocks.csv"

# Output file paths
ROUTES_CSV = "output/popular_routes.csv"

# Parameters
TARGET_NODES = ['10113001008', '10076001001', '10143001021']  # Times Square, Empire State, MET
DAYS_OF_WEEK = ['Monday', 'Saturday']
HOURS = list(range(10, 22))  # 10 AM – 9 PM
POSSIBLE_ROUTES = [
    ['10113001008', '10076001001', '10143001021'], # Route 1: Times Square -> Empire State -> MET
    ['10113001008', '10143001021', '10076001001'], # Route 2: Times Square -> MET -> Empire State
    ['10076001001', '10113001008', '10143001021'], # Route 3: Empire State -> Times Square -> MET
    ['10076001001', '10143001021', '10113001008'], # Route 4: Empire State -> MET -> Times Square
    ['10143001021', '10113001008', '10076001001'], # Route 5: MET -> Times Square -> Empire State
    ['10143001021', '10076001001', '10113001008'], # Route 6: MET -> Empire State -> Times Square
]
START_TIMES = [10, 12, 14, 16]  # Possible tour starting hours


# ========== MAIN FUNCTIONS ========== #

def load_data():
    """Load and preprocess taxi trip data."""
    print("Loading taxi trip data...")
    df = pd.read_csv(TAXI_BLOCKS_CSV)
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'], errors='coerce')
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'], errors='coerce')

    # Format block IDs
    for col in ['BCTCB2010_x', 'BCTCB2010_y']:
        df[col] = df[col].apply(
            lambda x: str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)
        ).str.strip()

    # Calculate travel time (minutes)
    df['travel_time'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0
    df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
    df['pickup_day'] = df['tpep_pickup_datetime'].dt.day_name()
    return df


def compute_mean_coords(df):
    """Compute mean latitude/longitude for each block."""
    combined_coords = pd.concat([
        df[['BCTCB2010_x', 'pickup_latitude', 'pickup_longitude']]
        .rename(columns={'BCTCB2010_x': 'BCTCB2010', 'pickup_latitude': 'latitude', 'pickup_longitude': 'longitude'}),
        df[['BCTCB2010_y', 'dropoff_latitude', 'dropoff_longitude']]
        .rename(columns={'BCTCB2010_y': 'BCTCB2010', 'dropoff_latitude': 'latitude', 'dropoff_longitude': 'longitude'})
    ])
    return combined_coords.groupby('BCTCB2010').agg(
        mean_latitude=('latitude', 'mean'),
        mean_longitude=('longitude', 'mean')
    ).reset_index()


def build_graphs(df, mean_coords):
    """Build hourly taxi route graphs by day of week."""
    # Merge mean coordinates
    df = df.merge(mean_coords, left_on='BCTCB2010_x', right_on='BCTCB2010', how='left').drop(columns=['BCTCB2010'])
    df = df.merge(mean_coords, left_on='BCTCB2010_y', right_on='BCTCB2010', how='left', suffixes=('_x', '_y')).drop(columns=['BCTCB2010'])

    # Route stats
    route_stats = df.groupby(['pickup_hour', 'pickup_day', 'BCTCB2010_x', 'BCTCB2010_y']).agg(
        avg_travel_time=('travel_time', 'mean'),
        trip_count=('BCTCB2010_x', 'count')
    ).reset_index()

    # Unique block positions
    unique_blocks = pd.concat([
        df[['BCTCB2010_x', 'mean_latitude_x', 'mean_longitude_x']]
        .rename(columns={'BCTCB2010_x': 'block_id', 'mean_latitude_x': 'lat', 'mean_longitude_x': 'lng'}),
        df[['BCTCB2010_y', 'mean_latitude_y', 'mean_longitude_y']]
        .rename(columns={'BCTCB2010_y': 'block_id', 'mean_latitude_y': 'lat', 'mean_longitude_y': 'lng'})
    ]).drop_duplicates()
    block_positions = {row['block_id']: (row['lng'], row['lat']) for _, row in unique_blocks.iterrows()}

    graphs = {}



def calculate_route_time(route, start_time, day, graphs):
    """Simulate travel along a route, returning time on road and arrival times."""
    total_time, time_on_road, arrival_times = 0, 0, [start_time]

    for i in range(len(route) - 1):
        from_block, to_block = route[i], route[i + 1]
        current_hour = int(start_time + (total_time // 60)) % 24
        graph_key = f"{current_hour}_{day}"
        G = graphs.get(graph_key)

        if not G:
            return None, None

        path_time = nx.dijkstra_path_length(G, from_block, to_block, weight='weight')
        total_time += path_time
        time_on_road += path_time

        # Add visit times
        if to_block == '10113001008':  # Times Square
            total_time += 30
        elif to_block == '10076001001':  # Empire State
            total_time += 120
        elif to_block == '10143001021':  # MET
            total_time += 180

        arrival_times.append((start_time + (total_time // 60)) % 24)

    return time_on_road, arrival_times


def evaluate_routes(graphs):
    """Evaluate all possible routes for given start times and days."""
    route_info = []
    for start_time in START_TIMES:
        for day in DAYS_OF_WEEK:
            for idx, route in enumerate(POSSIBLE_ROUTES, start=1):
                time_on_road, arrivals = calculate_route_time(route, start_time, day, graphs)
                if time_on_road is not None:
                    route_info.append(
                        [f"Route {idx}", start_time, day, round(time_on_road, 2)] + arrivals
                    )
    return pd.DataFrame(
        route_info,
        columns=['route_name', 'start_time', 'day', 'total_time',
                 'arrival_time_1', 'arrival_time_2', 'arrival_time_3']
    )


# ========== MAIN ========== #

def main():
    df = load_data()
    mean_coords = compute_mean_coords(df)
    graphs, degrees_df = build_graphs(df, mean_coords)


    # Evaluate routes
    routes_df = evaluate_routes(graphs)
    routes_df.to_csv(ROUTES_CSV, index=False)
    print(f"Popular routes saved to {ROUTES_CSV}")


if __name__ == "__main__":
    main()
