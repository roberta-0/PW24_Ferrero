"""
Test dei modelli di scorta.

I test verificano sia la correttezza numerica delle formule (confronto con
valori calcolati a mano) sia le **proprieta' di monotonia** richieste dalla
specifica PW24: al crescere del lead time deve crescere la scorta pipeline,
al crescere della variabilita' deve crescere la scorta di sicurezza, e cosi'
via.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.inventory import (
    InventoryError,
    anticipation_stock,
    compute_inventory_plan,
    cycle_stock,
    pipeline_stock,
    safety_stock,
    service_level_to_z,
)


# ---------------------------------------------------------------------------
# Fattore di sicurezza
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "livello, z_atteso",
    [(0.90, 1.2816), (0.95, 1.6449), (0.975, 1.9600), (0.99, 2.3263)],
)
def test_z_corrisponde_ai_valori_tabulati(livello: float, z_atteso: float) -> None:
    """I valori devono coincidere con le tavole della normale standard."""
    assert service_level_to_z(livello) == pytest.approx(z_atteso, abs=1e-3)


def test_z_cresce_con_il_livello_di_servizio() -> None:
    livelli = [0.90, 0.95, 0.975, 0.99]
    z = [service_level_to_z(s) for s in livelli]
    assert z == sorted(z)


def test_z_rifiuta_livelli_non_validi() -> None:
    for livello in (0.0, 0.3, 1.0, 1.5):
        with pytest.raises(InventoryError):
            service_level_to_z(livello)


# ---------------------------------------------------------------------------
# Scorta ciclica
# ---------------------------------------------------------------------------


def test_scorta_ciclica_formula_esatta() -> None:
    """Q = D x R ; scorta media = Q/2."""
    assert cycle_stock(average_demand=1000.0, review_period_months=2.0) == pytest.approx(
        1000.0
    )


def test_scorta_ciclica_proporzionale_al_periodo_di_riesame() -> None:
    base = cycle_stock(1000.0, 1.0)
    doppio = cycle_stock(1000.0, 2.0)
    assert doppio == pytest.approx(2.0 * base)


def test_scorta_ciclica_proporzionale_alla_domanda() -> None:
    assert cycle_stock(2000.0, 1.0) == pytest.approx(2.0 * cycle_stock(1000.0, 1.0))


def test_scorta_ciclica_rifiuta_parametri_non_validi() -> None:
    with pytest.raises(InventoryError):
        cycle_stock(1000.0, review_period_months=0.0)
    with pytest.raises(InventoryError):
        cycle_stock(-100.0, review_period_months=1.0)


# ---------------------------------------------------------------------------
# Scorta di sicurezza
# ---------------------------------------------------------------------------


def test_scorta_sicurezza_formula_esatta() -> None:
    """SS = z x sigma x sqrt(L) ; con L=4, sigma=100, 95% -> 1,6449*100*2."""
    valore = safety_stock(sigma_monthly=100.0, lead_time_months=4.0, service_level=0.95)
    assert valore == pytest.approx(1.6449 * 100.0 * 2.0, abs=0.1)


def test_scorta_sicurezza_cresce_con_la_variabilita() -> None:
    """Requisito PW24: piu' variabilita' -> piu' scorta di sicurezza."""
    bassa = safety_stock(50.0, 2.0, 0.95)
    alta = safety_stock(150.0, 2.0, 0.95)
    assert alta > bassa
    assert alta == pytest.approx(3.0 * bassa)   # lineare in sigma


def test_scorta_sicurezza_cresce_con_il_lead_time() -> None:
    """Requisito PW24: piu' lead time -> piu' scorta di sicurezza."""
    valori = [safety_stock(100.0, lt, 0.95) for lt in (1.0, 2.0, 4.0, 8.0)]
    assert valori == sorted(valori)


def test_scorta_sicurezza_cresce_con_radice_del_lead_time() -> None:
    """La crescita e' sub-lineare: quadruplicare L raddoppia la scorta."""
    uno = safety_stock(100.0, 1.0, 0.95)
    quattro = safety_stock(100.0, 4.0, 0.95)
    assert quattro == pytest.approx(2.0 * uno)


def test_scorta_sicurezza_cresce_con_il_livello_di_servizio() -> None:
    valori = [safety_stock(100.0, 2.0, s) for s in (0.90, 0.95, 0.975, 0.99)]
    assert valori == sorted(valori)


def test_scorta_sicurezza_nulla_senza_variabilita() -> None:
    """Domanda perfettamente nota: nessun cuscinetto necessario."""
    assert safety_stock(0.0, 5.0, 0.99) == pytest.approx(0.0)


def test_scorta_sicurezza_nulla_con_lead_time_nullo() -> None:
    assert safety_stock(100.0, 0.0, 0.99) == pytest.approx(0.0)


def test_intervallo_di_protezione_esteso_aumenta_la_scorta() -> None:
    """Includere il periodo di riesame allunga l'intervallo di protezione."""
    solo_lt = safety_stock(100.0, 2.0, 0.95, review_period_months=0.0)
    con_riesame = safety_stock(100.0, 2.0, 0.95, review_period_months=1.0)
    assert con_riesame > solo_lt
    assert con_riesame == pytest.approx(
        service_level_to_z(0.95) * 100.0 * np.sqrt(3.0)
    )


def test_scorta_sicurezza_rifiuta_parametri_non_validi() -> None:
    with pytest.raises(InventoryError):
        safety_stock(-10.0, 2.0, 0.95)
    with pytest.raises(InventoryError):
        safety_stock(100.0, -1.0, 0.95)
    with pytest.raises(InventoryError):
        safety_stock(100.0, 2.0, 1.5)


# ---------------------------------------------------------------------------
# Scorta anticipata
# ---------------------------------------------------------------------------


def test_scorta_anticipata_nulla_con_domanda_piatta() -> None:
    """Senza stagionalita' non serve alcun accumulo preventivo."""
    assert anticipation_stock([1000.0] * 12) == pytest.approx(0.0)


def test_scorta_anticipata_caso_calcolato_a_mano() -> None:
    """Sei mesi a 100 e sei mesi a 300: media 200.

    Eccedenze: -100 per sei mesi (cum. da 0 a -600), poi +100 per sei mesi
    (cum. da -600 a 0). max = 0, min = -600 -> scorta anticipata = 600.
    """
    previsione = [100.0] * 6 + [300.0] * 6
    assert anticipation_stock(previsione) == pytest.approx(600.0)


def test_scorta_anticipata_cresce_con_lampiezza_stagionale() -> None:
    """Requisito PW24: piu' stagionalita' -> piu' scorta anticipata."""
    debole = [900.0] * 6 + [1100.0] * 6
    forte = [500.0] * 6 + [1500.0] * 6
    assert anticipation_stock(forte) > anticipation_stock(debole)


def test_scorta_anticipata_con_profilo_sinusoidale() -> None:
    """Ampiezze crescenti devono produrre scorte anticipate crescenti."""
    t = np.arange(12)
    valori = [
        anticipation_stock(1000.0 + ampiezza * np.sin(2 * np.pi * t / 12))
        for ampiezza in (50.0, 150.0, 400.0)
    ]
    assert valori == sorted(valori)


def test_scorta_anticipata_mai_negativa() -> None:
    rng = np.random.default_rng(11)
    for _ in range(25):
        previsione = rng.uniform(100, 2000, size=12)
        assert anticipation_stock(previsione) >= 0.0


def test_scorta_anticipata_con_ritmo_produttivo_esplicito() -> None:
    """Un ritmo produttivo inferiore alla domanda richiede piu' accumulo."""
    previsione = [1000.0] * 12
    assert anticipation_stock(previsione, production_rate=1000.0) == pytest.approx(0.0)
    assert anticipation_stock(previsione, production_rate=800.0) > 0.0


def test_scorta_anticipata_rifiuta_input_non_validi() -> None:
    with pytest.raises(InventoryError):
        anticipation_stock([])
    with pytest.raises(InventoryError):
        anticipation_stock([100.0, np.nan, 200.0])
    with pytest.raises(InventoryError):
        anticipation_stock([100.0] * 6, production_rate=-5.0)


# ---------------------------------------------------------------------------
# Scorta pipeline
# ---------------------------------------------------------------------------


def test_scorta_pipeline_formula_esatta() -> None:
    """Pipeline = D x L (legge di Little)."""
    assert pipeline_stock(1000.0, 3.0) == pytest.approx(3000.0)


def test_scorta_pipeline_cresce_con_il_lead_time() -> None:
    """Requisito PW24 esplicito: deve aumentare se il lead time aumenta."""
    valori = [pipeline_stock(1000.0, lt) for lt in (1.0, 2.0, 3.0, 5.0, 8.0)]
    assert valori == sorted(valori)
    assert len(set(valori)) == len(valori)


def test_scorta_pipeline_lineare_nel_lead_time() -> None:
    assert pipeline_stock(1000.0, 6.0) == pytest.approx(
        3.0 * pipeline_stock(1000.0, 2.0)
    )


def test_scorta_pipeline_nulla_con_consegna_immediata() -> None:
    assert pipeline_stock(1000.0, 0.0) == pytest.approx(0.0)


def test_scorta_pipeline_rifiuta_parametri_non_validi() -> None:
    with pytest.raises(InventoryError):
        pipeline_stock(-100.0, 2.0)
    with pytest.raises(InventoryError):
        pipeline_stock(1000.0, -2.0)


# ---------------------------------------------------------------------------
# Piano di scorta complessivo
# ---------------------------------------------------------------------------


@pytest.fixture
def piano_base():
    """Piano di riferimento usato dai test sulla composizione."""
    previsione = [1000.0] * 6 + [2000.0] * 6
    return compute_inventory_plan(
        product="Test",
        forecast=previsione,
        sigma_monthly=200.0,
        lead_time_months=2.0,
        service_level=0.95,
        review_period_months=1.0,
    )


def test_totale_e_somma_delle_quattro_componenti(piano_base) -> None:
    atteso = (
        piano_base.cycle_stock
        + piano_base.safety_stock
        + piano_base.anticipation_stock
        + piano_base.pipeline_stock
    )
    assert piano_base.total_stock == pytest.approx(atteso)


def test_composizione_percentuale_somma_a_cento(piano_base) -> None:
    assert sum(piano_base.composition_pct.values()) == pytest.approx(100.0)


def test_piano_espone_le_quattro_componenti(piano_base) -> None:
    assert set(piano_base.components) == {
        "cycle_stock",
        "safety_stock",
        "anticipation_stock",
        "pipeline_stock",
    }
    assert all(v >= 0 for v in piano_base.components.values())


def test_etichette_italiane_delle_componenti(piano_base) -> None:
    etichette = set(piano_base.components_it)
    assert etichette == {
        "Scorta ciclica",
        "Scorta di sicurezza",
        "Scorta anticipata",
        "Scorta pipeline",
    }


def test_domanda_media_dalla_previsione(piano_base) -> None:
    """La domanda media e' calcolata sulla previsione, non sullo storico."""
    assert piano_base.average_demand == pytest.approx(1500.0)


def test_copertura_in_mesi(piano_base) -> None:
    attesa = piano_base.total_stock / piano_base.average_demand
    assert piano_base.coverage_months == pytest.approx(attesa)


def test_piano_registra_le_ipotesi(piano_base) -> None:
    """Le ipotesi dei modelli devono essere tracciate per la documentazione."""
    assert set(piano_base.assumptions) == {
        "scorta_ciclica",
        "scorta_sicurezza",
        "scorta_anticipata",
        "scorta_pipeline",
    }


def test_piano_lead_time_maggiore_aumenta_il_totale() -> None:
    previsione = [1000.0] * 12
    corto = compute_inventory_plan("X", previsione, 200.0, 1.0, 0.95, 1.0)
    lungo = compute_inventory_plan("X", previsione, 200.0, 6.0, 0.95, 1.0)
    assert lungo.total_stock > corto.total_stock
    assert lungo.pipeline_stock > corto.pipeline_stock
    assert lungo.safety_stock > corto.safety_stock
    # La scorta ciclica non dipende dal lead time.
    assert lungo.cycle_stock == pytest.approx(corto.cycle_stock)


def test_piano_rifiuta_previsione_vuota() -> None:
    with pytest.raises(InventoryError):
        compute_inventory_plan("X", [], 100.0, 2.0, 0.95, 1.0)


def test_piano_rifiuta_livello_di_servizio_non_valido() -> None:
    with pytest.raises(InventoryError):
        compute_inventory_plan("X", [1000.0] * 6, 100.0, 2.0, 1.0, 1.0)


def test_piano_con_intervallo_di_protezione_esteso() -> None:
    previsione = [1000.0] * 12
    base = compute_inventory_plan("X", previsione, 200.0, 2.0, 0.95, 1.0)
    esteso = compute_inventory_plan(
        "X", previsione, 200.0, 2.0, 0.95, 1.0, include_review_in_protection=True
    )
    assert esteso.safety_stock > base.safety_stock
    assert esteso.protection_interval_months == pytest.approx(3.0)
    assert base.protection_interval_months == pytest.approx(2.0)
