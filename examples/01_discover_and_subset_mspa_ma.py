"""
Exemplo 01 — Descoberta e recorte de MSPA-MA.

    python examples/01_discover_and_subset_mspa_ma.py
"""

import geopandas as gpd
from ybyrastac import DiscoveryProvider, COGProvider, subset

CATALOG = "https://data.source.coop/celsohlsj/ybyra-br/catalog.json"

disc = DiscoveryProvider(CATALOG)
print("Temas:", disc.list_themes())
print("Coleções em 'fragmentation':")
for c in disc.list_collections(theme="fragmentation"):
    print(" -", c["id"], "|", c["title"])

cog = COGProvider(CATALOG)
ds = cog.open_dataset("ybyra-mspa-ma", version="1.0", years=[2020, 2021, 2022, 2023])
print(ds)

ma = gpd.read_file(
    "https://raw.githubusercontent.com/giuliano-macedo/geodata-br-states/main/geojson/br_states/br_ma.json"
).geometry.iloc[0]
ds_sub = subset(ds, geometry=ma, crs="EPSG:4674")
ds_sub.to_netcdf("mspa_ma_2020_2023.nc")
print("✓ salvou mspa_ma_2020_2023.nc")
