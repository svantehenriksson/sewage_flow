#!/usr/bin/env python3
import argparse
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

import datetime as dt

def daily_timestamps(start, end):
    """
    Generator yielding datetime objects from start to end (inclusive),
    with 1-day increments.
    """
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)

def quarter_hourly_timestamps(start, end):
    """
    Generator yielding datetime objects from start to end (inclusive),
    with 1-day increments.
    """
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(seconds=900)

def read_elprices():
    # Read the data from the provided sheet to simulate electricity prices
    df = pd.read_excel("Hackathon_HSY_data.xlsx")
    df["Time stamp"] = pd.to_datetime(df["Time stamp"], dayfirst=True)

    # Localize to Finnish winter time (UTC+2, no DST)
    df["Time stamp"] = df["Time stamp"].dt.tz_localize("Etc/GMT-2")

    # Convert to UTC
    df["date"] = df["Time stamp"].dt.tz_convert("UTC")
    # Rename column
    df["electricityPrice"] = df["Electricity price 2: normal"]
    
    return df

def fmi_query(fmisid, parameter, start, end):
    """Download one FMI timevaluepair series and return a DataFrame."""
    url = "https://opendata.fmi.fi/wfs"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": "fmi::observations::weather::timevaluepair",
        "fmisid": fmisid,
        "parameters": parameter,
        "starttime": start,
        "endtime": end,
    }

    r = requests.get(url, params=params)
    r.raise_for_status()

    ns = {"wml2": "http://www.opengis.net/waterml/2.0"}

    root = ET.fromstring(r.content)

    times = []
    values = []

    for m in root.findall(".//wml2:MeasurementTVP", ns):
        times.append(m.find("wml2:time", ns).text)
        values.append(float(m.find("wml2:value", ns).text))

    return pd.DataFrame({
        "time": pd.to_datetime(times),
        "value": values,
        "fmisid": fmisid,
        "parameter": parameter
    })

def predict_rain_inflow(df,
                        t_query,
                        time_col="time",
                        precip_col="value",
                        lag_hours=9,
                        slope=613.6):
    """
    Predict the inflow at time t_query using precipitation values with a
    fixed time lag.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing timestamps and precipitation.
    t_query : str or pd.Timestamp
        The time at which the inflow should be predicted.
    time_col : str
        Name of the timestamp column.
    precip_col : str
        Name of the precipitation column.
    lag_hours : float
        Time lag between precipitation and inflow response.
    slope : float
        Regression slope relating precipitation to inflow.

    Returns
    -------
    float
        Predicted inflow at t_query. Returns NaN if no precip value at the required lag exists.
    """

    # Prepare timestamp
    t_query = pd.to_datetime(t_query)
    t_lag = t_query - pd.Timedelta(hours=lag_hours)


    # Convert timestamp column to datetime
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])

    # Find precipitation closest to the lagged time
    idx = (df[time_col] - t_lag).abs().idxmin()
    precip_at_lag = df.loc[idx, precip_col]

    if pd.isna(precip_at_lag):
        return np.nan

    # Linear model to compute inflow
    inflow = slope * precip_at_lag
    return inflow

# Fourier coefficients from the fitted model
a0 = 1008.84939054
a = [153.84311321, 167.07631902, 12.95154069,  8.08029008, -8.83528269]
b = [-304.88935553, 82.14413811, -11.28999361, 10.23866451, -13.25220271]

def predict_urban_inflow(ts):
    """
    Return predicted inflow (m3 / 15 min) at a given timestamp using
    the 5-harmonic Fourier model fitted to the first 5 days of data.

    Parameters:
        ts (datetime or str): timestamp

    Returns:
        float: predicted inflow at that time
    """

    # Allow passing timestamps as strings
    if isinstance(ts, str):
        ts = dt.datetime.fromisoformat(ts)

    # Convert time to normalized fraction of day
    minutes = ts.hour * 60 + ts.minute
    t = minutes / 1440.0  # Normalize to [0, 1]

    # Fourier model
    Q = a0
    for k in range(1, 6):
        Q += a[k-1] * np.cos(2*np.pi*k*t) + b[k-1] * np.sin(2*np.pi*k*t)

    return Q


def parse_args():
    parser = argparse.ArgumentParser(
        description="Template script with basic arguments."
    )

    parser.add_argument(
        "--starttime",
        type=str,
        required=True,
        help="Start time (format as needed, e.g. YYYY-MM-DD HH:MM)."
    )

    parser.add_argument(
        "--endtime",
        type=str,
        required=True,
        help="End time (format as needed)."
    )

    parser.add_argument(
        "--outfile",
        type=str,
        required=True,
        help="Path to the output file."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("Start time:", args.starttime)
    print("End time:", args.endtime)
    print("Output file:", args.outfile)

    # ---------------------------------------------------------
    # LOOP OVER QUERIES
    # ---------------------------------------------------------

    stations = [874863]        # Tapiola FMISID
    parameters = ["r_1h"]      # precipitation

    df_all = []   # collect partial dataframes


    request_start = None
    for t in daily_timestamps(dt.datetime.fromisoformat(args.starttime), dt.datetime.fromisoformat(args.endtime)):
        request_end = t
        if request_start == None:
            request_start = request_end
            continue

        for sid in stations:
            print(f"Downloading station {sid}...")
            for param in parameters:
                df_station = fmi_query(sid, param, request_start.strftime("%Y-%m-%dT%H:%M:%SZ"), request_end.strftime("%Y-%m-%dT%H:%M:%SZ"))
                df_all.append(df_station)
        request_start = request_end

    # Combine all stations into one dataframe
    df = pd.concat(df_all, ignore_index=True)

    # create a dataframe with forecasted inflow values
    inflow = []
    time = []
    for t in quarter_hourly_timestamps(dt.datetime.fromisoformat(args.starttime),dt.datetime.fromisoformat(args.endtime)):
        time.append(t)#.strftime("%Y-%m-%dT%H:%M:%SZ"))
        inflow.append(predict_rain_inflow(df,t.strftime("%Y-%m-%dT%H:%M:%SZ")) + predict_urban_inflow(t.strftime("%Y-%m-%dT%H:%M:%SZ")))

    df = pd.DataFrame({
        "date": time,
        "waterInflow": inflow
    })
    
    # add electricity price data to the set
    df = df.merge(read_elprices()[["date", "electricityPrice"]], on="date", how="left")
    df["date"] = df["date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    df.to_json(args.outfile,orient='records')
    
if __name__ == "__main__":
    main()

