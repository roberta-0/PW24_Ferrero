"""
Indicatori di accuratezza previsionale.

Il modulo implementa le tre metriche richieste dalla specifica PW24 (MAE,
RMSE, MAPE) piu' due indicatori complementari (bias medio e sMAPE) utili
nell'interpretazione dei risultati.

Formule
-------
Dati i valori osservati ``y(i)`` e previsti ``f(i)``, con ``n`` osservazioni:

* **MAE** (Mean Absolute Error) - errore medio assoluto, nell'unita' di
  misura della domanda::

      MAE = (1/n) * sum |y(i) - f(i)|

* **RMSE** (Root Mean Squared Error) - radice dell'errore quadratico medio;
  penalizza maggiormente gli errori grandi::

      RMSE = sqrt( (1/n) * sum (y(i) - f(i))^2 )

* **MAPE** (Mean Absolute Percentage Error) - errore percentuale medio
  assoluto, adimensionale e quindi confrontabile fra prodotti di volume
  diverso::

      MAPE = (100/n') * sum |y(i) - f(i)| / |y(i)|,   solo per y(i) != 0

* **Bias** (errore medio con segno) - diagnostica di sovra/sotto-stima
  sistematica::

      Bias = (1/n) * sum (f(i) - y(i))

* **sMAPE** (symmetric MAPE) - alternativa simmetrica al MAPE, definita
  anche in presenza di osservazioni nulle::

      sMAPE = (100/n) * sum 2*|y(i)-f(i)| / (|y(i)| + |f(i)|)

Gestione dei valori nulli nel MAPE
----------------------------------
Il MAPE non e' definito quando ``y(i) = 0``. Le osservazioni con domanda
nulla vengono **escluse** dal calcolo e il numero di osservazioni effettive
``n'`` e' ridotto di conseguenza. Se *tutte* le osservazioni sono nulle il
MAPE restituisce ``NaN``: in tal caso il criterio di selezione del modello
ripiega automaticamente sull'RMSE (cfr. :mod:`src.evaluation`).
"""

from __future__ import annotations

from typing import Dict

import numpy as np

__all__ = [
    "MetricsError",
    "mae",
    "rmse",
    "mape",
    "bias",
    "smape",
    "compute_all_metrics",
    "METRIC_LABELS_IT",
]


class MetricsError(Exception):
    """Errore nel calcolo delle metriche, con messaggio in italiano."""


#: Etichette italiane e unita' di misura delle metriche, usate in dashboard.
METRIC_LABELS_IT: Dict[str, str] = {
    "MAE": "MAE (unita')",
    "RMSE": "RMSE (unita')",
    "MAPE": "MAPE (%)",
    "Bias": "Bias medio (unita')",
    "sMAPE": "sMAPE (%)",
}


def _align(y_true, y_pred) -> tuple[np.ndarray, np.ndarray]:
    """Converte gli input in array float e verifica la compatibilita'."""
    actual = np.asarray(y_true, dtype=float).ravel()
    predicted = np.asarray(y_pred, dtype=float).ravel()

    if actual.size == 0:
        raise MetricsError(
            "Impossibile calcolare le metriche: la serie osservata e' vuota."
        )
    if actual.size != predicted.size:
        raise MetricsError(
            "Impossibile calcolare le metriche: valori osservati "
            f"({actual.size}) e previsti ({predicted.size}) hanno lunghezza "
            "diversa."
        )

    # Si considerano solo le coppie interamente valide.
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    if not mask.any():
        raise MetricsError(
            "Impossibile calcolare le metriche: nessuna coppia "
            "osservato/previsto valida."
        )
    return actual[mask], predicted[mask]


def mae(y_true, y_pred) -> float:
    """Errore medio assoluto (Mean Absolute Error)."""
    actual, predicted = _align(y_true, y_pred)
    return float(np.mean(np.abs(actual - predicted)))


def rmse(y_true, y_pred) -> float:
    """Radice dell'errore quadratico medio (Root Mean Squared Error)."""
    actual, predicted = _align(y_true, y_pred)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mape(y_true, y_pred) -> float:
    """Errore percentuale medio assoluto, in punti percentuali.

    Le osservazioni con domanda nulla sono escluse dal calcolo (il rapporto
    non sarebbe definito). Se tutte le osservazioni sono nulle restituisce
    ``NaN``.
    """
    actual, predicted = _align(y_true, y_pred)
    nonzero = actual != 0.0
    if not nonzero.any():
        return float("nan")
    ratios = np.abs((actual[nonzero] - predicted[nonzero]) / actual[nonzero])
    return float(np.mean(ratios) * 100.0)


def bias(y_true, y_pred) -> float:
    """Errore medio con segno: positivo se il modello sovrastima la domanda."""
    actual, predicted = _align(y_true, y_pred)
    return float(np.mean(predicted - actual))


def smape(y_true, y_pred) -> float:
    """MAPE simmetrico, definito anche con osservazioni nulle."""
    actual, predicted = _align(y_true, y_pred)
    denominator = np.abs(actual) + np.abs(predicted)
    valid = denominator != 0.0
    if not valid.any():
        return float("nan")
    ratios = 2.0 * np.abs(actual[valid] - predicted[valid]) / denominator[valid]
    return float(np.mean(ratios) * 100.0)


def compute_all_metrics(y_true, y_pred) -> Dict[str, float]:
    """Calcola in un'unica chiamata tutte le metriche di accuratezza.

    Returns
    -------
    dict
        Dizionario con chiavi ``MAE``, ``RMSE``, ``MAPE``, ``Bias``, ``sMAPE``.
    """
    return {
        "MAE": mae(y_true, y_pred),
        "RMSE": rmse(y_true, y_pred),
        "MAPE": mape(y_true, y_pred),
        "Bias": bias(y_true, y_pred),
        "sMAPE": smape(y_true, y_pred),
    }
