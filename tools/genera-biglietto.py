# -*- coding: utf-8 -*-
"""TRACCIATO — biglietti da visita di Gabriel Calasi.

Due impianti, stessi dati, stesso marchio. Entrambi 85x55 mm a lato unico,
abbondanza 3 mm, crocini di taglio.

  SCURO   antracite pieno, nome in Anton, il carattere da insegna del sito.
          Si fa notare. Una colonna sola, gerarchia affidata alla dimensione.

  SOBRIO  carta chiara, solo Barlow, la gerarchia affidata al peso invece
          che al corpo. Due assi — margine sinistro e margine destro — e un
          filetto che separa chi sono da come mi trovi. Il QR non ha bisogno
          di nessuna tessera: sta direttamente sulla carta.

Tavolozza, marchio, QR e verifiche stanno in tools/tracciato.py, in comune
con il volantino.
"""

import os, sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm

from tracciato import (ANTRACITE, ARANCIO, CARTA, CHIARO, FUMO, MATITA, FILETTO,
                       CAP_ANTON, CAP_BARLOW, NOME, RUOLO, LAVORI, TEL, ZONA, URL,
                       carica_font, azzera, reg, larghezza, verifica as _verifica,
                       BOX, CORPI,
                       tracking, marchio, qr_vettoriale, crocini, didascalia)

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "stampati"
carica_font()

# ---------------------------------------------------------------- geometria
TRIM_W, TRIM_H = 85 * mm, 55 * mm
BLEED, MARK_ROOM = 3 * mm, 5 * mm
OFF = BLEED + MARK_ROOM
PAGE_W, PAGE_H = TRIM_W + 2 * OFF, TRIM_H + 2 * OFF


def bordi(margine):
    """Area di sicurezza per un dato margine, in coordinate di pagina."""
    return (OFF + margine, OFF + TRIM_W - margine,
            OFF + margine, OFF + TRIM_H - margine)


def verifica(margine):
    return _verifica(*bordi(margine))


def sfondo(c, colore):
    """Il colore si ferma all'abbondanza: fuori resta carta bianca, e i
    crocini restano leggibili."""
    c.setFillColor(colore)
    c.rect(OFF - BLEED, OFF - BLEED, TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED, stroke=0, fill=1)


def rifinitura(c, testo):
    crocini(c, OFF, OFF, TRIM_W, TRIM_H, BLEED)
    didascalia(c, PAGE_W / 2, 2.2 * mm, testo)


# ------------------------------------------------------------------- SCURO


MARGINE_SCURO = 5 * mm


def scuro(c):
    """Antracite pieno, nome in Anton: l'impianto che si fa notare."""
    L, R, B, T = bordi(MARGINE_SCURO)
    sfondo(c, ANTRACITE)

    # la tessera del QR. Su fondo scuro il codice andrebbe invertito, ma non
    # tutti i lettori reggono l'inversione: meglio aprire un chiaro, perche'
    # su carta stampata non si torna indietro.
    tess, alta = 19.5 * mm, 23.4 * mm
    tx, ty = R - tess, B
    c.setFillColor(CARTA)
    c.roundRect(tx, ty, tess, alta, 1.2 * mm, stroke=0, fill=1)
    pad = 1.8 * mm
    n, modulo = qr_vettoriale(c, tx + pad, ty + alta - pad - (tess - 2 * pad),
                              tess - 2 * pad, URL)
    # la didascalia sta dentro la tessera, sotto il codice: sul fondo scuro
    # non avrebbe spazio sotto, e staccata dal chiaro sembrerebbe un avanzo
    c.setFont("Barlow-SB", 7.8)
    c.setFillColor(ANTRACITE)
    c.drawCentredString(tx + tess / 2, ty + 2.0 * mm, "Il sito")
    larghezza("Il sito", "Barlow-SB", 7.8)
    reg("tessera QR", tx, ty, tx + tess, ty + alta)

    s = 8.4 * mm
    marchio(c, L, T - s, s)
    reg("marchio", L, T - s, L + s, T)

    x_nome, y_nome = L + s + 3.4 * mm, T - s + 1.4 * mm
    c.setFont("Anton", 23.0)
    c.setFillColor(CHIARO)
    c.drawString(x_nome, y_nome, NOME)
    reg("nome", x_nome, y_nome, x_nome + larghezza(NOME, "Anton", 23.0),
        y_nome + 23.0 * CAP_ANTON)

    y_linea = T - 13.2 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(0.7)
    c.line(L, y_linea, R, y_linea)

    y_ruolo = y_linea - 4.2 * mm
    w = tracking(c, L, y_ruolo, RUOLO.upper(), "Barlow-SB", 8.0, ARANCIO, 1.5)
    reg("ruolo", L, y_ruolo, L + w, y_ruolo + 8.0 * CAP_BARLOW)

    y_lav, interlinea = y_ruolo - 4.8 * mm, 3.7 * mm
    c.setFont("Barlow", 8.0)
    c.setFillColor(FUMO)
    for i, riga in enumerate(LAVORI):
        c.drawString(L, y_lav - i * interlinea, riga)
    reg("lavori", L, y_lav - (len(LAVORI) - 1) * interlinea - 1.7,
        L + max(larghezza(r, "Barlow", 8.0) for r in LAVORI), y_lav + 8.0 * CAP_BARLOW)

    y_tel = B + 8.0 * mm
    c.setFont("Anton", 25.0)
    c.setFillColor(CHIARO)
    c.drawString(L, y_tel, TEL)
    reg("telefono", L, y_tel, L + larghezza(TEL, "Anton", 25.0), y_tel + 25.0 * CAP_ANTON)

    y_zona = B + 3.4 * mm
    w = tracking(c, L, y_zona, ZONA.upper(), "Barlow-SB", 8.0, FUMO, 1.1)
    reg("zona", L, y_zona, L + w, y_zona + 8.0 * CAP_BARLOW)

    rifinitura(c, "GABRIEL CALASI  ·  scuro  ·  85 x 55 mm  ·  abbondanza 3 mm")
    c.showPage()
    return n, modulo


# ------------------------------------------------------------------ SOBRIO


MARGINE_SOBRIO = 6 * mm


def sobrio(c):
    """Carta chiara, un carattere solo, due assi.

    Niente Anton: la gerarchia la fa il peso, non il corpo, ed e' la ragione
    per cui questo impianto sembra piu' serio. Il marchio e il ruolo sono gli
    unici due punti di arancio; il resto e' inchiostro e vuoto.
    """
    L, R, B, T = bordi(MARGINE_SOBRIO)
    sfondo(c, CARTA)

    # --- il QR in alto a destra, direttamente sulla carta: nessuna tessera,
    # nessun riquadro. Senza il riquadro che lo isola pero'' il lettore fatica
    # a trovarlo in mezzo al resto, quindi qui il codice e'' piu'' grande che
    # sulla versione scura: 18,5 mm invece di 16.
    lato = 18.5 * mm
    qx, qy = R - lato, T - lato
    n, modulo = qr_vettoriale(c, qx, qy, lato, URL)

    # la didascalia appartiene al codice: sta appesa sotto, e si registra
    # insieme a lui come un blocco solo. Fra una figura e la sua didascalia
    # non vale lo stacco che serve fra due blocchi diversi.
    y_did = qy - 3.0 * mm
    c.setFont("Barlow-SB", 7.8)
    c.setFillColor(MATITA)
    c.drawRightString(R, y_did, "Il sito")
    larghezza("Il sito", "Barlow-SB", 7.8)
    reg("QR", qx, y_did - 1.8, qx + lato, qy + lato)

    # --- identita': marchio e nome sulla stessa linea, come una firma
    s = 7.2 * mm
    y_m = T - s
    marchio(c, L, y_m, s, segno=CARTA)
    reg("marchio", L, y_m, L + s, T)

    c_nome = 12.5
    x_nome = L + s + 3.6 * mm
    y_nome = y_m + (s - c_nome * CAP_BARLOW) / 2 + 0.2 * mm
    w_nome = tracking(c, x_nome, y_nome, NOME, "Barlow-B", c_nome, ANTRACITE, 0.9)
    reg("nome", x_nome, y_nome, x_nome + w_nome, y_nome + c_nome * CAP_BARLOW)

    # --- il mestiere: minuscolo, non gridato. L'arancio basta a segnalarlo.
    y_ruolo = y_m - 5.0 * mm
    c.setFont("Barlow", 9.0)
    c.setFillColor(ARANCIO)
    c.drawString(L, y_ruolo, RUOLO)
    reg("ruolo", L, y_ruolo - 1.9, L + larghezza(RUOLO, "Barlow", 9.0),
        y_ruolo + 9.0 * CAP_BARLOW)

    # --- in che cosa consiste
    y_lav, interlinea = y_ruolo - 6.6 * mm, 4.0 * mm
    c.setFont("Barlow", 8.0)
    c.setFillColor(MATITA)
    for i, riga in enumerate(LAVORI):
        c.drawString(L, y_lav - i * interlinea, riga)
    reg("lavori", L, y_lav - (len(LAVORI) - 1) * interlinea - 1.7,
        L + max(larghezza(r, "Barlow", 8.0) for r in LAVORI), y_lav + 8.0 * CAP_BARLOW)

    # --- il filetto separa chi sono da come mi trovi. Da margine a margine:
    # e' la riga che tiene insieme i due assi.
    y_filo = B + 13.0 * mm
    c.setStrokeColor(FILETTO)
    c.setLineWidth(0.5)
    c.line(L, y_filo, R, y_filo)

    # --- il numero: qui il peso fa il lavoro che altrove faceva il corpo
    c_tel = 16.5
    y_tel = B + 2.8 * mm
    c.setFont("Barlow-B", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    reg("telefono", L, y_tel, L + larghezza(TEL, "Barlow-B", c_tel),
        y_tel + c_tel * CAP_BARLOW)

    # --- numero e zona sulla stessa linea di base, da un margine all'altro:
    # senza piu' l'indirizzo scritto e' questa riga a reggere i due assi
    c.setFont("Barlow-SB", 8.0)
    c.setFillColor(MATITA)
    c.drawRightString(R, y_tel, ZONA)
    reg("zona", R - larghezza(ZONA, "Barlow-SB", 8.0), y_tel - 1.8, R,
        y_tel + 8.0 * CAP_BARLOW)

    rifinitura(c, "GABRIEL CALASI  ·  sobrio  ·  85 x 55 mm  ·  abbondanza 3 mm")
    c.showPage()
    return n, modulo


# ------------------------------------------------------------------ stampa


def stampa(nome_file, disegna, margine, sottotitolo):
    azzera()
    percorso = os.path.join(CARTELLA, nome_file)
    c = rl_canvas.Canvas(percorso, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Gabriel Calasi - biglietto da visita")
    c.setAuthor("Gabriel Calasi")
    c.setSubject("85x55 mm, lato unico, %s, abbondanza 3 mm" % sottotitolo)
    n, modulo = disegna(c)
    errori = verifica(margine)
    for e in errori:
        print("ERRORE [%s]: %s" % (sottotitolo, e))
    if errori:
        sys.exit(1)
    c.save()
    print("%-42s %d elementi | corpo min %.1f pt | QR %dx%d da %.2f mm"
          % (percorso, len(BOX), min(cp for _, cp in CORPI), n, n, modulo / mm))


stampa("gabriel-biglietto-scuro-stampa.pdf", scuro, MARGINE_SCURO, "scuro")
stampa("gabriel-biglietto-sobrio-stampa.pdf", sobrio, MARGINE_SOBRIO, "sobrio")
