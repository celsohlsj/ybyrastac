"""
build_ybyra_stac.py
===================

Gera automaticamente Collection + Items STAC para TODOS os produtos YbYrá-BR
a partir de um diretório local de COGs (organizados por produto/versão).

Estrutura esperada em --input-root:
    <input-root>/
      fragmentation/ybyra-mspa-ma/v1.0/*.tif
      fragmentation/ybyra-mspa-br/v1.0/*.tif
      primary-forest/ybyra-primary-forest/v1.0/*.tif
      emissions/ybyra-emissions-brazil/v1.0/*.tif   (prefixo: deforestation_co2_, fire_co2_, ...)
      fire/ybyra-fire-probability-pa/v1.0/*.tif
      recovery/ybyra-secondary-forest-recovery/v1.0/*.tif  + *.zarr/

Uso:
    python scripts/stac_generation/build_ybyra_stac.py \\
        --input-root /data/cog \\
        --base-href https://data.source.coop/celsohlsj/ybyra-br \\
        --out stac_catalog/
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pystac
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box, mapping

YEAR_RE = re.compile(r"(\d{4})")

# ------------------------------------------------------------------
# Configurações de cada coleção
# ------------------------------------------------------------------
COLLECTIONS = {
    "ybyra-mspa-ma": {
        "theme": "fragmentation",
        "title": "MSPA — Maranhão",
        "description": (
            "Annual MSPA of MapBiomas Col 10.1 primary forest for Maranhão. "
            "EEW=34px, FGCONN=8, TRANSITION=1, INTERNAL=1. 30m EPSG:4674."
        ),
        "asset_key": "data",
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": False,
    },
    "ybyra-mspa-br": {
        "theme": "fragmentation",
        "title": "MSPA — Brasil",
        "description": (
            "Annual MSPA for all Brazilian biomes. Mosaic-first workflow. "
            "EEW=34px, FGCONN=8, TRANSITION=1, INTERNAL=1. 30m EPSG:4674."
        ),
        "asset_key": "data",
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": False,
    },
    "ybyra-primary-forest": {
        "theme": "primary-forest",
        "title": "Primary Forest Mask — Brasil",
        "description": (
            "Binary primary forest mask from MapBiomas Col 10.1 "
            "(brazil_pret_vegetation_qcn_v2). brazilForests mask applied. 30m EPSG:4674."
        ),
        "asset_key": "data",
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": False,
    },
    "ybyra-emissions-brazil": {
        "theme": "emissions",
        "title": "Unified GHG Emissions — Brasil",
        "description": (
            "Annual GHG pixel rasters (CO₂/CH₄/N₂O) from deforestation, fire, "
            "selective logging. brazilForests mask applied to ALL inputs. 30m EPSG:4674."
        ),
        "asset_key": None,           # múltiplos assets por item (multi_asset=True)
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": True,
        # Prefixos dos arquivos → nome do asset STAC
        "asset_map": {
            "deforestation_co2":       "Deforestation CO₂",
            "deforestation_ch4":       "Deforestation CH₄",
            "deforestation_n2o":       "Deforestation N₂O",
            "fire_co2":                "Fire CO₂ (Amazon)",
            "selective_logging_co2":   "Selective Logging CO₂ (Amazon)",
        },
    },
    "ybyra-fire-probability-pa": {
        "theme": "fire",
        "title": "Fire Probability — Pará",
        "description": (
            "Annual fire probability (Random Forest, AUC-ROC=0.933) for Pará. "
            "1km EPSG:4674. Scale factor 10000 (uint16 → [0,1])."
        ),
        "asset_key": "data",
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": False,
    },
    "ybyra-secondary-forest-recovery": {
        "theme": "recovery",
        "title": "Secondary Forest Recovery — Brasil",
        "description": (
            "Chapman-Richards AGB projections 1986–2100, scenarios A (k₀) and B (kf_2024). "
            "Robinson et al. 2025 parameters. β=0.4638, m=0.67. 30m EPSG:4674."
        ),
        "asset_key": None,
        "asset_media_type": pystac.MediaType.COG,
        "multi_asset": True,
        "asset_map": {
            "scenario_a": "Scenario A (no-fire legacy)",
            "scenario_b": "Scenario B (fire legacy kf_2024)",
            "timeseries":  "Full time-series Zarr",
        },
    },
}

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def bbox_footprint_meta(path: Path):
    with rasterio.open(path) as src:
        bounds = src.bounds
        bbox = list(transform_bounds(src.crs, "EPSG:4326", *bounds))
        footprint = mapping(box(*bbox))
        return bbox, footprint, float(src.res[0]), src.crs.to_epsg()


def year_from_stem(stem: str) -> Optional[int]:
    m = YEAR_RE.search(stem)
    return int(m.group(1)) if m else None


def make_item(
    collection_id: str,
    tif: Path,
    year: int,
    base_href: str,
    theme: str,
    version: str,
    asset_key: str = "data",
    asset_title: str = "",
    media_type: str = pystac.MediaType.COG,
) -> pystac.Item:
    bbox, footprint, gsd, epsg = bbox_footprint_meta(tif)
    href = f"{base_href}/{theme}/{collection_id}/v{version}/{tif.name}"
    item = pystac.Item(
        id=f"{collection_id}_{year}",
        geometry=footprint,
        bbox=bbox,
        datetime=datetime(year, 1, 1, tzinfo=timezone.utc),
        properties={
            "start_datetime": f"{year}-01-01T00:00:00Z",
            "end_datetime":   f"{year}-12-31T23:59:59Z",
            "version": version,
            "gsd": 30,
            "proj:epsg": epsg,
        },
    )
    item.add_asset(
        asset_key,
        pystac.Asset(
            href=href,
            media_type=media_type,
            roles=["data"],
            title=asset_title or f"{collection_id} {year}",
        ),
    )
    return item


# ------------------------------------------------------------------
# Builders por tipo de coleção
# ------------------------------------------------------------------

def build_single_asset_collection(
    cfg: dict, collection_id: str, tif_dir: Path, base_href: str, version: str
) -> list[pystac.Item]:
    items = []
    for tif in sorted(tif_dir.glob("*.tif")):
        year = year_from_stem(tif.stem)
        if year is None:
            continue
        item = make_item(
            collection_id, tif, year, base_href,
            cfg["theme"], version, "data",
            f"{cfg['title']} {year}", cfg["asset_media_type"],
        )
        items.append(item)
    return items


def build_multi_asset_collection(
    cfg: dict, collection_id: str, tif_dir: Path, base_href: str, version: str
) -> list[pystac.Item]:
    """Agrupa múltiplos TIFs do mesmo ano em um único Item STAC."""
    asset_map: dict[str, str] = cfg["asset_map"]
    theme = cfg["theme"]

    # descobrir anos únicos presentes
    years: dict[int, list[Path]] = {}
    for tif in sorted(tif_dir.glob("*.tif")):
        year = year_from_stem(tif.stem)
        if year is None:
            continue
        years.setdefault(year, []).append(tif)

    items = []
    for year, tifs in sorted(years.items()):
        # referência de bbox/footprint do primeiro arquivo
        bbox, footprint, gsd, epsg = bbox_footprint_meta(tifs[0])
        item = pystac.Item(
            id=f"{collection_id}_{year}",
            geometry=footprint,
            bbox=bbox,
            datetime=datetime(year, 1, 1, tzinfo=timezone.utc),
            properties={
                "start_datetime": f"{year}-01-01T00:00:00Z",
                "end_datetime":   f"{year}-12-31T23:59:59Z",
                "version": version,
                "gsd": gsd,
                "proj:epsg": epsg,
            },
        )
        # adiciona um asset para cada prefixo encontrado
        for tif in tifs:
            matched_key = None
            for prefix, label in asset_map.items():
                if tif.stem.startswith(prefix) or prefix in tif.stem:
                    matched_key = prefix
                    break
            if matched_key is None:
                matched_key = tif.stem  # fallback

            href = f"{base_href}/{theme}/{collection_id}/v{version}/{tif.name}"
            item.add_asset(
                matched_key,
                pystac.Asset(
                    href=href,
                    media_type=cfg["asset_media_type"],
                    roles=["data"],
                    title=f"{asset_map.get(matched_key, matched_key)} — {year}",
                ),
            )
        items.append(item)

    # Zarr (recovery): procura store .zarr
    for zarr_store in tif_dir.glob("*.zarr"):
        href = f"{base_href}/{theme}/{collection_id}/v{version}/{zarr_store.name}"
        if items:
            items[0].add_asset(
                "timeseries_zarr",
                pystac.Asset(
                    href=href,
                    media_type="application/vnd+zarr",
                    roles=["data"],
                    title="Full time-series — Zarr",
                ),
            )
    return items


def build_collection(
    collection_id: str,
    cfg: dict,
    input_root: Path,
    out_root: Path,
    base_href: str,
    version: str,
) -> None:
    theme = cfg["theme"]
    tif_dir = input_root / theme / collection_id / f"v{version}"
    if not tif_dir.exists():
        print(f"  ⚠ diretório não encontrado, pulando: {tif_dir}")
        return

    col_dir = out_root / theme / collection_id
    col_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Processando {collection_id} ...")

    collection = pystac.Collection(
        id=collection_id,
        description=cfg["description"],
        title=cfg["title"],
        license="CC-BY-4.0",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-74, -34, -28, 6]]),
            temporal=pystac.TemporalExtent(
                [[datetime(1985, 1, 1, tzinfo=timezone.utc), None]]
            ),
        ),
        extra_fields={"version": version},
    )

    if cfg["multi_asset"]:
        items = build_multi_asset_collection(cfg, collection_id, tif_dir, base_href, version)
    else:
        items = build_single_asset_collection(cfg, collection_id, tif_dir, base_href, version)

    for item in items:
        collection.add_item(item)

    collection.normalize_hrefs(str(col_dir))
    collection.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print(f"  ✓ {len(items)} items — {col_dir}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Gera catálogo STAC YbYrá-BR completo.")
    p.add_argument("--input-root", required=True,
                   help="Raiz dos COGs locais organizados por produto.")
    p.add_argument("--base-href", required=True,
                   help="URL pública base (ex.: https://data.source.coop/celsohlsj/ybyra-br).")
    p.add_argument("--out", default="stac_catalog",
                   help="Diretório de saída do catálogo STAC.")
    p.add_argument("--version", default="1.0")
    p.add_argument("--collections", nargs="*",
                   help="Processar apenas essas coleções (default: todas).")
    args = p.parse_args()

    input_root = Path(args.input_root)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    selected = set(args.collections) if args.collections else set(COLLECTIONS)

    print(f"\n{'='*55}")
    print(f"  YbYrá STAC builder — versão {args.version}")
    print(f"  input-root : {input_root}")
    print(f"  base-href  : {args.base_href}")
    print(f"  output     : {out_root}")
    print(f"{'='*55}\n")

    for cid, cfg in COLLECTIONS.items():
        if cid not in selected:
            continue
        build_collection(cid, cfg, input_root, out_root, args.base_href, args.version)

    # Root catalog.json
    root_cat = pystac.Catalog(
        id="ybyra-br",
        description="YbYráSTAC: Brazilian forest EO products (YbYrá-BR / CCAL-IPAM / GCBC).",
        title="YbYrá-BR STAC Catalog",
    )
    # Re-lê as coleções geradas e liga ao root
    for cid, cfg in COLLECTIONS.items():
        if cid not in selected:
            continue
        col_json = out_root / cfg["theme"] / cid / "collection.json"
        if col_json.exists():
            col = pystac.Collection.from_file(str(col_json))
            root_cat.add_child(col)

    root_cat.normalize_hrefs(str(out_root))
    root_cat.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print(f"\n✓ Root catalog.json gerado em {out_root}/catalog.json")
    print("  Pronto para upload e publicação via GitHub Pages.")


if __name__ == "__main__":
    main()
