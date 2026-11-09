# 2. Origine, natura e generazione del dataset

> **Dichiarazione di natura dei dati.** Il dataset utilizzato in questo
> progetto è **interamente sintetico**. È stato generato da un algoritmo
> scritto appositamente (`src/data_generator.py`) a partire da parametri
> scelti dallo studente. **Nessun valore proviene da Ferrero**, nessun valore
> è stato stimato a partire da dati aziendali riservati e **nessun valore
> rappresenta vendite reali**. I nomi dei prodotti e dell'impresa sono reali;
> le quantità no.

---

## 2.1 Perché dati sintetici

La specifica del Project Work 24 ammette esplicitamente l'uso di dati
«reali, stimati o generati». La scelta di dati **generati** è motivata da tre
ragioni:

1. **Impossibilità di accesso a dati reali.** I volumi di vendita per
   referenza di un'impresa privata non sono pubblici. Qualunque "dato reale"
   presentato come tale sarebbe in realtà inventato, con un problema di
   onestà intellettuale.
2. **Controllo sui comportamenti di domanda.** La specifica richiede quattro
   serie con comportamenti **diversi fra loro**. Generando i dati è possibile
   garantire per costruzione — e verificare con test automatici — che le
   differenze richieste siano effettivamente presenti e visibili nei grafici.
3. **Riproducibilità.** Con un seed fissato, chiunque cloni il repository
   ottiene esattamente lo stesso dataset e quindi esattamente gli stessi
   risultati riportati nella relazione.

Il costo di questa scelta è dichiarato fra i limiti del modello: i risultati
numerici hanno valore **metodologico**, non predittivo sul mercato reale.

---

## 2.2 Il modello generatore

Il generatore combina matematicamente le quattro componenti classiche
dell'analisi delle serie storiche, più una componente promozionale opzionale.

Per il mese `t = 0, 1, …, 47` e il corrispondente mese solare `m ∈ {1,…,12}`:

### Componente 1 — Livello con trend

```
L(t) = base_demand × (1 + trend_rate × t)
```

Il trend è **lineare** (additivo sul livello base). Un `trend_rate` di 0,005
corrisponde a +0,5% del livello base per mese, cioè circa +6% all'anno.

### Componente 2 — Fattore stagionale

```
S(m) = 1 + A × cos( 2π (m − peak_month) / 12 ) + F(m)
```

- `A` è l'ampiezza della sinusoide (0,10 = oscillazione del ±10%);
- `peak_month` è il mese in cui la sinusoide raggiunge il massimo; il minimo
  cade automaticamente sei mesi dopo;
- `F(m)` è il **profilo festivo**, una sovra-domanda puntuale definita per
  mesi specifici.

La scelta del **coseno** anziché del seno è deliberata: `cos` vale 1 quando
l'argomento è nullo, quindi il massimo cade *esattamente* nel mese indicato
da `peak_month`, rendendo il parametro immediatamente interpretabile.

Il profilo festivo esiste perché una sinusoide pura **non** è in grado di
riprodurre il picco natalizio di Ferrero Rocher: una sinusoide è simmetrica,
mentre la domanda di pralineria regalo presenta un picco stretto e asimmetrico
concentrato su due o tre mesi. Per Ferrero Rocher si è adottato:

| Mese | Sovra-domanda `F(m)` |
|---|---|
| Ottobre | +45% |
| Novembre | +105% |
| Dicembre | +75% |

Il massimo cade a **novembre** e non a dicembre perché la grandezza modellata
è la domanda rivolta all'impresa (ordini della distribuzione), che **anticipa**
il consumo finale: il prodotto deve essere a scaffale prima delle festività.

### Componente 3 — Rumore casuale

```
ε(t) ~ N(0, noise_std)        →        fattore moltiplicativo (1 + ε(t))
```

Il rumore è **moltiplicativo** e `noise_std` è espresso come **coefficiente
di variazione**. Questa scelta ha due conseguenze desiderabili:

- la dispersione assoluta cresce proporzionalmente al livello della serie,
  come si osserva nella realtà (un prodotto da 12.000 unità/mese ha
  oscillazioni assolute maggiori di uno da 3.000);
- il parametro è confrontabile fra prodotti di volume diverso: `noise_std =
  0,05` significa "5% di variabilità" indipendentemente dalla scala.

### Componente 4 — Picchi promozionali

```
con probabilità p:    P(t) = L(t) × promotion_amplitude × U(0,6 ; 1,4)
altrimenti:           P(t) = 0
```

La componente è **episodica** (si verifica solo in alcuni mesi, estratti
casualmente) e di **entità variabile** (il fattore uniforme `U(0,6; 1,4)`
evita che tutte le promozioni abbiano esattamente la stessa intensità).

### Formula complessiva

```
D(t) = round( max( 1 ;  L(t) × S(m) × (1 + ε(t))  +  P(t) ) )
```

Il troncamento a 1 e l'arrotondamento garantiscono i vincoli di dominio
richiesti dalla specifica: **quantità intere e strettamente positive**.

---

## 2.3 Parametri adottati per i quattro prodotti

I parametri sono definiti in `src/config.py` (classe `ProductParameters`) ed
esportati in `data/product_parameters.csv`.

| Parametro | Nutella | Kinder Cioccolato | Ferrero Rocher | Kinder Happy Hippo |
|---|---|---|---|---|
| `base_demand` | 12.000 | 8.000 | 5.000 | 3.000 |
| `trend_rate` (mese) | 0,0010 | 0,0050 | 0,0030 | 0,0060 |
| `trend_rate` (anno ≈) | +1,2% | +6,0% | +3,6% | +7,2% |
| `seasonal_amplitude` | 0,05 | 0,12 | 0,18 | 0,12 |
| `seasonal_peak_month` | 11 | 12 | 12 | 12 |
| `festive_profile` | — | — | 10:+0,45 / 11:+1,05 / 12:+0,75 | — |
| `noise_std` | 0,05 | 0,08 | 0,10 | **0,18** |
| `promotion_probability` | 0,00 | 0,06 | 0,00 | **0,20** |
| `promotion_amplitude` | 0,00 | 0,12 | 0,00 | **0,45** |

Unità di misura: **cartoni/mese**. La scelta del cartone come unità (anziché
il pezzo) riflette il fatto che la pianificazione logistica verso la grande
distribuzione avviene su unità di carico, non su unità di vendita.

### Logica delle scelte parametriche

- **Nutella** ha i parametri di variabilità più bassi di tutti (rumore 5%,
  nessuna promozione, stagionalità 5%) perché deve risultare la serie più
  regolare, come richiesto dalla specifica.
- **Kinder Happy Hippo** ha rumore 18% e promozioni frequenti (20% dei mesi,
  +45% di ampiezza): è per costruzione la serie più "difficile" da prevedere.
- **Ferrero Rocher** ha un rumore moderato (10%) ma la stagionalità più
  marcata, grazie alla combinazione di sinusoide ampia e profilo festivo.
- **Kinder Cioccolato** occupa una posizione intermedia su tutte le
  dimensioni, con il trend più visibile dopo Happy Hippo.

---

## 2.4 Riproducibilità

### Seed e flussi casuali indipendenti

Il seed globale del progetto è **24** (`RANDOM_SEED` in `src/config.py`,
scelto per richiamare il numero del Project Work).

Ogni prodotto non usa direttamente il seed globale, ma un **flusso casuale
derivato** tramite `numpy.random.SeedSequence(seed).spawn(16)[indice]`:

```python
rng = np.random.default_rng(np.random.SeedSequence(seed).spawn(16)[product_index])
```

Questa scelta garantisce una proprietà importante per la simulazione degli
scenari: **modificare i parametri di un prodotto non altera le realizzazioni
casuali degli altri**. Senza di essa, spostare un cursore della dashboard
avrebbe cambiato anche le serie dei prodotti non selezionati, rendendo i
confronti non interpretabili.

La proprietà è verificata dal test
`test_flussi_casuali_indipendenti_fra_prodotti`.

### Proprietà di identità

Con tutti i moltiplicatori di scenario pari a 1,0 la serie rigenerata
**coincide esattamente** con il dataset storico di base. È questa proprietà
che consente di interpretare qualunque differenza osservata come effetto
esclusivo della leva modificata. È verificata dai test
`test_scaled_con_moltiplicatori_unitari_non_modifica_nulla` e
`test_leve_neutre_riproducono_il_dataset_di_base`.

### Rigenerazione

```bash
python -m src.data_generator
```

Il comando ricostruisce i tre file CSV e stampa le statistiche descrittive di
controllo. Lo stesso risultato è ottenibile dal pulsante
«🔄 Rigenera dataset sintetico» nelle opzioni avanzate della dashboard.

---

## 2.5 Struttura dei file prodotti

### `data/demand_history.csv` — formato lungo (principale)

192 righe (4 prodotti × 48 mesi) con tre colonne:

| Colonna | Tipo | Descrizione |
|---|---|---|
| `date` | data `AAAA-MM-GG` | Primo giorno del mese di riferimento |
| `product` | testo | Nome del prodotto |
| `demand` | intero | Domanda mensile in cartoni |

```csv
date,product,demand
2022-01-01,Ferrero Rocher,4833
2022-02-01,Ferrero Rocher,6672
...
```

### `data/demand_history_wide.csv` — formato pivot

48 righe, una colonna per prodotto. Più comodo per l'ispezione visiva in un
foglio di calcolo e per il confronto diretto fra serie.

### `data/product_parameters.csv` — parametri di generazione

Una riga per prodotto con tutti i parametri del processo generatore. Serve a
rendere il dataset **auto-documentato**: chiunque può ricostruire la logica di
generazione senza leggere il codice.

---

## 2.6 Caratteristiche delle serie generate

Statistiche calcolate sul dataset effettivamente prodotto con seed 24
(output di `python -m src.data_generator`):

| Prodotto | Oss. | Media | Dev. std | Minimo | Massimo | **CV (%)** |
|---|---|---|---|---|---|---|
| Nutella | 48 | 12.242 | 823 | 10.643 | 14.427 | **6,7** |
| Kinder Cioccolato | 48 | 9.019 | 1.268 | 6.769 | 12.195 | **14,1** |
| Ferrero Rocher | 48 | 6.260 | 2.497 | 3.497 | 12.809 | **39,9** |
| Kinder Happy Hippo | 48 | 3.814 | 1.020 | 1.849 | 6.217 | **26,8** |

Il **coefficiente di variazione** (CV = deviazione standard / media) è
l'indicatore sintetico della "difficoltà previsionale" di una serie. L'ordine
ottenuto — Nutella 6,7% < Kinder Cioccolato 14,1% < Happy Hippo 26,8% <
Ferrero Rocher 39,9% — conferma la differenziazione richiesta.

Si noti che Ferrero Rocher ha il CV più alto pur avendo un rumore casuale
moderato (10%): la sua variabilità è in larga parte **sistematica**
(stagionale) e quindi **prevedibile**. È esattamente questa la distinzione
che la valutazione previsionale metterà in luce: il naive stagionale ottiene
su Rocher un MAPE del 9,9%, molto migliore del 24,6% ottenuto su Happy Hippo,
la cui variabilità è invece in gran parte **casuale** e quindi irriducibile.

### Profilo stagionale (indice mensile, media annua = 100)

| Mese | Nutella | Kinder Cioccolato | Ferrero Rocher | Kinder Happy Hippo |
|---|---|---|---|---|
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

La lettura conferma i comportamenti progettati:

- **Nutella** oscilla fra 93 e 108: stagionalità praticamente irrilevante ai
  fini della pianificazione.
- **Kinder Cioccolato** mostra il tipico **avvallamento estivo** (88 a maggio
  e giugno) e il massimo a dicembre (117).
- **Ferrero Rocher** presenta un'escursione di 118 punti, con il picco a
  novembre (187) quasi triplo rispetto al minimo di giugno (69). È il profilo
  che giustifica l'esistenza della scorta anticipata.
- **Kinder Happy Hippo** ha una stagionalità moderata (57 punti) resa
  irregolare dai picchi promozionali (si noti l'anomalia di luglio, 106,
  dovuta a promozioni casuali e non a stagionalità).

---

## 2.7 Validazione del dataset

Il modulo `src/data_validation.py` sottopone qualunque dataset caricato a otto
controlli prima che venga utilizzato. Tutti i messaggi di errore sono in
italiano e formulati per l'utente finale, senza esporre traceback Python.

| # | Controllo | Severità | Messaggio di esempio |
|---|---|---|---|
| 1 | Colonne obbligatorie presenti | Bloccante | «Colonne obbligatorie mancanti nel dataset: demand.» |
| 2 | Formato delle date valido | Bloccante | «Rilevate 3 date in formato non valido: è atteso il formato 'AAAA-MM-GG'.» |
| 3 | Valori di domanda numerici | Bloccante | «Rilevati 2 valori di domanda non numerici.» |
| 4 | Assenza di valori mancanti | Bloccante | «Sono presenti 5 valori mancanti nella colonna 'demand'.» |
| 5 | Assenza di date duplicate | Bloccante | «Rilevate 2 righe con data duplicata per lo stesso prodotto.» |
| 6 | Domanda non negativa | Bloccante | «Rilevati 1 valori di domanda negativi.» |
| 7 | Prodotti in anagrafica | Bloccante | «Prodotti non previsti in anagrafica: Cioccolato Fittizio.» |
| 8 | Osservazioni sufficienti (≥ 24) | Bloccante | «Il prodotto 'Nutella' ha solo 10 osservazioni: ne servono almeno 24.» |
| 9 | Continuità mensile | Bloccante | «La serie del prodotto 'Nutella' non è continua su base mensile: mancano 1 mesi (es.: 2023-09).» |
| 10 | Domanda nulla | **Segnalazione** | «Rilevati 2 mesi con domanda pari a zero: il MAPE verrà calcolato escludendo tali osservazioni.» |
| 11 | Prodotto assente | **Segnalazione** | «Prodotti dell'anagrafica assenti dal dataset: Nutella.» |

La distinzione fra **errori bloccanti** e **segnalazioni** è deliberata: una
domanda pari a zero è un dato legittimo (rottura di stock, prodotto non
distribuito in quel mese), ma ha conseguenze sul calcolo del MAPE che
l'utente deve conoscere. Impedire l'analisi sarebbe sbagliato; tacere il
problema anche.

Sono inoltre gestite le condizioni di errore sul file:

- file inesistente → messaggio con il suggerimento di rigenerare il dataset;
- file vuoto → messaggio dedicato;
- CSV malformato (struttura incoerente) → messaggio che invita a verificare
  separatore e struttura;
- errore di lettura del sistema operativo → messaggio con la causa.

Tutti i controlli sono coperti da test automatici in
`tests/test_data_validation.py` (21 test).
