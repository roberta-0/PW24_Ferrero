# 1. L'impresa selezionata: Ferrero

> **Avvertenza di integrità accademica.** Questo capitolo descrive Ferrero
> utilizzando esclusivamente **informazioni pubbliche** (sito istituzionale,
> rapporti di sostenibilità pubblicati dall'azienda, stampa economica). Tutti
> i **dati numerici di domanda** impiegati nel progetto sono invece
> **sintetici**, generati algoritmicamente a scopo didattico: non provengono
> da Ferrero, non sono stati forniti da Ferrero e **non rappresentano
> vendite, scorte o informazioni riservate** dell'azienda.

---

## 1.1 Perché Ferrero

La scelta di Ferrero come impresa di riferimento per il Project Work 24
risponde a tre criteri:

1. **Rilevanza del problema di pianificazione.** Ferrero opera nel settore
   dolciario, caratterizzato da una domanda fortemente influenzata dalla
   stagionalità (festività, temperature), da una *shelf life* limitata e da
   una filiera distributiva che richiede disponibilità continua presso la
   grande distribuzione organizzata. Sono esattamente le condizioni in cui
   un errore di previsione si traduce immediatamente in costi.

2. **Portafoglio prodotti eterogeneo.** L'azienda commercializza prodotti con
   comportamenti di domanda strutturalmente diversi: dalla crema spalmabile a
   consumo quotidiano alla pralineria da regalo concentrata nel periodo
   natalizio. Questa eterogeneità consente di costruire le quattro serie
   storiche con profili differenziati richieste dalla specifica.

3. **Disponibilità di informazione pubblica.** Esiste una documentazione
   istituzionale ampia e verificabile sul perimetro industriale e sul
   posizionamento del Gruppo, sufficiente a inquadrare il contesto senza
   ricorrere a informazioni riservate.

## 1.2 Profilo dell'impresa

Ferrero è un gruppo industriale italiano fondato ad **Alba (Cuneo)** nel
**1946** da Pietro Ferrero. È oggi uno dei principali gruppi mondiali nel
settore dolciario, con una struttura proprietaria di tipo **familiare** e una
presenza produttiva e commerciale su scala internazionale.

| Dimensione | Informazione pubblica |
|---|---|
| Settore | Industria alimentare dolciaria (confectionery) |
| Fondazione | 1946, Alba (CN), Italia |
| Natura | Gruppo privato a controllo familiare |
| Presenza | Stabilimenti produttivi e filiali commerciali in numerosi Paesi |
| Marchi principali | Nutella, Kinder, Ferrero Rocher, Tic Tac, Mon Chéri, Pocket Coffee |
| Canali | Grande distribuzione organizzata, distribuzione tradizionale, travel retail |

Il Gruppo pubblica annualmente un *Rapporto di Sostenibilità* che espone
informazioni su perimetro industriale, approvvigionamento delle materie prime
e politiche ambientali; tale documento è la fonte pubblica di riferimento per
le informazioni istituzionali citate in questo progetto (cfr.
[`references.md`](references.md)).

## 1.3 Contesto produttivo

Il modello produttivo del settore dolciario presenta alcune caratteristiche
strutturali che incidono direttamente sulla pianificazione delle scorte. Le
seguenti considerazioni sono **di natura settoriale generale** e non
descrivono procedure specifiche di Ferrero.

### Materie prime critiche

La produzione dipende da materie prime agricole soggette a stagionalità di
raccolto e a volatilità di prezzo: **nocciole**, **cacao**, **zucchero**,
**latte in polvere**, **olio vegetale**. La disponibilità di queste materie
non è uniforme nell'anno e il loro approvvigionamento avviene tipicamente con
contratti pluriennali e scorte di materia prima significative.

**Implicazione per il progetto.** Il lead time di approvvigionamento non è
trascurabile e può variare sensibilmente: è questa la ragione per cui la
dashboard consente di esplorare lead time da 0,5 a 8 mesi.

### Vincoli di processo

- **Shelf life limitata.** Il prodotto finito ha una vita commerciale
  definita; accumulare scorta eccessiva genera **rischio di obsolescenza** e
  non solo costo finanziario di immobilizzo.
- **Catena del freddo e temperatura.** Il cioccolato è sensibile al calore:
  nei mesi estivi la distribuzione richiede condizioni controllate e alcuni
  prodotti registrano fisiologicamente consumi inferiori. Questo spiega il
  profilo stagionale con minimo estivo adottato per i prodotti a base di
  cioccolato nel dataset sintetico.
- **Capacità produttiva rigida nel breve periodo.** Le linee di produzione
  non si riconfigurano istantaneamente: per servire un picco stagionale
  occorre o produrre in anticipo (generando **scorta anticipata**) oppure
  disporre di flessibilità di capacità (turni aggiuntivi, personale
  stagionale), con costi associati.

### Livellamento della produzione

La combinazione fra capacità rigida e domanda stagionale genera il classico
problema di *production smoothing*: conviene produrre a ritmo costante e
accumulare magazzino, oppure inseguire la domanda con capacità flessibile?
Il progetto modella la prima strategia (produzione livellata) tramite la
**scorta anticipata**, documentata in [`inventory.md`](inventory.md).

## 1.4 Contesto commerciale

### Canali di vendita

Il canale prevalente per i beni di largo consumo confezionati è la **grande
distribuzione organizzata (GDO)**. Questo comporta alcune conseguenze
rilevanti per la pianificazione:

- **Livelli di servizio contrattualizzati.** Gli accordi di fornitura con le
  insegne prevedono tipicamente obiettivi di disponibilità elevati; il
  mancato rispetto può comportare penali e, soprattutto, la perdita di spazio
  a scaffale a favore dei concorrenti. È questo il motivo per cui la
  dashboard propone livelli di servizio dal 90% al 99%, con il 95% come
  valore predefinito.
- **Effetto delle promozioni.** Le attività promozionali concordate con la
  distribuzione generano picchi di domanda di entità rilevante e di
  collocazione temporale non perfettamente regolare. Il generatore di dati
  riproduce questo fenomeno tramite una componente promozionale episodica,
  particolarmente marcata per Kinder Happy Hippo.
- **Effetto frusta (*bullwhip effect*).** Gli ordini della distribuzione sono
  più variabili dei consumi finali, perché incorporano le politiche di
  riordino dei clienti. Il progetto non modella esplicitamente questo
  fenomeno, ma la variabilità complessiva delle serie sintetiche ne tiene
  implicitamente conto.

### Stagionalità commerciale

Il calendario commerciale del settore dolciario è dominato da alcune
ricorrenze:

| Periodo | Effetto sulla domanda |
|---|---|
| Ottobre - dicembre | Picco principale: confezioni regalo, consumo natalizio |
| Febbraio | San Valentino (pralineria) |
| Marzo - aprile | Pasqua (uova e prodotti dedicati) |
| Giugno - agosto | Flessione per i prodotti a base di cioccolato |

Il picco natalizio è il più rilevante dal punto di vista della
pianificazione: la **produzione e la spedizione anticipano il consumo**,
concentrandosi fra ottobre e novembre perché il prodotto deve essere a
scaffale prima delle festività. Nel dataset sintetico questo fenomeno è
riprodotto per Ferrero Rocher con un profilo festivo che assegna il massimo a
novembre.

## 1.5 Contesto logistico

La filiera logistica di un produttore dolciario di scala internazionale si
articola tipicamente su più livelli:

```
Fornitori materie prime
        │
        ▼
Stabilimenti produttivi  ──────►  Magazzini centrali
                                        │
                                        ▼
                                 Piattaforme / depositi regionali
                                        │
                                        ▼
                                 Centri distributivi GDO
                                        │
                                        ▼
                                  Punti vendita
```

Ai fini del progetto rilevano tre grandezze logistiche:

1. **Lead time di approvvigionamento (`L`).** Tempo che intercorre fra
   l'emissione di un ordine di rifornimento e la disponibilità della merce
   nel punto di stoccaggio considerato. Comprende tempo di produzione,
   controllo qualità, trasporto e messa a disposizione. Nella simulazione è
   espresso in **mesi** ed è la leva che determina la **scorta pipeline**.

2. **Periodo di riesame / riordino (`R`).** Intervallo fra due decisioni di
   rifornimento successive. Determina l'ampiezza del lotto e quindi la
   **scorta ciclica**.

3. **Variabilità del lead time.** Nella realtà il tempo di
   approvvigionamento è esso stesso aleatorio. Il modello implementato
   assume per semplicità un **lead time deterministico**: l'ipotesi è
   dichiarata esplicitamente ed è discussa fra i limiti del modello in
   [`methodology.md`](methodology.md).

### Perché il lead time è la leva più critica

Nel modello adottato la scorta pipeline cresce **linearmente** con il lead
time (`D × L`), mentre la scorta di sicurezza cresce con la **radice
quadrata** dell'intervallo di protezione (`z × σ × √L`). Ne consegue che
allungare l'approvvigionamento penalizza soprattutto il capitale immobilizzato
in transito: è una delle conclusioni gestionali quantificate dalla dashboard
nella sezione di confronto fra scenari.

---

## 1.6 I quattro prodotti analizzati

I quattro prodotti selezionati sono **prodotti reali** del Gruppo Ferrero. La
descrizione che segue riporta informazioni pubblicamente note; le
**caratteristiche di domanda** indicate nell'ultima colonna sono invece
**ipotesi di modellazione** adottate per generare le serie sintetiche.

### Nutella

- **Categoria**: crema spalmabile alla nocciola e cacao.
- **Informazione pubblica**: è il prodotto più noto del Gruppo, lanciato nel
  1964, a diffusione internazionale.
- **Profilo di consumo ipotizzato**: prodotto a consumo **quotidiano e
  abitudinario**, con acquisto ricorrente e scarsa dipendenza da ricorrenze
  specifiche.
- **Comportamento di domanda modellato**: domanda **stabile**, variabilità
  casuale **bassa**, trend **molto limitato**, stagionalità **debole**.

### Kinder Cioccolato

- **Categoria**: snack di cioccolato al latte con ripieno al latte,
  appartenente alla linea Kinder.
- **Informazione pubblica**: prodotto storico della linea Kinder, rivolto
  principalmente al consumo familiare e infantile.
- **Profilo di consumo ipotizzato**: consumo regolare con flessione estiva
  tipica dei prodotti a base di cioccolato.
- **Comportamento di domanda modellato**: domanda **moderatamente stabile**,
  trend positivo **moderato**, variabilità **moderata**, stagionalità
  **debole/moderata** con minimo estivo.

### Ferrero Rocher

- **Categoria**: pralina di cioccolato con nocciola intera, wafer e granella;
  venduta prevalentemente in confezioni regalo.
- **Informazione pubblica**: prodotto di pralineria premium, fortemente
  associato all'uso come **dono** e alle ricorrenze.
- **Profilo di consumo ipotizzato**: domanda concentrata nel periodo
  autunnale/natalizio, con ordini della distribuzione anticipati rispetto al
  consumo finale.
- **Comportamento di domanda modellato**: stagionalità **forte** con picchi
  rilevanti fra ottobre e dicembre, variabilità **moderata**, trend di lungo
  periodo **moderato**.

### Kinder Happy Hippo

- **Categoria**: snack a base di wafer con ripieno, in forma di ippopotamo.
- **Informazione pubblica**: prodotto della linea Kinder rivolto al target
  infantile.
- **Profilo di consumo ipotizzato**: prodotto di **impulso**, più esposto
  all'attività promozionale e alle iniziative di marketing, con volumi
  assoluti inferiori agli altri tre.
- **Comportamento di domanda modellato**: domanda **più variabile**, trend
  positivo **moderato**, **picchi promozionali** casuali, stagionalità
  **moderata**, rumore **superiore** a Nutella e Kinder Cioccolato.

### Sintesi dei quattro profili

| Prodotto | Volume relativo | Variabilità | Trend | Stagionalità | Promozioni |
|---|---|---|---|---|---|
| Nutella | Alto | Bassa | Molto limitato | Debole | Assenti |
| Kinder Cioccolato | Medio-alto | Moderata | Moderato | Debole/moderata | Rare |
| Ferrero Rocher | Medio | Moderata | Moderato | **Forte (Natale)** | Assenti |
| Kinder Happy Hippo | Basso | **Alta** | Moderato | Moderata | **Frequenti** |

La differenziazione è verificata quantitativamente sui dati generati in
[`dataset.md`](dataset.md) ed è oggetto di test automatici
(`tests/test_data_generator.py`).

---

## 1.7 Il problema di pianificazione nel caso di studio

Sintetizzando quanto esposto, l'impresa simulata deve rispondere a quattro
domande operative:

1. **Quanta domanda attendersi** nei prossimi mesi, per ciascun prodotto?
2. **Quale metodo previsionale** è più affidabile per ciascun profilo di
   domanda?
3. **Quanta scorta tenere**, scomposta nelle sue componenti funzionali?
4. **Come cambia la risposta** al variare delle condizioni di contesto
   (variabilità, trend, stagionalità, lead time, livello di servizio)?

Il resto della documentazione risponde a queste domande:
[`dataset.md`](dataset.md) descrive la costruzione dei dati,
[`forecasting.md`](forecasting.md) i metodi previsionali,
[`inventory.md`](inventory.md) i modelli di scorta,
[`scenarios.md`](scenarios.md) la simulazione degli scenari.
