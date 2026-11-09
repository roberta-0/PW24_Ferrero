"""
Valutazione out-of-sample e selezione del modello.

Il modulo implementa lo **split cronologico train/test** richiesto dalla
specifica PW24 e il criterio automatico di scelta del metodo migliore per
ciascun prodotto.

Principio metodologico
----------------------
Le serie storiche **non** possono essere mescolate casualmente: l'ordine
temporale porta informazione. Lo split e' quindi rigorosamente cronologico:

    [-------- training (primi T-k mesi) --------][--- test (ultimi k) ---]

I modelli sono stimati **esclusivamente** sul training set e le previsioni
per i ``k`` mesi di test sono confrontate con la domanda effettivamente
osservata. Nessuna informazione del test set entra nella stima: la
valutazione e' pertanto onesta (out-of-sample).

Criterio di selezione del metodo migliore
-----------------------------------------
Il criterio primario e' il **MAPE** out-of-sample minimo, perche':

* e' adimensionale, quindi confrontabile fra prodotti con volumi molto
  diversi (Nutella ~12.000 vs Happy Hippo ~3.000 unita'/mese);
* e' immediatamente interpretabile in sede di discussione manageriale
  ("il modello sbaglia in media del 7%").

**Fallback documentato**: se per un prodotto il MAPE non e' calcolabile
(tutte le osservazioni di test nulle), la selezione ripiega sull'**RMSE**
minimo. MAE e RMSE restano sempre esposti come indicatori di supporto.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_ALPHA,
    DEFAULT_MA_WINDOW,
    DEFAULT_TEST_SIZE,
    MIN_TRAIN_SIZE,
    SEASONAL_PERIOD,
)
from .forecasting import (
    ForecastingError,
    ForecastResult,
    available_methods,
    run_method,
)
from .metrics import compute_all_metrics

__all__ = [
    "EvaluationError",
    "TrainTestSplit",
    "chronological_split",
    "evaluate_methods",
    "select_best_method",
    "evaluate_all_products",
    "forecast_with_interval",
    "ForecastBundle",
]


class EvaluationError(Exception):
    """Errore di valutazione con messaggio in italiano."""


@dataclass(frozen=True)
class TrainTestSplit:
    """Risultato dello split cronologico di una serie storica."""

    train: pd.Series
    test: pd.Series

    @property
    def n_train(self) -> int:
        return len(self.train)

    @property
    def n_test(self) -> int:
        return len(self.test)


def chronological_split(
    series: pd.Series,
    test_size: int = DEFAULT_TEST_SIZE,
    min_train_size: int = MIN_TRAIN_SIZE,
) -> TrainTestSplit:
    """Divide la serie in training e test **rispettando l'ordine temporale**.

    Parameters
    ----------
    series:
        Serie storica indicizzata per data (ordine crescente).
    test_size:
        Numero di mesi finali riservati al test.
    min_train_size:
        Numero minimo di osservazioni che devono restare nel training.

    Raises
    ------
    EvaluationError
        Se la serie e' troppo corta per lo split richiesto.
    """
    series = series.sort_index()
    n = len(series)

    if test_size < 1:
        raise EvaluationError(
            f"La dimensione del test set deve essere almeno 1 mese "
            f"(richiesta: {test_size})."
        )
    if n - test_size < min_train_size:
        raise EvaluationError(
            f"Serie troppo corta per lo split richiesto: {n} osservazioni "
            f"disponibili, ne servono almeno {min_train_size + test_size} "
            f"(training minimo {min_train_size} + test {test_size})."
        )

    return TrainTestSplit(train=series.iloc[: n - test_size], test=series.iloc[n - test_size :])


def _default_method_params(
    ma_window: int = DEFAULT_MA_WINDOW,
    alpha: float = DEFAULT_ALPHA,
    period: int = SEASONAL_PERIOD,
) -> Dict[str, float]:
    """Raccoglie i parametri configurabili condivisi da tutti i metodi."""
    return {"window": ma_window, "alpha": alpha, "period": period}


def evaluate_methods(
    series: pd.Series,
    product: str,
    test_size: int = DEFAULT_TEST_SIZE,
    method_params: Optional[Mapping[str, float]] = None,
    methods: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Valuta tutti i metodi disponibili su una singola serie prodotto.

    Per ogni metodo: stima sul training, previsione sui ``test_size`` mesi di
    test, confronto con i valori osservati.

    Returns
    -------
    pandas.DataFrame
        Colonne: ``Prodotto``, ``Metodo``, ``MAE``, ``RMSE``, ``MAPE``,
        ``Bias``, ``sMAPE``, ``Nota`` (eventuale motivo di esclusione).
    """
    split = chronological_split(series, test_size=test_size)
    params = dict(_default_method_params())
    if method_params:
        params.update(method_params)

    candidates = list(
        methods
        if methods is not None
        else available_methods(split.n_train, period=int(params.get("period", SEASONAL_PERIOD)))
    )
    if not candidates:
        raise EvaluationError(
            f"Nessun metodo previsionale applicabile al prodotto '{product}': "
            f"lo storico di addestramento ({split.n_train} mesi) e' troppo breve."
        )

    y_test = split.test.to_numpy(dtype=float)
    rows: List[Dict[str, object]] = []

    for name in candidates:
        try:
            result: ForecastResult = run_method(
                name, split.train.to_numpy(dtype=float), split.n_test, params
            )
            metrics = compute_all_metrics(y_test, result.forecast)
            rows.append(
                {
                    "Prodotto": product,
                    "Metodo": name,
                    "Etichetta": result.method,
                    **metrics,
                    "Nota": "",
                }
            )
        except ForecastingError as exc:
            # Il metodo non e' applicabile: viene registrato ma escluso dal
            # confronto (metriche NaN), senza interrompere la valutazione.
            rows.append(
                {
                    "Prodotto": product,
                    "Metodo": name,
                    "Etichetta": name,
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "MAPE": np.nan,
                    "Bias": np.nan,
                    "sMAPE": np.nan,
                    "Nota": f"Non applicabile: {exc}",
                }
            )

    return pd.DataFrame(rows)


def select_best_method(results: pd.DataFrame) -> str:
    """Seleziona il metodo migliore secondo il criterio documentato.

    Criterio primario: **MAPE** out-of-sample minimo.
    Fallback (MAPE non calcolabile per nessun metodo): **RMSE** minimo.

    Raises
    ------
    EvaluationError
        Se nessun metodo ha prodotto metriche valide.
    """
    if results.empty:
        raise EvaluationError("Nessun risultato di valutazione disponibile.")

    by_mape = results.dropna(subset=["MAPE"])
    if not by_mape.empty:
        return str(by_mape.loc[by_mape["MAPE"].idxmin(), "Metodo"])

    by_rmse = results.dropna(subset=["RMSE"])
    if not by_rmse.empty:
        # Fallback documentato: il MAPE non e' definito (domanda sempre nulla).
        return str(by_rmse.loc[by_rmse["RMSE"].idxmin(), "Metodo"])

    raise EvaluationError(
        "Nessun metodo previsionale ha prodotto metriche valide: verificare "
        "la lunghezza e la qualita' della serie storica."
    )


def evaluate_all_products(
    data: pd.DataFrame,
    test_size: int = DEFAULT_TEST_SIZE,
    method_params: Optional[Mapping[str, float]] = None,
) -> tuple[pd.DataFrame, Dict[str, str]]:
    """Esegue la valutazione completa su tutti i prodotti del dataset.

    Parameters
    ----------
    data:
        Dataset in formato lungo (``date``, ``product``, ``demand``).
    test_size:
        Mesi riservati al test set.
    method_params:
        Parametri dei metodi (finestra media mobile, alpha, periodo).

    Returns
    -------
    tuple
        ``(tabella_confronto, {prodotto: metodo_migliore})``.
    """
    frames: List[pd.DataFrame] = []
    best: Dict[str, str] = {}

    for product, group in data.groupby("product", sort=False):
        series = group.set_index("date")["demand"].sort_index()
        results = evaluate_methods(
            series, product=product, test_size=test_size, method_params=method_params
        )
        frames.append(results)
        best[product] = select_best_method(results)

    comparison = pd.concat(frames, ignore_index=True)
    comparison["Migliore"] = comparison.apply(
        lambda r: best.get(r["Prodotto"]) == r["Metodo"], axis=1
    )
    return comparison, best


# ---------------------------------------------------------------------------
# Previsione finale con banda di incertezza
# ---------------------------------------------------------------------------


@dataclass
class ForecastBundle:
    """Previsione finale di un prodotto con tutti gli elementi di contesto.

    Attributes
    ----------
    product:
        Nome del prodotto.
    method:
        Metodo utilizzato per la previsione finale.
    method_label:
        Etichetta estesa del metodo (include i parametri).
    train / test:
        Partizioni cronologiche dello storico.
    test_forecast:
        Previsione sul periodo di test (usata per il calcolo delle metriche).
    future_index:
        Indice temporale mensile dei periodi previsti.
    forecast:
        Previsione per i periodi futuri.
    lower / upper:
        Estremi della banda di incertezza empirica.
    rmse_out_of_sample:
        RMSE out-of-sample usato per dimensionare la banda.
    sigma_forecast_error:
        Deviazione standard dell'errore previsionale adottata nel modello di
        scorta di sicurezza.
    confidence_level:
        Livello di confidenza nominale della banda.
    """

    product: str
    method: str
    method_label: str
    train: pd.Series
    test: pd.Series
    test_forecast: pd.Series
    future_index: pd.DatetimeIndex
    forecast: pd.Series
    lower: pd.Series
    upper: pd.Series
    rmse_out_of_sample: float
    sigma_forecast_error: float
    confidence_level: float


def forecast_with_interval(
    series: pd.Series,
    product: str,
    method: str,
    horizon: int,
    test_size: int = DEFAULT_TEST_SIZE,
    method_params: Optional[Mapping[str, float]] = None,
    confidence_level: float = 0.95,
) -> ForecastBundle:
    """Genera la previsione finale e una banda di incertezza empirica.

    Procedura in due passi:

    1. **Validazione** - il metodo e' stimato sul training set e valutato sui
       mesi di test; da questo confronto si ottiene l'RMSE out-of-sample.
    2. **Previsione finale** - il metodo e' ri-stimato su *tutta* la storia
       disponibile (training + test) e proiettato per ``horizon`` mesi.

    **Banda di incertezza**: ampiezza ``+/- z * RMSE_out_of_sample``, con ``z``
    quantile della normale standard al livello di confidenza richiesto.
    Si tratta di una **stima empirica basata sul modello**, non di un
    intervallo di previsione derivato analiticamente: assume errori
    indipendenti, a media nulla, distribuiti normalmente e con varianza
    costante lungo l'orizzonte. L'assunzione e' dichiarata esplicitamente in
    dashboard e in documentazione.
    """
    from scipy.stats import norm  # import locale: dipendenza usata solo qui

    if horizon < 1:
        raise EvaluationError(
            f"L'orizzonte di previsione deve essere di almeno 1 mese "
            f"(richiesto: {horizon})."
        )
    if not 0.5 < confidence_level < 1.0:
        raise EvaluationError(
            "Il livello di confidenza della banda deve essere compreso fra "
            f"0,5 e 1 (ricevuto {confidence_level})."
        )

    params = dict(_default_method_params())
    if method_params:
        params.update(method_params)

    series = series.sort_index()
    split = chronological_split(series, test_size=test_size)

    # (1) passo di validazione out-of-sample
    try:
        validation = run_method(
            method, split.train.to_numpy(dtype=float), split.n_test, params
        )
    except ForecastingError as exc:
        raise EvaluationError(str(exc)) from exc

    test_forecast = pd.Series(validation.forecast, index=split.test.index)
    out_of_sample = compute_all_metrics(split.test.to_numpy(dtype=float), validation.forecast)
    rmse_oos = float(out_of_sample["RMSE"])

    # (2) ri-stima su tutta la storia e proiezione futura
    try:
        final = run_method(method, series.to_numpy(dtype=float), horizon, params)
    except ForecastingError as exc:
        raise EvaluationError(str(exc)) from exc

    last_date = series.index[-1]
    future_index = pd.date_range(
        start=last_date + pd.DateOffset(months=1), periods=horizon, freq="MS"
    )
    forecast = pd.Series(np.maximum(final.forecast, 0.0), index=future_index)

    z = float(norm.ppf(0.5 + confidence_level / 2.0))
    half_width = z * rmse_oos
    lower = (forecast - half_width).clip(lower=0.0)
    upper = forecast + half_width

    return ForecastBundle(
        product=product,
        method=method,
        method_label=final.method,
        train=split.train,
        test=split.test,
        test_forecast=test_forecast,
        future_index=future_index,
        forecast=forecast,
        lower=lower,
        upper=upper,
        rmse_out_of_sample=rmse_oos,
        sigma_forecast_error=rmse_oos,
        confidence_level=confidence_level,
    )
