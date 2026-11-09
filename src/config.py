"""
Configurazione centrale del Project Work 24.

Questo modulo raccoglie tutte le costanti di progetto: percorsi, orizzonte
temporale del dataset storico, anagrafica dei quattro prodotti analizzati e
parametri di generazione delle serie sintetiche.

AVVERTENZA ACCADEMICA
---------------------
Ferrero e i prodotti citati (Nutella, Kinder Cioccolato, Ferrero Rocher,
Kinder Happy Hippo) sono reali. I parametri numerici contenuti in questo file
sono invece INVENTATI a scopo esclusivamente didattico: servono a generare
serie storiche sintetiche plausibili, NON rappresentano vendite reali Ferrero
e non derivano da alcuna fonte aziendale riservata.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Dict, List

# ---------------------------------------------------------------------------
# Percorsi di progetto
# ---------------------------------------------------------------------------

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
REPORT_DIR: Path = PROJECT_ROOT / "report"
FIGURES_DIR: Path = REPORT_DIR / "figures"

DEMAND_HISTORY_CSV: Path = DATA_DIR / "demand_history.csv"
DEMAND_WIDE_CSV: Path = DATA_DIR / "demand_history_wide.csv"
PRODUCT_PARAMETERS_CSV: Path = DATA_DIR / "product_parameters.csv"

# ---------------------------------------------------------------------------
# Orizzonte temporale del dataset storico
# ---------------------------------------------------------------------------

HISTORY_START: str = "2022-01-01"
N_PERIODS: int = 48           # 48 osservazioni mensili: gen-2022 / dic-2025
FREQUENCY: str = "MS"         # inizio mese (Month Start)

#: Seed globale: garantisce la riproducibilita' del dataset di base.
RANDOM_SEED: int = 24

#: Numero minimo di osservazioni mensili accettate dal livello di validazione.
MIN_OBSERVATIONS: int = 24

# ---------------------------------------------------------------------------
# Split cronologico train/test
# ---------------------------------------------------------------------------

#: Numero di mesi riservati al test set (gli ultimi del periodo storico).
DEFAULT_TEST_SIZE: int = 12

#: Numero minimo di osservazioni che devono restare nel training set.
MIN_TRAIN_SIZE: int = 24

# ---------------------------------------------------------------------------
# Parametri previsionali di default
# ---------------------------------------------------------------------------

DEFAULT_FORECAST_HORIZON: int = 12
FORECAST_HORIZON_OPTIONS: List[int] = [3, 6, 12]

DEFAULT_MA_WINDOW: int = 3
MA_WINDOW_OPTIONS: List[int] = [3, 6, 12]

DEFAULT_ALPHA: float = 0.30

SEASONAL_PERIOD: int = 12

# ---------------------------------------------------------------------------
# Parametri logistici / di scorta di default
# ---------------------------------------------------------------------------

DEFAULT_LEAD_TIME_MONTHS: float = 2.0
DEFAULT_REVIEW_PERIOD_MONTHS: float = 1.0
DEFAULT_SERVICE_LEVEL: float = 0.95

#: Livelli di servizio selezionabili in dashboard (ciclo di ordine tipo).
SERVICE_LEVEL_OPTIONS: List[float] = [0.90, 0.95, 0.975, 0.99]

#: Fattori di sicurezza z della distribuzione normale standard, tabulati per
#: riferimento/documentazione. A runtime il valore e' calcolato con
#: ``scipy.stats.norm.ppf`` (cfr. :mod:`src.inventory`).
Z_SCORE_REFERENCE: Dict[float, float] = {
    0.90: 1.2816,
    0.95: 1.6449,
    0.975: 1.9600,
    0.99: 2.3263,
}


# ---------------------------------------------------------------------------
# Anagrafica e parametri di generazione dei prodotti
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProductParameters:
    """Parametri che descrivono il processo generatore di un prodotto.

    Il modello di domanda implementato in :mod:`src.data_generator` e':

    ``domanda(t) = livello(t) * fattore_stagionale(mese) * (1 + rumore) + promo(t)``

    dove ``livello(t) = base_demand * (1 + trend_rate * t)``.

    Attributes
    ----------
    name:
        Nome commerciale del prodotto (reale).
    category:
        Categoria merceologica di appartenenza (informazione pubblica).
    unit:
        Unita' di misura della domanda (cartoni/mese nella simulazione).
    base_demand:
        Livello medio di domanda al tempo t=0, in unita' di misura.
    trend_rate:
        Incremento percentuale lineare per mese (0.005 = +0.5% al mese
        rispetto al livello base).
    seasonal_amplitude:
        Ampiezza della componente stagionale sinusoidale (0.10 = +/-10%).
    seasonal_peak_month:
        Mese (1-12) in cui la sinusoide raggiunge il massimo.
    festive_profile:
        Sovra-domanda addizionale per mese, espressa come quota del livello
        (es. ``{11: 0.85}`` = +85% a novembre). Modella i picchi natalizi che
        una semplice sinusoide non riuscirebbe a riprodurre.
    noise_std:
        Deviazione standard del rumore casuale moltiplicativo, espressa come
        coefficiente di variazione del livello (0.08 = 8%).
    promotion_probability:
        Probabilita' mensile che si verifichi un picco promozionale.
    promotion_amplitude:
        Entita' del picco promozionale, come quota del livello corrente.
    description:
        Descrizione sintetica del comportamento atteso della serie.
    """

    name: str
    category: str
    unit: str
    base_demand: float
    trend_rate: float
    seasonal_amplitude: float
    seasonal_peak_month: int
    noise_std: float
    promotion_probability: float
    promotion_amplitude: float
    description: str
    festive_profile: Dict[int, float] = field(default_factory=dict)

    def to_row(self) -> Dict[str, object]:
        """Serializza i parametri in un dizionario adatto a un CSV piatto."""
        row = asdict(self)
        festive = row.pop("festive_profile") or {}
        # Il profilo festivo viene appiattito in una stringa "mese:valore;..."
        row["festive_profile"] = ";".join(
            f"{month}:{value}" for month, value in sorted(festive.items())
        )
        return row

    def scaled(
        self,
        *,
        variability_multiplier: float = 1.0,
        trend_multiplier: float = 1.0,
        seasonality_multiplier: float = 1.0,
    ) -> "ProductParameters":
        """Restituisce una copia dei parametri riscalata per uno scenario.

        I moltiplicatori agiscono separatamente sulle tre leve richieste dalla
        specifica PW24 (variabilita', trend, stagionalita'); con tutti i
        moltiplicatori pari a 1.0 la copia e' identica all'originale e la
        serie rigenerata coincide esattamente con quella di base.
        """
        return replace(
            self,
            noise_std=self.noise_std * variability_multiplier,
            promotion_amplitude=self.promotion_amplitude * variability_multiplier,
            trend_rate=self.trend_rate * trend_multiplier,
            seasonal_amplitude=self.seasonal_amplitude * seasonality_multiplier,
            festive_profile={
                month: value * seasonality_multiplier
                for month, value in self.festive_profile.items()
            },
        )


#: Parametri sintetici dei quattro prodotti analizzati.
#: I quattro profili sono volutamente differenti fra loro, come richiesto
#: dalla specifica del Project Work 24.
PRODUCTS: Dict[str, ProductParameters] = {
    "Nutella": ProductParameters(
        name="Nutella",
        category="Crema spalmabile alla nocciola",
        unit="cartoni/mese",
        base_demand=12_000.0,
        trend_rate=0.0010,          # ~ +1,2% all'anno: trend molto contenuto
        seasonal_amplitude=0.05,    # stagionalita' debole (+/-5%)
        seasonal_peak_month=11,
        noise_std=0.05,             # variabilita' casuale bassa
        promotion_probability=0.00,
        promotion_amplitude=0.00,
        description=(
            "Domanda relativamente stabile, variabilita' casuale bassa, "
            "trend molto limitato e stagionalita' debole."
        ),
        festive_profile={},
    ),
    "Kinder Cioccolato": ProductParameters(
        name="Kinder Cioccolato",
        category="Snack di cioccolato al latte",
        unit="cartoni/mese",
        base_demand=8_000.0,
        trend_rate=0.0050,          # ~ +6% all'anno: trend positivo moderato
        seasonal_amplitude=0.12,    # stagionalita' debole/moderata
        seasonal_peak_month=12,
        noise_std=0.08,             # variabilita' moderata
        promotion_probability=0.06,
        promotion_amplitude=0.12,
        description=(
            "Domanda moderatamente stabile con trend positivo moderato, "
            "variabilita' casuale moderata e stagionalita' debole/moderata "
            "(calo estivo tipico del cioccolato)."
        ),
        festive_profile={},
    ),
    "Ferrero Rocher": ProductParameters(
        name="Ferrero Rocher",
        category="Praline di cioccolato (pralineria da regalo)",
        unit="cartoni/mese",
        base_demand=5_000.0,
        trend_rate=0.0030,          # trend di lungo periodo moderato
        seasonal_amplitude=0.18,
        seasonal_peak_month=12,
        noise_std=0.10,             # variabilita' casuale moderata
        promotion_probability=0.00,
        promotion_amplitude=0.00,
        description=(
            "Stagionalita' forte con picchi rilevanti nel periodo "
            "natalizio/festivo, variabilita' moderata e trend di lungo "
            "periodo moderato."
        ),
        # Picchi natalizi: la produzione/spedizione anticipa il consumo,
        # quindi il massimo cade fra ottobre e novembre.
        festive_profile={10: 0.45, 11: 1.05, 12: 0.75},
    ),
    "Kinder Happy Hippo": ProductParameters(
        name="Kinder Happy Hippo",
        category="Snack wafer ripieno",
        unit="cartoni/mese",
        base_demand=3_000.0,
        trend_rate=0.0060,          # ~ +7% all'anno
        seasonal_amplitude=0.12,    # stagionalita' moderata
        seasonal_peak_month=12,
        noise_std=0.18,             # rumore piu' elevato degli altri prodotti
        promotion_probability=0.20,  # picchi promozionali frequenti
        promotion_amplitude=0.45,
        description=(
            "Domanda piu' variabile, trend positivo moderato, picchi "
            "promozionali casuali, stagionalita' moderata e rumore "
            "superiore a Nutella e Kinder Cioccolato."
        ),
        festive_profile={},
    ),
}

#: Elenco ordinato dei nomi prodotto (usato da validazione e dashboard).
PRODUCT_NAMES: List[str] = list(PRODUCTS.keys())

# ---------------------------------------------------------------------------
# Etichette italiane riutilizzate da dashboard e documentazione
# ---------------------------------------------------------------------------

MONTH_NAMES_IT: List[str] = [
    "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre",
]

STOCK_LABELS_IT: Dict[str, str] = {
    "cycle_stock": "Scorta ciclica",
    "safety_stock": "Scorta di sicurezza",
    "anticipation_stock": "Scorta anticipata",
    "pipeline_stock": "Scorta pipeline",
}

#: Disclaimer da mostrare in dashboard e documentazione.
SYNTHETIC_DATA_DISCLAIMER: str = (
    "I dati di domanda utilizzati in questo progetto sono **sintetici** e "
    "generati algoritmicamente a soli fini didattici. L'impresa Ferrero e i "
    "prodotti citati sono reali, ma **nessun valore numerico rappresenta "
    "vendite, scorte o informazioni riservate Ferrero**."
)
