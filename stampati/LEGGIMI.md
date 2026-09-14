# Stampati — Gabriel Calasi

Quattro file pronti per la stampa. I caratteri sono incorporati nei PDF,
quindi in tipografia non vengono sostituiti.

## Biglietti da visita

Due versioni dello stesso biglietto: **scegline una**, non servono entrambe.
Formato 85 × 55 mm, un lato solo, abbondanza 3 mm, crocini di taglio.

| File | Com'è | Quando usarlo |
|---|---|---|
| `gabriel-biglietto-sobrio-stampa.pdf` | Carta chiara, un carattere solo | Preventivi in casa, ditte, fornitori |
| `gabriel-biglietto-scuro-stampa.pdf` | Fondo antracite pieno | Bacheche, volantinaggio, si fa notare |

Da dire alla tipografia: 85 × 55 mm finito, 3 mm di abbondanza, crocini
inclusi nel file. Il fondo pieno della versione scura costa un po' di più e
tende a segnare le impronte su carta opaca: se la tipografia lo sconsiglia,
usa la versione sobria.

## Volantino

Formato A6, 105 × 148,5 mm, un lato solo.

| File | A cosa serve |
|---|---|
| `volantino-a6-stampa.pdf` | Il singolo con i crocini, da dare in tipografia |
| `volantino-a4-4-per-foglio.pdf` | Un A4 con quattro volantini, da stampare e ritagliare |

**Per stamparlo in proprio**: usa il file A4, stampa **al 100%**, *non*
"adatta alla pagina" — altrimenti i quattro non restano A6 e i tagli non
tornano. Le linee di taglio cadono nel bianco fra un volantino e l'altro:
si può tagliare anche con le forbici. Nessun colore arriva al bordo, quindi
il margine che la stampante non copre resta carta bianca e non si vede.

**Se ne stampi qualche centinaio**: conviene la copisteria su carta patinata
da 150 g, costa pochi centesimi a volantino e la fotografia cambia faccia.

## Una cosa da decidere prima di ordinare

I codici QR puntano a `gabriel-tuttofare.vercel.app`. Se prendi un dominio
tuo, **i codici vanno rifatti e la carta già stampata diventa da buttare**.
Decidi il dominio prima di mandare in stampa. Rigenerare i file è un comando:

    python tools/genera-biglietto.py
    python tools/genera-volantino.py

## Come sono stati progettati

`FILOSOFIA-BIGLIETTI.md` e `FILOSOFIA-VOLANTINO.md` raccontano l'impianto
visivo dietro le due famiglie. Non servono per stampare.
