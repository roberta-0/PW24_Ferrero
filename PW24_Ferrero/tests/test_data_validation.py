"""
Test del livello di validazione dei dati.

Ogni controllo previsto dalla specifica e' verificato con un dataset
volutamente corrotto, accertando che l'errore venga intercettato e che il
messaggio restituito sia in italiano e comprensibile.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_validation import (
    DataValidationError,
    load_demand_history,
    validate_demand_dataframe,
)


@pytest.fixture
def dataset_valido(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset.copy()


# ---------------------------------------------------------------------------
# Dataset valido
# ---------------------------------------------------------------------------


def test_dataset_generato_supera_la_validazione(dataset_valido) -> None:
    report = validate_demand_dataframe(dataset_valido)
    assert report.is_valid
    assert report.errors == []


def test_caricamento_dal_csv_di_progetto() -> None:
    """Il file versionato nel repository deve essere valido."""
    caricato = load_demand_history()
    assert len(caricato) == 192
    assert caricato["product"].nunique() == 4
    assert pd.api.types.is_datetime64_any_dtype(caricato["date"])


# ---------------------------------------------------------------------------
# Controlli strutturali
# ---------------------------------------------------------------------------


def test_colonne_mancanti(dataset_valido) -> None:
    report = validate_demand_dataframe(dataset_valido.drop(columns=["demand"]))
    assert not report.is_valid
    assert any("Colonne obbligatorie mancanti" in e for e in report.errors)
    assert any("demand" in e for e in report.errors)


def test_dataset_vuoto() -> None:
    report = validate_demand_dataframe(pd.DataFrame())
    assert not report.is_valid
    assert any("vuoto" in e.lower() for e in report.errors)


def test_valori_mancanti(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto.loc[5, "demand"] = np.nan
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("valori mancanti" in e.lower() for e in report.errors)


def test_date_duplicate(dataset_valido) -> None:
    corrotto = pd.concat([dataset_valido, dataset_valido.iloc[[0]]], ignore_index=True)
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("duplicata" in e.lower() for e in report.errors)


def test_domanda_negativa(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto.loc[10, "demand"] = -500
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("negativ" in e.lower() for e in report.errors)


def test_prodotto_non_in_anagrafica(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto.loc[0, "product"] = "Cioccolato Fittizio"
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("non previsti in anagrafica" in e for e in report.errors)


def test_formato_data_non_valido(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto["date"] = corrotto["date"].astype(str)
    corrotto.loc[3, "date"] = "data-non-valida"
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("formato non valido" in e.lower() for e in report.errors)


def test_domanda_non_numerica(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto["demand"] = corrotto["demand"].astype(object)
    corrotto.loc[2, "demand"] = "molti cartoni"
    report = validate_demand_dataframe(corrotto)
    assert not report.is_valid
    assert any("non numerici" in e.lower() for e in report.errors)


def test_osservazioni_insufficienti(dataset_valido) -> None:
    corto = dataset_valido[dataset_valido["product"] == "Nutella"].head(10)
    report = validate_demand_dataframe(corto)
    assert not report.is_valid
    assert any("osservazioni" in e.lower() for e in report.errors)


def test_serie_non_continua(dataset_valido) -> None:
    """Un mese mancante al centro della serie deve essere intercettato."""
    nutella = dataset_valido[dataset_valido["product"] == "Nutella"]
    con_buco = nutella.drop(nutella.index[20])
    report = validate_demand_dataframe(con_buco)
    assert not report.is_valid
    assert any("non e' continua" in e for e in report.errors)


# ---------------------------------------------------------------------------
# Segnalazioni non bloccanti
# ---------------------------------------------------------------------------


def test_domanda_nulla_genera_solo_segnalazione(dataset_valido) -> None:
    """Zero e' un valore ammissibile ma rilevante per il calcolo del MAPE."""
    corrotto = dataset_valido.copy()
    corrotto.loc[7, "demand"] = 0
    report = validate_demand_dataframe(corrotto)
    assert report.is_valid
    assert any("MAPE" in w for w in report.warnings)


def test_prodotto_assente_genera_segnalazione(dataset_valido) -> None:
    parziale = dataset_valido[dataset_valido["product"] != "Nutella"]
    report = validate_demand_dataframe(parziale)
    assert report.is_valid
    assert any("assenti dal dataset" in w for w in report.warnings)


# ---------------------------------------------------------------------------
# Gestione degli errori e messaggi
# ---------------------------------------------------------------------------


def test_raise_if_invalid_solleva_eccezione(dataset_valido) -> None:
    corrotto = dataset_valido.copy()
    corrotto.loc[0, "demand"] = -1
    report = validate_demand_dataframe(corrotto)
    with pytest.raises(DataValidationError):
        report.raise_if_invalid()


def test_messaggio_formattato_multiriga() -> None:
    errore = DataValidationError(["Primo problema.", "Secondo problema."])
    testo = errore.formatted()
    assert testo.count("\n") == 1
    assert testo.startswith("- ")


def test_file_inesistente(tmp_path) -> None:
    with pytest.raises(DataValidationError) as info:
        load_demand_history(tmp_path / "non_esiste.csv")
    messaggio = str(info.value)
    assert "non trovato" in messaggio
    assert "src.data_generator" in messaggio   # suggerisce la soluzione


def test_csv_vuoto(tmp_path) -> None:
    percorso = tmp_path / "vuoto.csv"
    percorso.write_text("", encoding="utf-8")
    with pytest.raises(DataValidationError, match="vuoto"):
        load_demand_history(percorso)


def test_csv_malformato(tmp_path) -> None:
    """Un CSV con struttura incoerente non deve propagare un traceback."""
    percorso = tmp_path / "rotto.csv"
    percorso.write_text(
        "date,product,demand\n2022-01-01,Nutella\n2022-02-01,Nutella,100\n",
        encoding="utf-8",
    )
    with pytest.raises(DataValidationError):
        load_demand_history(percorso)


def test_csv_con_dati_non_validi(tmp_path) -> None:
    percorso = tmp_path / "negativi.csv"
    righe = ["date,product,demand"]
    for i in range(30):
        mese = pd.Timestamp("2022-01-01") + pd.DateOffset(months=i)
        righe.append(f"{mese:%Y-%m-%d},Nutella,{-100 if i == 3 else 1000}")
    percorso.write_text("\n".join(righe), encoding="utf-8")

    with pytest.raises(DataValidationError) as info:
        load_demand_history(percorso)
    assert "negativ" in str(info.value).lower()


def test_tutti_i_messaggi_sono_in_italiano(dataset_valido) -> None:
    """Controllo trasversale: nessun messaggio tecnico in inglese."""
    casi = [
        dataset_valido.drop(columns=["demand"]),
        dataset_valido.assign(demand=lambda d: d["demand"] * -1),
        dataset_valido.head(5),
    ]
    parole_italiane = (
        "mancant", "negativ", "osservazioni", "colonne", "prodott", "serie", "dataset"
    )
    for caso in casi:
        report = validate_demand_dataframe(caso)
        for errore in report.errors:
            assert any(p in errore.lower() for p in parole_italiane), errore
