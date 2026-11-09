"""
Simulazione degli scenari.

Il modulo collega le leve configurabili dalla dashboard (variabilita',
trend, stagionalita', lead time, livello di servizio, parametri previsionali)
all'intera catena di calcolo: serie di domanda -> previsione -> scorte.

Principio di funzionamento
--------------------------
Le leve **non** sono etichette cosmetiche: le tre leve di domanda agiscono
sui parametri del processo generatore e la serie di scenario viene
**rigenerata** con lo stesso seed casuale. Questo garantisce due proprieta'
importanti:

1. **coerenza statistica** - lo scenario e' una realizzazione legittima dello
   stesso modello, non una deformazione arbitraria di una serie esistente;
2. **neutralita' dell'identita'** - con tutti i moltiplicatori pari a 1,0 la
   serie di scenario coincide *esattamente* con il dataset storico di base
   (proprieta' verificata nei test automatici).

Separazione dei dati
--------------------
Il dataset storico su disco (``data/demand_history.csv``) non viene **mai**
sovrascritto dalla simulazione: lo scenario vive interamente in memoria e la
:class:`ScenarioOutcome` conserva sia la serie di base sia quella simulata,
permettendo alla dashboard di distinguerle visivamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import (
    DEFAULT_ALPHA,
    DEFAULT_FORECAST_HORIZON,
    DEFAULT_LEAD_TIME_MONTHS,
    DEFAULT_MA_WINDOW,
    DEFAULT_REVIEW_PERIOD_MONTHS,
    DEFAULT_SERVICE_LEVEL,
    DEFAULT_TEST_SIZE,
    PRODUCTS,
    RANDOM_SEED,
    SEASONAL_PERIOD,
)
from .data_generator import build_date_index, generate_product_series
from .evaluation import (
    EvaluationError,
    ForecastBundle,
    evaluate_methods,
    forecast_with_interval,
    select_best_method,
)
from .inventory import InventoryPlan, compute_inventory_plan

__all__ = [
    "ScenarioError",
    "ScenarioConfig",
    "ScenarioOutcome",
    "simulate_scenario",
    "build_scenario_series",
    "compare_scenarios",
    "PRESET_SCENARIOS",
]


class ScenarioError(Exception):
    """Errore di configurazione dello scenario, con messaggio in italiano."""


# ---------------------------------------------------------------------------
# Configurazione di uno scenario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioConfig:
    """Parametri completi di uno scenario simulato.

    Le prime tre leve riscalano i parametri del processo generatore, le
    successive agiscono sulla previsione e sul dimensionamento delle scorte.

    Attributes
    ----------
    name:
        Etichetta dello scenario (es. "Scenario A").
    product:
        Prodotto analizzato.
    variability_multiplier:
        Moltiplicatore della variabilita' casuale (1,0 = baseline).
    trend_multiplier:
        Moltiplicatore del tasso di trend (1,0 = baseline; 0,0 = nessun trend;
        valori negativi invertono la direzione del trend).
    seasonality_multiplier:
        Moltiplicatore dell'ampiezza stagionale (1,0 = baseline; 0,0 =
        domanda destagionalizzata).
    lead_time_months:
        Lead time di approvvigionamento in mesi.
    service_level:
        Livello di servizio obiettivo.
    review_period_months:
        Periodo di riesame/riordino in mesi.
    forecast_horizon:
        Orizzonte di previsione in mesi.
    method:
        Metodo previsionale; ``None`` attiva la selezione automatica del
        metodo migliore secondo il criterio MAPE.
    ma_window:
        Ampiezza della finestra della media mobile.
    alpha:
        Parametro di smorzamento esponenziale.
    test_size:
        Mesi riservati alla validazione out-of-sample.
    include_review_in_protection:
        Se ``True`` l'intervallo di protezione della scorta di sicurezza
        include anche il periodo di riesame.
    """

    name: str = "Scenario"
    product: str = "Nutella"
    variability_multiplier: float = 1.0
    trend_multiplier: float = 1.0
    seasonality_multiplier: float = 1.0
    lead_time_months: float = DEFAULT_LEAD_TIME_MONTHS
    service_level: float = DEFAULT_SERVICE_LEVEL
    review_period_months: float = DEFAULT_REVIEW_PERIOD_MONTHS
    forecast_horizon: int = DEFAULT_FORECAST_HORIZON
    method: Optional[str] = None
    ma_window: int = DEFAULT_MA_WINDOW
    alpha: float = DEFAULT_ALPHA
    test_size: int = DEFAULT_TEST_SIZE
    include_review_in_protection: bool = False
    seed: int = RANDOM_SEED

    def validate(self) -> None:
        """Verifica la coerenza dei parametri, con messaggi in italiano.

        Raises
        ------
        ScenarioError
            Se una delle leve e' fuori dall'intervallo ammesso.
        """
        errors: List[str] = []

        if self.product not in PRODUCTS:
            errors.append(
                f"Prodotto '{self.product}' non presente in anagrafica. "
                "Prodotti ammessi: " + ", ".join(PRODUCTS) + "."
            )
        if self.variability_multiplier < 0:
            errors.append(
                "Il moltiplicatore di variabilita' non puo' essere negativo "
                f"(ricevuto: {self.variability_multiplier})."
            )
        if self.seasonality_multiplier < 0:
            errors.append(
                "Il moltiplicatore di stagionalita' non puo' essere negativo "
                f"(ricevuto: {self.seasonality_multiplier})."
            )
        if self.lead_time_months < 0:
            errors.append(
                f"Il lead time non puo' essere negativo (ricevuto: "
                f"{self.lead_time_months} mesi)."
            )
        if self.lead_time_months > 24:
            errors.append(
                "Il lead time supera i 24 mesi: valore non plausibile per "
                "una filiera alimentare."
            )
        if not 0.5 <= self.service_level < 1.0:
            errors.append(
                "Il livello di servizio deve essere compreso fra 50% e 100% "
                f"(escluso); ricevuto: {self.service_level:.1%}."
            )
        if self.review_period_months <= 0:
            errors.append(
                "Il periodo di riesame deve essere maggiore di zero mesi "
                f"(ricevuto: {self.review_period_months})."
            )
        if self.forecast_horizon < 1:
            errors.append(
                "L'orizzonte di previsione deve essere di almeno 1 mese "
                f"(ricevuto: {self.forecast_horizon})."
            )
        if self.ma_window < 1:
            errors.append(
                "La finestra della media mobile deve essere di almeno 1 mese "
                f"(ricevuto: {self.ma_window})."
            )
        if not 0.0 < self.alpha <= 1.0:
            errors.append(
                "Il parametro alpha deve essere compreso fra 0 (escluso) e 1 "
                f"(ricevuto: {self.alpha})."
            )
        if self.test_size < 1:
            errors.append(
                "Il periodo di test deve essere di almeno 1 mese "
                f"(ricevuto: {self.test_size})."
            )

        if errors:
            raise ScenarioError("\n".join(f"- {e}" for e in errors))

    @property
    def is_baseline(self) -> bool:
        """``True`` se le tre leve di domanda sono al valore neutro."""
        return (
            np.isclose(self.variability_multiplier, 1.0)
            and np.isclose(self.trend_multiplier, 1.0)
            and np.isclose(self.seasonality_multiplier, 1.0)
        )

    @property
    def method_params(self) -> Dict[str, float]:
        """Parametri previsionali nel formato atteso dal registro metodi."""
        return {
            "window": self.ma_window,
            "alpha": self.alpha,
            "period": SEASONAL_PERIOD,
        }

    def describe_levers(self) -> Dict[str, str]:
        """Descrizione testuale italiana delle leve, per la dashboard."""
        return {
            "Variabilita' domanda": f"x {self.variability_multiplier:.2f}",
            "Trend": f"x {self.trend_multiplier:.2f}",
            "Stagionalita'": f"x {self.seasonality_multiplier:.2f}",
            "Lead time": f"{self.lead_time_months:.1f} mesi",
            "Livello di servizio": f"{self.service_level:.1%}",
            "Periodo di riesame": f"{self.review_period_months:.1f} mesi",
            "Orizzonte previsione": f"{self.forecast_horizon} mesi",
        }


# ---------------------------------------------------------------------------
# Esito di uno scenario
# ---------------------------------------------------------------------------


@dataclass
class ScenarioOutcome:
    """Risultato completo della simulazione di uno scenario.

    Attributes
    ----------
    config:
        Configurazione che ha generato il risultato.
    baseline_series:
        Serie storica di base (dataset originale, mai modificato).
    scenario_series:
        Serie storica rigenerata con i parametri di scenario.
    comparison:
        Tabella di confronto dei metodi previsionali sulla serie di scenario.
    best_method:
        Metodo selezionato automaticamente secondo il criterio MAPE.
    bundle:
        Previsione finale con banda di incertezza.
    plan:
        Piano di scorta risultante.
    """

    config: ScenarioConfig
    baseline_series: pd.Series
    scenario_series: pd.Series
    comparison: pd.DataFrame
    best_method: str
    bundle: ForecastBundle
    plan: InventoryPlan
    diagnostics: Dict[str, float] = field(default_factory=dict)

    @property
    def used_method(self) -> str:
        """Metodo effettivamente impiegato per la previsione finale."""
        return self.bundle.method

    def kpi_table(self) -> pd.DataFrame:
        """Tabella sintetica degli indicatori principali dello scenario."""
        plan = self.plan
        return pd.DataFrame(
            {
                "Indicatore": [
                    "Domanda media storica (unita'/mese)",
                    "Domanda media prevista (unita'/mese)",
                    "Deviazione std errore previsionale (unita')",
                    "Lead time (mesi)",
                    "Livello di servizio",
                    "Scorta ciclica (unita')",
                    "Scorta di sicurezza (unita')",
                    "Scorta anticipata (unita')",
                    "Scorta pipeline (unita')",
                    "Scorta totale (unita')",
                    "Copertura scorta totale (mesi)",
                ],
                "Valore": [
                    self.scenario_series.mean(),
                    plan.average_demand,
                    plan.sigma_monthly,
                    plan.lead_time_months,
                    plan.service_level,
                    plan.cycle_stock,
                    plan.safety_stock,
                    plan.anticipation_stock,
                    plan.pipeline_stock,
                    plan.total_stock,
                    plan.coverage_months,
                ],
            }
        )


# ---------------------------------------------------------------------------
# Costruzione della serie di scenario
# ---------------------------------------------------------------------------


def build_scenario_series(
    config: ScenarioConfig,
    dates: Optional[pd.DatetimeIndex] = None,
) -> pd.Series:
    """Rigenera la serie storica del prodotto con i parametri di scenario.

    I moltiplicatori di variabilita', trend e stagionalita' riscalano i
    parametri del processo generatore; il seed resta invariato, cosicche' la
    sequenza di shock casuali sia la stessa e le differenze osservate siano
    attribuibili **unicamente** alle leve modificate.
    """
    config.validate()
    base_params = PRODUCTS[config.product]
    scenario_params = base_params.scaled(
        variability_multiplier=config.variability_multiplier,
        trend_multiplier=config.trend_multiplier,
        seasonality_multiplier=config.seasonality_multiplier,
    )
    product_index = list(PRODUCTS).index(config.product)
    return generate_product_series(
        scenario_params,
        dates=dates if dates is not None else build_date_index(),
        seed=config.seed,
        product_index=product_index,
    )


# ---------------------------------------------------------------------------
# Simulazione completa
# ---------------------------------------------------------------------------


def simulate_scenario(
    config: ScenarioConfig,
    baseline_series: Optional[pd.Series] = None,
) -> ScenarioOutcome:
    """Esegue l'intera catena di calcolo per uno scenario.

    Passi:

    1. rigenerazione della serie di domanda con le leve di scenario;
    2. valutazione out-of-sample di tutti i metodi previsionali;
    3. selezione del metodo (automatica o imposta dall'utente);
    4. previsione finale con banda di incertezza;
    5. dimensionamento delle quattro componenti di scorta.

    Raises
    ------
    ScenarioError
        Se i parametri non sono validi o la catena di calcolo fallisce, con
        messaggio in italiano adatto alla dashboard.
    """
    config.validate()

    scenario_series = build_scenario_series(config)
    if baseline_series is None:
        baseline_series = build_scenario_series(
            replace(
                config,
                variability_multiplier=1.0,
                trend_multiplier=1.0,
                seasonality_multiplier=1.0,
            )
        )

    try:
        comparison = evaluate_methods(
            scenario_series,
            product=config.product,
            test_size=config.test_size,
            method_params=config.method_params,
        )
        best_method = select_best_method(comparison)
        method = config.method or best_method

        bundle = forecast_with_interval(
            scenario_series,
            product=config.product,
            method=method,
            horizon=config.forecast_horizon,
            test_size=config.test_size,
            method_params=config.method_params,
            confidence_level=0.95,
        )
    except EvaluationError as exc:
        raise ScenarioError(
            f"Impossibile completare la previsione per '{config.product}': {exc}"
        ) from exc

    comparison["Migliore"] = comparison["Metodo"] == best_method

    plan = compute_inventory_plan(
        product=config.product,
        forecast=bundle.forecast.to_numpy(dtype=float),
        sigma_monthly=bundle.sigma_forecast_error,
        lead_time_months=config.lead_time_months,
        service_level=config.service_level,
        review_period_months=config.review_period_months,
        include_review_in_protection=config.include_review_in_protection,
    )

    diagnostics = {
        "cv_storico_%": float(
            scenario_series.std(ddof=1) / scenario_series.mean() * 100.0
        ),
        "domanda_media_storica": float(scenario_series.mean()),
        "delta_vs_baseline_%": float(
            (scenario_series.mean() - baseline_series.mean())
            / baseline_series.mean()
            * 100.0
        )
        if baseline_series.mean() != 0
        else 0.0,
        "ampiezza_banda_%": float(
            (bundle.upper - bundle.lower).mean() / bundle.forecast.mean() * 100.0
        )
        if bundle.forecast.mean() != 0
        else 0.0,
    }

    return ScenarioOutcome(
        config=config,
        baseline_series=baseline_series,
        scenario_series=scenario_series,
        comparison=comparison,
        best_method=best_method,
        bundle=bundle,
        plan=plan,
        diagnostics=diagnostics,
    )


# ---------------------------------------------------------------------------
# Confronto fra scenari
# ---------------------------------------------------------------------------


def compare_scenarios(
    outcome_a: ScenarioOutcome,
    outcome_b: ScenarioOutcome,
) -> pd.DataFrame:
    """Costruisce la tabella di confronto fra due scenari.

    Returns
    -------
    pandas.DataFrame
        Colonne: ``Indicatore``, nome scenario A, nome scenario B,
        ``Variazione``, ``Variazione %``.
    """
    name_a = outcome_a.config.name
    name_b = outcome_b.config.name
    if name_a == name_b:
        name_a, name_b = f"{name_a} (A)", f"{name_b} (B)"

    indicators = [
        ("Domanda media prevista (unita'/mese)", lambda o: o.plan.average_demand),
        ("Dev. std errore previsionale (unita')", lambda o: o.plan.sigma_monthly),
        ("Scorta ciclica (unita')", lambda o: o.plan.cycle_stock),
        ("Scorta di sicurezza (unita')", lambda o: o.plan.safety_stock),
        ("Scorta anticipata (unita')", lambda o: o.plan.anticipation_stock),
        ("Scorta pipeline (unita')", lambda o: o.plan.pipeline_stock),
        ("Scorta totale (unita')", lambda o: o.plan.total_stock),
        ("Copertura scorta totale (mesi)", lambda o: o.plan.coverage_months),
    ]

    rows = []
    for label, getter in indicators:
        value_a = float(getter(outcome_a))
        value_b = float(getter(outcome_b))
        delta = value_b - value_a
        pct = (delta / value_a * 100.0) if value_a != 0 else np.nan
        rows.append(
            {
                "Indicatore": label,
                name_a: value_a,
                name_b: value_b,
                "Variazione": delta,
                "Variazione %": pct,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Scenari predefiniti
# ---------------------------------------------------------------------------

#: Configurazioni preimpostate selezionabili in dashboard. Riproducono i due
#: casi tipici citati nella specifica PW24 (filiera stabile vs filiera sotto
#: stress) piu' due varianti utili alla discussione.
PRESET_SCENARIOS: Dict[str, Dict[str, float]] = {
    "Baseline (dataset storico)": {
        "variability_multiplier": 1.0,
        "trend_multiplier": 1.0,
        "seasonality_multiplier": 1.0,
        "lead_time_months": 2.0,
        "service_level": 0.95,
    },
    "A - Filiera stabile": {
        "variability_multiplier": 0.5,
        "trend_multiplier": 1.0,
        "seasonality_multiplier": 1.0,
        "lead_time_months": 2.0,
        "service_level": 0.95,
    },
    "B - Filiera sotto stress": {
        "variability_multiplier": 2.0,
        "trend_multiplier": 1.0,
        "seasonality_multiplier": 1.0,
        "lead_time_months": 5.0,
        "service_level": 0.99,
    },
    "C - Picco stagionale accentuato": {
        "variability_multiplier": 1.0,
        "trend_multiplier": 1.0,
        "seasonality_multiplier": 2.0,
        "lead_time_months": 3.0,
        "service_level": 0.975,
    },
    "D - Crescita sostenuta": {
        "variability_multiplier": 1.0,
        "trend_multiplier": 3.0,
        "seasonality_multiplier": 1.0,
        "lead_time_months": 2.0,
        "service_level": 0.95,
    },
}
