"""
visualize_block_connections_alternative.py

Aggregates NYC Taxi pickup and dropoff data by census block,
then visualizes the total trip connections in Manhattan using Folium.

Author: eknar31
Date: 2025-03-21
"""

import pandas as pd
import geopandas as gpd
import folium
from branca.colormap import linear

# ========== CONFIGURATION ========== #

BLOCKS_SHP = "data/nycb2010_25a/nycb2010.shp" 
PICKUP_CSV = "data/pickup_blocks.csv" 
DROPOFF_CSV = "data/dropoff_blocks.csv" 

OUTPUT_MAP = "output/Manhattan_Block_Connections.html" 
OUTPUT_CSV = "output/manhattan_blocks_aggregated.csv" 
OUTPUT_SHP = "output/manhattan_blocks_aggregated.shp"

MAP_CENTER = [40.7831, -73.9712]

# ========== HELPERS ========== #

def get_color(value, colormap):
    """Return color from colormap."""
    return colormap(value)

# ========== MAIN FUNCTION ========== #

def main():
    # Load Shapefile and Taxi Data
    blocks = gpd.read_file(BLOCKS_SHP).to_crs(epsg=4326)
    manhattan_blocks = blocks[blocks['BoroName'] == 'Manhattan'].copy()
    
    pickup_blocks = pd.read_csv(PICKUP_CSV)
    dropoff_blocks = pd.read_csv(DROPOFF_CSV)
    pickup_blocks["BCTCB2010"] = pickup_blocks["BCTCB2010"].fillna(0).apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")
    dropoff_blocks["BCTCB2010"] = dropoff_blocks["BCTCB2010"].fillna(0).apply(lambda x: str(int(float(x))) if pd.notnull(x) else "")

    # group by block to get trip count
    pickup_counts = pickup_blocks.groupby("BCTCB2010").size().reset_index(name="trip_count")
    dropoff_counts = dropoff_blocks.groupby("BCTCB2010").size().reset_index(name="trip_count")

    # merge pickup_counts and dropoff_counts to get it all in one df
    block_connections = pd.merge(
        pickup_counts, dropoff_counts, on="BCTCB2010", how="outer", suffixes=("_pickup", "_dropoff")
    ).fillna(0)

    # assign "total_connections" with the total pickups and dropoffs in each block
    block_connections["total_connections"] = block_connections["trip_count_pickup"] + block_connections["trip_count_dropoff"]

    # Since there was an issue with line spacing and float numbers, make sure they are of the same type
    manhattan_blocks['BCTCB2010'] = manhattan_blocks['BCTCB2010'].apply(lambda x: str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)).str.strip()
    block_connections['BCTCB2010'] = block_connections['BCTCB2010'].apply(lambda x: str(int(float(x))) if isinstance(x, float) and float(x).is_integer() else str(x)).str.strip()

    # merge manhattan blocks with the block_connections
    manhattan_blocks = manhattan_blocks.merge(block_connections, on='BCTCB2010', how='left').fillna({'total_connections': 0})

    # Creating Map 
    m = folium.Map(location=MAP_CENTER, zoom_start=12)

    # Create a color scale based on total_connections
    max_connections = manhattan_blocks['total_connections'].max()
    colormap = linear.YlOrRd_09.scale(0, max_connections)

    # Add the color scale to the map
    colormap.caption = 'Number of Connections'
    colormap.add_to(m)

    # Add block polygons with color based on number of connections
    for _, row in manhattan_blocks.iterrows():
        color = get_color(row['total_connections'], colormap)
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feature, color=color: {
                'fillColor': color, 'color': 'black', 'weight': 0.5, 'fillOpacity': 0.6
            },
            tooltip=folium.Tooltip(f"Block: {row['BCTCB2010']}<br>Connections: {int(row['total_connections'])}")
        ).add_to(m)

    # Save map to HTML
    m.save(OUTPUT_MAP)
    print("Visualization saved as Manhattan_Block_Connections.html")

    # Save CSV and SHP
    manhattan_blocks.drop(columns=['geometry']).to_csv(OUTPUT_CSV, index=False)
    manhattan_blocks.to_file(OUTPUT_SHP)
    print("Manhattan_blocks saved as csv and shape files")
    print('Code all completed!')

# ========== MAIN ========== #

if __name__ == "__main__":
    main()
