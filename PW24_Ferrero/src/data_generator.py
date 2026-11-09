"""
Generazione del dataset sintetico di domanda.

Il modulo costruisce, per ciascuno dei quattro prodotti analizzati, una serie
storica mensile di 48 osservazioni combinando matematicamente quattro
componenti classiche dell'analisi delle serie storiche piu' una componente
promozionale opzionale.

MODELLO GENERATORE
------------------
Per il mese ``t = 0, 1, ..., T-1`` (con ``T = 48``) e il corrispondente mese
solare ``m in {1, ..., 12}``:

1. **Livello con trend** (componente sistematica di lungo periodo)::

       L(t) = base_demand * (1 + trend_rate * t)

2. **Fattore stagionale** (componente periodica a 12 mesi)::

       S(m) = 1 + A * cos(2*pi*(m - peak_month)/12) + F(m)

   dove ``A`` e' l'ampiezza sinusoidale e ``F(m)`` e' il profilo festivo
   addizionale (usato per i picchi natalizi di Ferrero Rocher).

3. **Rumore casuale** moltiplicativo (componente accidentale)::

       e(t) ~ N(0, noise_std)      ->      fattore (1 + e(t))

   ``noise_std`` e' espresso come coefficiente di variazione, quindi la
   dispersione assoluta cresce proporzionalmente al livello della serie.

4. **Picchi promozionali** (componente episodica opzionale)::

       P(t) = L(t) * promotion_amplitude * U(0.6, 1.4)   con prob. p

Formula complessiva::

       D(t) = round( max(1, L(t) * S(m) * (1 + e(t)) + P(t)) )

RIPRODUCIBILITA'
----------------
Ogni prodotto riceve un generatore ``numpy.random.Generator`` derivato dal
seed globale tramite ``SeedSequence.spawn``: modificare i parametri di un
prodotto non altera quindi le realizzazioni casuali degli altri.

AVVERTENZA: i valori prodotti sono sintetici e non rappresentano dati reali
Ferrero (cfr. :data:`src.config.SYNTHETIC_DATA_DISCLAIMER`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

from .config import (
    DATA_DIR,
    DEMAND_HISTORY_CSV,
    DEMAND_WIDE_CSV,
    FREQUENCY,
    HISTORY_START,
    N_PERIODS,
    PRODUCTS,
    PRODUCT_PARAMETERS_CSV,
    RANDOM_SEED,
    ProductParameters,
)

__all__ = [
    "build_date_index",
    "seasonal_factor",
    "generate_product_series",
    "generate_demand_dataset",
    "build_parameters_table",
    "to_wide_format",
    "save_dataset",
    "regenerate_all",
]


# ---------------------------------------------------------------------------
# Componenti del modello generatore
# ---------------------------------------------------------------------------


def build_date_index(
    start: str = HISTORY_START,
    periods: int = N_PERIODS,
    freq: str = FREQUENCY,
) -> pd.DatetimeIndex:
    """Costruisce l'indice temporale mensile del dataset.

    Parameters
    ----------
    start:
        Data iniziale in formato ISO (``YYYY-MM-DD``).
    periods:
        Numero di osservazioni mensili da generare.
    freq:
        Frequenza pandas; il progetto usa ``"MS"`` (inizio mese).
    """
    if periods <= 0:
        raise ValueError("Il numero di periodi deve essere positivo.")
    return pd.date_range(start=start, periods=periods, freq=freq)


def seasonal_factor(
    months: np.ndarray,
    amplitude: float,
    peak_month: int,
    festive_profile: Optional[Dict[int, float]] = None,
) -> np.ndarray:
    """Calcola il fattore stagionale moltiplicativo ``S(m)``.

    La componente sinusoidale (coseno) garantisce un massimo esatto nel mese
    ``peak_month`` e un minimo sei mesi dopo; il profilo festivo aggiunge una
    sovra-domanda puntuale su mesi specifici.

    Parameters
    ----------
    months:
        Array dei mesi solari (valori 1-12).
    amplitude:
        Ampiezza relativa della sinusoide (0.10 = +/-10%).
    peak_month:
        Mese di picco della sinusoide.
    festive_profile:
        Mappa ``mese -> sovra-domanda relativa`` (facoltativa).

    Returns
    -------
    numpy.ndarray
        Fattori stagionali, uno per ciascun mese in input.
    """
    base = 1.0 + amplitude * np.cos(2.0 * np.pi * (months - peak_month) / 12.0)
    if festive_profile:
        uplift = np.array(
            [float(festive_profile.get(int(m), 0.0)) for m in months],
            dtype=float,
        )
        base = base + uplift
    # Il fattore stagionale non puo' annullare o invertire la domanda.
    return np.maximum(base, 0.05)


def generate_product_series(
    params: ProductParameters,
    dates: Optional[pd.DatetimeIndex] = None,
    seed: int = RANDOM_SEED,
    product_index: int = 0,
) -> pd.Series:
    """Genera la serie storica sintetica di un singolo prodotto.

    Parameters
    ----------
    params:
        Parametri del processo generatore (cfr. :class:`ProductParameters`).
    dates:
        Indice temporale; se omesso viene usato quello di default del progetto.
    seed:
        Seed globale di riproducibilita'.
    product_index:
        Indice del prodotto, usato per derivare un flusso casuale dedicato.

    Returns
    -------
    pandas.Series
        Domanda mensile intera e strettamente positiva, indicizzata per data.
    """
    if dates is None:
        dates = build_date_index()

    # Flusso casuale indipendente per ciascun prodotto: i parametri di un
    # prodotto non influenzano le realizzazioni casuali degli altri.
    rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(16)[product_index])

    t = np.arange(len(dates), dtype=float)
    months = dates.month.to_numpy()

    # (1) livello con trend lineare
    level = params.base_demand * (1.0 + params.trend_rate * t)

    # (2) componente stagionale
    season = seasonal_factor(
        months,
        amplitude=params.seasonal_amplitude,
        peak_month=params.seasonal_peak_month,
        festive_profile=params.festive_profile,
    )

    # (3) rumore casuale moltiplicativo
    noise = rng.normal(loc=0.0, scale=max(params.noise_std, 0.0), size=len(dates))

    # (4) picchi promozionali episodici
    promo_hits = rng.random(len(dates)) < params.promotion_probability
    promo_size = rng.uniform(0.6, 1.4, size=len(dates))
    promotions = promo_hits * promo_size * params.promotion_amplitude * level

    demand = level * season * (1.0 + noise) + promotions

    # Vincoli di dominio: quantita' intere e strettamente positive.
    demand = np.maximum(demand, 1.0)
    demand = np.rint(demand).astype(int)

    return pd.Series(demand, index=dates, name=params.name)


# ---------------------------------------------------------------------------
# Costruzione del dataset completo
# ---------------------------------------------------------------------------


def generate_demand_dataset(
    products: Optional[Dict[str, ProductParameters]] = None,
    dates: Optional[pd.DatetimeIndex] = None,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Genera il dataset in formato lungo (``date``, ``product``, ``demand``).

    Parameters
    ----------
    products:
        Dizionario dei prodotti; di default l'anagrafica di :mod:`src.config`.
    dates:
        Indice temporale; di default gen-2022 / dic-2025.
    seed:
        Seed globale di riproducibilita'.

    Returns
    -------
    pandas.DataFrame
        Colonne ``date`` (datetime), ``product`` (str), ``demand`` (int),
        ordinate per prodotto e data.
    """
    products = products if products is not None else PRODUCTS
    dates = dates if dates is not None else build_date_index()

    frames = []
    # L'indice posizionale nell'anagrafica di configurazione determina il
    # flusso casuale: l'ordine dei prodotti va quindi mantenuto stabile.
    reference_order = list(PRODUCTS.keys())
    for name, params in products.items():
        product_index = (
            reference_order.index(name) if name in reference_order else len(frames)
        )
        series = generate_product_series(
            params, dates=dates, seed=seed, product_index=product_index
        )
        frames.append(
            pd.DataFrame(
                {
                    "date": series.index,
                    "product": name,
                    "demand": series.to_numpy(),
                }
            )
        )

    dataset = pd.concat(frames, ignore_index=True)
    return dataset.sort_values(["product", "date"]).reset_index(drop=True)


def build_parameters_table(
    products: Optional[Dict[str, ProductParameters]] = None,
) -> pd.DataFrame:
    """Costruisce la tabella dei parametri di generazione sintetica."""
    products = products if products is not None else PRODUCTS
    return pd.DataFrame([params.to_row() for params in products.values()])


def to_wide_format(dataset: pd.DataFrame) -> pd.DataFrame:
    """Converte il dataset lungo in formato pivot (una colonna per prodotto)."""
    wide = dataset.pivot(index="date", columns="product", values="demand")
    # Mantiene l'ordine di anagrafica invece dell'ordine alfabetico.
    ordered = [name for name in PRODUCTS if name in wide.columns]
    wide = wide[ordered]
    wide.columns.name = None
    return wide.reset_index()


# ---------------------------------------------------------------------------
# Persistenza su disco
# ---------------------------------------------------------------------------


def save_dataset(
    dataset: pd.DataFrame,
    data_dir: Path = DATA_DIR,
    write_parameters: bool = True,
    products: Optional[Dict[str, ProductParameters]] = None,
) -> Dict[str, Path]:
    """Salva il dataset (lungo, pivot) e la tabella parametri su CSV.

    Returns
    -------
    dict
        Mappa ``nome logico -> percorso`` dei file effettivamente scritti.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    long_path = data_dir / DEMAND_HISTORY_CSV.name
    wide_path = data_dir / DEMAND_WIDE_CSV.name

    out = dataset.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out.to_csv(long_path, index=False)

    wide = to_wide_format(dataset)
    wide["date"] = pd.to_datetime(wide["date"]).dt.strftime("%Y-%m-%d")
    wide.to_csv(wide_path, index=False)

    written = {"demand_history": long_path, "demand_history_wide": wide_path}

    if write_parameters:
        params_path = data_dir / PRODUCT_PARAMETERS_CSV.name
        build_parameters_table(products).to_csv(params_path, index=False)
        written["product_parameters"] = params_path

    return written


def regenerate_all(
    data_dir: Path = DATA_DIR,
    seed: int = RANDOM_SEED,
    verbose: bool = True,
) -> Dict[str, Path]:
    """Rigenera e salva l'intero dataset sintetico.

    Funzione invocata sia dalla CLI (``python -m src.data_generator``) sia dal
    pulsante di rigenerazione della dashboard.
    """
    dataset = generate_demand_dataset(seed=seed)
    written = save_dataset(dataset, data_dir=data_dir)

    if verbose:
        print("Dataset sintetico rigenerato con successo.")
        print(f"  Seed casuale .......... {seed}")
        print(f"  Osservazioni totali ... {len(dataset)}")
        print(f"  Prodotti .............. {dataset['product'].nunique()}")
        print(
            "  Periodo ............... "
            f"{dataset['date'].min():%Y-%m} / {dataset['date'].max():%Y-%m}"
        )
        for label, path in written.items():
            print(f"  File [{label}] -> {path}")
        print(
            "\nAVVERTENZA: dati sintetici a fini didattici. "
            "Non rappresentano vendite reali Ferrero."
        )

    return written


def _summarise(dataset: pd.DataFrame) -> pd.DataFrame:
    """Statistiche descrittive di controllo, usate dalla CLI."""
    grouped = dataset.groupby("product")["demand"]
    summary = pd.DataFrame(
        {
            "osservazioni": grouped.count(),
            "media": grouped.mean().round(1),
            "dev_std": grouped.std(ddof=1).round(1),
            "minimo": grouped.min(),
            "massimo": grouped.max(),
        }
    )
    summary["cv_%"] = (summary["dev_std"] / summary["media"] * 100).round(1)
    ordered: Iterable[str] = [p for p in PRODUCTS if p in summary.index]
    return summary.loc[list(ordered)]


if __name__ == "__main__":  # pragma: no cover - entry point da riga di comando
    regenerate_all()
    print("\nStatistiche descrittive delle serie generate:")
    print(_summarise(generate_demand_dataset()).to_string())
