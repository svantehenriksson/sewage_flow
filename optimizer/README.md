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
- The pumps are more effective when the water level is high so use `pumping_score.py` to get a score based on electricy price and water level.

## Test data

From input.json get

- initialWaterLevel: the intitial water level

From every item:

- date
- waterInflow: how much water flows into the system at that 15min
- electricity price: price per kWh during that interval

## Specs

### Pumps

#### Pump 1.1

1.1 Flow: 1500m3/h, Electricity: 185kWh/h
1.2 Flow: 3000m3/h, Electricity: 350kWh/h
1.3 Flow: 3000m3/h, Electricity: 350kWh/h
1.4 Flow: 3000m3/h, Electricity: 350kWh/h

2.1 Flow: 1500m3/h, Electricity: 185kWh/h
2.2 Flow: 3000m3/h, Electricity: 350kWh/h
2.3 Flow: 3000m3/h, Electricity: 350kWh/h
2.4 Flow: 3000m3/h, Electricity: 350kWh/h

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

- Take water level into account
- I wanting to equalize load, can track how much each pump have been used and tweak its multiplier
