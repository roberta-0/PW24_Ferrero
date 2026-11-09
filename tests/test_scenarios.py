"""
Test della simulazione degli scenari.

Questi test sono i piu' importanti ai fini della specifica PW24: verificano
che le leve della dashboard **non siano cosmetiche**, ma producano gli effetti
attesi su domanda, previsioni e fabbisogno di scorta.

Effetti attesi (dalla specifica):

* variabilita' ↑  ->  incertezza previsionale ↑  e  scorta di sicurezza ↑
* lead time   ↑  ->  scorta pipeline ↑  e  scorta di sicurezza ↑
* stagionalita' ↑ ->  picchi piu' marcati  e  scorta anticipata modificata
* trend       ↑  ->  previsione futura ↑  e  fabbisogno di scorta ↑
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from src.scenarios import (
    PRESET_SCENARIOS,
    ScenarioConfig,
    ScenarioError,
    build_scenario_series,
    compare_scenarios,
    simulate_scenario,
)


@pytest.fixture(scope="module")
def config_base() -> ScenarioConfig:
    """Configurazione neutra su un prodotto fortemente stagionale."""
    return ScenarioConfig(name="Base", product="Ferrero Rocher")


@pytest.fixture(scope="module")
def esito_base(config_base: ScenarioConfig):
    return simulate_scenario(config_base)


# ---------------------------------------------------------------------------
# Neutralita' e separazione dei dati
# ---------------------------------------------------------------------------


def test_leve_neutre_riproducono_il_dataset_di_base(config_base) -> None:
    """Con moltiplicatori unitari la serie coincide con quella storica."""
    from src.data_generator import generate_product_series
    from src.config import PRODUCTS

    scenario = build_scenario_series(config_base)
    storica = generate_product_series(PRODUCTS["Ferrero Rocher"], product_index=2)
    pd.testing.assert_series_equal(scenario, storica)


def test_flag_baseline_coerente() -> None:
    assert ScenarioConfig().is_baseline
    assert not ScenarioConfig(variability_multiplier=2.0).is_baseline
    assert not ScenarioConfig(trend_multiplier=0.0).is_baseline
    assert not ScenarioConfig(seasonality_multiplier=1.5).is_baseline


def test_dataset_storico_non_viene_sovrascritto(tmp_path, monkeypatch) -> None:
    """La simulazione non deve toccare i file su disco."""
    from src.config import DEMAND_HISTORY_CSV

    prima = DEMAND_HISTORY_CSV.read_bytes() if DEMAND_HISTORY_CSV.exists() else None
    simulate_scenario(
        ScenarioConfig(product="Nutella", variability_multiplier=3.0)
    )
    dopo = DEMAND_HISTORY_CSV.read_bytes() if DEMAND_HISTORY_CSV.exists() else None
    assert prima == dopo


def test_esito_conserva_sia_base_sia_scenario() -> None:
    """La dashboard deve poter distinguere le due serie."""
    esito = simulate_scenario(
        ScenarioConfig(product="Nutella", variability_multiplier=2.5)
    )
    assert len(esito.baseline_series) == len(esito.scenario_series)
    assert not esito.baseline_series.equals(esito.scenario_series)


# ---------------------------------------------------------------------------
# Effetto della leva VARIABILITA'
# ---------------------------------------------------------------------------


def test_variabilita_aumenta_la_dispersione_della_domanda(config_base) -> None:
    bassa = build_scenario_series(replace(config_base, variability_multiplier=0.25))
    alta = build_scenario_series(replace(config_base, variability_multiplier=3.0))
    cv_bassa = bassa.std(ddof=1) / bassa.mean()
    cv_alta = alta.std(ddof=1) / alta.mean()
    assert cv_alta > cv_bassa


def test_variabilita_aumenta_la_scorta_di_sicurezza(config_base) -> None:
    """Requisito PW24 esplicito."""
    bassa = simulate_scenario(replace(config_base, variability_multiplier=0.25))
    alta = simulate_scenario(replace(config_base, variability_multiplier=3.0))
    assert alta.plan.safety_stock > bassa.plan.safety_stock


def test_variabilita_aumenta_lincertezza_previsionale(config_base) -> None:
    """Requisito PW24: piu' variabilita' -> banda di previsione piu' ampia."""
    bassa = simulate_scenario(replace(config_base, variability_multiplier=0.25))
    alta = simulate_scenario(replace(config_base, variability_multiplier=3.0))
    assert alta.bundle.rmse_out_of_sample > bassa.bundle.rmse_out_of_sample
    larghezza_bassa = (bassa.bundle.upper - bassa.bundle.lower).mean()
    larghezza_alta = (alta.bundle.upper - alta.bundle.lower).mean()
    assert larghezza_alta > larghezza_bassa


def test_variabilita_nulla_rende_la_serie_quasi_deterministica(config_base) -> None:
    """Azzerando il rumore resta solo la componente sistematica."""
    esito = simulate_scenario(replace(config_base, variability_multiplier=0.0))
    assert esito.plan.safety_stock < 0.35 * esito.plan.total_stock


# ---------------------------------------------------------------------------
# Effetto della leva LEAD TIME
# ---------------------------------------------------------------------------


def test_lead_time_aumenta_la_scorta_pipeline(config_base) -> None:
    """Requisito PW24 esplicito: deve crescere all'aumentare del lead time."""
    valori = [
        simulate_scenario(replace(config_base, lead_time_months=lt)).plan.pipeline_stock
        for lt in (1.0, 2.0, 4.0, 6.0)
    ]
    assert valori == sorted(valori)
    assert len(set(np.round(valori, 6))) == 4


def test_lead_time_aumenta_la_scorta_di_sicurezza(config_base) -> None:
    corto = simulate_scenario(replace(config_base, lead_time_months=1.0))
    lungo = simulate_scenario(replace(config_base, lead_time_months=6.0))
    assert lungo.plan.safety_stock > corto.plan.safety_stock


def test_lead_time_aumenta_la_scorta_totale(config_base) -> None:
    corto = simulate_scenario(replace(config_base, lead_time_months=2.0))
    lungo = simulate_scenario(replace(config_base, lead_time_months=5.0))
    assert lungo.plan.total_stock > corto.plan.total_stock


def test_lead_time_non_altera_la_serie_di_domanda(config_base) -> None:
    """Il lead time e' una leva logistica, non di domanda."""
    a = simulate_scenario(replace(config_base, lead_time_months=1.0))
    b = simulate_scenario(replace(config_base, lead_time_months=7.0))
    pd.testing.assert_series_equal(a.scenario_series, b.scenario_series)
    assert a.plan.cycle_stock == pytest.approx(b.plan.cycle_stock)


# ---------------------------------------------------------------------------
# Effetto della leva STAGIONALITA'
# ---------------------------------------------------------------------------


def test_stagionalita_accentua_i_picchi(config_base) -> None:
    debole = build_scenario_series(replace(config_base, seasonality_multiplier=0.0))
    forte = build_scenario_series(replace(config_base, seasonality_multiplier=2.5))

    def escursione(serie: pd.Series) -> float:
        medie = serie.groupby(serie.index.month).mean()
        indice = medie / medie.mean() * 100.0
        return float(indice.max() - indice.min())

    assert escursione(forte) > escursione(debole)


def test_stagionalita_aumenta_la_scorta_anticipata(config_base) -> None:
    """Requisito PW24: la scorta anticipata deve reagire alla stagionalita'."""
    debole = simulate_scenario(replace(config_base, seasonality_multiplier=0.25))
    forte = simulate_scenario(replace(config_base, seasonality_multiplier=2.5))
    assert forte.plan.anticipation_stock > debole.plan.anticipation_stock


def test_stagionalita_nulla_riduce_fortemente_la_scorta_anticipata(config_base) -> None:
    piatta = simulate_scenario(replace(config_base, seasonality_multiplier=0.0))
    normale = simulate_scenario(config_base)
    assert piatta.plan.anticipation_stock < normale.plan.anticipation_stock


# ---------------------------------------------------------------------------
# Effetto della leva TREND
# ---------------------------------------------------------------------------


def test_trend_aumenta_la_domanda_prevista() -> None:
    """Requisito PW24: un trend piu' forte alza la previsione futura."""
    base = ScenarioConfig(product="Kinder Happy Hippo", method="Regressione lineare")
    piatto = simulate_scenario(replace(base, trend_multiplier=0.0))
    crescente = simulate_scenario(replace(base, trend_multiplier=4.0))
    assert crescente.plan.average_demand > piatto.plan.average_demand


def test_trend_aumenta_il_fabbisogno_di_scorta() -> None:
    base = ScenarioConfig(product="Kinder Happy Hippo", method="Regressione lineare")
    piatto = simulate_scenario(replace(base, trend_multiplier=0.0))
    crescente = simulate_scenario(replace(base, trend_multiplier=4.0))
    assert crescente.plan.pipeline_stock > piatto.plan.pipeline_stock
    assert crescente.plan.cycle_stock > piatto.plan.cycle_stock


def test_trend_negativo_riduce_la_domanda() -> None:
    base = ScenarioConfig(product="Kinder Cioccolato", method="Regressione lineare")
    crescente = simulate_scenario(replace(base, trend_multiplier=1.0))
    calante = simulate_scenario(replace(base, trend_multiplier=-2.0))
    assert calante.scenario_series.mean() < crescente.scenario_series.mean()


# ---------------------------------------------------------------------------
# Effetto del LIVELLO DI SERVIZIO e degli altri parametri
# ---------------------------------------------------------------------------


def test_livello_di_servizio_aumenta_la_scorta_di_sicurezza(config_base) -> None:
    valori = [
        simulate_scenario(replace(config_base, service_level=s)).plan.safety_stock
        for s in (0.90, 0.95, 0.975, 0.99)
    ]
    assert valori == sorted(valori)


def test_periodo_di_riesame_aumenta_la_scorta_ciclica(config_base) -> None:
    corto = simulate_scenario(replace(config_base, review_period_months=1.0))
    lungo = simulate_scenario(replace(config_base, review_period_months=3.0))
    assert lungo.plan.cycle_stock == pytest.approx(3.0 * corto.plan.cycle_stock)


def test_orizzonte_di_previsione_rispettato(config_base) -> None:
    for orizzonte in (3, 6, 12):
        esito = simulate_scenario(replace(config_base, forecast_horizon=orizzonte))
        assert len(esito.bundle.forecast) == orizzonte
        assert esito.plan.horizon_months == orizzonte


def test_metodo_imposto_viene_rispettato(config_base) -> None:
    esito = simulate_scenario(replace(config_base, method="Media mobile"))
    assert esito.used_method == "Media mobile"


def test_selezione_automatica_quando_il_metodo_non_e_imposto(config_base, esito_base) -> None:
    assert esito_base.config.method is None
    assert esito_base.used_method == esito_base.best_method


def test_finestra_media_mobile_influenza_la_previsione(config_base) -> None:
    stretta = simulate_scenario(
        replace(config_base, method="Media mobile", ma_window=3)
    )
    ampia = simulate_scenario(
        replace(config_base, method="Media mobile", ma_window=12)
    )
    assert not np.allclose(
        stretta.bundle.forecast.to_numpy(), ampia.bundle.forecast.to_numpy()
    )


def test_alpha_influenza_la_previsione(config_base) -> None:
    lento = simulate_scenario(
        replace(config_base, method="Smorzamento esponenziale", alpha=0.1)
    )
    rapido = simulate_scenario(
        replace(config_base, method="Smorzamento esponenziale", alpha=0.9)
    )
    assert not np.allclose(
        lento.bundle.forecast.to_numpy(), rapido.bundle.forecast.to_numpy()
    )


# ---------------------------------------------------------------------------
# Validazione dei parametri
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parametri",
    [
        {"product": "Prodotto Inesistente"},
        {"lead_time_months": -1.0},
        {"lead_time_months": 48.0},
        {"service_level": 1.0},
        {"service_level": 0.2},
        {"review_period_months": 0.0},
        {"forecast_horizon": 0},
        {"ma_window": 0},
        {"alpha": 0.0},
        {"alpha": 1.5},
        {"variability_multiplier": -1.0},
        {"seasonality_multiplier": -0.5},
        {"test_size": 0},
    ],
)
def test_parametri_non_validi_sollevano_errore_in_italiano(parametri) -> None:
    config = ScenarioConfig(**parametri)
    with pytest.raises(ScenarioError) as info:
        config.validate()
    messaggio = str(info.value)
    assert len(messaggio) > 10
    # Il messaggio deve essere in italiano, non un traceback tecnico.
    assert "Traceback" not in messaggio


def test_configurazione_valida_non_solleva_errori() -> None:
    ScenarioConfig(product="Nutella").validate()


def test_errore_di_valutazione_tradotto_in_scenario_error() -> None:
    """Un test set troppo lungo deve produrre un messaggio comprensibile."""
    config = ScenarioConfig(product="Nutella", test_size=30)
    with pytest.raises(ScenarioError, match="Impossibile completare la previsione"):
        simulate_scenario(config)


# ---------------------------------------------------------------------------
# Confronto fra scenari
# ---------------------------------------------------------------------------


def test_confronto_struttura_tabella(config_base) -> None:
    a = simulate_scenario(replace(config_base, name="A", lead_time_months=2.0))
    b = simulate_scenario(replace(config_base, name="B", lead_time_months=5.0))
    tabella = compare_scenarios(a, b)

    assert list(tabella.columns) == ["Indicatore", "A", "B", "Variazione", "Variazione %"]
    assert len(tabella) == 8
    assert "Scorta totale (unita')" in set(tabella["Indicatore"])


def test_confronto_variazioni_coerenti(config_base) -> None:
    a = simulate_scenario(replace(config_base, name="A", lead_time_months=2.0))
    b = simulate_scenario(replace(config_base, name="B", lead_time_months=5.0))
    tabella = compare_scenarios(a, b)

    for _, riga in tabella.iterrows():
        assert riga["Variazione"] == pytest.approx(riga["B"] - riga["A"])


def test_confronto_evidenzia_aumento_con_lead_time(config_base) -> None:
    a = simulate_scenario(replace(config_base, name="A", lead_time_months=2.0))
    b = simulate_scenario(replace(config_base, name="B", lead_time_months=5.0))
    tabella = compare_scenarios(a, b).set_index("Indicatore")
    assert tabella.loc["Scorta pipeline (unita')", "Variazione %"] > 0
    assert tabella.loc["Scorta totale (unita')", "Variazione %"] > 0


def test_confronto_gestisce_nomi_identici(config_base) -> None:
    a = simulate_scenario(replace(config_base, name="Uguale"))
    b = simulate_scenario(replace(config_base, name="Uguale", lead_time_months=4.0))
    tabella = compare_scenarios(a, b)
    assert "Uguale (A)" in tabella.columns
    assert "Uguale (B)" in tabella.columns


# ---------------------------------------------------------------------------
# Scenari predefiniti
# ---------------------------------------------------------------------------


def test_preset_definiti_e_simulabili() -> None:
    assert len(PRESET_SCENARIOS) >= 2
    for nome, valori in PRESET_SCENARIOS.items():
        config = ScenarioConfig(name=nome, product="Ferrero Rocher", **valori)
        esito = simulate_scenario(config)
        assert esito.plan.total_stock > 0


def test_preset_stress_piu_oneroso_del_preset_stabile() -> None:
    """Lo scenario B della specifica deve richiedere piu' scorta dell'A."""
    stabile = simulate_scenario(
        ScenarioConfig(
            name="A", product="Ferrero Rocher", **PRESET_SCENARIOS["A - Filiera stabile"]
        )
    )
    stress = simulate_scenario(
        ScenarioConfig(
            name="B",
            product="Ferrero Rocher",
            **PRESET_SCENARIOS["B - Filiera sotto stress"],
        )
    )
    assert stress.plan.total_stock > stabile.plan.total_stock
    assert stress.plan.safety_stock > stabile.plan.safety_stock
    assert stress.plan.pipeline_stock > stabile.plan.pipeline_stock


# ---------------------------------------------------------------------------
# Esito della simulazione
# ---------------------------------------------------------------------------


def test_esito_espone_tabella_kpi(esito_base) -> None:
    kpi = esito_base.kpi_table()
    assert len(kpi) == 11
    assert set(kpi.columns) == {"Indicatore", "Valore"}


def test_esito_calcola_le_diagnostiche(esito_base) -> None:
    for chiave in (
        "cv_storico_%",
        "domanda_media_storica",
        "delta_vs_baseline_%",
        "ampiezza_banda_%",
    ):
        assert chiave in esito_base.diagnostics
        assert np.isfinite(esito_base.diagnostics[chiave])


def test_confronto_metodi_presente_nellesito(esito_base) -> None:
    assert len(esito_base.comparison) == 5
    assert esito_base.comparison["Migliore"].sum() == 1


def test_simulazione_su_tutti_i_prodotti() -> None:
    from src.config import PRODUCT_NAMES

    for prodotto in PRODUCT_NAMES:
        esito = simulate_scenario(ScenarioConfig(product=prodotto))
        assert esito.plan.total_stock > 0
        assert len(esito.bundle.forecast) == esito.config.forecast_horizon
