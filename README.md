# YbYráSTAC

**YbYráSTAC** é uma biblioteca Python e catálogo STAC (SpatioTemporal Asset Catalog)
para descoberta e acesso cloud-native aos produtos de Observação da Terra gerados
no âmbito do projeto **YbYrá-BR / CCAL-IPAM / GCBC**, com foco em florestas
brasileiras, fragmentação, emissões, fogo e recuperação de vegetação secundária.

Inspirado em [eoforeststac](https://github.com/simonbesnard1/eoforeststac)
(Simon Besnard / GFZ), adaptado para o contexto brasileiro.

## Principais produtos do catálogo (piloto)

| Coleção | Descrição | Resolução | Cobertura | Formato |
|--------|-----------|-----------|-----------|---------|
| `ybyra-secondary-forest-brazil` | Secondary Forest Brazil — YbYrá-BR v8.1 (MapBiomas Col 10.1) | 30 m | BR, 1986–2024 | COG |
| `ybyra-mspa-br` | MSPA para Brasil (biomas) | 30 m | BR, 1985–2023 | COG |
| `ybyra-primary-forest` | Vegetação primária MapBiomas Col 10.1 (remapeada) | 30 m | BR | COG |
| `ybyra-emissions-brazil` | Emissões unificadas (CO₂/CH₄/N₂O) — desmatamento, fogo, exploração seletiva | 30 m | BR, 1985–2023 | COG |
| `ybyra-secondary-forest-recovery` | Recuperação de florestas secundárias (Chapman-Richards, cenários A/B) | 30 m | BR, 1986–2100 | Zarr |
| `ybyra-fire-probability-pa` | Probabilidade de fogo — Pará (Random Forest, AUC=0.933) | 1 km | PA | COG |
| `ybyra-landscape-metrics-pa` | Métricas de paisagem (ED, MPA, ENN, NP) | 1 km | PA | COG |

## Instalação

```bash
python -m pip install "git+https://github.com/celsohlsj/ybyrastac.git"
```

Requer Python >= 3.10.

## Quick start

```python
from ybyrastac.providers.discovery import DiscoveryProvider
from ybyrastac.providers.cog import COGProvider
from ybyrastac.providers.subset import subset
import geopandas as gpd

CATALOG = "https://raw.githubusercontent.com/celsohlsj/ybyrastac/main/stac_catalog/catalog.json"

# 1. Descoberta
disc = DiscoveryProvider(catalog_url=CATALOG)
disc.list_themes()                      # ['fragmentation', 'emissions', ...]
disc.list_collections(theme="secondary-forest")

# 2. Carregamento cloud-native (sem download)
provider = COGProvider(catalog_url=CATALOG)
ds = provider.open_dataset(
    collection_id="ybyra-secondary-forest-brazil",
    version="8.1",
    years=[2020, 2022, 2024],
)

# 3. Recorte espacial
br = gpd.read_file("brasil.geojson")
ds_subset = subset(ds, geometry=br.geometry.iloc[0], crs="EPSG:4674")
ds_subset.rio.to_raster("secondary_forest_brazil_2020_2024.tif")
```

## Browser interativo

<https://celsohlsj.github.io/ybyrastac/>

## Documentação

<https://ybyrastac.readthedocs.io/>

## Licença

Software: **EUPL-1.2** (compatível com eoforeststac original).
Dados: **CC-BY-4.0** (citação obrigatória).

## Como citar

> Silva Junior, C. H. L. et al. (2026). YbYráSTAC: A toolbox for accessing
> Brazilian forest Earth Observation datasets. GitHub:
> https://github.com/celsohlsj/ybyrastac

## Financiamento

CNPq (Bolsa PQ-C), IPAM, GCBC-UK, YbYrá-BR, UFMA/PPGBC.

## Contato

Celso H. L. Silva Junior — `celso.junior@ufma.br` / IPAM / UFMA
