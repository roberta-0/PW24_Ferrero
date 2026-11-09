# Risultati generati automaticamente

> File prodotto da `scripts/generate_report_assets.py`.
> Dataset sintetico, seed 24. **Nessun valore rappresenta dati reali Ferrero.**

Ultima esecuzione su 192 osservazioni
(2022-01 / 2025-12).

## 1. Statistiche descrittive delle serie storiche

| Prodotto | Osservazioni | Media | Dev. std | Minimo | Massimo |
|---|---|---|---|---|---|
| Nutella | 48 | 12.242,00 | 822,60 | 10643 | 14427 |
| Kinder Cioccolato | 48 | 9.018,70 | 1.268,10 | 6769 | 12195 |
| Ferrero Rocher | 48 | 6.259,90 | 2.497,50 | 3497 | 12809 |
| Kinder Happy Hippo | 48 | 3.814,20 | 1.020,40 | 1849 | 6217 |

## 2. Confronto dei metodi previsionali (valutazione out-of-sample)

Split cronologico: 36 mesi di addestramento, 12 mesi di test.

| Prodotto | Metodo | MAE | RMSE | MAPE | Migliore |
|---|---|---|---|---|---|
| Ferrero Rocher | Media mobile | 4.188,61 | 4.618,00 | 80,93 |  |
| Ferrero Rocher | Smorzamento esponenziale | 3.170,44 | 3.367,08 | 59,28 |  |
| Ferrero Rocher | Regressione lineare | 2.406,85 | 2.604,38 | 43,80 |  |
| Ferrero Rocher | Naive stagionale | 599,25 | 719,94 | 9,91 | SI |
| Ferrero Rocher | Holt-Winters additivo | 962,92 | 1.170,93 | 15,84 |  |
| Kinder Cioccolato | Media mobile | 1.013,64 | 1.220,34 | 11,08 |  |
| Kinder Cioccolato | Smorzamento esponenziale | 910,47 | 1.083,30 | 9,78 | SI |
| Kinder Cioccolato | Regressione lineare | 961,49 | 1.153,03 | 10,35 |  |
| Kinder Cioccolato | Naive stagionale | 1.205,00 | 1.432,10 | 12,05 |  |
| Kinder Cioccolato | Holt-Winters additivo | 1.186,50 | 1.333,68 | 12,49 |  |
| Kinder Happy Hippo | Media mobile | 1.085,28 | 1.381,11 | 33,32 |  |
| Kinder Happy Hippo | Smorzamento esponenziale | 1.019,62 | 1.206,91 | 29,66 |  |
| Kinder Happy Hippo | Regressione lineare | 1.010,28 | 1.145,86 | 24,60 | SI |
| Kinder Happy Hippo | Naive stagionale | 1.292,75 | 1.532,61 | 30,38 |  |
| Kinder Happy Hippo | Holt-Winters additivo | 1.115,72 | 1.214,82 | 30,54 |  |
| Nutella | Media mobile | 701,67 | 855,22 | 5,64 |  |
| Nutella | Smorzamento esponenziale | 643,65 | 833,40 | 5,00 |  |
| Nutella | Regressione lineare | 702,11 | 942,74 | 5,36 |  |
| Nutella | Naive stagionale | 960,92 | 1.214,38 | 7,47 |  |
| Nutella | Holt-Winters additivo | 649,13 | 950,37 | 4,95 | SI |

## 3. Metodo migliore per prodotto (criterio: MAPE minimo)

| Prodotto | Domanda media | Dev. std | CV (%) | Metodo migliore | MAE | RMSE | MAPE (%) |
|---|---|---|---|---|---|---|---|
| Nutella | 12.242,00 | 823,00 | 6,70 | Holt-Winters additivo | 649,10 | 950,40 | 4,95 |
| Kinder Cioccolato | 9.019,00 | 1.268,00 | 14,10 | Smorzamento esponenziale | 910,50 | 1.083,30 | 9,78 |
| Ferrero Rocher | 6.260,00 | 2.497,00 | 39,90 | Naive stagionale | 599,20 | 719,90 | 9,91 |
| Kinder Happy Hippo | 3.814,00 | 1.020,00 | 26,80 | Regressione lineare | 1.010,30 | 1.145,90 | 24,60 |

## 4. Piano di scorta - scenario baseline

Parametri: lead time 2 mesi, livello di servizio 95%, periodo di riesame
1 mese, orizzonte di previsione 12 mesi.

| Prodotto | Domanda media prevista | Scorta ciclica | Scorta di sicurezza | Scorta anticipata | Scorta pipeline | Scorta totale | Copertura (mesi) | Metodo |
|---|---|---|---|---|---|---|---|---|
| Nutella | 13.366,00 | 6.683,00 | 2.211,00 | 3.479,00 | 26.732,00 | 39.105,00 | 2,90 | Holt-Winters additivo |
| Kinder Cioccolato | 10.149,00 | 5.075,00 | 2.520,00 | 0,00 | 20.299,00 | 27.893,00 | 2,70 | Smorzamento esponenziale |
| Ferrero Rocher | 6.374,00 | 3.187,00 | 1.675,00 | 11.272,00 | 12.748,00 | 28.882,00 | 4,50 | Naive stagionale |
| Kinder Happy Hippo | 4.354,00 | 2.177,00 | 2.665,00 | 324,00 | 8.709,00 | 13.876,00 | 3,20 | Regressione lineare |

## 5. Confronto fra scenari (prodotto: Ferrero Rocher)

- **Scenario A - Filiera stabile**: variabilita' x0,5; lead time 2 mesi; servizio 95%.
- **Scenario B - Filiera sotto stress**: variabilita' x2,0; lead time 5 mesi; servizio 99%.

| Indicatore | A - Filiera stabile | B - Filiera sotto stress | Variazione | Variazione % |
|---|---|---|---|---|
| Domanda media prevista (unita'/mese) | 6.532,58 | 6.056,75 | -475,83 | -7,28 |
| Dev. std errore previsionale (unita') | 358,20 | 1.496,04 | 1.137,85 | 317,66 |
| Scorta ciclica (unita') | 3.266,29 | 3.028,38 | -237,92 | -7,28 |
| Scorta di sicurezza (unita') | 833,23 | 7.782,22 | 6.948,99 | 833,99 |
| Scorta anticipata (unita') | 11.606,67 | 10.603,00 | -1.003,67 | -8,65 |
| Scorta pipeline (unita') | 13.065,17 | 30.283,75 | 17.218,58 | 131,79 |
| Scorta totale (unita') | 28.771,35 | 51.697,34 | 22.925,99 | 79,68 |
| Copertura scorta totale (mesi) | 4,40 | 8,54 | 4,13 | 93,80 |

### Lettura gestionale

Passando da **A - Filiera stabile** a **B - Filiera sotto stress** la scorta totale varia del **+79,7%** (da 28.771 a 51.697 cartoni), con una copertura che passa da 4,4 a 8,5 mesi di domanda.

Il principale responsabile dello scostamento e' la **scorta pipeline** (+17.219 cartoni, pari al 75,1% della variazione complessiva).

Le leve modificate sono: il lead time passa da 2 mesi a 5 mesi; il livello di servizio passa dal 95.0% al 99.0% (z da 1.645 a 2.326); la variabilita' della domanda passa da x0.50 a x2.00.

**Implicazione gestionale.** Lo scenario B richiede un investimento in capitale circolante sensibilmente superiore. La decisione non e' puramente tecnica: occorre confrontare il costo di mantenimento della scorta aggiuntiva con il costo atteso delle rotture di stock evitate (mancato margine, penali contrattuali verso la grande distribuzione, perdita di spazio a scaffale). Per un prodotto alimentare va inoltre considerato il rischio di obsolescenza legato alla shelf life.
