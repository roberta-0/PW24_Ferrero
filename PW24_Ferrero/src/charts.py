"""
Costruzione dei grafici Plotly.

Tutti i grafici della dashboard sono definiti qui: titoli, etichette degli
assi, legende e tooltip sono in italiano e includono l'unita' di misura.
Separare la visualizzazione dall'interfaccia permette di riusare le stesse
figure per esportare le immagini della relazione finale.

Scelte di rappresentazione
--------------------------
* le scale degli assi partono da zero quando il confronto riguarda quantita'
  assolute, per non amplificare visivamente differenze modeste;
* la banda di incertezza e' resa come area semitrasparente, mai come linea
  piena, per non essere confusa con una previsione puntuale;
* periodo di addestramento, periodo di test e previsione hanno colori e
  stili di linea distinti, come richiesto dalla specifica PW24.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import pandas as pd
import plotly.graph_objects as go

from .config import MONTH_NAMES_IT, STOCK_LABELS_IT
from .evaluation import ForecastBundle
from .inventory import InventoryPlan

__all__ = [
    "COLORS",
    "chart_demand_and_forecast",
    "chart_method_accuracy",
    "chart_inventory_composition",
    "chart_inventory_share",
    "chart_scenario_comparison",
    "chart_seasonal_profile",
    "chart_products_overview",
    "chart_baseline_vs_scenario",
]

#: Palette coerente in tutta la dashboard.
COLORS: Dict[str, str] = {
    "train": "#1f4e79",        # blu scuro - periodo di addestramento
    "test": "#2e8b57",         # verde - periodo di test (valori osservati)
    "test_forecast": "#e67e22",  # arancio - previsione sul test
    "forecast": "#c0392b",     # rosso - previsione futura
    "band": "rgba(192,57,43,0.15)",
    "baseline": "#95a5a6",     # grigio - serie di base
    "scenario": "#8e44ad",     # viola - serie di scenario
    "cycle_stock": "#4e79a7",
    "safety_stock": "#f28e2b",
    "anticipation_stock": "#59a14f",
    "pipeline_stock": "#b07aa1",
}

# Il margine superiore e' ampio perche' i titoli sono su due righe (titolo +
# sottotitolo) e la legenda orizzontale va collocata fra titolo e area del
# grafico senza sovrapposizioni.
_LAYOUT = dict(
    template="plotly_white",
    hovermode="x unified",
    margin=dict(l=70, r=30, t=105, b=60),
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
)


def _title(text: str, subtitle: Optional[str] = None) -> Dict[str, object]:
    """Titolo allineato a sinistra, con sottotitolo opzionale su seconda riga."""
    testo = f"{text}<br><sub>{subtitle}</sub>" if subtitle else text
    return dict(text=testo, x=0.0, xanchor="left", y=0.97, yanchor="top")


# ---------------------------------------------------------------------------
# Sezione 2 - Domanda storica e prevista
# ---------------------------------------------------------------------------


def chart_demand_and_forecast(
    bundle: ForecastBundle,
    unit: str = "cartoni",
    show_band: bool = True,
) -> go.Figure:
    """Grafico principale: storico (train/test), previsione e banda.

    Il grafico distingue visivamente le quattro informazioni richieste dalla
    specifica: periodo di addestramento, periodo di test, previsione sul test
    (per valutare l'accuratezza a vista) e previsione futura.
    """
    fig = go.Figure()

    # Periodo di addestramento
    fig.add_trace(
        go.Scatter(
            x=bundle.train.index,
            y=bundle.train.to_numpy(),
            mode="lines+markers",
            name="Domanda storica - addestramento",
            line=dict(color=COLORS["train"], width=2),
            marker=dict(size=4),
            hovertemplate="%{x|%b %Y}<br>Domanda: %{y:,.0f} " + unit + "<extra></extra>",
        )
    )

    # Periodo di test (osservato). Si aggancia all'ultimo punto di training
    # per evitare un'interruzione visiva della linea.
    test_x = [bundle.train.index[-1], *bundle.test.index]
    test_y = [bundle.train.iloc[-1], *bundle.test.to_numpy()]
    fig.add_trace(
        go.Scatter(
            x=test_x,
            y=test_y,
            mode="lines+markers",
            name="Domanda storica - test (osservata)",
            line=dict(color=COLORS["test"], width=2),
            marker=dict(size=5),
            hovertemplate="%{x|%b %Y}<br>Osservato: %{y:,.0f} " + unit + "<extra></extra>",
        )
    )

    # Previsione sul periodo di test
    fig.add_trace(
        go.Scatter(
            x=bundle.test_forecast.index,
            y=bundle.test_forecast.to_numpy(),
            mode="lines",
            name="Previsione sul periodo di test",
            line=dict(color=COLORS["test_forecast"], width=2, dash="dot"),
            hovertemplate="%{x|%b %Y}<br>Previsto (test): %{y:,.0f} " + unit + "<extra></extra>",
        )
    )

    # Banda di incertezza empirica
    if show_band:
        band_x = list(bundle.future_index) + list(bundle.future_index[::-1])
        band_y = list(bundle.upper.to_numpy()) + list(bundle.lower.to_numpy()[::-1])
        fig.add_trace(
            go.Scatter(
                x=band_x,
                y=band_y,
                fill="toself",
                fillcolor=COLORS["band"],
                line=dict(width=0),
                name=f"Banda empirica {bundle.confidence_level:.0%}",
                hoverinfo="skip",
                showlegend=True,
            )
        )

    # Previsione futura, agganciata all'ultimo dato storico
    forecast_x = [bundle.test.index[-1], *bundle.future_index]
    forecast_y = [bundle.test.iloc[-1], *bundle.forecast.to_numpy()]
    fig.add_trace(
        go.Scatter(
            x=forecast_x,
            y=forecast_y,
            mode="lines+markers",
            name="Previsione futura",
            line=dict(color=COLORS["forecast"], width=3),
            marker=dict(size=6, symbol="diamond"),
            hovertemplate="%{x|%b %Y}<br>Previsto: %{y:,.0f} " + unit + "<extra></extra>",
        )
    )

    # Linee verticali di separazione dei periodi. Shape e annotazione sono
    # aggiunte separatamente: 'add_vline' con annotazione non gestisce
    # correttamente gli assi temporali basati su pandas.Timestamp.
    for data_limite, etichetta in (
        (bundle.train.index[-1], "inizio test"),
        (bundle.test.index[-1], "inizio previsione"),
    ):
        fig.add_shape(
            type="line",
            x0=data_limite,
            x1=data_limite,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="#7f8c8d", width=1, dash="dash"),
        )
        fig.add_annotation(
            x=data_limite,
            y=1.0,
            yref="paper",
            text=etichetta,
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(size=11, color="#7f8c8d"),
        )

    fig.update_layout(
        title=_title(
            f"Domanda storica e prevista - {bundle.product}",
            f"Metodo: {bundle.method_label}",
        ),
        xaxis_title="Mese",
        yaxis_title=f"Domanda ({unit}/mese)",
        **_LAYOUT,
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f")
    return fig


# ---------------------------------------------------------------------------
# Sezione 3 - Confronto dei metodi previsionali
# ---------------------------------------------------------------------------


def chart_method_accuracy(
    comparison: pd.DataFrame,
    metric: str = "MAPE",
    best_method: Optional[str] = None,
) -> go.Figure:
    """Grafico a barre dell'accuratezza dei metodi sul periodo di test.

    Il metodo migliore e' evidenziato cromaticamente: la lettura e' immediata
    e il criterio di selezione resta trasparente.
    """
    data = comparison.dropna(subset=[metric]).sort_values(metric)
    unit = "%" if metric in ("MAPE", "sMAPE") else "unita'"

    colors = [
        COLORS["forecast"] if m == best_method else COLORS["train"]
        for m in data["Metodo"]
    ]

    fig = go.Figure(
        go.Bar(
            x=data["Metodo"],
            y=data[metric],
            marker_color=colors,
            text=[f"{v:,.2f}" for v in data[metric]],
            textposition="outside",
            hovertemplate="%{x}<br>" + metric + ": %{y:,.2f} " + unit + "<extra></extra>",
            name=metric,
        )
    )
    fig.update_layout(
        title=_title(
            f"Accuratezza dei metodi previsionali - {metric} (piu' basso = migliore)",
            "Valutazione out-of-sample sul periodo di test",
        ),
        xaxis_title="Metodo previsionale",
        yaxis_title=f"{metric} ({unit})",
        showlegend=False,
        **_LAYOUT,
    )
    fig.update_yaxes(rangemode="tozero")
    return fig


# ---------------------------------------------------------------------------
# Sezione 4 - Composizione delle scorte
# ---------------------------------------------------------------------------


def chart_inventory_composition(
    plan: InventoryPlan,
    unit: str = "cartoni",
) -> go.Figure:
    """Barra impilata con le quattro componenti della scorta totale."""
    fig = go.Figure()
    total = plan.total_stock

    for key, value in plan.components.items():
        share = value / total * 100.0 if total > 0 else 0.0
        fig.add_trace(
            go.Bar(
                x=[plan.product],
                y=[value],
                name=STOCK_LABELS_IT[key],
                marker_color=COLORS[key],
                text=[f"{value:,.0f}<br>({share:.1f}%)"],
                textposition="inside",
                hovertemplate=(
                    STOCK_LABELS_IT[key]
                    + "<br>%{y:,.0f} "
                    + unit
                    + f"<br>Quota: {share:.1f}%<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        barmode="stack",
        title=_title(
            f"Composizione della scorta totale - {plan.product}",
            f"Scorta totale: {total:,.0f} {unit} "
            f"({plan.coverage_months:.1f} mesi di copertura)",
        ),
        xaxis_title="Prodotto",
        yaxis_title=f"Scorta ({unit})",
        **_LAYOUT,
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f")
    return fig


def chart_inventory_share(plan: InventoryPlan) -> go.Figure:
    """Grafico ad anello con il peso percentuale di ciascuna componente."""
    labels = [STOCK_LABELS_IT[k] for k in plan.components]
    values = list(plan.components.values())
    colors = [COLORS[k] for k in plan.components]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker=dict(colors=colors),
            textinfo="label+percent",
            hovertemplate="%{label}<br>%{value:,.0f} cartoni<br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        title=_title("Peso percentuale delle componenti di scorta"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=70, b=20),
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Sezione 7 - Confronto fra scenari
# ---------------------------------------------------------------------------


def chart_scenario_comparison(
    comparison: pd.DataFrame,
    name_a: str,
    name_b: str,
    unit: str = "cartoni",
) -> go.Figure:
    """Barre affiancate di confronto fra due scenari sulle voci di scorta."""
    rows = comparison[comparison["Indicatore"].str.contains("Scorta")]

    fig = go.Figure()
    for name, color in ((name_a, COLORS["train"]), (name_b, COLORS["forecast"])):
        fig.add_trace(
            go.Bar(
                x=rows["Indicatore"].str.replace(r" \(unita'\)", "", regex=True),
                y=rows[name],
                name=name,
                marker_color=color,
                text=[f"{v:,.0f}" for v in rows[name]],
                textposition="outside",
                hovertemplate="%{x}<br>" + name + ": %{y:,.0f} " + unit + "<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="group",
        title=_title(
            "Confronto fra scenari - componenti di scorta",
            "Barre affiancate: stesso prodotto, due configurazioni alternative",
        ),
        xaxis_title="Componente di scorta",
        yaxis_title=f"Quantita' ({unit})",
        **_LAYOUT,
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f")
    return fig


# ---------------------------------------------------------------------------
# Grafici di supporto
# ---------------------------------------------------------------------------


def chart_seasonal_profile(
    series: pd.Series,
    product: str,
) -> go.Figure:
    """Profilo stagionale medio: indice mensile con media annua = 100.

    L'indicizzazione a 100 rende il grafico confrontabile fra prodotti con
    volumi molto diversi ed evidenzia immediatamente l'intensita' della
    stagionalita'.
    """
    monthly = series.groupby(series.index.month).mean()
    index = monthly / monthly.mean() * 100.0
    labels = [MONTH_NAMES_IT[m - 1] for m in index.index]

    colors = [
        COLORS["forecast"] if v >= 110 else COLORS["train"] if v >= 90 else COLORS["baseline"]
        for v in index
    ]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=index.to_numpy(),
            marker_color=colors,
            text=[f"{v:.0f}" for v in index],
            textposition="outside",
            hovertemplate="%{x}<br>Indice stagionale: %{y:.1f}<extra></extra>",
        )
    )
    fig.add_hline(
        y=100,
        line=dict(color="#7f8c8d", width=1, dash="dash"),
        annotation_text="media annua = 100",
        annotation_position="right",
        annotation_font_size=11,
    )
    fig.update_layout(
        title=_title(
            f"Profilo stagionale medio - {product}",
            "Indice mensile, media annua = 100",
        ),
        xaxis_title="Mese",
        yaxis_title="Indice stagionale",
        showlegend=False,
        **_LAYOUT,
    )
    return fig


def chart_products_overview(data: pd.DataFrame, products: Sequence[str]) -> go.Figure:
    """Confronto visivo delle quattro serie storiche su un unico grafico.

    I volumi sono normalizzati alla media di ciascun prodotto (media = 100):
    senza normalizzazione la serie Nutella (~12.000) schiaccerebbe quella
    Happy Hippo (~3.000) rendendo illeggibili le differenze di profilo.
    """
    palette = ["#1f4e79", "#e67e22", "#c0392b", "#2e8b57"]
    fig = go.Figure()

    for i, product in enumerate(products):
        group = data[data["product"] == product].sort_values("date")
        if group.empty:
            continue
        normalised = group["demand"] / group["demand"].mean() * 100.0
        fig.add_trace(
            go.Scatter(
                x=group["date"],
                y=normalised,
                mode="lines",
                name=product,
                line=dict(color=palette[i % len(palette)], width=2),
                customdata=group["demand"],
                hovertemplate=(
                    "%{x|%b %Y}<br>"
                    + product
                    + "<br>Indice: %{y:.0f}<br>Domanda: %{customdata:,.0f} cartoni"
                    "<extra></extra>"
                ),
            )
        )

    fig.add_hline(y=100, line=dict(color="#bdc3c7", width=1, dash="dash"))
    fig.update_layout(
        title=_title(
            "Confronto dei profili di domanda dei quattro prodotti",
            "Valori normalizzati: media di ciascun prodotto = 100",
        ),
        xaxis_title="Mese",
        yaxis_title="Domanda normalizzata (media prodotto = 100)",
        **_LAYOUT,
    )
    return fig


def chart_baseline_vs_scenario(
    baseline: pd.Series,
    scenario: pd.Series,
    product: str,
    unit: str = "cartoni",
) -> go.Figure:
    """Sovrapposizione fra serie storica di base e serie di scenario.

    Rende esplicito l'effetto delle leve sulla domanda simulata e separa
    chiaramente il dataset storico (mai modificato) dallo scenario.
    """
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=baseline.index,
            y=baseline.to_numpy(),
            mode="lines",
            name="Dataset storico di base",
            line=dict(color=COLORS["baseline"], width=2, dash="dot"),
            hovertemplate="%{x|%b %Y}<br>Base: %{y:,.0f} " + unit + "<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=scenario.index,
            y=scenario.to_numpy(),
            mode="lines",
            name="Serie simulata di scenario",
            line=dict(color=COLORS["scenario"], width=2.5),
            hovertemplate="%{x|%b %Y}<br>Scenario: %{y:,.0f} " + unit + "<extra></extra>",
        )
    )
    fig.update_layout(
        title=_title(
            f"Dataset storico vs scenario simulato - {product}",
            "Il dataset su disco non viene mai modificato dalla simulazione",
        ),
        xaxis_title="Mese",
        yaxis_title=f"Domanda ({unit}/mese)",
        **_LAYOUT,
    )
    fig.update_yaxes(rangemode="tozero", tickformat=",.0f")
    return fig
