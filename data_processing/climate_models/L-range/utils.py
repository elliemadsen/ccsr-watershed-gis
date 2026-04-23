"""
Utility functions for reading/writing ESRI ASCII Grid (.asc) files
and working with the L-Range / MODIS datasets.
"""

import numpy as np
import os


# ---------------------------------------------------------------------------
# ASC I/O
# ---------------------------------------------------------------------------

def read_asc_header(filepath):
    """Read only the 6-line header of an ASC file and return as a dict."""
    header = {}
    with open(filepath) as f:
        for _ in range(6):
            parts = f.readline().strip().split()
            key = parts[0].lower()
            # Store numeric values appropriately
            if key in ("ncols", "nrows"):
                header[key] = int(parts[1])
            else:
                header[key] = float(parts[1])
    return header


def read_asc(filepath):
    """
    Read an ESRI ASCII Grid file.

    Returns
    -------
    header : dict
        Keys: ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value
    data : np.ndarray
        1-D array of length ncols * nrows (row-major).
    """
    header = read_asc_header(filepath)
    ncols = header["ncols"]
    nrows = header["nrows"]

    data = np.empty(ncols * nrows, dtype=np.float64)
    idx = 0
    with open(filepath) as f:
        # skip header
        for _ in range(6):
            f.readline()
        for line in f:
            vals = line.split()
            n = len(vals)
            data[idx : idx + n] = [float(v) for v in vals]
            idx += n

    return header, data


def write_asc(filepath, header, data):
    """
    Write an ESRI ASCII Grid file.

    Parameters
    ----------
    filepath : str
    header : dict  (must contain ncols, nrows, xllcorner, yllcorner,
                     cellsize, nodata_value)
    data : np.ndarray  (1-D, length = ncols * nrows)
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    ncols = int(header["ncols"])

    with open(filepath, "w") as f:
        f.write(f"ncols         {int(header['ncols'])}\n")
        f.write(f"nrows         {int(header['nrows'])}\n")
        f.write(f"xllcorner     {header['xllcorner']}\n")
        f.write(f"yllcorner     {header['yllcorner']}\n")
        f.write(f"cellsize      {header['cellsize']}\n")
        f.write(f"NODATA_value  {header['nodata_value']}\n")

        for i in range(0, len(data), ncols):
            row = data[i : i + ncols]
            f.write(" ".join(f"{v:.5f}" for v in row) + "\n")


def write_tiff(filepath, header, data, crs="EPSG:26918"):
    """
    Write a GeoTIFF from an ASC header + 1-D data array.

    Parameters
    ----------
    filepath : str
    header : dict  (ncols, nrows, xllcorner, yllcorner, cellsize, nodata_value)
    data : np.ndarray  (1-D, length = ncols * nrows)
    crs : str   EPSG code (default: NAD83 / UTM Zone 18N, matching the L-Range grids)
    """
    import rasterio
    from rasterio.transform import from_origin

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    ncols = int(header["ncols"])
    nrows = int(header["nrows"])
    cellsize = float(header["cellsize"])
    west = float(header["xllcorner"])
    north = float(header["yllcorner"]) + nrows * cellsize
    nodata = float(header["nodata_value"])

    transform = from_origin(west, north, cellsize, cellsize)
    grid = data.reshape(nrows, ncols).astype(np.float32)

    with rasterio.open(
        filepath,
        "w",
        driver="GTiff",
        height=nrows,
        width=ncols,
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
        nodata=nodata,
        compress="lzw",
    ) as dst:
        dst.write(grid, 1)


def read_mask(filepath):
    """Read the unified watershed mask and return a boolean array."""
    _, data = read_asc(filepath)
    return data == 1


# ---------------------------------------------------------------------------
# File-path helpers
# ---------------------------------------------------------------------------

def model_et_path(model_dir, month, year):
    """Return the path for a monthly L-Range ET file."""
    return os.path.join(model_dir, f"et____1_{month}_{year}_avg_cells.asc")


def model_lai_path(model_dir, facet, month, year):
    """Return the path for a monthly L-Range LAI file (single facet)."""
    return os.path.join(model_dir, f"lai___{facet}_{month}_{year}_avg_cells.asc")


def obs_et_path(obs_dir, year, month):
    """Return the path for a monthly MODIS observed ET file."""
    return os.path.join(obs_dir, "ET", f"et___{year}_{month:02d}.asc")


def obs_lai_path(obs_dir, year, month):
    """Return the path for a monthly MODIS observed LAI file."""
    return os.path.join(obs_dir, "LAI", f"lai__{year}_{month:02d}.asc")


# ---------------------------------------------------------------------------
# Grid loading helpers
# ---------------------------------------------------------------------------

def load_model_et(model_dir, month, year):
    """Load a single L-Range ET grid as a 1-D numpy array."""
    _, data = read_asc(model_et_path(model_dir, month, year))
    return data


def load_model_lai_total(model_dir, month, year):
    """Load L-Range LAI (sum of 3 facets) as a 1-D numpy array."""
    total = None
    for facet in (1, 2, 3):
        _, data = read_asc(model_lai_path(model_dir, facet, month, year))
        if total is None:
            total = data.copy()
        else:
            total += data
    return total


def load_obs_et(obs_dir, year, month):
    """Load a single MODIS observed ET grid."""
    _, data = read_asc(obs_et_path(obs_dir, year, month))
    return data


def load_obs_lai(obs_dir, year, month):
    """Load a single MODIS observed LAI grid."""
    _, data = read_asc(obs_lai_path(obs_dir, year, month))
    return data
