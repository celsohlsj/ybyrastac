"""
Discovery provider: browse themes, collections and versions in the YbYrá STAC.
"""

from __future__ import annotations

from typing import Optional
import pystac


class DiscoveryProvider:
    """Explora o catálogo YbYrá STAC programaticamente.

    Parameters
    ----------
    catalog_url : str
        URL do root catalog.json do YbYráSTAC.
    endpoint_url : str, optional
        Endpoint S3 quando o armazenamento for compatível com S3 (Source Coop,
        Cloudflare R2, MinIO institucional, etc.). Default None (HTTP público).
    anon : bool
        Acesso anônimo. Default True.
    """

    def __init__(
        self,
        catalog_url: str,
        endpoint_url: Optional[str] = None,
        anon: bool = True,
    ) -> None:
        self.catalog_url = catalog_url
        self.endpoint_url = endpoint_url
        self.anon = anon
        self._catalog: pystac.Catalog = pystac.Catalog.from_file(catalog_url)

    # ------------------------------------------------------------------
    # Temas (ex.: 'fragmentation', 'emissions', 'fire', 'recovery')
    # ------------------------------------------------------------------
    def list_themes(self) -> list[str]:
        """Lista temas (pastas de primeiro nível) do catálogo."""
        themes = []
        for child in self._catalog.get_children():
            themes.append(child.id)
        return sorted(themes)

    # ------------------------------------------------------------------
    # Coleções
    # ------------------------------------------------------------------
    def list_collections(self, theme: Optional[str] = None) -> list[dict]:
        """Lista coleções, opcionalmente filtradas por tema."""
        out = []
        iterator = (
            self._catalog.get_child(theme).get_collections()
            if theme
            else self._catalog.get_all_collections()
        )
        for col in iterator:
            out.append(
                {
                    "id": col.id,
                    "title": col.title,
                    "description": (col.description or "")[:140],
                    "license": col.license,
                    "extent": col.extent.to_dict(),
                    "versions": self._list_versions(col),
                }
            )
        return out

    def _list_versions(self, collection: pystac.Collection) -> list[str]:
        """Versões presentes em 'summaries.version' ou subcoleções versionadas."""
        summaries = getattr(collection, "summaries", None)
        if summaries and "version" in summaries.to_dict():
            return summaries.to_dict()["version"]
        return [collection.extra_fields.get("version", "1.0")]

    # ------------------------------------------------------------------
    # Item lookup
    # ------------------------------------------------------------------
    def get_collection(self, collection_id: str) -> pystac.Collection:
        return self._catalog.get_child(collection_id, recursive=True)

    def describe(self, collection_id: str) -> dict:
        col = self.get_collection(collection_id)
        if col is None:
            raise KeyError(f"Coleção '{collection_id}' não encontrada.")
        return col.to_dict()
