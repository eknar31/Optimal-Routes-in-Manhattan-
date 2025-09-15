"""
final_analysis.py

Compares travel times across routes, days, and times and visualizes traffic 
clusters and their impact on routes.


Author: eknar31
Date: 2025-03-21
"""

import os
import itertools
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


# ========== CONFIGURATION ========== #

# Input files
POPULAR_ROUTES_CSV = "output/popular_routes.csv"
DEGREES_CSV = "output/degrees.csv"

# Output folder
OUTPUT_DIR = "output/analysis_plots"

# Route nodes (Times Square, Empire State, MET)
NODES = {
    "TS": "10113001008",   # Times Square
    "ES": "10076001001",   # Empire State
    "MET": "10143001021"   # The MET
}
DAYS = ["Monday", "Saturday"]
START_HOURS = list(range(10, 22))  # 10 AM – 9 PM


# ========== MAIN FUNCTIONS ========== #

def load_data():
    """Load route-level and degree data, preprocess IDs."""
    print("Loading route data...")
    df = pd.read_csv(POPULAR_ROUTES_CSV)

    # Ensure start_time is integer
    if "start_time" in df.columns:
        df["start_time"] = df["start_time"].astype(int)

    # Load degrees 
    print("Loading degree data (if exists)...")
    if os.path.exists(DEGREES_CSV):
        degrees = pd.read_csv(DEGREES_CSV)

        # Split "graph" column into hour + day 
        if "graph" in degrees.columns:
            degrees[["hour", "day"]] = degrees["graph"].str.split("_", expand=True)
            degrees["hour"] = degrees["hour"].astype(int)
        else:
            raise KeyError("Expected 'graph' column in degrees.csv")

    else:
        degrees = None

    return df, degrees


def define_routes():
    """Generate all possible landmark route permutations."""
    nodes = [NODES["TS"], NODES["ES"], NODES["MET"]]
    perms = list(itertools.permutations(nodes, 3))
    return pd.DataFrame(perms, columns=["node1", "node2", "node3"])


def analyze_travel_times(df):
    """Plot and summarize travel times by route and day."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Average travel time by day
    avg_day = df.groupby("day")["total_time"].mean()
    avg_day.plot(kind="bar", title="Average Travel Time by Day")
    plt.ylabel("Minutes")
    plt.savefig(f"{OUTPUT_DIR}/avg_travel_time_by_day.png")
    plt.close()

    # Boxplot of time distributions
    sns.boxplot(x="day", y="total_time", data=df)
    plt.title("Travel Time Distribution by Day")
    plt.savefig(f"{OUTPUT_DIR}/travel_time_boxplot.png")
    plt.close()


def analyze_clusters(df):
    """Explore travel times across cluster-related columns if present."""
    cluster_cols = [c for c in df.columns if "clusterinfo" in c]

    for col in cluster_cols:
        sns.boxplot(x=col, y="total_time", data=df)
        plt.title(f"Travel Time vs {col}")
        plt.savefig(f"{OUTPUT_DIR}/cluster_boxplot_{col}.png")
        plt.close()


def integrate_degrees(df, degrees):
    """Merge degree data into routes and compute averages."""
    if degrees is None:
        print("No degree data available; skipping integration.")
        df["average_degree"] = np.nan
        return df

    # Merge degrees by matching start_time and day
    merged = df.merge(
        degrees,
        left_on=["day", "start_time"],
        right_on=["day", "hour"],
        how="left"
    )

    # Drop duplicate hour column
    merged = merged.drop(columns=["hour"])
    return merged


def compare_travel_vs_congestion(df, degrees):
    """Compare average travel times and congestion across hours and days."""
    if degrees is None:
        print("No degree data available; skipping congestion analysis.")
        return

    avg_times = df.groupby(["day", "start_time"])["total_time"].mean().reset_index()
    avg_degrees = degrees.groupby(["day", "hour"])["degree"].mean().reset_index()

    # Side by side comparison plots
    for day in DAYS:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        subset_time = avg_times[avg_times["day"] == day]
        subset_deg = avg_degrees[avg_degrees["day"] == day]

        axes[0].plot(subset_time["start_time"], subset_time["total_time"], marker="o")
        axes[0].set_title(f"Avg Travel Time ({day})")
        axes[0].set_xlabel("Hour")
        axes[0].set_ylabel("Minutes")

        axes[1].plot(subset_deg["hour"], subset_deg["degree"], marker="o", color="red")
        axes[1].set_title(f"Avg Congestion (Degrees) ({day})")
        axes[1].set_xlabel("Hour")
        axes[1].set_ylabel("Average Degree")

        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/travel_vs_congestion_{day}.png")
        plt.close()


# ========== MAIN ========== #

def main():
    routes_df, degrees_df = load_data()
    routes_def = define_routes()

    analyze_travel_times(routes_df)
    analyze_clusters(routes_df)

    merged_df = integrate_degrees(routes_df, degrees_df)
    compare_travel_vs_congestion(merged_df, degrees_df)

    print(f"Analysis complete. Plots saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
