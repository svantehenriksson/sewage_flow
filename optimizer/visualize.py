#!/usr/bin/env python3
"""
Visualize water pump optimization results
"""

import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import numpy as np


def load_results(filename='optimization_result.json'):
    """Load optimization results from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)


def visualize_results(results):
    """Create comprehensive visualization of optimization results."""
    
    schedule = results['schedule']
    
    # Extract data
    intervals = [item['interval'] for item in schedule]
    dates = [datetime.fromisoformat(item['date'].replace('Z', '+00:00')) for item in schedule]
    water_levels = [item['water_level_start_m'] for item in schedule]
    water_levels.append(schedule[-1]['water_level_end_m'])  # Add final level
    
    volumes = [item['volume_start_m3'] for item in schedule]
    volumes.append(schedule[-1]['volume_end_m3'])
    
    inflows = [item['inflow_m3'] for item in schedule]
    outflows = [item['outflow_m3'] for item in schedule]
    prices = [item['electricity_price_eur_per_kwh'] for item in schedule]
    costs = [item['interval_cost_eur'] for item in schedule]
    
    # Extract pump schedules
    pump_names = ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '2.3', '2.4']
    pump_schedules = {pump: [] for pump in pump_names}
    
    for item in schedule:
        active = item['active_pumps']
        for pump in pump_names:
            pump_schedules[pump].append(1 if pump in active else 0)
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(5, 1, hspace=0.3, height_ratios=[1.2, 1, 1, 0.8, 1])
    
    # Color scheme
    colors = {
        '1.1': '#FF6B6B', '1.2': '#4ECDC4', '1.3': '#45B7D1', '1.4': '#96CEB4',
        '2.1': '#FFEAA7', '2.2': '#DFE6E9', '2.3': '#74B9FF', '2.4': '#A29BFE'
    }
    
    # ============================================================
    # Subplot 1: Water Level and Volume
    # ============================================================
    ax1 = fig.add_subplot(gs[0])
    
    # Plot water level
    ax1.plot(intervals + [len(intervals)], water_levels, 'b-', linewidth=2, label='Water Level')
    ax1.axhline(y=0.5, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='Low Level Threshold (0.5m)')
    ax1.axhline(y=0.0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Min Level (0m)')
    ax1.axhline(y=8.0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Max Level (8m)')
    ax1.fill_between(intervals + [len(intervals)], 0, water_levels, alpha=0.3, color='blue')
    
    ax1.set_ylabel('Water Level (m)', fontsize=11, fontweight='bold')
    ax1.set_title(f'Water Pump Optimization Results (48 Hours)\nTotal Cost: €{results["total_cost_eur"]:.2f}', 
                  fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left', fontsize=9)
    ax1.set_xlim(0, len(intervals))
    
    # Add volume on secondary y-axis
    ax1b = ax1.twinx()
    ax1b.plot(intervals + [len(intervals)], volumes, 'g--', linewidth=1.5, alpha=0.6, label='Volume')
    ax1b.set_ylabel('Volume (m³)', fontsize=11, fontweight='bold', color='green')
    ax1b.tick_params(axis='y', labelcolor='green')
    ax1b.legend(loc='upper right', fontsize=9)
    
    # ============================================================
    # Subplot 2: Pump Schedule (Stacked Area)
    # ============================================================
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    
    # Create stacked area chart
    bottom = np.zeros(len(intervals))
    for pump in pump_names:
        values = np.array(pump_schedules[pump])
        ax2.fill_between(intervals, bottom, bottom + values, 
                         label=f'Pump {pump}', alpha=0.8, color=colors[pump])
        bottom += values
    
    ax2.set_ylabel('Active Pumps', fontsize=11, fontweight='bold')
    ax2.set_title('Pump Schedule (Stacked)', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', ncol=4, fontsize=8, framealpha=0.9)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xlim(0, len(intervals))
    ax2.set_ylim(0, max(bottom) + 0.5)
    
    # ============================================================
    # Subplot 3: Individual Pump Schedules (Gantt-style)
    # ============================================================
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    
    for idx, pump in enumerate(pump_names):
        schedule_data = pump_schedules[pump]
        y_pos = idx
        
        # Find continuous segments
        segments = []
        start = None
        for i, active in enumerate(schedule_data):
            if active and start is None:
                start = i
            elif not active and start is not None:
                segments.append((start, i - start))
                start = None
        if start is not None:
            segments.append((start, len(schedule_data) - start))
        
        # Draw segments
        for seg_start, seg_width in segments:
            ax3.barh(y_pos, seg_width, left=seg_start, height=0.8, 
                    color=colors[pump], alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax3.set_yticks(range(len(pump_names)))
    ax3.set_yticklabels([f'Pump {p}' for p in pump_names])
    ax3.set_ylabel('Pumps', fontsize=11, fontweight='bold')
    ax3.set_title('Pump Schedule (Timeline)', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='x')
    ax3.set_xlim(0, len(intervals))
    
    # ============================================================
    # Subplot 4: Electricity Price
    # ============================================================
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    
    ax4.fill_between(intervals, prices, alpha=0.4, color='blue', label='Electricity Price')
    ax4.plot(intervals, prices, 'b-', linewidth=1.5)
    ax4.set_ylabel('Price (€/kWh)', fontsize=11, fontweight='bold')
    ax4.set_title('Electricity Price', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=9)
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, len(intervals))
    
    # ============================================================
    # Subplot 5: Flow and Cost
    # ============================================================
    ax5 = fig.add_subplot(gs[4], sharex=ax1)
    
    x = np.array(intervals)
    ax5.bar(x - 0.2, inflows, width=0.4, alpha=0.7, color='green', label='Inflow')
    ax5.bar(x + 0.2, [-o for o in outflows], width=0.4, alpha=0.7, color='red', label='Outflow')
    ax5.axhline(y=0, color='black', linewidth=0.8)
    
    ax5.set_ylabel('Flow (m³/15min)', fontsize=11, fontweight='bold')
    ax5.set_xlabel('Time Interval (15 minutes each)', fontsize=11, fontweight='bold')
    ax5.set_title('Water Inflow vs Outflow', fontsize=12, fontweight='bold')
    ax5.legend(loc='upper left', fontsize=9)
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(0, len(intervals))
    
    # Add cost on secondary y-axis
    ax5b = ax5.twinx()
    ax5b.plot(intervals, costs, 'orange', linewidth=2, marker='o', markersize=2, 
             alpha=0.7, label='Interval Cost')
    ax5b.set_ylabel('Cost (€/15min)', fontsize=11, fontweight='bold', color='orange')
    ax5b.tick_params(axis='y', labelcolor='orange')
    ax5b.legend(loc='upper right', fontsize=9)
    
    # Format x-axis with time labels (every 12 intervals = 3 hours)
    tick_positions = range(0, len(intervals) + 1, 12)
    tick_labels = [f'{i//4}h' for i in tick_positions]
    ax5.set_xticks(tick_positions)
    ax5.set_xticklabels(tick_labels, rotation=45)
    
    plt.tight_layout()
    
    # Save figure
    output_file = 'optimization_visualization.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Visualization saved to {output_file}")
    
    # Don't show interactively to avoid GUI issues
    plt.close(fig)
    
    return output_file


def print_statistics(results):
    """Print summary statistics."""
    schedule = results['schedule']
    
    print("\n" + "="*70)
    print("OPTIMIZATION STATISTICS")
    print("="*70)
    
    print(f"\nTotal Cost: €{results['total_cost_eur']:.2f}")
    print(f"Initial Water Level: {results['initial_water_level_m']:.2f} m")
    print(f"Initial Volume: {results['initial_volume_m3']:.0f} m³")
    
    # Calculate statistics
    total_inflow = sum(item['inflow_m3'] for item in schedule)
    total_outflow = sum(item['outflow_m3'] for item in schedule)
    min_level = min(item['water_level_start_m'] for item in schedule)
    max_level = max(item['water_level_start_m'] for item in schedule)
    avg_cost = np.mean([item['interval_cost_eur'] for item in schedule])
    
    print(f"\nTotal Inflow: {total_inflow:,.0f} m³")
    print(f"Total Outflow: {total_outflow:,.0f} m³")
    print(f"Net Change: {total_inflow - total_outflow:,.0f} m³")
    print(f"\nWater Level Range: {min_level:.2f} m - {max_level:.2f} m")
    print(f"Average Cost per Interval: €{avg_cost:.2f}")
    
    # Cost breakdown by hour
    hourly_costs = []
    for i in range(0, len(schedule), 4):
        hour_cost = sum(schedule[j]['interval_cost_eur'] for j in range(i, min(i+4, len(schedule))))
        hourly_costs.append(hour_cost)
    
    print(f"\nHourly Cost - Min: €{min(hourly_costs):.2f}, Max: €{max(hourly_costs):.2f}, Avg: €{np.mean(hourly_costs):.2f}")
    
    # Find most expensive and cheapest hours
    most_expensive_hour = np.argmax(hourly_costs)
    cheapest_hour = np.argmin(hourly_costs)
    
    print(f"Most Expensive Hour: {most_expensive_hour} (€{hourly_costs[most_expensive_hour]:.2f})")
    print(f"Cheapest Hour: {cheapest_hour} (€{hourly_costs[cheapest_hour]:.2f})")
    
    # Pump usage
    print("\n" + "-"*70)
    print("PUMP USAGE")
    print("-"*70)
    
    pump_hours = {}
    pump_names = ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '2.3', '2.4']
    for pump in pump_names:
        hours = sum(1 for item in schedule if pump in item['active_pumps']) * 0.25
        pump_hours[pump] = hours
        pct = (hours / 48) * 100
        print(f"Pump {pump}: {hours:6.2f} hours ({pct:5.1f}%)")
    
    print("\n" + "="*70)


def main():
    """Main entry point."""
    print("Loading optimization results...")
    results = load_results()
    
    print_statistics(results)
    
    print("\nGenerating visualization...")
    visualize_results(results)
    
    print("\n✓ Visualization complete!")


if __name__ == '__main__':
    main()

