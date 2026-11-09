# 8. Riferimenti

Le fonti sono separate in tre categorie, come richiesto dalla specifica.
Sono riportate **solo fonti realmente esistenti e verificabili**; non sono
state inventate citazioni.

---

## 8.1 Fonti sull'impresa e sui prodotti

Le informazioni istituzionali su Ferrero e sui prodotti citati provengono
esclusivamente da materiale **pubblico**. Nessuna informazione riservata è
stata utilizzata.

| # | Fonte | Tipo | Uso nel progetto |
|---|---|---|---|
| A1 | Ferrero — Sito istituzionale del Gruppo, <https://www.ferrero.com> | Sito aziendale | Storia, fondazione, perimetro, marchi |
| A2 | Ferrero — *Rapporto di Sostenibilità* (pubblicazione annuale), disponibile su <https://www.ferrerosustainability.com> | Documento aziendale pubblico | Perimetro industriale, approvvigionamento materie prime |
| A3 | Ferrero Italia — Sito commerciale, <https://www.ferrero.it> | Sito aziendale | Descrizione delle referenze di prodotto |
| A4 | Nutella — Sito ufficiale di prodotto, <https://www.nutella.com> | Sito di prodotto | Descrizione e storia del prodotto |
| A5 | Kinder — Sito ufficiale di marca, <https://www.kinder.com> | Sito di marca | Descrizione linea Kinder (Cioccolato, Happy Hippo) |
| A6 | Ferrero Rocher — Sito ufficiale di prodotto, <https://www.ferrerorocher.com> | Sito di prodotto | Posizionamento della pralineria da regalo |

> **Nota di integrità.** Da queste fonti sono state tratte **unicamente**
> informazioni qualitative di carattere istituzionale e descrittivo. **Nessun
> dato numerico di domanda, vendita, produzione o scorta** proviene da queste
> fonti né da altre fonti aziendali: tutti i valori numerici del progetto
> sono **sintetici** e generati algoritmicamente (cfr.
> [`dataset.md`](dataset.md)).

---

## 8.2 Fonti teoriche e accademiche

### Previsione della domanda

| # | Riferimento |
|---|---|
| T1 | Hyndman, R.J., Athanasopoulos, G. (2021). *Forecasting: Principles and Practice*, 3ª ed. OTexts, Melbourne. Disponibile gratuitamente: <https://otexts.com/fpp3/> |
| T2 | Hyndman, R.J., Koehler, A.B. (2006). "Another look at measures of forecast accuracy". *International Journal of Forecasting*, 22(4), 679-688. |
| T3 | Makridakis, S., Wheelwright, S.C., Hyndman, R.J. (1998). *Forecasting: Methods and Applications*, 3ª ed. John Wiley & Sons. |
| T4 | Winters, P.R. (1960). "Forecasting Sales by Exponentially Weighted Moving Averages". *Management Science*, 6(3), 324-342. |
| T5 | Holt, C.C. (2004). "Forecasting seasonals and trends by exponentially weighted moving averages". *International Journal of Forecasting*, 20(1), 5-10. (Ristampa del rapporto originale del 1957.) |

**Uso nel progetto.** T1 è il riferimento principale per la formulazione dei
metodi di smorzamento esponenziale, per la metodologia di valutazione
out-of-sample e per l'uso del naive stagionale come benchmark. T2 documenta
i limiti del MAPE e la sua asimmetria, discussi in
[`forecasting.md`](forecasting.md). T4 e T5 sono le fonti originali del
metodo Holt-Winters implementato.

### Gestione delle scorte e Operations Management

| # | Riferimento |
|---|---|
| T6 | Silver, E.A., Pyke, D.F., Thomas, D.J. (2016). *Inventory and Production Management in Supply Chains*, 4ª ed. CRC Press. |
| T7 | Chopra, S., Meindl, P. (2016). *Supply Chain Management: Strategy, Planning, and Operation*, 6ª ed. Pearson. |
| T8 | Nahmias, S., Olsen, T.L. (2015). *Production and Operations Analysis*, 7ª ed. Waveland Press. |
| T9 | Slack, N., Brandon-Jones, A., Johnston, R. (2016). *Operations Management*, 8ª ed. Pearson. |
| T10 | Harris, F.W. (1913). "How Many Parts to Make at Once". *Factory, The Magazine of Management*, 10(2), 135-136. (Formulazione originale del lotto economico.) |
| T11 | Little, J.D.C. (1961). "A Proof for the Queuing Formula: L = λW". *Operations Research*, 9(3), 383-387. |

**Uso nel progetto.** T6 e T7 sono i riferimenti per la scomposizione
funzionale delle scorte (ciclica, sicurezza, anticipata, pipeline) e per la
formula della scorta di sicurezza `z·σ·√L`. T7 documenta inoltre la
distinzione fra *cycle service level* e *fill rate*, adottata in
[`inventory.md`](inventory.md). T8 è il riferimento per il livellamento della
produzione alla base del modello di scorta anticipata. T10 è la fonte
originale dell'EOQ, deliberatamente non adottato e discusso nelle scelte di
modellazione. T11 è la legge di Little, su cui si fonda il calcolo della
scorta pipeline.

### Effetto frusta e dinamiche di filiera

| # | Riferimento |
|---|---|
| T12 | Lee, H.L., Padmanabhan, V., Whang, S. (1997). "Information Distortion in a Supply Chain: The Bullwhip Effect". *Management Science*, 43(4), 546-558. |
| T13 | Forrester, J.W. (1958). "Industrial Dynamics: A Major Breakthrough for Decision Makers". *Harvard Business Review*, 36(4), 37-66. |

**Uso nel progetto.** Citati in [`company.md`](company.md) per inquadrare la
maggiore variabilità degli ordini della distribuzione rispetto ai consumi
finali. Il fenomeno non è modellato esplicitamente ma è richiamato come
elemento di contesto.

---

## 8.3 Fonti software e tecniche

### Librerie utilizzate

| # | Software | Versione | Documentazione | Ruolo |
|---|---|---|---|---|
| S1 | Python | 3.12 | <https://docs.python.org/3.12/> | Linguaggio |
| S2 | Streamlit | 1.65.0 | <https://docs.streamlit.io/> | Dashboard web |
| S3 | pandas | 2.2.3 | <https://pandas.pydata.org/docs/> | Serie storiche |
| S4 | NumPy | 2.1.3 | <https://numpy.org/doc/stable/> | Calcolo numerico |
| S5 | Plotly | 5.24.1 | <https://plotly.com/python/> | Grafici interattivi |
| S6 | SciPy | 1.14.1 | <https://docs.scipy.org/doc/scipy/> | `norm.ppf` (fattore z) |
| S7 | pytest | 8.3.4 | <https://docs.pytest.org/> | Test automatici |
| S8 | PyArrow | 18.1.0 | <https://arrow.apache.org/docs/python/> | Serializzazione tabelle |

### Documentazione tecnica consultata

| # | Riferimento |
|---|---|
| S9 | Streamlit — *App testing* (harness `streamlit.testing.v1.AppTest`): <https://docs.streamlit.io/develop/concepts/app-testing> |
| S10 | Streamlit — *Caching* (`st.cache_data`): <https://docs.streamlit.io/develop/concepts/architecture/caching> |
| S11 | NumPy — *Random sampling* (`default_rng`, `SeedSequence`): <https://numpy.org/doc/stable/reference/random/> |
| S12 | SciPy — `scipy.stats.norm`: <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html> |
| S13 | pandas — *Time series / date functionality*: <https://pandas.pydata.org/docs/user_guide/timeseries.html> |

**Uso nel progetto.** S9 è il riferimento per i 22 test funzionali della
dashboard. S11 documenta `SeedSequence.spawn`, il meccanismo che garantisce
flussi casuali indipendenti per prodotto (cfr. [`dataset.md`](dataset.md)
§2.4).

### Licenze

Tutte le librerie utilizzate sono distribuite con licenze open source
permissive (BSD-3-Clause per NumPy, SciPy e pandas; Apache 2.0 per Streamlit
e PyArrow; MIT per Plotly e pytest), compatibili con l'uso accademico e con
la pubblicazione del codice su repository pubblico.

---

## 8.4 Specifica di riferimento

| # | Riferimento |
|---|---|
| P1 | Specifica ufficiale del **Project Work 24** — «Sviluppo di una mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte di un'impresa», Corso di Studi in Informatica per le Aziende Digitali (L-31). Settori scientifico-disciplinari: INF/01, ING-INF/05, ING-IND/35. |

La mappatura puntuale fra ciascun requisito della specifica e la sua
implementazione è riportata in [`pw24_compliance.md`](pw24_compliance.md).
