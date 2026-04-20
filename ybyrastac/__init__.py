"""
YbYráSTAC
=========

Toolbox para acesso cloud-native aos produtos de EO do projeto YbYrá-BR via STAC.
"""

__version__ = "0.1.0"
__author__ = "Celso H. L. Silva Junior"

from ybyrastac.providers.discovery import DiscoveryProvider
from ybyrastac.providers.cog import COGProvider
from ybyrastac.providers.zarr import ZarrProvider
from ybyrastac.providers.subset import subset

__all__ = [
    "DiscoveryProvider",
    "COGProvider",
    "ZarrProvider",
    "subset",
]
