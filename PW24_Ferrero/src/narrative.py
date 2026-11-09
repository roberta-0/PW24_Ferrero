"""
Generazione dei commenti gestionali dinamici.

La specifica PW24 richiede che la dashboard interpreti le conseguenze
manageriali dello scenario analizzato. I testi prodotti da questo modulo
sono **costruiti sui valori effettivamente calcolati**: ogni frase cita
numeri provenienti dal piano di scorta e dalla valutazione previsionale, e
cambia al variare delle leve impostate dall'utente.

Il modulo non contiene logica di calcolo: riceve gli oggetti gia' calcolati
da :mod:`src.scenarios` e li traduce in testo italiano.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from .config import PRODUCTS
from .forecasting import METHOD_DESCRIPTIONS
from .inventory import InventoryPlan
from .scenarios import ScenarioOutcome
from .utils import format_months, format_number, format_percent

__all__ = [
    "describe_demand_profile",
    "describe_method_choice",
    "describe_inventory_mix",
    "describe_scenario_effects",
    "describe_scenario_comparison",
]


def _dominant_component(plan: InventoryPlan) -> tuple[str, float]:
    """Componente di scorta con il peso percentuale maggiore."""
    from .config import STOCK_LABELS_IT

    shares = plan.composition_pct
    key = max(shares, key=shares.get)
    return STOCK_LABELS_IT[key], shares[key]


def describe_demand_profile(outcome: ScenarioOutcome) -> str:
    """Commento sul profilo di domanda osservato nello scenario corrente."""
    config = outcome.config
    series = outcome.scenario_series
    cv = outcome.diagnostics["cv_storico_%"]

    monthly = series.groupby(series.index.month).mean()
    seasonal_index = monthly / monthly.mean() * 100.0
    peak_month = int(seasonal_index.idxmax())
    trough_month = int(seasonal_index.idxmin())
    from .config import MONTH_NAMES_IT

    if cv < 10:
        regularity = (
            "una serie **regolare**, prevedibile con modelli semplici e con "
            "un fabbisogno di scorta di sicurezza contenuto"
        )
    elif cv < 25:
        regularity = (
            "una serie a **variabilita' media**, che richiede un modello "
            "previsionale calibrato e una scorta di sicurezza apprezzabile"
        )
    else:
        regularity = (
            "una serie **fortemente variabile**, difficile da prevedere e "
            "che impone una copertura di sicurezza rilevante"
        )

    seasonal_range = seasonal_index.max() - seasonal_index.min()
    if seasonal_range < 20:
        seasonality_text = "La stagionalita' e' debole e incide poco sulla pianificazione."
    elif seasonal_range < 60:
        seasonality_text = (
            f"La stagionalita' e' moderata: il mese di punta "
            f"(**{MONTH_NAMES_IT[peak_month - 1]}**, indice "
            f"{seasonal_index.max():.0f}) supera il mese piu' debole "
            f"(**{MONTH_NAMES_IT[trough_month - 1]}**, indice "
            f"{seasonal_index.min():.0f})."
        )
    else:
        seasonality_text = (
            f"La stagionalita' e' **marcata**: a "
            f"**{MONTH_NAMES_IT[peak_month - 1]}** la domanda raggiunge un "
            f"indice di {seasonal_index.max():.0f} contro i "
            f"{seasonal_index.min():.0f} di "
            f"**{MONTH_NAMES_IT[trough_month - 1]}**, con un'escursione di "
            f"{seasonal_range:.0f} punti. Questo profilo giustifica il "
            "ricorso alla scorta anticipata e il livellamento della "
            "produzione nei mesi di bassa stagione."
        )

    lines = [
        f"Nello scenario corrente **{config.product}** presenta una domanda media "
        f"di **{format_number(series.mean(), 0)} cartoni/mese** con un "
        f"coefficiente di variazione del **{format_percent(cv)}**: si tratta di "
        f"{regularity}.",
        seasonality_text,
    ]

    delta = outcome.diagnostics["delta_vs_baseline_%"]
    if abs(delta) > 1.0:
        direction = "superiore" if delta > 0 else "inferiore"
        lines.append(
            f"Rispetto al dataset storico di base, la domanda media simulata e' "
            f"**{direction} del {format_percent(abs(delta))}**, effetto diretto "
            "delle leve di scenario impostate."
        )

    return "\n\n".join(lines)


def describe_method_choice(outcome: ScenarioOutcome) -> str:
    """Commento sulla selezione automatica del metodo previsionale."""
    comparison = outcome.comparison.dropna(subset=["MAPE"]).sort_values("MAPE")
    if comparison.empty:
        return (
            "Nessun metodo ha prodotto metriche valide su questo scenario: "
            "il criterio di selezione ripiega sull'RMSE."
        )

    best = comparison.iloc[0]
    worst = comparison.iloc[-1]
    used = outcome.used_method
    is_auto = outcome.config.method is None

    lines = [
        f"Il criterio di selezione (**MAPE out-of-sample minimo**) individua "
        f"**{best['Metodo']}** come metodo migliore per {outcome.config.product}, "
        f"con un MAPE del **{format_percent(best['MAPE'], 2)}** "
        f"(MAE {format_number(best['MAE'], 0)} cartoni, "
        f"RMSE {format_number(best['RMSE'], 0)} cartoni). "
        f"{METHOD_DESCRIPTIONS.get(best['Metodo'], '')}"
    ]

    if len(comparison) > 1:
        gap = worst["MAPE"] - best["MAPE"]
        lines.append(
            f"Il metodo meno accurato su questa serie e' **{worst['Metodo']}** "
            f"({format_percent(worst['MAPE'], 2)} di MAPE): lo scarto di "
            f"**{format_percent(gap, 2)}** fra il migliore e il peggiore mostra "
            "quanto la scelta del modello incida concretamente sulla qualita' "
            "della pianificazione."
        )

    if not is_auto and used != best["Metodo"]:
        used_row = outcome.comparison[outcome.comparison["Metodo"] == used]
        if not used_row.empty and pd.notna(used_row.iloc[0]["MAPE"]):
            penalty = used_row.iloc[0]["MAPE"] - best["MAPE"]
            lines.append(
                f"L'utente ha imposto manualmente il metodo **{used}**, che su "
                f"questa serie comporta un MAPE superiore di "
                f"**{format_percent(penalty, 2)}** rispetto alla scelta ottimale: "
                "la previsione mostrata e' quindi meno accurata di quella "
                "ottenibile con la selezione automatica."
            )
    elif is_auto:
        lines.append(
            "La previsione futura mostrata nella Sezione 2 e' generata con "
            "questo metodo, ri-stimato sull'intera serie storica disponibile."
        )

    return "\n\n".join(lines)


def describe_inventory_mix(outcome: ScenarioOutcome) -> str:
    """Commento sulla composizione della scorta totale."""
    plan = outcome.plan
    label, share = _dominant_component(plan)
    pct = plan.composition_pct

    reasons = {
        "Scorta pipeline": (
            f"il lead time di {format_months(plan.lead_time_months)} immobilizza "
            "una quantita' di merce proporzionale al tempo di transito"
        ),
        "Scorta anticipata": (
            "la forte concentrazione stagionale della domanda obbliga ad "
            "accumulare prodotto finito prima del picco"
        ),
        "Scorta di sicurezza": (
            f"l'elevata incertezza previsionale (deviazione standard "
            f"{format_number(plan.sigma_monthly, 0)} cartoni) combinata con un "
            f"livello di servizio del {plan.service_level:.1%} richiede un "
            "cuscinetto consistente"
        ),
        "Scorta ciclica": (
            f"il periodo di riesame di {format_months(plan.review_period_months)} "
            "determina lotti di riordino che generano giacenza media elevata"
        ),
    }

    lines = [
        f"La scorta totale rilevante ammonta a **{format_number(plan.total_stock, 0)} "
        f"cartoni**, pari a **{format_number(plan.coverage_months, 1)} mesi** di "
        f"copertura della domanda media prevista "
        f"({format_number(plan.average_demand, 0)} cartoni/mese).",
        f"La componente dominante e' la **{label.lower()}** "
        f"({format_percent(share)} del totale): {reasons.get(label, '')}.",
        "Ripartizione completa: "
        f"scorta ciclica {format_percent(pct['cycle_stock'])}, "
        f"scorta di sicurezza {format_percent(pct['safety_stock'])}, "
        f"scorta anticipata {format_percent(pct['anticipation_stock'])}, "
        f"scorta pipeline {format_percent(pct['pipeline_stock'])}.",
    ]
    return "\n\n".join(lines)


def describe_scenario_effects(
    outcome: ScenarioOutcome,
    reference: Optional[ScenarioOutcome] = None,
) -> str:
    """Analisi gestionale dello scenario, confrontato con la configurazione base.

    Se e' fornito uno scenario di riferimento, il testo quantifica gli
    scostamenti; in caso contrario commenta i valori assoluti.
    """
    plan = outcome.plan
    config = outcome.config
    lines: List[str] = []

    # --- effetto del lead time -------------------------------------------
    lines.append(
        f"**Lead time.** Con un lead time di {format_months(config.lead_time_months)} "
        f"la scorta pipeline vale **{format_number(plan.pipeline_stock, 0)} cartoni** "
        f"({format_percent(plan.composition_pct['pipeline_stock'])} del totale). "
        "Questa quantita' cresce in modo **lineare** con il lead time, mentre la "
        "scorta di sicurezza cresce con la **radice quadrata** dell'intervallo di "
        f"protezione ({format_months(plan.protection_interval_months)}): allungare "
        "l'approvvigionamento penalizza quindi soprattutto il capitale in transito."
    )

    # --- effetto della variabilita' / livello di servizio -----------------
    lines.append(
        f"**Variabilita' e livello di servizio.** La deviazione standard "
        f"dell'errore previsionale e' di {format_number(plan.sigma_monthly, 0)} "
        f"cartoni/mese; con un livello di servizio del {config.service_level:.1%} "
        f"(fattore z = {plan.z_factor:.3f}) la scorta di sicurezza si attesta a "
        f"**{format_number(plan.safety_stock, 0)} cartoni**. "
        "Poiche' il fattore z cresce in modo piu' che proporzionale avvicinandosi "
        "al 100%, ogni punto di servizio aggiuntivo oltre il 97,5% ha un costo "
        "marginale crescente."
    )

    # --- effetto della stagionalita' --------------------------------------
    if plan.anticipation_stock > 0.05 * plan.total_stock:
        lines.append(
            f"**Stagionalita'.** La scorta anticipata vale "
            f"**{format_number(plan.anticipation_stock, 0)} cartoni** "
            f"({format_percent(plan.composition_pct['anticipation_stock'])} del "
            "totale): e' la quantita' che l'impresa deve accumulare nei mesi di "
            "bassa stagione per servire il picco mantenendo la produzione "
            "livellata. In alternativa occorrerebbe flessibilita' di capacita' "
            "produttiva, con costi di straordinario e di personale stagionale."
        )
    else:
        lines.append(
            "**Stagionalita'.** Il profilo di domanda e' sufficientemente piatto "
            f"da rendere marginale la scorta anticipata "
            f"({format_number(plan.anticipation_stock, 0)} cartoni, "
            f"{format_percent(plan.composition_pct['anticipation_stock'])} del "
            "totale): la produzione puo' seguire la domanda senza accumuli "
            "preventivi significativi."
        )

    # --- effetto del trend -------------------------------------------------
    historical_mean = float(outcome.scenario_series.mean())
    growth = (
        (plan.average_demand - historical_mean) / historical_mean * 100.0
        if historical_mean
        else 0.0
    )
    if abs(growth) > 2.0:
        direction = "in crescita" if growth > 0 else "in calo"
        lines.append(
            f"**Trend.** La domanda media prevista sui prossimi "
            f"{config.forecast_horizon} mesi "
            f"({format_number(plan.average_demand, 0)} cartoni/mese) e' "
            f"{direction} del **{format_percent(abs(growth))}** rispetto alla media "
            "storica dello scenario. Tutte le componenti di scorta proporzionali "
            "alla domanda (ciclica e pipeline) si adeguano automaticamente a "
            "questo livello atteso."
        )

    # --- confronto con il riferimento -------------------------------------
    if reference is not None and reference is not outcome:
        ref = reference.plan
        if ref.total_stock > 0:
            delta_total = (plan.total_stock - ref.total_stock) / ref.total_stock * 100.0
            delta_ss = (
                (plan.safety_stock - ref.safety_stock) / ref.safety_stock * 100.0
                if ref.safety_stock
                else 0.0
            )
            delta_ps = (
                (plan.pipeline_stock - ref.pipeline_stock) / ref.pipeline_stock * 100.0
                if ref.pipeline_stock
                else 0.0
            )
            verdict = (
                "un maggiore capitale immobilizzato, compensato da un minore "
                "rischio di rottura di stock"
                if delta_total > 0
                else "un alleggerimento del capitale circolante, a fronte di una "
                "minore protezione contro la variabilita'"
            )
            lines.append(
                f"**Confronto con la configurazione di riferimento.** La scorta "
                f"totale passa da {format_number(ref.total_stock, 0)} a "
                f"{format_number(plan.total_stock, 0)} cartoni "
                f"(**{format_percent(delta_total, 1, with_sign=True)}**), con la "
                f"scorta di sicurezza a {format_percent(delta_ss, 1, with_sign=True)} "
                f"e la scorta pipeline a {format_percent(delta_ps, 1, with_sign=True)}. "
                f"Dal punto di vista gestionale cio' comporta {verdict}."
            )

    return "\n\n".join(lines)


def describe_scenario_comparison(
    outcome_a: ScenarioOutcome,
    outcome_b: ScenarioOutcome,
    comparison: pd.DataFrame,
) -> str:
    """Commento gestionale sul confronto fra due scenari."""
    plan_a, plan_b = outcome_a.plan, outcome_b.plan
    name_a, name_b = outcome_a.config.name, outcome_b.config.name

    total_row = comparison[comparison["Indicatore"].str.startswith("Scorta totale")]
    delta_total = float(total_row["Variazione %"].iloc[0]) if not total_row.empty else 0.0

    # Individua la componente che spiega la maggior parte dello scostamento.
    deltas = {
        "scorta ciclica": plan_b.cycle_stock - plan_a.cycle_stock,
        "scorta di sicurezza": plan_b.safety_stock - plan_a.safety_stock,
        "scorta anticipata": plan_b.anticipation_stock - plan_a.anticipation_stock,
        "scorta pipeline": plan_b.pipeline_stock - plan_a.pipeline_stock,
    }
    driver = max(deltas, key=lambda k: abs(deltas[k]))
    driver_delta = deltas[driver]
    total_delta = plan_b.total_stock - plan_a.total_stock
    driver_share = abs(driver_delta) / abs(total_delta) * 100.0 if total_delta else 0.0

    lines = [
        f"Passando da **{name_a}** a **{name_b}** la scorta totale varia del "
        f"**{format_percent(delta_total, 1, with_sign=True)}** "
        f"(da {format_number(plan_a.total_stock, 0)} a "
        f"{format_number(plan_b.total_stock, 0)} cartoni), con una copertura che "
        f"passa da {format_number(plan_a.coverage_months, 1)} a "
        f"{format_number(plan_b.coverage_months, 1)} mesi di domanda.",
        f"Il principale responsabile dello scostamento e' la **{driver}** "
        f"({'+' if driver_delta > 0 else ''}{format_number(driver_delta, 0)} "
        f"cartoni, pari al {format_percent(driver_share)} della variazione "
        "complessiva).",
    ]

    # Lettura delle leve che differiscono fra i due scenari.
    diffs: List[str] = []
    if abs(plan_a.lead_time_months - plan_b.lead_time_months) > 1e-9:
        diffs.append(
            f"il lead time passa da {format_months(plan_a.lead_time_months)} a "
            f"{format_months(plan_b.lead_time_months)}"
        )
    if abs(plan_a.service_level - plan_b.service_level) > 1e-9:
        diffs.append(
            f"il livello di servizio passa dal {plan_a.service_level:.1%} al "
            f"{plan_b.service_level:.1%} (z da {plan_a.z_factor:.3f} a "
            f"{plan_b.z_factor:.3f})"
        )
    if (
        abs(
            outcome_a.config.variability_multiplier
            - outcome_b.config.variability_multiplier
        )
        > 1e-9
    ):
        diffs.append(
            f"la variabilita' della domanda passa da "
            f"x{outcome_a.config.variability_multiplier:.2f} a "
            f"x{outcome_b.config.variability_multiplier:.2f}"
        )
    if (
        abs(
            outcome_a.config.seasonality_multiplier
            - outcome_b.config.seasonality_multiplier
        )
        > 1e-9
    ):
        diffs.append(
            f"l'ampiezza stagionale passa da "
            f"x{outcome_a.config.seasonality_multiplier:.2f} a "
            f"x{outcome_b.config.seasonality_multiplier:.2f}"
        )
    if abs(outcome_a.config.trend_multiplier - outcome_b.config.trend_multiplier) > 1e-9:
        diffs.append(
            f"il trend passa da x{outcome_a.config.trend_multiplier:.2f} a "
            f"x{outcome_b.config.trend_multiplier:.2f}"
        )

    if diffs:
        lines.append("Le leve modificate sono: " + "; ".join(diffs) + ".")

    if delta_total > 15:
        lines.append(
            "**Implicazione gestionale.** Lo scenario B richiede un investimento "
            "in capitale circolante sensibilmente superiore. La decisione non e' "
            "puramente tecnica: occorre confrontare il costo di mantenimento "
            "della scorta aggiuntiva con il costo atteso delle rotture di stock "
            "evitate (mancato margine, penali contrattuali verso la grande "
            "distribuzione, perdita di spazio a scaffale). Per un prodotto "
            "alimentare va inoltre considerato il rischio di obsolescenza legato "
            "alla shelf life."
        )
    elif delta_total < -15:
        lines.append(
            "**Implicazione gestionale.** Lo scenario B libera capitale "
            "circolante in misura significativa. Il beneficio finanziario va "
            "tuttavia bilanciato con la riduzione del margine di protezione: "
            "una filiera piu' snella e' piu' esposta a shock di domanda o di "
            "fornitura, e richiede un monitoraggio piu' frequente della "
            "previsione."
        )
    else:
        lines.append(
            "**Implicazione gestionale.** I due scenari comportano un fabbisogno "
            "di scorta complessivamente simile; cambia tuttavia la **composizione** "
            "del magazzino, e quindi la natura del rischio sopportato "
            "(immobilizzo in transito, cuscinetto contro l'incertezza, oppure "
            "accumulo stagionale)."
        )

    return "\n\n".join(lines)
