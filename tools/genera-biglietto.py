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

Tre regole non negoziabili, verificate prima di salvare:
  - nessun testo sotto i 7,5 pt: un biglietto si legge in mano, non allo zoom;
  - niente fuori dai margini, niente sopra qualcos'altro;
  - almeno 2 mm di stacco fra due blocchi incolonnati.
"""

import os, sys, tempfile
import qrcode
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "biglietto"


def carica_font():
    """I caratteri del sito stanno in fonts/ come .woff2. Qui vengono riscritti
    in .ttf, che reportlab sa incorporare nel PDF: nessun font di sistema,
    nessuna sostituzione a sorpresa in tipografia."""
    from fontTools.ttLib import TTFont as FTFont
    tmp = tempfile.mkdtemp(prefix="biglietto-font-")
    for nome, sorgente in (("Anton", "Anton-400.woff2"),
                           ("Barlow", "Barlow-400.woff2"),
                           ("Barlow-SB", "Barlow-600.woff2"),
                           ("Barlow-B", "Barlow-700.woff2")):
        f = FTFont(os.path.join("fonts", sorgente))
        f.flavor = None
        dst = os.path.join(tmp, sorgente.replace(".woff2", ".ttf"))
        f.save(dst)
        pdfmetrics.registerFont(TTFont(nome, dst))


carica_font()

# ---------------------------------------------------------------- tavolozza
ANTRACITE = HexColor("#16181A")
ARANCIO   = HexColor("#F26522")
CARTA     = HexColor("#F3F0E9")
CHIARO    = HexColor("#FFFFFF")
FUMO      = HexColor("#A7ACB1")   # secondario sul fondo scuro
MATITA    = HexColor("#6B6660")   # secondario sulla carta
FILETTO   = HexColor("#CFC9BE")   # la riga di separazione, sulla carta

# ---------------------------------------------------------------- geometria
TRIM_W, TRIM_H = 85 * mm, 55 * mm
BLEED, MARK_ROOM = 3 * mm, 5 * mm
OFF = BLEED + MARK_ROOM
PAGE_W, PAGE_H = TRIM_W + 2 * OFF, TRIM_H + 2 * OFF

CAP_ANTON, CAP_BARLOW = 0.727, 0.72        # rapporto maiuscola/em


def bordi(margine):
    """Area di sicurezza per un dato margine, in coordinate di pagina."""
    return (OFF + margine, OFF + TRIM_W - margine,
            OFF + margine, OFF + TRIM_H - margine)


# ---------------------------------------------------------------- contenuto
NOME   = "GABRIEL CALASI"
RUOLO  = "Tuttofare per la casa"
LAVORI = ("Idraulica, caldaie e condizionatori",
          "Bagni, muratura, piastrelle e riparazioni")
TEL    = "320 417 7267"
ZONA   = "Milano e provincia"
SITO   = "gabriel-tuttofare.vercel.app"
URL    = "https://gabriel-tuttofare.vercel.app"

MINIMO = 7.5           # corpo minimo leggibile, in punti
ARIA = 2.0 * mm        # stacco minimo fra due blocchi incolonnati

# ---------------------------------------------------------------- strumenti

BOX, CORPI = [], []


def azzera():
    del BOX[:]
    del CORPI[:]


def reg(nome, x0, y0, x1, y1):
    BOX.append((nome, x0, y0, x1, y1))


def larghezza(testo, font, corpo, track=0.0):
    CORPI.append((testo[:26], corpo))
    return pdfmetrics.stringWidth(testo, font, corpo) + track * (len(testo) - 1)


def verifica(margine):
    """Si controlla con i numeri, non guardando l'anteprima."""
    L, R, B, T = bordi(margine)
    err = []
    for testo, corpo in CORPI:
        if corpo < MINIMO - .01:
            err.append("corpo %.1f pt sotto il minimo leggibile — '%s'" % (corpo, testo))
    for nome, x0, y0, x1, y1 in BOX:
        if x0 < L - .01 or x1 > R + .01 or y0 < B - .01 or y1 > T + .01:
            err.append("'%s' esce dall'area di sicurezza" % nome)
    for i in range(len(BOX)):
        for j in range(i + 1, len(BOX)):
            a, b = BOX[i], BOX[j]
            if a[1] < b[3] - .01 and b[1] < a[3] - .01:          # stessa colonna
                if a[2] < b[4] - .01 and b[2] < a[4] - .01:
                    err.append("'%s' e '%s' si sovrappongono" % (a[0], b[0]))
                else:
                    # non basta non toccarsi: sotto i 2 mm il biglietto sembra
                    # affollato anche se tecnicamente e' corretto
                    stacco = max(a[2], b[2]) - min(a[4], b[4])
                    if stacco < ARIA - .01:
                        err.append("'%s' e '%s' distano %.1f mm, meno dei %.1f minimi"
                                   % (a[0], b[0], stacco / mm, ARIA / mm))
    return err


def tracking(c, x, y, testo, font, corpo, colore, track, align="left"):
    """Le etichette in maiuscolo reggono solo se respirano."""
    w = larghezza(testo, font, corpo, track)
    if align == "right":
        x -= w
    c.setFont(font, corpo)
    c.setFillColor(colore)
    for ch in testo:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, corpo) + track
    return w


def marchio(c, x, y, s, segno=ANTRACITE):
    """Il marchio del sito: stesse proporzioni dell'SVG (viewBox 32),
    asse Y ribaltato per il PDF."""
    c.setFillColor(ARANCIO)
    c.roundRect(x, y, s, s, s * 7 / 32.0, stroke=0, fill=1)
    u = s / 32.0
    p = c.beginPath()
    p.moveTo(x + 8.5 * u, y + 9.4 * u)
    p.lineTo(x + 16.0 * u, y + 22.9 * u)
    p.lineTo(x + 23.5 * u, y + 9.4 * u)
    p.close()
    c.setFillColor(segno)
    c.drawPath(p, stroke=0, fill=1)


def qr_vettoriale(c, x, y, lato, dato):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    q.add_data(dato)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    u = lato / float(n)
    c.setFillColor(ANTRACITE)
    for r, riga in enumerate(m):
        cc = 0
        while cc < n:
            if riga[cc]:
                run = cc
                while run < n and riga[run]:
                    run += 1
                # moduli contigui fusi in un rettangolo solo: niente fessure
                # bianche quando la stampante interpola
                c.rect(x + cc * u, y + lato - (r + 1) * u, (run - cc) * u, u, stroke=0, fill=1)
                cc = run
            else:
                cc += 1
    return n, u


def sfondo(c, colore):
    """Il colore si ferma all'abbondanza: fuori resta carta bianca, e i
    crocini restano leggibili."""
    c.setFillColor(colore)
    c.rect(OFF - BLEED, OFF - BLEED, TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED, stroke=0, fill=1)


def rifinitura(c, didascalia):
    c.setStrokeColor(Color(0, 0, 0))
    c.setLineWidth(0.25)
    lung, stacco = 4 * mm, BLEED
    for x in (OFF, OFF + TRIM_W):
        for y in (OFF, OFF + TRIM_H):
            sx = -1 if x == OFF else 1
            sy = -1 if y == OFF else 1
            c.line(x, y + sy * stacco, x, y + sy * (stacco + lung))
            c.line(x + sx * stacco, y, x + sx * (stacco + lung), y)
    c.setFont("Barlow", 4.5)
    c.setFillColor(Color(.55, .55, .55))
    c.drawCentredString(PAGE_W / 2, 2.2 * mm, didascalia)


# ------------------------------------------------------------------- SCURO


MARGINE_SCURO = 5 * mm


def scuro(c):
    """Antracite pieno, nome in Anton: l'impianto che si fa notare."""
    L, R, B, T = bordi(MARGINE_SCURO)
    sfondo(c, ANTRACITE)

    # la tessera del QR. Su fondo scuro il codice andrebbe invertito, ma non
    # tutti i lettori reggono l'inversione: meglio aprire un chiaro, perche'
    # su carta stampata non si torna indietro.
    tess = 19.5 * mm
    tx, ty = R - tess, B
    c.setFillColor(CARTA)
    c.roundRect(tx, ty, tess, tess, 1.2 * mm, stroke=0, fill=1)
    pad = 1.8 * mm
    n, modulo = qr_vettoriale(c, tx + pad, ty + pad, tess - 2 * pad, URL)
    reg("tessera QR", tx, ty, tx + tess, ty + tess)

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

    y_tel = B + 9.6 * mm
    c.setFont("Anton", 25.0)
    c.setFillColor(CHIARO)
    c.drawString(L, y_tel, TEL)
    reg("telefono", L, y_tel, L + larghezza(TEL, "Anton", 25.0), y_tel + 25.0 * CAP_ANTON)

    y_zona = B + 5.0 * mm
    w = tracking(c, L, y_zona, ZONA.upper(), "Barlow-SB", 8.0, FUMO, 1.1)
    reg("zona", L, y_zona, L + w, y_zona + 8.0 * CAP_BARLOW)

    y_sito = B + 0.8 * mm
    c.setFont("Barlow", 7.6)
    c.setFillColor(FUMO)
    c.drawString(L, y_sito, SITO)
    reg("sito", L, y_sito - 1.5, L + larghezza(SITO, "Barlow", 7.6), y_sito + 7.6 * CAP_BARLOW)

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
    reg("QR", qx, qy, qx + lato, qy + lato)

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
    y_filo = B + 15.4 * mm
    c.setStrokeColor(FILETTO)
    c.setLineWidth(0.5)
    c.line(L, y_filo, R, y_filo)

    # --- il numero: qui il peso fa il lavoro che altrove faceva il corpo
    c_tel = 15.0
    y_tel = B + 8.4 * mm
    c.setFont("Barlow-B", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    reg("telefono", L, y_tel, L + larghezza(TEL, "Barlow-B", c_tel),
        y_tel + c_tel * CAP_BARLOW)

    # --- il piede tiene i due assi: la zona parte da sinistra, l'indirizzo
    # arriva a destra. Il QR sopra e l'indirizzo sotto reggono il margine
    # destro, che altrimenti resterebbe un bordo vuoto.
    y_piede = B + 1.4 * mm
    c.setFont("Barlow-SB", 8.0)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_piede, ZONA)
    reg("zona", L, y_piede - 1.8, L + larghezza(ZONA, "Barlow-SB", 8.0),
        y_piede + 8.0 * CAP_BARLOW)

    c.setFont("Barlow", 8.0)
    c.setFillColor(MATITA)
    c.drawRightString(R, y_piede, SITO)
    reg("indirizzo", R - larghezza(SITO, "Barlow", 8.0), y_piede - 1.8, R,
        y_piede + 8.0 * CAP_BARLOW)

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
