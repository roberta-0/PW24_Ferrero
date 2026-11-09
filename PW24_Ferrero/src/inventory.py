"""
Modelli di pianificazione delle scorte.

Il modulo calcola le quattro componenti di scorta richieste dalla specifica
PW24 - ciclica, di sicurezza, anticipata e pipeline - e la loro composizione
percentuale.

Notazione comune
----------------
=========  ==================================================================
Simbolo    Significato
=========  ==================================================================
``D``      domanda media mensile prevista (unita'/mese)
``R``      periodo di riesame / ciclo di riordino (mesi)
``L``      lead time di approvvigionamento (mesi)
``sigma``  deviazione standard mensile dell'errore previsionale (unita')
``z``      fattore di sicurezza della normale standard
=========  ==================================================================

AVVERTENZA: i modelli implementati sono formulazioni didattiche standard
della letteratura di Operations Management. **Non** riproducono le procedure
operative effettive di Ferrero, che non sono pubbliche.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

import numpy as np
from scipy.stats import norm

from .config import STOCK_LABELS_IT

__all__ = [
    "InventoryError",
    "service_level_to_z",
    "cycle_stock",
    "safety_stock",
    "anticipation_stock",
    "pipeline_stock",
    "InventoryPlan",
    "compute_inventory_plan",
]


class InventoryError(Exception):
    """Errore nei parametri di scorta, con messaggio in italiano."""


# ---------------------------------------------------------------------------
# Fattore di sicurezza
# ---------------------------------------------------------------------------


def service_level_to_z(service_level: float) -> float:
    """Converte un livello di servizio nel fattore di sicurezza ``z``.

    Il fattore e' il quantile della distribuzione normale standard::

        z = Phi^-1(service_level)

    Esempi: 90% -> 1,282 | 95% -> 1,645 | 97,5% -> 1,960 | 99% -> 2,326.

    Il livello di servizio e' qui inteso come **cycle service level**, ossia
    la probabilita' di non andare in rottura di stock durante un ciclo di
    riordino (non la frazione di domanda servita, che sarebbe il *fill rate*).
    """
    if not 0.5 <= service_level < 1.0:
        raise InventoryError(
            "Il livello di servizio deve essere compreso fra 50% e 100% "
            f"(escluso); valore ricevuto: {service_level:.3f}. "
            "Un livello del 100% richiederebbe una scorta infinita."
        )
    return float(norm.ppf(service_level))


# ---------------------------------------------------------------------------
# 1) Scorta ciclica
# ---------------------------------------------------------------------------


def cycle_stock(
    average_demand: float,
    review_period_months: float,
) -> float:
    """Scorta ciclica (cycle stock).

    **Modello adottato** - riordino a intervallo fisso con copertura pari al
    periodo di riesame. Il lotto di riordino e'::

        Q = D * R

    Con prelievi a tasso costante, la giacenza oscilla linearmente fra ``Q``
    (subito dopo il ricevimento) e ``0`` (alla fine del ciclo); la giacenza
    **media** dovuta al solo ciclo di riordino e' quindi::

        Scorta ciclica = Q / 2 = D * R / 2

    **Ipotesi semplificative dichiarate**: domanda prelevata a tasso uniforme
    all'interno del periodo, nessun vincolo di lotto minimo di produzione,
    nessuno sconto quantita'. Si e' deliberatamente evitato il modello EOQ di
    Wilson perche' richiederebbe costi di ordinazione e di mantenimento che,
    nel caso Ferrero, non sono pubblicamente disponibili e andrebbero a loro
    volta inventati.

    Parameters
    ----------
    average_demand:
        Domanda media mensile prevista ``D``.
    review_period_months:
        Periodo di riesame/riordino ``R`` in mesi.
    """
    if average_demand < 0:
        raise InventoryError(
            f"La domanda media non puo' essere negativa (ricevuto: {average_demand:.1f})."
        )
    if review_period_months <= 0:
        raise InventoryError(
            "Il periodo di riesame deve essere maggiore di zero mesi "
            f"(ricevuto: {review_period_months})."
        )
    return float(average_demand * review_period_months / 2.0)


# ---------------------------------------------------------------------------
# 2) Scorta di sicurezza
# ---------------------------------------------------------------------------


def safety_stock(
    sigma_monthly: float,
    lead_time_months: float,
    service_level: float,
    review_period_months: float = 0.0,
) -> float:
    """Scorta di sicurezza (safety stock).

    **Modello adottato** - formulazione classica basata sulla variabilita'
    della domanda durante l'intervallo di protezione::

        Scorta di sicurezza = z * sigma_LT

    dove ``sigma_LT`` e' la deviazione standard della domanda cumulata
    sull'intervallo di protezione. Assumendo errori previsionali mensili
    indipendenti e identicamente distribuiti, le varianze si sommano::

        sigma_LT = sigma * sqrt(intervallo di protezione)

    **Intervallo di protezione**: nella configurazione di base coincide con
    il solo lead time ``L`` (formulazione richiesta dalla specifica PW24).
    Impostando ``review_period_months > 0`` si adotta l'estensione classica
    del riordino periodico, in cui la copertura deve estendersi anche al
    periodo che intercorre fra due revisioni::

        sigma_LT = sigma * sqrt(L + R)

    **Ipotesi dichiarate**:

    * ``sigma`` e' stimata dalla variabilita' dell'**errore previsionale**
      out-of-sample (RMSE sul test set), non dalla variabilita' grezza della
      domanda: cio' che genera rottura di stock e' l'errore di previsione,
      non la stagionalita' gia' anticipata dal modello;
    * gli errori mensili sono assunti indipendenti (nessuna autocorrelazione);
    * il lead time e' deterministico (nessuna variabilita' di fornitura);
    * la domanda nell'intervallo di protezione e' approssimata come normale.

    Questa e' una formulazione didattica standard, **non** una procedura
    operativa Ferrero.
    """
    if sigma_monthly < 0:
        raise InventoryError(
            "La deviazione standard della domanda non puo' essere negativa "
            f"(ricevuto: {sigma_monthly:.1f})."
        )
    if lead_time_months < 0:
        raise InventoryError(
            f"Il lead time non puo' essere negativo (ricevuto: {lead_time_months})."
        )
    if review_period_months < 0:
        raise InventoryError(
            "Il periodo di riesame non puo' essere negativo "
            f"(ricevuto: {review_period_months})."
        )

    protection_interval = lead_time_months + review_period_months
    z = service_level_to_z(service_level)
    sigma_lt = sigma_monthly * np.sqrt(protection_interval)
    return float(z * sigma_lt)


# ---------------------------------------------------------------------------
# 3) Scorta anticipata
# ---------------------------------------------------------------------------


def anticipation_stock(
    forecast: Sequence[float],
    production_rate: Optional[float] = None,
) -> float:
    """Scorta anticipata (anticipation / seasonal stock).

    **Modello adottato** - *livellamento della produzione*. Si ipotizza che
    l'impresa produca a ritmo costante ``B`` (capacita' livellata) mentre la
    domanda prevista ``d(t)`` e' stagionale: nei mesi di bassa stagione si
    accumula scorta, che viene poi consumata durante il picco.

    Definendo l'eccedenza cumulata di domanda rispetto alla produzione::

        C(t) = sum_{k=1..t} ( d(k) - B ),        C(0) = 0

    la giacenza al tempo ``t`` vale ``I(t) = I(0) - C(t)``. Per non andare
    mai in rottura serve ``I(0) >= max_t C(t)``; adottando il valore minimo,
    la **giacenza massima** generata dal livellamento e'::

        Scorta anticipata = max_t C(t) - min_t C(t)        (con t >= 0)

    Il valore e' nullo per una domanda perfettamente piatta e cresce al
    crescere dell'ampiezza stagionale: e' quindi l'indicatore che risponde
    direttamente alla leva "stagionalita'" della dashboard. E' la componente
    dominante per Ferrero Rocher, la cui domanda si concentra nei mesi
    autunnali/natalizi.

    Parameters
    ----------
    forecast:
        Domanda prevista per ciascun mese dell'orizzonte.
    production_rate:
        Ritmo produttivo livellato ``B``; di default la media della domanda
        prevista sull'orizzonte (produzione perfettamente livellata).
    """
    values = np.asarray(forecast, dtype=float).ravel()
    if values.size == 0:
        raise InventoryError(
            "Impossibile calcolare la scorta anticipata: la previsione e' vuota."
        )
    if np.isnan(values).any():
        raise InventoryError(
            "Impossibile calcolare la scorta anticipata: la previsione "
            "contiene valori mancanti."
        )

    rate = float(np.mean(values)) if production_rate is None else float(production_rate)
    if rate < 0:
        raise InventoryError(
            f"Il ritmo produttivo non puo' essere negativo (ricevuto: {rate:.1f})."
        )

    # Si antepone C(0)=0: la giacenza di partenza e' un punto ammissibile.
    cumulative = np.concatenate(([0.0], np.cumsum(values - rate)))
    return float(max(cumulative.max() - cumulative.min(), 0.0))


# ---------------------------------------------------------------------------
# 4) Scorta pipeline
# ---------------------------------------------------------------------------


def pipeline_stock(
    average_demand: float,
    lead_time_months: float,
) -> float:
    """Scorta pipeline (in transito).

    **Modello adottato** - legge di Little applicata al flusso logistico: la
    merce mediamente "in viaggio" e' pari al flusso per il tempo di attesa::

        Scorta pipeline = D * L

    dove ``D`` e' la domanda media mensile prevista (approssimazione del
    flusso di rifornimento a regime) e ``L`` il lead time in mesi.

    Il valore cresce **linearmente** con il lead time: raddoppiando ``L``
    raddoppia il capitale immobilizzato in transito. E' la componente che
    risponde in modo piu' diretto alla leva "lead time" della dashboard.

    Si noti che questa scorta e' di proprieta' dell'impresa ma non e'
    disponibile per la vendita immediata: incide sul capitale circolante
    senza contribuire al livello di servizio nel breve periodo.
    """
    if average_demand < 0:
        raise InventoryError(
            f"La domanda media non puo' essere negativa (ricevuto: {average_demand:.1f})."
        )
    if lead_time_months < 0:
        raise InventoryError(
            f"Il lead time non puo' essere negativo (ricevuto: {lead_time_months})."
        )
    return float(average_demand * lead_time_months)


# ---------------------------------------------------------------------------
# Piano di scorta complessivo
# ---------------------------------------------------------------------------


@dataclass
class InventoryPlan:
    """Piano di scorta completo di un prodotto, con le quattro componenti."""

    product: str
    cycle_stock: float
    safety_stock: float
    anticipation_stock: float
    pipeline_stock: float
    # Parametri di input conservati per tracciabilita' e commento dinamico.
    average_demand: float = 0.0
    sigma_monthly: float = 0.0
    lead_time_months: float = 0.0
    review_period_months: float = 0.0
    service_level: float = 0.0
    z_factor: float = 0.0
    protection_interval_months: float = 0.0
    horizon_months: int = 0
    assumptions: Dict[str, str] = field(default_factory=dict)

    @property
    def total_stock(self) -> float:
        """Scorta totale rilevante: somma delle quattro componenti."""
        return (
            self.cycle_stock
            + self.safety_stock
            + self.anticipation_stock
            + self.pipeline_stock
        )

    @property
    def components(self) -> Dict[str, float]:
        """Componenti in ordine espositivo, con chiavi tecniche."""
        return {
            "cycle_stock": self.cycle_stock,
            "safety_stock": self.safety_stock,
            "anticipation_stock": self.anticipation_stock,
            "pipeline_stock": self.pipeline_stock,
        }

    @property
    def components_it(self) -> Dict[str, float]:
        """Componenti con etichette italiane, pronte per grafici e tabelle."""
        return {STOCK_LABELS_IT[k]: v for k, v in self.components.items()}

    @property
    def composition_pct(self) -> Dict[str, float]:
        """Peso percentuale di ciascuna componente sulla scorta totale."""
        total = self.total_stock
        if total <= 0:
            return {k: 0.0 for k in self.components}
        return {k: v / total * 100.0 for k, v in self.components.items()}

    @property
    def coverage_months(self) -> float:
        """Copertura della scorta totale, espressa in mesi di domanda."""
        if self.average_demand <= 0:
            return 0.0
        return self.total_stock / self.average_demand

    def to_dict(self) -> Dict[str, float]:
        """Rappresentazione piatta, usata per le tabelle di confronto."""
        return {
            "Domanda media prevista": self.average_demand,
            "Scorta ciclica": self.cycle_stock,
            "Scorta di sicurezza": self.safety_stock,
            "Scorta anticipata": self.anticipation_stock,
            "Scorta pipeline": self.pipeline_stock,
            "Scorta totale": self.total_stock,
            "Copertura (mesi)": self.coverage_months,
        }


def compute_inventory_plan(
    product: str,
    forecast: Sequence[float],
    sigma_monthly: float,
    lead_time_months: float,
    service_level: float,
    review_period_months: float,
    include_review_in_protection: bool = False,
    production_rate: Optional[float] = None,
) -> InventoryPlan:
    """Calcola il piano di scorta completo a partire dalla previsione.

    La domanda media mensile ``D`` e' la media della previsione sull'orizzonte
    selezionato: le scorte sono quindi dimensionate sulla domanda **attesa
    futura**, non sulla media storica.

    Parameters
    ----------
    product:
        Nome del prodotto.
    forecast:
        Domanda prevista mese per mese sull'orizzonte scelto.
    sigma_monthly:
        Deviazione standard mensile dell'errore previsionale.
    lead_time_months:
        Lead time di approvvigionamento ``L``.
    service_level:
        Livello di servizio obiettivo (es. 0.95).
    review_period_months:
        Periodo di riesame/riordino ``R``.
    include_review_in_protection:
        Se ``True`` l'intervallo di protezione della scorta di sicurezza e'
        ``L + R`` invece del solo ``L``.
    production_rate:
        Ritmo produttivo livellato per la scorta anticipata.
    """
    values = np.asarray(forecast, dtype=float).ravel()
    if values.size == 0:
        raise InventoryError(
            f"Impossibile pianificare le scorte per '{product}': "
            "la previsione e' vuota."
        )

    average_demand = float(np.mean(values))
    review_for_ss = review_period_months if include_review_in_protection else 0.0

    plan = InventoryPlan(
        product=product,
        cycle_stock=cycle_stock(average_demand, review_period_months),
        safety_stock=safety_stock(
            sigma_monthly=sigma_monthly,
            lead_time_months=lead_time_months,
            service_level=service_level,
            review_period_months=review_for_ss,
        ),
        anticipation_stock=anticipation_stock(values, production_rate=production_rate),
        pipeline_stock=pipeline_stock(average_demand, lead_time_months),
        average_demand=average_demand,
        sigma_monthly=float(sigma_monthly),
        lead_time_months=float(lead_time_months),
        review_period_months=float(review_period_months),
        service_level=float(service_level),
        z_factor=service_level_to_z(service_level),
        protection_interval_months=float(lead_time_months + review_for_ss),
        horizon_months=int(values.size),
        assumptions={
            "scorta_ciclica": "Q = D x R, giacenza media Q/2 (prelievo uniforme).",
            "scorta_sicurezza": (
                "z x sigma x sqrt(intervallo di protezione); sigma stimata "
                "dall'RMSE out-of-sample; errori i.i.d. e lead time "
                "deterministico."
            ),
            "scorta_anticipata": (
                "Livellamento della produzione: max-min dell'eccedenza "
                "cumulata rispetto al ritmo produttivo medio."
            ),
            "scorta_pipeline": "D x L (legge di Little).",
        },
    )
    return plan
