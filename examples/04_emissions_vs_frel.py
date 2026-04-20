"""
Exemplo 04 — Emissões anuais do Brasil vs National FREL.

Replica parcialmente a análise do manuscrito Nature Comm.
(Silva Junior et al., 'Increased deforestation and forest degradation
counteract Brazil's REDD+ results in 2022').
"""

import pandas as pd
import matplotlib.pyplot as plt
from ybyrastac import COGProvider

CATALOG = "https://data.source.coop/celsohlsj/ybyra-br/catalog.json"
cog = COGProvider(CATALOG)

# Carrega emissões de desmatamento CO2 para todos os anos disponíveis
ds_emis = cog.open_dataset(
    "ybyra-emissions-brazil",
    version="1.0",
)

# Agrega pixels → total nacional por ano (Mg CO2 eq/ano)
# (pixel = 30 m → 0.09 ha; 1 ha = 10000 m²)
PIXEL_AREA_HA = (30 * 30) / 10_000
totals = []
for t in ds_emis.time:
    val = float(
        ds_emis["deforestation_co2"].sel(time=t).sum() * PIXEL_AREA_HA / 1e6
    )  # Mt CO2 eq
    totals.append({"year": int(str(t.values)[:4]), "emissions_MtCO2eq": val})

df = pd.DataFrame(totals).set_index("year")

# National FREL (replicado via GEE, ver celsohlsj/Brazil-National-FREL)
FREL = 672  # Mt CO2 eq/ano (valor de referência)

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(df.index, df["emissions_MtCO2eq"], color="#c0392b", alpha=0.8, label="Emissões YbYrá-BR")
ax.axhline(FREL, color="navy", ls="--", lw=1.5, label=f"National FREL ({FREL} Mt CO₂ eq/ano)")
ax.set_xlabel("Ano")
ax.set_ylabel("Mt CO₂ eq / ano")
ax.set_title("Emissões de desmatamento Brasil vs National FREL")
ax.legend()
plt.tight_layout()
plt.savefig("brazil_emissions_vs_frel.png", dpi=150)
print("✓ figura salva")
print(df.to_string())
