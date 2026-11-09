# 4. Modelli di pianificazione delle scorte

Questo capitolo descrive le quattro componenti di scorta calcolate dal
progetto, le formule adottate, le ipotesi semplificative dichiarate e
l'interpretazione gestionale di ciascuna componente.

Codice di riferimento: `src/inventory.py`.

> **Avvertenza.** Le formule implementate sono **formulazioni didattiche
> standard** della letteratura di Operations Management. Non riproducono le
> procedure operative effettive di Ferrero, che non sono pubbliche, e non
> pretendono di essere politiche di scorta ottimali per un caso reale.

---

## 4.1 Perché scomporre la scorta

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

Questa scomposizione è il cuore della sezione 4 della dashboard: mostrare
*quanta* scorta serve è utile, ma mostrare *perché* serve è ciò che consente
di decidere dove intervenire.

### Notazione comune

| Simbolo | Significato | Unità |
|---|---|---|
| `D` | domanda media mensile **prevista** | cartoni/mese |
| `R` | periodo di riesame / ciclo di riordino | mesi |
| `L` | lead time di approvvigionamento | mesi |
| `σ` | dev. standard mensile dell'**errore previsionale** | cartoni |
| `z` | fattore di sicurezza della normale standard | — |

Una precisazione importante: `D` è la media della **previsione** sull'orizzonte
selezionato, **non** la media storica. Le scorte si dimensionano sulla domanda
che ci si attende, non su quella passata. È per questo che la leva «trend»
influenza il fabbisogno di scorta.

---

## 4.2 Scorta ciclica (*cycle stock*)

### Formula

```
Q  = D × R                    (lotto di riordino)
Scorta ciclica = Q / 2 = D × R / 2
```

### Derivazione

Il modello adottato è il **riordino a intervallo fisso con copertura pari al
periodo di riesame**: ogni `R` mesi si ordina la quantità necessaria a coprire
i successivi `R` mesi di domanda, cioè `Q = D × R`.

Se la domanda viene prelevata a tasso uniforme all'interno del periodo, la
giacenza evolve linearmente da `Q` (subito dopo il ricevimento) a `0` (alla
fine del ciclo). La giacenza **media** su un ciclo è quindi l'area del
triangolo divisa per la base, cioè `Q/2`.

```
giacenza
   Q │╲          ╲          ╲
     │ ╲          ╲          ╲
 Q/2 │··╲··········╲··········╲···  ← giacenza media
     │   ╲          ╲          ╲
   0 └────╲──────────╲──────────╲──→ tempo
     0    R         2R         3R
```

### Ipotesi semplificative dichiarate

1. **Prelievo uniforme** all'interno del periodo di riesame.
2. **Nessun vincolo di lotto minimo** di produzione.
3. **Nessuno sconto quantità** che incentivi lotti maggiori.
4. **Nessun costo esplicito** di ordinazione o mantenimento.

### Perché non il modello EOQ di Wilson

Il lotto economico (*Economic Order Quantity*) sarebbe la scelta teoricamente
più raffinata:

```
Q* = √( 2 · D · costo_ordine / costo_mantenimento_unitario )
```

È stata **deliberatamente evitata** perché richiede il costo di emissione
dell'ordine e il costo unitario di mantenimento. Nel caso Ferrero questi
valori non sono pubblici: andrebbero inventati, e il risultato apparirebbe
più rigoroso di quanto sia. Il modello a copertura fissa, pur più semplice,
ha il vantaggio di dipendere da un solo parametro (`R`) che l'utente può
impostare consapevolmente, senza introdurre numeri arbitrari.

L'estensione all'EOQ è indicata fra i possibili sviluppi futuri.

### Leve che la influenzano

| Leva | Effetto |
|---|---|
| Periodo di riesame `R` | **lineare** — raddoppiare `R` raddoppia la scorta ciclica |
| Domanda prevista `D` | **lineare** |
| Lead time `L` | **nessuno** — la scorta ciclica non dipende dal lead time |

---

## 4.3 Scorta di sicurezza (*safety stock*)

### Formula

```
Scorta di sicurezza = z × σ_IP

con    σ_IP = σ × √(intervallo di protezione)
```

Nella configurazione di base l'intervallo di protezione è il solo lead time:

```
Scorta di sicurezza = z × σ × √L
```

### Derivazione

La scorta di sicurezza protegge dalla **variabilità della domanda durante il
periodo in cui non si può reagire**. Se la domanda mensile ha deviazione
standard `σ` e gli errori mensili sono **indipendenti**, le varianze si
sommano sui mesi dell'intervallo di protezione:

```
Var( domanda su L mesi ) = L · σ²     →     σ_IP = σ · √L
```

Approssimando la domanda cumulata con una distribuzione normale, la scorta
che garantisce una probabilità `SL` di non andare in rottura è `z · σ_IP`, con
`z = Φ⁻¹(SL)`.

### Il fattore di sicurezza z

| Livello di servizio | z |
|---|---:|
| 90,0% | 1,282 |
| 95,0% | 1,645 |
| 97,5% | 1,960 |
| 99,0% | 2,326 |

A runtime `z` è calcolato con `scipy.stats.norm.ppf`; i valori tabulati sono
riportati in `src/config.py` come riferimento documentale e verificati dai
test.

**Osservazione gestionale.** La relazione fra livello di servizio e `z` è
**fortemente non lineare**. Passare dal 90% al 95% costa 0,36 punti di `z`;
passare dal 95% al 99% ne costa 0,68; passare dal 99% al 99,9% ne costerebbe
altri 0,78. Il costo marginale della protezione cresce rapidamente, e il
100% richiederebbe una scorta infinita. È una delle conclusioni che la
dashboard rende esplicite nel commento dinamico.

### Significato del livello di servizio adottato

Il livello di servizio è qui inteso come **cycle service level**: la
probabilità di **non** andare in rottura di stock durante un ciclo di
riordino. Non è il *fill rate* (frazione della domanda servita), che è una
grandezza diversa e in genere più elevata a parità di scorta. La distinzione
è dichiarata perché le due grandezze sono spesso confuse.

### Stima di σ: l'errore previsionale, non la domanda

**Questa è la scelta metodologicamente più rilevante del modello di scorta.**

Una formulazione elementare userebbe la deviazione standard della **domanda
storica**. Il progetto usa invece la deviazione standard dell'**errore
previsionale out-of-sample** (l'RMSE sul periodo di test).

La ragione è che ciò che causa una rottura di stock non è la variabilità
della domanda in sé, ma la parte di variabilità che **non si è riusciti a
prevedere**. Una domanda fortemente stagionale ma perfettamente anticipata
dal modello non richiede alcun cuscinetto di sicurezza: richiede semmai
scorta anticipata, che è un'altra cosa.

L'effetto di questa scelta è ben visibile sui dati di progetto:

| Prodotto | Dev. std domanda | σ (RMSE out-of-sample) | Rapporto |
|---|---:|---:|---:|
| Nutella | 823 | 950 | 1,15 |
| Kinder Cioccolato | 1.268 | 1.083 | 0,85 |
| **Ferrero Rocher** | **2.497** | **720** | **0,29** |
| Kinder Happy Hippo | 1.020 | 1.146 | 1,12 |

Su Ferrero Rocher, usare la variabilità grezza della domanda avrebbe
sovrastimato il fabbisogno di sicurezza di oltre **tre volte**: la gran
parte di quella variabilità è stagionalità, che il modello previsionale
cattura e che va gestita con la scorta anticipata. È una differenza
quantitativamente enorme e gestionalmente sostanziale.

### Intervallo di protezione esteso (opzione avanzata)

Nel riordino **periodico** la copertura dovrebbe estendersi anche al tempo
che intercorre fra due revisioni successive: fra una revisione e l'altra
l'impresa non può reagire a uno scostamento, anche se il fornitore
consegnasse istantaneamente. La formulazione estesa è:

```
σ_IP = σ × √( L + R )
```

La dashboard offre questa variante come opzione nelle impostazioni avanzate
(«Intervallo di protezione = lead time + periodo di riesame»), disattivata
per impostazione predefinita per aderire alla formulazione richiesta dalla
specifica PW24. La differenza è didatticamente istruttiva: con `L = 2` e
`R = 1`, attivare l'opzione aumenta la scorta di sicurezza del 22,5%
(`√3/√2`).

### Ipotesi dichiarate

1. `σ` è stimata dall'**errore previsionale out-of-sample**, non dalla
   variabilità grezza della domanda.
2. Gli errori previsionali mensili sono **indipendenti** (nessuna
   autocorrelazione). Nella realtà gli errori tendono a essere correlati, il
   che renderebbe la formula `σ·√L` una **sottostima**.
3. Il **lead time è deterministico**. Un lead time variabile aggiungerebbe un
   termine `D² · σ_L²` sotto radice, aumentando il fabbisogno.
4. La domanda nell'intervallo di protezione è approssimata come **normale**.
5. Il livello di servizio è un **cycle service level**.

### Leve che la influenzano

| Leva | Effetto |
|---|---|
| Variabilità della domanda | **lineare** in σ — raddoppiare σ raddoppia la scorta |
| Lead time `L` | **radice quadrata** — quadruplicare `L` raddoppia la scorta |
| Livello di servizio | **non lineare crescente** via `z` |

---

## 4.4 Scorta anticipata (*anticipation / seasonal stock*)

### Formula

```
C(t) = Σ ( d(k) − B )           per k = 1…t,   con C(0) = 0

Scorta anticipata = max C(t) − min C(t)
```

dove `d(k)` è la domanda prevista del mese `k` e `B` il ritmo produttivo
livellato (per impostazione predefinita la media della previsione
sull'orizzonte).

### Derivazione

Il modello rappresenta il **livellamento della produzione**: l'impresa
produce a ritmo costante `B` mentre la domanda `d(t)` è stagionale. Nei mesi
di bassa stagione si accumula magazzino, che viene poi consumato durante il
picco.

Definita l'eccedenza cumulata della domanda rispetto alla produzione `C(t)`,
la giacenza al tempo `t` è:

```
I(t) = I(0) − C(t)
```

Per non andare mai in rottura serve `I(t) ≥ 0` per ogni `t`, cioè
`I(0) ≥ max C(t)`. Adottando il valore minimo ammissibile, la **giacenza
massima** generata dal livellamento è:

```
I_max = I(0) − min C(t) = max C(t) − min C(t)
```

Il punto `C(0) = 0` è incluso fra i candidati perché la giacenza iniziale è
essa stessa un punto ammissibile della traiettoria.

```
domanda
   │        ╭──╮
 B │────────┼──┼────────  ← produzione livellata
   │  ╰──╯  │  │
   └────────┴──┴──────→
      accumulo  consumo
      (scorta anticipata)
```

### Proprietà del modello

| Situazione | Risultato |
|---|---|
| Domanda perfettamente piatta | **0** — nessun accumulo necessario |
| Ampiezza stagionale crescente | **crescente** — monotòno |
| Produzione `B` inferiore alla domanda media | **crescente** |

Esempio verificabile a mano (e coperto da test): sei mesi a 100 unità seguiti
da sei mesi a 300 danno media 200; l'eccedenza cumulata scende a −600 e
risale a 0, quindi la scorta anticipata vale **600 unità**.

### Dipendenza dalla forma della previsione

**Osservazione importante e dichiarata.** La scorta anticipata è calcolata
sulla **previsione**, non sulla serie storica. Ne consegue che se il metodo
previsionale selezionato produce una previsione **piatta** — come la media
mobile e lo smorzamento esponenziale semplice — la scorta anticipata risulta
**nulla**, anche se la serie storica è stagionale.

Questo comportamento si osserva effettivamente nei risultati: per Kinder
Cioccolato, il cui metodo migliore è lo smorzamento esponenziale, la scorta
anticipata vale 0.

Il comportamento è **internamente coerente**: se la previsione ufficiale
dell'impresa non prevede picchi, non c'è nulla da anticipare. Ma è anche un
**limite del modello** che merita attenzione gestionale: segnala che
adottare un metodo previsionale non stagionale su un prodotto stagionale non
produce solo previsioni peggiori, ma **azzera anche la pianificazione
dell'accumulo preventivo**. È un effetto a cascata della scelta del modello
che il progetto rende visibile anziché nascondere, ed è discusso fra i limiti
in [`methodology.md`](methodology.md).

### Rilevanza per Ferrero Rocher

È la componente dominante del prodotto più stagionale. Nello scenario
baseline la scorta anticipata di Ferrero Rocher vale **11.272 cartoni**, pari
al **39%** della sua scorta totale: la quantità che l'impresa deve accumulare
nei mesi estivi per servire il picco di novembre mantenendo la produzione
livellata.

L'alternativa gestionale sarebbe dotarsi di **flessibilità di capacità
produttiva** (turni aggiuntivi, personale stagionale, linee dedicate), con
costi di straordinario e di gestione del personale. Il confronto fra il costo
di mantenimento di 11.272 cartoni per alcuni mesi e il costo della
flessibilità produttiva è una decisione classica di *aggregate planning*, che
il progetto quantifica dal lato della scorta.

### Leve che la influenzano

| Leva | Effetto |
|---|---|
| Stagionalità | **crescente** — è la leva principale |
| Metodo previsionale | **determinante** — previsione piatta ⇒ scorta nulla |
| Orizzonte di previsione | rilevante — orizzonti inferiori a 12 mesi catturano solo parte del ciclo |

---

## 4.5 Scorta pipeline (*in transito*)

### Formula

```
Scorta pipeline = D × L
```

### Derivazione

È un'applicazione diretta della **legge di Little**: in un sistema stazionario
il numero medio di unità presenti è pari al tasso di flusso moltiplicato per
il tempo di permanenza.

```
WIP medio = tasso di flusso × tempo di attraversamento
          = D × L
```

Il tasso di flusso del rifornimento a regime coincide con la domanda media
(ciò che esce dal magazzino deve mediamente entrarvi), e il tempo di
attraversamento è il lead time.

### Interpretazione gestionale

La scorta pipeline è **già di proprietà dell'impresa** — tipicamente già
pagata o impegnata — ma **non è disponibile per la vendita immediata**.
Incide quindi sul capitale circolante senza contribuire al livello di
servizio nel breve periodo. È la componente che un direttore finanziario
guarda con maggiore attenzione.

### Perché è la componente dominante nei risultati

Nello scenario baseline la scorta pipeline rappresenta il **68%** della
scorta totale di Nutella e il **73%** di quella di Kinder Cioccolato. Il
motivo è strutturale: con `L = 2` mesi e `R = 1` mese, la pipeline vale
`D × 2` mentre la ciclica vale `D × 0,5`, cioè **quattro volte di meno**.

Questo risultato ha una conseguenza gestionale diretta e quantificabile:
l'intervento con il maggiore impatto sul capitale circolante non è
l'ottimizzazione dei lotti di riordino né la riduzione del livello di
servizio, ma **l'accorciamento del lead time** (fornitori più vicini,
trasporto più rapido, produzione più reattiva).

### Leve che la influenzano

| Leva | Effetto |
|---|---|
| Lead time `L` | **lineare** — raddoppiare `L` raddoppia la scorta pipeline |
| Domanda prevista `D` | **lineare** |
| Livello di servizio | **nessuno** |

---

## 4.6 Scorta totale e composizione

```
Scorta totale rilevante =
      Scorta ciclica
    + Scorta di sicurezza
    + Scorta anticipata
    + Scorta pipeline
```

La dashboard espone, oltre al totale:

- il **valore assoluto** di ciascuna componente (cartoni);
- la **quota percentuale** sul totale;
- la **copertura in mesi** di domanda media prevista (`scorta totale / D`),
  indicatore sintetico immediatamente confrontabile fra prodotti.

### Risultati nello scenario baseline

Parametri: lead time 2 mesi, livello di servizio 95%, periodo di riesame 1
mese, orizzonte di previsione 12 mesi.

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
| Kinder Happy Hippo | 15,7% | **19,2%** | 2,3% | **62,8%** |

### Lettura dei risultati

**La composizione racconta il prodotto.** Le quattro righe hanno profili
nettamente diversi, e ciascuno riflette la natura della domanda:

- **Ferrero Rocher** è l'unico in cui la pipeline non domina: il 39% della
  sua scorta è **anticipata**, cioè esiste per ragioni di stagionalità. È il
  prodotto in cui la pianificazione della produzione conta più della logistica
  di approvvigionamento.
- **Kinder Happy Hippo** ha la quota di **scorta di sicurezza più alta**
  (19,2%), pur essendo il prodotto con i volumi minori. È la conseguenza
  diretta della sua variabilità casuale: è il prodotto che "costa di più"
  in termini di incertezza.
- **Nutella e Kinder Cioccolato** sono dominati dalla pipeline: sono prodotti
  prevedibili e regolari, per i quali il problema di scorta è essenzialmente
  un problema di **tempi di approvvigionamento**.

**Ferrero Rocher ha la copertura più alta** (4,5 mesi contro 2,7-3,2 degli
altri) nonostante volumi intermedi: la stagionalità impone strutturalmente
più magazzino. È il prezzo della concentrazione della domanda nel tempo.

**La scorta di sicurezza è ovunque la componente minore** (fra il 5,7% e il
19,2%). È un risultato che merita commento, perché contraddice l'intuizione
comune secondo cui la scorta serve soprattutto a "stare tranquilli". Nel
modello adottato la maggior parte del magazzino esiste per ragioni
**strutturali** — tempi di transito e lotti di riordino — e non per
incertezza. Ne segue che chi volesse ridurre il magazzino dovrebbe agire
prima di tutto sui tempi di filiera, non sul livello di servizio.
