# 7. Metodologia, risultati, limiti e sviluppi

Questo capitolo ricompone il percorso metodologico complessivo, sintetizza i
risultati, dichiara con precisione i limiti del lavoro e indica le direzioni
di sviluppo.

---

## 7.1 Impostazione metodologica

### La domanda di ricerca

Il progetto risponde a una domanda operativa precisa:

> Data una serie storica di domanda, **quanto magazzino serve** per garantire
> un livello di servizio obiettivo, e **come cambia** questa risposta al
> variare delle caratteristiche della domanda e della filiera?

La risposta richiede tre passaggi logici concatenati, ciascuno dei quali
condiziona il successivo:

```
    Dati         →     Previsione      →      Scorte
      │                     │                    │
 quanto è             quanto bene            quanta scorta
 variabile?           so prevedere?          mi serve?
      │                     │                    │
      └─────────────────────┴────────────────────┘
              l'errore previsionale è il
              ponte fra previsione e scorte
```

Il passaggio chiave è il secondo: la scorta di sicurezza non si dimensiona
sulla variabilità della domanda, ma sulla variabilità dell'**errore di
previsione**. È ciò che collega strutturalmente le due metà del progetto e
che rende la qualità del modello previsionale una variabile **economica** e
non solo statistica.

### Le fasi del lavoro

| Fase | Attività | Esito |
|---|---|---|
| 1 | Analisi dei requisiti e progettazione architetturale | Struttura a moduli con logica separata dalla UI |
| 2 | Costruzione del generatore sintetico | 4 serie × 48 mesi, profili differenziati |
| 3 | Validazione dei dati | 11 controlli con messaggi in italiano |
| 4 | Implementazione dei metodi previsionali | 5 metodi scritti da zero |
| 5 | Valutazione out-of-sample | Split cronologico 36/12, 5 metriche |
| 6 | Selezione automatica del modello | Criterio MAPE con fallback documentato |
| 7 | Modelli di scorta | 4 componenti con ipotesi dichiarate |
| 8 | Motore di simulazione | Leve che rigenerano la serie |
| 9 | Dashboard | 8 sezioni, UI interamente in italiano |
| 10 | Test automatici | 264 test, tutti superati |
| 11 | Documentazione e relazione | Risultati generati da esecuzione reale |

### Il principio guida: dichiarare, non nascondere

Ogni volta che il progetto ha dovuto adottare una semplificazione, la scelta
è stata **esplicitata** anziché mascherata dietro un'apparenza di rigore.
Esempi:

- la banda di incertezza è chiamata «banda empirica» e non «intervallo di
  confidenza», perché non è derivata analiticamente;
- non è stato adottato il modello EOQ perché avrebbe richiesto costi
  inventati;
- i parametri di Holt-Winters non sono ottimizzati, e lo si dice;
- il lead time è deterministico, e si indica quale sarebbe l'estensione.

Questa impostazione è coerente con il vincolo di integrità accademica del
progetto: è preferibile un modello semplice e onesto a uno complesso e
indifendibile.

---

## 7.2 Sintesi dei risultati

### Risultato 1 — Le quattro serie hanno profili effettivamente diversi

| Prodotto | Media | CV (%) | Escursione stagionale | Profilo |
|---|---:|---:|---:|---|
| Nutella | 12.242 | 6,7 | 15 | stabile |
| Kinder Cioccolato | 9.019 | 14,1 | 29 | trend moderato |
| Ferrero Rocher | 6.260 | 39,9 | **118** | fortemente stagionale |
| Kinder Happy Hippo | 3.814 | 26,8 | 57 | rumoroso e promozionale |

### Risultato 2 — Ogni prodotto richiede un metodo previsionale diverso

| Prodotto | Metodo migliore | MAPE (%) | Peggiore | MAPE (%) | Divario |
|---|---|---:|---|---:|---:|
| Nutella | Holt-Winters additivo | 4,95 | Naive stagionale | 7,47 | 2,5 pt |
| Kinder Cioccolato | Smorzamento esponenziale | 9,78 | Holt-Winters | 12,49 | 2,7 pt |
| Ferrero Rocher | Naive stagionale | 9,91 | Media mobile | 80,93 | **71,0 pt** |
| Kinder Happy Hippo | Regressione lineare | 24,60 | Media mobile | 33,32 | 8,7 pt |

È il risultato centrale del lavoro: **quattro prodotti, quattro metodi
diversi**. Conferma empiricamente la premessa della specifica PW24.

Il divario di 71 punti su Ferrero Rocher quantifica il costo di applicare un
metodo inadeguato: una media mobile su un prodotto fortemente stagionale
produce previsioni praticamente inutilizzabili.

### Risultato 3 — Variabilità sistematica e variabilità casuale non sono la stessa cosa

| Prodotto | CV storico (%) | MAPE (%) | Natura della variabilità |
|---|---:|---:|---|
| Ferrero Rocher | **39,9** | 9,91 | prevalentemente **sistematica** (stagionale) |
| Kinder Happy Hippo | 26,8 | **24,60** | prevalentemente **casuale** (rumore, promozioni) |

Ferrero Rocher è la serie più variabile ma non la meno prevedibile: la sua
variabilità è in larga parte stagionale, cioè anticipabile. Happy Hippo ha
variabilità inferiore ma MAPE più che doppio.

La conseguenza gestionale è diretta e non banale:

- la variabilità **sistematica** si gestisce con la **scorta anticipata**
  (pianificazione della produzione);
- la variabilità **casuale** si gestisce con la **scorta di sicurezza**
  (cuscinetto contro l'ignoto).

Confondere le due porta a sovradimensionare la sicurezza su prodotti
stagionali. Il modello implementato evita l'errore stimando `σ` sull'errore
previsionale: su Ferrero Rocher, usare la variabilità grezza avrebbe
sovrastimato la scorta di sicurezza di **3,5 volte**.

### Risultato 4 — La composizione delle scorte è specifica del prodotto

| Prodotto | Ciclica | Sicurezza | Anticipata | Pipeline | Copertura |
|---|---:|---:|---:|---:|---:|
| Nutella | 17,1% | 5,7% | 8,9% | **68,4%** | 2,9 mesi |
| Kinder Cioccolato | 18,2% | 9,0% | 0,0% | **72,8%** | 2,7 mesi |
| Ferrero Rocher | 11,0% | 5,8% | **39,0%** | 44,1% | **4,5 mesi** |
| Kinder Happy Hippo | 15,7% | **19,2%** | 2,3% | 62,8% | 3,2 mesi |

Ferrero Rocher ha la copertura più alta pur avendo volumi intermedi: la
stagionalità impone strutturalmente più magazzino.
Happy Hippo ha la quota di sicurezza più alta: è l'imprevedibilità a costare.

### Risultato 5 — Il lead time è la leva dominante

Nello scenario baseline la **scorta pipeline** rappresenta fra il 44% e il
73% della scorta totale. Il confronto A/B su Ferrero Rocher mostra che
passando da una filiera stabile a una sotto stress:

- la scorta di sicurezza cresce del **+834%** (il moltiplicatore maggiore);
- la scorta pipeline cresce del **+132%**, ma spiega il **75%**
  dell'incremento assoluto perché parte da una base molto più grande.

La conclusione gestionale è che **ridurre il lead time ha più impatto sul
capitale circolante che ridurre il livello di servizio**, anche se è
quest'ultimo a produrre le variazioni percentuali più vistose.

### Risultato 6 — Il costo marginale del servizio è crescente

| Da → A | Incremento di z | Incremento scorta sicurezza |
|---|---:|---:|
| 90% → 95% | +0,363 | +28,3% |
| 95% → 97,5% | +0,315 | +19,2% |
| 97,5% → 99% | +0,366 | +18,7% |
| 99% → 99,9% | +0,764 | +32,8% |

Ogni punto di servizio aggiuntivo oltre il 97,5% ha un costo marginale
crescente, e il 100% richiederebbe una scorta infinita. La scelta del livello
di servizio è quindi una decisione economica, non tecnica: va confrontato il
costo di mantenimento con il costo atteso delle rotture evitate.

---

## 7.3 Limiti del modello

I limiti sono raggruppati per area. Nessuno di essi invalida il lavoro: sono
semplificazioni consapevoli, dichiarate per consentire una valutazione
corretta della portata dei risultati.

### Limiti relativi ai dati

| # | Limite | Implicazione |
|---|---|---|
| L1 | I dati sono **sintetici** | I risultati numerici hanno valore metodologico, non predittivo sul mercato reale |
| L2 | Il generatore impone una **struttura nota** (trend lineare, stagionalità sinusoidale) | I metodi sono avvantaggiati rispetto a dati reali, dove la struttura è ignota e instabile |
| L3 | Le serie sono **brevi** (48 mesi, 4 cicli) | Il test set copre un solo ciclo stagionale; la stima degli indici stagionali è basata su pochi cicli |
| L4 | Non sono modellati **eventi eccezionali** | Nessuna rottura di fornitura, nessun lancio o ritiro di prodotto, nessuno shock esogeno |
| L5 | Nessuna **correlazione fra prodotti** | Nella realtà esistono cannibalizzazione e sostituzione fra referenze |

### Limiti relativi alla previsione

| # | Limite | Implicazione |
|---|---|---|
| L6 | Parametri di Holt-Winters **non ottimizzati** | Il metodo potrebbe fare meglio con α, β, γ calibrati |
| L7 | **Una sola partizione** train/test | Una *rolling origin evaluation* darebbe stime più robuste |
| L8 | Nessun modello della **componente promozionale** | Le promozioni sono trattate come rumore, non come eventi noti in anticipo |
| L9 | La **banda di incertezza è costante** sull'orizzonte | Un intervallo rigoroso si allargherebbe al crescere di h |
| L10 | Il MAPE è **asimmetrico** | Penalizza le sovrastime più delle sottostime |

### Limiti relativi ai modelli di scorta

| # | Limite | Implicazione |
|---|---|---|
| L11 | **Lead time deterministico** | Con lead time variabile servirebbe un termine aggiuntivo `D²·σ_L²`; la scorta di sicurezza è **sottostimata** |
| L12 | Errori previsionali assunti **indipendenti** | Con autocorrelazione positiva la formula `σ·√L` **sottostima** il fabbisogno |
| L13 | Scorta ciclica a **copertura fissa**, non EOQ | Non si ottimizzano i costi di ordinazione e mantenimento |
| L14 | **Nessun costo monetario** nel modello | Si dimensionano quantità, non si ottimizzano costi; manca il *trade-off* economico esplicito |
| L15 | Nessun vincolo di **capacità produttiva o di stoccaggio** | La scorta anticipata calcolata potrebbe eccedere la capacità fisica disponibile |
| L16 | Non è modellata la **shelf life** | Per un prodotto alimentare, coperture elevate comportano rischio di obsolescenza non quantificato |
| L17 | Domanda assunta **normale** nell'intervallo di protezione | Con domanda molto asimmetrica l'approssimazione peggiora |

### Limite L18 — La scorta anticipata dipende dal metodo previsionale

Merita una voce dedicata perché è l'interazione più sottile fra i due blocchi
del progetto.

La scorta anticipata è calcolata sulla **previsione**, non sulla serie
storica. Se il metodo selezionato produce una previsione **piatta** (media
mobile, smorzamento esponenziale), la scorta anticipata risulta **nulla**
anche su un prodotto stagionale.

L'effetto è visibile nei risultati: Kinder Cioccolato, il cui metodo migliore
è lo smorzamento esponenziale, ha scorta anticipata pari a **zero** pur
avendo un'escursione stagionale di 29 punti indice.

Il comportamento è **internamente coerente** (se la previsione ufficiale non
prevede picchi, non c'è nulla da anticipare) ma segnala un rischio
gestionale reale: adottare un metodo non stagionale su un prodotto stagionale
non peggiora solo le previsioni, ma **azzera anche la pianificazione
dell'accumulo preventivo**. Il progetto rende visibile questo effetto a
cascata anziché nasconderlo.

Una versione più robusta calcolerebbe la scorta anticipata su un profilo
stagionale stimato **indipendentemente** dal metodo previsionale adottato.
È indicato fra gli sviluppi futuri.

---

## 7.4 Sviluppi futuri

Elencati in ordine di rapporto fra valore aggiunto e complessità di
realizzazione.

### Priorità alta

**S1 — Scorta anticipata indipendente dal metodo previsionale.**
Stimare gli indici stagionali con una decomposizione dedicata e usarli per la
scorta anticipata, superando il limite L18. Sforzo contenuto, beneficio
elevato.

**S2 — Validazione a origine mobile (*rolling origin*).**
Ripetere la valutazione su più finestre temporali scorrevoli anziché su una
sola partizione, mediando le metriche. Elimina la dipendenza del risultato
dalla particolare scelta del punto di taglio (limite L7).

**S3 — Ottimizzazione dei parametri di Holt-Winters.**
Minimizzare l'errore su una finestra di validazione interna al training con
`scipy.optimize`. Supera il limite L6 senza introdurre dipendenze nuove.

**S4 — Lead time stocastico.**
Estendere la scorta di sicurezza alla formula completa:

```
σ_IP = √( L·σ_D²  +  D²·σ_L² )
```

Richiede un solo parametro aggiuntivo (la variabilità del lead time) e supera
il limite L11, che è la sottostima più rilevante del modello attuale.

### Priorità media

**S5 — Dimensione economica.**
Introdurre costo unitario, tasso di mantenimento e costo di rottura, per
passare dal dimensionamento delle quantità all'**ottimizzazione dei costi**.
Consentirebbe di calcolare il livello di servizio ottimale anziché
imporlo, e abiliterebbe il modello EOQ (limite L13).

**S6 — Modellazione esplicita delle promozioni.**
Trattare le promozioni come variabile esplicativa nota in anticipo anziché
come rumore, tramite una regressione con variabili dummy. Migliorerebbe
sensibilmente la previsione di Kinder Happy Hippo, oggi il prodotto meno
prevedibile (MAPE 24,6%).

**S7 — Vincoli di capacità.**
Verificare che la scorta anticipata richiesta sia compatibile con la capacità
di stoccaggio disponibile, segnalando le violazioni (limite L15).

**S8 — Analisi di sensitività sistematica.**
Esplorare l'intero spazio dei parametri generando superfici di risposta
(scorta totale in funzione di lead time × livello di servizio), anziché
confrontare due scenari alla volta.

### Priorità bassa

**S9 — Modelli previsionali avanzati.** ARIMA/SARIMA, metodi di *ensemble*,
modelli di apprendimento automatico. Attenzione: su serie di 48 osservazioni
il rischio di sovra-adattamento è elevato, e il beneficio atteso modesto.

**S10 — Simulazione Monte Carlo.** Stimare la distribuzione del livello di
servizio effettivamente conseguito anziché limitarsi al valore nominale,
verificando la validità dell'approssimazione normale (limite L17).

**S11 — Esportazione dei risultati.** Generazione automatica di un report PDF
dalla dashboard.

**S12 — Caricamento di dati esterni.** Interfaccia per caricare un CSV
proprio: il livello di validazione è già pronto a gestirlo.

---

## 7.5 Valutazione complessiva del lavoro

### Cosa il progetto dimostra

1. **Competenza di programmazione applicata** al dominio: cinque metodi
   previsionali e quattro modelli di scorta implementati da zero, con
   architettura modulare e 264 test automatici.
2. **Comprensione metodologica**: la distinzione fra valutazione in-sample e
   out-of-sample, fra variabilità sistematica e casuale, fra variabilità
   della domanda e variabilità dell'errore previsionale.
3. **Capacità di interpretazione gestionale**: i risultati sono tradotti in
   conclusioni operative quantificate, non in tabelle di numeri.
4. **Integrità intellettuale**: la natura sintetica dei dati è dichiarata
   ovunque, le semplificazioni sono esplicitate, i limiti sono elencati
   analiticamente.

### Cosa il progetto non è

- Non è uno strumento utilizzabile operativamente da Ferrero.
- Non produce previsioni sul mercato dolciario reale.
- Non riproduce le procedure di pianificazione effettive dell'azienda.

Il valore del lavoro è **metodologico**: mostra come si imposta, si
implementa, si valida e si interpreta un sistema di previsione della domanda
e pianificazione delle scorte. I numeri sono sintetici; il metodo è reale.
