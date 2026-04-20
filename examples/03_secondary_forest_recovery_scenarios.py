"""
Exemplo 03 — Projeções de recuperação de florestas secundárias (Zarr).

Compara Cenário A vs B para o estado do Pará em 2050 e 2100.
"""

import geopandas as gpd
import matplotlib.pyplot as plt
from ybyrastac import ZarrProvider, subset

CATALOG = "https://data.source.coop/celsohlsj/ybyra-br/catalog.json"
zarr = ZarrProvider(CATALOG)

# Carrega cubo completo (lazy via Dask)
ds = zarr.open_dataset("ybyra-secondary-forest-recovery", version="1.0")
print(ds)
# Dims esperados: time (1986–2100), y, x, scenario (A, B)

# Recorte para o Pará
pa = gpd.read_file(
    "https://raw.githubusercontent.com/giuliano-macedo/geodata-br-states/main/geojson/br_states/br_pa.json"
).geometry.iloc[0]
ds_pa = subset(ds, geometry=pa, crs="EPSG:4674")

# Comparação por cenário em anos milestone
for year in [2030, 2050, 2075, 2100]:
    ds_year = ds_pa.sel(time=str(year), method="nearest")
    diff = ds_year["agb"].sel(scenario="A") - ds_year["agb"].sel(scenario="B")
    lost = float(diff.mean())
    print(f"{year}: AGB perdido por legado de fogo (cenário A−B): {lost:.1f} Mg/ha")

# Mapa comparativo 2050
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
ds_pa.sel(time="2050", method="nearest")["agb"].sel(scenario="A").plot(
    ax=axes[0], cmap="YlGn", vmin=0, vmax=200,
    cbar_kwargs={"label": "AGB (Mg/ha)"}
)
axes[0].set_title("Cenário A — sem legado de fogo — 2050")
ds_pa.sel(time="2050", method="nearest")["agb"].sel(scenario="B").plot(
    ax=axes[1], cmap="YlGn", vmin=0, vmax=200,
    cbar_kwargs={"label": "AGB (Mg/ha)"}
)
axes[1].set_title("Cenário B — com legado de fogo (kf_2024) — 2050")
plt.tight_layout()
plt.savefig("recovery_pa_2050_scenarios.png", dpi=150)
print("✓ figura salva")
