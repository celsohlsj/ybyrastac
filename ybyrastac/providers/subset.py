"""
Subset utilities: recorte espacial (geometry) e temporal (time) aplicados a
xarray.Dataset produzidos por COGProvider/ZarrProvider.
"""

from __future__ import annotations

from typing import Optional, Tuple
import xarray as xr
import geopandas as gpd
from shapely.geometry.base import BaseGeometry


def subset(
    ds: xr.Dataset,
    geometry: Optional[BaseGeometry] = None,
    crs: str = "EPSG:4674",
    time: Optional[Tuple[str, str]] = None,
) -> xr.Dataset:
    """Recorta um Dataset espacial e/ou temporalmente.

    Parameters
    ----------
    ds : xr.Dataset
        Entrada (eixos 'time', 'y', 'x' esperados).
    geometry : shapely geometry, optional
        Polígono/MultiPolígono de recorte. Se fornecido, faz clip raster.
    crs : str
        CRS da geometria. Default EPSG:4674 (SIRGAS 2000).
    time : (start, end), optional
        Intervalo temporal ISO-8601.
    """
    if time is not None and "time" in ds.dims:
        ds = ds.sel(time=slice(*time))

    if geometry is not None:
        gdf = gpd.GeoDataFrame(geometry=[geometry], crs=crs)
        if ds.rio.crs is None:
            raise ValueError("Dataset sem CRS; abra com rioxarray ou defina rio.write_crs.")
        gdf = gdf.to_crs(ds.rio.crs)
        ds = ds.rio.clip(gdf.geometry.values, gdf.crs, drop=True, all_touched=True)

    return ds
