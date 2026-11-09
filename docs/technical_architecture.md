# 6. Architettura software

Questo capitolo descrive l'organizzazione del codice, le scelte progettuali e
la strategia di test.

---

## 6.1 Principio architetturale

Il progetto è costruito attorno a un'unica regola:

> **La logica di calcolo non conosce l'interfaccia.**

Tutta la logica previsionale, di gestione scorte e di simulazione risiede nel
package `src/` e non importa mai Streamlit. Il file `app.py` contiene
**esclusivamente** presentazione: legge i widget, chiama funzioni di `src/`,
visualizza i risultati.

Le conseguenze pratiche sono tre:

1. **Testabilità.** Il 90% del codice è verificabile con pytest senza avviare
   alcun server. I test girano in meno di cinque secondi.
2. **Riusabilità.** Lo script `scripts/generate_report_assets.py` produce
   figure e tabelle per la relazione riutilizzando le stesse funzioni della
   dashboard, senza duplicare una riga di logica.
3. **Sostituibilità dell'interfaccia.** Se un domani si volesse esporre il
   modello via API o CLI, non servirebbe riscrivere nulla di sostanziale.

---

## 6.2 Struttura delle cartelle

```
PW24_Ferrero/
│
├── app.py                      # Dashboard Streamlit (solo presentazione)
├── requirements.txt            # Dipendenze con versioni fissate
├── pytest.ini                  # Configurazione dei test
├── README.md                   # Guida principale
├── .gitignore
│
├── data/                       # Dataset sintetico
│   ├── demand_history.csv          # formato lungo (192 righe)
│   ├── demand_history_wide.csv     # formato pivot (48 righe)
│   ├── product_parameters.csv      # parametri di generazione
│   └── README.md                   # dizionario dei dati
│
├── src/                        # Logica applicativa (nessun import di Streamlit)
│   ├── __init__.py
│   ├── config.py                   # costanti, anagrafica prodotti, parametri
│   ├── data_generator.py           # generazione del dataset sintetico
│   ├── data_validation.py          # validazione e caricamento
│   ├── forecasting.py              # 5 metodi previsionali
│   ├── metrics.py                  # MAE, RMSE, MAPE, Bias, sMAPE
│   ├── evaluation.py               # split cronologico, selezione modello
│   ├── inventory.py                # 4 componenti di scorta
│   ├── scenarios.py                # motore di simulazione
│   ├── charts.py                   # figure Plotly
│   ├── narrative.py                # commenti gestionali dinamici
│   └── utils.py                    # formattazione italiana
│
├── tests/                      # 264 test automatici
│   ├── __init__.py
│   ├── conftest.py                 # fixture condivise
│   ├── test_data_generator.py      # 31 test
│   ├── test_data_validation.py     # 21 test
│   ├── test_forecasting.py         # 64 test
│   ├── test_metrics.py             # 34 test
│   ├── test_inventory.py           # 42 test
│   ├── test_scenarios.py           # 50 test
│   └── test_dashboard.py           # 22 test (harness ufficiale Streamlit)
│
├── scripts/
│   ├── __init__.py
│   └── generate_report_assets.py   # figure e tabelle per la relazione
│
├── docs/                       # Documentazione tecnica (italiano)
│   ├── README.md                   # indice e percorsi di lettura
│   ├── company.md                  # impresa, prodotti, contesto
│   ├── dataset.md                  # origine e generazione dei dati
│   ├── forecasting.md              # metodi e valutazione
│   ├── inventory.md                # modelli di scorta
│   ├── scenarios.md                # simulazione degli scenari
│   ├── methodology.md              # metodologia, limiti, sviluppi
│   ├── technical_architecture.md   # questo documento
│   ├── pw24_compliance.md          # audit di conformità alla specifica
│   └── references.md               # fonti
│
└── report/
    ├── relazione_pw24.md           # bozza della relazione finale
    ├── figures/                    # 23 figure Plotly interattive (HTML)
    └── results/                    # tabelle CSV + sintesi Markdown
```

---

## 6.3 Dipendenze fra i moduli

```
                        config.py
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
  data_generator.py   data_validation.py    utils.py
          │                 │
          │                 ▼
          │          forecasting.py ◄── metrics.py
          │                 │
          │                 ▼
          │           evaluation.py
          │                 │
          └────────┬────────┤
                   ▼        ▼
              scenarios.py  inventory.py
                   │
          ┌────────┴────────┐
          ▼                 ▼
      charts.py        narrative.py
          │                 │
          └────────┬────────┘
                   ▼
                app.py
```

Il grafo è **aciclico** e orientato in un'unica direzione: nessun modulo di
livello inferiore importa un modulo di livello superiore. `config.py` è
l'unico modulo importato da quasi tutti gli altri, e non importa nulla del
progetto.

---

## 6.4 Responsabilità dei moduli

| Modulo | Responsabilità | Non fa |
|---|---|---|
| `config.py` | Costanti, anagrafica prodotti, parametri di default | Nessun calcolo |
| `data_generator.py` | Generazione e salvataggio del dataset sintetico | Non legge dati esterni |
| `data_validation.py` | 11 controlli di validità, caricamento CSV | Non modifica i dati |
| `forecasting.py` | 5 metodi previsionali | Non valuta l'accuratezza |
| `metrics.py` | 5 indicatori di errore | Non conosce i metodi |
| `evaluation.py` | Split cronologico, confronto, selezione, banda | Non calcola scorte |
| `inventory.py` | 4 componenti di scorta + piano complessivo | Non prevede |
| `scenarios.py` | Orchestrazione dell'intera catena | Non disegna grafici |
| `charts.py` | Figure Plotly in italiano | Nessun calcolo |
| `narrative.py` | Commenti gestionali dinamici | Nessun calcolo |
| `utils.py` | Formattazione italiana, statistiche descrittive | Nessuna logica di dominio |
| `app.py` | Presentazione, widget, gestione errori utente | Nessuna logica di dominio |

---

## 6.5 Scelte progettuali

### Metodi previsionali scritti da zero

I cinque metodi sono implementati con NumPy anziché con `statsmodels`. Le
ragioni:

- **Trasparenza didattica.** La formulazione matematica è leggibile
  direttamente nel codice; un professore può verificare la ricorsione di
  Holt-Winters riga per riga.
- **Dipendenze ridotte.** `statsmodels` aggiungerebbe un pacchetto pesante
  per cinque funzioni di poche righe.
- **Controllo sull'inizializzazione.** L'inizializzazione di Holt-Winters è
  deterministica e documentata, anziché affidata a un'ottimizzazione
  numerica opaca.

Il costo è che Holt-Winters non ottimizza i parametri: è una semplificazione
dichiarata (cfr. [`forecasting.md`](forecasting.md) §E).

### Registro dei metodi

```python
METHOD_REGISTRY: Dict[str, Callable[..., ForecastResult]] = {
    "Media mobile": moving_average_forecast,
    "Smorzamento esponenziale": simple_exponential_smoothing,
    ...
}
```

Dashboard e motore di valutazione **iterano** sul registro anziché contenere
elenchi hard-coded. Aggiungere un sesto metodo richiede: scrivere la
funzione, aggiungere una voce al registro, dichiarare i parametri
configurabili. Nessuna modifica a `app.py` o `evaluation.py`.

### Dataclass immutabili per la configurazione

`ScenarioConfig` e `ProductParameters` sono `@dataclass(frozen=True)`. La
scelta abilita tre proprietà:

- sono **hashable**, quindi utilizzabili come chiave della cache di Streamlit
  (`@st.cache_data`): due scenari identici non vengono ricalcolati;
- le modifiche avvengono con `dataclasses.replace()`, che produce una copia,
  rendendo impossibile alterare per errore lo stato condiviso;
- i confronti di uguaglianza sono strutturali, il che semplifica i test.

### Errori tipizzati per dominio

Ogni modulo definisce la propria eccezione:
`DataValidationError`, `ForecastingError`, `MetricsError`,
`InventoryError`, `EvaluationError`, `ScenarioError`.

Tutte portano messaggi **in italiano, rivolti all'utente finale**. La
dashboard cattura le eccezioni di dominio e le mostra con `st.error`, senza
mai esporre un traceback:

```python
try:
    outcome = calcola_scenario(config)
except ScenarioError as exc:
    mostra_errore("Configurazione dello scenario non valida", str(exc))
    st.stop()
```

### Gestione della cache

Tre funzioni sono decorate con `@st.cache_data`: caricamento del dataset,
simulazione di uno scenario, valutazione di tutti i prodotti. Poiché
`ScenarioConfig` è hashable, la cache funziona per configurazione: muovere un
cursore e poi tornare indietro non ricalcola nulla.

Il pulsante di rigenerazione del dataset invalida esplicitamente la cache con
`st.cache_data.clear()`.

---

## 6.6 Strategia di test

### Numeri

**264 test**, tempo di esecuzione **inferiore a 5 secondi**.

| File | Test | Oggetto |
|---|---:|---|
| `test_data_generator.py` | 31 | struttura, dominio, riproducibilità, profili differenziati |
| `test_data_validation.py` | 21 | 11 controlli + gestione errori file |
| `test_forecasting.py` | 64 | 5 metodi su serie deterministiche + casi limite |
| `test_metrics.py` | 34 | formule, casi limite, split cronologico, selezione |
| `test_inventory.py` | 42 | formule, monotonie, piano complessivo |
| `test_scenarios.py` | 50 | effetti delle leve, validazione, confronto |
| `test_dashboard.py` | 22 | avvio, sezioni, widget, interazione, grafici, commenti |

### Tre livelli di verifica

**1. Correttezza numerica su casi calcolati a mano.** Dove possibile i test
confrontano il risultato con un valore derivato analiticamente:

```python
def test_smorzamento_ricorsione_esatta():
    serie = np.array([100.0, 200.0, 300.0])
    risultato = simple_exponential_smoothing(serie, horizon=1, alpha=0.5)
    # L0 = 100 ; L1 = 0.5*200 + 0.5*100 = 150 ; L2 = 0.5*300 + 0.5*150 = 225
    assert risultato.forecast[0] == pytest.approx(225.0)
```

**2. Proprietà matematiche.** Alcune proprietà devono valere sempre,
indipendentemente dai dati:

- `RMSE ≥ MAE` (disuguaglianza di Jensen), verificata su 20 serie casuali;
- la scorta anticipata non è mai negativa, verificata su 25 serie casuali;
- la somma delle quote percentuali è sempre 100;
- quadruplicare il lead time raddoppia esattamente la scorta di sicurezza.

**3. Requisiti della specifica.** I requisiti direzionali del PW24 sono
tradotti in test espliciti, elencati in [`scenarios.md`](scenarios.md) §5.4.

### Serie deterministiche come banco di prova

I metodi previsionali sono testati principalmente su serie di cui si conosce
analiticamente il comportamento:

- **serie costante** → ogni metodo deve prevedere esattamente la costante;
- **serie lineare perfetta** → la regressione deve recuperare pendenza e
  intercetta esatte, con residui nulli;
- **serie trend + sinusoide** → Holt-Winters deve ottenere errore relativo
  inferiore al 5%.

Questo rende i test **stringenti e stabili**: non dipendono dalla particolare
realizzazione casuale del dataset.

### Verifica dell'assenza di fughe di informazione

Il test `test_metodi_ignorano_il_periodo_di_test` moltiplica per 10 i valori
del solo periodo di test e verifica che le previsioni di tutti i metodi
restino identiche. È la garanzia automatica che la valutazione out-of-sample
sia onesta.

### Test della dashboard

`test_dashboard.py` usa `streamlit.testing.v1.AppTest`, l'harness ufficiale
di Streamlit, che esegue l'app in modalità headless e consente di ispezionare
gli elementi prodotti e simulare l'interazione:

```python
def test_aumento_lead_time_aumenta_la_scorta_pipeline():
    istanza = avvia_dashboard()
    lead_time = next(s for s in istanza.sidebar.slider if "Lead time" in s.label)
    lead_time.set_value(1.0).run()
    pipeline_corto = _valore_kpi(istanza, "Scorta pipeline")
    ...
```

È una verifica **end-to-end**: il requisito PW24 è controllato attraverso
l'intera catena, dal widget al KPI visualizzato.

---

## 6.7 Note sulle dipendenze

| Pacchetto | Versione | Ruolo |
|---|---|---|
| `streamlit` | 1.65.0 | dashboard web |
| `pandas` | 2.2.3 | manipolazione serie storiche |
| `numpy` | 2.1.3 | calcolo numerico, generazione casuale |
| `plotly` | 5.24.1 | grafici interattivi |
| `scipy` | 1.14.1 | `norm.ppf` per il fattore z |
| `pyarrow` | 18.1.0 | serializzazione tabelle (richiesto da Streamlit) |
| `pytest` | 8.3.4 | test automatici |

Le versioni sono **fissate** per garantire la riproducibilità dei risultati
riportati nella relazione.

**Uso di SciPy.** SciPy è impiegato per una sola funzione: `norm.ppf`, il
quantile della normale standard usato per il fattore di sicurezza `z`. La
dipendenza è giustificata perché un'implementazione manuale della funzione
quantile inversa sarebbe meno accurata e più fragile di quella di una
libreria scientifica consolidata.

**Nessuna connessione di rete.** Dopo l'installazione dei pacchetti
l'applicazione funziona **interamente offline**: non esistono chiamate a API,
download di dati o servizi esterni.

---

## 6.8 Qualità del codice

Convenzioni adottate:

- **Type hints** su tutte le funzioni pubbliche.
- **Docstring** su ogni modulo, classe e funzione pubblica, con la
  formulazione matematica esplicitata dove rilevante.
- **Commenti esplicativi in italiano** sui passaggi non ovvi (scelte di
  modellazione, ipotesi, accorgimenti tecnici).
- **Nomi di dominio in italiano** nell'interfaccia (`costruisci_sidebar`,
  `sezione_scenario`, `mostra_errore`), **identificatori tecnici in inglese**
  in `src/` (`safety_stock`, `chronological_split`), secondo la convenzione
  prevalente nel codice scientifico Python.
- **Stato globale assente**: nessuna variabile modificata a runtime fuori
  dalle funzioni.
- **`__all__`** dichiarato in ogni modulo di `src/` per esplicitare l'API
  pubblica.
