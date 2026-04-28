# Quickstart

```python
from ybyrastac import DiscoveryProvider, COGProvider, subset

CATALOG = "https://raw.githubusercontent.com/celsohlsj/ybyrastac/main/stac_catalog/catalog.json"

disc = DiscoveryProvider(CATALOG)
disc.list_themes()

cog = COGProvider(CATALOG)
ds = cog.open_dataset("ybyra-mspa-ma", years=[2020, 2023])
```

Veja mais em `auto_examples/`.
