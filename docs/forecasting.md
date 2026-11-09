# 3. Metodi previsionali e valutazione dell'accuratezza

Questo capitolo descrive i cinque metodi previsionali implementati, le
metriche di accuratezza, la procedura di valutazione out-of-sample e il
criterio di selezione automatica del modello.

Codice di riferimento: `src/forecasting.py`, `src/metrics.py`,
`src/evaluation.py`.

---

## 3.1 Il problema previsionale

Data una serie storica di domanda mensile `y(1), …, y(T)`, si vuole stimare
la domanda futura `y(T+1), …, y(T+h)` per un orizzonte `h` di 3, 6 o 12 mesi.

La difficoltà non sta nel produrre *una* previsione — qualunque formula ne
produce una — ma nel capire **quanto ci si può fidare** di quella previsione
e **quale metodo scegliere** fra i molti disponibili. È questa la ragione per
cui il progetto dedica più spazio alla valutazione che alla previsione in sé.

---

## 3.2 I metodi implementati

Sono implementati **cinque** metodi, tutti scritti da zero con NumPy per
rendere esplicita la formulazione matematica. La specifica ne richiede almeno
due (e raccomanda tre); i cinque implementati coprono l'intero spettro dei
comportamenti presenti nel dataset.

| Metodo | Coglie il livello | Coglie il trend | Coglie la stagionalità |
|---|:---:|:---:|:---:|
| Media mobile semplice | ✔ | ✘ | ✘ |
| Smorzamento esponenziale semplice | ✔ | ✘ | ✘ |
| Regressione lineare sul tempo | ✔ | ✔ | ✘ |
| Naive stagionale | ✔ | ✘ | ✔ |
| Holt-Winters additivo | ✔ | ✔ | ✔ |

La tabella spiega in anticipo il risultato dell'analisi: nessun metodo domina
gli altri in assoluto, perché ciascuno ipotizza una struttura diversa dei
dati. Il metodo migliore dipende dal prodotto.

---

### A) Media mobile semplice (*Simple Moving Average*)

**Formulazione.** La previsione per tutti i periodi futuri è la media delle
ultime `w` osservazioni:

```
F(T+h) = (1/w) · Σ y(i)        per i = T−w+1 … T,   per ogni h ≥ 1
```

**Previsione in-sample** (usata per i residui), a un passo e senza uso di
informazione futura:

```
F̂(t) = (1/w) · Σ y(i)        per i = t−w … t−1
```

**Parametro configurabile**: ampiezza della finestra `w` ∈ {3, 6, 12} mesi.

**Interpretazione.** Il metodo assume che la serie sia **stazionaria** attorno
a un livello costante e che le oscillazioni siano puro rumore da mediare. La
previsione è **piatta**: una linea orizzontale.

**Effetto della finestra.** Finestre strette (3 mesi) rendono il metodo
reattivo ma rumoroso; finestre ampie (12 mesi) producono previsioni molto
lisce ma lente a reagire ai cambiamenti. Su una serie stagionale, una
finestra di 12 mesi ha l'effetto collaterale di **destagionalizzare**
completamente la previsione, riportandola alla media annua.

**Limite strutturale.** Essendo piatta, la previsione è sistematicamente in
ritardo su una serie con trend e completamente cieca alla stagionalità. Sul
prodotto Ferrero Rocher questo si traduce in un MAPE dell'80,9%, di gran
lunga il peggiore osservato.

---

### B) Smorzamento esponenziale semplice (*Simple Exponential Smoothing*)

**Formulazione.** Ricorsione sul livello stimato:

```
L(t) = α · y(t) + (1 − α) · L(t−1)        con 0 < α ≤ 1
L(0) = y(0)
```

La previsione è piatta e pari all'ultimo livello:

```
F(T+h) = L(T)        per ogni h ≥ 1
```

**Parametro configurabile**: `α` ∈ (0, 1], regolabile in dashboard da 0,05 a
1,00 con passo 0,05; valore predefinito **0,30**.

**Interpretazione.** È una media ponderata di *tutte* le osservazioni passate,
con pesi che decrescono esponenzialmente verso il passato. Espandendo la
ricorsione:

```
L(T) = α·y(T) + α(1−α)·y(T−1) + α(1−α)²·y(T−2) + …
```

**Confronto con la media mobile.** Entrambi producono previsioni piatte, ma
lo smorzamento esponenziale usa tutta la storia con pesi decrescenti, mentre
la media mobile usa solo le ultime `w` osservazioni con peso uguale e scarta
bruscamente le precedenti. Nella pratica lo smorzamento tende a essere più
stabile, come confermato dai risultati: batte la media mobile su tutti e
quattro i prodotti.

**Casi limite.** Con `α = 1` il metodo degenera nel *naive* (la previsione è
l'ultima osservazione); con `α → 0` tende alla media di tutta la serie.

---

### C) Regressione lineare sul tempo

**Formulazione.** Si stima per minimi quadrati ordinari il modello:

```
y(t) = a + b·t + e(t)        con t = 0, 1, …, T−1
```

I coefficienti `a` (intercetta) e `b` (pendenza) minimizzano la somma dei
quadrati dei residui. La previsione estrapola la retta stimata:

```
F(T+h) = a + b·(T + h − 1)
```

**Troncamento.** Le previsioni sono vincolate a essere non negative: un trend
stimato fortemente decrescente, estrapolato su 12 mesi, potrebbe altrimenti
produrre domanda negativa, priva di significato.

**Interpretazione.** È l'unico metodo che modella esplicitamente una
**direzione di lungo periodo**. Funziona bene quando la crescita (o il calo)
è il fenomeno dominante e la stagionalità è secondaria.

**Limite.** Ignora completamente la stagionalità e assume che il trend sia
**lineare** e **persistente** anche nel futuro. Estrapolazioni su orizzonti
lunghi vanno trattate con cautela.

---

### D) Naive stagionale (*Seasonal Naive*)

**Formulazione.** La previsione per un dato mese è il valore osservato nello
stesso mese del ciclo precedente:

```
F(T+h) = y( T + h − m·⌈h/m⌉ )        con m = 12
```

In pratica: «la domanda del prossimo novembre sarà quella dello scorso
novembre».

**Interpretazione.** È un **benchmark**, non un modello sofisticato. Il suo
ruolo metodologico è fondamentale: se un modello complesso non batte il
naive stagionale, la sua complessità non è giustificata. È un principio
standard della letteratura previsionale.

**Punti di forza.** Cattura l'intero profilo stagionale — compresi picchi
asimmetrici che una sinusoide non riproduce — senza stimare alcun parametro.

**Punti di debolezza.** Non filtra il rumore: eredita integralmente gli shock
casuali dell'anno precedente. Non coglie il trend. Richiede almeno un ciclo
stagionale completo di storia.

**Risultato sorprendente.** Su Ferrero Rocher il naive stagionale è il metodo
**migliore in assoluto** (MAPE 9,9%), superando Holt-Winters (15,8%). La
ragione è che il picco natalizio del generatore è molto **regolare** e
**asimmetrico**: il naive lo riproduce esattamente, mentre Holt-Winters tende
a lisciarlo nel processo di aggiornamento esponenziale degli indici
stagionali. È un esempio didatticamente prezioso del fatto che il modello più
complesso non è necessariamente il migliore.

---

### E) Holt-Winters additivo (smorzamento esponenziale triplo)

**Formulazione.** Il metodo aggiorna simultaneamente tre componenti:

```
Livello:       L(t) = α·( y(t) − S(t−m) ) + (1−α)·( L(t−1) + B(t−1) )
Trend:         B(t) = β·( L(t) − L(t−1) ) + (1−β)·B(t−1)
Stagionalità:  S(t) = γ·( y(t) − L(t) )   + (1−γ)·S(t−m)
```

Previsione:

```
F(T+h) = L(T) + h·B(T) + S( T + h − m·⌈h/m⌉ )
```

**Inizializzazione** (deterministica, senza ottimizzazione numerica):

- livello iniziale = media del primo ciclo stagionale;
- trend iniziale = (media del secondo ciclo − media del primo ciclo) / m;
- indici stagionali iniziali = scarti del primo ciclo dalla propria media.

Servono quindi **almeno due cicli completi** (24 mesi) di storia.

**Parametri.** `α = 0,30`, `β = 0,10`, `γ = 0,20`. Sono valori di uso comune
in letteratura e **non sono ottimizzati numericamente**.

**Semplificazione dichiarata.** Un'implementazione professionale
ottimizzerebbe i tre parametri minimizzando l'errore in-sample. Si è scelto
di non farlo per tre ragioni: (i) manterrebbe il codice leggibile, (ii)
l'ottimizzazione in-sample rischia il sovra-adattamento, (iii) il confronto
fra metodi resta equo perché anche gli altri metodi usano parametri fissati.
La semplificazione è un **limite del modello**, non un errore, ed è
dichiarata come tale.

**Risultato.** Su Nutella — serie con trend minimo e stagionalità debole —
Holt-Winters è il metodo migliore (MAPE 4,95%), ma con un margine minimo
sullo smorzamento esponenziale (5,00%). Il margine è talmente ridotto da
rendere la scelta sostanzialmente indifferente dal punto di vista pratico: è
un'osservazione gestionalmente rilevante, discussa nella relazione.

---

## 3.3 Indicatori di accuratezza

Dati i valori osservati `y(i)` e previsti `f(i)` su `n` osservazioni di test.

### MAE — Mean Absolute Error

```
MAE = (1/n) · Σ | y(i) − f(i) |
```

**Unità di misura**: cartoni. **Interpretazione**: di quanti cartoni il
modello sbaglia in media, in valore assoluto.

**Pro**: immediatamente interpretabile in termini operativi. **Contro**: non
confrontabile fra prodotti di volume diverso (un errore di 650 cartoni è
modesto su Nutella, enorme su Happy Hippo).

### RMSE — Root Mean Squared Error

```
RMSE = √[ (1/n) · Σ ( y(i) − f(i) )² ]
```

**Unità di misura**: cartoni. **Interpretazione**: errore tipico, ma con
**penalizzazione più che proporzionale degli errori grandi**, perché gli
scarti sono elevati al quadrato prima di essere mediati.

**Proprietà matematica**: vale sempre `RMSE ≥ MAE` (disuguaglianza di
Jensen). Il rapporto `RMSE/MAE` è un indicatore della presenza di errori
occasionali di grande entità: più il rapporto è vicino a 1, più gli errori
sono omogenei.

**Ruolo nel progetto**: l'RMSE out-of-sample è usato come stima della
deviazione standard dell'errore previsionale `σ` nel dimensionamento della
scorta di sicurezza. La scelta è coerente: la scorta di sicurezza deve
proteggere soprattutto dagli errori grandi, ed è proprio quelli che l'RMSE
pesa di più.

### MAPE — Mean Absolute Percentage Error

```
MAPE = (100/n′) · Σ | y(i) − f(i) | / | y(i) |        solo per y(i) ≠ 0
```

**Unità di misura**: punti percentuali. **Interpretazione**: di quale
percentuale il modello sbaglia in media.

**Pro**: **adimensionale**, quindi confrontabile fra prodotti con volumi
molto diversi; immediatamente comprensibile in sede di discussione
manageriale.

**Contro e cautele**:

- **non è definito per `y(i) = 0`**;
- è **asimmetrico**: penalizza di più le sovrastime delle sottostime, perché
  il denominatore è il valore osservato;
- diventa instabile quando i valori osservati sono molto piccoli.

### Gestione dei valori nulli nel MAPE

Le osservazioni con domanda nulla sono **escluse** dal calcolo e il numero di
osservazioni effettive `n′` è ridotto di conseguenza. La scelta alternativa —
trattare lo zero come un valore piccolo — produrrebbe percentuali enormi e
arbitrarie.

Se **tutte** le osservazioni di test sono nulle il MAPE restituisce `NaN`; in
tal caso il criterio di selezione del modello **ripiega automaticamente
sull'RMSE** (cfr. §3.5). Sul dataset di progetto questo caso non si verifica
mai (la domanda è sempre strettamente positiva per costruzione), ma la
gestione è implementata e testata perché l'applicazione deve restare robusta
se l'utente carica un dataset diverso.

### Indicatori complementari

Oltre ai tre richiesti, il progetto calcola:

**Bias (errore medio con segno)**

```
Bias = (1/n) · Σ ( f(i) − y(i) )
```

Diagnostica di **sovra/sotto-stima sistematica**: un bias positivo indica che
il modello sovrastima costantemente. A differenza del MAE, non misura la
grandezza dell'errore ma la sua **direzione prevalente**. Un modello con MAE
basso ma bias elevato ha un problema strutturale.

**sMAPE (MAPE simmetrico)**

```
sMAPE = (100/n) · Σ 2·| y(i) − f(i) | / ( | y(i) | + | f(i) | )
```

Alternativa simmetrica al MAPE, definita anche in presenza di osservazioni
nulle. È riportata come controllo di robustezza.

---

## 3.4 Valutazione out-of-sample: lo split cronologico

### Il principio

Valutare un modello sugli stessi dati usati per stimarlo produce una misura
**ottimisticamente distorta**: il modello ha già "visto" quei dati. È il
problema del sovra-adattamento (*overfitting*).

La soluzione standard è dividere i dati in **addestramento** e **test**. Per
le serie storiche questa divisione deve rispettare una regola aggiuntiva e
vincolante: **non si può mescolare casualmente**. L'ordine temporale porta
informazione, e usare dati futuri per prevedere il passato sarebbe una fuga
di informazione (*data leakage*) che invaliderebbe l'intera valutazione.

### L'implementazione

```
┌──────────────── 48 mesi di storia ────────────────┐
│                                                   │
├────── addestramento: 36 mesi ──────┬── test: 12 ──┤
│      gen 2022 → dic 2024           │ gen → dic 25 │
└────────────────────────────────────┴──────────────┘
```

- **Addestramento**: 36 mesi (gennaio 2022 – dicembre 2024). Tre cicli
  stagionali completi, sufficienti anche per Holt-Winters (che ne richiede
  due).
- **Test**: 12 mesi (gennaio – dicembre 2025). Un ciclo stagionale completo,
  così che la valutazione comprenda sia i mesi di picco sia quelli di morbida
  e nessun metodo risulti avvantaggiato dalla scelta della finestra.

La dimensione del test è configurabile in dashboard (da 6 a 18 mesi) nelle
opzioni avanzate, con un vincolo: devono restare almeno 24 mesi di
addestramento.

### Verifica dell'assenza di fughe di informazione

Oltre all'ispezione del codice, la proprietà è verificata da un test
automatico (`test_metodi_ignorano_il_periodo_di_test`) che:

1. prende la serie originale;
2. ne crea una copia in cui i valori del **solo periodo di test** sono
   moltiplicati per 10;
3. verifica che le previsioni di **tutti** i metodi restino identiche.

Se un metodo usasse anche indirettamente il periodo di test, le previsioni
cambierebbero e il test fallirebbe.

---

## 3.5 Criterio di selezione del metodo migliore

### Criterio primario: MAPE out-of-sample minimo

```
metodo* = argmin  MAPE_out-of-sample(metodo)
```

**Motivazione della scelta:**

1. **Confrontabilità fra prodotti.** Il dataset comprende prodotti con volumi
   da 3.000 a 12.000 cartoni/mese. Un criterio basato su MAE o RMSE
   produrrebbe numeri non confrontabili fra loro e renderebbe impossibile
   affermare, ad esempio, che «Nutella è più prevedibile di Happy Hippo».
2. **Interpretabilità manageriale.** «Il modello sbaglia in media del 5%» è
   una frase comprensibile a un direttore della supply chain. «Il modello
   sbaglia in media di 649 cartoni» richiede un contesto aggiuntivo.
3. **Diffusione.** Il MAPE è l'indicatore più usato nella pratica aziendale
   di *demand planning*.

### Fallback documentato

Se il MAPE **non è calcolabile per nessun metodo** (tutte le osservazioni di
test nulle), la selezione ripiega sull'**RMSE minimo**. Se nemmeno l'RMSE è
disponibile, viene sollevato un errore con messaggio esplicativo in italiano.

### Indicatori di supporto

MAE e RMSE sono **sempre** esposti in tabella e selezionabili nel grafico
dell'accuratezza. Questo per due ragioni: consentono di verificare che la
scelta non sia un artefatto del MAPE, e forniscono l'ordine di grandezza
dell'errore in unità operative.

Sul dataset di progetto i tre criteri **concordano** per tutti e quattro i
prodotti tranne Nutella, dove MAPE indica Holt-Winters (4,95% contro 5,00%)
mentre RMSE indicherebbe lo smorzamento esponenziale (833 contro 950). La
divergenza è discussa nella relazione: il margine è talmente esiguo da
rendere le due alternative equivalenti nella pratica.

---

## 3.6 Previsione finale e banda di incertezza

### Procedura in due passi

La previsione mostrata in dashboard è costruita in due fasi distinte:

1. **Passo di validazione.** Il metodo è stimato sui 36 mesi di
   addestramento e valutato sui 12 mesi di test. Da questo confronto si
   ottengono le metriche di accuratezza e, in particolare, l'**RMSE
   out-of-sample**.
2. **Passo di previsione.** Il metodo è **ri-stimato su tutta la storia
   disponibile** (48 mesi) e proiettato per l'orizzonte richiesto.

Il secondo passo è importante: sarebbe uno spreco di informazione prevedere
il 2026 usando un modello stimato solo fino al 2024. La valutazione serve a
**scegliere** il metodo; la previsione finale usa tutti i dati disponibili.

### Banda di incertezza

```
banda = previsione  ±  z · RMSE_out-of-sample
```

con `z` quantile della normale standard al livello di confidenza richiesto
(95% per impostazione predefinita, quindi `z ≈ 1,96`).

**Dichiarazione esplicita delle ipotesi.** Si tratta di una **stima empirica
basata sul modello**, non di un intervallo di previsione derivato
analiticamente dalla struttura statistica del metodo. L'etichetta usata in
dashboard è «Banda empirica 95%» e la didascalia dichiara integralmente le
ipotesi sottostanti:

- gli errori previsionali sono **indipendenti**;
- hanno **media nulla**;
- sono distribuiti **normalmente**;
- hanno **varianza costante** lungo l'orizzonte.

**Perché la banda non si allarga con l'orizzonte.** Un intervallo di
previsione statisticamente rigoroso si allarga all'aumentare di `h`, perché
l'incertezza si accumula. Si è scelto deliberatamente di **non** riprodurre
questo comportamento con una formula arbitraria (del tipo `√h`), perché la
forma esatta dell'allargamento dipende dal modello e non sarebbe corretta per
tutti e cinque i metodi implementati. Si è preferita una banda costante,
onestamente dichiarata come approssimazione, piuttosto che una banda
apparentemente più sofisticata ma non giustificabile. Questa scelta è
registrata fra i limiti del modello.

---

## 3.7 Risultati sul dataset di progetto

Valutazione out-of-sample, split 36/12, parametri predefiniti
(`finestra MA = 3`, `α = 0,30`).

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

### Sintesi

| Prodotto | CV storico (%) | Metodo migliore | MAPE (%) |
|---|---:|---|---:|
| Nutella | 6,7 | Holt-Winters additivo | **4,95** |
| Kinder Cioccolato | 14,1 | Smorzamento esponenziale | **9,78** |
| Ferrero Rocher | 39,9 | Naive stagionale | **9,91** |
| Kinder Happy Hippo | 26,8 | Regressione lineare | **24,60** |

### Lettura dei risultati

**Ogni prodotto richiede un metodo diverso.** È il risultato centrale del
progetto e conferma la premessa della specifica PW24: non esiste un metodo
universalmente migliore. La scelta deve essere guidata dai dati, prodotto per
prodotto.

**Il metodo migliore riflette la struttura della serie.**

- Nutella, serie quasi stazionaria, è ben servita da metodi che stimano il
  livello (Holt-Winters e smorzamento esponenziale sono praticamente
  equivalenti).
- Kinder Cioccolato, con trend moderato e stagionalità debole, premia lo
  smorzamento esponenziale, che insegue il livello senza sovra-modellare una
  stagionalità poco pronunciata.
- Ferrero Rocher, fortemente stagionale, è prevedibile solo da metodi che
  modellano la stagionalità: lo scarto fra il migliore (9,91%) e il peggiore
  (80,93%) è di **71 punti percentuali**.
- Kinder Happy Hippo, dominato da rumore e promozioni casuali, premia la
  regressione lineare, che coglie il trend sottostante ignorando il rumore.

**La variabilità sistematica è prevedibile; quella casuale no.** Ferrero
Rocher ha il coefficiente di variazione più alto (39,9%) ma un MAPE del
9,91%: la sua variabilità è quasi tutta **stagionale**, cioè sistematica e
anticipabile. Kinder Happy Hippo ha un CV inferiore (26,8%) ma il MAPE
peggiore (24,60%): la sua variabilità è **casuale** e per definizione
irriducibile. È la distinzione concettualmente più importante dell'intero
progetto, e ha una conseguenza gestionale diretta: la variabilità sistematica
si gestisce con la **scorta anticipata**, quella casuale con la **scorta di
sicurezza**.

**La complessità non garantisce l'accuratezza.** Holt-Winters, il metodo più
sofisticato, vince solo su un prodotto su quattro, ed è battuto dal
semplicissimo naive stagionale proprio sulla serie più stagionale. È la
conferma empirica del principio per cui un modello complesso va adottato solo
se supera un benchmark semplice.
