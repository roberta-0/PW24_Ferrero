"""
Fixture condivise fra i moduli di test.

Il file garantisce inoltre che la radice del progetto sia nel ``sys.path``,
in modo che i test possano essere eseguiti sia con ``pytest`` dalla radice
sia tramite ``python -m pytest``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PRODUCTS  # noqa: E402
from src.data_generator import generate_demand_dataset  # noqa: E402


@pytest.fixture(scope="session")
def dataset() -> pd.DataFrame:
    """Dataset sintetico completo generato in memoria (formato lungo)."""
    return generate_demand_dataset()


@pytest.fixture(scope="session")
def serie_nutella(dataset: pd.DataFrame) -> pd.Series:
    """Serie storica di un prodotto a domanda stabile."""
    return (
        dataset[dataset["product"] == "Nutella"]
        .set_index("date")["demand"]
        .sort_index()
    )


@pytest.fixture(scope="session")
def serie_rocher(dataset: pd.DataFrame) -> pd.Series:
    """Serie storica di un prodotto fortemente stagionale."""
    return (
        dataset[dataset["product"] == "Ferrero Rocher"]
        .set_index("date")["demand"]
        .sort_index()
    )


@pytest.fixture
def serie_lineare() -> pd.Series:
    """Serie deterministica perfettamente lineare, utile come caso di controllo."""
    index = pd.date_range("2022-01-01", periods=48, freq="MS")
    return pd.Series(np.arange(48, dtype=float) * 10.0 + 1000.0, index=index)


@pytest.fixture
def serie_costante() -> pd.Series:
    """Serie deterministica costante: tutti i metodi devono azzerare l'errore."""
    index = pd.date_range("2022-01-01", periods=48, freq="MS")
    return pd.Series(np.full(48, 500.0), index=index)


@pytest.fixture(scope="session")
def nomi_prodotti() -> list[str]:
    """Elenco dei prodotti in anagrafica."""
    return list(PRODUCTS)
