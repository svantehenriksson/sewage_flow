import xarray as xr
import os

os.mkdir("forecasts")

run = ['00','03','06','09','12','15','18','21']
day = [x for x in range(15,31)]

for d in day:
    for r in run:

        # OPeNDAP/THREDDS URL with your subset constraints
        url = (
            f"https://thredds.met.no/thredds/dodsC/meps25epsarchive/2024/11/{d}/"
            f"meps_det_sfc_202411{d}T{r}Z.ncml"
            "?forecast_reference_time,"
            "x[0:1:948],"
            "y[0:1:1068],"
            "longitude[0:1:1068][0:1:948],"
            "latitude[0:1:1068][0:1:948],"
            "time[0:1:48],"
            "precipitation_amount_acc[0:1:48][0:1:0][0:1:1068][0:1:948]"
        )
        print(url)
        # Open the remote dataset via OPeNDAP
        ds = xr.open_dataset(url)

        # Save the subset locally as a NetCDF file
        out_file = f"forecasts/meps_det_sfc_202411{d}T{r}Z_subset.nc"
        ds.to_netcdf(out_file)

        print(f"Saved to {out_file}")
