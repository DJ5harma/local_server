import os
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
from sv30config import RESULTS_FOLDER, GRAPHS_FOLDER

METRICS_JSON = os.path.join(RESULTS_FOLDER, "sv30_metrics.json")

def generate_graphs():
    """
    Generate visualization graphs from metrics
    
    Creates two plots:
    1. Sludge height vs time
    2. Instantaneous velocity vs time
    
    Saves as PNG files in graphs folder
    """
    print(f"\n[GRAPHS] Starting")
    print(f"  Input: {METRICS_JSON}")
    print(f"  Output: {GRAPHS_FOLDER}\n")
    
    if not os.path.exists(METRICS_JSON):
        print("[ERROR] Metrics JSON not found")
        return
    
    try:
        with open(METRICS_JSON, "r") as f:
            data = json.load(f)
    except:
        print("[ERROR] Failed to read metrics JSON")
        return
    
    if not data:
        print("[ERROR] Metrics JSON is empty")
        return
    
    # Extract data series
    times = [d["time_sec"] / 60 for d in data]  # Convert to minutes
    sludge_heights = [d["sludge_height_px"] for d in data]
    sv30_values = [d["sv30_pct"] for d in data]
    inst_velocities = [d["inst_velocity_pct_per_sec"] for d in data]
    avg_velocities = [d["avg_velocity_pct_per_sec"] for d in data]
    
    # ===== GRAPH 1: Sludge Height vs Time =====
    plt.figure(figsize=(10, 6))
    plt.plot(times, sludge_heights, 'b-', linewidth=2, marker='o', markersize=4)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Sludge Height (pixels)', fontsize=12)
    plt.title('Sludge Height vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    height_graph_path = os.path.join(GRAPHS_FOLDER, "sludge_height_vs_time.png")
    plt.savefig(height_graph_path, dpi=150)
    plt.close()
    print(f"  [OK] Saved: sludge_height_vs_time.png")
    
    # ===== GRAPH 2: SV30 vs Time =====
    plt.figure(figsize=(10, 6))
    plt.plot(times, sv30_values, 'g-', linewidth=2, marker='s', markersize=4)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('SV30 (%)', fontsize=12)
    plt.title('SV30 Value vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    sv30_graph_path = os.path.join(GRAPHS_FOLDER, "sv30_vs_time.png")
    plt.savefig(sv30_graph_path, dpi=150)
    plt.close()
    print(f"  [OK] Saved: sv30_vs_time.png")
    
    # ===== GRAPH 3: Instantaneous Velocity vs Time =====
    plt.figure(figsize=(10, 6))
    plt.plot(times, inst_velocities, 'r-', linewidth=2, marker='^', markersize=4)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Instantaneous Velocity (%/sec)', fontsize=12)
    plt.title('Instantaneous Settling Velocity vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    inst_vel_graph_path = os.path.join(GRAPHS_FOLDER, "inst_velocity_vs_time.png")
    plt.savefig(inst_vel_graph_path, dpi=150)
    plt.close()
    print(f"  [OK] Saved: inst_velocity_vs_time.png")
    
    # ===== GRAPH 4: Average Velocity vs Time =====
    plt.figure(figsize=(10, 6))
    plt.plot(times, avg_velocities, 'm-', linewidth=2, marker='d', markersize=4)
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Average Velocity (%/sec)', fontsize=12)
    plt.title('Average Settling Velocity vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    plt.tight_layout()
    
    avg_vel_graph_path = os.path.join(GRAPHS_FOLDER, "avg_velocity_vs_time.png")
    plt.savefig(avg_vel_graph_path, dpi=150)
    plt.close()
    print(f"  [OK] Saved: avg_velocity_vs_time.png")
    
    # ===== GRAPH 5: Combined Dashboard View =====
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Sludge Height
    ax1.plot(times, sludge_heights, 'b-', linewidth=2, marker='o', markersize=3)
    ax1.set_xlabel('Time (min)')
    ax1.set_ylabel('Height (px)')
    ax1.set_title('Sludge Height')
    ax1.grid(True, alpha=0.3)
    
    # SV30
    ax2.plot(times, sv30_values, 'g-', linewidth=2, marker='s', markersize=3)
    ax2.set_xlabel('Time (min)')
    ax2.set_ylabel('SV30 (%)')
    ax2.set_title('SV30 Value')
    ax2.grid(True, alpha=0.3)
    
    # Instantaneous Velocity
    ax3.plot(times, inst_velocities, 'r-', linewidth=2, marker='^', markersize=3)
    ax3.set_xlabel('Time (min)')
    ax3.set_ylabel('Velocity (%/sec)')
    ax3.set_title('Instantaneous Velocity')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # Average Velocity
    ax4.plot(times, avg_velocities, 'm-', linewidth=2, marker='d', markersize=3)
    ax4.set_xlabel('Time (min)')
    ax4.set_ylabel('Velocity (%/sec)')
    ax4.set_title('Average Velocity')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    plt.suptitle('SV30 Test Results - Complete Dashboard', fontsize=16, fontweight='bold')
    plt.tight_layout()
    
    dashboard_path = os.path.join(GRAPHS_FOLDER, "dashboard_combined.png")
    plt.savefig(dashboard_path, dpi=150)
    plt.close()
    print(f"  [OK] Saved: dashboard_combined.png")
    
    print(f"\n[GRAPHS] Complete - 5 graphs generated\n")

if __name__ == "__main__":
    generate_graphs()
