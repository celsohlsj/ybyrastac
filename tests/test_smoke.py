"""Teste de smoke: valida que o pacote importa e a API pública está presente."""

import ybyrastac


def test_imports():
    assert ybyrastac.__version__
    assert hasattr(ybyrastac, "DiscoveryProvider")
    assert hasattr(ybyrastac, "COGProvider")
    assert hasattr(ybyrastac, "ZarrProvider")
    assert hasattr(ybyrastac, "subset")
