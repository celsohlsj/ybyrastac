"""
tif_to_cog.py
=============

Converte GeoTIFFs "comuns" (saída de GEE/QGIS/ArcGIS) em Cloud-Optimized
GeoTIFFs válidos (tiled, overviews internas, LZW). Pré-requisito para o
catálogo YbYráSTAC.

    pip install rio-cogeo
    python scripts/ingestion/tif_to_cog.py -i raw/ -o cog/
"""

from __future__ import annotations

import argparse
from pathlib import Path
from rio_cogeo.cogeo import cog_translate, cog_validate
from rio_cogeo.profiles import cog_profiles


def convert(src: Path, dst: Path, profile: str = "lzw") -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cog_translate(
        str(src),
        str(dst),
        cog_profiles.get(profile),
        overview_level=5,
        overview_resampling="nearest",
        in_memory=False,
        quiet=True,
    )
    assert cog_validate(str(dst))[0], f"COG inválido: {dst}"
    print(f"✓ {dst.name}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input-dir", required=True)
    p.add_argument("-o", "--output-dir", required=True)
    p.add_argument("--profile", default="lzw",
                   choices=["lzw", "deflate", "zstd", "jpeg", "raw"])
    args = p.parse_args()

    in_dir, out_dir = Path(args.input_dir), Path(args.output_dir)
    for tif in in_dir.glob("*.tif"):
        convert(tif, out_dir / tif.name, args.profile)


if __name__ == "__main__":
    main()
