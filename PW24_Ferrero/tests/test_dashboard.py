"""
Test funzionali della dashboard Streamlit.

Usano ``streamlit.testing.v1.AppTest``, l'harness ufficiale di Streamlit, che
esegue l'applicazione in modalita' headless e consente di ispezionare gli
elementi prodotti e di simulare l'interazione con i widget.

I test verificano che la dashboard si avvii senza eccezioni, che tutte le
sezioni previste dalla specifica siano presenti e - soprattutto - che le leve
della sidebar producano effetti osservabili sui valori mostrati.
"""

from __future__ import annotations

from pathlib import Path

import pytest

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
from src.narrative import (
    describe_demand_profile,
    describe_inventory_mix,
    describe_method_choice,
    describe_scenario_comparison,
    describe_scenario_effects,
)
from src.scenarios import ScenarioConfig, compare_scenarios, simulate_scenario

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

#: Percorso assoluto dell'applicazione: i percorsi relativi verrebbero
#: risolti rispetto alla cartella dei test anziche' alla radice del progetto.
APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def avvia_dashboard():
    """Istanzia ed esegue la dashboard in modalita' headless."""
    return AppTest.from_file(APP_PATH, default_timeout=900).run()


@pytest.fixture(scope="module")
def app():
    """Avvia la dashboard una sola volta per l'intero modulo di test."""
    return avvia_dashboard()


# ---------------------------------------------------------------------------
# Avvio e struttura della dashboard
# ---------------------------------------------------------------------------


def test_dashboard_si_avvia_senza_eccezioni(app) -> None:
    assert not app.exception, [e.message for e in app.exception]


def test_dashboard_contiene_le_otto_sezioni(app) -> None:
    """Le sezioni 1-6 sono richieste dalla specifica; 7-8 sono estensioni."""
    titoli = " ".join(h.value for h in app.header)
    for atteso in (
        "Scenario di analisi",
        "Domanda storica e prevista",
        "Confronto dei metodi previsionali",
        "Composizione delle scorte",
        "Indicatori sintetici",
        "Analisi dello scenario",
        "Confronto fra scenari",
        "Quadro di sintesi",
    ):
        assert atteso in titoli


def test_dashboard_espone_i_kpi_richiesti(app) -> None:
    """Domanda, lead time, servizio e le quattro scorte devono essere KPI."""
    etichette = " ".join(m.label for m in app.metric)
    for atteso in (
        "Domanda media storica",
        "Domanda media prevista",
        "Lead time",
        "Livello di servizio",
        "Scorta ciclica",
        "Scorta di sicurezza",
        "Scorta anticipata",
        "Scorta pipeline",
        "Scorta totale",
    ):
        assert atteso in etichette


def test_dashboard_mostra_il_disclaimer_sui_dati_sintetici(app) -> None:
    """Requisito di integrita' accademica."""
    testi = " ".join(w.value for w in app.warning).lower()
    assert "sintetic" in testi
    assert "ferrero" in testi


def test_dashboard_mostra_tabelle_e_grafici(app) -> None:
    assert len(app.dataframe) >= 5
    assert len(app.markdown) >= 10


def test_nessun_messaggio_di_errore_allavvio(app) -> None:
    assert len(app.error) == 0


# ---------------------------------------------------------------------------
# Controlli della sidebar
# ---------------------------------------------------------------------------


def test_sidebar_espone_tutte_le_leve(app) -> None:
    """Le leve richieste dalla specifica devono essere tutte presenti."""
    etichette = " ".join(
        w.label
        for gruppo in (app.sidebar.selectbox, app.sidebar.slider, app.sidebar.select_slider)
        for w in gruppo
    )
    for atteso in (
        "Articolo analizzato",
        "Metodo previsivo",
        "Orizzonte di previsione",
        "Finestra media mobile",
        "Alpha",
        "Variabilita'",
        "Trend",
        "Stagionalita'",
        "Lead time",
        "Livello di servizio",
    ):
        assert atteso in etichette, f"Leva mancante: {atteso}"


def test_selettore_prodotto_contiene_i_quattro_articoli(app) -> None:
    opzioni = app.sidebar.selectbox[0].options
    assert set(opzioni) == {
        "Nutella",
        "Kinder Cioccolato",
        "Ferrero Rocher",
        "Kinder Happy Hippo",
    }


def test_selettore_metodo_include_automatico_e_cinque_metodi(app) -> None:
    opzioni = app.sidebar.selectbox[1].options
    assert len(opzioni) == 6
    assert any("automatica" in o for o in opzioni)
    assert "Media mobile" in opzioni
    assert "Smorzamento esponenziale" in opzioni
    assert "Regressione lineare" in opzioni


# ---------------------------------------------------------------------------
# Interazione: le leve devono produrre effetti
# ---------------------------------------------------------------------------


def _valore_kpi(app_instance, etichetta: str) -> str:
    for metrica in app_instance.metric:
        if metrica.label == etichetta:
            return metrica.value
    raise AssertionError(f"KPI '{etichetta}' non trovato nella dashboard.")


def test_cambio_prodotto_aggiorna_la_dashboard() -> None:
    istanza = avvia_dashboard()
    prima = _valore_kpi(istanza, "Domanda media storica")

    istanza.sidebar.selectbox[0].set_value("Ferrero Rocher").run()
    assert not istanza.exception, [e.message for e in istanza.exception]
    assert _valore_kpi(istanza, "Domanda media storica") != prima


def test_aumento_lead_time_aumenta_la_scorta_pipeline() -> None:
    """Verifica end-to-end del requisito piu' importante sulle leve."""
    istanza = avvia_dashboard()
    lead_time = next(
        s for s in istanza.sidebar.slider if "Lead time" in s.label
    )

    lead_time.set_value(1.0).run()
    pipeline_corto = _valore_kpi(istanza, "Scorta pipeline")

    lead_time = next(s for s in istanza.sidebar.slider if "Lead time" in s.label)
    lead_time.set_value(7.0).run()
    pipeline_lungo = _valore_kpi(istanza, "Scorta pipeline")

    def numero(testo: str) -> float:
        return float(testo.replace(".", "").replace(",", "."))

    assert numero(pipeline_lungo) > numero(pipeline_corto)


def test_metodo_imposto_viene_mostrato_nei_kpi() -> None:
    istanza = avvia_dashboard()
    istanza.sidebar.selectbox[1].set_value("Regressione lineare").run()
    assert not istanza.exception, [e.message for e in istanza.exception]
    assert _valore_kpi(istanza, "Metodo previsivo") == "Regressione lineare"


def test_leve_estreme_non_generano_eccezioni() -> None:
    """Robustezza: combinazioni limite devono essere gestite correttamente."""
    istanza = avvia_dashboard()

    for slider in istanza.sidebar.slider:
        if "Variabilita'" in slider.label or "Stagionalita'" in slider.label:
            slider.set_value(0.0)
        elif "Trend" in slider.label:
            slider.set_value(-2.0)
    istanza.run()
    assert not istanza.exception, [e.message for e in istanza.exception]


# ---------------------------------------------------------------------------
# Grafici: costruzione senza errori e titoli in italiano
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def esito():
    return simulate_scenario(ScenarioConfig(name="Test", product="Ferrero Rocher"))


def test_tutti_i_grafici_si_costruiscono(esito, dataset) -> None:
    figure = [
        chart_demand_and_forecast(esito.bundle),
        chart_method_accuracy(esito.comparison, "MAPE", esito.best_method),
        chart_inventory_composition(esito.plan),
        chart_inventory_share(esito.plan),
        chart_seasonal_profile(esito.scenario_series, "Ferrero Rocher"),
        chart_products_overview(dataset, list(dataset["product"].unique())),
        chart_baseline_vs_scenario(
            esito.baseline_series, esito.scenario_series, "Ferrero Rocher"
        ),
    ]
    for figura in figure:
        assert len(figura.data) >= 1


def test_grafici_hanno_titoli_ed_assi_in_italiano(esito) -> None:
    figura = chart_demand_and_forecast(esito.bundle)
    assert "Domanda storica e prevista" in figura.layout.title.text
    assert "Mese" == figura.layout.xaxis.title.text
    assert "Domanda" in figura.layout.yaxis.title.text


def test_grafico_composizione_ha_quattro_componenti(esito) -> None:
    figura = chart_inventory_composition(esito.plan)
    nomi = {traccia.name for traccia in figura.data}
    assert nomi == {
        "Scorta ciclica",
        "Scorta di sicurezza",
        "Scorta anticipata",
        "Scorta pipeline",
    }


def test_grafico_confronto_scenari(esito) -> None:
    from dataclasses import replace

    altro = simulate_scenario(
        replace(esito.config, name="Stress", lead_time_months=6.0)
    )
    tabella = compare_scenarios(esito, altro)
    figura = chart_scenario_comparison(tabella, "Test", "Stress")
    assert len(figura.data) == 2


def test_grafico_previsione_contiene_tutte_le_serie(esito) -> None:
    """Storico train, test osservato, previsione sul test, banda e futuro."""
    figura = chart_demand_and_forecast(esito.bundle, show_band=True)
    nomi = " ".join(t.name or "" for t in figura.data)
    assert "addestramento" in nomi
    assert "test" in nomi
    assert "Previsione futura" in nomi
    assert "Banda" in nomi


# ---------------------------------------------------------------------------
# Commenti dinamici: devono contenere numeri dello scenario
# ---------------------------------------------------------------------------


def test_commenti_citano_valori_calcolati(esito) -> None:
    """I testi non devono essere generici: devono contenere cifre."""
    for testo in (
        describe_demand_profile(esito),
        describe_method_choice(esito),
        describe_inventory_mix(esito),
        describe_scenario_effects(esito),
    ):
        assert any(carattere.isdigit() for carattere in testo)
        assert len(testo) > 150


def test_commenti_cambiano_con_lo_scenario() -> None:
    """Il commento gestionale deve dipendere dai valori, non essere fisso."""
    from dataclasses import replace

    base = ScenarioConfig(product="Ferrero Rocher", lead_time_months=1.0)
    a = simulate_scenario(base)
    b = simulate_scenario(replace(base, lead_time_months=7.0))
    assert describe_scenario_effects(a) != describe_scenario_effects(b)


def test_commento_confronto_identifica_il_driver() -> None:
    from dataclasses import replace

    base = ScenarioConfig(name="A", product="Ferrero Rocher", lead_time_months=2.0)
    a = simulate_scenario(base)
    b = simulate_scenario(replace(base, name="B", lead_time_months=6.0))
    testo = describe_scenario_comparison(a, b, compare_scenarios(a, b))
    assert "scorta pipeline" in testo.lower()
    assert "lead time" in testo.lower()


def test_commento_menziona_la_stagionalita_per_rocher(esito) -> None:
    testo = describe_scenario_effects(esito)
    assert "Stagionalita'" in testo
    assert "scorta anticipata" in testo.lower()
