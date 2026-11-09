"""
Metodi previsionali.

Il modulo implementa cinque metodi di previsione della domanda, tutti scritti
"da zero" con NumPy per rendere esplicita la formulazione matematica (nessuna
libreria statistica esterna oltre a NumPy/SciPy).

Metodi implementati
-------------------
========================  ==========================================
Metodo                    Adatto a
========================  ==========================================
Media mobile semplice     serie stazionarie, rumore elevato
Smorzamento esponenziale  serie stazionarie con livello che deriva
Regressione lineare       serie con trend sistematico
Naive stagionale          serie fortemente stagionali (benchmark)
Holt-Winters additivo     serie con trend E stagionalita'
========================  ==========================================

Convenzione comune
------------------
Ogni funzione riceve la sola storia di addestramento ``y`` e l'orizzonte
``horizon``, e restituisce un :class:`ForecastResult` contenente:

* ``fitted``  : valori interpolati in-sample (``NaN`` dove non definiti);
* ``forecast``: previsioni per i ``horizon`` periodi successivi.

Nessun metodo "sbircia" i dati di test: la valutazione out-of-sample in
:mod:`src.evaluation` passa esclusivamente il training set.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Mapping, Optional

import numpy as np

from .config import DEFAULT_ALPHA, DEFAULT_MA_WINDOW, SEASONAL_PERIOD

__all__ = [
    "ForecastResult",
    "ForecastingError",
    "moving_average_forecast",
    "simple_exponential_smoothing",
    "linear_trend_regression",
    "seasonal_naive_forecast",
    "holt_winters_additive",
    "METHOD_REGISTRY",
    "METHOD_NAMES",
    "run_method",
    "available_methods",
]


class ForecastingError(Exception):
    """Errore previsionale con messaggio in italiano per l'utente finale."""


@dataclass
class ForecastResult:
    """Esito di un metodo previsionale.

    Attributes
    ----------
    method:
        Nome del metodo (in italiano, usato anche nelle tabelle di output).
    forecast:
        Previsioni per i periodi futuri (lunghezza pari all'orizzonte).
    fitted:
        Valori interpolati in-sample, allineati alla serie di input;
        contengono ``NaN`` nei periodi in cui il metodo non e' definito.
    params:
        Parametri effettivamente utilizzati dal metodo.
    """

    method: str
    forecast: np.ndarray
    fitted: np.ndarray
    params: Dict[str, float] = field(default_factory=dict)

    @property
    def residuals(self) -> np.ndarray:
        """Residui in-sample (``NaN`` dove il fitted non e' definito)."""
        return self._residuals

    def with_residuals(self, y: np.ndarray) -> "ForecastResult":
        """Calcola e memorizza i residui rispetto alla serie osservata."""
        self._residuals = np.asarray(y, dtype=float) - self.fitted
        return self

    _residuals: np.ndarray = field(
        default_factory=lambda: np.array([]), repr=False, compare=False
    )


# ---------------------------------------------------------------------------
# Utilita' interne
# ---------------------------------------------------------------------------


def _prepare(y, horizon: int, min_length: int, method_label: str) -> np.ndarray:
    """Valida gli input comuni a tutti i metodi e restituisce l'array float."""
    arr = np.asarray(y, dtype=float).ravel()

    if np.isnan(arr).any():
        raise ForecastingError(
            f"{method_label}: la serie contiene valori mancanti. "
            "Eseguire la validazione dei dati prima della previsione."
        )
    if horizon < 1:
        raise ForecastingError(
            f"{method_label}: l'orizzonte di previsione deve essere almeno 1 "
            f"mese (ricevuto {horizon})."
        )
    if len(arr) < min_length:
        raise ForecastingError(
            f"{method_label}: servono almeno {min_length} osservazioni "
            f"storiche, ne sono disponibili {len(arr)}."
        )
    return arr


# ---------------------------------------------------------------------------
# A) Media mobile semplice
# ---------------------------------------------------------------------------


def moving_average_forecast(
    y,
    horizon: int,
    window: int = DEFAULT_MA_WINDOW,
) -> ForecastResult:
    """Media mobile semplice (Simple Moving Average).

    La previsione per tutti i periodi futuri coincide con la media delle
    ultime ``window`` osservazioni::

        F(T+h) = (1/w) * sum_{i=T-w+1..T} y(i)        per ogni h >= 1

    In-sample il valore interpolato al tempo ``t`` usa le ``w`` osservazioni
    *precedenti* (previsione a un passo, nessun uso di informazione futura).

    Parameters
    ----------
    y:
        Serie storica di addestramento.
    horizon:
        Numero di mesi da prevedere.
    window:
        Ampiezza della finestra mobile (3, 6 o 12 mesi in dashboard).
    """
    label = "Media mobile"
    if window < 1:
        raise ForecastingError(
            f"{label}: l'ampiezza della finestra deve essere almeno 1 "
            f"(ricevuto {window})."
        )
    arr = _prepare(y, horizon, min_length=window, method_label=label)

    fitted = np.full(len(arr), np.nan)
    for t in range(window, len(arr)):
        fitted[t] = arr[t - window : t].mean()

    level = float(arr[-window:].mean())
    forecast = np.full(horizon, level)

    return ForecastResult(
        method=f"Media mobile ({window} mesi)",
        forecast=forecast,
        fitted=fitted,
        params={"window": float(window)},
    ).with_residuals(arr)


# ---------------------------------------------------------------------------
# B) Smorzamento esponenziale semplice
# ---------------------------------------------------------------------------


def simple_exponential_smoothing(
    y,
    horizon: int,
    alpha: float = DEFAULT_ALPHA,
) -> ForecastResult:
    """Smorzamento esponenziale semplice (Simple Exponential Smoothing).

    Ricorsione sul livello::

        L(t) = alpha * y(t) + (1 - alpha) * L(t-1),    0 < alpha <= 1
        L(0) = y(0)

    La previsione e' piatta e pari all'ultimo livello stimato::

        F(T+h) = L(T)         per ogni h >= 1

    Valori elevati di ``alpha`` rendono il modello piu' reattivo alle
    osservazioni recenti; valori bassi producono previsioni piu' lisce.
    """
    label = "Smorzamento esponenziale"
    if not 0.0 < alpha <= 1.0:
        raise ForecastingError(
            f"{label}: il parametro alpha deve essere compreso fra 0 "
            f"(escluso) e 1 (incluso); ricevuto {alpha}."
        )
    arr = _prepare(y, horizon, min_length=2, method_label=label)

    level = float(arr[0])
    fitted = np.full(len(arr), np.nan)
    for t in range(1, len(arr)):
        fitted[t] = level                       # previsione a un passo
        level = alpha * arr[t] + (1.0 - alpha) * level

    forecast = np.full(horizon, level)

    return ForecastResult(
        method=f"Smorzamento esponenziale (alpha={alpha:.2f})",
        forecast=forecast,
        fitted=fitted,
        params={"alpha": float(alpha)},
    ).with_residuals(arr)


# ---------------------------------------------------------------------------
# C) Regressione lineare sul tempo
# ---------------------------------------------------------------------------


def linear_trend_regression(y, horizon: int) -> ForecastResult:
    """Regressione lineare della domanda sul tempo (minimi quadrati).

    Si stima il modello::

        y(t) = a + b * t + e(t)

    con ``t = 0, 1, ..., T-1``; i coefficienti sono ottenuti per minimi
    quadrati ordinari. La previsione estrapola la retta::

        F(T+h) = a + b * (T + h - 1)

    Le previsioni sono troncate a zero: la domanda non puo' essere negativa
    anche in presenza di un trend stimato fortemente decrescente.
    """
    label = "Regressione lineare"
    arr = _prepare(y, horizon, min_length=3, method_label=label)

    t = np.arange(len(arr), dtype=float)
    slope, intercept = np.polyfit(t, arr, deg=1)

    fitted = intercept + slope * t
    future_t = np.arange(len(arr), len(arr) + horizon, dtype=float)
    forecast = np.maximum(intercept + slope * future_t, 0.0)

    return ForecastResult(
        method="Regressione lineare",
        forecast=forecast,
        fitted=fitted,
        params={"intercetta": float(intercept), "pendenza": float(slope)},
    ).with_residuals(arr)


# ---------------------------------------------------------------------------
# D) Naive stagionale
# ---------------------------------------------------------------------------


def seasonal_naive_forecast(
    y,
    horizon: int,
    period: int = SEASONAL_PERIOD,
) -> ForecastResult:
    """Naive stagionale: la previsione ripete il valore dello stesso mese.

    Formula::

        F(T+h) = y(T + h - period * ceil(h / period))

    Per un periodo di 12 mesi, la previsione di novembre prossimo e' la
    domanda osservata lo scorso novembre. E' un benchmark semplice ma
    sorprendentemente efficace per serie fortemente stagionali, ed e' il
    riferimento classico per valutare se un modello piu' complesso "vale"
    la sua complessita'.
    """
    label = "Naive stagionale"
    if period < 1:
        raise ForecastingError(
            f"{label}: il periodo stagionale deve essere almeno 1 "
            f"(ricevuto {period})."
        )
    arr = _prepare(y, horizon, min_length=period + 1, method_label=label)

    fitted = np.full(len(arr), np.nan)
    fitted[period:] = arr[:-period]

    forecast = np.empty(horizon, dtype=float)
    for h in range(horizon):
        # Indice ciclico sull'ultimo ciclo stagionale completo osservato.
        forecast[h] = arr[len(arr) - period + (h % period)]

    return ForecastResult(
        method=f"Naive stagionale ({period} mesi)",
        forecast=forecast,
        fitted=fitted,
        params={"period": float(period)},
    ).with_residuals(arr)


# ---------------------------------------------------------------------------
# E) Holt-Winters additivo
# ---------------------------------------------------------------------------


def holt_winters_additive(
    y,
    horizon: int,
    period: int = SEASONAL_PERIOD,
    alpha: float = 0.30,
    beta: float = 0.10,
    gamma: float = 0.20,
) -> ForecastResult:
    """Smorzamento esponenziale triplo (Holt-Winters) in forma additiva.

    Il metodo aggiorna simultaneamente tre componenti::

        L(t) = alpha*(y(t) - S(t-m)) + (1-alpha)*(L(t-1) + B(t-1))   livello
        B(t) = beta *(L(t) - L(t-1)) + (1-beta )* B(t-1)             trend
        S(t) = gamma*(y(t) - L(t))   + (1-gamma)* S(t-m)             stagion.

    con previsione::

        F(T+h) = L(T) + h*B(T) + S(T + h - m*ceil(h/m))

    **Inizializzazione** (deterministica, senza ottimizzazione numerica):
    il livello iniziale e' la media del primo ciclo stagionale, il trend
    iniziale e' la differenza media fra il secondo e il primo ciclo divisa
    per ``m``, gli indici stagionali iniziali sono gli scarti del primo ciclo
    dalla sua media. Servono quindi almeno due cicli completi (24 mesi).

    I parametri ``alpha``, ``beta`` e ``gamma`` sono fissati a valori di uso
    comune in letteratura e **non** sono ottimizzati: questa semplificazione
    e' documentata e accettata nel contesto didattico del Project Work.
    """
    label = "Holt-Winters"
    for pname, pval in (("alpha", alpha), ("beta", beta), ("gamma", gamma)):
        if not 0.0 <= pval <= 1.0:
            raise ForecastingError(
                f"{label}: il parametro {pname} deve essere compreso fra 0 e 1 "
                f"(ricevuto {pval})."
            )
    if period < 2:
        raise ForecastingError(
            f"{label}: il periodo stagionale deve essere almeno 2 "
            f"(ricevuto {period})."
        )

    arr = _prepare(y, horizon, min_length=2 * period, method_label=label)
    n = len(arr)

    # --- inizializzazione delle componenti --------------------------------
    first_cycle = arr[:period]
    second_cycle = arr[period : 2 * period]
    level = float(first_cycle.mean())
    trend = float((second_cycle.mean() - first_cycle.mean()) / period)
    season = (first_cycle - first_cycle.mean()).astype(float)

    fitted = np.full(n, np.nan)
    season_hist = list(season)

    # --- ricorsione --------------------------------------------------------
    for t in range(period, n):
        s_old = season_hist[t - period]
        fitted[t] = level + trend + s_old      # previsione a un passo

        new_level = alpha * (arr[t] - s_old) + (1.0 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1.0 - beta) * trend
        new_season = gamma * (arr[t] - new_level) + (1.0 - gamma) * s_old

        level, trend = new_level, new_trend
        season_hist.append(new_season)

    # --- previsione --------------------------------------------------------
    forecast = np.empty(horizon, dtype=float)
    for h in range(1, horizon + 1):
        # Indice stagionale piu' recente disponibile per il mese bersaglio.
        s_index = len(season_hist) - period + ((h - 1) % period)
        forecast[h - 1] = level + h * trend + season_hist[s_index]
    forecast = np.maximum(forecast, 0.0)

    return ForecastResult(
        method="Holt-Winters additivo",
        forecast=forecast,
        fitted=fitted,
        params={
            "alpha": float(alpha),
            "beta": float(beta),
            "gamma": float(gamma),
            "period": float(period),
        },
    ).with_residuals(arr)


# ---------------------------------------------------------------------------
# Registro dei metodi
# ---------------------------------------------------------------------------

#: Mappa ``nome italiano -> funzione``. La dashboard e il motore di
#: valutazione iterano su questo registro: aggiungere un metodo richiede solo
#: di inserire una voce qui.
METHOD_REGISTRY: Dict[str, Callable[..., ForecastResult]] = {
    "Media mobile": moving_average_forecast,
    "Smorzamento esponenziale": simple_exponential_smoothing,
    "Regressione lineare": linear_trend_regression,
    "Naive stagionale": seasonal_naive_forecast,
    "Holt-Winters additivo": holt_winters_additive,
}

METHOD_NAMES: List[str] = list(METHOD_REGISTRY)

#: Parametri configurabili dalla dashboard, per metodo.
METHOD_TUNABLE_PARAMS: Dict[str, List[str]] = {
    "Media mobile": ["window"],
    "Smorzamento esponenziale": ["alpha"],
    "Regressione lineare": [],
    "Naive stagionale": ["period"],
    "Holt-Winters additivo": ["period"],
}

#: Descrizioni sintetiche mostrate in dashboard.
METHOD_DESCRIPTIONS: Dict[str, str] = {
    "Media mobile": (
        "Media delle ultime N osservazioni; previsione piatta. Adatta a serie "
        "stazionarie, non coglie trend ne' stagionalita'."
    ),
    "Smorzamento esponenziale": (
        "Media ponderata con pesi decrescenti in modo esponenziale verso il "
        "passato. Reagisce ai cambi di livello, non modella il trend."
    ),
    "Regressione lineare": (
        "Retta dei minimi quadrati sul tempo. Coglie il trend sistematico ma "
        "ignora completamente la stagionalita'."
    ),
    "Naive stagionale": (
        "Ripete il valore osservato nello stesso mese dell'anno precedente. "
        "Benchmark di riferimento per serie stagionali."
    ),
    "Holt-Winters additivo": (
        "Smorzamento esponenziale triplo: aggiorna congiuntamente livello, "
        "trend e indici stagionali. Adatto a serie con trend e stagionalita'."
    ),
}


def available_methods(n_observations: int, period: int = SEASONAL_PERIOD) -> List[str]:
    """Restituisce i metodi applicabili data la lunghezza della serie.

    Serve a evitare che la dashboard proponga, ad esempio, Holt-Winters su
    una serie troppo corta: i requisiti minimi sono 24 osservazioni per
    Holt-Winters e 13 per il naive stagionale (con periodo 12).
    """
    methods: List[str] = []
    for name in METHOD_REGISTRY:
        if name == "Holt-Winters additivo" and n_observations < 2 * period:
            continue
        if name == "Naive stagionale" and n_observations < period + 1:
            continue
        if name == "Regressione lineare" and n_observations < 3:
            continue
        methods.append(name)
    return methods


def run_method(
    name: str,
    y,
    horizon: int,
    params: Optional[Mapping[str, float]] = None,
) -> ForecastResult:
    """Esegue un metodo del registro per nome.

    Parameters
    ----------
    name:
        Nome del metodo cosi' come compare in :data:`METHOD_REGISTRY`.
    y:
        Serie storica di addestramento.
    horizon:
        Orizzonte di previsione in mesi.
    params:
        Parametri specifici del metodo (es. ``{"window": 6}``). I parametri
        non pertinenti al metodo invocato vengono ignorati.

    Raises
    ------
    ForecastingError
        Se il metodo non esiste o i parametri non sono validi.
    """
    if name not in METHOD_REGISTRY:
        raise ForecastingError(
            f"Metodo previsionale '{name}' non riconosciuto. "
            "Metodi disponibili: " + ", ".join(METHOD_NAMES) + "."
        )

    func = METHOD_REGISTRY[name]
    accepted = METHOD_TUNABLE_PARAMS.get(name, [])
    kwargs = {k: v for k, v in (params or {}).items() if k in accepted}
    return func(y, horizon, **kwargs)
