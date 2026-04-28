"""
build_ybyra_stac.py
===================

Gera automaticamente Collection + Items STAC para TODOS os produtos YbYrá-BR
diretamente a partir das URLs públicas no Source Cooperative.

Não requer arquivos locais — usa o inventário do bucket S3-compatible.

Uso:
    pip install pystac
    python scripts/stac_generation/build_ybyra_stac.py

    # ou com opções:
    python scripts/stac_generation/build_ybyra_stac.py \\
        --base-href https://data.source.coop/ybyra-br \\
        --out stac_catalog/ \\
        --collections ybyra-secondary-forest-brazil ybyra-mspa-br

Depois de gerado, sincronize com o Source Cooperative:
    aws s3 sync stac_catalog/ s3://ybyra-br/ \\
        --endpoint-url https://data.source.coop \\
        --acl public-read \\
        --content-type application/json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pystac

# ---------------------------------------------------------------------------
# Bounding boxes por escopo geográfico (EPSG:4326, [W, S, E, N])
# ---------------------------------------------------------------------------
BBOX_BRAZIL = [-73.9873, -33.7683, -28.6468,  5.2718]
BBOX_PARA   = [-54.9692,  -9.8375, -45.8780,  2.5928]

GEOMETRY_BRAZIL = {
    "type": "Polygon",
    "coordinates": [[
        [-73.9873,  5.2718], [-28.6468,  5.2718],
        [-28.6468, -33.7683], [-73.9873, -33.7683],
        [-73.9873,  5.2718],
    ]]
}
GEOMETRY_PARA = {
    "type": "Polygon",
    "coordinates": [[
        [-54.9692,  2.5928], [-45.8780,  2.5928],
        [-45.8780, -9.8375], [-54.9692, -9.8375],
        [-54.9692,  2.5928],
    ]]
}

COG  = "image/tiff; application=geotiff; profile=cloud-optimized"
ZARR = "application/vnd+zarr"

# ---------------------------------------------------------------------------
# Definição de todas as coleções YbYrá-BR
# ---------------------------------------------------------------------------
# Cada entrada define:
#   bucket_prefix : prefixo no bucket S3 (relativo a base_href)
#   bbox / geometry: extensão espacial
#   gsd           : resolução espacial em metros
#   epsg          : CRS
#   years_*       : dicionário {produto: lista de anos} ou lista simples
#   filename_tpl  : template do nome do arquivo (usa .format(product=, year=))
#   assets        : lista de assets por produto
#   temporal      : [start_year, end_year]

COLLECTIONS: dict[str, dict] = {

    # ------------------------------------------------------------------
    "ybyra-secondary-forest-brazil": {
        "title": "Secondary Forest Brazil — YbYrá-BR v8.1",
        "description": (
            "Annual maps of secondary forest dynamics (age, extent, increment, loss) "
            "for Brazil from 1986 to 2024, derived from MapBiomas Collection 10.1 "
            "using Google Earth Engine. Forest Formation and Flooded Forest included."
        ),
        "bucket_prefix": "secondary-forest",
        "bbox": BBOX_BRAZIL,
        "geometry": GEOMETRY_BRAZIL,
        "gsd": 30,
        "epsg": 4326,
        "temporal": [1986, 2024],
        "assets": [
            {
                "key": "age",
                "title": "Secondary Forest Age",
                "description": "Years of continuous secondary forest since last disturbance.",
                "subdir": "age",
                "filename_tpl": "ybyra_secondary_forest_age_brazil_v8_1_{year}.tif",
                "years": list(range(1986, 2025)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "extent",
                "title": "Secondary Forest Extent",
                "description": "Binary presence/absence of secondary forest (1 = present).",
                "subdir": "extent",
                "filename_tpl": "ybyra_secondary_forest_extent_brazil_v8_1_{year}.tif",
                "years": list(range(1986, 2025)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "increment",
                "title": "Secondary Forest Increment",
                "description": "New secondary forest pixels per year (1 = new in this year).",
                "subdir": "increment",
                "filename_tpl": "ybyra_secondary_forest_increment_brazil_v8_1_{year}.tif",
                "years": list(range(1986, 2025)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "loss",
                "title": "Secondary Forest Loss",
                "description": "Secondary forest pixels cleared per year (1 = lost in this year).",
                "subdir": "loss",
                "filename_tpl": "ybyra_secondary_forest_loss_brazil_v8_1_{year}.tif",
                "years": list(range(1987, 2025)),  # loss começa em 1987
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "secondary forest", "Brazil", "Amazon", "Cerrado", "forest age",
            "forest dynamics", "deforestation", "MapBiomas", "Landsat",
            "remote sensing", "YbYrá-BR",
        ],
        "sci_doi": "10.1038/s41597-020-00600-4",
        "sci_citation": (
            "Silva Junior, C. H. L. et al. (2020). Benchmark maps of 33 years of "
            "secondary forest age for Brazil. Scientific Data. "
            "https://doi.org/10.1038/s41597-020-00600-4"
        ),
        "platform": "landsat",
        "instruments": ["OLI", "TM", "ETM+"],
        "source_coop_url": "https://source.coop/ybyra-br/secondary-forest",
    },

    # ------------------------------------------------------------------
    "ybyra-mspa-br": {
        "title": "MSPA Brasil — YbYrá-BR",
        "description": (
            "Annual Morphological Spatial Pattern Analysis (MSPA) for all Brazilian biomes. "
            "Mosaic-first workflow. EEW=34px, FGCONN=8, TRANSITION=1, INTERNAL=1. "
            "30m EPSG:4674."
        ),
        "bucket_prefix": "fragmentation",
        "bbox": BBOX_BRAZIL,
        "geometry": GEOMETRY_BRAZIL,
        "gsd": 30,
        "epsg": 4674,
        "temporal": [1985, 2023],
        "assets": [
            {
                "key": "mspa",
                "title": "MSPA Classification",
                "description": "Annual MSPA map (8 classes: core, islet, perforation, edge, loop, bridge, branch, background).",
                "subdir": "",
                "filename_tpl": "ybyra_mspa_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "MSPA", "fragmentation", "forest fragmentation", "Brazil",
            "morphological pattern", "landscape ecology", "YbYrá-BR",
        ],
        "sci_doi": None,
        "sci_citation": None,
        "platform": "landsat",
        "instruments": ["OLI", "TM", "ETM+"],
        "source_coop_url": "https://source.coop/ybyra-br/fragmentation",
    },

    # ------------------------------------------------------------------
    "ybyra-primary-forest": {
        "title": "Primary Forest Mask Brasil — YbYrá-BR",
        "description": (
            "Binary primary forest mask from MapBiomas Collection 10.1 "
            "(brazil_pret_vegetation_qcn_v2). brazilForests mask applied. 30m EPSG:4674."
        ),
        "bucket_prefix": "primary-forest",
        "bbox": BBOX_BRAZIL,
        "geometry": GEOMETRY_BRAZIL,
        "gsd": 30,
        "epsg": 4674,
        "temporal": [1985, 2023],
        "assets": [
            {
                "key": "primary_forest",
                "title": "Primary Forest Mask",
                "description": "Binary primary forest presence (1 = primary forest).",
                "subdir": "",
                "filename_tpl": "ybyra_primary_forest_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "primary forest", "Brazil", "MapBiomas", "land cover",
            "deforestation", "YbYrá-BR",
        ],
        "sci_doi": None,
        "sci_citation": None,
        "platform": "landsat",
        "instruments": ["OLI", "TM", "ETM+"],
        "source_coop_url": "https://source.coop/ybyra-br/primary-forest",
    },

    # ------------------------------------------------------------------
    "ybyra-emissions-brazil": {
        "title": "Unified GHG Emissions Brasil — YbYrá-BR",
        "description": (
            "Annual pixel-level GHG emissions (CO₂/CH₄/N₂O) from deforestation, fire, "
            "and selective logging across all Brazilian biomes. "
            "brazilForests mask applied to ALL input layers. "
            "FREL v2.1 methodology. 30m EPSG:4674. 1985–2023."
        ),
        "bucket_prefix": "emissions",
        "bbox": BBOX_BRAZIL,
        "geometry": GEOMETRY_BRAZIL,
        "gsd": 30,
        "epsg": 4674,
        "temporal": [1985, 2023],
        "assets": [
            {
                "key": "deforestation_co2",
                "title": "Deforestation CO₂ Emissions",
                "description": "Annual CO₂ emissions from deforestation (t CO₂ eq/pixel).",
                "subdir": "deforestation",
                "filename_tpl": "ybyra_emissions_deforestation_co2_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "deforestation_ch4",
                "title": "Deforestation CH₄ Emissions",
                "description": "Annual CH₄ emissions from deforestation (t CO₂ eq/pixel).",
                "subdir": "deforestation",
                "filename_tpl": "ybyra_emissions_deforestation_ch4_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "deforestation_n2o",
                "title": "Deforestation N₂O Emissions",
                "description": "Annual N₂O emissions from deforestation (t CO₂ eq/pixel).",
                "subdir": "deforestation",
                "filename_tpl": "ybyra_emissions_deforestation_n2o_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "fire_co2",
                "title": "Fire CO₂ Emissions",
                "description": "Annual CO₂ emissions from fire (t CO₂ eq/pixel).",
                "subdir": "fire",
                "filename_tpl": "ybyra_emissions_fire_co2_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "selective_logging_co2",
                "title": "Selective Logging CO₂ Emissions",
                "description": "Annual CO₂ emissions from selective logging (t CO₂ eq/pixel).",
                "subdir": "selective-logging",
                "filename_tpl": "ybyra_emissions_selective_logging_co2_brazil_{year}.tif",
                "years": list(range(1985, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "GHG emissions", "CO2", "CH4", "N2O", "deforestation",
            "fire emissions", "selective logging", "Brazil", "REDD+",
            "FREL", "SEEG", "YbYrá-BR",
        ],
        "sci_doi": "10.1038/s41467-024-45949-x",
        "sci_citation": (
            "Silva Junior, C. H. L. et al. (2024). Increased deforestation and forest "
            "degradation counteract Brazil's REDD+ results in 2022. "
            "Nature Communications. https://doi.org/10.1038/s41467-024-45949-x"
        ),
        "platform": "landsat",
        "instruments": ["OLI", "TM", "ETM+"],
        "source_coop_url": "https://source.coop/ybyra-br/emissions",
    },

    # ------------------------------------------------------------------
    "ybyra-fire-probability-pa": {
        "title": "Fire Probability Pará — YbYrá-BR",
        "description": (
            "Annual fire probability maps for the state of Pará, Brazil. "
            "Random Forest model, AUC-ROC=0.933. "
            "ERA5-Land climate variables + vegetation predictors. "
            "1km resolution, EPSG:4674. Scale factor 10000 (uint16 → [0,1])."
        ),
        "bucket_prefix": "fire-probability",
        "bbox": BBOX_PARA,
        "geometry": GEOMETRY_PARA,
        "gsd": 1000,
        "epsg": 4674,
        "temporal": [2001, 2023],
        "assets": [
            {
                "key": "fire_probability",
                "title": "Fire Probability",
                "description": "Annual fire probability [0–1] × 10000 (uint16).",
                "subdir": "",
                "filename_tpl": "ybyra_fire_probability_para_{year}.tif",
                "years": list(range(2001, 2024)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "fire probability", "wildfire", "Pará", "Amazon", "Brazil",
            "Random Forest", "ERA5-Land", "remote sensing", "YbYrá-BR",
        ],
        "sci_doi": None,
        "sci_citation": None,
        "platform": "era5-land",
        "instruments": ["ERA5-Land"],
        "source_coop_url": "https://source.coop/ybyra-br/fire-probability",
    },

    # ------------------------------------------------------------------
    "ybyra-secondary-forest-recovery": {
        "title": "Secondary Forest Carbon Recovery Brasil — YbYrá-BR",
        "description": (
            "Chapman-Richards aboveground biomass projections for secondary forests "
            "in Brazil (1986–2100), under two scenarios: "
            "Scenario A (no fire legacy, k₀) and Scenario B (fire legacy, kf_2024). "
            "Parameters: k and b from Robinson et al. (2025); "
            "asymptote A from 4th National Inventory; m=0.67 (Bukoski et al. 2022). "
            "Stratified by phytophysiognomy × biome × state. 30m EPSG:4674."
        ),
        "bucket_prefix": "secondary-forest-recovery",
        "bbox": BBOX_BRAZIL,
        "geometry": GEOMETRY_BRAZIL,
        "gsd": 30,
        "epsg": 4674,
        "temporal": [1986, 2100],
        "assets": [
            {
                "key": "scenario_a",
                "title": "Scenario A — No Fire Legacy",
                "description": "AGB projection without fire legacy effect (k₀). t C/ha.",
                "subdir": "scenario_a",
                "filename_tpl": "ybyra_recovery_scenario_a_brazil_{year}.tif",
                "years": list(range(1986, 2101)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
            {
                "key": "scenario_b",
                "title": "Scenario B — Fire Legacy kf_2024",
                "description": "AGB projection with fire legacy effect (kf_2024). t C/ha.",
                "subdir": "scenario_b",
                "filename_tpl": "ybyra_recovery_scenario_b_brazil_{year}.tif",
                "years": list(range(1986, 2101)),
                "media_type": COG,
                "roles": ["data", "cloud-optimized"],
            },
        ],
        "license": "CC-BY-4.0",
        "keywords": [
            "carbon recovery", "secondary forest", "Chapman-Richards", "biomass",
            "Brazil", "fire legacy", "forest restoration", "REDD+",
            "Robinson 2025", "YbYrá-BR",
        ],
        "sci_doi": "10.1038/s41558-025-02234-5",
        "sci_citation": (
            "Robinson, B. E. et al. (2025). Global carbon accumulation rates in "
            "secondary forests. Nature Climate Change. "
            "https://doi.org/10.1038/s41558-025-02234-5"
        ),
        "platform": "landsat",
        "instruments": ["OLI", "TM", "ETM+"],
        "source_coop_url": "https://source.coop/ybyra-br/secondary-forest-recovery",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def asset_href(base_href: str, bucket_prefix: str, subdir: str, filename: str) -> str:
    parts = [base_href, bucket_prefix]
    if subdir:
        parts.append(subdir)
    parts.append(filename)
    return "/".join(parts)


def all_years_in_collection(cfg: dict) -> list[int]:
    years = set()
    for asset in cfg["assets"]:
        years.update(asset["years"])
    return sorted(years)


# ---------------------------------------------------------------------------
# Geração de itens
# ---------------------------------------------------------------------------

def make_items(cfg: dict, collection_id: str, base_href: str) -> list[pystac.Item]:
    items = []
    bucket_prefix = cfg["bucket_prefix"]
    all_years = all_years_in_collection(cfg)

    for year in all_years:
        item = pystac.Item(
            id=f"{collection_id}-{year}",
            geometry=cfg["geometry"],
            bbox=cfg["bbox"],
            datetime=datetime(year, 12, 31, tzinfo=timezone.utc),
            properties={
                "start_datetime": f"{year}-01-01T00:00:00Z",
                "end_datetime":   f"{year}-12-31T23:59:59Z",
                "title":          f"{cfg['title']} — {year}",
                "platform":       cfg.get("platform", "landsat"),
                "instruments":    cfg.get("instruments", []),
                "gsd":            cfg["gsd"],
                "proj:epsg":      cfg["epsg"],
                "license":        cfg["license"],
                **({"sci:doi":      cfg["sci_doi"]}     if cfg.get("sci_doi")      else {}),
                **({"sci:citation": cfg["sci_citation"]} if cfg.get("sci_citation") else {}),
            },
        )

        # Adiciona cada asset disponível para este ano
        for asset_def in cfg["assets"]:
            if year not in asset_def["years"]:
                continue
            filename = asset_def["filename_tpl"].format(year=year)
            href = asset_href(base_href, bucket_prefix, asset_def["subdir"], filename)
            item.add_asset(
                asset_def["key"],
                pystac.Asset(
                    href=href,
                    media_type=asset_def["media_type"],
                    title=asset_def["title"],
                    description=asset_def["description"],
                    roles=asset_def["roles"],
                ),
            )

        items.append(item)

    return items


# ---------------------------------------------------------------------------
# Geração de Collection
# ---------------------------------------------------------------------------

def make_collection(cfg: dict, collection_id: str, items: list[pystac.Item]) -> pystac.Collection:
    start_year, end_year = cfg["temporal"]
    collection = pystac.Collection(
        id=collection_id,
        description=cfg["description"],
        title=cfg["title"],
        license=cfg["license"],
        keywords=cfg.get("keywords", []),
        providers=[
            pystac.Provider(
                name="YbYrá-BR Project",
                roles=[pystac.ProviderRole.PRODUCER, pystac.ProviderRole.LICENSOR],
                url="https://github.com/celsohlsj/ybyrastac",
            ),
            pystac.Provider(
                name="Source Cooperative",
                roles=[pystac.ProviderRole.HOST],
                url=cfg.get("source_coop_url", "https://source.coop/ybyra-br"),
            ),
        ],
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([cfg["bbox"]]),
            temporal=pystac.TemporalExtent([[
                datetime(start_year, 1, 1, tzinfo=timezone.utc),
                datetime(end_year,   12, 31, tzinfo=timezone.utc),
            ]]),
        ),
        extra_fields={
            **({"sci:doi":      cfg["sci_doi"]}     if cfg.get("sci_doi")      else {}),
            **({"sci:citation": cfg["sci_citation"]} if cfg.get("sci_citation") else {}),
            "item_assets": {
                a["key"]: {
                    "title":       a["title"],
                    "description": a["description"],
                    "type":        a["media_type"],
                    "roles":       a["roles"],
                }
                for a in cfg["assets"]
            },
        },
    )

    collection.add_link(pystac.Link(
        rel="cite-as",
        target=f"https://doi.org/{cfg['sci_doi']}" if cfg.get("sci_doi") else
               "https://github.com/celsohlsj/ybyrastac",
        title=cfg.get("sci_citation", "YbYráSTAC"),
    ))
    collection.add_link(pystac.Link(
        rel="related",
        target="https://github.com/celsohlsj/ybyrastac",
        title="YbYráSTAC Python library",
    ))

    for item in items:
        collection.add_item(item)

    return collection


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Gera catálogo STAC YbYrá-BR (sem arquivos locais).")
    ap.add_argument(
        "--base-href",
        default="https://data.source.coop/ybyra-br",
        help="URL pública base do bucket (default: https://data.source.coop/ybyra-br)",
    )
    ap.add_argument(
        "--out",
        default="stac_catalog",
        help="Diretório de saída (default: stac_catalog/)",
    )
    ap.add_argument(
        "--collections",
        nargs="*",
        help="Processar apenas estas coleções (default: todas)",
    )
    args = ap.parse_args()

    base_href = args.base_href.rstrip("/")
    out_root  = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    selected  = set(args.collections) if args.collections else set(COLLECTIONS)

    print(f"\n{'='*60}")
    print(f"  YbYrá STAC builder")
    print(f"  base-href : {base_href}")
    print(f"  output    : {out_root}")
    print(f"  coleções  : {', '.join(sorted(selected))}")
    print(f"{'='*60}\n")

    # Root catalog
    root_cat = pystac.Catalog(
        id="ybyra-br",
        description=(
            "YbYráSTAC: Brazilian forest Earth Observation datasets. "
            "YbYrá-BR Project. Funded by CNPq (Process 401741/2023-0)."
        ),
        title="YbYrá-BR STAC Catalog",
        extra_fields={
            "funding": "CNPq Process 401741/2023-0",
        },
    )
    root_cat.add_link(pystac.Link(
        rel="related",
        target="https://github.com/celsohlsj/ybyrastac",
        title="YbYráSTAC GitHub",
    ))

    for collection_id, cfg in COLLECTIONS.items():
        if collection_id not in selected:
            continue

        print(f"  Processando {collection_id} ...")
        items      = make_items(cfg, collection_id, base_href)
        collection = make_collection(cfg, collection_id, items)
        root_cat.add_child(collection)
        print(f"  ✓ {len(items)} itens")

    # Salva tudo
    root_cat.normalize_hrefs(str(out_root))
    root_cat.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)

    # Contagem final
    total_items = sum(
        1 for _ in root_cat.get_items(recursive=True)
    )
    print(f"\n✓ Catálogo gerado: {out_root}/catalog.json")
    print(f"  {total_items} itens no total")
    print(f"\nPróximos passos:")
    print(f"  # Validar")
    print(f"  pip install stac-validator")
    print(f"  stac-validator {out_root}/catalog.json --recursive")
    print(f"\n  # Sincronizar com o Source Cooperative")
    print(f"  aws s3 sync {out_root}/ s3://ybyra-br/ \\")
    print(f"      --endpoint-url https://data.source.coop \\")
    print(f"      --acl public-read \\")
    print(f"      --content-type application/json")
    print(f"\n  # Abrir no STAC Browser")
    print(f"  https://radiantearth.github.io/stac-browser/#/external/{base_href}/catalog.json")


if __name__ == "__main__":
    main()