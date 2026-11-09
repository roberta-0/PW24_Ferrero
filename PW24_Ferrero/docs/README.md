# Documentazione tecnica — Project Work 24

Documentazione del progetto *«Sviluppo di una mini-dashboard Python per la
previsione della domanda e la pianificazione delle scorte di un'impresa»*,
Corso di Studi in Informatica per le Aziende Digitali (L-31).

L'intera documentazione è redatta in **italiano**. Restano in lingua originale
soltanto i titoli delle opere citate in bibliografia e gli identificatori del
codice sorgente, per i quali la traduzione sarebbe scorretta.

> **Avvertenza sui dati.** L'impresa Ferrero e i prodotti analizzati sono
> reali e le informazioni istituzionali provengono da fonti pubbliche. Tutti i
> **dati numerici di domanda sono sintetici**, generati algoritmicamente a fini
> didattici: nessun valore rappresenta vendite, scorte o informazioni
> riservate Ferrero.

---

## Indice dei documenti

| Documento | Contenuto |
|---|---|
| [`company.md`](company.md) | L'impresa Ferrero: profilo da fonti pubbliche, i quattro prodotti analizzati, contesto produttivo, commerciale e logistico |
| [`dataset.md`](dataset.md) | Origine dei dati: modello generatore, parametri per prodotto, riproducibilità con seed fissato, livello di validazione |
| [`forecasting.md`](forecasting.md) | I cinque metodi previsionali, le cinque metriche, lo split cronologico, il criterio di selezione del modello |
| [`inventory.md`](inventory.md) | Le quattro componenti di scorta: derivazione delle formule, ipotesi dichiarate, risultati |
| [`scenarios.md`](scenarios.md) | Motore di simulazione, effetto di ciascuna leva, confronto fra scenari |
| [`methodology.md`](methodology.md) | Impostazione metodologica, sintesi dei risultati, 18 limiti e 12 sviluppi futuri |
| [`technical_architecture.md`](technical_architecture.md) | Architettura software, moduli, scelte progettuali, strategia di test |
| [`pw24_compliance.md`](pw24_compliance.md) | Audit di conformità: ogni requisito della specifica mappato su codice, dashboard e documentazione |
| [`references.md`](references.md) | Fonti aziendali, accademiche e tecniche |

Documenti collegati fuori da questa cartella:

| Documento | Contenuto |
|---|---|
| [`../README.md`](../README.md) | Presentazione del progetto, installazione, esecuzione |
| [`../report/relazione_pw24.md`](../report/relazione_pw24.md) | Relazione finale in 22 capitoli, con i risultati effettivamente ottenuti |
| [`../data/README.md`](../data/README.md) | Dizionario dei dati dei tre file CSV |

---

## Percorsi di lettura consigliati

La documentazione è pensata per essere letta in modo selettivo. Di seguito tre
percorsi, a seconda dell'obiettivo.

**Per comprendere il progetto nel suo insieme** (lettura breve):
[`../README.md`](../README.md) → [`methodology.md`](methodology.md).

**Per valutare la correttezza metodologica** (lettura di merito):
[`dataset.md`](dataset.md) → [`forecasting.md`](forecasting.md) →
[`inventory.md`](inventory.md) → [`scenarios.md`](scenarios.md). È il percorso
che segue la catena di calcolo dell'applicazione: dati, previsione, scorte,
simulazione.

**Per verificare la conformità alla specifica PW24**:
[`pw24_compliance.md`](pw24_compliance.md), che rimanda puntualmente a tutti
gli altri documenti.

---

## La catena logica del progetto

I quattro documenti centrali corrispondono ai quattro passaggi del modello,
nell'ordine in cui l'applicazione li esegue:

```
   dataset.md          forecasting.md         inventory.md        scenarios.md
        │                     │                     │                   │
    Dati        →        Previsione       →       Scorte      →    Simulazione
        │                     │                     │                   │
   quanto e'            quanto bene            quanta scorta      cosa cambia
   variabile?           so prevedere?          mi serve?          se...?
```

Il passaggio dal secondo al terzo documento è il nodo concettuale del lavoro:
la scorta di sicurezza non si dimensiona sulla variabilità della domanda, ma
sulla variabilità dell'**errore di previsione**. La motivazione e le
conseguenze quantitative di questa scelta sono in
[`inventory.md`](inventory.md) §4.3.

---

## Corrispondenza fra documenti e codice

| Documento | Moduli descritti |
|---|---|
| [`dataset.md`](dataset.md) | `src/config.py`, `src/data_generator.py`, `src/data_validation.py` |
| [`forecasting.md`](forecasting.md) | `src/forecasting.py`, `src/metrics.py`, `src/evaluation.py` |
| [`inventory.md`](inventory.md) | `src/inventory.py` |
| [`scenarios.md`](scenarios.md) | `src/scenarios.py` |
| [`technical_architecture.md`](technical_architecture.md) | tutti, più `app.py`, `src/charts.py`, `src/narrative.py`, `src/utils.py` |
