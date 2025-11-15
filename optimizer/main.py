#!/usr/bin/env python3
"""
Water Pump Optimization using OR-Tools CP-SAT Solver
Minimizes electricity costs while satisfying operational constraints.
"""

import json
from ortools.sat.python import cp_model
from tunnel_volume import tunnel_volume
from pumping_score import pumping_score
import sys


def height_from_volume_approx(volume: float) -> float:
    """
    Approximate inverse of tunnel_volume using binary search.
    Given a volume, find the corresponding height.
    """
    if volume <= 350:
        return 0.0
    
    # Binary search for height
    low, high = 0.0, 14.1
    while high - low > 0.001:
        mid = (low + high) / 2
        v = tunnel_volume(mid)
        if v < volume:
            low = mid
        else:
            high = mid
    return (low + high) / 2


class PumpOptimizer:
    def __init__(self, data_file: str, time_horizon_hours: int = 48):
        """Initialize the optimizer with data and parameters."""
        self.time_horizon_hours = time_horizon_hours
        self.intervals_per_hour = 4  # 15-minute intervals
        self.num_intervals = time_horizon_hours * self.intervals_per_hour
        self.interval_hours = 0.25  # 15 minutes = 0.25 hours
        
        # Load data
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        self.initial_water_level = data['initialWaterLevel']
        self.initial_volume = tunnel_volume(self.initial_water_level)
        
        # Extract first num_intervals of data
        items = data['items'][:self.num_intervals]
        self.water_inflow = [item['waterInflow'] for item in items]
        self.electricity_price = [item['electricityPrice'] for item in items]
        self.dates = [item['date'] for item in items]
        
        # Pump specifications: (flow_m3_per_hour, power_kw)
        self.pumps = {
            '1.1': (1500, 185),
            '1.2': (3000, 350),
            '1.3': (3000, 350),
            '1.4': (3000, 350),
            '2.1': (1500, 185),
            '2.2': (3000, 350),
            '2.3': (3000, 350),
            '2.4': (3000, 350),
        }
        
        self.pump_names = list(self.pumps.keys())
        self.num_pumps = len(self.pump_names)
        
        # Constraints parameters
        self.min_water_level = 0.0
        self.max_water_level = 8.0
        self.low_level_threshold = 0.5
        self.min_on_off_intervals = 8  # 2 hours = 8 * 15min
        self.max_flow_per_interval = 4000  # m3 per 15min (16000 m3/h)
        self.empty_tank_threshold = 144000  # m3
        
        # Tank volume bounds (for scaling)
        self.min_volume = tunnel_volume(self.min_water_level)
        self.max_volume = tunnel_volume(self.max_water_level)
        
        # Scale factor for integer programming
        self.volume_scale = 1.0  # Keep volumes in m3
        
        # Placeholder for fixed pump schedules (can be customized)
        self.fixed_schedules = {}  # pump_name -> [True/False for each interval]
        
    def solve(self):
        """Build and solve the optimization model."""
        model = cp_model.CpModel()
        
        print("Building optimization model...")
        print(f"Time horizon: {self.num_intervals} intervals ({self.time_horizon_hours} hours)")
        print(f"Initial water level: {self.initial_water_level:.2f} m")
        print(f"Initial volume: {self.initial_volume:.2f} m³")
        
        # Decision variables: pump_on[p][t] = 1 if pump p is on at time t
        pump_on = {}
        for p in range(self.num_pumps):
            pump_on[p] = {}
            for t in range(self.num_intervals):
                pump_on[p][t] = model.NewBoolVar(f'pump_{self.pump_names[p]}_t{t}')
        
        # Volume at each time step (scaled to integer)
        volume = {}
        for t in range(self.num_intervals + 1):
            # Volume in m3, scaled to integers
            v_min = int(self.min_volume)
            v_max = int(self.max_volume * 1.5)  # Allow some buffer
            volume[t] = model.NewIntVar(v_min, v_max, f'volume_t{t}')
        
        # Set initial volume
        model.Add(volume[0] == int(self.initial_volume))
        
        # Constraint 1: At least one pump must always be running
        for t in range(self.num_intervals):
            model.Add(sum(pump_on[p][t] for p in range(self.num_pumps)) >= 1)
        
        # Constraint 2: Volume dynamics
        for t in range(self.num_intervals):
            # Outflow from all pumps in this interval (m3)
            outflow_terms = []
            for p in range(self.num_pumps):
                flow_rate, _ = self.pumps[self.pump_names[p]]
                outflow_per_interval = int(flow_rate * self.interval_hours)
                outflow_terms.append(pump_on[p][t] * outflow_per_interval)
            
            inflow = int(self.water_inflow[t])
            
            # volume[t+1] = volume[t] + inflow - outflow
            model.Add(volume[t + 1] == volume[t] + inflow - sum(outflow_terms))
        
        # Constraint 3: Volume bounds (corresponding to height bounds)
        for t in range(self.num_intervals + 1):
            model.Add(volume[t] >= int(tunnel_volume(self.min_water_level)))
            model.Add(volume[t] <= int(tunnel_volume(self.max_water_level)))
        
        # Constraint 4: Max flow constraint (16000 m3/h = 4000 m3/15min)
        for t in range(self.num_intervals):
            total_flow = []
            for p in range(self.num_pumps):
                flow_rate, _ = self.pumps[self.pump_names[p]]
                flow_per_interval = int(flow_rate * self.interval_hours)
                total_flow.append(pump_on[p][t] * flow_per_interval)
            model.Add(sum(total_flow) <= self.max_flow_per_interval)
        
        # Constraint 5: Minimum on/off time (2 hours = 8 intervals)
        for p in range(self.num_pumps):
            for t in range(self.num_intervals - 1):
                # If pump turns on at t, it must stay on for at least 8 intervals
                if t + self.min_on_off_intervals <= self.num_intervals:
                    # turned_on[t] = pump_on[p][t] - pump_on[p][t-1] (if >= 1)
                    # We enforce: if pump_on[p][t] > pump_on[p][t-1], then pump_on[p][t:t+8] must all be 1
                    for dt in range(1, min(self.min_on_off_intervals, self.num_intervals - t)):
                        # If it was off and now on, must stay on
                        if t > 0:
                            # pump_on[p][t] - pump_on[p][t-1] >= 1 implies pump_on[p][t+dt] = 1
                            # Encoded as: pump_on[p][t] + (1 - pump_on[p][t-1]) <= 1 + pump_on[p][t+dt]
                            model.Add(pump_on[p][t] - pump_on[p][t-1] <= pump_on[p][t+dt])
                
                # If pump turns off at t, it must stay off for at least 8 intervals
                if t + self.min_on_off_intervals <= self.num_intervals:
                    for dt in range(1, min(self.min_on_off_intervals, self.num_intervals - t)):
                        if t > 0:
                            # If it was on and now off, must stay off
                            # pump_on[p][t-1] - pump_on[p][t] >= 1 implies pump_on[p][t+dt] = 0
                            model.Add(pump_on[p][t-1] - pump_on[p][t] + pump_on[p][t+dt] <= 1)
        
        # Apply fixed pump schedules if any
        for pump_name, schedule in self.fixed_schedules.items():
            p = self.pump_names.index(pump_name)
            for t, must_run in enumerate(schedule):
                if t < self.num_intervals:
                    if must_run:
                        model.Add(pump_on[p][t] == 1)
        
        # Constraint 6: Low water level requirement
        # The tank must reach <= 0.5m at least once every 24h period
        low_level_volume = int(tunnel_volume(self.low_level_threshold))
        
        # Check each 24-hour period
        num_24h_periods = self.time_horizon_hours // 24
        for period in range(num_24h_periods):
            start_interval = period * 96  # 96 intervals = 24 hours
            end_interval = (period + 1) * 96
            
            # Check if total inflow in this period exceeds threshold
            period_inflow = sum(self.water_inflow[start_interval:min(end_interval, len(self.water_inflow))])
            
            if period_inflow <= self.empty_tank_threshold:
                # Must reach low level at least once in this 24h period
                low_level_reached = []
                for t in range(start_interval, min(end_interval + 1, self.num_intervals + 1)):
                    is_low = model.NewBoolVar(f'is_low_period{period}_t{t}')
                    # is_low = 1 if volume[t] <= low_level_volume
                    model.Add(volume[t] <= low_level_volume).OnlyEnforceIf(is_low)
                    model.Add(volume[t] > low_level_volume).OnlyEnforceIf(is_low.Not())
                    low_level_reached.append(is_low)
                
                # At least one must be true in this period
                model.Add(sum(low_level_reached) >= 1)
                print(f"  Added low-level constraint for period {period} (intervals {start_interval}-{end_interval})")
        
        # Objective: Minimize total electricity cost with water-level-dependent efficiency
        # Discretize water levels into bins for piecewise cost calculation
        water_level_bins = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        num_bins = len(water_level_bins) - 1
        
        # Create indicator variables for water level bins at each time step
        level_indicators = {}
        for t in range(self.num_intervals):
            level_indicators[t] = {}
            for b in range(num_bins):
                level_indicators[t][b] = model.NewBoolVar(f'level_bin_{b}_t{t}')
            
            # Exactly one bin must be active
            model.Add(sum(level_indicators[t][b] for b in range(num_bins)) == 1)
            
            # Link bin indicators to volume
            for b in range(num_bins):
                bin_low = tunnel_volume(water_level_bins[b])
                bin_high = tunnel_volume(water_level_bins[b + 1])
                
                # If this bin is active, volume must be in range
                model.Add(volume[t] >= int(bin_low)).OnlyEnforceIf(level_indicators[t][b])
                model.Add(volume[t] <= int(bin_high)).OnlyEnforceIf(level_indicators[t][b])
        
        cost_terms = []
        for t in range(self.num_intervals):
            for p in range(self.num_pumps):
                _, power_kw = self.pumps[self.pump_names[p]]
                
                # For each water level bin, calculate adjusted cost
                for b in range(num_bins):
                    # Use midpoint of bin for score calculation
                    bin_mid_level = (water_level_bins[b] + water_level_bins[b + 1]) / 2
                    
                    # Get pumping score based on electricity price and pump efficiency at this level
                    pumping_score_value = pumping_score(bin_mid_level, self.electricity_price[t])
                    
                    # Cost = power (kW) * time (h) * pumping_score (€/kWh)
                    # Scale by 1000 to keep precision
                    cost = int(power_kw * self.interval_hours * pumping_score_value * 1000)
                    
                    # This cost applies only if pump is on AND we're in this bin
                    # Create a variable for the conjunction
                    pump_and_bin = model.NewBoolVar(f'pump_{p}_bin_{b}_t{t}')
                    model.AddBoolAnd([pump_on[p][t], level_indicators[t][b]]).OnlyEnforceIf(pump_and_bin)
                    model.AddBoolOr([pump_on[p][t].Not(), level_indicators[t][b].Not()]).OnlyEnforceIf(pump_and_bin.Not())
                    
                    cost_terms.append(pump_and_bin * cost)
        
        total_cost = sum(cost_terms)
        model.Minimize(total_cost)
        
        # Solve
        print("\nSolving...")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 600.0  # 5 minutes timeout
        solver.parameters.log_search_progress = True
        
        status = solver.Solve(model)
        
        # Process results
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"\n{'='*60}")
            if status == cp_model.OPTIMAL:
                print("OPTIMAL SOLUTION FOUND")
            else:
                print("FEASIBLE SOLUTION FOUND")
            print(f"{'='*60}")
            
            total_cost_value = solver.ObjectiveValue() / 1000.0
            print(f"\nTotal Electricity Cost: €{total_cost_value:.2f}")
            
            # Extract solution
            solution = {
                'status': 'optimal' if status == cp_model.OPTIMAL else 'feasible',
                'total_cost_eur': total_cost_value,
                'initial_water_level_m': self.initial_water_level,
                'initial_volume_m3': self.initial_volume,
                'schedule': []
            }
            
            print("\n" + "="*80)
            print("PUMP SCHEDULE")
            print("="*80)
            
            for t in range(self.num_intervals):
                water_level = height_from_volume_approx(solver.Value(volume[t]))
                next_water_level = height_from_volume_approx(solver.Value(volume[t + 1]))
                
                active_pumps = []
                total_flow = 0
                interval_cost = 0
                
                # Calculate pumping score based on water level and electricity price
                pumping_score_value = pumping_score(water_level, self.electricity_price[t])
                
                for p in range(self.num_pumps):
                    if solver.Value(pump_on[p][t]) == 1:
                        pump_name = self.pump_names[p]
                        flow_rate, power_kw = self.pumps[pump_name]
                        active_pumps.append(pump_name)
                        total_flow += flow_rate * self.interval_hours
                        # Use pumping score that accounts for pump efficiency at this water level
                        interval_cost += power_kw * self.interval_hours * pumping_score_value
                
                interval_info = {
                    'interval': t,
                    'date': self.dates[t],
                    'active_pumps': active_pumps,
                    'water_level_start_m': water_level,
                    'water_level_end_m': next_water_level,
                    'volume_start_m3': solver.Value(volume[t]),
                    'volume_end_m3': solver.Value(volume[t + 1]),
                    'inflow_m3': self.water_inflow[t],
                    'outflow_m3': total_flow,
                    'electricity_price_eur_per_kwh': self.electricity_price[t],
                    'pumping_score_eur_per_kwh': pumping_score_value,
                    'pump_efficiency_pct': (self.electricity_price[t] / pumping_score_value * 100) if pumping_score_value > 0 else 100.0,
                    'interval_cost_eur': interval_cost
                }
                solution['schedule'].append(interval_info)
                
                # Print summary every hour (every 4 intervals)
                if t % 4 == 0:
                    print(f"\n{self.dates[t][:16]} (Hour {t//4})")
                
                efficiency = self.electricity_price[t] / pumping_score_value if pumping_score_value > 0 else 1.0
                print(f"  t={t:3d}: Pumps={','.join(active_pumps):20s} | "
                      f"Level={water_level:5.2f}m→{next_water_level:5.2f}m | "
                      f"Vol={solver.Value(volume[t]):7.0f}m³ | "
                      f"In={self.water_inflow[t]:6.0f}m³ Out={total_flow:6.0f}m³ | "
                      f"Eff={efficiency*100:5.1f}% | "
                      f"Cost=€{interval_cost:.2f}")
            
            # Save to file
            output_file = 'optimization_result.json'
            with open(output_file, 'w') as f:
                json.dump(solution, f, indent=2)
            print(f"\n{'='*80}")
            print(f"Full solution saved to {output_file}")
            
            # Summary statistics
            print(f"\n{'='*60}")
            print("SUMMARY STATISTICS")
            print(f"{'='*60}")
            
            final_volume = solver.Value(volume[self.num_intervals])
            final_level = height_from_volume_approx(final_volume)
            print(f"Initial water level: {self.initial_water_level:.2f} m ({self.initial_volume:.0f} m³)")
            print(f"Final water level:   {final_level:.2f} m ({final_volume:.0f} m³)")
            
            # Pump usage statistics
            print(f"\n{'='*60}")
            print("PUMP USAGE STATISTICS")
            print(f"{'='*60}")
            for p in range(self.num_pumps):
                hours_on = sum(solver.Value(pump_on[p][t]) for t in range(self.num_intervals)) * self.interval_hours
                pct = (hours_on / self.time_horizon_hours) * 100
                print(f"Pump {self.pump_names[p]}: {hours_on:6.2f} hours ({pct:5.1f}%)")
            
            return solution
            
        else:
            print(f"\nNo solution found. Status: {solver.StatusName(status)}")
            return None


def main():
    """Main entry point."""
    optimizer = PumpOptimizer('input.json', time_horizon_hours=48)
    
    # Optional: Add fixed pump schedules
    # Example: Force pump 1.1 to run for first 3 intervals (45 minutes)
    # optimizer.fixed_schedules['1.1'] = [True, True, True] + [None] * (optimizer.num_intervals - 3)
    
    solution = optimizer.solve()
    
    if solution:
        print(f"\n✓ Optimization completed successfully!")
        print(f"✓ Total cost: €{solution['total_cost_eur']:.2f}")
        return 0
    else:
        print(f"\n✗ Optimization failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

