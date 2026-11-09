# 5. Simulazione degli scenari

Questo capitolo descrive il motore di simulazione: come le leve della
dashboard agiscono sui calcoli, quali effetti producono e come i due scenari
di confronto sono costruiti.

Codice di riferimento: `src/scenarios.py`.

---

## 5.1 Il requisito

La specifica PW24 è esplicita su un punto: i controlli di scenario **non
devono limitarsi a cambiare le etichette**. Devono modificare realmente i
calcoli e produrre domanda, previsioni e fabbisogni di scorta aggiornati,
con effetti direzionalmente corretti:

| Se aumenta… | Allora deve aumentare… |
|---|---|
| la variabilità | l'incertezza previsionale e la scorta di sicurezza |
| il lead time | la scorta pipeline e la scorta di sicurezza |
| la stagionalità | l'intensità dei picchi e la scorta anticipata |
| il trend | la previsione futura e il fabbisogno complessivo |

Tutti e quattro gli effetti sono implementati e **verificati da test
automatici** (`tests/test_scenarios.py`).

---

## 5.2 Il principio di funzionamento

### Rigenerazione, non deformazione

Le tre leve di domanda (variabilità, trend, stagionalità) **non deformano**
la serie storica esistente moltiplicandola per un fattore. Agiscono invece
sui **parametri del processo generatore**, e la serie viene **rigenerata da
zero** con lo stesso seed casuale.

```
parametri di base          leve di scenario
       │                          │
       └──────────┬───────────────┘
                  ▼
      parametri di scenario  (ProductParameters.scaled)
                  ▼
        generate_product_series(seed invariato)
                  ▼
           serie di scenario
                  ▼
   valutazione metodi → previsione → piano di scorta
```

Questa scelta ha due conseguenze importanti.

**Coerenza statistica.** Lo scenario è una realizzazione legittima dello
stesso modello generatore, non una deformazione arbitraria. Aumentare la
stagionalità produce una serie che *potrebbe* essere stata generata da un
prodotto più stagionale, con tutte le proprietà statistiche coerenti.

**Isolamento della causa.** Poiché il seed resta invariato, la sequenza di
shock casuali è la stessa. Qualunque differenza osservata fra scenario e
baseline è attribuibile **esclusivamente** alla leva modificata, non a una
diversa estrazione casuale. Senza questa accortezza i confronti sarebbero
inquinati dal rumore di campionamento.

### Proprietà di identità

Con tutti i moltiplicatori pari a 1,0 la serie di scenario **coincide
esattamente** con il dataset storico di base. È la proprietà che rende il
confronto interpretabile, ed è verificata dal test
`test_leve_neutre_riproducono_il_dataset_di_base`.

### Separazione dei dati

Il file `data/demand_history.csv` **non viene mai modificato** dalla
simulazione: lo scenario vive interamente in memoria. L'oggetto
`ScenarioOutcome` conserva *entrambe* le serie (`baseline_series` e
`scenario_series`), così che la dashboard possa sovrapporle graficamente e
l'utente veda esattamente cosa è cambiato.

La proprietà è verificata dal test
`test_dataset_storico_non_viene_sovrascritto`, che confronta i byte del file
prima e dopo una simulazione.

---

## 5.3 Le leve e la loro azione

### Leve di domanda (agiscono sul generatore)

| Leva | Intervallo | Parametri riscalati |
|---|---|---|
| **Variabilità** | 0,0 – 3,0 | `noise_std`, `promotion_amplitude` |
| **Trend** | −2,0 – 4,0 | `trend_rate` |
| **Stagionalità** | 0,0 – 3,0 | `seasonal_amplitude`, `festive_profile` |

**Variabilità.** Riscala sia il rumore casuale sia l'ampiezza dei picchi
promozionali, perché entrambi sono fonti di imprevedibilità. A 0,0 la serie
diventa quasi deterministica (resta solo la componente sistematica); a 3,0 il
rumore triplica.

**Trend.** Riscala il tasso di crescita. A 0,0 il trend è annullato e la
serie diventa stazionaria attorno al livello base; **valori negativi
invertono la direzione**, generando una domanda in calo. Questa possibilità
è deliberata: un'impresa deve saper pianificare anche il declino di un
prodotto.

**Stagionalità.** Riscala sia l'ampiezza sinusoidale sia il profilo festivo.
A 0,0 la serie è completamente destagionalizzata; a 3,0 i picchi natalizi di
Ferrero Rocher diventano estremi.

### Leve logistiche (agiscono sul piano di scorta)

| Leva | Intervallo | Componente influenzata |
|---|---|---|
| **Lead time** | 0,5 – 8,0 mesi | pipeline (lineare), sicurezza (√) |
| **Livello di servizio** | 90% – 99% | sicurezza (via `z`) |
| **Periodo di riesame** | 0,5 – 6,0 mesi | ciclica (lineare) |

Queste leve **non modificano la serie di domanda**: il lead time è una
caratteristica della filiera, non del mercato. Il test
`test_lead_time_non_altera_la_serie_di_domanda` verifica esplicitamente
questa separazione concettuale.

### Leve previsionali

| Leva | Opzioni | Effetto |
|---|---|---|
| **Metodo previsivo** | automatico + 5 metodi | determina la previsione usata |
| **Orizzonte** | 3, 6, 12 mesi | lunghezza della proiezione |
| **Finestra media mobile** | 3, 6, 12 mesi | parametro della media mobile |
| **Alpha** | 0,05 – 1,00 | parametro dello smorzamento |
| **Mesi di test** | 6 – 18 | ampiezza della validazione |

La modalità **automatica** (predefinita) seleziona il metodo con MAPE
out-of-sample minimo *sulla serie di scenario*, non su quella di base: se le
leve cambiano la natura della domanda, può cambiare anche il metodo ottimale.
È un comportamento voluto e didatticamente interessante.

---

## 5.4 Verifica degli effetti

### Prova numerica (prodotto: Ferrero Rocher, orizzonte 12 mesi)

Partendo dalla configurazione baseline (variabilità ×1, lead time 2 mesi,
servizio 95%, riesame 1 mese) e modificando **una leva alla volta**:

| Configurazione | Sicurezza | Pipeline | Anticipata | Ciclica | **Totale** |
|---|---:|---:|---:|---:|---:|
| **Baseline** | 1.675 | 12.748 | 11.272 | 3.187 | **28.882** |
| Variabilità ×2 | **3.480** | 12.114 | 10.603 | 3.028 | 29.225 |
| Lead time 5 mesi | **2.648** | **31.870** | 11.272 | 3.187 | **48.977** |
| Stagionalità ×2 | 1.842 | 14.679 | **22.348** | 3.670 | 42.540 |
| Trend ×3 | 2.035 | **15.615** | 14.127 | **3.904** | 35.681 |

Lettura riga per riga:

- **Variabilità ×2** → la scorta di sicurezza passa da 1.675 a 3.480
  (**+108%**), coerentemente con la linearità in `σ`. Le altre componenti
  variano solo marginalmente, per effetto della diversa previsione.
- **Lead time 2 → 5 mesi** → la pipeline passa da 12.748 a 31.870, cioè
  **esattamente ×2,5** come previsto dalla linearità; la sicurezza passa da
  1.675 a 2.648, cioè **×1,58 ≈ √2,5** come previsto dalla radice quadrata.
  Le due diverse leggi di crescita sono verificabili numericamente.
- **Stagionalità ×2** → la scorta anticipata passa da 11.272 a 22.348,
  cioè **praticamente il doppio**: è la leva che la governa.
- **Trend ×3** → crescono le componenti proporzionali alla domanda (pipeline
  +22%, ciclica +22%), perché la domanda media prevista aumenta.

### Copertura con test automatici

| Requisito verificato | Test |
|---|---|
| Variabilità ↑ ⇒ dispersione ↑ | `test_variabilita_aumenta_la_dispersione_della_domanda` |
| Variabilità ↑ ⇒ scorta sicurezza ↑ | `test_variabilita_aumenta_la_scorta_di_sicurezza` |
| Variabilità ↑ ⇒ incertezza previsionale ↑ | `test_variabilita_aumenta_lincertezza_previsionale` |
| Lead time ↑ ⇒ pipeline ↑ (monotòno) | `test_lead_time_aumenta_la_scorta_pipeline` |
| Lead time ↑ ⇒ sicurezza ↑ | `test_lead_time_aumenta_la_scorta_di_sicurezza` |
| Lead time non altera la domanda | `test_lead_time_non_altera_la_serie_di_domanda` |
| Stagionalità ↑ ⇒ picchi più marcati | `test_stagionalita_accentua_i_picchi` |
| Stagionalità ↑ ⇒ anticipata ↑ | `test_stagionalita_aumenta_la_scorta_anticipata` |
| Trend ↑ ⇒ domanda prevista ↑ | `test_trend_aumenta_la_domanda_prevista` |
| Trend ↑ ⇒ fabbisogno ↑ | `test_trend_aumenta_il_fabbisogno_di_scorta` |
| Servizio ↑ ⇒ sicurezza ↑ (monotòno) | `test_livello_di_servizio_aumenta_la_scorta_di_sicurezza` |
| Riesame ↑ ⇒ ciclica ↑ (proporzionale) | `test_periodo_di_riesame_aumenta_la_scorta_ciclica` |

---

## 5.5 Scenari predefiniti

La dashboard propone cinque configurazioni preimpostate, che l'utente può
comunque personalizzare:

| Nome | Variabilità | Trend | Stagionalità | Lead time | Servizio |
|---|---:|---:|---:|---:|---:|
| Baseline (dataset storico) | ×1,0 | ×1,0 | ×1,0 | 2 mesi | 95% |
| **A — Filiera stabile** | ×0,5 | ×1,0 | ×1,0 | 2 mesi | 95% |
| **B — Filiera sotto stress** | ×2,0 | ×1,0 | ×1,0 | 5 mesi | 99% |
| C — Picco stagionale accentuato | ×1,0 | ×1,0 | ×2,0 | 3 mesi | 97,5% |
| D — Crescita sostenuta | ×1,0 | ×3,0 | ×1,0 | 2 mesi | 95% |

Gli scenari **A** e **B** riproducono i due casi tipici citati dalla
specifica PW24 e sono quelli adottati come confronto di riferimento nella
relazione.

---

## 5.6 Il confronto A/B di riferimento

Prodotto: **Ferrero Rocher**. Orizzonte 12 mesi, periodo di riesame 1 mese.

| Indicatore | A — Filiera stabile | B — Filiera sotto stress | Variazione | Var. % |
|---|---:|---:|---:|---:|
| Domanda media prevista (cartoni/mese) | 6.533 | 6.057 | −476 | −7,3% |
| Dev. std errore previsionale | 358 | 1.496 | +1.138 | **+317,7%** |
| Scorta ciclica | 3.266 | 3.028 | −238 | −7,3% |
| Scorta di sicurezza | 833 | 7.782 | +6.949 | **+834,0%** |
| Scorta anticipata | 11.607 | 10.603 | −1.004 | −8,7% |
| Scorta pipeline | 13.065 | 30.284 | +17.219 | **+131,8%** |
| **Scorta totale** | **28.771** | **51.697** | **+22.926** | **+79,7%** |
| Copertura (mesi) | 4,4 | 8,5 | +4,1 | +93,8% |

### Lettura gestionale

**La scorta totale cresce dell'80%, ma non tutte le componenti si muovono
nello stesso modo.** La scorta di sicurezza cresce di oltre otto volte
(+834%), la pipeline di poco più del doppio (+132%), mentre ciclica e
anticipata **diminuiscono** leggermente.

**Il moltiplicatore maggiore non è il contributo maggiore.** Benché la
sicurezza sia la voce che cresce di più in percentuale, in valore assoluto
la **pipeline** spiega il **75%** dell'aumento complessivo (+17.219 cartoni
su +22.926). Partiva da una base molto più grande. È una distinzione
operativamente decisiva: un manager che volesse contenere l'impatto dovrebbe
agire sul **lead time**, non sul livello di servizio, anche se è
quest'ultimo ad avere l'incremento percentuale più vistoso.

**Perché anticipata e ciclica diminuiscono.** Entrambe dipendono dalla
domanda media prevista, che nello scenario B risulta inferiore del 7,3%.
La maggiore variabilità altera le ultime osservazioni su cui il metodo
previsionale si basa, producendo una previsione leggermente più bassa. È un
effetto di secondo ordine, ma la dashboard lo mostra onestamente anziché
nasconderlo.

**L'incertezza previsionale è la vera variabile nascosta.** La deviazione
standard dell'errore quadruplica (+318%) pur essendo la variabilità della
domanda solo quadruplicata nel rapporto fra i due scenari (da ×0,5 a ×2,0).
Non è un'anomalia: è esattamente ciò che ci si attende, ed è il meccanismo
che trasmette la variabilità alla scorta di sicurezza.

**La copertura quasi raddoppia** (da 4,4 a 8,5 mesi). Per un prodotto
alimentare con shelf life limitata, 8,5 mesi di copertura è un livello che
solleva un problema ulteriore rispetto al solo costo finanziario: il **rischio
di obsolescenza**. È una considerazione che il modello non quantifica ma che
la discussione gestionale deve includere.

---

## 5.7 Il commento gestionale dinamico

La sezione 6 della dashboard genera automaticamente un'analisi in italiano
**costruita sui valori effettivamente calcolati** (`src/narrative.py`). Il
testo non è un modello fisso con segnaposto: cambia struttura, non solo
numeri, in funzione della configurazione.

Esempi di adattamento:

- se la scorta anticipata supera il 5% del totale, il commento spiega il
  meccanismo del livellamento produttivo; altrimenti osserva che il profilo
  di domanda è sufficientemente piatto da renderla marginale;
- se la domanda prevista si discosta di oltre il 2% dalla media storica, il
  commento aggiunge un paragrafo sul trend, altrimenti lo omette;
- il paragrafo di confronto identifica automaticamente **quale componente**
  spiega la maggior parte dello scostamento e **quali leve** differiscono fra
  i due scenari;
- la conclusione gestionale cambia a seconda che la variazione della scorta
  totale sia superiore a +15%, inferiore a −15%, oppure contenuta: nel terzo
  caso il commento osserva che cambia la **composizione** del rischio anziché
  il suo livello.

Due test automatici verificano che il meccanismo funzioni:
`test_commenti_citano_valori_calcolati` controlla che i testi contengano
cifre e abbiano lunghezza significativa;
`test_commenti_cambiano_con_lo_scenario` verifica che due configurazioni
diverse producano testi diversi.

---

## 5.8 Gestione degli errori di configurazione

Ogni `ScenarioConfig` è validata prima dell'esecuzione. I controlli
restituiscono messaggi in italiano, aggregati in un unico elenco:

| Condizione | Messaggio |
|---|---|
| Prodotto inesistente | «Prodotto 'X' non presente in anagrafica. Prodotti ammessi: …» |
| Lead time negativo | «Il lead time non può essere negativo (ricevuto: −1 mesi).» |
| Lead time > 24 mesi | «Il lead time supera i 24 mesi: valore non plausibile per una filiera alimentare.» |
| Servizio ≥ 100% | «Il livello di servizio deve essere compreso fra 50% e 100% (escluso).» |
| Riesame ≤ 0 | «Il periodo di riesame deve essere maggiore di zero mesi.» |
| Orizzonte < 1 | «L'orizzonte di previsione deve essere di almeno 1 mese.» |
| Alpha fuori (0,1] | «Il parametro alpha deve essere compreso fra 0 (escluso) e 1.» |
| Test set troppo lungo | «Serie troppo corta per lo split richiesto: 48 osservazioni disponibili, ne servono almeno 54.» |

Gli errori provenienti dai livelli inferiori (valutazione, previsione) sono
**tradotti** in `ScenarioError` con un messaggio contestualizzato, così che
la dashboard non debba mai esporre un traceback Python all'utente finale.
