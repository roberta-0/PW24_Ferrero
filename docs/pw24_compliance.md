# Audit di conformità alla specifica PW24

Questo documento mappa **ogni requisito** della specifica ufficiale del
Project Work 24 sulla sua realizzazione concreta nel progetto, indicando per
ciascuno:

- **Implementazione** — come il requisito è soddisfatto;
- **File sorgente** — dove si trova il codice;
- **Dashboard** — attraverso quale elemento dell'interfaccia è verificabile;
- **Documentazione** — dove è descritto e motivato.

La verifica è stata condotta a progetto completato, con l'applicazione
funzionante e la suite di test superata (**264 test, 0 fallimenti**).

Legenda esito: ✅ soddisfatto · ➕ soddisfatto oltre il minimo richiesto

---

## 1. Compiti richiesti allo studente

### R1 — Selezionare un'impresa reale

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Impresa selezionata: **Ferrero** (gruppo dolciario italiano, Alba, 1946). Informazioni tratte esclusivamente da fonti pubbliche istituzionali. |
| **File sorgente** | `src/config.py` (anagrafica `PRODUCTS`) |
| **Dashboard** | Sezione 1 «Scenario di analisi» — intestazione e scheda prodotto |
| **Documentazione** | `docs/company.md`; `README.md` §2; relazione cap. 3 |

### R2 — Descrivere brevemente settore, prodotti e contesto logistico

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Descrizione di settore dolciario, quattro prodotti reali e contesto logistico (filiera a cinque livelli, lead time, periodo di riesame). |
| **File sorgente** | `src/config.py` — descrizioni prodotto esposte in interfaccia |
| **Dashboard** | Sezione 1 — scheda prodotto con comportamento atteso della domanda |
| **Documentazione** | `docs/company.md`; relazione capp. 3, 4, 5 |

### R3 — Costruire serie storiche di domanda per **almeno quattro** prodotti

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Esattamente quattro prodotti: Nutella, Kinder Cioccolato, Ferrero Rocher, Kinder Happy Hippo. 48 osservazioni mensili ciascuno (gen 2022 – dic 2025), per un totale di 192 righe. |
| **File sorgente** | `src/data_generator.py`; `src/config.py`; output in `data/demand_history.csv`, `data/product_parameters.csv` |
| **Dashboard** | Selettore «Prodotto» in sidebar; Sezione 8 «Quadro di sintesi» (tutti e quattro) |
| **Documentazione** | `docs/dataset.md`; `data/README.md`; relazione cap. 7 |
| **Test** | `tests/test_data_generator.py` — numerosità, copertura temporale, presenza dei quattro prodotti |

### R4 — Utilizzare dati reali, stimati o generati

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Scelta: dati **generati**, opzione espressamente ammessa. Motivazione documentata: impossibilità di accesso a dati reali, necessità di controllare i profili differenziati, riproducibilità. |
| **File sorgente** | `src/data_generator.py` |
| **Dashboard** | Avvertenza sulla natura sintetica dei dati, visibile in Sezione 1 |
| **Documentazione** | `docs/dataset.md` §1; relazione §7.1 e dichiarazione iniziale |

### R5 — I quattro prodotti devono mostrare comportamenti di domanda **diversi**

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Differenziazione ottenuta per costruzione tramite parametri distinti e **verificata numericamente**: CV 6,7% / 14,1% / 39,9% / 26,8%; escursione stagionale 15 / 29 / 118 / 57 punti indice. |
| **File sorgente** | `src/config.py` — `PRODUCTS` (8 parametri per prodotto) |
| **Dashboard** | Sezione 1 — profilo stagionale e statistiche descrittive; Sezione 8 — confronto normalizzato dei quattro profili |
| **Documentazione** | `docs/dataset.md` §3; relazione capp. 4 e 8 |
| **Test** | `tests/test_data_generator.py` — test espliciti: Rocher più stagionale di Nutella; Happy Hippo più variabile di Nutella; Nutella la meno variabile |

### R6 — Sviluppare codice Python

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | 11 moduli applicativi in `src/`, 1 applicazione, 7 file di test, 1 script di generazione asset. Architettura modulare con logica di calcolo indipendente dall'interfaccia, *type hints* e *docstring* su tutte le funzioni pubbliche. |
| **File sorgente** | `src/` (11 moduli), `app.py`, `tests/` (7 file), `scripts/` |
| **Dashboard** | L'intera applicazione |
| **Documentazione** | `docs/technical_architecture.md`; relazione cap. 14 |

### R7 — Creare una mini-dashboard con una libreria Python

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Dashboard **Streamlit** in 8 sezioni, grafici **Plotly** interattivi, interfaccia interamente in italiano. |
| **File sorgente** | `app.py`, `src/charts.py` |
| **Dashboard** | Tutte le 8 sezioni |
| **Documentazione** | `README.md` §8; relazione cap. 13 |
| **Test** | `tests/test_dashboard.py` — 22 test headless tramite `streamlit.testing.v1.AppTest` |

### R8 — Applicare e confrontare metodi previsionali diversi

| | |
|---|---|
| **Esito** | ➕ (5 metodi, minimo richiesto 2, raccomandati 3) |
| **Implementazione** | Confronto sistematico dei 5 metodi su ciascun prodotto, con valutazione out-of-sample e 5 metriche. |
| **File sorgente** | `src/forecasting.py`, `src/evaluation.py` |
| **Dashboard** | Sezione 3 «Confronto dei metodi previsionali» — tabella + grafico a barre con metrica selezionabile |
| **Documentazione** | `docs/forecasting.md`; relazione capp. 9 e 10 |

### R9 — Consentire la modifica delle caratteristiche di domanda e di fornitura

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | 6 leve operative: variabilità, trend, stagionalità (domanda); lead time, livello di servizio, periodo di riesame (fornitura). Più 4 leve di metodo: metodo, orizzonte, finestra MA, alpha. |
| **File sorgente** | `src/scenarios.py` — `ScenarioConfig`, `build_scenario_series`, `simulate_scenario` |
| **Dashboard** | Sidebar «Configurazione», gruppi *Caratteristiche della domanda* e *Parametri logistici* |
| **Documentazione** | `docs/scenarios.md`; relazione cap. 15 |
| **Test** | `tests/test_scenarios.py` — verifica che ogni leva produca l'effetto direzionale atteso |

### R10 — Analizzare variabilità, stagionalità e lead time

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Analisi quantificata con effetti misurati: variabilità ×2 → sicurezza ×2,08; lead time 2→5 mesi → pipeline ×2,50 e sicurezza ×1,58 (≈√2,5); stagionalità ×2 → anticipata ×1,98. |
| **File sorgente** | `src/scenarios.py`, `src/inventory.py` |
| **Dashboard** | Sezioni 4, 5, 6 e 7 |
| **Documentazione** | `docs/scenarios.md` §4; relazione §15.2 e cap. 17 |

### R11 — Mostrare gli effetti su previsioni e tipologie di scorta

| | |
|---|---|
| **Esito** | ✅ |
| **Implementazione** | Ogni modifica di leva si propaga lungo l'intera catena: serie → valutazione metodi → previsione → σ → quattro componenti di scorta. Gli effetti sono visibili simultaneamente su grafici, tabelle e KPI. |
| **File sorgente** | `src/scenarios.py` (orchestrazione), `src/narrative.py` (commento) |
| **Dashboard** | Sezione 2 (previsione), Sezione 4 (scorte), Sezione 6 (commento), Sezione 7 (confronto) |
| **Documentazione** | `docs/scenarios.md`; relazione capp. 15, 16, 17 |

---

## 2. Obiettivi dichiarati dalla specifica

| # | Obiettivo | Esito | Realizzazione | Documentazione |
|---|---|:---:|---|---|
| O1 | Competenze di programmazione applicate a previsione e scorte | ✅ | 11 moduli, 5 metodi e 4 modelli di scorta scritti da zero con NumPy, 264 test | relazione §2, cap. 14 |
| O2 | Applicare e confrontare metodi, valutandone l'accuratezza | ✅ | 5 metodi, 5 metriche, split cronologico 36/12, selezione automatica | relazione capp. 9-10 |
| O3 | Analizzare effetti di caratteristiche della domanda e lead time sulle scorte | ✅ | 6 leve con effetti verificati numericamente, scomposizione in 4 componenti | relazione cap. 15 |
| O4 | Mini-dashboard per configurazione scenari e rappresentazione grafica | ✅ | Streamlit, 8 sezioni, 8 tipologie di grafico, confronto A/B dedicato | relazione cap. 13 |
| O5 | Interpretare le conseguenze gestionali | ✅ | Sezione 6 con commento generato dinamicamente dai valori calcolati | relazione cap. 17 |

---

## 3. Artefatti finali richiesti

| Artefatto richiesto | Esito | Dove si trova |
|---|:---:|---|
| Ricerca e descrizione dell'impresa | ✅ | `docs/company.md`; relazione cap. 3 |
| Descrizione dei prodotti | ✅ | `docs/company.md`; relazione cap. 4 |
| Descrizione del contesto produttivo, commerciale e logistico | ✅ | `docs/company.md`; relazione cap. 5 |
| Serie storiche per ≥4 prodotti con comportamenti diversi | ✅ | `data/demand_history.csv` (192 righe); relazione capp. 7-8 |
| Implementazione Python | ✅ | `src/`, `app.py`; relazione cap. 14 |
| Almeno due metodi previsionali | ➕ **5** | `src/forecasting.py`; relazione cap. 9 |
| Indicatori di accuratezza previsionale | ➕ **5** | `src/metrics.py`; relazione §10.2 |
| Selezione del metodo più appropriato per ciascun prodotto | ✅ | `src/evaluation.py` → `select_best_method`; relazione §10.3 |
| Stima e rappresentazione di **scorta ciclica** | ✅ | `src/inventory.py` → `cycle_stock`; relazione §12.1 |
| Stima e rappresentazione di **scorta di sicurezza** | ✅ | `src/inventory.py` → `safety_stock`; relazione §12.2 |
| Stima e rappresentazione di **scorta anticipata** | ✅ | `src/inventory.py` → `anticipation_stock`; relazione §12.3 |
| Stima e rappresentazione di **scorta pipeline** | ✅ | `src/inventory.py` → `pipeline_stock`; relazione §12.4 |
| Dashboard grafica | ✅ | `app.py`; relazione cap. 13 |
| Scenari configurabili: variabilità | ✅ | `variability_multiplier` (0,25–3,0) |
| Scenari configurabili: trend | ✅ | `trend_multiplier` (−2,0–5,0) |
| Scenari configurabili: stagionalità | ✅ | `seasonality_multiplier` (0,0–3,0) |
| Scenari configurabili: lead time | ✅ | `lead_time_months` (0,5–8,0) |
| Confronto degli effetti degli scenari su previsioni e scorte | ✅ | Sezione 7; `src/scenarios.py` → `compare_scenarios` |
| Visualizzazione domanda storica e prevista | ✅ | Sezione 2; `chart_demand_and_forecast` |
| Confronto grafico dell'accuratezza dei metodi | ✅ | Sezione 3; `chart_method_accuracy` |
| Visualizzazione della composizione delle scorte | ✅ | Sezione 4; `chart_inventory_composition`, `chart_inventory_share` |
| Documentazione finale | ✅ | `README.md` + 9 documenti tecnici in `docs/`, con indice |
| Repository GitHub con codice, dati e file necessari | ✅ | Struttura completa con `.gitignore`, `requirements.txt`, `pytest.ini` |

---

## 4. Requisiti tecnici di dettaglio

### 4.1 Dataset (specifica §4)

| Requisito | Esito | Realizzazione |
|---|:---:|---|
| 48 osservazioni mensili | ✅ | `N_PERIODS = 48` in `src/config.py` |
| Periodo gennaio 2022 – dicembre 2025 | ✅ | `HISTORY_START = "2022-01-01"`, frequenza `"MS"` |
| Frequenza mensile | ✅ | `FREQUENCY = "MS"` |
| Meccanismo riproducibile con seed fissato | ✅ | `RANDOM_SEED = 24`; flussi per prodotto via `SeedSequence.spawn(16)` |
| **Non** codificare a mano 192 numeri | ✅ | Nessun valore di domanda è hard-coded: tutto deriva da 8 parametri per prodotto |
| Modulo che combina matematicamente le componenti | ✅ | `src/data_generator.py`: livello, trend, stagionalità, rumore, promozioni |
| Generatore documentato | ✅ | `docs/dataset.md` §2; relazione §7.2 |
| Parametro `base_demand` | ✅ | `ProductParameters.base_demand` |
| Parametro `trend_rate` | ✅ | `ProductParameters.trend_rate` |
| Parametro `seasonal_amplitude` | ✅ | `ProductParameters.seasonal_amplitude` |
| Parametro `noise_std` | ✅ | `ProductParameters.noise_std` |
| Parametro `promotion_probability` | ✅ | `ProductParameters.promotion_probability` |
| Parametro `promotion_amplitude` | ✅ | `ProductParameters.promotion_amplitude` |
| Componente stagionale sinusoidale | ✅ | `seasonal_factor()` usa `cos(2π(m−peak)/12)` |
| Picchi natalizi realistici su Ferrero Rocher | ✅ | `festive_profile = {10: +0,45, 11: +1,05, 12: +0,75}` |
| Valori positivi | ✅ | `max(1, …)` nel generatore |
| Valori interi | ✅ | `round(…)`, dtype intero |
| Valori plausibili | ✅ | Intervalli 1.849–14.427 cartoni/mese |
| Valori riproducibili | ✅ | Test di riproducibilità bit-per-bit |
| `data/demand_history.csv` con `date`, `product`, `demand` | ✅ | Esattamente queste tre colonne |
| `data/product_parameters.csv` (opzionale) | ➕ | Creato: 4 righe con tutti i parametri generatori |
| Dataset pivotato (opzionale) | ➕ | Creato: `data/demand_history_wide.csv` |
| L'applicazione può rigenerare il dataset | ✅ | Pulsante in sidebar + `python -m src.data_generator` |

### 4.2 Validazione dei dati (specifica §5)

| Controllo richiesto | Esito | Funzione |
|---|:---:|---|
| Valori mancanti | ✅ | `_check_missing_values` |
| Date duplicate | ✅ | `_check_duplicates` |
| Domanda negativa | ✅ | `_check_demand_domain` |
| Prodotti non validi | ✅ | `_check_products` |
| Formato data non valido | ✅ | `_coerce_types` |
| Osservazioni sufficienti | ✅ | `_check_length_and_continuity` (≥ 24) |
| Continuità mensile | ✅ | `_check_length_and_continuity` |
| Messaggi di errore significativi **in italiano** | ✅ | Tutti i messaggi di `DataValidationError` |
| Fallimento controllato («fail gracefully») | ✅ | Nessun traceback esposto; `mostra_errore()` in `app.py` |

**File sorgente**: `src/data_validation.py` · **Test**: `tests/test_data_validation.py`
(21) · **Documentazione**: `docs/dataset.md` §5; relazione §7.6

### 4.3 Metodi previsionali (specifica §6)

| Metodo | Richiesto | Esito | Funzione | Parametro configurabile |
|---|:---:|:---:|---|---|
| Media mobile semplice | obbligatorio | ✅ | `moving_average_forecast` | finestra ∈ {3, 6, 12} mesi |
| Smorzamento esponenziale semplice | obbligatorio | ✅ | `simple_exponential_smoothing` | α ∈ [0,05; 1,00] |
| Regressione lineare sul tempo | obbligatorio | ✅ | `linear_trend_regression` | — |
| Naive stagionale | opzionale | ➕ | `seasonal_naive_forecast` | periodo = 12 |
| Holt-Winters additivo | opzionale | ➕ | `holt_winters_additive` | α, β, γ |

La specifica chiede «almeno tre» metodi con i tre obbligatori come minimo
robusto: tutti e tre sono presenti, più i due opzionali suggeriti. La
raccomandazione di **non complicare inutilmente l'architettura** è rispettata
tramite il registro `METHOD_REGISTRY`: i cinque metodi condividono la stessa
firma e sono iterati dinamicamente, senza elenchi duplicati nel codice.

**File sorgente**: `src/forecasting.py` · **Test**:
`tests/test_forecasting.py` (64) · **Documentazione**: `docs/forecasting.md`;
relazione cap. 9

### 4.4 Metriche e valutazione

| Requisito | Esito | Realizzazione |
|---|:---:|---|
| Indicatori di accuratezza | ➕ | MAE, RMSE, MAPE, Bias, sMAPE |
| Gestione sicura dei valori nulli nel MAPE | ✅ | Zeri esclusi, `NaN` se tutti nulli |
| Split cronologico (mai casuale) | ✅ | `chronological_split`, 36/12 |
| Assenza di fughe di informazione | ✅ | Test dedicato che altera il solo test set e verifica l'invarianza delle previsioni |
| Selezione automatica del metodo migliore | ✅ | MAPE minimo, fallback su RMSE documentato |
| Criterio di selezione dichiarato | ✅ | relazione §10.3; esposto anche in dashboard, Sezione 3 |

**File sorgente**: `src/metrics.py`, `src/evaluation.py` · **Test**:
`tests/test_metrics.py` (34)

### 4.5 Componenti di scorta

| Componente | Formula implementata | Funzione | Dashboard |
|---|---|---|---|
| Ciclica | `D · R / 2` | `cycle_stock` | Sezione 4, tabella con formula e valori sostituiti |
| Di sicurezza | `z · σ · √(IP)` | `safety_stock` | idem |
| Anticipata | `max C(t) − min C(t)` | `anticipation_stock` | idem |
| Pipeline | `D · L` | `pipeline_stock` | idem |
| Totale | somma delle quattro | `InventoryPlan.total_stock` | KPI Sezione 5 |
| Composizione percentuale | quota di ciascuna | `InventoryPlan.composition_pct` | Grafico ad anello Sezione 4 |

σ è la **deviazione standard dell'errore previsionale out-of-sample**, non la
variabilità grezza della domanda: scelta metodologica documentata in
`docs/inventory.md` §3 e relazione §12.2.

**File sorgente**: `src/inventory.py` · **Test**: `tests/test_inventory.py`
(42) · **Documentazione**: `docs/inventory.md`; relazione cap. 12

### 4.6 Qualità del codice (specifica §28)

| Prescrizione | Esito | Come è rispettata |
|---|:---:|---|
| Design modulare | ✅ | 11 moduli con responsabilità singola, grafo delle dipendenze aciclico |
| Nomi di variabile significativi | ✅ | Identificatori inglesi in `src/`, italiani nelle funzioni di presentazione |
| Docstring | ✅ | Su tutti i moduli e tutte le funzioni pubbliche |
| Stato globale limitato | ✅ | Nessuna variabile globale mutabile; configurazione in dataclass immutabili |
| Costanti di configurazione | ✅ | Centralizzate in `src/config.py` |
| **Evitare** script monolitici | ✅ | Nessun file supera le dimensioni di un modulo gestibile |
| **Evitare** logica duplicata | ✅ | `scripts/generate_report_assets.py` riusa le funzioni della dashboard |
| **Evitare** logica di business nei widget | ✅ | `app.py` è solo presentazione; `src/` non importa mai Streamlit |
| **Evitare** dipendenze inutili | ✅ | 7 dipendenze dirette, tutte con versione fissata |
| **Evitare** sovra-ingegnerizzazione | ✅ | Nessun ORM, nessun framework, nessun livello di astrazione non utilizzato |
| Calcoli indipendenti dall'interfaccia | ✅ | Verificabile: i test di `src/` girano senza avviare Streamlit |
| L'app Streamlit chiama funzioni di `src/` | ✅ | `app.py` contiene solo chiamate e rendering |

### 4.7 Riproducibilità (specifica §29)

| Passo richiesto | Esito | Comando documentato |
|---|:---:|---|
| 1. Clonare il repository | ✅ | `git clone <URL>` — `README.md` §5 |
| 2. Installare le dipendenze | ✅ | `pip install -r requirements.txt` |
| 3. Generare il dataset | ✅ | `python -m src.data_generator` |
| 4. Eseguire i test | ✅ | `pytest` |
| 5. Avviare la dashboard | ✅ | `streamlit run app.py` (oppure `python -m streamlit run app.py`) |
| Ogni passo documentato | ✅ | `README.md` §§5-6; relazione §21.2-21.3 |
| Seed fissato per il dataset di base | ✅ | `RANDOM_SEED = 24` |
| Funzionamento **completamente offline** | ✅ | Nessuna chiamata di rete nel codice applicativo |

---

## 5. Vincoli di integrità sui dati

| Vincolo | Esito | Verifica |
|---|:---:|---|
| Nessun dato proprietario Ferrero utilizzato | ✅ | Tutti i valori prodotti da `src/data_generator.py` |
| Tutti i dati di domanda generati artificialmente | ✅ | Nessun valore hard-coded, nessuna fonte esterna |
| Natura sintetica **documentata esplicitamente** | ✅ | README (avvertenza in apertura), dashboard, 9 documenti in `docs/`, relazione (dichiarazione in apertura) |
| Mai presentati come vendite reali Ferrero | ✅ | Dichiarazione in ogni documento; `SYNTHETIC_DATA_DISCLAIMER` in `src/config.py` |
| Nessuna informazione riservata inventata | ✅ | Solo informazioni istituzionali pubbliche, con fonti elencate |
| Solo informazioni pubblicamente difendibili sull'impresa | ✅ | 6 fonti pubbliche citate in `docs/references.md` §A |
| Nessuna citazione inventata | ✅ | Riferimenti divisi in impresa / accademici / software, tutti verificabili |
| Disclaimer esplicito in README e relazione finale | ✅ | `README.md` «Avvertenza sui dati»; relazione «Dichiarazione sulla natura dei dati» |
| Nessun risultato numerico inventato | ✅ | Tutti i valori nella relazione derivano da esecuzioni effettive, salvati in `report/results/` |

---

## 6. Verifica finale della specifica §30

Elenco di controllo richiesto dalla specifica. Le voci sono tradotte in
italiano; la formulazione originale è riportata in corsivo fra parentesi per
consentire il riscontro puntuale con il testo della specifica.

| | Voce | Esito | Riscontro |
|---|---|:---:|---|
| 1 | Quattro prodotti<br>*(Four products)* | ✅ | Nutella, Kinder Cioccolato, Ferrero Rocher, Kinder Happy Hippo — `src/config.py`, `data/product_parameters.csv` |
| 2 | Profili di domanda differenziati<br>*(Different demand patterns)* | ✅ | CV 6,7% / 14,1% / 39,9% / 26,8%; escursione stagionale 15 / 29 / 118 / 57 punti indice |
| 3 | Natura sintetica dei dati chiaramente dichiarata<br>*(Synthetic data clearly identified)* | ✅ | Avvertenza in README, dashboard, tutti i documenti `docs/`, relazione |
| 4 | Almeno due metodi previsionali<br>*(At least two forecasting methods)* | ✅ | 5 metodi implementati |
| 5 | Tre metodi previsionali implementati<br>*(Three forecasting methods implemented)* | ✅ | Media mobile, smorzamento esponenziale, regressione lineare — più naive stagionale e Holt-Winters |
| 6 | Indicatori di accuratezza<br>*(Accuracy metrics)* | ✅ | MAE, RMSE, MAPE, Bias, sMAPE — `src/metrics.py` |
| 7 | Selezione del metodo migliore<br>*(Best method selection)* | ✅ | `select_best_method`: MAPE minimo con ripiego su RMSE |
| 8 | Scorta ciclica<br>*(Cycle stock)* | ✅ | `cycle_stock` — `D·R/2` |
| 9 | Scorta di sicurezza<br>*(Safety stock)* | ✅ | `safety_stock` — `z·σ·√(IP)` |
| 10 | Scorta anticipata<br>*(Anticipation stock)* | ✅ | `anticipation_stock` — `max C(t) − min C(t)` |
| 11 | Scorta in transito<br>*(Pipeline stock)* | ✅ | `pipeline_stock` — `D·L` |
| 12 | Controllo della variabilità della domanda<br>*(Demand variability control)* | ✅ | Cursore «Variabilità della domanda» (0,25–3,0) |
| 13 | Controllo del trend<br>*(Trend control)* | ✅ | Cursore «Trend» (−2,0–5,0, inversione del segno inclusa) |
| 14 | Controllo della stagionalità<br>*(Seasonality control)* | ✅ | Cursore «Stagionalità» (0,0–3,0) |
| 15 | Controllo del lead time<br>*(Lead-time control)* | ✅ | Cursore «Lead time» (0,5–8,0 mesi) |
| 16 | Grafico della domanda storica<br>*(Historical demand chart)* | ✅ | Sezione 2; `chart_demand_and_forecast` |
| 17 | Grafico della previsione<br>*(Forecast chart)* | ✅ | Sezione 2, con banda di incertezza |
| 18 | Confronto dell'accuratezza<br>*(Accuracy comparison)* | ✅ | Sezione 3, tabella + grafico con metrica selezionabile |
| 19 | Composizione delle scorte<br>*(Inventory composition)* | ✅ | Sezione 4, barra impilata + grafico ad anello + tabella con le formule |
| 20 | Confronto fra scenari<br>*(Scenario comparison)* | ✅ | Sezione 7, confronto A/B con tabella delle variazioni |
| 21 | Dashboard Streamlit<br>*(Streamlit dashboard)* | ✅ | `app.py`, 8 sezioni |
| 22 | Interfaccia in italiano<br>*(Italian UI)* | ✅ | Ogni etichetta, titolo, asse, legenda, KPI e messaggio di errore in italiano |
| 23 | Test automatici<br>*(Tests)* | ✅ | 264 test in 7 file, tutti superati |
| 24 | README<br>*(README)* | ✅ | `README.md`, 14 sezioni |
| 25 | Documentazione tecnica<br>*(Technical documentation)* | ✅ | 9 documenti tecnici in `docs/`, con indice, + `data/README.md` |
| 26 | Bozza della relazione finale<br>*(Final report draft)* | ✅ | `report/relazione_pw24.md`, 22 capitoli con risultati reali |
| 27 | Struttura pronta per GitHub<br>*(GitHub-ready structure)* | ✅ | `.gitignore`, `requirements.txt` con versioni fissate, `pytest.ini`, repository git inizializzato |

**Esito complessivo: 27 / 27 voci soddisfatte.**

---

## 7. Elementi realizzati oltre il minimo richiesto

Non richiesti dalla specifica, aggiunti perché rafforzano la difendibilità
accademica del lavoro.

| Elemento | Motivazione |
|---|---|
| 5 metodi previsionali invece di 3 | Copertura dell'intero spettro di strutture presenti nel dataset; il naive stagionale funge da **benchmark** metodologico |
| 5 metriche invece di 1 | Bias diagnostica le distorsioni sistematiche; sMAPE è definito anche con osservazioni nulle |
| σ dall'**errore previsionale** anziché dalla domanda grezza | Evita di sovrastimare la sicurezza di 3,5 volte su prodotti stagionali |
| Scenari per **rigenerazione** anziché deformazione | Garantisce coerenza statistica e isolamento causale della leva modificata |
| Test di assenza di fughe di informazione | Dimostra che la valutazione out-of-sample è genuina |
| Commento gestionale generato dinamicamente | La Sezione 6 cambia struttura, non solo numeri, al variare dello scenario |
| 23 figure HTML autonome | Consultabili offline, riutilizzabili nella relazione cartacea |
| `data/product_parameters.csv` | Rende il dataset auto-documentato |
| Opzione intervallo di protezione esteso `√(L+R)` | Mostra la formulazione teoricamente più corretta per il riordino periodico |
| 18 limiti e 12 sviluppi futuri numerati | Delimita con precisione la portata dei risultati |
| Test headless della dashboard | Verifica end-to-end dell'interattività, non solo della logica di calcolo |

---

## 8. Conformità del processo (specifica §31)

Le 16 fasi prescritte sono state eseguite nell'ordine indicato, con
**esecuzione effettiva** del codice e non solo creazione di file.

| Fase | Attività | Esito |
|---|---|---|
| 1 | Analisi dei requisiti e proposta di architettura | Architettura a 11 moduli definita prima della scrittura del codice |
| 2 | Creazione della struttura di progetto | `src/`, `tests/`, `data/`, `docs/`, `report/`, `scripts/` |
| 3 | Generazione del dataset sintetico | `src/data_generator.py` |
| 4 | **Esecuzione** del generatore e ispezione del dataset | 192 righe generate e verificate statisticamente |
| 5 | Validazione dei dati | `src/data_validation.py`, 11 controlli |
| 6 | Metodi previsionali | `src/forecasting.py`, 5 metodi |
| 7 | Metriche e valutazione cronologica | `src/metrics.py`, `src/evaluation.py` |
| 8 | Calcoli di scorta | `src/inventory.py`, 4 componenti |
| 9 | Simulazione di scenario | `src/scenarios.py` |
| 10 | Dashboard Streamlit | `app.py`, `src/charts.py`, `src/narrative.py` |
| 11 | Test | 7 file, 264 test |
| 12 | **Esecuzione** dei test e correzione dei fallimenti | 264 superati, 0 falliti |
| 13 | **Esecuzione** dell'applicazione e verifica delle funzionalità | Tutte le 8 sezioni verificate nel browser |
| 14 | Documentazione | 9 documenti tecnici in `docs/`, con indice, + `README.md` + `data/README.md` |
| 15 | Relazione finale con **risultati effettivi** | `report/relazione_pw24.md`, nessun valore inventato |
| 16 | Audit di conformità PW24 | Questo documento |

---

## 9. Riepilogo quantitativo

| Indicatore | Valore |
|---|---:|
| Moduli applicativi | 11 |
| Metodi previsionali | 5 |
| Metriche di accuratezza | 5 |
| Componenti di scorta | 4 |
| Leve di scenario | 10 |
| Sezioni della dashboard | 8 |
| Tipologie di grafico | 8 |
| Test automatici | **264** |
| Test falliti | **0** |
| Documenti tecnici | 9 (+ README + dizionario dei dati) |
| Capitoli della relazione | 22 |
| Figure generate | 23 |
| Tabelle di risultati | 5 |
| Osservazioni nel dataset | 192 |
| Controlli di validazione | 11 |
| Limiti dichiarati | 18 |
| Sviluppi futuri proposti | 12 |
| Voci della verifica §30 soddisfatte | **27 / 27** |
