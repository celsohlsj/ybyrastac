"""
COG provider: carrega produtos em Cloud-Optimized GeoTIFF como xarray.Dataset.

Ideal para os produtos YbYrá que já são rasters anuais categóricos/contínuos
(MSPA, PRODES, emissões por pixel, fogo, métricas de paisagem).
"""

from __future__ import annotations

from typing import Iterable, Optional
import pystac
import xarray as xr
import rioxarray  # noqa: F401  # registra acessor .rio
import pandas as pd


class COGProvider:
    """Carrega ativos COG de uma coleção STAC como um xarray.Dataset empilhado no tempo."""

    def __init__(
        self,
        catalog_url: str,
        endpoint_url: Optional[str] = None,
        anon: bool = True,
    ) -> None:
        self.catalog_url = catalog_url
        self.endpoint_url = endpoint_url
        self.anon = anon
        self._catalog: pystac.Catalog = pystac.Catalog.from_file(catalog_url)

    def open_dataset(
        self,
        collection_id: str,
        version: str = "1.0",
        years: Optional[Iterable[int]] = None,
        chunks: dict | str = "auto",
    ) -> xr.Dataset:
        """Abre a coleção como xarray.Dataset empilhado (dim 'time')."""
        col = self._catalog.get_child(collection_id, recursive=True)
        if col is None:
            raise KeyError(collection_id)

        items = [
            it
            for it in col.get_all_items()
            if it.properties.get("version", "1.0") == version
        ]
        if years is not None:
            years = set(years)
            items = [
                it for it in items if pd.to_datetime(it.datetime).year in years
            ]
        items.sort(key=lambda it: it.datetime)

        arrays = []
        times = []
        for it in items:
            href = self._first_cog_href(it)
            da = rioxarray.open_rasterio(href, chunks=chunks, masked=True)
            if "band" in da.dims and da.sizes["band"] == 1:
                da = da.squeeze("band", drop=True)
            arrays.append(da)
            times.append(pd.to_datetime(it.datetime))

        ds = xr.concat(arrays, dim=pd.Index(times, name="time")).to_dataset(
            name=collection_id.split("-")[-1]
        )
        ds.attrs["collection"] = collection_id
        ds.attrs["version"] = version
        return ds

    @staticmethod
    def _first_cog_href(item: pystac.Item) -> str:
        for _, a in item.assets.items():
            if (a.media_type or "").startswith("image/tiff"):
                return a.href
        raise ValueError(f"Nenhum asset COG em {item.id}")
