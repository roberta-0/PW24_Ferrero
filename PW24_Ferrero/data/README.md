# Dizionario dei dati

> ⚠️ **I dati contenuti in questa cartella sono SINTETICI.** Sono generati
> algoritmicamente dal modulo `src/data_generator.py` a scopo esclusivamente
> didattico. **Nessun valore rappresenta vendite, scorte o informazioni reali
> di Ferrero.** I nomi dei prodotti e dell'impresa sono reali; le quantità no.

---

## File contenuti

| File | Righe | Descrizione |
|---|---:|---|
| `demand_history.csv` | 192 | Dataset principale in **formato lungo** |
| `demand_history_wide.csv` | 48 | Stessi dati in **formato pivot** |
| `product_parameters.csv` | 4 | Parametri del processo generatore |

Tutti i file sono codificati in **UTF-8** con separatore **virgola** e
terminatori di riga standard.

---

## `demand_history.csv` — dataset principale

Formato lungo (*tidy*): una riga per combinazione prodotto × mese.

| Colonna | Tipo | Dominio | Descrizione |
|---|---|---|---|
| `date` | data `AAAA-MM-GG` | 2022-01-01 … 2025-12-01 | Primo giorno del mese di riferimento |
| `product` | testo | 4 valori ammessi | Nome commerciale del prodotto |
| `demand` | intero | > 0 | Domanda mensile in **cartoni** |

**Valori ammessi per `product`**: `Nutella`, `Kinder Cioccolato`,
`Ferrero Rocher`, `Kinder Happy Hippo`.

**Vincoli garantiti dal generatore e verificati dalla validazione:**

- domanda sempre **strettamente positiva** e **intera**;
- nessun valore mancante;
- nessuna data duplicata per lo stesso prodotto;
- serie **continue su base mensile** (nessun mese mancante);
- 48 osservazioni per ciascuno dei 4 prodotti.

Estratto:

```csv
date,product,demand
2022-01-01,Ferrero Rocher,4833
2022-02-01,Ferrero Rocher,6672
2022-03-01,Ferrero Rocher,4658
```

---

## `demand_history_wide.csv` — formato pivot

Stessi dati riorganizzati con una colonna per prodotto. Più comodo per
l'ispezione in un foglio di calcolo e per il confronto diretto fra serie.

| Colonna | Tipo | Descrizione |
|---|---|---|
| `date` | data `AAAA-MM-GG` | Mese di riferimento |
| `Nutella` | intero | Domanda mensile (cartoni) |
| `Kinder Cioccolato` | intero | Domanda mensile (cartoni) |
| `Ferrero Rocher` | intero | Domanda mensile (cartoni) |
| `Kinder Happy Hippo` | intero | Domanda mensile (cartoni) |

---

## `product_parameters.csv` — parametri di generazione

Documenta il processo che ha prodotto i dati, rendendo il dataset
**auto-documentato**: la logica di generazione è ricostruibile senza leggere
il codice sorgente.

| Colonna | Tipo | Descrizione |
|---|---|---|
| `name` | testo | Nome del prodotto |
| `category` | testo | Categoria merceologica (informazione pubblica) |
| `unit` | testo | Unità di misura della domanda |
| `base_demand` | numero | Livello medio di domanda al tempo t = 0 |
| `trend_rate` | numero | Incremento relativo del livello base per mese |
| `seasonal_amplitude` | numero | Ampiezza della sinusoide stagionale (0,10 = ±10%) |
| `seasonal_peak_month` | intero | Mese (1-12) di massimo della sinusoide |
| `noise_std` | numero | Dev. standard del rumore, come coefficiente di variazione |
| `promotion_probability` | numero | Probabilità mensile di un picco promozionale |
| `promotion_amplitude` | numero | Entità del picco, come quota del livello |
| `festive_profile` | testo | Sovra-domanda per mese, formato `mese:valore;mese:valore` |
| `description` | testo | Descrizione del comportamento atteso |

---

## Modello generatore

Per il mese `t = 0…47` e il corrispondente mese solare `m ∈ {1…12}`:

```
L(t) = base_demand × (1 + trend_rate × t)                        livello con trend
S(m) = 1 + A × cos( 2π(m − peak_month)/12 ) + F(m)               fattore stagionale
ε(t) ~ N(0, noise_std)                                           rumore casuale
P(t) = L(t) × promotion_amplitude × U(0,6; 1,4)   con prob. p    picco promozionale

D(t) = round( max( 1 ; L(t) × S(m) × (1 + ε(t)) + P(t) ) )
```

Documentazione completa in [`../docs/dataset.md`](../docs/dataset.md).

---

## Riproducibilità

Il dataset è generato con **seed fissato a 24**. Ogni prodotto usa un flusso
casuale derivato tramite `SeedSequence.spawn`, così che modificare i
parametri di un prodotto non alteri le realizzazioni casuali degli altri.

Per rigenerare i file:

```bash
python -m src.data_generator
```

Il risultato è **bit-per-bit identico** a quello versionato nel repository.

---

## Statistiche descrittive del dataset versionato

| Prodotto | Oss. | Media | Dev. std | Minimo | Massimo | CV (%) |
|---|---:|---:|---:|---:|---:|---:|
| Nutella | 48 | 12.242 | 823 | 10.643 | 14.427 | 6,7 |
| Kinder Cioccolato | 48 | 9.019 | 1.268 | 6.769 | 12.195 | 14,1 |
| Ferrero Rocher | 48 | 6.260 | 2.497 | 3.497 | 12.809 | 39,9 |
| Kinder Happy Hippo | 48 | 3.814 | 1.020 | 1.849 | 6.217 | 26,8 |

I quattro coefficienti di variazione confermano la differenziazione dei
profili richiesta dalla specifica PW24.
