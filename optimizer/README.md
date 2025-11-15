## Running it

```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
python visualize.py
```

## Objective

- I want to minimize my electrical bill.
- This by optimizing when my water pumps should be running.
- I want to calculate when my pumps should be running the coming 48h in 15 min intervals.
- The tank has a cylindrical form. The formula for height to volume is defined in `tunnel_volume.py`
- Example data can be found in input.json. Use the inflow rates from there and starting water level and electricity price
- Use or-tools and the existing virtual environment
- The pumps are more effective when the water level is high so use the methods `pumps.py` to understand how much energy they use, and how much they pump at different levels
- We want to use the pumps about the same amount of time, so make it slightly more likely to use the least used pump

## Test data

From input.json get

- initialWaterLevel: the initial water level (in meters)
- underThresholdWithinMinutes: within how many minutes from the start the water level needs to go under 0.5m (e.g., 720 means the water level must go below 0.5m within the first 12 hours)
- pump statuses (pump1-1 through pump1-4, pump2-1 through pump2-4):
  - on: boolean indicating if the pump is currently running
  - locked: number of minutes the pump status cannot be changed
    - If a pump is ON and locked for 90 minutes, it must stay ON for those 90 minutes
    - If a pump is OFF and locked for 120 minutes, it cannot be turned ON for those 120 minutes
    - A locked value of 0 means the pump can be controlled immediately
    - totalMinutes: the amount of minutes the pump has been in use. Also return an updated value in the output
      - Used for load balancing - pumps with fewer hours are preferred (within their category)
- items (intervals):
  - date: ISO timestamp for the interval
  - waterInflow: how much water flows into the system during that 15min interval (in m³)
  - electricityPrice: price per kWh during that interval (in c/kWh)

## Specs

### Pumps

There are 8 pumps

1.1 small pump
1.2 big pump
1.3 big pump
1.4 big pump

2.1 small pump
2.2 big pump
2.3 big pump
2.4 big pump

### Input for model

- Restrictions:
  - Pump 1.1: [true, true, true, false, ...], e.g. if the pump must run during first 45 min (15 min intervals)
  - Pump 2.4: [true, true, false]
  - Water tank level <= 0.5m at least once: 0-1200 (coming 20h). Not required if predicted inflow during next 24h > [empty_tank_threshold]m3
    - The water tank level have to reach <= 0.5m in the coming 24h after the last time it was <= 0.5m
  - Water tank level >= 0m: always
  - Water tank level <= 8m: always
- In-water flow coming 24h [34, 45, ...]: 0-15 min 34m3, 15-30min 45m3
- Electicity price coming 24h [0.38, 0.56, ...]: 0-15 min 38c/kWh
- Current water level: 430 m3
- 1 Pump must always be running
- empty_tank_threshold variable, e.g. 144000m3
- If a pump is turned on, if have to be on for 2h, if it has been turned off, it needs to be off for 2h
- Max allowed flow is 16000m3/h -> 4000m3/15min

## Future Enhancements

- Optimize beginning with 15min intervals, but 24-48h with 3h intervals