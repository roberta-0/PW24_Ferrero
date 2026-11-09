"""
Dashboard Streamlit - Project Work 24.

Previsione della domanda e pianificazione delle scorte: simulazione
applicativa su quattro prodotti Ferrero con dati sintetici.

Avvio::

    streamlit run app.py

Il file contiene **esclusivamente** logica di presentazione: ogni calcolo e'
delegato ai moduli del package :mod:`src`, in modo che la logica
previsionale e di gestione scorte resti indipendente dall'interfaccia e
verificabile con i test automatici.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

import pandas as pd
import streamlit as st

from src.charts import (
    chart_baseline_vs_scenario,
    chart_demand_and_forecast,
    chart_inventory_composition,
    chart_inventory_share,
    chart_method_accuracy,
    chart_products_overview,
    chart_scenario_comparison,
    chart_seasonal_profile,
)
from src.config import (
    DEFAULT_ALPHA,
    DEFAULT_FORECAST_HORIZON,
    DEFAULT_LEAD_TIME_MONTHS,
    DEFAULT_MA_WINDOW,
    DEFAULT_REVIEW_PERIOD_MONTHS,
    DEFAULT_SERVICE_LEVEL,
    DEFAULT_TEST_SIZE,
    FORECAST_HORIZON_OPTIONS,
    MA_WINDOW_OPTIONS,
    PRODUCTS,
    PRODUCT_NAMES,
    SERVICE_LEVEL_OPTIONS,
    SYNTHETIC_DATA_DISCLAIMER,
)
from src.data_generator import regenerate_all
from src.data_validation import DataValidationError, load_demand_history
from src.evaluation import evaluate_all_products
from src.forecasting import METHOD_DESCRIPTIONS, METHOD_NAMES
from src.narrative import (
    describe_demand_profile,
    describe_inventory_mix,
    describe_method_choice,
    describe_scenario_comparison,
    describe_scenario_effects,
)
from src.scenarios import (
    PRESET_SCENARIOS,
    ScenarioConfig,
    ScenarioError,
    ScenarioOutcome,
    compare_scenarios,
    simulate_scenario,
)
from src.utils import describe_series, format_months, format_number, format_percent

AUTO_METHOD_LABEL = "Selezione automatica (MAPE minimo)"

st.set_page_config(
    page_title="PW24 - Previsione domanda e scorte | Ferrero",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Stile
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; padding-bottom: 3rem; }
      div[data-testid="stMetric"] {
          background-color: #f7f9fc;
          border: 1px solid #e3e8ef;
          border-left: 4px solid #1f4e79;
          border-radius: 6px;
          padding: 12px 14px;
      }
      div[data-testid="stMetricLabel"] p { font-size: 0.80rem; color: #4a5568; }
      div[data-testid="stMetricValue"] { font-size: 1.45rem; color: #1f2937; }
      h2 { border-bottom: 2px solid #e3e8ef; padding-bottom: 0.3rem;
           margin-top: 1.6rem; }
      .pw24-header {
          background: linear-gradient(90deg, #1f4e79 0%, #2d6ca3 100%);
          color: #ffffff; padding: 1.3rem 1.6rem; border-radius: 8px;
          margin-bottom: 1.2rem;
      }
      .pw24-header h1 { color: #ffffff; margin: 0; font-size: 1.75rem; }
      .pw24-header p  { color: #d6e4f0; margin: 0.35rem 0 0 0; font-size: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Caricamento dati e calcoli (con cache)
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def carica_dataset() -> pd.DataFrame:
    """Carica e valida il dataset storico; la cache evita riletture inutili."""
    return load_demand_history()


@st.cache_data(show_spinner=False)
def calcola_scenario(config: ScenarioConfig) -> ScenarioOutcome:
    """Esegue la simulazione di uno scenario (cache per configurazione)."""
    return simulate_scenario(config)


@st.cache_data(show_spinner=False)
def valuta_tutti_i_prodotti(
    data: pd.DataFrame, test_size: int, ma_window: int, alpha: float
) -> tuple[pd.DataFrame, dict]:
    """Valuta tutti i metodi su tutti i prodotti del dataset storico."""
    return evaluate_all_products(
        data,
        test_size=test_size,
        method_params={"window": ma_window, "alpha": alpha},
    )


def mostra_errore(titolo: str, messaggio: str) -> None:
    """Mostra un errore in italiano senza esporre il traceback Python."""
    st.error(f"**{titolo}**\n\n{messaggio}")


# ---------------------------------------------------------------------------
# Sidebar - Configurazione
# ---------------------------------------------------------------------------


def costruisci_sidebar() -> ScenarioConfig:
    """Costruisce i controlli di configurazione e restituisce lo scenario."""
    st.sidebar.title("⚙️ Configurazione")
    st.sidebar.caption(
        "Le leve agiscono sul processo generatore della domanda: modificano "
        "serie simulata, previsioni e fabbisogno di scorta."
    )

    # --- Prodotto ----------------------------------------------------------
    st.sidebar.subheader("Prodotto")
    prodotto = st.sidebar.selectbox(
        "Articolo analizzato",
        PRODUCT_NAMES,
        index=0,
        help="Quattro prodotti Ferrero con profili di domanda volutamente diversi.",
    )
    st.sidebar.caption(f"_{PRODUCTS[prodotto].description}_")

    # --- Previsione --------------------------------------------------------
    st.sidebar.subheader("Previsione")
    metodo_scelto = st.sidebar.selectbox(
        "Metodo previsivo",
        [AUTO_METHOD_LABEL, *METHOD_NAMES],
        index=0,
        help=(
            "Con la selezione automatica il metodo e' scelto confrontando il "
            "MAPE out-of-sample di tutti i metodi disponibili."
        ),
    )
    if metodo_scelto != AUTO_METHOD_LABEL:
        st.sidebar.caption(f"_{METHOD_DESCRIPTIONS.get(metodo_scelto, '')}_")

    orizzonte = st.sidebar.select_slider(
        "Orizzonte di previsione (mesi)",
        options=FORECAST_HORIZON_OPTIONS,
        value=DEFAULT_FORECAST_HORIZON,
    )
    finestra_mm = st.sidebar.select_slider(
        "Finestra media mobile (mesi)",
        options=MA_WINDOW_OPTIONS,
        value=DEFAULT_MA_WINDOW,
        help="Usata dal metodo 'Media mobile'.",
    )
    alpha = st.sidebar.slider(
        "Alpha - smorzamento esponenziale",
        min_value=0.05,
        max_value=1.00,
        value=DEFAULT_ALPHA,
        step=0.05,
        help=(
            "Peso attribuito all'osservazione piu' recente. Valori alti = "
            "modello reattivo; valori bassi = previsione piu' liscia."
        ),
    )

    # --- Caratteristiche della domanda ------------------------------------
    st.sidebar.subheader("Caratteristiche della domanda")
    variabilita = st.sidebar.slider(
        "Variabilita' della domanda (moltiplicatore)",
        min_value=0.0,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help=(
            "Riscala la componente casuale e i picchi promozionali. "
            "1,0 = dataset storico di base."
        ),
    )
    trend = st.sidebar.slider(
        "Trend (moltiplicatore)",
        min_value=-2.0,
        max_value=4.0,
        value=1.0,
        step=0.25,
        help=(
            "Riscala il tasso di crescita. 0,0 = nessun trend; valori negativi "
            "invertono la direzione (domanda in calo)."
        ),
    )
    stagionalita = st.sidebar.slider(
        "Stagionalita' (moltiplicatore)",
        min_value=0.0,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help=(
            "Riscala ampiezza sinusoidale e picchi festivi. 0,0 = domanda "
            "destagionalizzata."
        ),
    )

    # --- Parametri logistici ----------------------------------------------
    st.sidebar.subheader("Parametri logistici")
    lead_time = st.sidebar.slider(
        "Lead time di approvvigionamento (mesi)",
        min_value=0.5,
        max_value=8.0,
        value=DEFAULT_LEAD_TIME_MONTHS,
        step=0.5,
        help="Tempo fra emissione dell'ordine e disponibilita' a magazzino.",
    )
    livello_servizio = st.sidebar.select_slider(
        "Livello di servizio",
        options=SERVICE_LEVEL_OPTIONS,
        value=DEFAULT_SERVICE_LEVEL,
        format_func=lambda v: f"{v:.1%}",
        help="Probabilita' di non andare in rottura di stock in un ciclo.",
    )
    periodo_riesame = st.sidebar.slider(
        "Periodo di riesame / riordino (mesi)",
        min_value=0.5,
        max_value=6.0,
        value=DEFAULT_REVIEW_PERIOD_MONTHS,
        step=0.5,
        help="Intervallo fra due emissioni d'ordine; determina la scorta ciclica.",
    )

    # --- Opzioni avanzate --------------------------------------------------
    with st.sidebar.expander("Opzioni avanzate"):
        test_size = st.slider(
            "Mesi riservati al test (validazione)",
            min_value=6,
            max_value=18,
            value=DEFAULT_TEST_SIZE,
            step=1,
            help=(
                "Split cronologico: i modelli sono stimati sui mesi precedenti "
                "e valutati su questi ultimi mesi."
            ),
        )
        include_riesame = st.checkbox(
            "Intervallo di protezione = lead time + periodo di riesame",
            value=False,
            help=(
                "Se disattivo la scorta di sicurezza copre il solo lead time "
                "(formulazione base PW24)."
            ),
        )
        st.divider()
        if st.button("🔄 Rigenera dataset sintetico", width="stretch"):
            try:
                regenerate_all(verbose=False)
                st.cache_data.clear()
                st.success("Dataset rigenerato con il seed di progetto.")
                st.rerun()
            except OSError as exc:
                st.error(f"Impossibile scrivere i file del dataset: {exc}")

    st.sidebar.divider()
    st.sidebar.caption(
        "⚠️ **Dati sintetici.** Prodotti e impresa sono reali, i valori "
        "numerici sono generati algoritmicamente a fini didattici."
    )

    return ScenarioConfig(
        name="Scenario corrente",
        product=prodotto,
        variability_multiplier=variabilita,
        trend_multiplier=trend,
        seasonality_multiplier=stagionalita,
        lead_time_months=lead_time,
        service_level=livello_servizio,
        review_period_months=periodo_riesame,
        forecast_horizon=int(orizzonte),
        method=None if metodo_scelto == AUTO_METHOD_LABEL else metodo_scelto,
        ma_window=int(finestra_mm),
        alpha=float(alpha),
        test_size=int(test_size),
        include_review_in_protection=include_riesame,
    )


# ---------------------------------------------------------------------------
# Sezioni della pagina principale
# ---------------------------------------------------------------------------


def sezione_intestazione() -> None:
    """Intestazione con titolo, sottotitolo e disclaimer."""
    st.markdown(
        """
        <div class="pw24-header">
          <h1>Dashboard per la previsione della domanda e la pianificazione
          delle scorte</h1>
          <p>Project Work 24 &mdash; Simulazione applicativa per Ferrero |
          Corso di Studi in Informatica per le Aziende Digitali (L-31)</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "**Avvertenza sui dati.** " + SYNTHETIC_DATA_DISCLAIMER.replace("**", "")
    )


def sezione_scenario(outcome: ScenarioOutcome, dataset: pd.DataFrame) -> None:
    """SEZIONE 1 - Parametri dello scenario corrente."""
    st.header("1 · Scenario di analisi")
    config = outcome.config

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prodotto", config.product)
    col2.metric("Metodo previsivo", outcome.used_method)
    col3.metric("Orizzonte", format_months(config.forecast_horizon))
    col4.metric("Lead time", format_months(config.lead_time_months))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Livello di servizio", f"{config.service_level:.1%}")
    col6.metric("Variabilita'", f"× {config.variability_multiplier:.2f}")
    col7.metric("Trend", f"× {config.trend_multiplier:.2f}")
    col8.metric("Stagionalita'", f"× {config.seasonality_multiplier:.2f}")

    scheda = PRODUCTS[config.product]
    st.markdown(
        f"**{scheda.name}** — _{scheda.category}_. {scheda.description} "
        f"Unita' di misura della domanda: {scheda.unit}."
    )

    if config.is_baseline:
        st.info(
            "Le tre leve di domanda sono al valore neutro: la serie simulata "
            "coincide esattamente con il dataset storico di base."
        )
    else:
        st.info(
            "Le leve di domanda sono state modificate: la serie analizzata e' "
            "**rigenerata** con i parametri di scenario, mantenendo lo stesso "
            "seed casuale. Il dataset storico su disco resta invariato."
        )

    with st.expander("Serie storica di base, profilo stagionale e statistiche"):
        tab1, tab2, tab3 = st.tabs(
            ["Confronto base/scenario", "Profilo stagionale", "Statistiche descrittive"]
        )
        with tab1:
            st.plotly_chart(
                chart_baseline_vs_scenario(
                    outcome.baseline_series,
                    outcome.scenario_series,
                    config.product,
                ),
                width="stretch",
            )
        with tab2:
            st.plotly_chart(
                chart_seasonal_profile(outcome.scenario_series, config.product),
                width="stretch",
            )
        with tab3:
            colA, colB = st.columns([1, 1])
            with colA:
                st.markdown("**Serie di scenario**")
                st.dataframe(
                    describe_series(outcome.scenario_series).style.format(
                        {"Valore": "{:,.1f}"}
                    ),
                    hide_index=True,
                    width="stretch",
                )
            with colB:
                st.markdown("**Tutti i prodotti (dataset di base)**")
                st.plotly_chart(
                    chart_products_overview(dataset, PRODUCT_NAMES),
                    width="stretch",
                )

    st.markdown(describe_demand_profile(outcome))


def sezione_domanda_e_previsione(outcome: ScenarioOutcome) -> None:
    """SEZIONE 2 - Domanda storica e prevista."""
    st.header("2 · Domanda storica e prevista")
    bundle = outcome.bundle

    st.plotly_chart(
        chart_demand_and_forecast(bundle, unit=PRODUCTS[outcome.config.product].unit.split("/")[0]),
        width="stretch",
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Addestramento",
        f"{len(bundle.train)} mesi",
        help="Periodo usato per stimare i modelli.",
    )
    col2.metric(
        "Test (out-of-sample)",
        f"{len(bundle.test)} mesi",
        help="Periodo usato per misurare l'accuratezza.",
    )
    col3.metric(
        "RMSE out-of-sample",
        format_number(bundle.rmse_out_of_sample, 0) + " cartoni",
        help="Errore quadratico medio sul periodo di test.",
    )

    st.caption(
        f"**Banda di incertezza.** L'area ombreggiata rappresenta "
        f"± z × RMSE out-of-sample al livello del "
        f"{bundle.confidence_level:.0%} (± "
        f"{format_number((bundle.upper - bundle.forecast).iloc[0], 0)} cartoni). "
        "Si tratta di una **stima empirica basata sul modello**, non di un "
        "intervallo di previsione derivato analiticamente: assume errori "
        "indipendenti, a media nulla, normalmente distribuiti e con varianza "
        "costante lungo l'orizzonte."
    )

    with st.expander("Tabella della previsione futura"):
        tabella = pd.DataFrame(
            {
                "Mese": bundle.future_index.strftime("%Y-%m"),
                "Previsione (cartoni)": bundle.forecast.to_numpy(),
                "Limite inferiore": bundle.lower.to_numpy(),
                "Limite superiore": bundle.upper.to_numpy(),
            }
        )
        st.dataframe(
            tabella.style.format(
                {
                    "Previsione (cartoni)": "{:,.0f}",
                    "Limite inferiore": "{:,.0f}",
                    "Limite superiore": "{:,.0f}",
                }
            ),
            hide_index=True,
            width="stretch",
        )


def sezione_confronto_metodi(outcome: ScenarioOutcome) -> None:
    """SEZIONE 3 - Confronto dei metodi previsionali."""
    st.header("3 · Confronto dei metodi previsionali")
    st.markdown(
        "Tutti i metodi sono stimati **solo** sul periodo di addestramento e "
        "valutati sui mesi di test mai visti dal modello. Il criterio di "
        "selezione primario e' il **MAPE minimo**; MAE e RMSE sono riportati "
        "come indicatori di supporto."
    )

    comparison = outcome.comparison
    colonne = ["Metodo", "MAE", "RMSE", "MAPE", "Bias", "Migliore"]
    tabella = comparison[colonne].sort_values("MAPE", na_position="last")

    col1, col2 = st.columns([1.15, 1])
    with col1:
        st.dataframe(
            tabella.style.format(
                {
                    "MAE": "{:,.1f}",
                    "RMSE": "{:,.1f}",
                    "MAPE": "{:,.2f}",
                    "Bias": "{:,.1f}",
                }
            ).apply(
                lambda row: [
                    "background-color: #e8f5e9; font-weight: 600"
                    if row["Migliore"]
                    else ""
                    for _ in row
                ],
                axis=1,
            ),
            hide_index=True,
            width="stretch",
            column_config={
                "MAE": st.column_config.NumberColumn("MAE (cartoni)"),
                "RMSE": st.column_config.NumberColumn("RMSE (cartoni)"),
                "MAPE": st.column_config.NumberColumn("MAPE (%)"),
                "Bias": st.column_config.NumberColumn("Bias (cartoni)"),
                "Migliore": st.column_config.CheckboxColumn("Migliore"),
            },
        )
        metrica = st.radio(
            "Metrica rappresentata nel grafico",
            ["MAPE", "MAE", "RMSE"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with col2:
        st.plotly_chart(
            chart_method_accuracy(comparison, metric=metrica, best_method=outcome.best_method),
            width="stretch",
        )

    note = comparison[comparison["Nota"] != ""]
    if not note.empty:
        for _, riga in note.iterrows():
            st.caption(f"ℹ️ **{riga['Metodo']}** — {riga['Nota']}")

    st.markdown(describe_method_choice(outcome))


def sezione_composizione_scorte(outcome: ScenarioOutcome) -> None:
    """SEZIONE 4 - Composizione delle scorte."""
    st.header("4 · Composizione delle scorte")
    plan = outcome.plan

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.plotly_chart(chart_inventory_composition(plan), width="stretch")
    with col2:
        st.plotly_chart(chart_inventory_share(plan), width="stretch")

    pct = plan.composition_pct
    tabella = pd.DataFrame(
        {
            "Componente": [
                "Scorta ciclica",
                "Scorta di sicurezza",
                "Scorta anticipata",
                "Scorta pipeline",
                "SCORTA TOTALE",
            ],
            "Quantita' (cartoni)": [
                plan.cycle_stock,
                plan.safety_stock,
                plan.anticipation_stock,
                plan.pipeline_stock,
                plan.total_stock,
            ],
            "Quota sul totale (%)": [
                pct["cycle_stock"],
                pct["safety_stock"],
                pct["anticipation_stock"],
                pct["pipeline_stock"],
                100.0,
            ],
            "Formula adottata": [
                f"D × R / 2 = {plan.average_demand:,.0f} × "
                f"{plan.review_period_months:g} / 2",
                f"z × σ × √(IP) = {plan.z_factor:.3f} × "
                f"{plan.sigma_monthly:,.0f} × √{plan.protection_interval_months:g}",
                "max − min dell'eccedenza cumulata (produzione livellata)",
                f"D × L = {plan.average_demand:,.0f} × {plan.lead_time_months:g}",
            ]
            + ["somma delle quattro componenti"],
        }
    )
    st.dataframe(
        tabella.style.format(
            {"Quantita' (cartoni)": "{:,.0f}", "Quota sul totale (%)": "{:,.1f}"}
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "IP = intervallo di protezione; D = domanda media mensile prevista; "
        "R = periodo di riesame; L = lead time; σ = deviazione standard "
        "dell'errore previsionale out-of-sample."
    )

    st.markdown(describe_inventory_mix(outcome))


def sezione_kpi(outcome: ScenarioOutcome) -> None:
    """SEZIONE 5 - Indicatori sintetici (KPI)."""
    st.header("5 · Indicatori sintetici (KPI)")
    plan = outcome.plan
    storica = float(outcome.scenario_series.mean())
    delta_domanda = (
        (plan.average_demand - storica) / storica * 100.0 if storica else 0.0
    )

    riga1 = st.columns(4)
    riga1[0].metric(
        "Domanda media storica",
        format_number(storica, 0),
        help="Media della serie di scenario sui 48 mesi simulati (cartoni/mese).",
    )
    riga1[1].metric(
        "Domanda media prevista",
        format_number(plan.average_demand, 0),
        delta=format_percent(delta_domanda, 1, with_sign=True),
        help="Media della previsione sull'orizzonte selezionato (cartoni/mese).",
    )
    riga1[2].metric("Lead time", format_months(plan.lead_time_months))
    riga1[3].metric(
        "Livello di servizio",
        f"{plan.service_level:.1%}",
        help=f"Fattore di sicurezza z = {plan.z_factor:.3f}",
    )

    riga2 = st.columns(4)
    riga2[0].metric(
        "Scorta ciclica",
        format_number(plan.cycle_stock, 0),
        delta=format_percent(plan.composition_pct["cycle_stock"]) + " del totale",
        delta_color="off",
    )
    riga2[1].metric(
        "Scorta di sicurezza",
        format_number(plan.safety_stock, 0),
        delta=format_percent(plan.composition_pct["safety_stock"]) + " del totale",
        delta_color="off",
    )
    riga2[2].metric(
        "Scorta anticipata",
        format_number(plan.anticipation_stock, 0),
        delta=format_percent(plan.composition_pct["anticipation_stock"]) + " del totale",
        delta_color="off",
    )
    riga2[3].metric(
        "Scorta pipeline",
        format_number(plan.pipeline_stock, 0),
        delta=format_percent(plan.composition_pct["pipeline_stock"]) + " del totale",
        delta_color="off",
    )

    riga3 = st.columns(4)
    riga3[0].metric(
        "Scorta totale",
        format_number(plan.total_stock, 0),
        help="Somma delle quattro componenti (cartoni).",
    )
    riga3[1].metric(
        "Copertura",
        format_months(round(plan.coverage_months, 1)),
        help="Mesi di domanda media prevista coperti dalla scorta totale.",
    )
    riga3[2].metric(
        "MAPE del metodo scelto",
        format_percent(
            float(
                outcome.comparison.loc[
                    outcome.comparison["Metodo"] == outcome.used_method, "MAPE"
                ].iloc[0]
            ),
            2,
        ),
    )
    riga3[3].metric(
        "σ errore previsionale",
        format_number(plan.sigma_monthly, 0),
        help="RMSE out-of-sample, usato per dimensionare la scorta di sicurezza.",
    )


def sezione_analisi(outcome: ScenarioOutcome, riferimento: Optional[ScenarioOutcome]) -> None:
    """SEZIONE 6 - Analisi gestionale dello scenario."""
    st.header("6 · Analisi dello scenario e implicazioni gestionali")
    st.markdown(describe_scenario_effects(outcome, reference=riferimento))


def sezione_confronto_scenari(base_config: ScenarioConfig) -> None:
    """SEZIONE 7 - Confronto fra due scenari configurabili."""
    st.header("7 · Confronto fra scenari")
    st.markdown(
        "Due configurazioni alternative sulla stessa serie prodotto, valutate "
        "in parallelo. Il confronto evidenzia come le leve di domanda e i "
        "parametri logistici si traducano in fabbisogni di scorta diversi."
    )

    nomi_preset = list(PRESET_SCENARIOS)
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🅐 Scenario A")
        preset_a = st.selectbox(
            "Configurazione predefinita", nomi_preset, index=1, key="preset_a"
        )
        valori_a = PRESET_SCENARIOS[preset_a]
        with st.expander("Personalizza Scenario A"):
            var_a = st.slider(
                "Variabilita'", 0.0, 3.0, float(valori_a["variability_multiplier"]), 0.1, key="var_a"
            )
            tre_a = st.slider(
                "Trend", -2.0, 4.0, float(valori_a["trend_multiplier"]), 0.25, key="tre_a"
            )
            sta_a = st.slider(
                "Stagionalita'", 0.0, 3.0, float(valori_a["seasonality_multiplier"]), 0.1, key="sta_a"
            )
            lt_a = st.slider(
                "Lead time (mesi)", 0.5, 8.0, float(valori_a["lead_time_months"]), 0.5, key="lt_a"
            )
            sl_a = st.select_slider(
                "Livello di servizio",
                options=SERVICE_LEVEL_OPTIONS,
                value=float(valori_a["service_level"]),
                format_func=lambda v: f"{v:.1%}",
                key="sl_a",
            )

    with col_b:
        st.subheader("🅑 Scenario B")
        preset_b = st.selectbox(
            "Configurazione predefinita", nomi_preset, index=2, key="preset_b"
        )
        valori_b = PRESET_SCENARIOS[preset_b]
        with st.expander("Personalizza Scenario B"):
            var_b = st.slider(
                "Variabilita'", 0.0, 3.0, float(valori_b["variability_multiplier"]), 0.1, key="var_b"
            )
            tre_b = st.slider(
                "Trend", -2.0, 4.0, float(valori_b["trend_multiplier"]), 0.25, key="tre_b"
            )
            sta_b = st.slider(
                "Stagionalita'", 0.0, 3.0, float(valori_b["seasonality_multiplier"]), 0.1, key="sta_b"
            )
            lt_b = st.slider(
                "Lead time (mesi)", 0.5, 8.0, float(valori_b["lead_time_months"]), 0.5, key="lt_b"
            )
            sl_b = st.select_slider(
                "Livello di servizio",
                options=SERVICE_LEVEL_OPTIONS,
                value=float(valori_b["service_level"]),
                format_func=lambda v: f"{v:.1%}",
                key="sl_b",
            )

    config_a = replace(
        base_config,
        name=preset_a,
        variability_multiplier=var_a,
        trend_multiplier=tre_a,
        seasonality_multiplier=sta_a,
        lead_time_months=lt_a,
        service_level=sl_a,
    )
    config_b = replace(
        base_config,
        name=preset_b,
        variability_multiplier=var_b,
        trend_multiplier=tre_b,
        seasonality_multiplier=sta_b,
        lead_time_months=lt_b,
        service_level=sl_b,
    )

    try:
        esito_a = calcola_scenario(config_a)
        esito_b = calcola_scenario(config_b)
    except ScenarioError as exc:
        mostra_errore("Configurazione di scenario non valida", str(exc))
        return

    nome_a, nome_b = config_a.name, config_b.name
    if nome_a == nome_b:
        nome_a, nome_b = f"{nome_a} (A)", f"{nome_b} (B)"

    confronto = compare_scenarios(esito_a, esito_b)

    def evidenzia_variazione(valore: float) -> str:
        """Colora la variazione percentuale: rosso = piu' scorta, verde = meno."""
        if pd.isna(valore):
            return ""
        if valore > 5:
            return "background-color: #fdecea; color: #a93226; font-weight: 600"
        if valore < -5:
            return "background-color: #eafaf1; color: #1e8449; font-weight: 600"
        return "color: #5d6d7e"

    st.dataframe(
        confronto.style.format(
            {
                nome_a: "{:,.0f}",
                nome_b: "{:,.0f}",
                "Variazione": "{:+,.0f}",
                "Variazione %": "{:+,.1f}%",
            }
        ).map(evidenzia_variazione, subset=["Variazione %"]),
        hide_index=True,
        width="stretch",
    )

    st.plotly_chart(
        chart_scenario_comparison(confronto, nome_a, nome_b), width="stretch"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{nome_a}** — metodo: {esito_a.used_method}")
        st.plotly_chart(
            chart_demand_and_forecast(esito_a.bundle, show_band=False),
            width="stretch",
        )
    with col2:
        st.markdown(f"**{nome_b}** — metodo: {esito_b.used_method}")
        st.plotly_chart(
            chart_demand_and_forecast(esito_b.bundle, show_band=False),
            width="stretch",
        )

    st.markdown(describe_scenario_comparison(esito_a, esito_b, confronto))


def sezione_panoramica(dataset: pd.DataFrame, config: ScenarioConfig) -> None:
    """SEZIONE 8 - Quadro di sintesi su tutti e quattro i prodotti."""
    st.header("8 · Quadro di sintesi sui quattro prodotti")
    st.markdown(
        "Valutazione dei metodi previsionali su **tutti** i prodotti del "
        "dataset storico di base: evidenzia come prodotti con profili di "
        "domanda diversi richiedano metodi previsionali diversi."
    )

    try:
        confronto, migliori = valuta_tutti_i_prodotti(
            dataset, config.test_size, config.ma_window, config.alpha
        )
    except Exception:
        mostra_errore(
            "Valutazione non completata",
            "Non e' stato possibile valutare tutti i prodotti con i parametri "
            "correnti. Ridurre il numero di mesi di test nelle opzioni avanzate.",
        )
        return

    sintesi = []
    for prodotto in PRODUCT_NAMES:
        righe = confronto[
            (confronto["Prodotto"] == prodotto)
            & (confronto["Metodo"] == migliori.get(prodotto))
        ]
        if righe.empty:
            continue
        riga = righe.iloc[0]
        serie = dataset[dataset["product"] == prodotto]["demand"]
        sintesi.append(
            {
                "Prodotto": prodotto,
                "Domanda media (cartoni/mese)": serie.mean(),
                "Coeff. variazione (%)": serie.std(ddof=1) / serie.mean() * 100.0,
                "Metodo migliore": riga["Metodo"],
                "MAE (cartoni)": riga["MAE"],
                "RMSE (cartoni)": riga["RMSE"],
                "MAPE (%)": riga["MAPE"],
            }
        )

    st.dataframe(
        pd.DataFrame(sintesi).style.format(
            {
                "Domanda media (cartoni/mese)": "{:,.0f}",
                "Coeff. variazione (%)": "{:,.1f}",
                "MAE (cartoni)": "{:,.1f}",
                "RMSE (cartoni)": "{:,.1f}",
                "MAPE (%)": "{:,.2f}",
            }
        ),
        hide_index=True,
        width="stretch",
    )

    with st.expander("Tabella completa prodotto × metodo"):
        st.dataframe(
            confronto[["Prodotto", "Metodo", "MAE", "RMSE", "MAPE", "Migliore"]]
            .style.format({"MAE": "{:,.1f}", "RMSE": "{:,.1f}", "MAPE": "{:,.2f}"}),
            hide_index=True,
            width="stretch",
        )


# ---------------------------------------------------------------------------
# Punto di ingresso
# ---------------------------------------------------------------------------


def main() -> None:
    """Orchestrazione della dashboard, con gestione degli errori in italiano."""
    sezione_intestazione()

    # --- caricamento e validazione del dataset ----------------------------
    try:
        dataset = carica_dataset()
    except DataValidationError as exc:
        mostra_errore(
            "Dataset non valido o non disponibile",
            exc.formatted()
            + "\n\nRigenerare il dataset eseguendo `python -m src.data_generator` "
            "dalla cartella del progetto.",
        )
        st.stop()
        return

    config = costruisci_sidebar()

    # --- simulazione dello scenario corrente ------------------------------
    try:
        outcome = calcola_scenario(config)
    except ScenarioError as exc:
        mostra_errore("Configurazione dello scenario non valida", str(exc))
        st.stop()
        return

    # Scenario di riferimento (leve neutre) usato per quantificare gli scarti.
    riferimento: Optional[ScenarioOutcome] = None
    if not config.is_baseline:
        try:
            riferimento = calcola_scenario(
                replace(
                    config,
                    name="Riferimento (leve neutre)",
                    variability_multiplier=1.0,
                    trend_multiplier=1.0,
                    seasonality_multiplier=1.0,
                )
            )
        except ScenarioError:
            riferimento = None

    sezione_scenario(outcome, dataset)
    sezione_domanda_e_previsione(outcome)
    sezione_confronto_metodi(outcome)
    sezione_composizione_scorte(outcome)
    sezione_kpi(outcome)
    sezione_analisi(outcome, riferimento)
    sezione_confronto_scenari(config)
    sezione_panoramica(dataset, config)

    st.divider()
    st.caption(
        "Project Work 24 — Corso di Studi in Informatica per le Aziende "
        "Digitali (L-31). Settori: INF/01, ING-INF/05, ING-IND/35. "
        "Dati di domanda sintetici generati a fini didattici: non "
        "rappresentano vendite reali Ferrero."
    )


if __name__ == "__main__":
    main()
