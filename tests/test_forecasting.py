"""
Test dei metodi previsionali.

La strategia adottata e' quella di verificare i metodi su **serie
deterministiche** di cui si conosce analiticamente il risultato atteso
(serie costante, serie lineare, serie perfettamente stagionale), in modo che
i test siano stringenti e non dipendano dalla realizzazione casuale.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.forecasting import (
    METHOD_NAMES,
    METHOD_REGISTRY,
    ForecastingError,
    available_methods,
    holt_winters_additive,
    linear_trend_regression,
    moving_average_forecast,
    run_method,
    seasonal_naive_forecast,
    simple_exponential_smoothing,
)


# ---------------------------------------------------------------------------
# Proprieta' comuni a tutti i metodi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_tutti_i_metodi_restituiscono_orizzonte_corretto(nome: str, serie_rocher) -> None:
    for orizzonte in (3, 6, 12):
        risultato = run_method(nome, serie_rocher.to_numpy(float), orizzonte)
        assert len(risultato.forecast) == orizzonte


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_previsioni_finite_e_non_negative(nome: str, serie_rocher) -> None:
    risultato = run_method(nome, serie_rocher.to_numpy(float), 12)
    assert np.isfinite(risultato.forecast).all()
    assert (risultato.forecast >= 0).all()


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_fitted_allineato_alla_serie(nome: str, serie_rocher) -> None:
    """I valori interpolati devono avere la stessa lunghezza della serie."""
    risultato = run_method(nome, serie_rocher.to_numpy(float), 6)
    assert len(risultato.fitted) == len(serie_rocher)


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_serie_costante_prevista_esattamente(nome: str, serie_costante) -> None:
    """Su una serie perfettamente costante ogni metodo deve azzerare l'errore."""
    risultato = run_method(nome, serie_costante.to_numpy(float), 6)
    assert np.allclose(risultato.forecast, 500.0, atol=1e-6)


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_orizzonte_non_valido_solleva_errore(nome: str, serie_rocher) -> None:
    with pytest.raises(ForecastingError):
        run_method(nome, serie_rocher.to_numpy(float), 0)


@pytest.mark.parametrize("nome", METHOD_NAMES)
def test_valori_mancanti_sollevano_errore(nome: str) -> None:
    serie = np.full(40, 100.0)
    serie[5] = np.nan
    with pytest.raises(ForecastingError):
        run_method(nome, serie, 6)


# ---------------------------------------------------------------------------
# A) Media mobile
# ---------------------------------------------------------------------------


def test_media_mobile_calcolo_esatto() -> None:
    """La previsione e' la media esatta delle ultime N osservazioni."""
    serie = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
    risultato = moving_average_forecast(serie, horizon=3, window=3)
    assert np.allclose(risultato.forecast, 50.0)   # media di 40, 50, 60


def test_media_mobile_previsione_piatta(serie_rocher) -> None:
    risultato = moving_average_forecast(serie_rocher.to_numpy(float), 12, window=6)
    assert len(set(np.round(risultato.forecast, 6))) == 1


def test_media_mobile_finestra_piu_ampia_e_piu_liscia(serie_rocher) -> None:
    """Finestre ampie reagiscono meno agli ultimi mesi (serie stagionale)."""
    valori = serie_rocher.to_numpy(float)
    stretta = moving_average_forecast(valori, 6, window=3).forecast[0]
    ampia = moving_average_forecast(valori, 6, window=12).forecast[0]
    media_globale = valori.mean()
    assert abs(ampia - media_globale) < abs(stretta - media_globale)


def test_media_mobile_fitted_non_usa_il_futuro() -> None:
    """Il fitted al tempo t deve dipendere solo dalle osservazioni precedenti."""
    serie = np.array([10.0, 20.0, 30.0, 999.0, 50.0])
    risultato = moving_average_forecast(serie, horizon=1, window=2)
    assert risultato.fitted[3] == pytest.approx(25.0)   # media di 20 e 30
    assert np.isnan(risultato.fitted[:2]).all()


def test_media_mobile_finestra_non_valida(serie_rocher) -> None:
    with pytest.raises(ForecastingError):
        moving_average_forecast(serie_rocher.to_numpy(float), 6, window=0)


def test_media_mobile_finestra_piu_lunga_della_serie() -> None:
    with pytest.raises(ForecastingError):
        moving_average_forecast(np.arange(5, dtype=float), 3, window=12)


# ---------------------------------------------------------------------------
# B) Smorzamento esponenziale
# ---------------------------------------------------------------------------


def test_smorzamento_alpha_unitario_equivale_al_naive() -> None:
    """Con alpha = 1 il livello coincide sempre con l'ultima osservazione."""
    serie = np.array([10.0, 20.0, 30.0, 45.0])
    risultato = simple_exponential_smoothing(serie, horizon=4, alpha=1.0)
    assert np.allclose(risultato.forecast, 45.0)


def test_smorzamento_ricorsione_esatta() -> None:
    """Verifica numerica della ricorsione L(t) = a*y(t) + (1-a)*L(t-1)."""
    serie = np.array([100.0, 200.0, 300.0])
    risultato = simple_exponential_smoothing(serie, horizon=1, alpha=0.5)
    # L0 = 100 ; L1 = 0.5*200 + 0.5*100 = 150 ; L2 = 0.5*300 + 0.5*150 = 225
    assert risultato.forecast[0] == pytest.approx(225.0)


def test_smorzamento_previsione_piatta(serie_nutella) -> None:
    risultato = simple_exponential_smoothing(serie_nutella.to_numpy(float), 12, alpha=0.3)
    assert len(set(np.round(risultato.forecast, 6))) == 1


def test_smorzamento_alpha_alto_piu_reattivo() -> None:
    """Un alpha alto segue piu' da vicino un salto di livello recente."""
    serie = np.concatenate([np.full(20, 100.0), np.full(4, 500.0)])
    lento = simple_exponential_smoothing(serie, 1, alpha=0.1).forecast[0]
    rapido = simple_exponential_smoothing(serie, 1, alpha=0.9).forecast[0]
    assert rapido > lento
    assert rapido == pytest.approx(500.0, rel=0.02)


@pytest.mark.parametrize("alpha", [0.0, -0.1, 1.5])
def test_smorzamento_alpha_fuori_intervallo(alpha: float, serie_nutella) -> None:
    with pytest.raises(ForecastingError):
        simple_exponential_smoothing(serie_nutella.to_numpy(float), 6, alpha=alpha)


# ---------------------------------------------------------------------------
# C) Regressione lineare
# ---------------------------------------------------------------------------


def test_regressione_recupera_la_retta_esatta(serie_lineare) -> None:
    """Su una serie perfettamente lineare il fit deve essere esatto."""
    valori = serie_lineare.to_numpy(float)
    risultato = linear_trend_regression(valori, horizon=6)
    assert risultato.params["pendenza"] == pytest.approx(10.0)
    assert risultato.params["intercetta"] == pytest.approx(1000.0)
    attese = 1000.0 + 10.0 * np.arange(48, 54)
    assert np.allclose(risultato.forecast, attese)


def test_regressione_residui_nulli_su_serie_lineare(serie_lineare) -> None:
    risultato = linear_trend_regression(serie_lineare.to_numpy(float), 3)
    assert np.allclose(risultato.fitted, serie_lineare.to_numpy(float))


def test_regressione_tronca_a_zero() -> None:
    """Un trend fortemente negativo non deve produrre previsioni negative."""
    serie = np.linspace(1000.0, 10.0, 24)
    risultato = linear_trend_regression(serie, horizon=36)
    assert (risultato.forecast >= 0).all()


def test_regressione_coglie_il_trend(serie_lineare) -> None:
    risultato = linear_trend_regression(serie_lineare.to_numpy(float), 12)
    assert risultato.forecast[-1] > risultato.forecast[0]


def test_regressione_serie_troppo_corta() -> None:
    with pytest.raises(ForecastingError):
        linear_trend_regression(np.array([1.0, 2.0]), horizon=3)


# ---------------------------------------------------------------------------
# D) Naive stagionale
# ---------------------------------------------------------------------------


def test_naive_stagionale_ripete_lultimo_ciclo() -> None:
    ciclo = np.arange(1.0, 13.0)
    serie = np.concatenate([ciclo, ciclo * 2.0])
    risultato = seasonal_naive_forecast(serie, horizon=12, period=12)
    assert np.allclose(risultato.forecast, ciclo * 2.0)


def test_naive_stagionale_oltre_un_ciclo() -> None:
    """Oltre il periodo, la previsione si ripete ciclicamente."""
    ciclo = np.arange(1.0, 13.0)
    serie = np.concatenate([ciclo, ciclo])
    risultato = seasonal_naive_forecast(serie, horizon=18, period=12)
    assert np.allclose(risultato.forecast[12:], ciclo[:6])


def test_naive_stagionale_serie_troppo_corta() -> None:
    with pytest.raises(ForecastingError):
        seasonal_naive_forecast(np.arange(10, dtype=float), horizon=6, period=12)


def test_naive_stagionale_periodo_non_valido(serie_rocher) -> None:
    with pytest.raises(ForecastingError):
        seasonal_naive_forecast(serie_rocher.to_numpy(float), 6, period=0)


# ---------------------------------------------------------------------------
# E) Holt-Winters
# ---------------------------------------------------------------------------


def test_holt_winters_ricostruisce_trend_e_stagionalita() -> None:
    """Su una serie costruita come trend + stagionalita' l'errore e' piccolo."""
    t = np.arange(48, dtype=float)
    stagione = 50.0 * np.sin(2.0 * np.pi * t / 12.0)
    serie = 1000.0 + 5.0 * t + stagione

    risultato = holt_winters_additive(serie[:36], horizon=12)
    attesi = serie[36:]
    errore_relativo = np.mean(np.abs(risultato.forecast - attesi) / attesi)
    assert errore_relativo < 0.05


def test_holt_winters_batte_la_media_mobile_su_serie_stagionale(serie_rocher) -> None:
    """Su una serie fortemente stagionale deve superare un metodo piatto."""
    valori = serie_rocher.to_numpy(float)
    train, test = valori[:36], valori[36:]

    hw = holt_winters_additive(train, horizon=12).forecast
    mm = moving_average_forecast(train, horizon=12, window=3).forecast

    assert np.mean(np.abs(hw - test)) < np.mean(np.abs(mm - test))


def test_holt_winters_richiede_due_cicli_completi() -> None:
    with pytest.raises(ForecastingError):
        holt_winters_additive(np.arange(20, dtype=float), horizon=6, period=12)


@pytest.mark.parametrize(
    "parametri",
    [{"alpha": 1.5}, {"beta": -0.1}, {"gamma": 2.0}],
)
def test_holt_winters_parametri_fuori_intervallo(parametri, serie_rocher) -> None:
    with pytest.raises(ForecastingError):
        holt_winters_additive(serie_rocher.to_numpy(float), 6, **parametri)


def test_holt_winters_periodo_non_valido(serie_rocher) -> None:
    with pytest.raises(ForecastingError):
        holt_winters_additive(serie_rocher.to_numpy(float), 6, period=1)


# ---------------------------------------------------------------------------
# Registro dei metodi
# ---------------------------------------------------------------------------


def test_registro_contiene_i_metodi_obbligatori() -> None:
    """La specifica richiede almeno media mobile, smorzamento e regressione."""
    assert "Media mobile" in METHOD_REGISTRY
    assert "Smorzamento esponenziale" in METHOD_REGISTRY
    assert "Regressione lineare" in METHOD_REGISTRY
    assert len(METHOD_REGISTRY) >= 3


def test_metodo_sconosciuto_solleva_errore(serie_rocher) -> None:
    with pytest.raises(ForecastingError, match="non riconosciuto"):
        run_method("Rete neurale", serie_rocher.to_numpy(float), 6)


def test_run_method_ignora_parametri_non_pertinenti(serie_rocher) -> None:
    """Passare 'alpha' alla media mobile non deve generare errori."""
    risultato = run_method(
        "Media mobile", serie_rocher.to_numpy(float), 6, {"alpha": 0.5, "window": 6}
    )
    assert risultato.params["window"] == 6.0


def test_metodi_disponibili_filtrano_per_lunghezza() -> None:
    corti = available_methods(n_observations=15, period=12)
    assert "Holt-Winters additivo" not in corti
    assert "Naive stagionale" in corti

    lunghi = available_methods(n_observations=36, period=12)
    assert "Holt-Winters additivo" in lunghi
    assert len(lunghi) == len(METHOD_NAMES)


def test_residui_calcolati_correttamente(serie_lineare) -> None:
    valori = serie_lineare.to_numpy(float)
    risultato = linear_trend_regression(valori, 3)
    assert np.allclose(risultato.residuals, valori - risultato.fitted)
