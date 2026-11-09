# Sviluppo di una mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte di un'impresa

## Project Work 24

**Corso di Studi in Informatica per le Aziende Digitali (L-31)**

Settori scientifico-disciplinari:
INF/01 — Informatica
ING-INF/05 — Sistemi di elaborazione delle informazioni
ING-IND/35 — Ingegneria economico-gestionale

Tema: *La digitalizzazione dell'impresa*

Impresa analizzata: **Ferrero**

---

> ## Dichiarazione sulla natura dei dati
>
> L'impresa **Ferrero** e i prodotti analizzati — **Nutella**, **Kinder
> Cioccolato**, **Ferrero Rocher**, **Kinder Happy Hippo** — sono reali, e le
> informazioni istituzionali riportate in questa relazione provengono
> esclusivamente da **fonti pubbliche**.
>
> I **dati numerici di domanda** utilizzati nel progetto sono invece
> **interamente sintetici**: sono stati generati algoritmicamente da un
> modulo sviluppato appositamente (`src/data_generator.py`), a partire da
> parametri scelti dallo studente, con l'obiettivo di riprodurre
> comportamenti di domanda **plausibili ma fittizi**.
>
> In particolare:
>
> - **nessun valore** rappresenta vendite, volumi di produzione, giacenze o
>   quote di mercato reali di Ferrero;
> - **nessun dato** è stato fornito dall'azienda né derivato da
>   documentazione aziendale riservata;
> - **nessuna informazione interna o confidenziale** è utilizzata o
>   rappresentata;
> - i risultati numerici hanno valore **metodologico**, non predittivo sul
>   mercato reale.
>
> Il progetto non intrattiene alcun rapporto di collaborazione,
> sponsorizzazione o approvazione con Ferrero. I marchi citati appartengono
> ai rispettivi titolari e sono richiamati a soli fini descrittivi.

---

## Indice

1. [Introduzione](#1-introduzione)
2. [Obiettivi del Project Work](#2-obiettivi-del-project-work)
3. [L'impresa selezionata: Ferrero](#3-limpresa-selezionata-ferrero)
4. [Prodotti analizzati](#4-prodotti-analizzati)
5. [Contesto produttivo, commerciale e logistico](#5-contesto-produttivo-commerciale-e-logistico)
6. [Il problema della previsione della domanda](#6-il-problema-della-previsione-della-domanda)
7. [Costruzione del dataset](#7-costruzione-del-dataset)
8. [Analisi delle serie storiche](#8-analisi-delle-serie-storiche)
9. [Metodi previsionali](#9-metodi-previsionali)
10. [Valutazione dell'accuratezza](#10-valutazione-dellaccuratezza)
11. [Pianificazione delle scorte](#11-pianificazione-delle-scorte)
12. [Il modello delle scorte](#12-il-modello-delle-scorte)
13. [Progettazione della dashboard](#13-progettazione-della-dashboard)
14. [Implementazione Python](#14-implementazione-python)
15. [Simulazione degli scenari](#15-simulazione-degli-scenari)
16. [Risultati](#16-risultati)
17. [Interpretazione gestionale](#17-interpretazione-gestionale)
18. [Limiti](#18-limiti)
19. [Sviluppi futuri](#19-sviluppi-futuri)
20. [Conclusioni](#20-conclusioni)
21. [Repository e modalità di esecuzione](#21-repository-e-modalità-di-esecuzione)
22. [Riferimenti](#22-riferimenti)

---

## 1. Introduzione

La gestione delle scorte è uno dei problemi decisionali più antichi e al
tempo stesso più attuali dell'economia d'impresa. Ogni organizzazione che
detenga magazzini di prodotti finiti, componenti o materie prime si trova di
fronte a un dilemma apparentemente semplice: **quanto tenere**.

Il dilemma non ha una risposta ovvia perché le due direzioni dell'errore
hanno costi di natura diversa. Una scorta eccessiva genera **costi di
mantenimento** (capitale immobilizzato, spazio, movimentazione,
assicurazione) e, per i beni deperibili, **rischio di obsolescenza**. Una
scorta insufficiente genera **incapacità di soddisfare la domanda**, con
perdita di margine, danno reputazionale e — nel rapporto con la grande
distribuzione organizzata — il rischio concreto di perdere spazio a
scaffale a favore dei concorrenti.

La difficoltà sostanziale è che la decisione va presa **prima** di conoscere
la domanda. Si decide oggi quanto produrre e ordinare per servire un mercato
che si manifesterà fra settimane o mesi. La qualità della decisione dipende
quindi dalla qualità della **previsione**, e la previsione è inevitabilmente
imperfetta.

Le serie storiche di domanda possono presentare comportamenti molto diversi:
andamenti **stazionari** attorno a un livello costante, **tendenze** di
crescita o declino, **variazioni stagionali** legate al calendario,
**componenti casuali** irriducibili. Metodi previsionali diversi ipotizzano
strutture diverse, e nessuno è universalmente superiore: la scelta deve essere
guidata dai dati.

Questo Project Work affronta il problema costruendo uno **strumento
software** che integra le due metà della questione — previsione e
pianificazione — in un'unica applicazione interattiva. L'impresa di
riferimento è **Ferrero**, scelta per la rilevanza del problema di
pianificazione nel suo settore e per l'eterogeneità del suo portafoglio
prodotti. I dati di domanda sono **sintetici**, generati appositamente: una
scelta che, come si argomenterà, è non solo lecita ma metodologicamente
preferibile all'alternativa di presentare come reali dati che non lo sono.

---

## 2. Obiettivi del Project Work

La specifica fissa cinque obiettivi. Si indica per ciascuno come il progetto
vi risponde.

**Obiettivo 1 — Sviluppare competenze di programmazione applicate alla
previsione della domanda e alla gestione delle scorte.**
Sono stati implementati da zero, con NumPy, cinque metodi previsionali e
quattro modelli di scorta, organizzati in undici moduli Python con
architettura modulare, *type hints*, *docstring* e 264 test automatici.

**Obiettivo 2 — Applicare e confrontare metodi previsionali diversi,
valutandone l'accuratezza.**
I cinque metodi sono confrontati su ciascun prodotto mediante una valutazione
*out-of-sample* con split cronologico, misurata con MAE, RMSE, MAPE, Bias e
sMAPE. La selezione del metodo migliore è automatica, secondo un criterio
dichiarato.

**Obiettivo 3 — Analizzare gli effetti delle caratteristiche della domanda e
del lead time sulle diverse tipologie di scorta.**
La dashboard espone sei leve (variabilità, trend, stagionalità, lead time,
livello di servizio, periodo di riesame) che modificano realmente i calcoli,
e mostra la scomposizione della scorta nelle sue quattro componenti
funzionali.

**Obiettivo 4 — Realizzare una mini-dashboard per la configurazione di
scenari e la rappresentazione grafica.**
È stata sviluppata un'applicazione Streamlit in otto sezioni, con interfaccia
interamente in italiano, sette tipologie di grafico Plotly interattivo e una
sezione dedicata al confronto fra due scenari configurabili.

**Obiettivo 5 — Interpretare le conseguenze gestionali delle alternative.**
La sezione 6 della dashboard genera automaticamente un'analisi gestionale in
italiano **costruita sui valori effettivamente calcolati**, che cambia
struttura e contenuto al variare della configurazione.

---

## 3. L'impresa selezionata: Ferrero

### 3.1 Motivazione della scelta

La scelta di Ferrero risponde a tre criteri.

**Rilevanza del problema.** Il settore dolciario presenta una combinazione di
caratteristiche che rendono la pianificazione critica: domanda fortemente
influenzata dal calendario (festività) e dalla temperatura, *shelf life*
limitata, livelli di servizio contrattualizzati con la distribuzione
organizzata, capacità produttiva rigida nel breve periodo. Sono esattamente
le condizioni in cui un errore previsionale si traduce immediatamente in
costi.

**Eterogeneità del portafoglio.** L'azienda commercializza prodotti con
comportamenti di domanda strutturalmente diversi: dalla crema spalmabile a
consumo quotidiano alla pralineria da regalo concentrata nel periodo
natalizio. Questa varietà consente di costruire le quattro serie con profili
differenziati richieste dalla specifica.

**Disponibilità di informazione pubblica.** Esiste documentazione
istituzionale ampia e verificabile sul perimetro industriale e sul
posizionamento del Gruppo, sufficiente a inquadrare il contesto senza
ricorrere a informazioni riservate.

### 3.2 Profilo dell'impresa

Ferrero è un gruppo industriale italiano fondato ad **Alba (Cuneo)** nel
**1946** da Pietro Ferrero. È oggi uno dei principali gruppi mondiali nel
settore dolciario, con struttura proprietaria di tipo **familiare** e
presenza produttiva e commerciale su scala internazionale.

| Dimensione | Informazione pubblica |
|---|---|
| Settore | Industria alimentare dolciaria |
| Fondazione | 1946, Alba (CN), Italia |
| Natura | Gruppo privato a controllo familiare |
| Presenza | Stabilimenti e filiali commerciali in numerosi Paesi |
| Marchi principali | Nutella, Kinder, Ferrero Rocher, Tic Tac, Mon Chéri |
| Canali | GDO, distribuzione tradizionale, *travel retail* |

Le fonti di queste informazioni sono elencate al capitolo 22.

---

## 4. Prodotti analizzati

I quattro prodotti selezionati sono **prodotti reali** del Gruppo. Le
descrizioni che seguono riportano informazioni pubblicamente note; i
**comportamenti di domanda** indicati sono invece **ipotesi di
modellazione** adottate per generare le serie sintetiche.

### 4.1 Nutella

Crema spalmabile alla nocciola e cacao, lanciata nel 1964, è il prodotto più
noto del Gruppo. Il profilo di consumo ipotizzato è **quotidiano e
abitudinario**, con acquisto ricorrente e scarsa dipendenza da ricorrenze
specifiche.

**Comportamento modellato**: domanda **stabile**, variabilità casuale
**bassa**, trend **molto limitato**, stagionalità **debole**.

### 4.2 Kinder Cioccolato

Snack di cioccolato al latte con ripieno al latte, prodotto storico della
linea Kinder, rivolto principalmente al consumo familiare e infantile. Il
profilo ipotizzato prevede consumo regolare con **flessione estiva** tipica
dei prodotti a base di cioccolato.

**Comportamento modellato**: domanda **moderatamente stabile**, trend
positivo **moderato**, variabilità **moderata**, stagionalità
**debole/moderata** con minimo estivo.

### 4.3 Ferrero Rocher

Pralina di cioccolato con nocciola intera, wafer e granella, venduta
prevalentemente in confezioni regalo. È un prodotto di pralineria premium
fortemente associato all'uso come **dono** e alle ricorrenze. Il profilo
ipotizzato prevede domanda concentrata nel periodo autunnale/natalizio, con
ordini della distribuzione **anticipati** rispetto al consumo finale.

**Comportamento modellato**: stagionalità **forte** con picchi rilevanti fra
ottobre e dicembre, variabilità **moderata**, trend di lungo periodo
**moderato**.

### 4.4 Kinder Happy Hippo

Snack a base di wafer con ripieno, in forma di ippopotamo, della linea Kinder
rivolta al target infantile. Il profilo ipotizzato è quello di un prodotto di
**impulso**, più esposto all'attività promozionale, con volumi assoluti
inferiori agli altri tre.

**Comportamento modellato**: domanda **più variabile**, trend positivo
**moderato**, **picchi promozionali** casuali, stagionalità **moderata**,
rumore **superiore** a Nutella e Kinder Cioccolato.

### 4.5 Sintesi

| Prodotto | Volume relativo | Variabilità | Trend | Stagionalità | Promozioni |
|---|---|---|---|---|---|
| Nutella | Alto | Bassa | Molto limitato | Debole | Assenti |
| Kinder Cioccolato | Medio-alto | Moderata | Moderato | Debole/moderata | Rare |
| Ferrero Rocher | Medio | Moderata | Moderato | **Forte (Natale)** | Assenti |
| Kinder Happy Hippo | Basso | **Alta** | Moderato | Moderata | **Frequenti** |

---

## 5. Contesto produttivo, commerciale e logistico

### 5.1 Contesto produttivo

Le considerazioni che seguono sono di natura **settoriale generale** e non
descrivono procedure specifiche di Ferrero.

**Materie prime critiche.** La produzione dipende da materie prime agricole
soggette a stagionalità di raccolto e volatilità di prezzo: nocciole, cacao,
zucchero, latte in polvere, oli vegetali. L'approvvigionamento avviene
tipicamente con contratti pluriennali e scorte di materia prima
significative. Ne consegue che il **lead time di approvvigionamento non è
trascurabile** e può variare sensibilmente: è questa la ragione per cui la
dashboard consente di esplorare lead time da 0,5 a 8 mesi.

**Shelf life limitata.** Il prodotto finito ha vita commerciale definita:
accumulare scorta eccessiva genera **rischio di obsolescenza**, non solo
costo finanziario.

**Sensibilità alla temperatura.** Il cioccolato è sensibile al calore: nei
mesi estivi la distribuzione richiede condizioni controllate e alcuni
prodotti registrano fisiologicamente consumi inferiori. È il fondamento del
profilo stagionale con minimo estivo adottato per i prodotti a base di
cioccolato.

**Capacità produttiva rigida nel breve periodo.** Le linee non si
riconfigurano istantaneamente. Per servire un picco stagionale occorre o
produrre in anticipo — generando **scorta anticipata** — oppure disporre di
flessibilità di capacità, con costi di straordinario e personale stagionale.
È il classico problema di *production smoothing*, che il progetto modella
nella componente di scorta anticipata.

### 5.2 Contesto commerciale

**Canale prevalente: la GDO.** Il canale della grande distribuzione comporta
**livelli di servizio contrattualizzati**: gli accordi prevedono obiettivi di
disponibilità elevati, e il mancato rispetto può comportare penali e la
perdita di spazio a scaffale. È il motivo per cui la dashboard propone livelli
di servizio dal 90% al 99%, con il 95% come valore predefinito.

**Effetto delle promozioni.** Le attività promozionali concordate con la
distribuzione generano picchi di domanda rilevanti e di collocazione temporale
non perfettamente regolare. Il generatore riproduce il fenomeno con una
componente episodica, particolarmente marcata per Kinder Happy Hippo.

**Effetto frusta.** Gli ordini della distribuzione sono più variabili dei
consumi finali, perché incorporano le politiche di riordino dei clienti. Il
progetto non modella esplicitamente il fenomeno, ma la variabilità
complessiva delle serie ne tiene implicitamente conto.

**Stagionalità commerciale.**

| Periodo | Effetto sulla domanda |
|---|---|
| Ottobre – dicembre | Picco principale: confezioni regalo, consumo natalizio |
| Febbraio | San Valentino (pralineria) |
| Marzo – aprile | Pasqua |
| Giugno – agosto | Flessione per i prodotti a base di cioccolato |

Il picco natalizio è il più rilevante: la **produzione e la spedizione
anticipano il consumo**, concentrandosi fra ottobre e novembre perché il
prodotto deve essere a scaffale prima delle festività. Nel dataset sintetico
il fenomeno è riprodotto per Ferrero Rocher con un profilo festivo che
assegna il massimo a **novembre**.

### 5.3 Contesto logistico

```
Fornitori materie prime
        │
        ▼
Stabilimenti produttivi  ──►  Magazzini centrali
                                    │
                                    ▼
                           Piattaforme regionali
                                    │
                                    ▼
                           Centri distributivi GDO
                                    │
                                    ▼
                              Punti vendita
```

Ai fini del progetto rilevano tre grandezze:

1. **Lead time di approvvigionamento (`L`)** — tempo fra emissione
   dell'ordine e disponibilità della merce. Comprende produzione, controllo
   qualità, trasporto e messa a disposizione. Espresso in **mesi**, determina
   la **scorta pipeline**.
2. **Periodo di riesame (`R`)** — intervallo fra due decisioni di
   rifornimento. Determina l'ampiezza del lotto e quindi la **scorta
   ciclica**.
3. **Variabilità del lead time** — nella realtà il tempo di
   approvvigionamento è aleatorio. Il modello assume per semplicità un
   **lead time deterministico**: l'ipotesi è dichiarata ed è discussa al
   capitolo 18.

---

## 6. Il problema della previsione della domanda

### 6.1 Formulazione

Data una serie storica di domanda mensile `y(1), …, y(T)`, si vuole stimare
la domanda futura `y(T+1), …, y(T+h)` per un orizzonte `h` di 3, 6 o 12 mesi.

La difficoltà non sta nel produrre *una* previsione, ma nel determinare
**quanto ci si può fidare** di quella previsione e **quale metodo scegliere**
fra i molti disponibili. È per questa ragione che il progetto dedica più
attenzione alla valutazione che alla previsione in sé.

### 6.2 Le componenti di una serie storica

| Componente | Natura | Prevedibile? |
|---|---|---|
| **Livello** | valore medio attorno a cui oscilla la serie | sì |
| **Trend** | direzione sistematica di lungo periodo | sì |
| **Stagionalità** | variazione periodica legata al calendario | sì |
| **Componente casuale** | fluttuazione irregolare residua | **no** |

La distinzione fra le prime tre e la quarta è concettualmente decisiva. Le
prime tre sono **sistematiche**: un modello adeguato le cattura e le
anticipa. La quarta è **irriducibile**: nessun modello può prevederla, e
l'unica difesa è il cuscinetto della scorta di sicurezza.

Da questa distinzione segue la struttura logica dell'intero progetto:

```
    Dati          →      Previsione       →       Scorte
      │                       │                      │
 quanto è                quanto bene            quanta scorta
 variabile?              so prevedere?          mi serve?
      │                       │                      │
      └───────────────────────┴──────────────────────┘
               l'errore previsionale è il ponte
               fra previsione e pianificazione
```

Il passaggio chiave è il secondo: la scorta di sicurezza non si dimensiona
sulla variabilità della domanda, ma sulla variabilità dell'**errore di
previsione**. È ciò che rende la qualità del modello previsionale una
variabile **economica**, non solo statistica.

---

## 7. Costruzione del dataset

### 7.1 Perché dati sintetici

La specifica ammette dati «reali, stimati o generati». La scelta di dati
**generati** è motivata da tre ragioni.

**Impossibilità di accesso a dati reali.** I volumi di vendita per referenza
di un'impresa privata non sono pubblici. Qualunque "dato reale" presentato
come tale sarebbe in realtà inventato, con un problema di onestà
intellettuale che il progetto ha scelto di evitare.

**Controllo sui comportamenti di domanda.** La specifica richiede quattro
serie con comportamenti **diversi fra loro**. Generando i dati è possibile
garantire per costruzione — e **verificare con test automatici** — che le
differenze richieste siano effettivamente presenti.

**Riproducibilità.** Con un seed fissato, chiunque cloni il repository
ottiene esattamente lo stesso dataset e quindi gli stessi risultati riportati
in questa relazione.

Il costo della scelta è dichiarato fra i limiti: i risultati hanno valore
**metodologico**, non predittivo sul mercato reale.

### 7.2 Il modello generatore

Per il mese `t = 0, …, 47` e il mese solare `m ∈ {1,…,12}`:

**Livello con trend**

```
L(t) = base_demand × (1 + trend_rate × t)
```

**Fattore stagionale**

```
S(m) = 1 + A × cos( 2π(m − peak_month)/12 ) + F(m)
```

La scelta del coseno è deliberata: `cos` vale 1 quando l'argomento è nullo,
quindi il massimo cade *esattamente* nel mese indicato da `peak_month`.
`F(m)` è il **profilo festivo**, necessario perché una sinusoide pura, in
quanto simmetrica, non riesce a riprodurre il picco **stretto e asimmetrico**
della pralineria da regalo. Per Ferrero Rocher:

| Mese | Sovra-domanda |
|---|---|
| Ottobre | +45% |
| Novembre | +105% |
| Dicembre | +75% |

**Rumore casuale**

```
ε(t) ~ N(0, noise_std)        →        fattore (1 + ε(t))
```

Il rumore è **moltiplicativo** e `noise_std` è espresso come coefficiente di
variazione: la dispersione assoluta cresce con il livello della serie (come
si osserva nella realtà) e il parametro è confrontabile fra prodotti di
volume diverso.

**Picchi promozionali**

```
con probabilità p:   P(t) = L(t) × promotion_amplitude × U(0,6; 1,4)
```

La componente è **episodica** e di **entità variabile**, così che le
promozioni non abbiano tutte la stessa intensità.

**Formula complessiva**

```
D(t) = round( max( 1 ;  L(t) × S(m) × (1 + ε(t)) + P(t) ) )
```

Il troncamento e l'arrotondamento garantiscono i vincoli richiesti dalla
specifica: **quantità intere e strettamente positive**.

### 7.3 Parametri adottati

| Parametro | Nutella | Kinder Cioccolato | Ferrero Rocher | Kinder Happy Hippo |
|---|---:|---:|---:|---:|
| `base_demand` | 12.000 | 8.000 | 5.000 | 3.000 |
| `trend_rate` (mese) | 0,0010 | 0,0050 | 0,0030 | 0,0060 |
| `seasonal_amplitude` | 0,05 | 0,12 | 0,18 | 0,12 |
| `seasonal_peak_month` | 11 | 12 | 12 | 12 |
| `festive_profile` | — | — | 10:+0,45 / 11:+1,05 / 12:+0,75 | — |
| `noise_std` | 0,05 | 0,08 | 0,10 | **0,18** |
| `promotion_probability` | 0,00 | 0,06 | 0,00 | **0,20** |
| `promotion_amplitude` | 0,00 | 0,12 | 0,00 | **0,45** |

Unità di misura: **cartoni/mese**. La scelta del cartone riflette il fatto
che la pianificazione logistica verso la distribuzione avviene su unità di
carico, non su unità di vendita.

### 7.4 Riproducibilità

Il seed globale è **24**. Ogni prodotto usa un flusso casuale **derivato**
tramite `numpy.random.SeedSequence(seed).spawn(16)[indice]`. Questa scelta
garantisce una proprietà essenziale per la simulazione: **modificare i
parametri di un prodotto non altera le realizzazioni casuali degli altri**.
Senza di essa, muovere un cursore della dashboard avrebbe cambiato anche le
serie dei prodotti non selezionati, rendendo i confronti non interpretabili.

Vale inoltre la **proprietà di identità**: con tutti i moltiplicatori di
scenario pari a 1,0 la serie rigenerata coincide *esattamente* con il dataset
di base. Entrambe le proprietà sono verificate da test automatici.

### 7.5 File prodotti

| File | Righe | Contenuto |
|---|---:|---|
| `data/demand_history.csv` | 192 | formato lungo: `date`, `product`, `demand` |
| `data/demand_history_wide.csv` | 48 | formato pivot, una colonna per prodotto |
| `data/product_parameters.csv` | 4 | parametri del processo generatore |

Il terzo file rende il dataset **auto-documentato**: la logica di generazione
è ricostruibile senza leggere il codice.

### 7.6 Validazione dei dati

Il modulo `src/data_validation.py` sottopone ogni dataset caricato a **undici
controlli** prima dell'uso, con messaggi in italiano rivolti all'utente
finale.

Controlli **bloccanti**: colonne obbligatorie, formato delle date, valori
numerici, valori mancanti, date duplicate, domanda non negativa, prodotti in
anagrafica, numerosità minima (≥ 24 osservazioni), continuità mensile.

**Segnalazioni** non bloccanti: presenza di domanda nulla (con avviso
sull'effetto sul calcolo del MAPE), prodotti dell'anagrafica assenti.

La distinzione è deliberata: una domanda pari a zero è un dato legittimo —
può rappresentare una rottura di stock — ma ha conseguenze sul MAPE che
l'utente deve conoscere. Impedire l'analisi sarebbe sbagliato; tacere il
problema anche.

Sono inoltre gestite le condizioni di errore sul file: inesistente, vuoto,
malformato, non leggibile. In nessun caso l'applicazione espone un traceback
Python.

---

## 8. Analisi delle serie storiche

### 8.1 Statistiche descrittive

Dataset generato con seed 24, 48 osservazioni mensili per prodotto
(gennaio 2022 – dicembre 2025).

| Prodotto | Oss. | Media | Dev. std | Minimo | Massimo | **CV (%)** |
|---|---:|---:|---:|---:|---:|---:|
| Nutella | 48 | 12.242 | 823 | 10.643 | 14.427 | **6,7** |
| Kinder Cioccolato | 48 | 9.019 | 1.268 | 6.769 | 12.195 | **14,1** |
| Ferrero Rocher | 48 | 6.260 | 2.497 | 3.497 | 12.809 | **39,9** |
| Kinder Happy Hippo | 48 | 3.814 | 1.020 | 1.849 | 6.217 | **26,8** |

Il **coefficiente di variazione** è l'indicatore sintetico della difficoltà
previsionale di una serie. L'ordine ottenuto — Nutella 6,7% < Kinder
Cioccolato 14,1% < Happy Hippo 26,8% < Ferrero Rocher 39,9% — conferma la
differenziazione richiesta.

> **Figura 1** — `report/figures/01_panoramica_prodotti.html`
> Confronto dei quattro profili di domanda, con valori normalizzati
> (media di ciascun prodotto = 100).

### 8.2 Profilo stagionale

Indice mensile, media annua = 100.

| Mese | Nutella | Kinder Cioccolato | Ferrero Rocher | Kinder Happy Hippo |
|---|---:|---:|---:|---:|
| Gennaio | 106 | 100 | 88 | 90 |
| Febbraio | 101 | 107 | 90 | 93 |
| Marzo | 94 | 103 | 77 | 81 |
| Aprile | 95 | 97 | 77 | 95 |
| Maggio | 93 | 88 | 71 | 90 |
| Giugno | 97 | 88 | **69** | 73 |
| Luglio | 96 | 92 | 75 | 106 |
| Agosto | 99 | 99 | 77 | 88 |
| Settembre | 103 | 96 | 88 | 116 |
| Ottobre | 108 | 104 | 134 | 112 |
| Novembre | 102 | 108 | **187** | **130** |
| Dicembre | 108 | **117** | 167 | 127 |
| **Escursione** | **15** | **29** | **118** | **57** |

> **Figura 2** — `report/figures/02_profilo_stagionale_*.html`
> Profilo stagionale medio di ciascun prodotto.

**Lettura.** Nutella oscilla fra 93 e 108: stagionalità praticamente
irrilevante ai fini della pianificazione. Kinder Cioccolato mostra il tipico
**avvallamento estivo** (88 a maggio e giugno) e il massimo a dicembre.
Ferrero Rocher presenta un'escursione di 118 punti, con il picco di novembre
(187) quasi triplo rispetto al minimo di giugno (69): è il profilo che
giustifica l'esistenza della scorta anticipata. Kinder Happy Hippo ha
stagionalità moderata resa irregolare dai picchi promozionali — si noti
l'anomalia di luglio (106), dovuta a promozioni casuali e non a stagionalità.

### 8.3 Un'osservazione preliminare importante

Ferrero Rocher ha il coefficiente di variazione più alto (39,9%) pur avendo
un rumore casuale moderato (10%). La sua variabilità è in larga parte
**sistematica**, cioè stagionale, e quindi **prevedibile**.

Questa distinzione — fra variabilità sistematica e variabilità casuale —
emergerà come il risultato concettualmente più rilevante dell'intero lavoro,
ed è anticipata qui perché orienta la lettura di tutto ciò che segue.

---

## 9. Metodi previsionali

Sono implementati **cinque** metodi, tutti scritti da zero con NumPy. La
specifica ne richiede almeno due e raccomanda tre; i cinque implementati
coprono l'intero spettro dei comportamenti presenti nel dataset.

| Metodo | Livello | Trend | Stagionalità |
|---|:---:|:---:|:---:|
| Media mobile semplice | ✔ | ✘ | ✘ |
| Smorzamento esponenziale semplice | ✔ | ✘ | ✘ |
| Regressione lineare sul tempo | ✔ | ✔ | ✘ |
| Naive stagionale | ✔ | ✘ | ✔ |
| Holt-Winters additivo | ✔ | ✔ | ✔ |

La tabella anticipa il risultato: nessun metodo domina gli altri in assoluto,
perché ciascuno ipotizza una struttura diversa dei dati.

### 9.1 Media mobile semplice

```
F(T+h) = (1/w) · Σ y(i)        per i = T−w+1 … T,   per ogni h ≥ 1
```

Parametro configurabile: ampiezza della finestra `w` ∈ {3, 6, 12} mesi.

Il metodo assume che la serie sia **stazionaria** attorno a un livello
costante. La previsione è **piatta**. Finestre ampie producono previsioni
lisce ma lente; su una serie stagionale, una finestra di 12 mesi ha l'effetto
di **destagionalizzare** completamente la previsione.

### 9.2 Smorzamento esponenziale semplice

```
L(t) = α·y(t) + (1−α)·L(t−1),      L(0) = y(0),      0 < α ≤ 1
F(T+h) = L(T)
```

Parametro: `α`, regolabile da 0,05 a 1,00; predefinito **0,30**.

È una media ponderata di **tutte** le osservazioni passate, con pesi
decrescenti esponenzialmente. A differenza della media mobile — che usa solo
le ultime `w` osservazioni con peso uguale e scarta bruscamente le
precedenti — utilizza l'intera storia con decadimento graduale. Nella pratica
risulta più stabile: nei risultati batte la media mobile su **tutti e
quattro** i prodotti.

### 9.3 Regressione lineare sul tempo

```
y(t) = a + b·t + e(t)          stima per minimi quadrati ordinari
F(T+h) = a + b·(T + h − 1)
```

Le previsioni sono vincolate a essere **non negative**: un trend fortemente
decrescente, estrapolato su 12 mesi, potrebbe altrimenti produrre domanda
negativa, priva di significato.

È l'unico metodo che modella esplicitamente una **direzione di lungo
periodo**. Ignora però completamente la stagionalità e assume che il trend sia
lineare e persistente anche nel futuro.

### 9.4 Naive stagionale

```
F(T+h) = y( T + h − m·⌈h/m⌉ )          con m = 12
```

In pratica: «la domanda del prossimo novembre sarà quella dello scorso
novembre».

È un **benchmark**, non un modello sofisticato, e il suo ruolo metodologico è
fondamentale: se un modello complesso non batte il naive stagionale, la sua
complessità non è giustificata. È un principio standard della letteratura
previsionale.

Cattura l'intero profilo stagionale — compresi picchi asimmetrici che una
sinusoide non riproduce — senza stimare alcun parametro. In compenso non
filtra il rumore e non coglie il trend.

### 9.5 Holt-Winters additivo

```
Livello:       L(t) = α·( y(t) − S(t−m) ) + (1−α)·( L(t−1) + B(t−1) )
Trend:         B(t) = β·( L(t) − L(t−1) ) + (1−β)·B(t−1)
Stagionalità:  S(t) = γ·( y(t) − L(t) )   + (1−γ)·S(t−m)

F(T+h) = L(T) + h·B(T) + S( T + h − m·⌈h/m⌉ )
```

Inizializzazione **deterministica**: livello iniziale = media del primo ciclo;
trend iniziale = differenza fra le medie del secondo e del primo ciclo divisa
per `m`; indici stagionali iniziali = scarti del primo ciclo dalla propria
media. Servono quindi almeno due cicli completi (24 mesi).

Parametri: `α = 0,30`, `β = 0,10`, `γ = 0,20`, valori di uso comune in
letteratura e **non ottimizzati numericamente**. La semplificazione è
dichiarata: un'implementazione professionale li calibrerebbe minimizzando
l'errore. Si è scelto di non farlo per mantenere il codice leggibile, evitare
il sovra-adattamento in-sample e garantire un confronto equo fra metodi, tutti
con parametri fissati.

---

## 10. Valutazione dell'accuratezza

### 10.1 Il principio dello split cronologico

Valutare un modello sugli stessi dati usati per stimarlo produce una misura
**ottimisticamente distorta**: il modello ha già "visto" quei dati. È il
problema del sovra-adattamento.

La soluzione standard è dividere i dati in addestramento e test. Per le serie
storiche questa divisione deve rispettare una regola vincolante: **non si può
mescolare casualmente**. L'ordine temporale porta informazione, e usare dati
futuri per prevedere il passato sarebbe una fuga di informazione che
invaliderebbe l'intera valutazione.

```
┌──────────────── 48 mesi di storia ────────────────┐
├────── addestramento: 36 mesi ──────┬── test: 12 ──┤
│      gen 2022 → dic 2024           │ gen → dic 25 │
└────────────────────────────────────┴──────────────┘
```

- **Addestramento**: 36 mesi, tre cicli stagionali completi, sufficienti
  anche per Holt-Winters (che ne richiede due).
- **Test**: 12 mesi, un ciclo completo, così che la valutazione comprenda sia
  i mesi di picco sia quelli di morbida e nessun metodo risulti avvantaggiato
  dalla scelta della finestra.

**Verifica automatica dell'assenza di fughe di informazione.** Il test
`test_metodi_ignorano_il_periodo_di_test` moltiplica per 10 i valori del solo
periodo di test e verifica che le previsioni di tutti i metodi restino
identiche. Se un metodo usasse anche indirettamente il test set, il test
fallirebbe.

### 10.2 Le metriche

**MAE — Mean Absolute Error**

```
MAE = (1/n) · Σ | y(i) − f(i) |
```

Unità: cartoni. Indica di quanti cartoni il modello sbaglia in media. È
immediatamente interpretabile in termini operativi, ma **non confrontabile
fra prodotti di volume diverso**: un errore di 650 cartoni è modesto su
Nutella (12.242 di media) ed enorme su Happy Hippo (3.814).

**RMSE — Root Mean Squared Error**

```
RMSE = √[ (1/n) · Σ ( y(i) − f(i) )² ]
```

Unità: cartoni. Penalizza in modo **più che proporzionale gli errori
grandi**, perché gli scarti sono elevati al quadrato prima di essere mediati.
Vale sempre `RMSE ≥ MAE` (disuguaglianza di Jensen): il rapporto fra i due
indica la presenza di errori occasionali di grande entità.

Nel progetto l'RMSE out-of-sample ha un ruolo aggiuntivo: è usato come stima
della deviazione standard dell'errore previsionale `σ` nel dimensionamento
della scorta di sicurezza. La scelta è coerente, perché la scorta di sicurezza
deve proteggere soprattutto dagli errori grandi, che sono proprio quelli che
l'RMSE pesa di più.

**MAPE — Mean Absolute Percentage Error**

```
MAPE = (100/n′) · Σ | y(i) − f(i) | / | y(i) |        solo per y(i) ≠ 0
```

Unità: punti percentuali. È **adimensionale**, quindi confrontabile fra
prodotti con volumi molto diversi, e immediatamente comprensibile in sede di
discussione manageriale.

Presenta però tre cautele: non è definito per `y(i) = 0`; è **asimmetrico**
(penalizza più le sovrastime delle sottostime, perché il denominatore è il
valore osservato); diventa instabile quando i valori osservati sono molto
piccoli.

**Gestione dei valori nulli.** Le osservazioni con domanda nulla sono
**escluse** dal calcolo e `n′` è ridotto di conseguenza. L'alternativa —
trattare lo zero come un valore piccolo — produrrebbe percentuali enormi e
arbitrarie. Se tutte le osservazioni di test sono nulle il MAPE restituisce
`NaN` e il criterio di selezione ripiega sull'RMSE.

**Indicatori complementari.** Sono inoltre calcolati il **Bias**
(`(1/n)·Σ(f−y)`), diagnostica di sovra/sotto-stima sistematica, e lo
**sMAPE** (MAPE simmetrico), definito anche in presenza di osservazioni nulle.

### 10.3 Il criterio di selezione del modello

**Criterio primario: MAPE out-of-sample minimo.**

```
metodo* = argmin  MAPE_out-of-sample(metodo)
```

Le ragioni della scelta sono tre:

1. **Confrontabilità fra prodotti.** Il dataset comprende volumi da 3.000 a
   12.000 cartoni/mese. Un criterio basato su MAE o RMSE produrrebbe numeri
   non confrontabili e renderebbe impossibile affermare che «Nutella è più
   prevedibile di Happy Hippo».
2. **Interpretabilità manageriale.** «Il modello sbaglia in media del 5%» è
   una frase comprensibile a un direttore della supply chain.
3. **Diffusione.** Il MAPE è l'indicatore più usato nella pratica aziendale
   di *demand planning*.

**Fallback documentato.** Se il MAPE non è calcolabile per nessun metodo, la
selezione ripiega sull'**RMSE minimo**. Se nemmeno l'RMSE è disponibile, viene
sollevato un errore con messaggio esplicativo in italiano.

**Indicatori di supporto.** MAE e RMSE sono **sempre** esposti in tabella e
selezionabili nel grafico, per consentire di verificare che la scelta non sia
un artefatto del MAPE.

### 10.4 Previsione finale e banda di incertezza

La previsione è costruita in **due passi**:

1. **Validazione** — il metodo è stimato sui 36 mesi di addestramento e
   valutato sui 12 di test, ottenendo le metriche e l'RMSE out-of-sample.
2. **Previsione** — il metodo è **ri-stimato su tutta la storia disponibile**
   (48 mesi) e proiettato per l'orizzonte richiesto.

Il secondo passo è importante: sarebbe uno spreco prevedere il 2026 con un
modello stimato solo fino al 2024. La valutazione serve a **scegliere** il
metodo; la previsione finale usa tutti i dati.

**Banda di incertezza**

```
banda = previsione  ±  z · RMSE_out-of-sample
```

Si tratta di una **stima empirica basata sul modello**, non di un intervallo
di previsione derivato analiticamente. Le ipotesi sono dichiarate
integralmente in dashboard: errori indipendenti, a media nulla, normalmente
distribuiti, con varianza costante lungo l'orizzonte.

La banda **non si allarga** con l'orizzonte. La scelta è deliberata: un
intervallo rigoroso si allargherebbe, ma la forma esatta
dell'allargamento dipende dal modello e non sarebbe corretta per tutti e
cinque i metodi implementati. Si è preferita una banda costante, onestamente
dichiarata come approssimazione, a una banda apparentemente più sofisticata ma
non giustificabile.

### 10.5 Risultati della valutazione

Split 36/12, parametri predefiniti (finestra MA = 3, α = 0,30).

| Prodotto | Metodo | MAE | RMSE | MAPE (%) | Migliore |
|---|---|---:|---:|---:|:---:|
| **Nutella** | Media mobile | 701,7 | 855,2 | 5,64 | |
| | Smorzamento esponenziale | 643,7 | 833,4 | 5,00 | |
| | Regressione lineare | 702,1 | 942,7 | 5,36 | |
| | Naive stagionale | 960,9 | 1.214,4 | 7,47 | |
| | **Holt-Winters additivo** | **649,1** | **950,4** | **4,95** | ✔ |
| **Kinder Cioccolato** | Media mobile | 1.013,6 | 1.220,3 | 11,08 | |
| | **Smorzamento esponenziale** | **910,5** | **1.083,3** | **9,78** | ✔ |
| | Regressione lineare | 961,5 | 1.153,0 | 10,35 | |
| | Naive stagionale | 1.205,0 | 1.432,1 | 12,05 | |
| | Holt-Winters additivo | 1.186,5 | 1.333,7 | 12,49 | |
| **Ferrero Rocher** | Media mobile | 4.188,6 | 4.618,0 | 80,93 | |
| | Smorzamento esponenziale | 3.170,4 | 3.367,1 | 59,28 | |
| | Regressione lineare | 2.406,9 | 2.604,4 | 43,80 | |
| | **Naive stagionale** | **599,3** | **719,9** | **9,91** | ✔ |
| | Holt-Winters additivo | 962,9 | 1.170,9 | 15,84 | |
| **Kinder Happy Hippo** | Media mobile | 1.085,3 | 1.381,1 | 33,32 | |
| | Smorzamento esponenziale | 1.019,6 | 1.206,9 | 29,66 | |
| | **Regressione lineare** | **1.010,3** | **1.145,9** | **24,60** | ✔ |
| | Naive stagionale | 1.292,8 | 1.532,6 | 30,38 | |
| | Holt-Winters additivo | 1.115,7 | 1.214,8 | 30,54 | |

> **Figura 3** — `report/figures/03_domanda_e_previsione_*.html`
> Domanda storica (addestramento e test), previsione sul test, previsione
> futura e banda di incertezza.
>
> **Figura 4** — `report/figures/04_accuratezza_metodi_*.html`
> Confronto grafico dell'accuratezza dei cinque metodi.

### 10.6 Sintesi e commento

| Prodotto | CV storico (%) | Metodo migliore | MAPE (%) |
|---|---:|---|---:|
| Nutella | 6,7 | Holt-Winters additivo | **4,95** |
| Kinder Cioccolato | 14,1 | Smorzamento esponenziale | **9,78** |
| Ferrero Rocher | 39,9 | Naive stagionale | **9,91** |
| Kinder Happy Hippo | 26,8 | Regressione lineare | **24,60** |

**Quattro prodotti, quattro metodi diversi.** È il risultato centrale del
progetto e conferma empiricamente la premessa della specifica: non esiste un
metodo universalmente migliore.

**Il metodo migliore riflette la struttura della serie.** Nutella, quasi
stazionaria, è ben servita da metodi che stimano il livello. Kinder
Cioccolato, con trend moderato e stagionalità debole, premia lo smorzamento
esponenziale, che insegue il livello senza sovra-modellare una stagionalità
poco pronunciata. Ferrero Rocher, fortemente stagionale, è prevedibile solo da
metodi che modellano la stagionalità. Happy Hippo, dominato da rumore e
promozioni, premia la regressione lineare, che coglie il trend sottostante
ignorando il rumore.

**Il costo di un metodo inadeguato è quantificabile.** Su Ferrero Rocher lo
scarto fra il migliore (9,91%) e il peggiore (80,93%) è di **71 punti
percentuali**. Una media mobile su un prodotto fortemente stagionale produce
previsioni praticamente inutilizzabili.

**La complessità non garantisce l'accuratezza.** Holt-Winters, il metodo più
sofisticato, vince su un solo prodotto su quattro ed è battuto dal
semplicissimo naive stagionale proprio sulla serie più stagionale. La ragione
è che il picco natalizio del generatore è molto **regolare** e
**asimmetrico**: il naive lo riproduce esattamente, mentre Holt-Winters tende
a lisciarlo nell'aggiornamento esponenziale degli indici stagionali. È la
conferma empirica del principio per cui un modello complesso va adottato solo
se supera un benchmark semplice.

**Una divergenza fra criteri.** Su Nutella il MAPE indica Holt-Winters
(4,95% contro 5,00%) mentre l'RMSE indicherebbe lo smorzamento esponenziale
(833 contro 950). Il margine è talmente esiguo da rendere le due alternative
**equivalenti nella pratica**: è un'osservazione onesta che un'applicazione
meno trasparente nasconderebbe.

---

## 11. Pianificazione delle scorte

### 11.1 Perché scomporre la scorta

Una giacenza di magazzino non è una grandezza indistinta: è la somma di
componenti che esistono per **ragioni diverse** e che rispondono a **leve
diverse**. Sommarle senza distinguerle impedisce qualunque diagnosi
gestionale.

| Componente | Esiste perché… | Si riduce agendo su… |
|---|---|---|
| **Ciclica** | si ordina a lotti, non unità per unità | frequenza di riordino |
| **Di sicurezza** | la domanda futura è incerta | accuratezza previsionale, livello di servizio |
| **Anticipata** | la domanda è stagionale e la capacità rigida | flessibilità produttiva |
| **Pipeline** | la merce impiega tempo ad arrivare | lead time, prossimità dei fornitori |

Mostrare *quanta* scorta serve è utile; mostrare *perché* serve è ciò che
consente di decidere dove intervenire.

### 11.2 Notazione

| Simbolo | Significato | Unità |
|---|---|---|
| `D` | domanda media mensile **prevista** | cartoni/mese |
| `R` | periodo di riesame / ciclo di riordino | mesi |
| `L` | lead time di approvvigionamento | mesi |
| `σ` | dev. standard dell'**errore previsionale** | cartoni |
| `z` | fattore di sicurezza della normale standard | — |

`D` è la media della **previsione** sull'orizzonte selezionato, **non** la
media storica: le scorte si dimensionano sulla domanda attesa, non su quella
passata. È per questo che la leva «trend» influenza il fabbisogno.

---

## 12. Il modello delle scorte

### 12.1 Scorta ciclica

```
Q = D × R                      (lotto di riordino)
Scorta ciclica = Q / 2 = D × R / 2
```

**Derivazione.** Il modello adottato è il riordino a intervallo fisso con
copertura pari al periodo di riesame: ogni `R` mesi si ordina la quantità
necessaria a coprire i successivi `R` mesi. Se la domanda è prelevata a tasso
uniforme, la giacenza evolve linearmente da `Q` a `0`, e la giacenza **media**
su un ciclo è `Q/2`.

**Ipotesi dichiarate**: prelievo uniforme nel periodo; nessun vincolo di
lotto minimo; nessuno sconto quantità; nessun costo esplicito di ordinazione
o mantenimento.

**Perché non l'EOQ.** Il lotto economico di Wilson sarebbe teoricamente più
raffinato, ma richiede il costo di emissione dell'ordine e il costo unitario
di mantenimento. Nel caso Ferrero questi valori non sono pubblici:
andrebbero **inventati**, e il risultato apparirebbe più rigoroso di quanto
sia. Il modello a copertura fissa dipende da un solo parametro (`R`) che
l'utente imposta consapevolmente, senza introdurre numeri arbitrari.

### 12.2 Scorta di sicurezza

```
Scorta di sicurezza = z × σ × √(intervallo di protezione)
```

Nella configurazione di base l'intervallo di protezione è il solo lead time:
`z × σ × √L`.

**Derivazione.** La scorta di sicurezza protegge dalla variabilità della
domanda durante il periodo in cui non si può reagire. Se gli errori mensili
sono **indipendenti**, le varianze si sommano sui mesi dell'intervallo:
`Var(domanda su L mesi) = L·σ²`, quindi `σ_L = σ·√L`. Approssimando con una
distribuzione normale, la scorta che garantisce probabilità `SL` di non andare
in rottura è `z·σ_L`, con `z = Φ⁻¹(SL)`.

| Livello di servizio | z |
|---|---:|
| 90,0% | 1,282 |
| 95,0% | 1,645 |
| 97,5% | 1,960 |
| 99,0% | 2,326 |

Il livello di servizio è inteso come **cycle service level** — probabilità di
non andare in rottura durante un ciclo — e non come *fill rate*, che è una
grandezza diversa. La distinzione è dichiarata perché le due sono spesso
confuse.

**La scelta metodologicamente più rilevante: σ è l'errore previsionale.**
Una formulazione elementare userebbe la deviazione standard della **domanda
storica**. Il progetto usa invece la deviazione standard dell'**errore
previsionale out-of-sample** (l'RMSE sul test).

La ragione è che ciò che causa una rottura di stock non è la variabilità
della domanda in sé, ma la parte di variabilità che **non si è riusciti a
prevedere**. Una domanda stagionale ma perfettamente anticipata dal modello
non richiede alcun cuscinetto: richiede semmai scorta anticipata, che è
un'altra cosa.

L'effetto è quantitativamente enorme:

| Prodotto | Dev. std domanda | σ (RMSE out-of-sample) | Rapporto |
|---|---:|---:|---:|
| Nutella | 823 | 950 | 1,15 |
| Kinder Cioccolato | 1.268 | 1.083 | 0,85 |
| **Ferrero Rocher** | **2.497** | **720** | **0,29** |
| Kinder Happy Hippo | 1.020 | 1.146 | 1,12 |

Su Ferrero Rocher, usare la variabilità grezza avrebbe **sovrastimato di
3,5 volte** il fabbisogno di sicurezza.

**Ipotesi dichiarate**: `σ` stimata dall'errore previsionale; errori mensili
indipendenti; lead time deterministico; domanda normale nell'intervallo di
protezione; livello di servizio come *cycle service level*.

**Opzione avanzata.** Nel riordino periodico la copertura dovrebbe estendersi
anche al tempo fra due revisioni: `σ_IP = σ·√(L+R)`. La dashboard offre la
variante come opzione, disattivata per impostazione predefinita per aderire
alla formulazione richiesta dalla specifica. Con `L = 2` e `R = 1`, attivarla
aumenta la scorta di sicurezza del 22,5% (`√3/√2`).

### 12.3 Scorta anticipata

```
C(t) = Σ ( d(k) − B )          per k = 1…t,   C(0) = 0
Scorta anticipata = max C(t) − min C(t)
```

dove `d(k)` è la domanda prevista del mese `k` e `B` il ritmo produttivo
livellato (per default la media della previsione).

**Derivazione.** Il modello rappresenta il **livellamento della produzione**:
l'impresa produce a ritmo costante `B` mentre la domanda è stagionale. Nei
mesi di bassa stagione si accumula magazzino, consumato poi durante il picco.
Definita l'eccedenza cumulata `C(t)`, la giacenza è `I(t) = I(0) − C(t)`. Per
non andare in rottura serve `I(0) ≥ max C(t)`; adottando il valore minimo, la
giacenza **massima** generata dal livellamento è `max C(t) − min C(t)`.

Il punto `C(0) = 0` è incluso fra i candidati perché la giacenza iniziale è
essa stessa un punto ammissibile della traiettoria.

**Proprietà.** Vale 0 per domanda perfettamente piatta; cresce
monotonicamente con l'ampiezza stagionale. Esempio verificabile a mano: sei
mesi a 100 unità seguiti da sei a 300 danno media 200; l'eccedenza cumulata
scende a −600 e risale a 0, quindi la scorta anticipata vale **600 unità**.

**Alternativa gestionale.** Per Ferrero Rocher l'alternativa all'accumulo
sarebbe dotarsi di **flessibilità di capacità produttiva** (turni aggiuntivi,
personale stagionale), con costi di straordinario e di gestione del personale.
Il confronto fra i due è una decisione classica di *aggregate planning*, che
il progetto quantifica dal lato della scorta.

### 12.4 Scorta pipeline

```
Scorta pipeline = D × L
```

**Derivazione.** È un'applicazione diretta della **legge di Little**: in un
sistema stazionario il numero medio di unità presenti è pari al tasso di
flusso per il tempo di permanenza. Il tasso di flusso del rifornimento a
regime coincide con la domanda media, e il tempo di attraversamento è il lead
time.

**Interpretazione.** La scorta pipeline è **già di proprietà dell'impresa** —
tipicamente già pagata o impegnata — ma **non è disponibile per la vendita
immediata**. Incide sul capitale circolante senza contribuire al livello di
servizio nel breve periodo.

Cresce **linearmente** con il lead time: raddoppiando `L` raddoppia il
capitale in transito.

### 12.5 Scorta totale

```
Scorta totale rilevante = ciclica + sicurezza + anticipata + pipeline
```

La dashboard espone, oltre al totale: il valore assoluto di ciascuna
componente, la quota percentuale sul totale e la **copertura in mesi** di
domanda media prevista, indicatore sintetico confrontabile fra prodotti.

---

## 13. Progettazione della dashboard

### 13.1 Scelta della tecnologia

È stata adottata **Streamlit**, espressamente ammessa dalla specifica, per
cinque ragioni: l'applicazione resta interamente in Python; è adeguata a una
mini-dashboard; fornisce controlli interattivi, tabelle e grafici nativi;
semplifica la dimostrazione locale; elimina la complessità di un frontend
separato.

I grafici sono realizzati con **Plotly**, che offre interattività (zoom,
tooltip, selezione delle serie dalla legenda) e si integra nativamente con
Streamlit.

### 13.2 Struttura dell'interfaccia

L'interfaccia è **interamente in italiano**.

**Sidebar — «Configurazione»**, organizzata in quattro gruppi:

- *Prodotto*: articolo analizzato, con descrizione del comportamento atteso;
- *Previsione*: metodo (automatico o imposto), orizzonte, finestra media
  mobile, alpha;
- *Caratteristiche della domanda*: variabilità, trend, stagionalità;
- *Parametri logistici*: lead time, livello di servizio, periodo di riesame;
- *Opzioni avanzate*: mesi di test, intervallo di protezione esteso, pulsante
  di rigenerazione del dataset.

**Pagina principale** — otto sezioni:

| Sezione | Contenuto |
|---|---|
| **1 · Scenario di analisi** | Parametri correnti, scheda prodotto, confronto base/scenario, profilo stagionale, statistiche descrittive |
| **2 · Domanda storica e prevista** | Grafico con addestramento, test, previsione sul test, previsione futura, banda di incertezza; tabella della previsione |
| **3 · Confronto dei metodi previsionali** | Tabella MAE/RMSE/MAPE/Bias con il migliore evidenziato, grafico a barre con metrica selezionabile, commento sulla selezione |
| **4 · Composizione delle scorte** | Barra impilata, grafico ad anello, tabella con le **formule applicate e i valori sostituiti** |
| **5 · Indicatori sintetici (KPI)** | 12 KPI in tre righe di schede |
| **6 · Analisi dello scenario** | Interpretazione gestionale generata dinamicamente dai valori calcolati |
| **7 · Confronto fra scenari** | Due configurazioni A/B, tabella di variazione, grafici comparativi affiancati |
| **8 · Quadro di sintesi** | Tutti e quattro i prodotti, con il metodo migliore per ciascuno |

### 13.3 Scelte di rappresentazione grafica

- Tutti i grafici hanno **titoli, etichette degli assi, legende e tooltip in
  italiano**, con indicazione dell'unità di misura.
- Le scale degli assi **partono da zero** quando il confronto riguarda
  quantità assolute, per non amplificare visivamente differenze modeste.
- La banda di incertezza è resa come **area semitrasparente**, mai come linea
  piena, per non essere confusa con una previsione puntuale.
- Addestramento, test, previsione sul test e previsione futura hanno
  **colori e stili di linea distinti**, con linee verticali che segnano i
  confini dei periodi.
- Nel confronto dei quattro prodotti i volumi sono **normalizzati** (media di
  ciascun prodotto = 100): senza normalizzazione la serie Nutella (~12.000)
  schiaccerebbe quella Happy Hippo (~3.000), rendendo illeggibili le
  differenze di profilo.

### 13.4 Gestione degli errori

L'applicazione **non espone mai un traceback Python**. Ogni modulo definisce
un'eccezione di dominio con messaggio in italiano, e la dashboard la cattura
mostrandola in un riquadro di errore con il suggerimento dell'azione
correttiva.

Sono gestite: dataset mancante, vuoto o malformato; combinazioni di parametri
non valide; prodotto non in anagrafica; lead time o livello di servizio fuori
intervallo; osservazioni storiche insufficienti; test set troppo lungo per lo
split richiesto.

---

## 14. Implementazione Python

### 14.1 Principio architetturale

Il progetto è costruito attorno a un'unica regola: **la logica di calcolo non
conosce l'interfaccia**. Tutta la logica previsionale, di gestione scorte e di
simulazione risiede nel package `src/` e non importa mai Streamlit. Il file
`app.py` contiene esclusivamente presentazione.

Le conseguenze pratiche sono tre: il 90% del codice è **testabile** senza
avviare un server; lo script di generazione degli asset per la relazione
**riusa** le stesse funzioni della dashboard senza duplicare logica;
l'interfaccia sarebbe **sostituibile** senza riscrivere il modello.

### 14.2 Moduli

| Modulo | Responsabilità |
|---|---|
| `config.py` | Costanti, anagrafica prodotti, parametri di default |
| `data_generator.py` | Generazione e salvataggio del dataset sintetico |
| `data_validation.py` | 11 controlli di validità, caricamento CSV |
| `forecasting.py` | 5 metodi previsionali |
| `metrics.py` | MAE, RMSE, MAPE, Bias, sMAPE |
| `evaluation.py` | Split cronologico, confronto, selezione, banda |
| `inventory.py` | 4 componenti di scorta + piano complessivo |
| `scenarios.py` | Orchestrazione dell'intera catena |
| `charts.py` | Figure Plotly in italiano |
| `narrative.py` | Commenti gestionali dinamici |
| `utils.py` | Formattazione italiana, statistiche descrittive |

Il grafo delle dipendenze è **aciclico**: nessun modulo di livello inferiore
importa un modulo di livello superiore.

### 14.3 Scelte progettuali

**Metodi scritti da zero.** I cinque metodi sono implementati con NumPy
anziché con `statsmodels`, per trasparenza didattica (la formulazione
matematica è leggibile nel codice), per ridurre le dipendenze e per
controllare l'inizializzazione di Holt-Winters, che è deterministica e
documentata.

**Registro dei metodi.** Dashboard e motore di valutazione **iterano** su un
dizionario `METHOD_REGISTRY` anziché contenere elenchi fissi. Aggiungere un
sesto metodo richiede di scrivere la funzione e inserire una voce nel
registro: nessuna modifica a `app.py` o `evaluation.py`.

**Dataclass immutabili.** `ScenarioConfig` e `ProductParameters` sono
`frozen=True`: sono *hashable* e quindi utilizzabili come chiave della cache
di Streamlit (due scenari identici non vengono ricalcolati); le modifiche
avvengono con `dataclasses.replace()`, che produce una copia, rendendo
impossibile alterare per errore lo stato condiviso.

**Errori tipizzati per dominio.** Sei eccezioni specifiche
(`DataValidationError`, `ForecastingError`, `MetricsError`,
`InventoryError`, `EvaluationError`, `ScenarioError`), tutte con messaggi in
italiano rivolti all'utente finale.

### 14.4 Test automatici

**264 test**, tempo di esecuzione **inferiore a 5 secondi**, tutti superati.

| File | Test | Oggetto |
|---|---:|---|
| `test_data_generator.py` | 31 | struttura, dominio, riproducibilità, profili differenziati |
| `test_data_validation.py` | 21 | 11 controlli + gestione errori file |
| `test_forecasting.py` | 64 | 5 metodi su serie deterministiche + casi limite |
| `test_metrics.py` | 34 | formule, casi limite, split cronologico, selezione |
| `test_inventory.py` | 42 | formule, monotonie, piano complessivo |
| `test_scenarios.py` | 50 | effetti delle leve, validazione, confronto |
| `test_dashboard.py` | 22 | avvio, sezioni, widget, interazione, grafici, commenti |
| **Totale** | **264** | |

La verifica si articola su **tre livelli**.

**Correttezza numerica su casi calcolati a mano.** Dove possibile i test
confrontano il risultato con un valore derivato analiticamente. Esempio: per
la serie `[100, 200, 300]` con `α = 0,5`, la ricorsione dà `L₀ = 100`,
`L₁ = 150`, `L₂ = 225`, e il test verifica che la previsione sia esattamente
225.

**Proprietà matematiche.** Alcune proprietà devono valere sempre: `RMSE ≥ MAE`
(verificata su 20 serie casuali); scorta anticipata mai negativa (25 serie
casuali); somma delle quote percentuali pari a 100; quadruplicare il lead
time raddoppia esattamente la scorta di sicurezza.

**Requisiti della specifica.** I requisiti direzionali del PW24 sono tradotti
in test espliciti: variabilità ↑ ⇒ sicurezza ↑; lead time ↑ ⇒ pipeline ↑;
stagionalità ↑ ⇒ anticipata ↑; trend ↑ ⇒ domanda prevista ↑.

**Serie deterministiche come banco di prova.** I metodi previsionali sono
testati su serie di cui si conosce analiticamente il comportamento (costante,
lineare perfetta, trend + sinusoide), rendendo i test stringenti e stabili,
indipendenti dalla particolare realizzazione casuale.

**Test della dashboard.** `test_dashboard.py` usa
`streamlit.testing.v1.AppTest`, l'harness ufficiale di Streamlit, che esegue
l'app in modalità headless e consente di simulare l'interazione. Verifica
end-to-end che, ad esempio, aumentando il cursore del lead time il KPI della
scorta pipeline aumenti effettivamente.

---

## 15. Simulazione degli scenari

### 15.1 Il principio: rigenerazione, non deformazione

Le tre leve di domanda **non deformano** la serie esistente moltiplicandola
per un fattore. Agiscono sui **parametri del processo generatore**, e la serie
viene **rigenerata da zero** con lo stesso seed.

```
parametri di base        leve di scenario
       │                        │
       └───────────┬────────────┘
                   ▼
       parametri di scenario
                   ▼
    generate_product_series(seed invariato)
                   ▼
            serie di scenario
                   ▼
  valutazione metodi → previsione → piano di scorta
```

La scelta ha due conseguenze. **Coerenza statistica**: lo scenario è una
realizzazione legittima dello stesso modello, non una deformazione arbitraria.
**Isolamento della causa**: poiché il seed resta invariato, la sequenza di
shock casuali è la stessa, e qualunque differenza osservata è attribuibile
**esclusivamente** alla leva modificata, non a una diversa estrazione
casuale.

**Separazione dei dati.** Il file `data/demand_history.csv` **non viene mai
modificato** dalla simulazione: lo scenario vive in memoria, e l'applicazione
conserva *entrambe* le serie per sovrapporle graficamente. La proprietà è
verificata da un test che confronta i byte del file prima e dopo una
simulazione.

### 15.2 Verifica degli effetti

Partendo dalla configurazione baseline su Ferrero Rocher (variabilità ×1,
lead time 2 mesi, servizio 95%, riesame 1 mese) e modificando **una leva alla
volta**:

| Configurazione | σ | Sicurezza | Pipeline | Anticipata | Ciclica | **Totale** |
|---|---:|---:|---:|---:|---:|---:|
| **Baseline** | 720 | 1.675 | 12.748 | 11.272 | 3.187 | **28.882** |
| Variabilità ×2 | **1.496** | **3.480** | 12.114 | 10.603 | 3.028 | 29.225 |
| Lead time 5 mesi | 720 | **2.648** | **31.870** | 11.272 | 3.187 | **48.977** |
| Stagionalità ×2 | 792 | 1.842 | 14.679 | **22.348** | 3.670 | 42.540 |
| Trend ×3 | 875 | 2.035 | **15.615** | 14.127 | **3.904** | 35.681 |

Rapporti rispetto al baseline:

| Configurazione | Sicurezza | Pipeline | Anticipata | Totale |
|---|---:|---:|---:|---:|
| Variabilità ×2 | **×2,08** | ×0,95 | ×0,94 | ×1,01 |
| Lead time 5 mesi | **×1,58** | **×2,50** | ×1,00 | ×1,70 |
| Stagionalità ×2 | ×1,10 | ×1,15 | **×1,98** | ×1,47 |
| Trend ×3 | ×1,22 | ×1,23 | ×1,25 | ×1,24 |

**Lettura.** Variabilità ×2 → la scorta di sicurezza passa da 1.675 a 3.480
(+108%), coerentemente con la linearità in `σ`. Lead time 2 → 5 mesi → la
pipeline passa da 12.748 a 31.870, cioè **esattamente ×2,5** come previsto
dalla linearità, e la sicurezza da 1.675 a 2.648, cioè **×1,58 ≈ √2,5** come
previsto dalla radice quadrata: le due diverse leggi di crescita sono
verificabili numericamente. Stagionalità ×2 → la scorta anticipata raddoppia
praticamente (da 11.272 a 22.348). Trend ×3 → crescono le componenti
proporzionali alla domanda.

### 15.3 Il confronto A/B di riferimento

Prodotto **Ferrero Rocher**, orizzonte 12 mesi, riesame 1 mese.

- **Scenario A — Filiera stabile**: variabilità ×0,5; lead time 2 mesi;
  servizio 95%.
- **Scenario B — Filiera sotto stress**: variabilità ×2,0; lead time 5 mesi;
  servizio 99%.

| Indicatore | A | B | Variazione | Var. % |
|---|---:|---:|---:|---:|
| Domanda media prevista (cartoni/mese) | 6.533 | 6.057 | −476 | −7,3% |
| Dev. std errore previsionale | 358 | 1.496 | +1.138 | **+317,7%** |
| Scorta ciclica | 3.266 | 3.028 | −238 | −7,3% |
| Scorta di sicurezza | 833 | 7.782 | +6.949 | **+834,0%** |
| Scorta anticipata | 11.607 | 10.603 | −1.004 | −8,7% |
| Scorta pipeline | 13.065 | 30.284 | +17.219 | **+131,8%** |
| **Scorta totale** | **28.771** | **51.697** | **+22.926** | **+79,7%** |
| Copertura (mesi) | 4,4 | 8,5 | +4,1 | +93,8% |

> **Figura 7** — `report/figures/07_confronto_scenari.html`
> Confronto grafico delle componenti di scorta nei due scenari.

**Il moltiplicatore maggiore non è il contributo maggiore.** Benché la
sicurezza cresca dell'834% — il moltiplicatore più vistoso — in valore
assoluto la **pipeline** spiega il **75%** dell'aumento complessivo (+17.219
su +22.926), perché partiva da una base molto più grande. È una distinzione
operativamente decisiva: per contenere l'impatto occorre agire sul **lead
time**, non sul livello di servizio.

**Perché anticipata e ciclica diminuiscono.** Entrambe dipendono dalla domanda
media prevista, inferiore del 7,3% nello scenario B. La maggiore variabilità
altera le ultime osservazioni su cui il metodo si basa, producendo una
previsione leggermente più bassa. È un effetto di secondo ordine, che
l'applicazione mostra onestamente anziché nascondere.

### 15.4 Il commento gestionale dinamico

La sezione 6 della dashboard genera automaticamente un'analisi in italiano
**costruita sui valori effettivamente calcolati**. Il testo non è un modello
fisso con segnaposto: cambia **struttura**, non solo numeri.

Esempi di adattamento: se la scorta anticipata supera il 5% del totale il
commento spiega il meccanismo del livellamento produttivo, altrimenti osserva
che il profilo è troppo piatto per renderla rilevante; se la domanda prevista
si discosta di oltre il 2% dalla media storica viene aggiunto un paragrafo sul
trend, altrimenti omesso; il paragrafo di confronto identifica
automaticamente **quale componente** spiega la maggior parte dello scostamento
e **quali leve** differiscono; la conclusione gestionale cambia a seconda che
la variazione sia superiore a +15%, inferiore a −15%, oppure contenuta — nel
terzo caso osservando che cambia la **composizione** del rischio anziché il
suo livello.

---

## 16. Risultati

### 16.1 Le quattro serie hanno profili effettivamente diversi

| Prodotto | Media | CV (%) | Escursione stagionale | Profilo |
|---|---:|---:|---:|---|
| Nutella | 12.242 | 6,7 | 15 | stabile |
| Kinder Cioccolato | 9.019 | 14,1 | 29 | trend moderato |
| Ferrero Rocher | 6.260 | 39,9 | **118** | fortemente stagionale |
| Kinder Happy Hippo | 3.814 | 26,8 | 57 | rumoroso e promozionale |

### 16.2 Ogni prodotto richiede un metodo previsionale diverso

| Prodotto | Metodo migliore | MAPE (%) | Peggiore | MAPE (%) | Divario |
|---|---|---:|---|---:|---:|
| Nutella | Holt-Winters additivo | 4,95 | Naive stagionale | 7,47 | 2,5 pt |
| Kinder Cioccolato | Smorzamento esponenziale | 9,78 | Holt-Winters | 12,49 | 2,7 pt |
| Ferrero Rocher | Naive stagionale | 9,91 | Media mobile | 80,93 | **71,0 pt** |
| Kinder Happy Hippo | Regressione lineare | 24,60 | Media mobile | 33,32 | 8,7 pt |

### 16.3 Composizione delle scorte nello scenario baseline

Lead time 2 mesi, servizio 95%, riesame 1 mese, orizzonte 12 mesi.

| Prodotto | Ciclica | Sicurezza | Anticipata | Pipeline | **Totale** | Copertura |
|---|---:|---:|---:|---:|---:|---:|
| Nutella | 6.683 | 2.211 | 3.479 | 26.732 | **39.105** | 2,9 mesi |
| Kinder Cioccolato | 5.075 | 2.520 | 0 | 20.299 | **27.893** | 2,7 mesi |
| Ferrero Rocher | 3.187 | 1.675 | 11.272 | 12.748 | **28.882** | 4,5 mesi |
| Kinder Happy Hippo | 2.177 | 2.665 | 324 | 8.709 | **13.876** | 3,2 mesi |

Composizione percentuale:

| Prodotto | Ciclica | Sicurezza | Anticipata | Pipeline |
|---|---:|---:|---:|---:|
| Nutella | 17,1% | 5,7% | 8,9% | **68,4%** |
| Kinder Cioccolato | 18,2% | 9,0% | 0,0% | **72,8%** |
| Ferrero Rocher | 11,0% | 5,8% | **39,0%** | 44,1% |
| Kinder Happy Hippo | 15,7% | **19,2%** | 2,3% | 62,8% |

> **Figura 5** — `report/figures/05_composizione_scorte_*.html`
> Barra impilata delle quattro componenti per ciascun prodotto.
>
> **Figura 6** — `report/figures/06_quota_scorte_*.html`
> Peso percentuale delle componenti.

### 16.4 Il costo marginale del livello di servizio è crescente

| Da → A | Incremento di z | Incremento scorta sicurezza |
|---|---:|---:|
| 90% → 95% | +0,363 | +28,3% |
| 95% → 97,5% | +0,315 | +19,2% |
| 97,5% → 99% | +0,366 | +18,7% |
| 99% → 99,9% | +0,764 | +32,8% |

---

## 17. Interpretazione gestionale

### 17.1 Variabilità sistematica e variabilità casuale non sono la stessa cosa

| Prodotto | CV storico (%) | MAPE (%) | Natura della variabilità |
|---|---:|---:|---|
| Ferrero Rocher | **39,9** | 9,91 | prevalentemente **sistematica** (stagionale) |
| Kinder Happy Hippo | 26,8 | **24,60** | prevalentemente **casuale** (rumore, promozioni) |

Ferrero Rocher è la serie **più variabile** ma **non la meno prevedibile**:
la sua variabilità è in larga parte stagionale, cioè anticipabile. Happy
Hippo ha variabilità inferiore ma MAPE più che doppio.

La conseguenza gestionale è diretta e non banale:

- la variabilità **sistematica** si gestisce con la **scorta anticipata**,
  cioè con la pianificazione della produzione;
- la variabilità **casuale** si gestisce con la **scorta di sicurezza**, cioè
  con un cuscinetto contro l'ignoto.

Confondere le due porta a **sovradimensionare la sicurezza su prodotti
stagionali**. Il modello implementato evita l'errore stimando `σ` sull'errore
previsionale: su Ferrero Rocher, usare la variabilità grezza avrebbe
sovrastimato la scorta di sicurezza di **3,5 volte**.

La conferma empirica è nella composizione delle scorte: Ferrero Rocher ha il
39% di scorta **anticipata** e solo il 5,8% di sicurezza; Happy Hippo ha il
19,2% di **sicurezza** e solo il 2,3% di anticipata. Le due strategie sono
opposte, e la diagnosi corretta della natura della variabilità è ciò che
permette di scegliere quella giusta.

### 17.2 La composizione racconta il prodotto

Le quattro righe della tabella di composizione hanno profili nettamente
diversi, e ciascuno riflette la natura della domanda.

**Ferrero Rocher** è l'unico in cui la pipeline non domina: il 39% della sua
scorta esiste per ragioni di **stagionalità**. È il prodotto in cui la
pianificazione della produzione conta più della logistica di
approvvigionamento. Ha anche la copertura più alta (4,5 mesi contro 2,7-3,2
degli altri) nonostante volumi intermedi: la concentrazione della domanda nel
tempo impone strutturalmente più magazzino.

**Kinder Happy Hippo** ha la quota di sicurezza più alta (19,2%) pur essendo
il prodotto con i volumi minori. È il prezzo dell'imprevedibilità: è il
prodotto che "costa di più" in termini di incertezza.

**Nutella e Kinder Cioccolato** sono dominati dalla pipeline (68% e 73%): sono
prodotti prevedibili e regolari, per i quali il problema di scorta è
essenzialmente un problema di **tempi di approvvigionamento**.

### 17.3 Il lead time è la leva dominante

Nello scenario baseline la scorta pipeline rappresenta fra il **44% e il 73%**
della scorta totale. È il risultato con la conseguenza operativa più
immediata.

Il motivo è strutturale: con `L = 2` mesi e `R = 1` mese, la pipeline vale
`D × 2` mentre la ciclica vale `D × 0,5`, cioè **quattro volte di meno**.
E mentre la pipeline cresce **linearmente** con il lead time, la sicurezza
cresce con la **radice quadrata**.

Ne segue che l'intervento con il maggiore impatto sul capitale circolante non
è l'ottimizzazione dei lotti di riordino né la riduzione del livello di
servizio, ma **l'accorciamento del lead time**: fornitori più vicini,
trasporto più rapido, produzione più reattiva.

Il confronto A/B lo conferma quantitativamente: la pipeline spiega il **75%**
dell'incremento di scorta fra i due scenari, pur avendo un moltiplicatore
percentuale molto inferiore a quello della sicurezza.

### 17.4 La scorta di sicurezza è ovunque la componente minore

Fra il 5,7% e il 19,2% del totale. È un risultato che merita commento, perché
contraddice l'intuizione comune secondo cui la scorta serve soprattutto a
"stare tranquilli".

Nel modello adottato la maggior parte del magazzino esiste per ragioni
**strutturali** — tempi di transito e lotti di riordino — e non per
incertezza. Chi volesse ridurre il magazzino dovrebbe agire prima di tutto
sui **tempi di filiera**, non sul livello di servizio.

### 17.5 La scelta del livello di servizio è una decisione economica

Il fattore `z` cresce in modo **più che proporzionale** avvicinandosi al 100%,
e il 100% richiederebbe una scorta infinita. Ogni punto oltre il 97,5% ha un
costo marginale crescente.

La decisione non è quindi tecnica ma economica: va confrontato il costo di
mantenimento della scorta aggiuntiva con il costo atteso delle rotture di
stock evitate — mancato margine, penali contrattuali verso la distribuzione,
perdita di spazio a scaffale. Per un prodotto alimentare va inoltre
considerato il rischio di **obsolescenza** legato alla shelf life, che il
modello non quantifica ma che la discussione deve includere.

### 17.6 La qualità della previsione ha un valore economico misurabile

La catena logica del progetto rende esplicito un collegamento che spesso
resta implicito:

```
metodo previsionale migliore
        ↓
  errore previsionale minore (σ)
        ↓
 scorta di sicurezza minore
        ↓
  capitale circolante minore
```

Su Ferrero Rocher, passare dalla media mobile (RMSE 4.618) al naive
stagionale (RMSE 720) riduce `σ` di **6,4 volte**, e con essa la scorta di
sicurezza nella stessa proporzione. Investire nel miglioramento del processo
previsionale non è un esercizio statistico: è un investimento con un ritorno
quantificabile in capitale liberato.

### 17.7 Il metodo previsionale condiziona anche la pianificazione stagionale

Un'interazione sottile emerge dai risultati: Kinder Cioccolato ha scorta
anticipata **pari a zero**, pur avendo un'escursione stagionale di 29 punti
indice.

La ragione è che il suo metodo migliore — lo smorzamento esponenziale —
produce una previsione **piatta**, e la scorta anticipata è calcolata sulla
previsione. Se la previsione ufficiale non prevede picchi, non c'è nulla da
anticipare.

Il comportamento è **internamente coerente**, ma segnala un rischio reale:
adottare un metodo non stagionale su un prodotto stagionale non peggiora solo
le previsioni, ma **azzera anche la pianificazione dell'accumulo preventivo**.
È un effetto a cascata che l'applicazione rende visibile anziché nascondere, e
che costituisce un limite del modello (cfr. capitolo 18).

---

## 18. Limiti

I limiti che seguono sono semplificazioni **consapevoli**, dichiarate per
consentire una valutazione corretta della portata dei risultati. Nessuno
invalida il lavoro.

### 18.1 Limiti relativi ai dati

| # | Limite | Implicazione |
|---|---|---|
| L1 | I dati sono **sintetici** | I risultati hanno valore metodologico, non predittivo sul mercato reale |
| L2 | Il generatore impone una **struttura nota** | I metodi sono avvantaggiati rispetto a dati reali, dove la struttura è ignota e instabile |
| L3 | Le serie sono **brevi** (48 mesi) | Il test copre un solo ciclo stagionale; gli indici stagionali sono stimati su pochi cicli |
| L4 | Nessun **evento eccezionale** | Nessuna rottura di fornitura, nessun lancio o ritiro di prodotto, nessuno shock esogeno |
| L5 | Nessuna **correlazione fra prodotti** | Nella realtà esistono cannibalizzazione e sostituzione fra referenze |

### 18.2 Limiti relativi alla previsione

| # | Limite | Implicazione |
|---|---|---|
| L6 | Parametri di Holt-Winters **non ottimizzati** | Il metodo potrebbe fare meglio con α, β, γ calibrati |
| L7 | **Una sola partizione** train/test | Una *rolling origin evaluation* darebbe stime più robuste |
| L8 | Nessun modello della **componente promozionale** | Le promozioni sono trattate come rumore, non come eventi noti in anticipo |
| L9 | **Banda di incertezza costante** sull'orizzonte | Un intervallo rigoroso si allargherebbe al crescere di h |
| L10 | Il MAPE è **asimmetrico** | Penalizza le sovrastime più delle sottostime |

### 18.3 Limiti relativi ai modelli di scorta

| # | Limite | Implicazione |
|---|---|---|
| L11 | **Lead time deterministico** | Con lead time variabile servirebbe un termine `D²·σ_L²`; la scorta di sicurezza è **sottostimata** |
| L12 | Errori previsionali **indipendenti** | Con autocorrelazione positiva la formula `σ·√L` **sottostima** il fabbisogno |
| L13 | Scorta ciclica a **copertura fissa**, non EOQ | Non si ottimizzano i costi di ordinazione e mantenimento |
| L14 | **Nessun costo monetario** | Si dimensionano quantità, non si ottimizzano costi; manca il *trade-off* economico esplicito |
| L15 | Nessun **vincolo di capacità** | La scorta anticipata calcolata potrebbe eccedere la capacità fisica disponibile |
| L16 | **Shelf life non modellata** | Per un prodotto alimentare, coperture elevate comportano rischio di obsolescenza non quantificato |
| L17 | Domanda assunta **normale** | Con domanda molto asimmetrica l'approssimazione peggiora |
| L18 | **Scorta anticipata dipendente dal metodo previsionale** | Con previsione piatta risulta nulla anche su prodotti stagionali (effetto visibile su Kinder Cioccolato, §17.7) |

I limiti **L11** e **L12** vanno nella stessa direzione: entrambi comportano
una **sottostima** della scorta di sicurezza. È un'indicazione utile per
chiunque volesse usare i risultati come punto di partenza: i valori calcolati
sono prudenziali per difetto, non per eccesso.

---

## 19. Sviluppi futuri

In ordine di rapporto fra valore aggiunto e complessità di realizzazione.

### Priorità alta

**S1 — Scorta anticipata indipendente dal metodo previsionale.** Stimare gli
indici stagionali con una decomposizione dedicata e usarli per la scorta
anticipata, superando il limite L18. Sforzo contenuto, beneficio elevato.

**S2 — Validazione a origine mobile.** Ripetere la valutazione su più
finestre temporali scorrevoli anziché su una sola partizione, mediando le
metriche. Elimina la dipendenza del risultato dalla scelta del punto di taglio
(L7).

**S3 — Ottimizzazione dei parametri di Holt-Winters.** Minimizzare l'errore su
una finestra di validazione interna al training con `scipy.optimize` (L6).

**S4 — Lead time stocastico.** Estendere la scorta di sicurezza alla formula
completa `σ_IP = √( L·σ_D² + D²·σ_L² )`. Richiede un solo parametro
aggiuntivo e supera il limite L11, che è la sottostima più rilevante del
modello attuale.

### Priorità media

**S5 — Dimensione economica.** Introdurre costo unitario, tasso di
mantenimento e costo di rottura, per passare dal dimensionamento delle
quantità all'**ottimizzazione dei costi**. Consentirebbe di calcolare il
livello di servizio ottimale anziché imporlo, e abiliterebbe l'EOQ (L13, L14).

**S6 — Modellazione esplicita delle promozioni.** Trattarle come variabile
esplicativa nota in anticipo tramite regressione con variabili dummy.
Migliorerebbe sensibilmente la previsione di Kinder Happy Hippo, oggi il
prodotto meno prevedibile (L8).

**S7 — Vincoli di capacità.** Verificare che la scorta anticipata richiesta
sia compatibile con la capacità di stoccaggio disponibile (L15).

**S8 — Analisi di sensitività sistematica.** Generare superfici di risposta
(scorta totale in funzione di lead time × livello di servizio), anziché
confrontare due scenari alla volta.

### Priorità bassa

**S9 — Modelli previsionali avanzati** (ARIMA/SARIMA, *ensemble*,
apprendimento automatico). Su serie di 48 osservazioni il rischio di
sovra-adattamento è elevato e il beneficio atteso modesto.

**S10 — Simulazione Monte Carlo** per stimare la distribuzione del livello di
servizio effettivamente conseguito, verificando la validità
dell'approssimazione normale (L17).

**S11 — Esportazione automatica** di un report PDF dalla dashboard.

**S12 — Caricamento di dati esterni**: il livello di validazione è già pronto
a gestirlo.

---

## 20. Conclusioni

Il Project Work ha prodotto un'applicazione Python funzionante che integra la
previsione della domanda e la pianificazione delle scorte in un unico
strumento interattivo, applicandola a quattro prodotti Ferrero con dati
sintetici generati appositamente.

**Sul piano tecnico** sono stati implementati cinque metodi previsionali e
quattro modelli di scorta, scritti da zero con NumPy e organizzati in undici
moduli con architettura modulare in cui la logica di calcolo è completamente
indipendente dall'interfaccia. La correttezza è garantita da **264 test
automatici**, che verificano non solo il funzionamento ma anche le proprietà
matematiche attese e i requisiti direzionali della specifica.

**Sul piano metodologico** il lavoro ha adottato una valutazione
*out-of-sample* con split cronologico rigoroso, verificando automaticamente
l'assenza di fughe di informazione, e un criterio di selezione del modello
dichiarato con il proprio fallback. Ogni semplificazione è stata esplicitata
anziché mascherata: la banda di incertezza è chiamata «empirica» perché tale
è; il modello EOQ non è stato adottato perché avrebbe richiesto costi
inventati; i limiti sono elencati analiticamente in diciotto voci.

**Sul piano dei risultati** tre conclusioni emergono con chiarezza.

La prima è che **ogni prodotto richiede un metodo previsionale diverso**:
quattro prodotti, quattro metodi vincenti, con divari fino a 71 punti di MAPE
fra la scelta migliore e la peggiore. Non esiste un metodo universale, e la
scelta deve essere guidata dai dati.

La seconda è che **la variabilità sistematica e quella casuale richiedono
risposte opposte**. Ferrero Rocher è la serie più variabile ma non la meno
prevedibile, perché la sua variabilità è stagionale: si gestisce con la
scorta anticipata (39% del suo magazzino). Kinder Happy Hippo è meno
variabile ma meno prevedibile, perché la sua variabilità è casuale: si
gestisce con la scorta di sicurezza (19,2% del suo magazzino). Diagnosticare
correttamente la natura della variabilità è ciò che permette di scegliere la
strategia giusta — e di evitare di sovradimensionare la sicurezza di 3,5 volte
su un prodotto stagionale.

La terza è che **il lead time è la leva dominante sul capitale circolante**.
La scorta pipeline rappresenta fra il 44% e il 73% del magazzino totale, e
cresce linearmente con il lead time mentre la sicurezza cresce con la radice
quadrata. Ridurre i tempi di filiera libera più capitale che ridurre il
livello di servizio, anche se è quest'ultimo a produrre le variazioni
percentuali più vistose.

**Sul piano dell'integrità accademica**, la natura sintetica dei dati è
dichiarata nel README, in ogni documento tecnico, in questa relazione e nella
dashboard stessa. Nessun valore numerico è presentato come dato reale
Ferrero; le informazioni istituzionali provengono esclusivamente da fonti
pubbliche verificabili.

Il valore del lavoro è **metodologico**: mostra come si imposta, si
implementa, si valida e si interpreta un sistema di previsione della domanda e
pianificazione delle scorte. I numeri sono sintetici; il metodo è reale.

---

## 21. Repository e modalità di esecuzione

### 21.1 Struttura del repository

```
PW24_Ferrero/
├── app.py                      # Dashboard Streamlit
├── requirements.txt            # Dipendenze con versioni fissate
├── pytest.ini
├── README.md
├── .gitignore
├── data/                       # Dataset sintetico + dizionario dei dati
├── src/                        # Logica applicativa (11 moduli)
├── tests/                      # 264 test automatici
├── scripts/                    # Generazione asset per la relazione
├── docs/                       # Documentazione tecnica (9 documenti + indice)
└── report/                     # Questa relazione, 23 figure, 4 tabelle
```

### 21.2 Installazione

**Windows (PowerShell)**

```powershell
git clone <URL-DEL-REPOSITORY>
cd PW24_Ferrero
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se PowerShell blocca l'attivazione con un errore di *execution policy*:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Linux / macOS**

```bash
git clone <URL-DEL-REPOSITORY>
cd PW24_Ferrero
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 21.3 Esecuzione

```bash
# Avviare la dashboard (si apre su http://localhost:8501)
streamlit run app.py

# Avvio alternativo, se il comando 'streamlit' non è disponibile
python -m streamlit run app.py

# Rigenerare il dataset sintetico (seed 24)
python -m src.data_generator

# Generare figure e tabelle per la relazione
python -m scripts.generate_report_assets

# Eseguire i test
pytest
```

### 21.4 Riproducibilità

Il **seed fissato a 24** garantisce che il dataset rigenerato sia
bit-per-bit identico a quello versionato nel repository, e quindi che **tutti
i numeri riportati in questa relazione siano ottenibili da chiunque** ripeta
la procedura.

L'applicazione funziona **interamente offline** dopo l'installazione delle
dipendenze: non esistono chiamate ad API, download di dati o servizi esterni.

### 21.5 Figure e tabelle

Le figure sono salvate in `report/figures/` come **file HTML autonomi
interattivi**, apribili in qualsiasi browser anche senza connessione. Da
ciascun grafico della dashboard è inoltre possibile scaricare un'immagine PNG
tramite il pulsante «fotocamera» della barra Plotly.

Le tabelle numeriche dei risultati sono in `report/results/`:

| File | Contenuto |
|---|---|
| `confronto_metodi.csv` | Tutte le combinazioni prodotto × metodo con le 5 metriche |
| `sintesi_prodotti.csv` | Metodo migliore per prodotto con le relative metriche |
| `piano_scorte_baseline.csv` | Piano di scorta dei quattro prodotti |
| `confronto_scenari.csv` | Confronto A/B su Ferrero Rocher |
| `risultati.md` | Sintesi di tutti i risultati in formato Markdown |

---

## 22. Riferimenti

### 22.1 Fonti sull'impresa e sui prodotti

Tutte le informazioni istituzionali provengono da materiale **pubblico**.
Nessuna informazione riservata è stata utilizzata. Da queste fonti sono state
tratte **unicamente** informazioni qualitative descrittive: **nessun dato
numerico** di domanda, vendita, produzione o scorta.

| # | Fonte |
|---|---|
| A1 | Ferrero — Sito istituzionale del Gruppo, <https://www.ferrero.com> |
| A2 | Ferrero — *Rapporto di Sostenibilità* (pubblicazione annuale), <https://www.ferrerosustainability.com> |
| A3 | Ferrero Italia — <https://www.ferrero.it> |
| A4 | Nutella — Sito ufficiale di prodotto, <https://www.nutella.com> |
| A5 | Kinder — Sito ufficiale di marca, <https://www.kinder.com> |
| A6 | Ferrero Rocher — Sito ufficiale di prodotto, <https://www.ferrerorocher.com> |

### 22.2 Fonti teoriche e accademiche

**Previsione della domanda**

| # | Riferimento |
|---|---|
| T1 | Hyndman, R.J., Athanasopoulos, G. (2021). *Forecasting: Principles and Practice*, 3ª ed. OTexts, Melbourne. <https://otexts.com/fpp3/> |
| T2 | Hyndman, R.J., Koehler, A.B. (2006). "Another look at measures of forecast accuracy". *International Journal of Forecasting*, 22(4), 679-688. |
| T3 | Makridakis, S., Wheelwright, S.C., Hyndman, R.J. (1998). *Forecasting: Methods and Applications*, 3ª ed. John Wiley & Sons. |
| T4 | Winters, P.R. (1960). "Forecasting Sales by Exponentially Weighted Moving Averages". *Management Science*, 6(3), 324-342. |
| T5 | Holt, C.C. (2004). "Forecasting seasonals and trends by exponentially weighted moving averages". *International Journal of Forecasting*, 20(1), 5-10. |

**Gestione delle scorte e Operations Management**

| # | Riferimento |
|---|---|
| T6 | Silver, E.A., Pyke, D.F., Thomas, D.J. (2016). *Inventory and Production Management in Supply Chains*, 4ª ed. CRC Press. |
| T7 | Chopra, S., Meindl, P. (2016). *Supply Chain Management: Strategy, Planning, and Operation*, 6ª ed. Pearson. |
| T8 | Nahmias, S., Olsen, T.L. (2015). *Production and Operations Analysis*, 7ª ed. Waveland Press. |
| T9 | Slack, N., Brandon-Jones, A., Johnston, R. (2016). *Operations Management*, 8ª ed. Pearson. |
| T10 | Harris, F.W. (1913). "How Many Parts to Make at Once". *Factory, The Magazine of Management*, 10(2), 135-136. |
| T11 | Little, J.D.C. (1961). "A Proof for the Queuing Formula: L = λW". *Operations Research*, 9(3), 383-387. |

**Dinamiche di filiera**

| # | Riferimento |
|---|---|
| T12 | Lee, H.L., Padmanabhan, V., Whang, S. (1997). "Information Distortion in a Supply Chain: The Bullwhip Effect". *Management Science*, 43(4), 546-558. |
| T13 | Forrester, J.W. (1958). "Industrial Dynamics: A Major Breakthrough for Decision Makers". *Harvard Business Review*, 36(4), 37-66. |

### 22.3 Fonti software e tecniche

| # | Software | Versione | Documentazione |
|---|---|---|---|
| S1 | Python | 3.12 | <https://docs.python.org/3.12/> |
| S2 | Streamlit | 1.65.0 | <https://docs.streamlit.io/> |
| S3 | pandas | 2.2.3 | <https://pandas.pydata.org/docs/> |
| S4 | NumPy | 2.1.3 | <https://numpy.org/doc/stable/> |
| S5 | Plotly | 5.24.1 | <https://plotly.com/python/> |
| S6 | SciPy | 1.14.1 | <https://docs.scipy.org/doc/scipy/> |
| S7 | pytest | 8.3.4 | <https://docs.pytest.org/> |
| S8 | PyArrow | 18.1.0 | <https://arrow.apache.org/docs/python/> |

**Documentazione tecnica consultata**

| # | Riferimento |
|---|---|
| S9 | Streamlit — *App testing*: <https://docs.streamlit.io/develop/concepts/app-testing> |
| S10 | Streamlit — *Caching*: <https://docs.streamlit.io/develop/concepts/architecture/caching> |
| S11 | NumPy — *Random sampling*: <https://numpy.org/doc/stable/reference/random/> |
| S12 | SciPy — `scipy.stats.norm`: <https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html> |
| S13 | pandas — *Time series*: <https://pandas.pydata.org/docs/user_guide/timeseries.html> |

### 22.4 Specifica di riferimento

| # | Riferimento |
|---|---|
| P1 | Specifica ufficiale del **Project Work 24** — «Sviluppo di una mini-dashboard Python per la previsione della domanda e la pianificazione delle scorte di un'impresa», Corso di Studi in Informatica per le Aziende Digitali (L-31). SSD: INF/01, ING-INF/05, ING-IND/35. |

La mappatura puntuale fra ciascun requisito della specifica e la sua
implementazione è riportata in `docs/pw24_compliance.md`.
