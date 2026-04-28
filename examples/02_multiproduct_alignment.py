"""
Exemplo 02 — Alinhamento multi-produto.

Carrega MSPA-MA + Emissões-BR + Fogo-PA em uma grade comum (resolução do MSPA).
"""

from ybyrastac import COGProvider
from ybyrastac.utils import align_on_common_grid

CATALOG = "https://raw.githubusercontent.com/celsohlsj/ybyrastac/main/stac_catalog/catalog.json"
cog = COGProvider(CATALOG)

mspa  = cog.open_dataset("ybyra-mspa-ma",           years=[2023])
emis  = cog.open_dataset("ybyra-emissions-brazil",  years=[2023])
fire  = cog.open_dataset("ybyra-fire-probability-pa", years=[2023])

emis_on_mspa, fire_on_mspa = align_on_common_grid(
    [emis, fire],
    reference=mspa,
    resampling="bilinear",
)
print("Todas alinhadas:", mspa.rio.resolution(), emis_on_mspa.rio.resolution())
