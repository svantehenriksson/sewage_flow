#!/usr/bin/env python3
"""
Water Pump Optimization using OR-Tools CP-SAT Solver
Minimizes electricity costs while satisfying operational constraints.
"""

import json
from ortools.sat.python import cp_model
from tunnel_volume import tunnel_volume
from pumps import small_pump, big_pump
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
        
        # Load under threshold constraint
        self.under_threshold_within_minutes = data.get('underThresholdWithinMinutes', None)
        
        # Extract first num_intervals of data
        items = data['items'][960:960+self.num_intervals]
        self.water_inflow = [item['waterInflow'] for item in items]
        # Note: electricityPrice in JSON is in c/kWh (cents per kWh)
        # Convert to €/kWh for cost calculations
        self.electricity_price_cents = [item['electricityPriceHigh'] for item in items]
        self.electricity_price = [price / 100.0 for price in self.electricity_price_cents]
        self.dates = [item['date'] for item in items]
        
        # Load initial pump statuses (convert pump1-1 format to 1.1 format)
        self.pump_initial_status = {}
        pump_status_mapping = {
            'pump1-1': '1.1',
            'pump1-2': '1.2',
            'pump1-3': '1.3',
            'pump1-4': '1.4',
            'pump2-1': '2.1',
            'pump2-2': '2.2',
            'pump2-3': '2.3',
            'pump2-4': '2.4',
        }
        
        for json_key, pump_key in pump_status_mapping.items():
            if json_key in data:
                status = data[json_key]
                locked_minutes = status.get('locked', 0)
                locked_intervals = int((locked_minutes + 14) // 15)  # Round up to nearest interval
                self.pump_initial_status[pump_key] = {
                    'on': status.get('on', False),
                    'locked_intervals': locked_intervals
                }
            else:
                # Default: pump is off and not locked
                self.pump_initial_status[pump_key] = {
                    'on': False,
                    'locked_intervals': 0
                }
        
        # Pump specifications: pump type ('small' or 'big')
        # Performance varies with water level - use small_pump() and big_pump() functions
        self.pump_types = {
            '1.1': 'small',
            '1.2': 'big',
            '1.3': 'big',
            '1.4': 'big',
            '2.1': 'small',
            '2.2': 'big',
            '2.3': 'big',
            '2.4': 'big',
        }
        
        self.pump_names = list(self.pump_types.keys())
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
        
    def get_pump_specs(self, pump_name: str, water_level: float):
        """Get pump power and flow rate at a given water level."""
        if self.pump_types[pump_name] == 'small':
            power_kw, flow_m3h = small_pump(water_level)
        else:
            power_kw, flow_m3h = big_pump(water_level)
        return power_kw, flow_m3h
        
    def solve(self):
        """Build and solve the optimization model."""
        model = cp_model.CpModel()
        
        print("Building optimization model...")
        print(f"Time horizon: {self.num_intervals} intervals ({self.time_horizon_hours} hours)")
        print(f"Initial water level: {self.initial_water_level:.2f} m")
        print(f"Initial volume: {self.initial_volume:.2f} m³")
        print("\nInitial pump statuses:")
        for pump_name in self.pump_names:
            status = self.pump_initial_status[pump_name]
            state = "ON" if status['on'] else "OFF"
            locked = status['locked_intervals']
            if locked > 0:
                print(f"  Pump {pump_name}: {state}, locked for {locked} intervals ({locked * 15} minutes)")
            else:
                print(f"  Pump {pump_name}: {state}, not locked")
        
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
        
        # Constraint 0: Enforce initial pump statuses and locked intervals
        for p in range(self.num_pumps):
            pump_name = self.pump_names[p]
            status = self.pump_initial_status[pump_name]
            initial_state = 1 if status['on'] else 0
            locked_intervals = status['locked_intervals']
            
            # Lock the pump state for the specified number of intervals
            for t in range(min(locked_intervals, self.num_intervals)):
                model.Add(pump_on[p][t] == initial_state)
        
        # Constraint 1: At least one pump must always be running
        for t in range(self.num_intervals):
            model.Add(sum(pump_on[p][t] for p in range(self.num_pumps)) >= 1)
        
        # Constraint 2: Volume dynamics
        # Use average pump performance (at mid-range water level) for volume dynamics
        avg_water_level = (self.min_water_level + self.max_water_level) / 2
        pump_avg_specs = {}
        for p in range(self.num_pumps):
            pump_name = self.pump_names[p]
            power_kw, flow_m3h = self.get_pump_specs(pump_name, avg_water_level)
            pump_avg_specs[p] = (power_kw, flow_m3h)
        
        for t in range(self.num_intervals):
            # Outflow from all pumps in this interval (m3)
            outflow_terms = []
            for p in range(self.num_pumps):
                _, flow_rate = pump_avg_specs[p]
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
        # Use maximum possible flow (at highest water level) to ensure constraint is respected
        max_water_level_for_flow = self.max_water_level
        for t in range(self.num_intervals):
            total_flow = []
            for p in range(self.num_pumps):
                pump_name = self.pump_names[p]
                _, flow_rate = self.get_pump_specs(pump_name, max_water_level_for_flow)
                flow_per_interval = int(flow_rate * self.interval_hours)
                total_flow.append(pump_on[p][t] * flow_per_interval)
            model.Add(sum(total_flow) <= self.max_flow_per_interval)
        
        # Constraint 5: Minimum on/off time (2 hours = 8 intervals)
        for p in range(self.num_pumps):
            pump_name = self.pump_names[p]
            status = self.pump_initial_status[pump_name]
            initial_state = 1 if status['on'] else 0
            
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
                        else:
                            # At t=0, check against initial state
                            # If initial was off (0) and t=0 is on (1), must stay on
                            model.Add(pump_on[p][t] - initial_state <= pump_on[p][t+dt])
                
                # If pump turns off at t, it must stay off for at least 8 intervals
                if t + self.min_on_off_intervals <= self.num_intervals:
                    for dt in range(1, min(self.min_on_off_intervals, self.num_intervals - t)):
                        if t > 0:
                            # If it was on and now off, must stay off
                            # pump_on[p][t-1] - pump_on[p][t] >= 1 implies pump_on[p][t+dt] = 0
                            model.Add(pump_on[p][t-1] - pump_on[p][t] + pump_on[p][t+dt] <= 1)
                        else:
                            # At t=0, check against initial state
                            # If initial was on (1) and t=0 is off (0), must stay off
                            model.Add(initial_state - pump_on[p][t] + pump_on[p][t+dt] <= 1)
        
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
        
        # Constraint 6a: Under threshold within specified minutes (if configured)
        if self.under_threshold_within_minutes is not None:
            # Convert minutes to intervals (15-minute intervals)
            max_intervals = int(self.under_threshold_within_minutes / 15)
            max_intervals = min(max_intervals, self.num_intervals)
            
            print(f"  Adding constraint: water level must go under {self.low_level_threshold}m within {self.under_threshold_within_minutes} minutes ({max_intervals} intervals)")
            
            # Must reach low level at least once within the specified time window
            low_level_reached = []
            for t in range(max_intervals + 1):
                is_low = model.NewBoolVar(f'is_low_initial_t{t}')
                # is_low = 1 if volume[t] <= low_level_volume
                model.Add(volume[t] <= low_level_volume).OnlyEnforceIf(is_low)
                model.Add(volume[t] > low_level_volume).OnlyEnforceIf(is_low.Not())
                low_level_reached.append(is_low)
            
            # At least one must be true in this time window
            model.Add(sum(low_level_reached) >= 1)
        
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
        
        # Objective: Minimize total electricity cost
        # Use average water level for cost calculation to avoid complexity
        # The actual cost will be calculated post-hoc with real water levels
        cost_terms = []
        for t in range(self.num_intervals):
            for p in range(self.num_pumps):
                pump_name = self.pump_names[p]
                
                # Use average pump power for optimization
                # This is a reasonable approximation and vastly simplifies the model
                power_kw, _ = pump_avg_specs[p]
                
                # Cost = power (kW) * time (h) * electricity_price (€/kWh)
                # Scale by 1000 to keep precision
                cost = int(power_kw * self.interval_hours * self.electricity_price[t] * 1000)
                
                cost_terms.append(pump_on[p][t] * cost)
        
        total_cost = sum(cost_terms)
        model.Minimize(total_cost)
        
        # Provide a simple heuristic solution hint to speed up solving
        # Strategy: Run pumps during cheapest hours while respecting constraints
        print("\nGenerating initial solution hint...")
        for t in range(self.num_intervals):
            for p in range(self.num_pumps):
                # Simple heuristic: maintain initial state for locked pumps,
                # otherwise prefer at least one pump on
                pump_name = self.pump_names[p]
                status = self.pump_initial_status[pump_name]
                if t < status['locked_intervals']:
                    hint_value = 1 if status['on'] else 0
                else:
                    # Simple heuristic: first pump always on, others based on price
                    if p == 0:
                        hint_value = 1
                    else:
                        # Turn on more pumps during cheap hours
                        hint_value = 1 if self.electricity_price[t] < 0.05 else 0
                model.AddHint(pump_on[p][t], hint_value)
        
        # Solve
        print("\nSolving...")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 120.0  # 2 minutes timeout
        solver.parameters.num_search_workers = 8  # Use multiple threads
        solver.parameters.log_search_progress = True
        solver.parameters.linearization_level = 2  # More aggressive linearization
        solver.parameters.cp_model_presolve = True  # Enable presolve
        
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
                
                for p in range(self.num_pumps):
                    if solver.Value(pump_on[p][t]) == 1:
                        pump_name = self.pump_names[p]
                        # Get actual pump specs at the current water level
                        power_kw, flow_rate = self.get_pump_specs(pump_name, water_level)
                        active_pumps.append(pump_name)
                        total_flow += flow_rate * self.interval_hours
                        # Calculate cost: power * time * electricity price
                        interval_cost += power_kw * self.interval_hours * self.electricity_price[t]
                
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
                    'electricity_price_cents_per_kwh': self.electricity_price_cents[t],
                    'interval_cost_eur': interval_cost
                }
                solution['schedule'].append(interval_info)
                
                # Print summary every hour (every 4 intervals)
                if t % 4 == 0:
                    print(f"\n{self.dates[t][:16]} (Hour {t//4})")
                
                print(f"  t={t:3d}: Pumps={','.join(active_pumps):20s} | "
                      f"Level={water_level:5.2f}m→{next_water_level:5.2f}m | "
                      f"Vol={solver.Value(volume[t]):7.0f}m³ | "
                      f"In={self.water_inflow[t]:6.0f}m³ Out={total_flow:6.0f}m³ | "
                      f"Price={self.electricity_price_cents[t]:.1f}c/kWh | "
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

