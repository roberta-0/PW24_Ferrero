# Mini-dashboard per la previsione della domanda e la pianificazione delle scorte

**Project Work 24** — Simulazione applicativa su quattro prodotti Ferrero

Corso di Studi in **Informatica per le Aziende Digitali (L-31)**
Settori scientifico-disciplinari: **INF/01** (Informatica), **ING-INF/05**
(Sistemi di elaborazione delle informazioni), **ING-IND/35** (Ingegneria
economico-gestionale)
Tema: *La digitalizzazione dell'impresa*

---

## ⚠️ Avvertenza sui dati

> **L'impresa Ferrero e i prodotti citati (Nutella, Kinder Cioccolato,
> Ferrero Rocher, Kinder Happy Hippo) sono reali. I dati di domanda
> utilizzati in questo progetto sono invece interamente SINTETICI**: sono
> generati algoritmicamente dal modulo `src/data_generator.py` a partire da
> parametri scelti dallo studente, a **scopo esclusivamente didattico**.
>
> - Nessun valore rappresenta vendite, scorte, produzione o quote di mercato reali.
> - Nessun dato è stato fornito da Ferrero.
> - Nessuna informazione riservata o interna dell'azienda è utilizzata o rappresentata.
> - Le informazioni istituzionali su Ferrero provengono esclusivamente da fonti pubbliche.
>
> I risultati del progetto hanno valore **metodologico**, non predittivo sul
> mercato reale.

---

## 1. Obiettivi

Il progetto risponde ai cinque obiettivi della specifica PW24:

1. **Sviluppare competenze di programmazione** applicate alla previsione
   della domanda e alla gestione delle scorte.
2. **Applicare e confrontare metodi previsionali diversi**, valutandone
   l'accuratezza con criteri oggettivi.
3. **Analizzare gli effetti** delle caratteristiche della domanda e del lead
   time sulle diverse tipologie di scorta.
4. **Realizzare una mini-dashboard** per la configurazione di scenari e la
   rappresentazione grafica dei risultati.
5. **Interpretare le conseguenze gestionali** delle alternative analizzate.

---

## 2. L'impresa e i prodotti

**Ferrero** è un gruppo dolciario italiano fondato ad Alba (CN) nel 1946.
Il settore è caratterizzato da domanda stagionale, *shelf life* limitata e
livelli di servizio contrattualizzati con la grande distribuzione: condizioni
in cui un errore previsionale si traduce immediatamente in costi.

Sono analizzati quattro prodotti con comportamenti di domanda
**deliberatamente diversi**:

| Prodotto | Comportamento modellato | CV osservato | Stagionalità |
|---|---|---:|---:|
| **Nutella** | Stabile, variabilità bassa, trend minimo | 6,7% | debole (15 pt) |
| **Kinder Cioccolato** | Trend positivo moderato, calo estivo | 14,1% | moderata (29 pt) |
| **Ferrero Rocher** | Forte stagionalità con picco natalizio | 39,9% | **forte (118 pt)** |
| **Kinder Happy Hippo** | Rumoroso, con picchi promozionali | 26,8% | moderata (57 pt) |

Descrizione completa in [`docs/company.md`](docs/company.md).

---

## 3. Metodologia

```
Generazione dati sintetici   →   Validazione   →   Previsione
  4 prodotti × 48 mesi            11 controlli      5 metodi
  seed fisso = 24                                        │
                                                         ▼
                                            Valutazione out-of-sample
                                            split cronologico 36/12
                                            MAE · RMSE · MAPE
                                                         │
                                                         ▼
                                            Selezione automatica
                                            (criterio: MAPE minimo)
                                                         │
                                                         ▼
                                            Pianificazione scorte
                                       ciclica · sicurezza · anticipata · pipeline
                                                         │
                                                         ▼
                                            Simulazione scenari
                                 variabilità · trend · stagionalità · lead time
```

### Metodi previsionali implementati (5)

| Metodo | Livello | Trend | Stagionalità |
|---|:---:|:---:|:---:|
| Media mobile semplice (finestra 3/6/12) | ✔ | ✘ | ✘ |
| Smorzamento esponenziale semplice (α configurabile) | ✔ | ✘ | ✘ |
| Regressione lineare sul tempo | ✔ | ✔ | ✘ |
| Naive stagionale | ✔ | ✘ | ✔ |
| Holt-Winters additivo | ✔ | ✔ | ✔ |

Tutti implementati da zero con NumPy. Dettagli in
[`docs/forecasting.md`](docs/forecasting.md).

### Metriche di accuratezza

| Metrica | Formula | Ruolo |
|---|---|---|
| **MAE** | `(1/n)·Σ\|y−f\|` | errore medio in cartoni |
| **RMSE** | `√[(1/n)·Σ(y−f)²]` | penalizza gli errori grandi; stima di σ per la scorta di sicurezza |
| **MAPE** | `(100/n′)·Σ\|y−f\|/\|y\|` | **criterio primario** di selezione; adimensionale |
| Bias | `(1/n)·Σ(f−y)` | diagnostica di sovra/sotto-stima |
| sMAPE | `(100/n)·Σ 2\|y−f\|/(\|y\|+\|f\|)` | alternativa simmetrica |

I valori nulli sono **esclusi** dal calcolo del MAPE; se il MAPE non è
calcolabile il criterio ripiega sull'**RMSE** (fallback documentato).

### Modelli di scorta

| Componente | Formula | Leva principale |
|---|---|---|
| **Scorta ciclica** | `D × R / 2` | periodo di riesame (lineare) |
| **Scorta di sicurezza** | `z × σ × √(IP)` | variabilità (lineare), lead time (radice) |
| **Scorta anticipata** | `max C(t) − min C(t)` da produzione livellata | stagionalità |
| **Scorta pipeline** | `D × L` (legge di Little) | lead time (lineare) |

`D` = domanda media **prevista**; `R` = periodo di riesame; `L` = lead time;
`IP` = intervallo di protezione; `σ` = dev. standard dell'**errore
previsionale out-of-sample**; `z` = quantile della normale standard.

Derivazioni e ipotesi in [`docs/inventory.md`](docs/inventory.md).

### Simulazione degli scenari

Le leve **non sono cosmetiche**: le tre leve di domanda agiscono sui
parametri del processo generatore e la serie viene **rigenerata** con lo
stesso seed. Con tutti i moltiplicatori a 1,0 la serie coincide esattamente
con il dataset di base. Il file `data/demand_history.csv` **non viene mai
sovrascritto** dalla simulazione.

| Leva | Intervallo | Effetto verificato da test |
|---|---|---|
| Variabilità | 0,0 – 3,0 | ↑ incertezza previsionale, ↑ scorta di sicurezza |
| Trend | −2,0 – 4,0 | ↑ domanda prevista, ↑ fabbisogno |
| Stagionalità | 0,0 – 3,0 | ↑ picchi, ↑ scorta anticipata |
| Lead time | 0,5 – 8,0 mesi | ↑ pipeline (lineare), ↑ sicurezza (radice) |
| Livello di servizio | 90% – 99% | ↑ scorta di sicurezza |
| Periodo di riesame | 0,5 – 6,0 mesi | ↑ scorta ciclica |

Dettagli in [`docs/scenarios.md`](docs/scenarios.md).

---

## 4. Tecnologie

| Pacchetto | Versione | Ruolo |
|---|---|---|
| Python | 3.12 | linguaggio |
| Streamlit | 1.65.0 | dashboard web interattiva |
| pandas | 2.2.3 | manipolazione serie storiche |
| NumPy | 2.1.3 | calcolo numerico e generazione casuale |
| Plotly | 5.24.1 | grafici interattivi |
| SciPy | 1.14.1 | quantili della normale (fattore z) |
| PyArrow | 18.1.0 | serializzazione tabelle (richiesto da Streamlit) |
| pytest | 8.3.4 | test automatici |

**L'applicazione funziona interamente offline** dopo l'installazione delle
dipendenze: nessuna chiamata a servizi esterni.

---

## 5. Installazione

### Requisiti

- Python **3.10 o superiore** (sviluppato e testato su 3.12.10)
- circa 400 MB di spazio su disco per l'ambiente virtuale

### Windows (PowerShell)

```powershell
# 1. Clonare il repository
git clone <URL-DEL-REPOSITORY>
cd PW24_Ferrero

# 2. Creare l'ambiente virtuale
python -m venv .venv

# 3. Attivare l'ambiente virtuale
.\.venv\Scripts\Activate.ps1

# 4. Installare le dipendenze
pip install -r requirements.txt
```

> Se PowerShell blocca l'attivazione con un errore di *execution policy*,
> eseguire una sola volta:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> In alternativa, da **Prompt dei comandi (cmd)**: `.\.venv\Scripts\activate.bat`

### Linux / macOS

```bash
git clone <URL-DEL-REPOSITORY>
cd PW24_Ferrero
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 6. Esecuzione

### Avviare la dashboard

```bash
streamlit run app.py
```

L'applicazione si apre automaticamente nel browser all'indirizzo
<http://localhost:8501>.

> **Avvio alternativo.** Se il comando `streamlit` non è disponibile o viene
> bloccato da policy di sicurezza del sistema, usare il modulo Python:
> ```bash
> python -m streamlit run app.py
> ```

### Rigenerare il dataset sintetico

```bash
python -m src.data_generator
```

Il comando ricostruisce i tre file CSV in `data/` con il seed di progetto
(24) e stampa le statistiche descrittive di controllo. Lo stesso risultato è
ottenibile dal pulsante **«🔄 Rigenera dataset sintetico»** nelle opzioni
avanzate della sidebar.

Poiché il seed è fissato, **la rigenerazione produce sempre lo stesso
dataset**: i risultati riportati nella relazione sono riproducibili.

### Generare figure e tabelle per la relazione

```bash
python -m scripts.generate_report_assets
```

Produce 23 figure Plotly interattive in `report/figures/` (file HTML
autonomi, apribili in qualsiasi browser anche offline), quattro tabelle CSV e
una sintesi in Markdown in `report/results/`.

### Eseguire i test

```bash
pytest
```

Output atteso:

```
264 passed in ~5s
```

Opzioni utili:

```bash
pytest -v                          # output dettagliato
pytest tests/test_inventory.py     # un solo modulo
pytest -k "lead_time"              # solo i test sul lead time
```

---

## 7. Struttura del progetto

```
PW24_Ferrero/
│
├── app.py                      # Dashboard Streamlit (solo presentazione)
├── requirements.txt            # Dipendenze con versioni fissate
├── pytest.ini                  # Configurazione test
├── README.md                   # Questo file
├── .gitignore
│
├── data/                       # Dataset sintetico
│   ├── demand_history.csv          # 192 righe (formato lungo)
│   ├── demand_history_wide.csv     # 48 righe (formato pivot)
│   ├── product_parameters.csv      # parametri di generazione
│   └── README.md                   # dizionario dei dati
│
├── src/                        # Logica applicativa (indipendente dalla UI)
│   ├── config.py                   # costanti e anagrafica prodotti
│   ├── data_generator.py           # generazione dataset sintetico
│   ├── data_validation.py          # 11 controlli di validità
│   ├── forecasting.py              # 5 metodi previsionali
│   ├── metrics.py                  # MAE, RMSE, MAPE, Bias, sMAPE
│   ├── evaluation.py               # split cronologico e selezione modello
│   ├── inventory.py                # 4 componenti di scorta
│   ├── scenarios.py                # motore di simulazione
│   ├── charts.py                   # figure Plotly
│   ├── narrative.py                # commenti gestionali dinamici
│   └── utils.py                    # formattazione italiana
│
├── tests/                      # 264 test automatici
│   ├── conftest.py
│   ├── test_data_generator.py
│   ├── test_data_validation.py
│   ├── test_forecasting.py
│   ├── test_metrics.py
│   ├── test_inventory.py
│   ├── test_scenarios.py
│   └── test_dashboard.py
│
├── scripts/
│   └── generate_report_assets.py
│
├── docs/                       # Documentazione tecnica (italiano)
│   ├── company.md                  # impresa, prodotti, contesto
│   ├── dataset.md                  # origine e generazione dati
│   ├── forecasting.md              # metodi e valutazione
│   ├── inventory.md                # modelli di scorta
│   ├── scenarios.md                # simulazione scenari
│   ├── methodology.md              # metodologia, risultati, limiti
│   ├── technical_architecture.md   # architettura software
│   ├── pw24_compliance.md          # audit di conformità
│   └── references.md               # fonti
│
└── report/
    ├── relazione_pw24.md           # bozza relazione finale
    ├── figures/                    # 23 figure HTML interattive
    └── results/                    # tabelle CSV + sintesi Markdown
```

---

## 8. La dashboard

L'interfaccia è **interamente in italiano** e articolata in otto sezioni.

**Sidebar — Configurazione**: prodotto, metodo previsivo, orizzonte, finestra
media mobile, alpha, variabilità, trend, stagionalità, lead time, livello di
servizio, periodo di riesame, opzioni avanzate.

| Sezione | Contenuto |
|---|---|
| **1 · Scenario di analisi** | Parametri correnti, scheda prodotto, confronto base/scenario, profilo stagionale, statistiche |
| **2 · Domanda storica e prevista** | Grafico con addestramento, test, previsione sul test, previsione futura e banda di incertezza |
| **3 · Confronto dei metodi previsionali** | Tabella MAE/RMSE/MAPE/Bias con il migliore evidenziato, grafico a barre, commento sulla selezione |
| **4 · Composizione delle scorte** | Barra impilata, grafico ad anello, tabella con le formule applicate |
| **5 · Indicatori sintetici (KPI)** | 12 KPI: domanda, lead time, servizio, quattro componenti, totale, copertura, MAPE, σ |
| **6 · Analisi dello scenario** | Interpretazione gestionale **generata dinamicamente dai valori calcolati** |
| **7 · Confronto fra scenari** | Due configurazioni A/B affiancate, tabella di variazione, grafici comparativi |
| **8 · Quadro di sintesi** | Tutti e quattro i prodotti a confronto, con il metodo migliore per ciascuno |

---

## 9. Risultati principali

### Il metodo migliore cambia per ogni prodotto

| Prodotto | Metodo migliore | MAE | RMSE | MAPE |
|---|---|---:|---:|---:|
| Nutella | Holt-Winters additivo | 649,1 | 950,4 | **4,95%** |
| Kinder Cioccolato | Smorzamento esponenziale | 910,5 | 1.083,3 | **9,78%** |
| Ferrero Rocher | Naive stagionale | 599,2 | 719,9 | **9,91%** |
| Kinder Happy Hippo | Regressione lineare | 1.010,3 | 1.145,9 | **24,60%** |

Su Ferrero Rocher lo scarto fra il metodo migliore (9,91%) e il peggiore
(80,93%) è di **71 punti percentuali**: la scelta del modello non è un
dettaglio tecnico.

### Composizione delle scorte (scenario baseline)

Lead time 2 mesi, servizio 95%, riesame 1 mese, orizzonte 12 mesi.

| Prodotto | Ciclica | Sicurezza | Anticipata | Pipeline | **Totale** | Copertura |
|---|---:|---:|---:|---:|---:|---:|
| Nutella | 6.683 | 2.211 | 3.479 | 26.732 | **39.105** | 2,9 mesi |
| Kinder Cioccolato | 5.075 | 2.520 | 0 | 20.299 | **27.893** | 2,7 mesi |
| Ferrero Rocher | 3.187 | 1.675 | 11.272 | 12.748 | **28.882** | 4,5 mesi |
| Kinder Happy Hippo | 2.177 | 2.665 | 324 | 8.709 | **13.876** | 3,2 mesi |

### Confronto fra scenari (Ferrero Rocher)

| Indicatore | A — Filiera stabile | B — Filiera sotto stress | Var. % |
|---|---:|---:|---:|
| Scorta di sicurezza | 833 | 7.782 | **+834,0%** |
| Scorta pipeline | 13.065 | 30.284 | +131,8% |
| **Scorta totale** | **28.771** | **51.697** | **+79,7%** |
| Copertura | 4,4 mesi | 8,5 mesi | +93,8% |

La scorta di sicurezza ha il moltiplicatore maggiore, ma è la **pipeline** a
spiegare il **75%** dell'incremento assoluto.

---

## 10. Interpretazione accademica

**Variabilità sistematica ≠ variabilità casuale.** Ferrero Rocher ha il
coefficiente di variazione più alto (39,9%) ma un MAPE del 9,91%: la sua
variabilità è prevalentemente **stagionale**, quindi anticipabile. Kinder
Happy Hippo ha variabilità minore (26,8%) ma MAPE più che doppio (24,60%):
la sua variabilità è **casuale** e irriducibile. La prima si gestisce con la
scorta **anticipata**, la seconda con la scorta di **sicurezza**.

**Il lead time è la leva dominante.** La scorta pipeline rappresenta fra il
44% e il 73% del magazzino totale e cresce **linearmente** con il lead time,
mentre la scorta di sicurezza cresce con la **radice quadrata**. Ridurre i
tempi di filiera libera più capitale che ridurre il livello di servizio.

**La complessità non garantisce l'accuratezza.** Holt-Winters, il metodo più
sofisticato, vince su un solo prodotto su quattro ed è battuto dal
semplicissimo naive stagionale proprio sulla serie più stagionale.

**Il livello di servizio è una decisione economica.** Il fattore `z` cresce
in modo più che proporzionale avvicinandosi al 100%: ogni punto oltre il
97,5% ha un costo marginale crescente.

---

## 11. Limiti

Limiti principali (elenco completo in
[`docs/methodology.md`](docs/methodology.md) §7.3):

- **Dati sintetici**: i risultati hanno valore metodologico, non predittivo.
- **Lead time deterministico**: con lead time variabile la scorta di
  sicurezza risulterebbe maggiore (sottostima attuale).
- **Errori previsionali assunti indipendenti**: con autocorrelazione il
  fabbisogno sarebbe superiore.
- **Nessun costo monetario**: si dimensionano quantità, non si ottimizzano
  costi.
- **Parametri di Holt-Winters non ottimizzati**.
- **Banda di incertezza costante** sull'orizzonte, dichiarata come stima
  empirica e non come intervallo statistico.
- **Scorta anticipata dipendente dal metodo previsionale**: con previsioni
  piatte risulta nulla anche su prodotti stagionali (effetto visibile su
  Kinder Cioccolato e discusso in documentazione).
- **Shelf life non modellata**: coperture elevate comportano rischio di
  obsolescenza non quantificato.

---

## 12. Documentazione

| Documento | Contenuto |
|---|---|
| [`docs/README.md`](docs/README.md) | Indice della documentazione e percorsi di lettura consigliati |
| [`docs/company.md`](docs/company.md) | Ferrero: profilo, contesto produttivo, commerciale e logistico; i quattro prodotti |
| [`docs/dataset.md`](docs/dataset.md) | Modello generatore, parametri, riproducibilità, validazione |
| [`docs/forecasting.md`](docs/forecasting.md) | I 5 metodi, le metriche, lo split cronologico, il criterio di selezione |
| [`docs/inventory.md`](docs/inventory.md) | Le 4 componenti di scorta: derivazioni, ipotesi, risultati |
| [`docs/scenarios.md`](docs/scenarios.md) | Motore di simulazione, effetti delle leve, confronto A/B |
| [`docs/methodology.md`](docs/methodology.md) | Metodologia, sintesi risultati, 18 limiti, 12 sviluppi futuri |
| [`docs/technical_architecture.md`](docs/technical_architecture.md) | Architettura, moduli, scelte progettuali, strategia di test |
| [`docs/pw24_compliance.md`](docs/pw24_compliance.md) | Audit di conformità: ogni requisito mappato su codice, dashboard e documentazione |
| [`docs/references.md`](docs/references.md) | Fonti aziendali, accademiche e tecniche |
| [`report/relazione_pw24.md`](report/relazione_pw24.md) | Bozza della relazione finale |

---

## 13. Riproducibilità

Il progetto è integralmente riproducibile. Un nuovo utente deve:

```bash
git clone <URL>                          # 1. clonare
cd PW24_Ferrero
python -m venv .venv                     # 2. creare l'ambiente
.\.venv\Scripts\Activate.ps1             #    (Windows)
pip install -r requirements.txt          # 3. installare
python -m src.data_generator             # 4. rigenerare i dati
pytest                                   # 5. eseguire i test
streamlit run app.py                     # 6. avviare la dashboard
```

Il **seed fissato a 24** garantisce che il dataset rigenerato sia
bit-per-bit identico a quello versionato, e quindi che tutti i numeri
riportati in questo README e nella relazione siano ottenibili da chiunque.

---

## 14. Licenza e uso

Progetto realizzato a **scopo didattico** nell'ambito del Project Work 24.
Il codice è liberamente consultabile e riutilizzabile per finalità di studio.

I marchi Ferrero, Nutella, Kinder, Ferrero Rocher e Kinder Happy Hippo
appartengono ai rispettivi titolari e sono citati esclusivamente a fini
descrittivi nel contesto di una simulazione accademica, senza alcun rapporto
di collaborazione, sponsorizzazione o approvazione da parte di Ferrero.
