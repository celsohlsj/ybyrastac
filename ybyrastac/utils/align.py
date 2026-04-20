"""Reamostragem de múltiplos Datasets em uma grade comum (reference)."""

from __future__ import annotations

from typing import Iterable
import xarray as xr


def align_on_common_grid(
    datasets: Iterable[xr.Dataset],
    reference: xr.Dataset,
    resampling: str = "nearest",
) -> list[xr.Dataset]:
    """Reprojeta uma lista de datasets para o CRS, extensão e grade do `reference`."""
    out = []
    for ds in datasets:
        ds_r = ds.rio.reproject_match(reference, resampling=resampling)
        out.append(ds_r)
    return out
