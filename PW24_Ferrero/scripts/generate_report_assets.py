"""
Generazione degli asset per la relazione finale.

Lo script esegue l'intera catena di analisi sul dataset di base e produce:

* ``report/figures/*.html``  - figure Plotly interattive e autonome (si aprono
  in qualsiasi browser, anche offline);
* ``report/results/*.csv``   - tabelle numeriche dei risultati;
* ``report/results/risultati.md`` - sintesi dei risultati in formato Markdown,
  pronta per essere inclusa nella relazione.

Esecuzione::

    python -m scripts.generate_report_assets

**Nota sulle immagini statiche**: l'esportazione in PNG richiederebbe il
pacchetto ``kaleido`` (che incorpora un browser Chromium). Per mantenere il
progetto leggero e funzionante offline su qualsiasi macchina, le figure sono
salvate in HTML autonomo; da ciascun grafico della dashboard e' comunque
possibile scaricare un PNG con il pulsante "fotocamera" della barra Plotly.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.charts import (  # noqa: E402
    chart_baseline_vs_scenario,
    chart_demand_and_forecast,
    chart_inventory_composition,
    chart_inventory_share,
    chart_method_accuracy,
    chart_products_overview,
    chart_scenario_comparison,
    chart_seasonal_profile,
)
from src.config import PRODUCT_NAMES, PRODUCTS, REPORT_DIR  # noqa: E402
from src.data_validation import load_demand_history  # noqa: E402
from src.evaluation import evaluate_all_products  # noqa: E402
from src.narrative import describe_scenario_comparison  # noqa: E402
from src.scenarios import (  # noqa: E402
    PRESET_SCENARIOS,
    ScenarioConfig,
    compare_scenarios,
    simulate_scenario,
)

FIGURES_DIR = REPORT_DIR / "figures"
RESULTS_DIR = REPORT_DIR / "results"


def _save_figure(fig, nome: str) -> Path:
    """Salva una figura Plotly come HTML autonomo."""
    percorso = FIGURES_DIR / f"{nome}.html"
    fig.write_html(str(percorso), include_plotlyjs="cdn", full_html=True)
    return percorso


def genera_figure(dataset: pd.DataFrame, esiti: Dict[str, object]) -> List[Path]:
    """Produce tutte le figure citate nella relazione."""
    salvate: List[Path] = []

    salvate.append(
        _save_figure(
            chart_products_overview(dataset, PRODUCT_NAMES), "01_panoramica_prodotti"
        )
    )

    for prodotto, esito in esiti.items():
        slug = prodotto.lower().replace(" ", "_")
        salvate.append(
            _save_figure(
                chart_seasonal_profile(esito.scenario_series, prodotto),
                f"02_profilo_stagionale_{slug}",
            )
        )
        salvate.append(
            _save_figure(
                chart_demand_and_forecast(esito.bundle),
                f"03_domanda_e_previsione_{slug}",
            )
        )
        salvate.append(
            _save_figure(
                chart_method_accuracy(esito.comparison, "MAPE", esito.best_method),
                f"04_accuratezza_metodi_{slug}",
            )
        )
        salvate.append(
            _save_figure(
                chart_inventory_composition(esito.plan),
                f"05_composizione_scorte_{slug}",
            )
        )
        salvate.append(
            _save_figure(
                chart_inventory_share(esito.plan), f"06_quota_scorte_{slug}"
            )
        )

    return salvate


def genera_confronto_scenari(prodotto: str = "Ferrero Rocher"):
    """Esegue il confronto A/B documentato nella relazione."""
    base = ScenarioConfig(product=prodotto)
    config_a = replace(
        base, name="A - Filiera stabile", **PRESET_SCENARIOS["A - Filiera stabile"]
    )
    config_b = replace(
        base,
        name="B - Filiera sotto stress",
        **PRESET_SCENARIOS["B - Filiera sotto stress"],
    )
    esito_a = simulate_scenario(config_a)
    esito_b = simulate_scenario(config_b)
    tabella = compare_scenarios(esito_a, esito_b)

    _save_figure(
        chart_scenario_comparison(tabella, config_a.name, config_b.name),
        "07_confronto_scenari",
    )
    _save_figure(
        chart_baseline_vs_scenario(
            esito_b.baseline_series, esito_b.scenario_series, prodotto
        ),
        "08_baseline_vs_scenario",
    )
    return esito_a, esito_b, tabella


def _tabella_sintesi(dataset: pd.DataFrame, confronto: pd.DataFrame, migliori: dict):
    """Tabella riassuntiva prodotto -> metodo migliore e relative metriche."""
    righe = []
    for prodotto in PRODUCT_NAMES:
        serie = dataset[dataset["product"] == prodotto]["demand"]
        riga = confronto[
            (confronto["Prodotto"] == prodotto)
            & (confronto["Metodo"] == migliori[prodotto])
        ].iloc[0]
        righe.append(
            {
                "Prodotto": prodotto,
                "Domanda media": round(serie.mean(), 0),
                "Dev. std": round(serie.std(ddof=1), 0),
                "CV (%)": round(serie.std(ddof=1) / serie.mean() * 100, 1),
                "Metodo migliore": riga["Metodo"],
                "MAE": round(riga["MAE"], 1),
                "RMSE": round(riga["RMSE"], 1),
                "MAPE (%)": round(riga["MAPE"], 2),
            }
        )
    return pd.DataFrame(righe)


def _markdown(df: pd.DataFrame) -> str:
    """Converte un DataFrame in tabella Markdown senza dipendenze esterne."""
    intestazione = "| " + " | ".join(str(c) for c in df.columns) + " |"
    separatore = "|" + "|".join("---" for _ in df.columns) + "|"
    righe = [
        "| " + " | ".join(_fmt(v) for v in riga) + " |"
        for riga in df.itertuples(index=False)
    ]
    return "\n".join([intestazione, separatore, *righe])


def _fmt(valore) -> str:
    """Formatta un valore per la tabella Markdown."""
    if isinstance(valore, bool):
        return "SI" if valore else ""
    if isinstance(valore, float):
        if pd.isna(valore):
            return "n.d."
        return f"{valore:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return str(valore)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Caricamento e validazione del dataset...")
    dataset = load_demand_history()

    print("Valutazione dei metodi previsionali su tutti i prodotti...")
    confronto, migliori = evaluate_all_products(dataset)
    confronto.to_csv(RESULTS_DIR / "confronto_metodi.csv", index=False)

    sintesi = _tabella_sintesi(dataset, confronto, migliori)
    sintesi.to_csv(RESULTS_DIR / "sintesi_prodotti.csv", index=False)

    print("Simulazione dello scenario baseline per ciascun prodotto...")
    esiti = {
        prodotto: simulate_scenario(ScenarioConfig(name="Baseline", product=prodotto))
        for prodotto in PRODUCT_NAMES
    }

    scorte = pd.DataFrame(
        [
            {
                "Prodotto": prodotto,
                # Le quantita' si arrotondano all'unita'; la copertura e'
                # espressa in mesi e richiede un decimale per restare
                # informativa (2,9 mesi e 3,4 mesi non sono equivalenti).
                **{
                    chiave: round(valore, 1 if chiave == "Copertura (mesi)" else 0)
                    for chiave, valore in esito.plan.to_dict().items()
                },
                "Metodo": esito.used_method,
            }
            for prodotto, esito in esiti.items()
        ]
    )
    scorte.to_csv(RESULTS_DIR / "piano_scorte_baseline.csv", index=False)

    print("Generazione delle figure...")
    figure = genera_figure(dataset, esiti)

    print("Confronto fra scenari A e B...")
    esito_a, esito_b, tabella_scenari = genera_confronto_scenari()
    tabella_scenari.to_csv(RESULTS_DIR / "confronto_scenari.csv", index=False)

    # --- sintesi in Markdown ---------------------------------------------
    statistiche = (
        dataset.groupby("product")["demand"]
        .agg(["count", "mean", "std", "min", "max"])
        .reindex(PRODUCT_NAMES)
        .round(1)
        .reset_index()
        .rename(
            columns={
                "product": "Prodotto",
                "count": "Osservazioni",
                "mean": "Media",
                "std": "Dev. std",
                "min": "Minimo",
                "max": "Massimo",
            }
        )
    )

    contenuto = f"""# Risultati generati automaticamente

> File prodotto da `scripts/generate_report_assets.py`.
> Dataset sintetico, seed 24. **Nessun valore rappresenta dati reali Ferrero.**

Ultima esecuzione su {len(dataset)} osservazioni
({dataset['date'].min():%Y-%m} / {dataset['date'].max():%Y-%m}).

## 1. Statistiche descrittive delle serie storiche

{_markdown(statistiche)}

## 2. Confronto dei metodi previsionali (valutazione out-of-sample)

Split cronologico: 36 mesi di addestramento, 12 mesi di test.

{_markdown(confronto[['Prodotto', 'Metodo', 'MAE', 'RMSE', 'MAPE', 'Migliore']])}

## 3. Metodo migliore per prodotto (criterio: MAPE minimo)

{_markdown(sintesi)}

## 4. Piano di scorta - scenario baseline

Parametri: lead time 2 mesi, livello di servizio 95%, periodo di riesame
1 mese, orizzonte di previsione 12 mesi.

{_markdown(scorte)}

## 5. Confronto fra scenari (prodotto: Ferrero Rocher)

- **Scenario A - Filiera stabile**: variabilita' x0,5; lead time 2 mesi; servizio 95%.
- **Scenario B - Filiera sotto stress**: variabilita' x2,0; lead time 5 mesi; servizio 99%.

{_markdown(tabella_scenari)}

### Lettura gestionale

{describe_scenario_comparison(esito_a, esito_b, tabella_scenari)}
"""
    (RESULTS_DIR / "risultati.md").write_text(contenuto, encoding="utf-8")

    print("\nCompletato.")
    print(f"  Figure HTML ....... {len(figure) + 2} in {FIGURES_DIR}")
    print(f"  Tabelle CSV ....... 4 in {RESULTS_DIR}")
    print(f"  Sintesi Markdown .. {RESULTS_DIR / 'risultati.md'}")
    print("\nMetodo migliore per prodotto:")
    for prodotto, metodo in migliori.items():
        print(f"  {prodotto:22s} -> {metodo}")


if __name__ == "__main__":
    main()
