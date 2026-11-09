"""
Utilita' trasversali: formattazione italiana e supporto alla dashboard.

Il modulo raccoglie le funzioni di presentazione (separatori di migliaia,
nomi dei mesi, etichette di periodo) in modo che la formattazione in italiano
sia definita una sola volta e riutilizzata da dashboard, tabelle e grafici.
"""

from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

from .config import MONTH_NAMES_IT

__all__ = [
    "format_number",
    "format_percent",
    "format_months",
    "month_label",
    "period_label",
    "italian_number_format",
    "describe_series",
]


def italian_number_format(value: float, decimals: int = 0) -> str:
    """Formatta un numero con la convenzione italiana (1.234,5).

    Python usa il punto come separatore decimale; qui si effettua lo scambio
    dei separatori per allineare l'output alle convenzioni italiane.
    """
    if value is None or pd.isna(value):
        return "n.d."
    formatted = f"{value:,.{decimals}f}"
    # Scambio dei separatori: ',' -> '.' e '.' -> ',' tramite segnaposto.
    return formatted.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def format_number(value: float, decimals: int = 0, unit: Optional[str] = None) -> str:
    """Numero formattato all'italiana con unita' di misura opzionale."""
    text = italian_number_format(value, decimals)
    return f"{text} {unit}" if unit else text


def format_percent(value: float, decimals: int = 1, with_sign: bool = False) -> str:
    """Percentuale formattata all'italiana (es. ``12,5%`` oppure ``+12,5%``).

    Parameters
    ----------
    value:
        Valore gia' espresso in punti percentuali (12.5 = 12,5%).
    with_sign:
        Se ``True`` antepone il segno ``+`` ai valori positivi.
    """
    if value is None or pd.isna(value):
        return "n.d."
    text = italian_number_format(value, decimals)
    if with_sign and value > 0:
        text = f"+{text}"
    return f"{text}%"


def format_months(value: float) -> str:
    """Durata in mesi con accordo singolare/plurale."""
    if pd.isna(value):
        return "n.d."
    text = italian_number_format(value, 0 if float(value).is_integer() else 1)
    return f"{text} mese" if abs(value - 1.0) < 1e-9 else f"{text} mesi"


def month_label(timestamp) -> str:
    """Etichetta mese/anno in italiano (es. ``Nov 2025``)."""
    ts = pd.Timestamp(timestamp)
    return f"{MONTH_NAMES_IT[ts.month - 1][:3]} {ts.year}"


def period_label(index: Iterable) -> str:
    """Etichetta di un intervallo temporale (es. ``Gen 2022 - Dic 2025``)."""
    values = pd.DatetimeIndex(pd.Series(list(index)).astype("datetime64[ns]"))
    if len(values) == 0:
        return "n.d."
    return f"{month_label(values.min())} - {month_label(values.max())}"


def describe_series(series: pd.Series) -> pd.DataFrame:
    """Statistiche descrittive in italiano di una serie di domanda.

    Include il coefficiente di variazione, indicatore chiave per valutare
    quanto la serie sia "difficile" da prevedere.
    """
    values = series.dropna()
    mean = float(values.mean()) if len(values) else float("nan")
    std = float(values.std(ddof=1)) if len(values) > 1 else float("nan")
    cv = (std / mean * 100.0) if mean else float("nan")
    return pd.DataFrame(
        {
            "Statistica": [
                "Osservazioni",
                "Media (unita'/mese)",
                "Deviazione standard (unita')",
                "Coefficiente di variazione (%)",
                "Minimo (unita')",
                "Massimo (unita')",
                "Escursione max/min",
            ],
            "Valore": [
                float(len(values)),
                mean,
                std,
                cv,
                float(values.min()) if len(values) else float("nan"),
                float(values.max()) if len(values) else float("nan"),
                float(values.max() / values.min())
                if len(values) and values.min() > 0
                else float("nan"),
            ],
        }
    )
