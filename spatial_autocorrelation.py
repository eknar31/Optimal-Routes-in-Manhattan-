"""
spatial_autocorrelation.py

Performs spatial autocorrelation analysis (Local and Global Moran's I)
on NYC taxi trip counts aggregated by Manhattan census blocks.

Generates a cluster map to visualize spatial patterns of taxi activity.

Author: eknar31
Date: 2025-03-21
"""

import os
import pandas as pd
import geopandas as gpd
import esda
from libpysal.weights import DistanceBand
import matplotlib.pyplot as plt


# ========== CONFIGURATION ========== #

# Input file paths
BLOCKS_SHP = "data/nycb2010_25a/nycb2010.shp"
PICKUP_CSV = "data/pickup_blocks_sample.csv"
DROPOFF_CSV = "data/dropoff_blocks_sample.csv"

# Output file paths
CLUSTER_MAP_PNG = "output/local_morans_i_clusters.png"


# ========== MAIN FUNCTIONS ========== #

def load_data():
    """Load spatial and taxi data."""
    print("Loading shapefile and taxi block data...")
    blocks = gpd.read_file(BLOCKS_SHP)
    pickup_blocks = pd.read_csv(PICKUP_CSV)
    dropoff_blocks = pd.read_csv(DROPOFF_CSV)
    return blocks, pickup_blocks, dropoff_blocks


def preprocess_data(blocks, pickup_blocks, dropoff_blocks):
    """Aggregate taxi trips and merge with census blocks."""
    # Filter to Manhattan blocks only
    manhattan_blocks = blocks[blocks['BoroName'] == 'Manhattan'].copy()

    # Count pickups and dropoffs per census block
    pickup_counts = pickup_blocks.groupby("BCTCB2010").size().reset_index(name="trip_count_pickup")
    dropoff_counts = dropoff_blocks.groupby("BCTCB2010").size().reset_index(name="trip_count_dropoff")

    # Merge pickup and dropoff counts
    block_connections = pd.merge(
        pickup_counts, dropoff_counts, on="BCTCB2010", how="outer"
    ).fillna(0)

    # Calculate total connections
    block_connections["total_connections"] = block_connections["trip_count_pickup"] + block_connections["trip_count_dropoff"]

    # Fix BCTCB2010 as string for merging
    def fix_block_id(x):
        if isinstance(x, float) and x.is_integer():
            return str(int(x))
        return str(x).strip()

    manhattan_blocks['BCTCB2010'] = manhattan_blocks['BCTCB2010'].apply(fix_block_id)
    block_connections['BCTCB2010'] = block_connections['BCTCB2010'].apply(fix_block_id)

    # Merge counts with spatial data
    manhattan_overall = manhattan_blocks.merge(block_connections, on='BCTCB2010', how='left').fillna({'total_connections': 0})

    return manhattan_overall


def spatial_autocorrelation_analysis(manhattan_overall, threshold=1000):
    """Perform spatial autocorrelation and classify clusters."""

    # Reproject to NYC State Plane (meters)
    manhattan_overall = manhattan_overall.to_crs(epsg=2263)

    # Create spatial weights matrix (distance band within threshold meters)
    w = DistanceBand.from_dataframe(manhattan_overall, threshold=threshold, binary=True, silence_warnings=True)

    # Identify and remove islands (no neighbors)
    islands = [i for i, neighbors in w.neighbors.items() if len(neighbors) == 0]
    manhattan_filtered = manhattan_overall.drop(index=islands)

    # Recalculate weights for filtered data
    w_filtered = DistanceBand.from_dataframe(manhattan_filtered, threshold=threshold, binary=True, silence_warnings=True)

    # Get variable for analysis
    y = manhattan_filtered['total_connections'].values

    # Local Moran's I
    moran_local = esda.Moran_Local(y, w_filtered)

    manhattan_filtered['local_moran'] = moran_local.Is
    manhattan_filtered['p_value'] = moran_local.p_sim

    # Global Moran's I
    moran_global = esda.Moran(y, w_filtered)

    print(f"Global Moran's I: {moran_global.I:.4f}")
    print(f"Global Moran's I p-value: {moran_global.p_sim:.4f}")

    # Cluster classification based on Local Moran's I
    def classify_cluster(row):
        if row['p_value'] < 0.05:
            if row['local_moran'] > 0:
                return 'High-High' if row['total_connections'] > y.mean() else 'Low-Low'
            else:
                return 'Low-High' if row['total_connections'] > y.mean() else 'High-Low'
        else:
            return 'Not Significant'

    manhattan_filtered['cluster_type'] = manhattan_filtered.apply(classify_cluster, axis=1)

    return manhattan_filtered


def plot_clusters(manhattan_filtered, output_path):
    """Plot and save Local Moran's I cluster map."""
    print("Plotting cluster map...")
    fig, ax = plt.subplots(figsize=(10, 10))
    manhattan_filtered.plot(
        column='cluster_type',
        ax=ax,
        legend=True,
        cmap='coolwarm',
        edgecolor='black',
        legend_kwds={'title': "Local Moran's I Cluster Type"}
    )
    ax.set_title("Local Moran's I Clusters for Total Taxi Connections in Manhattan")
    ax.axis('off')

    # Save the figure
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Cluster map saved to {output_path}")


# ========== MAIN ========== #

def main():
    blocks, pickup_blocks, dropoff_blocks = load_data()
    manhattan_overall = preprocess_data(blocks, pickup_blocks, dropoff_blocks)
    manhattan_filtered = spatial_autocorrelation_analysis(manhattan_overall)
    plot_clusters(manhattan_filtered, CLUSTER_MAP_PNG)


if __name__ == "__main__":
    main()
