"""
Zarr provider: para cubos multidimensionais (ex.: projeções de recuperação
secundária 1986-2100 x cenário A/B, ensembles futuros bioclimáticos).
"""

from __future__ import annotations

from typing import Optional
import pystac
import xarray as xr
import fsspec


class ZarrProvider:
    """Abre coleções cujas `assets` apontam para stores Zarr."""

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
        consolidated: bool = True,
    ) -> xr.Dataset:
        col = self._catalog.get_child(collection_id, recursive=True)
        if col is None:
            raise KeyError(collection_id)

        zarr_asset = None
        for it in col.get_all_items():
            if it.properties.get("version", "1.0") != version:
                continue
            for a in it.assets.values():
                if (a.media_type or "").endswith("zarr") or a.href.endswith(".zarr"):
                    zarr_asset = a
                    break
            if zarr_asset:
                break
        if zarr_asset is None:
            raise ValueError(f"Nenhum asset Zarr em {collection_id}@{version}")

        storage_opts = {}
        if self.endpoint_url:
            storage_opts = {
                "client_kwargs": {"endpoint_url": self.endpoint_url},
                "anon": self.anon,
            }
        mapper = fsspec.get_mapper(zarr_asset.href, **storage_opts)
        ds = xr.open_zarr(mapper, consolidated=consolidated)
        ds.attrs["collection"] = collection_id
        ds.attrs["version"] = version
        return ds
