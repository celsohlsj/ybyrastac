"""
Exemplo 01 — Descoberta e recorte de Secondary Forest Brazil.

    python examples/01_discover_and_subset_secondary_forest.py
"""

import geopandas as gpd
from ybyrastac import DiscoveryProvider, COGProvider, subset

CATALOG = "https://raw.githubusercontent.com/celsohlsj/ybyrastac/main/stac_catalog/catalog.json"

disc = DiscoveryProvider(CATALOG)
print("Temas:", disc.list_themes())
print("Coleções em 'secondary-forest':")
for c in disc.list_collections(theme="secondary-forest"):
    print(" -", c["id"], "|", c["title"])

cog = COGProvider(CATALOG)
ds = cog.open_dataset("ybyra-secondary-forest-brazil", version="8.1", years=[2020, 2021, 2022, 2023, 2024])
print(ds)

br = gpd.read_file(
    "https://raw.githubusercontent.com/giuliano-macedo/geodata-br-states/main/geojson/br_states/br_all.json"
).geometry.dissolve().iloc[0]
ds_sub = subset(ds, geometry=br, crs="EPSG:4674")
ds_sub.to_netcdf("secondary_forest_brazil_2020_2024.nc")
print("✓ salvou secondary_forest_brazil_2020_2024.nc")
