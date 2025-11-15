import requests
import xml.etree.ElementTree as ET
import pandas as pd

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

def fmi_query(place, parameter, start, end):
    """Download one FMI timevaluepair series and return a DataFrame."""
    url = "https://opendata.fmi.fi/wfs"
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": "fmi::forecast::harmonie::surface::point::timevaluepair",
        "place": place,
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
        "place": place,
        "parameter" : parameter
    })


# ---------------------------------------------------------
# LOOP OVER QUERIES
# ---------------------------------------------------------

stations = ["Espoo"]        # example FMISID list
parameters = ["PrecipitationAmount"]    # precipitation

df_all = []   # collect partial dataframes

start = dt.datetime(2025, 11, 15)
end   = dt.datetime(2025, 11, 19)

request_start = None
for t in daily_timestamps(start, end):
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

df.to_csv(
    "weather.csv",
    sep=";",        # Use semicolon instead of comma
    encoding="utf-8",  # Set encoding
    date_format="%Y-%m-%dT%H:%M:%SZ",  # Format datetime columns
    header=True,     # Include column names
    index=False      # Skip DataFrame index
)

