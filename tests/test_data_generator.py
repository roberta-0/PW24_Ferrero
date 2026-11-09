"""
Test della generazione del dataset sintetico.

Verificano struttura, dominio dei valori, riproducibilita' e - soprattutto -
che i quattro prodotti esibiscano effettivamente i comportamenti di domanda
differenziati richiesti dalla specifica PW24.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config import N_PERIODS, PRODUCTS, RANDOM_SEED
from src.data_generator import (
    build_date_index,
    build_parameters_table,
    generate_demand_dataset,
    generate_product_series,
    save_dataset,
    seasonal_factor,
    to_wide_format,
)


# ---------------------------------------------------------------------------
# Struttura del dataset
# ---------------------------------------------------------------------------


def test_dataset_ha_quattro_prodotti(dataset: pd.DataFrame) -> None:
    """La specifica richiede almeno quattro articoli."""
    assert dataset["product"].nunique() == 4
    assert set(dataset["product"]) == set(PRODUCTS)


def test_dataset_ha_48_osservazioni_per_prodotto(dataset: pd.DataFrame) -> None:
    """48 osservazioni mensili per prodotto, 192 righe complessive."""
    conteggi = dataset.groupby("product")["demand"].count()
    assert (conteggi == N_PERIODS).all()
    assert len(dataset) == 4 * N_PERIODS


def test_dataset_ha_colonne_richieste(dataset: pd.DataFrame) -> None:
    assert {"date", "product", "demand"}.issubset(dataset.columns)


def test_periodo_coperto_gennaio_2022_dicembre_2025(dataset: pd.DataFrame) -> None:
    assert dataset["date"].min() == pd.Timestamp("2022-01-01")
    assert dataset["date"].max() == pd.Timestamp("2025-12-01")


def test_continuita_mensile(dataset: pd.DataFrame) -> None:
    """Nessun mese mancante all'interno di ciascuna serie."""
    for _, gruppo in dataset.groupby("product"):
        date = pd.DatetimeIndex(gruppo["date"].sort_values())
        attese = pd.date_range(date[0], date[-1], freq="MS")
        assert date.equals(attese)


def test_nessuna_data_duplicata(dataset: pd.DataFrame) -> None:
    assert not dataset.duplicated(subset=["product", "date"]).any()


# ---------------------------------------------------------------------------
# Dominio dei valori
# ---------------------------------------------------------------------------


def test_domanda_sempre_positiva(dataset: pd.DataFrame) -> None:
    """Requisito esplicito: tutti i valori di domanda devono essere positivi."""
    assert (dataset["demand"] > 0).all()


def test_domanda_intera(dataset: pd.DataFrame) -> None:
    """Le quantita' sono cartoni: devono essere numeri interi."""
    assert pd.api.types.is_integer_dtype(dataset["demand"])


def test_nessun_valore_mancante(dataset: pd.DataFrame) -> None:
    assert not dataset.isna().any().any()


def test_valori_plausibili(dataset: pd.DataFrame) -> None:
    """Ogni serie resta entro un intervallo plausibile attorno al livello base."""
    for prodotto, gruppo in dataset.groupby("product"):
        base = PRODUCTS[prodotto].base_demand
        assert gruppo["demand"].min() > base * 0.2
        assert gruppo["demand"].max() < base * 5.0


# ---------------------------------------------------------------------------
# Riproducibilita'
# ---------------------------------------------------------------------------


def test_generazione_riproducibile() -> None:
    """Due generazioni con lo stesso seed devono coincidere esattamente."""
    primo = generate_demand_dataset(seed=RANDOM_SEED)
    secondo = generate_demand_dataset(seed=RANDOM_SEED)
    pd.testing.assert_frame_equal(primo, secondo)


def test_seed_diverso_produce_serie_diverse() -> None:
    """Cambiare seed deve cambiare le realizzazioni casuali."""
    primo = generate_demand_dataset(seed=RANDOM_SEED)
    secondo = generate_demand_dataset(seed=RANDOM_SEED + 1)
    assert not primo["demand"].equals(secondo["demand"])


def test_flussi_casuali_indipendenti_fra_prodotti() -> None:
    """Modificare i parametri di un prodotto non deve alterare gli altri.

    Proprieta' garantita dall'uso di ``SeedSequence.spawn``: e' essenziale
    perche' le leve di scenario agiscono su un solo prodotto alla volta.
    """
    base = generate_demand_dataset()
    modificati = dict(PRODUCTS)
    modificati["Nutella"] = PRODUCTS["Nutella"].scaled(variability_multiplier=3.0)
    alterato = generate_demand_dataset(products=modificati)

    for prodotto in PRODUCTS:
        serie_base = base[base["product"] == prodotto]["demand"].to_numpy()
        serie_alt = alterato[alterato["product"] == prodotto]["demand"].to_numpy()
        if prodotto == "Nutella":
            assert not np.array_equal(serie_base, serie_alt)
        else:
            assert np.array_equal(serie_base, serie_alt)


# ---------------------------------------------------------------------------
# Comportamenti di domanda differenziati (requisito PW24)
# ---------------------------------------------------------------------------


def _coefficiente_variazione(dataset: pd.DataFrame, prodotto: str) -> float:
    serie = dataset[dataset["product"] == prodotto]["demand"]
    return float(serie.std(ddof=1) / serie.mean() * 100.0)


def _escursione_stagionale(dataset: pd.DataFrame, prodotto: str) -> float:
    """Escursione dell'indice stagionale (media annua = 100)."""
    gruppo = dataset[dataset["product"] == prodotto].copy()
    gruppo["mese"] = gruppo["date"].dt.month
    medie = gruppo.groupby("mese")["demand"].mean()
    indice = medie / medie.mean() * 100.0
    return float(indice.max() - indice.min())


def test_nutella_e_la_serie_piu_stabile(dataset: pd.DataFrame) -> None:
    """Nutella deve avere la variabilita' complessiva piu' bassa."""
    cv = {p: _coefficiente_variazione(dataset, p) for p in PRODUCTS}
    assert cv["Nutella"] == min(cv.values())
    assert cv["Nutella"] < 10.0


def test_happy_hippo_piu_rumoroso_di_nutella_e_kinder(dataset: pd.DataFrame) -> None:
    """Requisito: rumore superiore a Nutella e Kinder Cioccolato."""
    cv = {p: _coefficiente_variazione(dataset, p) for p in PRODUCTS}
    assert cv["Kinder Happy Hippo"] > cv["Nutella"]
    assert cv["Kinder Happy Hippo"] > cv["Kinder Cioccolato"]


def test_rocher_ha_la_stagionalita_piu_forte(dataset: pd.DataFrame) -> None:
    """Ferrero Rocher deve esibire la stagionalita' piu' marcata."""
    escursioni = {p: _escursione_stagionale(dataset, p) for p in PRODUCTS}
    assert escursioni["Ferrero Rocher"] == max(escursioni.values())
    assert escursioni["Ferrero Rocher"] > 80.0


def test_rocher_ha_picchi_nel_periodo_festivo(dataset: pd.DataFrame) -> None:
    """I mesi di punta devono cadere nel periodo autunnale/natalizio."""
    gruppo = dataset[dataset["product"] == "Ferrero Rocher"].copy()
    gruppo["mese"] = gruppo["date"].dt.month
    medie = gruppo.groupby("mese")["demand"].mean()
    tre_mesi_di_punta = set(medie.nlargest(3).index)
    assert tre_mesi_di_punta.issubset({10, 11, 12})


def test_prodotti_con_trend_positivo_crescono(dataset: pd.DataFrame) -> None:
    """Per i prodotti con trend, l'ultimo anno supera il primo."""
    for prodotto in ("Kinder Cioccolato", "Kinder Happy Hippo"):
        serie = (
            dataset[dataset["product"] == prodotto]
            .sort_values("date")["demand"]
            .to_numpy()
        )
        assert serie[-12:].mean() > serie[:12].mean()


def test_nutella_ha_trend_trascurabile(dataset: pd.DataFrame) -> None:
    """Il trend di Nutella deve restare molto contenuto (< 10% in 4 anni)."""
    serie = dataset[dataset["product"] == "Nutella"].sort_values("date")["demand"]
    variazione = (serie[-12:].mean() - serie[:12].mean()) / serie[:12].mean()
    assert abs(variazione) < 0.10


# ---------------------------------------------------------------------------
# Componenti del modello generatore
# ---------------------------------------------------------------------------


def test_fattore_stagionale_massimo_nel_mese_di_picco() -> None:
    mesi = np.arange(1, 13)
    fattori = seasonal_factor(mesi, amplitude=0.2, peak_month=12)
    assert int(mesi[np.argmax(fattori)]) == 12
    assert int(mesi[np.argmin(fattori)]) == 6


def test_fattore_stagionale_neutro_con_ampiezza_nulla() -> None:
    fattori = seasonal_factor(np.arange(1, 13), amplitude=0.0, peak_month=12)
    assert np.allclose(fattori, 1.0)


def test_profilo_festivo_incrementa_i_mesi_indicati() -> None:
    mesi = np.arange(1, 13)
    senza = seasonal_factor(mesi, amplitude=0.0, peak_month=12)
    con = seasonal_factor(mesi, amplitude=0.0, peak_month=12, festive_profile={11: 1.0})
    assert con[10] == pytest.approx(senza[10] + 1.0)
    assert con[0] == pytest.approx(senza[0])


def test_scaled_con_moltiplicatori_unitari_non_modifica_nulla() -> None:
    """Proprieta' di identita': fondamentale per la neutralita' dello scenario."""
    originale = PRODUCTS["Ferrero Rocher"]
    copia = originale.scaled(
        variability_multiplier=1.0, trend_multiplier=1.0, seasonality_multiplier=1.0
    )
    assert copia == originale


def test_scaled_amplifica_le_componenti_richieste() -> None:
    originale = PRODUCTS["Ferrero Rocher"]
    scalato = originale.scaled(
        variability_multiplier=2.0, trend_multiplier=0.0, seasonality_multiplier=3.0
    )
    assert scalato.noise_std == pytest.approx(originale.noise_std * 2.0)
    assert scalato.trend_rate == pytest.approx(0.0)
    assert scalato.seasonal_amplitude == pytest.approx(
        originale.seasonal_amplitude * 3.0
    )
    assert scalato.festive_profile[11] == pytest.approx(
        originale.festive_profile[11] * 3.0
    )


def test_variabilita_maggiore_aumenta_la_dispersione() -> None:
    """Aumentare il moltiplicatore di variabilita' deve aumentare il CV."""
    base = PRODUCTS["Nutella"]
    serie_base = generate_product_series(base, product_index=0)
    serie_alta = generate_product_series(
        base.scaled(variability_multiplier=4.0), product_index=0
    )
    cv_base = serie_base.std(ddof=1) / serie_base.mean()
    cv_alta = serie_alta.std(ddof=1) / serie_alta.mean()
    assert cv_alta > cv_base


def test_stagionalita_maggiore_amplia_escursione() -> None:
    base = PRODUCTS["Ferrero Rocher"]
    serie_base = generate_product_series(base, product_index=2)
    serie_alta = generate_product_series(
        base.scaled(seasonality_multiplier=2.0), product_index=2
    )
    escursione_base = serie_base.max() - serie_base.min()
    escursione_alta = serie_alta.max() - serie_alta.min()
    assert escursione_alta > escursione_base


# ---------------------------------------------------------------------------
# Indice temporale, formato pivot e persistenza
# ---------------------------------------------------------------------------


def test_indice_temporale_mensile() -> None:
    index = build_date_index()
    assert len(index) == N_PERIODS
    assert (index.day == 1).all()


def test_indice_temporale_rifiuta_periodi_non_positivi() -> None:
    with pytest.raises(ValueError):
        build_date_index(periods=0)


def test_formato_pivot_coerente(dataset: pd.DataFrame) -> None:
    wide = to_wide_format(dataset)
    assert len(wide) == N_PERIODS
    assert list(wide.columns) == ["date", *PRODUCTS]


def test_tabella_parametri_completa() -> None:
    tabella = build_parameters_table()
    assert len(tabella) == 4
    for colonna in ("base_demand", "trend_rate", "seasonal_amplitude", "noise_std"):
        assert colonna in tabella.columns


def test_salvataggio_su_disco(tmp_path, dataset: pd.DataFrame) -> None:
    """Il salvataggio deve produrre i tre CSV previsti e rileggibili."""
    scritti = save_dataset(dataset, data_dir=tmp_path)
    assert set(scritti) == {
        "demand_history",
        "demand_history_wide",
        "product_parameters",
    }
    for percorso in scritti.values():
        assert percorso.exists()
    riletto = pd.read_csv(scritti["demand_history"])
    assert len(riletto) == len(dataset)
