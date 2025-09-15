"""
node_degrees.py

Builds block-to-block travel time graphs by hour and weekday and compute node 
degrees for selected landmarks.

Author: eknar31
Date: 2025-03-21
"""

import os
import pandas as pd
import networkx as nx


# ========== CONFIGURATION ========== #

# Input file path
TAXI_BLOCKS_CSV = "data/pickup_dropoff_blocks.csv"

# Output file path
DEGREES_CSV = "output/degrees.csv"

# Parameters
TARGET_NODES = ['10113001008', '10076001001', '10143001021']  # Times Square, Empire State, MET
DAYS_OF_WEEK = ['Monday', 'Saturday']
HOURS = list(range(10, 22))  # 10 AM – 9 PM


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
    """Build taxi route graphs grouped by hour and weekday."""
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

    return route_stats, block_positions


def compute_node_degrees(route_stats, block_positions):
    """Compute node degrees for target nodes across hours and days."""
    node_degrees = []

    for hour in HOURS:
        for day in DAYS_OF_WEEK:
            filtered = route_stats[(route_stats['pickup_hour'] == hour) & (route_stats['pickup_day'] == day)]
            G = nx.Graph()

            for block_id, (lng, lat) in block_positions.items():
                G.add_node(block_id, pos=(lng, lat))

            for _, row in filtered.iterrows():
                G.add_edge(row['BCTCB2010_x'], row['BCTCB2010_y'], weight=row['avg_travel_time'])

            for node in TARGET_NODES:
                if node in G:
                    node_degrees.append({
                        'graph': f"{hour}_{day}",
                        'node': node,
                        'degree': G.degree(node)
                    })

    return pd.DataFrame(node_degrees)


# ========== MAIN ========== #

def main():
    df = load_data()
    mean_coords = compute_mean_coords(df)
    route_stats, block_positions = build_graphs(df, mean_coords)
    degrees_df = compute_node_degrees(route_stats, block_positions)

    # Save results
    os.makedirs(os.path.dirname(DEGREES_CSV), exist_ok=True)
    degrees_df.to_csv(DEGREES_CSV, index=False)
    print(f"Node degrees saved to {DEGREES_CSV}")


if __name__ == "__main__":
    main()
