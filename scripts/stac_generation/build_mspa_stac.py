"""
build_mspa_stac.py
==================

Gera um `Collection` + `Items` STAC para uma série anual de COGs MSPA.

Uso:
    python scripts/stac_generation/build_mspa_stac.py \
        --input-dir /data/mspa_ma/cog \
        --collection-id ybyra-mspa-ma \
        --theme fragmentation \
        --base-href https://data.source.coop/celsohlsj/ybyra-br \
        --out stac_catalog/
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pystac
import rasterio
from rasterio.warp import transform_bounds
from shapely.geometry import box, mapping


YEAR_RE = re.compile(r"(\d{4})")


def bbox_and_footprint(path: Path):
    with rasterio.open(path) as src:
        bounds = src.bounds
        crs = src.crs
        bbox = transform_bounds(crs, "EPSG:4326", *bounds)
        footprint = mapping(box(*bbox))
        return list(bbox), footprint, src.res[0], src.crs.to_epsg()


def build(args):
    out_root = Path(args.out)
    col_dir = out_root / args.theme / args.collection_id
    col_dir.mkdir(parents=True, exist_ok=True)

    collection = pystac.Collection(
        id=args.collection_id,
        description=args.description,
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-74, -34, -34, 6]]),   # BR bbox default
            temporal=pystac.TemporalExtent([[datetime(1985, 1, 1, tzinfo=timezone.utc), None]]),
        ),
        title=args.title,
        license="CC-BY-4.0",
    )

    for cog in sorted(Path(args.input_dir).glob("*.tif")):
        m = YEAR_RE.search(cog.stem)
        if not m:
            continue
        year = int(m.group(1))

        bbox, footprint, gsd, epsg = bbox_and_footprint(cog)
        href = f"{args.base_href}/{args.theme}/{args.collection_id}/v{args.version}/{cog.name}"

        item = pystac.Item(
            id=f"{args.collection_id}_{year}",
            geometry=footprint,
            bbox=bbox,
            datetime=datetime(year, 1, 1, tzinfo=timezone.utc),
            properties={
                "start_datetime": f"{year}-01-01T00:00:00Z",
                "end_datetime":   f"{year}-12-31T23:59:59Z",
                "version": args.version,
                "gsd": gsd,
                "proj:epsg": epsg,
            },
        )
        item.add_asset(
            "data",
            pystac.Asset(
                href=href,
                media_type=pystac.MediaType.COG,
                roles=["data"],
                title=f"{args.collection_id} {year}",
            ),
        )
        collection.add_item(item)

    collection.normalize_hrefs(str(col_dir))
    collection.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print(f"✓ Coleção gerada em {col_dir}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", required=True)
    p.add_argument("--collection-id", required=True)
    p.add_argument("--theme", default="fragmentation")
    p.add_argument("--title", default="")
    p.add_argument("--description", default="YbYrá-BR product")
    p.add_argument("--version", default="1.0")
    p.add_argument("--base-href", required=True,
                   help="URL pública base onde os COGs estão hospedados")
    p.add_argument("--out", default="stac_catalog")
    build(p.parse_args())
