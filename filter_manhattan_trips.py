"""
filter_manhattan_trips.py

Merges pickup and dropoff block data for NYC taxi trips, filters for trips
within Manhattan only, and exports a cleaned dataset for analysis.

Author: eknar31
Date: 2025-03-21
"""

import pandas as pd
import os

# ========== CONFIGURATION ========== #

# Input file paths 
PICKUP_CSV = "data/pickup_blocks.csv"
DROPOFF_CSV = "data/dropoff_blocks.csv"

#Output file paths
MERGED_CSV = "output/pickup_dropoff_blocks.csv"
MANHATTAN_ONLY_CSV = "output/manhattan_taxi_blocks.csv"


# ========== MAIN FUNCTION ========== #

def main():
    print("Loading pickup and dropoff data...")

    pickup_blocks = pd.read_csv(PICKUP_CSV, parse_dates=['tpep_pickup_datetime'])
    dropoff_blocks = pd.read_csv(DROPOFF_CSV, parse_dates=['tpep_dropoff_datetime'])

    # Merge on event_id
    merged_blocks = pd.merge(
        pickup_blocks,
        dropoff_blocks,
        on="event_id",
        how="outer"
    )

    print("Sample merged data:")
    print(merged_blocks.head())

    # Save full merged data
    os.makedirs("output", exist_ok=True)
    merged_blocks.to_csv(MERGED_CSV, index=False)

    # Filter for Manhattan-to-Manhattan trips
    manhattan_blocks = merged_blocks[
        (merged_blocks['BoroName_x'] == 'Manhattan') &
        (merged_blocks['BoroName_y'] == 'Manhattan')
    ]

    print(f"Number of Manhattan-only trips: {len(manhattan_blocks)}")
    print("Unique pickup boroughs:", merged_blocks['BoroName_x'].unique())
    print("Unique dropoff boroughs:", merged_blocks['BoroName_y'].unique())

    # Select relevant columns
    manhattan_blocks = manhattan_blocks[[
        'event_id',
        'tpep_pickup_datetime', 'BCTCB2010_x', 'pickup_longitude', 'pickup_latitude',
        'tpep_dropoff_datetime', 'BCTCB2010_y', 'dropoff_longitude', 'dropoff_latitude'
    ]]

    # Save Manhattan-only dataset
    manhattan_blocks.to_csv(MANHATTAN_ONLY_CSV, index=False)

    print("Filtered data saved!")


# ========== MAIN ========== #

if __name__ == "__main__":
    main()
