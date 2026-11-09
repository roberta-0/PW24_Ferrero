"""
Livello di validazione dei dati di domanda.

Il modulo verifica che il dataset caricato rispetti i vincoli strutturali e
di dominio richiesti dall'applicazione, producendo messaggi di errore in
italiano comprensibili all'utente finale (nessun traceback Python esposto in
dashboard).

Controlli implementati
----------------------
1. presenza delle colonne obbligatorie;
2. formato delle date non valido / non interpretabile;
3. valori mancanti;
4. date duplicate per uno stesso prodotto;
5. domanda negativa o nulla;
6. prodotti non previsti in anagrafica;
7. numero di osservazioni sufficiente;
8. continuita' mensile della serie (nessun mese mancante).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

import pandas as pd

from .config import (
    DEMAND_HISTORY_CSV,
    MIN_OBSERVATIONS,
    PRODUCT_NAMES,
)

__all__ = [
    "DataValidationError",
    "ValidationReport",
    "validate_demand_dataframe",
    "load_demand_history",
]

REQUIRED_COLUMNS: Sequence[str] = ("date", "product", "demand")


class DataValidationError(Exception):
    """Errore di validazione con messaggio in italiano per l'utente finale."""

    def __init__(self, messages: Sequence[str]) -> None:
        self.messages: List[str] = list(messages)
        super().__init__(" | ".join(self.messages))

    def formatted(self) -> str:
        """Messaggio multi-riga pronto per essere mostrato in dashboard."""
        return "\n".join(f"- {m}" for m in self.messages)


@dataclass
class ValidationReport:
    """Esito della validazione: errori bloccanti e segnalazioni non bloccanti."""

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """``True`` se non sono stati rilevati errori bloccanti."""
        return not self.errors

    def raise_if_invalid(self) -> None:
        """Solleva :class:`DataValidationError` se la validazione e' fallita."""
        if self.errors:
            raise DataValidationError(self.errors)


def _check_columns(df: pd.DataFrame, report: ValidationReport) -> bool:
    """Verifica la presenza delle colonne obbligatorie."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        report.errors.append(
            "Colonne obbligatorie mancanti nel dataset: "
            + ", ".join(missing)
            + ". Sono richieste le colonne 'date', 'product' e 'demand'."
        )
        return False
    return True


def _coerce_types(df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
    """Converte le colonne nei tipi attesi, segnalando i valori non validi."""
    out = df.copy()

    parsed = pd.to_datetime(out["date"], errors="coerce", format="mixed")
    invalid_dates = int(parsed.isna().sum()) - int(out["date"].isna().sum())
    if invalid_dates > 0:
        report.errors.append(
            f"Rilevate {invalid_dates} date in formato non valido: "
            "e' atteso il formato 'AAAA-MM-GG'."
        )
    out["date"] = parsed

    numeric = pd.to_numeric(out["demand"], errors="coerce")
    invalid_demand = int(numeric.isna().sum()) - int(out["demand"].isna().sum())
    if invalid_demand > 0:
        report.errors.append(
            f"Rilevati {invalid_demand} valori di domanda non numerici: "
            "la colonna 'demand' deve contenere solo numeri."
        )
    out["demand"] = numeric

    out["product"] = out["product"].astype("string")
    return out


def _check_missing_values(df: pd.DataFrame, report: ValidationReport) -> None:
    """Segnala i valori mancanti nelle colonne obbligatorie."""
    for column, label in (
        ("date", "data"),
        ("product", "prodotto"),
        ("demand", "domanda"),
    ):
        n_missing = int(df[column].isna().sum())
        if n_missing > 0:
            report.errors.append(
                f"Sono presenti {n_missing} valori mancanti nella colonna "
                f"'{column}' ({label}). Il dataset deve essere completo."
            )


def _check_duplicates(df: pd.DataFrame, report: ValidationReport) -> None:
    """Segnala coppie (prodotto, data) duplicate."""
    subset = df.dropna(subset=["date", "product"])
    duplicated = subset.duplicated(subset=["product", "date"], keep=False)
    if duplicated.any():
        examples = (
            subset.loc[duplicated, ["product", "date"]]
            .drop_duplicates()
            .head(3)
            .apply(lambda r: f"{r['product']} - {r['date']:%Y-%m}", axis=1)
            .tolist()
        )
        report.errors.append(
            f"Rilevate {int(duplicated.sum())} righe con data duplicata per lo "
            "stesso prodotto (es.: " + "; ".join(examples) + "). "
            "Ogni prodotto deve avere una sola osservazione per mese."
        )


def _check_demand_domain(df: pd.DataFrame, report: ValidationReport) -> None:
    """Verifica che la domanda sia positiva e verosimile."""
    demand = df["demand"].dropna()

    negative = int((demand < 0).sum())
    if negative > 0:
        report.errors.append(
            f"Rilevati {negative} valori di domanda negativi. "
            "La domanda non puo' assumere valori inferiori a zero."
        )

    zeros = int((demand == 0).sum())
    if zeros > 0:
        report.warnings.append(
            f"Rilevati {zeros} mesi con domanda pari a zero: il MAPE verra' "
            "calcolato escludendo tali osservazioni (cfr. documentazione)."
        )


def _check_products(
    df: pd.DataFrame,
    report: ValidationReport,
    expected_products: Sequence[str],
) -> None:
    """Verifica che i prodotti presenti appartengano all'anagrafica."""
    present = set(df["product"].dropna().unique())
    unexpected = sorted(present - set(expected_products))
    if unexpected:
        report.errors.append(
            "Prodotti non previsti in anagrafica: "
            + ", ".join(unexpected)
            + ". Prodotti ammessi: "
            + ", ".join(expected_products)
            + "."
        )

    missing = sorted(set(expected_products) - present)
    if missing:
        report.warnings.append(
            "Prodotti dell'anagrafica assenti dal dataset: " + ", ".join(missing) + "."
        )


def _check_length_and_continuity(
    df: pd.DataFrame,
    report: ValidationReport,
    min_observations: int,
) -> None:
    """Verifica numerosita' minima e continuita' mensile per ogni prodotto."""
    subset = df.dropna(subset=["date", "product"])
    for product, group in subset.groupby("product", observed=True):
        n_obs = len(group)
        if n_obs < min_observations:
            report.errors.append(
                f"Il prodotto '{product}' ha solo {n_obs} osservazioni: "
                f"ne servono almeno {min_observations} per eseguire "
                "l'analisi previsionale."
            )
            continue

        dates = pd.DatetimeIndex(group["date"].sort_values())
        expected = pd.date_range(start=dates[0], end=dates[-1], freq="MS")
        if len(expected) != len(dates) or not expected.equals(
            pd.DatetimeIndex(dates.to_period("M").to_timestamp())
        ):
            gaps = sorted(set(expected) - set(dates.to_period("M").to_timestamp()))
            if gaps:
                shown = ", ".join(f"{d:%Y-%m}" for d in gaps[:5])
                report.errors.append(
                    f"La serie del prodotto '{product}' non e' continua su base "
                    f"mensile: mancano {len(gaps)} mesi (es.: {shown})."
                )


def validate_demand_dataframe(
    df: pd.DataFrame,
    expected_products: Optional[Sequence[str]] = None,
    min_observations: int = MIN_OBSERVATIONS,
) -> ValidationReport:
    """Esegue tutti i controlli di validita' sul dataset di domanda.

    Parameters
    ----------
    df:
        DataFrame da validare.
    expected_products:
        Elenco dei prodotti ammessi; di default l'anagrafica di progetto.
    min_observations:
        Numero minimo di osservazioni mensili per prodotto.

    Returns
    -------
    ValidationReport
        Report con errori bloccanti ed eventuali segnalazioni.
    """
    expected_products = (
        list(expected_products) if expected_products is not None else PRODUCT_NAMES
    )
    report = ValidationReport()

    if df is None or len(df) == 0:
        report.errors.append(
            "Il dataset e' vuoto: non e' possibile effettuare alcuna analisi."
        )
        return report

    if not _check_columns(df, report):
        # Senza le colonne obbligatorie gli altri controlli non sono eseguibili.
        return report

    typed = _coerce_types(df, report)
    _check_missing_values(typed, report)
    _check_duplicates(typed, report)
    _check_demand_domain(typed, report)
    _check_products(typed, report, expected_products)
    _check_length_and_continuity(typed, report, min_observations)

    return report


def load_demand_history(
    path: Path = DEMAND_HISTORY_CSV,
    validate: bool = True,
    min_observations: int = MIN_OBSERVATIONS,
) -> pd.DataFrame:
    """Carica e valida il dataset storico di domanda da file CSV.

    Parameters
    ----------
    path:
        Percorso del file CSV in formato lungo.
    validate:
        Se ``True`` esegue la validazione e solleva errore in caso di problemi.
    min_observations:
        Numero minimo di osservazioni mensili per prodotto.

    Raises
    ------
    DataValidationError
        Se il file non esiste, non e' leggibile oppure non supera i controlli.
    """
    path = Path(path)

    if not path.exists():
        raise DataValidationError(
            [
                f"File dei dati non trovato: '{path}'. "
                "Rigenerare il dataset con il comando "
                "'python -m src.data_generator'."
            ]
        )

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise DataValidationError([f"Il file '{path.name}' e' vuoto."]) from exc
    except pd.errors.ParserError as exc:
        raise DataValidationError(
            [
                f"Il file '{path.name}' non e' un CSV valido e non puo' essere "
                "interpretato. Verificare il separatore e la struttura delle "
                "colonne, oppure rigenerare il dataset."
            ]
        ) from exc
    except OSError as exc:
        raise DataValidationError(
            [f"Impossibile leggere il file '{path}': {exc.strerror}."]
        ) from exc

    if validate:
        report = validate_demand_dataframe(df, min_observations=min_observations)
        report.raise_if_invalid()

    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df["demand"] = pd.to_numeric(df["demand"])
    df["product"] = df["product"].astype(str)
    return df.sort_values(["product", "date"]).reset_index(drop=True)
