"""
process_taxi_data.py

Processes NYC Yellow Taxi trip data (Jan 2015), filters trips within NYC,
calculates travel time, and performs spatial joins with NYC census blocks
to assign block info to pickup and dropoff locations.

Author: eknar31
Date: 2025-03-21
"""

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# ========== CONFIGURATION ========== #

# Input file paths 
TAXI_DATA_PATH = "data/yellow_tripdata_2015-01.csv"
BLOCKS_SHP_PATH = "data/nycb2010_25a/nycb2010.shp"

# Output file paths
PICKUP_OUTPUT = "data/pickup_blocks.csv"
DROPOFF_OUTPUT = "data/dropoff_blocks.csv"

# NYC bounding box (approximate)
NYC_BBOX = {
    'min_lon': -74.25909,
    'max_lon': -73.70018,
    'min_lat': 40.477399,
    'max_lat': 40.917577
}


# ========== MAIN FUNCTION ========== #

def main():
    print("Loading NYC Taxi data...")
    taxi_df = pd.read_csv(
        TAXI_DATA_PATH,
        usecols=[
            'pickup_longitude', 'pickup_latitude',
            'dropoff_longitude', 'dropoff_latitude',
            'tpep_pickup_datetime', 'tpep_dropoff_datetime'
        ],
        parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime']
    )

    print(f"Initial rows: {len(taxi_df)}")

    # Filter invalid coordinates
    taxi_df = taxi_df[
        (taxi_df['pickup_longitude'].between(NYC_BBOX['min_lon'], NYC_BBOX['max_lon'])) &
        (taxi_df['pickup_latitude'].between(NYC_BBOX['min_lat'], NYC_BBOX['max_lat'])) &
        (taxi_df['dropoff_longitude'].between(NYC_BBOX['min_lon'], NYC_BBOX['max_lon'])) &
        (taxi_df['dropoff_latitude'].between(NYC_BBOX['min_lat'], NYC_BBOX['max_lat']))
    ]

    taxi_df = taxi_df.dropna(subset=[
        'pickup_longitude', 'pickup_latitude',
        'dropoff_longitude', 'dropoff_latitude'
    ])

    # Calculate travel time in minutes
    taxi_df["travel_time"] = (
        (taxi_df["tpep_dropoff_datetime"] - taxi_df["tpep_pickup_datetime"])
        .dt.total_seconds() / 60.0
    )

    # Filter by reasonable trip durations
    taxi_df = taxi_df[
        (taxi_df["travel_time"] >= 1) &
        (taxi_df["travel_time"] <= 300)
    ]

    print(f"Filtered rows: {len(taxi_df)}")

    # Add unique event ID
    taxi_df['event_id'] = range(len(taxi_df))

    # Load NYC census blocks shapefile
    print("Loading NYC census blocks...")
    blocks = gpd.read_file(BLOCKS_SHP_PATH).to_crs(epsg=4326)

    # Create GeoDataFrames for pickup and dropoff points
    pickup_gdf = gpd.GeoDataFrame(
        taxi_df[['event_id', 'pickup_longitude', 'pickup_latitude', 'tpep_pickup_datetime']],
        geometry=gpd.points_from_xy(taxi_df['pickup_longitude'], taxi_df['pickup_latitude']),
        crs="EPSG:4326"
    )

    dropoff_gdf = gpd.GeoDataFrame(
        taxi_df[['event_id', 'dropoff_longitude', 'dropoff_latitude', 'tpep_dropoff_datetime']],
        geometry=gpd.points_from_xy(taxi_df['dropoff_longitude'], taxi_df['dropoff_latitude']),
        crs="EPSG:4326"
    )

    # Spatial join with census blocks
    print("Performing spatial joins...")
    pickup_blocks = gpd.sjoin(pickup_gdf, blocks, how='left', predicate='within')
    dropoff_blocks = gpd.sjoin(dropoff_gdf, blocks, how='left', predicate='within')

    # Drop geometry columns before saving to CSV
    pickup_blocks = pickup_blocks.drop(columns='geometry')
    dropoff_blocks = dropoff_blocks.drop(columns='geometry')

    # Save sample (or full if small) output
    pickup_blocks.to_csv(PICKUP_OUTPUT, index=False)
    dropoff_blocks.to_csv(DROPOFF_OUTPUT, index=False)

    print(f"Saved pickup_blocks_sample.csv ({len(pickup_blocks)} rows)")
    print(f"Saved dropoff_blocks_sample.csv ({len(dropoff_blocks)} rows)")


# ========== MAIN ========== #

if __name__ == "__main__":
    main()
