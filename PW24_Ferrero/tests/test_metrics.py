"""
Test degli indicatori di accuratezza e della valutazione train/test.

Le metriche sono verificate con esempi calcolati a mano, in modo che un
eventuale errore nella formula venga intercettato immediatamente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.evaluation import (
    EvaluationError,
    chronological_split,
    evaluate_all_products,
    evaluate_methods,
    forecast_with_interval,
    select_best_method,
)
from src.metrics import (
    MetricsError,
    bias,
    compute_all_metrics,
    mae,
    mape,
    rmse,
    smape,
)


# ---------------------------------------------------------------------------
# Correttezza numerica delle metriche
# ---------------------------------------------------------------------------


def test_mae_esempio_calcolato_a_mano() -> None:
    osservati = [100.0, 200.0, 300.0]
    previsti = [110.0, 180.0, 330.0]
    # errori assoluti: 10, 20, 30 -> media 20
    assert mae(osservati, previsti) == pytest.approx(20.0)


def test_rmse_esempio_calcolato_a_mano() -> None:
    osservati = [100.0, 200.0, 300.0]
    previsti = [110.0, 180.0, 330.0]
    # quadrati: 100, 400, 900 -> media 466,67 -> radice 21,602
    assert rmse(osservati, previsti) == pytest.approx(np.sqrt(1400.0 / 3.0))


def test_mape_esempio_calcolato_a_mano() -> None:
    osservati = [100.0, 200.0, 400.0]
    previsti = [110.0, 180.0, 440.0]
    # errori %: 10%, 10%, 10% -> media 10%
    assert mape(osservati, previsti) == pytest.approx(10.0)


def test_bias_segno_corretto() -> None:
    """Bias positivo quando il modello sovrastima."""
    assert bias([100.0, 100.0], [120.0, 130.0]) == pytest.approx(25.0)
    assert bias([100.0, 100.0], [80.0, 70.0]) == pytest.approx(-25.0)


def test_smape_simmetrico() -> None:
    """Lo sMAPE deve dare lo stesso valore scambiando osservato e previsto."""
    a, b = [100.0, 200.0], [120.0, 150.0]
    assert smape(a, b) == pytest.approx(smape(b, a))


def test_previsione_perfetta_azzera_tutte_le_metriche() -> None:
    valori = [100.0, 250.0, 310.0]
    metriche = compute_all_metrics(valori, valori)
    for nome in ("MAE", "RMSE", "MAPE", "Bias", "sMAPE"):
        assert metriche[nome] == pytest.approx(0.0)


def test_rmse_non_inferiore_al_mae() -> None:
    """Proprieta' matematica: RMSE >= MAE sempre (disuguaglianza di Jensen)."""
    rng = np.random.default_rng(7)
    for _ in range(20):
        osservati = rng.uniform(50, 500, size=15)
        previsti = osservati + rng.normal(0, 40, size=15)
        assert rmse(osservati, previsti) >= mae(osservati, previsti) - 1e-9


def test_metriche_invarianti_rispetto_allordine() -> None:
    osservati = [100.0, 200.0, 300.0]
    previsti = [90.0, 230.0, 280.0]
    diretto = compute_all_metrics(osservati, previsti)
    inverso = compute_all_metrics(osservati[::-1], previsti[::-1])
    assert diretto["MAE"] == pytest.approx(inverso["MAE"])
    assert diretto["RMSE"] == pytest.approx(inverso["RMSE"])


# ---------------------------------------------------------------------------
# Gestione dei casi limite
# ---------------------------------------------------------------------------


def test_mape_esclude_le_osservazioni_nulle() -> None:
    """Le osservazioni con domanda nulla sono escluse, non trattate come zero."""
    osservati = [0.0, 100.0, 200.0]
    previsti = [50.0, 110.0, 180.0]
    # considerate solo le ultime due: 10% e 10% -> 10%
    assert mape(osservati, previsti) == pytest.approx(10.0)


def test_mape_nan_se_tutte_le_osservazioni_sono_nulle() -> None:
    """Caso limite documentato: il criterio ripiega sull'RMSE."""
    assert np.isnan(mape([0.0, 0.0, 0.0], [10.0, 20.0, 30.0]))


def test_smape_definito_anche_con_osservazioni_nulle() -> None:
    valore = smape([0.0, 100.0], [10.0, 110.0])
    assert np.isfinite(valore)


def test_lunghezze_diverse_sollevano_errore() -> None:
    with pytest.raises(MetricsError, match="lunghezza"):
        mae([1.0, 2.0, 3.0], [1.0, 2.0])


def test_serie_vuota_solleva_errore() -> None:
    with pytest.raises(MetricsError):
        mae([], [])


def test_valori_mancanti_esclusi_dal_calcolo() -> None:
    osservati = [100.0, np.nan, 300.0]
    previsti = [110.0, 200.0, 330.0]
    # considerate solo prima e terza: errori 10 e 30 -> MAE 20
    assert mae(osservati, previsti) == pytest.approx(20.0)


def test_tutti_valori_mancanti_sollevano_errore() -> None:
    with pytest.raises(MetricsError):
        mae([np.nan, np.nan], [1.0, 2.0])


# ---------------------------------------------------------------------------
# Split cronologico
# ---------------------------------------------------------------------------


def test_split_rispetta_lordine_temporale(serie_rocher) -> None:
    """Requisito critico: nessun rimescolamento casuale della serie."""
    split = chronological_split(serie_rocher, test_size=12)
    assert split.n_train == 36
    assert split.n_test == 12
    assert split.train.index.max() < split.test.index.min()


def test_split_conserva_tutte_le_osservazioni(serie_rocher) -> None:
    split = chronological_split(serie_rocher, test_size=12)
    assert split.n_train + split.n_test == len(serie_rocher)
    ricomposta = pd.concat([split.train, split.test])
    pd.testing.assert_series_equal(ricomposta, serie_rocher.sort_index())


def test_split_prende_gli_ultimi_mesi_come_test(serie_rocher) -> None:
    split = chronological_split(serie_rocher, test_size=12)
    assert split.test.index[0] == pd.Timestamp("2025-01-01")
    assert split.test.index[-1] == pd.Timestamp("2025-12-01")


def test_split_rifiuta_serie_troppo_corta() -> None:
    corta = pd.Series(
        np.arange(20.0), index=pd.date_range("2024-01-01", periods=20, freq="MS")
    )
    with pytest.raises(EvaluationError, match="troppo corta"):
        chronological_split(corta, test_size=12)


def test_split_rifiuta_test_size_non_valido(serie_rocher) -> None:
    with pytest.raises(EvaluationError):
        chronological_split(serie_rocher, test_size=0)


# ---------------------------------------------------------------------------
# Valutazione e selezione del metodo
# ---------------------------------------------------------------------------


def test_valutazione_restituisce_una_riga_per_metodo(serie_rocher) -> None:
    risultati = evaluate_methods(serie_rocher, product="Ferrero Rocher")
    assert len(risultati) == 5
    assert set(["Prodotto", "Metodo", "MAE", "RMSE", "MAPE"]).issubset(risultati.columns)


def test_valutazione_produce_metriche_positive(serie_rocher) -> None:
    risultati = evaluate_methods(serie_rocher, product="Ferrero Rocher")
    validi = risultati.dropna(subset=["MAE"])
    assert (validi["MAE"] >= 0).all()
    assert (validi["RMSE"] >= 0).all()
    assert (validi["MAPE"] >= 0).all()


def test_selezione_sceglie_il_mape_minimo() -> None:
    risultati = pd.DataFrame(
        {
            "Metodo": ["A", "B", "C"],
            "MAE": [10.0, 5.0, 20.0],
            "RMSE": [12.0, 6.0, 25.0],
            "MAPE": [8.0, 3.0, 15.0],
        }
    )
    assert select_best_method(risultati) == "B"


def test_selezione_ripiega_su_rmse_senza_mape() -> None:
    """Fallback documentato quando il MAPE non e' calcolabile."""
    risultati = pd.DataFrame(
        {
            "Metodo": ["A", "B"],
            "MAE": [10.0, 5.0],
            "RMSE": [12.0, 6.0],
            "MAPE": [np.nan, np.nan],
        }
    )
    assert select_best_method(risultati) == "B"


def test_selezione_senza_risultati_validi() -> None:
    risultati = pd.DataFrame(
        {"Metodo": ["A"], "MAE": [np.nan], "RMSE": [np.nan], "MAPE": [np.nan]}
    )
    with pytest.raises(EvaluationError):
        select_best_method(risultati)


def test_metodi_ignorano_il_periodo_di_test(serie_rocher) -> None:
    """Alterare il test set non deve cambiare le previsioni del modello.

    Se cambiassero, il modello starebbe usando informazione futura.
    """
    alterata = serie_rocher.copy()
    alterata.iloc[36:] = alterata.iloc[36:] * 10

    originale = evaluate_methods(serie_rocher, product="X")
    from src.forecasting import run_method

    split_orig = chronological_split(serie_rocher, test_size=12)
    split_alt = chronological_split(alterata, test_size=12)
    for metodo in originale["Metodo"]:
        a = run_method(metodo, split_orig.train.to_numpy(float), 12).forecast
        b = run_method(metodo, split_alt.train.to_numpy(float), 12).forecast
        assert np.allclose(a, b)


def test_valutazione_tutti_i_prodotti(dataset) -> None:
    confronto, migliori = evaluate_all_products(dataset)
    assert len(migliori) == 4
    assert set(migliori) == set(dataset["product"].unique())
    assert confronto["Migliore"].sum() == 4


def test_prodotti_diversi_possono_avere_metodi_diversi(dataset) -> None:
    """Risultato atteso dato che i profili di domanda sono differenziati."""
    _, migliori = evaluate_all_products(dataset)
    assert len(set(migliori.values())) > 1


# ---------------------------------------------------------------------------
# Previsione finale e banda di incertezza
# ---------------------------------------------------------------------------


def test_bundle_struttura_coerente(serie_rocher) -> None:
    bundle = forecast_with_interval(
        serie_rocher, "Ferrero Rocher", "Naive stagionale", horizon=12
    )
    assert len(bundle.forecast) == 12
    assert len(bundle.future_index) == 12
    assert bundle.future_index[0] == pd.Timestamp("2026-01-01")
    assert len(bundle.train) + len(bundle.test) == len(serie_rocher)


def test_banda_contiene_la_previsione(serie_rocher) -> None:
    bundle = forecast_with_interval(
        serie_rocher, "Ferrero Rocher", "Naive stagionale", horizon=12
    )
    assert (bundle.lower <= bundle.forecast + 1e-9).all()
    assert (bundle.upper >= bundle.forecast - 1e-9).all()
    assert (bundle.lower >= 0).all()


def test_banda_piu_ampia_con_confidenza_maggiore(serie_rocher) -> None:
    stretta = forecast_with_interval(
        serie_rocher, "X", "Naive stagionale", 6, confidence_level=0.80
    )
    ampia = forecast_with_interval(
        serie_rocher, "X", "Naive stagionale", 6, confidence_level=0.99
    )
    larghezza_s = (stretta.upper - stretta.lower).mean()
    larghezza_a = (ampia.upper - ampia.lower).mean()
    assert larghezza_a > larghezza_s


def test_bundle_rifiuta_orizzonte_non_valido(serie_rocher) -> None:
    with pytest.raises(EvaluationError):
        forecast_with_interval(serie_rocher, "X", "Media mobile", horizon=0)


def test_bundle_rifiuta_confidenza_non_valida(serie_rocher) -> None:
    with pytest.raises(EvaluationError):
        forecast_with_interval(
            serie_rocher, "X", "Media mobile", 6, confidence_level=1.5
        )


def test_orizzonti_diversi_supportati(serie_nutella) -> None:
    for orizzonte in (3, 6, 12):
        bundle = forecast_with_interval(
            serie_nutella, "Nutella", "Media mobile", horizon=orizzonte
        )
        assert len(bundle.forecast) == orizzonte
