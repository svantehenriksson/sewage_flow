import numpy as np
import xarray as xr
import datetime as dt
from shapely.geometry import Point, Polygon
import pandas as pd
import argparse

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

def read_elprices():
    # Read the data from the provided sheet to simulate electricity prices
    df = pd.read_excel("Hackathon_HSY_data.xlsx")
    df["Time stamp"] = pd.to_datetime(df["Time stamp"], dayfirst=True)

    # Localize to Finnish winter time (UTC+2, no DST)
    df["Time stamp"] = df["Time stamp"].dt.tz_localize("Etc/GMT-2")

    # Convert to UTC
    df["date"] = df["Time stamp"].dt.tz_convert("UTC")
    df["date"] = df["date"].dt.tz_localize(None)
    # Rename column
    df["electricityPrice"] = df["Electricity price 2: normal"]

    return df

# Espoo polygon (lon, lat)
coords = [
    [24.5620, 60.2080],
    [24.5700, 60.2400],
    [24.5900, 60.2850],
    [24.6050, 60.3200],
    [24.6200, 60.3500],
    [24.6700, 60.4000],
    [24.7300, 60.4300],
    [24.7900, 60.4500],
    [24.8400, 60.4600],
    [24.9000, 60.4550],
    [24.9500, 60.4350],
    [24.9800, 60.4050],
    [24.9900, 60.3600],
    [24.9950, 60.3200],
    [24.9900, 60.2800],
    [24.9700, 60.2400],
    [24.9400, 60.2150],
    [24.9000, 60.2050],
    [24.8500, 60.2000],
    [24.8000, 60.2020],
    [24.7500, 60.2100],
    [24.7000, 60.2200],
    [24.6500, 60.2300],
    [24.6000, 60.2250],
    [24.5620, 60.2080],
]

poly = Polygon(coords)

def point_in_poly(lon, lat, poly=poly):
    # use covers() if you want boundary points to be True as well
    return poly.covers(Point(float(lon), float(lat)))


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
        "--outfile",
        type=str,
        required=True,
        help="Path to the output file."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    ds = xr.open_dataset(f"forecasts/meps_det_sfc_{args.starttime}Z_subset.nc")

    # Vectorize to work on numpy/xarray arrays
    point_in_poly_ufunc = np.frompyfunc(point_in_poly, 2, 1)

    mask_np = point_in_poly_ufunc(ds["longitude"].values, ds["latitude"].values).astype(bool)

    mask = xr.DataArray(
        mask_np,
        coords=ds["longitude"].coords,
        dims=ds["longitude"].dims,
        name="mask_espoo",
    )

    # Optionally attach to the dataset
    ds = ds.assign(mask_espoo=mask)

    ds = ds.where(ds.mask_espoo)  # dataset clipped to the polygon

    mean_prec_rate = ds["precipitation_amount_acc"].mean(dim=["x", "y"]).diff(dim="time")

    new_time = xr.date_range(
        start=ds.time[0].values,
        end=ds.time[-1].values,
        freq="15min"
    )

    da_diff_15min = mean_prec_rate.interp(time=new_time)


    inflow=[]
    for t in new_time.values:
        inflow.append(predict_urban_inflow(pd.to_datetime(t).strftime("%Y-%m-%dT%H:%M:%SZ")))


    df = pd.DataFrame({
        "date": da_diff_15min.time.values.squeeze(),
        "rainInflow": da_diff_15min.values.squeeze() * 613,
        "urbanInflow": inflow
    })

    df = df.fillna(0)

    df["waterInflow"] = df["rainInflow"] + df["urbanInflow"]
    df = df.merge(read_elprices()[["date", "electricityPrice"]], on="date", how="left")
    df["date"] = df["date"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")


    df.to_json(args.outfile,orient='records')

if __name__ == "__main__":
    main()

