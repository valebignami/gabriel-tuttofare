# -*- coding: utf-8 -*-
"""TRACCIATO — biglietto da visita di Gabriel Calasi.

Un solo lato, 85x55 mm, abbondanza 3 mm, crocini di taglio.
Caratteri e colori sono quelli del sito: carta e schermo dicono la stessa cosa.

Tre regole non negoziabili, verificate dal programma prima di salvare:
  - nessun testo sotto i 7,5 pt, perche' un biglietto si legge in mano
    e non allo zoom;
  - niente fuori dai margini, niente sopra qualcos'altro;
  - niente che invada la colonna del QR.
"""

import os, sys, tempfile
import qrcode
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "biglietto/gabriel-biglietto-stampa.pdf"


def carica_font():
    """I caratteri del sito stanno in fonts/ come .woff2. Qui vengono riscritti
    in .ttf, che reportlab sa incorporare nel PDF: nessun font di sistema,
    nessuna sostituzione a sorpresa in tipografia."""
    from fontTools.ttLib import TTFont as FTFont
    tmp = tempfile.mkdtemp(prefix="biglietto-font-")
    for nome, sorgente in (("Anton", "Anton-400.woff2"),
                           ("Barlow", "Barlow-400.woff2"),
                           ("Barlow-SB", "Barlow-600.woff2")):
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
FUMO      = HexColor("#A7ACB1")   # secondario sul fondo scuro, schiarito per leggere

# ---------------------------------------------------------------- geometria
TRIM_W, TRIM_H = 85 * mm, 55 * mm
BLEED, MARK_ROOM = 3 * mm, 5 * mm
OFF = BLEED + MARK_ROOM
PAGE_W, PAGE_H = TRIM_W + 2 * OFF, TRIM_H + 2 * OFF
SAFE = 5 * mm

L, R = OFF + SAFE, OFF + TRIM_W - SAFE        # colonne
B, T = OFF + SAFE, OFF + TRIM_H - SAFE        # piede e cielo
CAP = 0.727                                   # rapporto maiuscola/em di Anton

# ---------------------------------------------------------------- contenuto
NOME   = "GABRIEL CALASI"
RUOLO  = "TUTTOFARE PER LA CASA"
LAVORI = ("Idraulica, caldaie e condizionatori",
          "Bagni, muratura, piastrelle e riparazioni")
TEL    = "320 417 7267"
ZONA   = "MILANO E PROVINCIA"
SITO   = "gabriel-tuttofare.vercel.app"
URL    = "https://gabriel-tuttofare.vercel.app"

# ------------------------------------------------- scala tipografica (punti)
# Sotto i 7,5 pt un biglietto non si legge in mano: da li' in su si sale.
C_NOME, C_TEL     = 23.0, 25.0        # Anton, le due voci alte
C_RUOLO, C_LAVORI = 8.0, 8.0
C_ZONA, C_SITO    = 8.0, 7.6
MINIMO = 7.5
ARIA = 2.0 * mm        # stacco minimo fra due blocchi incolonnati

# ---------------------------------------------------------------- strumenti

BOX, CORPI = [], []


def reg(nome, x0, y0, x1, y1):
    BOX.append((nome, x0, y0, x1, y1))


def larghezza(testo, font, corpo, track=0.0):
    CORPI.append((testo[:24], corpo))
    return pdfmetrics.stringWidth(testo, font, corpo) + track * (len(testo) - 1)


def verifica():
    """Si controlla con i numeri, non guardando l'anteprima."""
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


def tracking(c, x, y, testo, font, corpo, colore, track):
    """Le etichette in maiuscolo reggono solo se respirano."""
    w = larghezza(testo, font, corpo, track)
    c.setFont(font, corpo)
    c.setFillColor(colore)
    for ch in testo:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, corpo) + track
    return w


def marchio(c, x, y, s):
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
    c.setFillColor(ANTRACITE)
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


def crocini(c):
    c.setStrokeColor(Color(0, 0, 0))
    c.setLineWidth(0.25)
    lung, stacco = 4 * mm, BLEED
    for x in (OFF, OFF + TRIM_W):
        for y in (OFF, OFF + TRIM_H):
            sx = -1 if x == OFF else 1
            sy = -1 if y == OFF else 1
            c.line(x, y + sy * stacco, x, y + sy * (stacco + lung))
            c.line(x + sx * stacco, y, x + sx * (stacco + lung), y)


# ------------------------------------------------------------- composizione


def biglietto(c):
    # il colore si ferma all'abbondanza: fuori resta carta bianca, e i crocini
    # restano leggibili
    c.setFillColor(ANTRACITE)
    c.rect(OFF - BLEED, OFF - BLEED, TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED, stroke=0, fill=1)

    # --- la tessera del QR. Su fondo scuro il codice andrebbe invertito, ma non
    # tutti i lettori reggono l'inversione: meglio aprire un chiaro e dormire
    # tranquilli, perche' su carta stampata non si torna indietro.
    tess = 19.5 * mm
    tx, ty = R - tess, B
    c.setFillColor(CARTA)
    c.roundRect(tx, ty, tess, tess, 1.2 * mm, stroke=0, fill=1)
    pad = 1.8 * mm
    n, modulo = qr_vettoriale(c, tx + pad, ty + pad, tess - 2 * pad, URL)
    reg("tessera QR", tx, ty, tx + tess, ty + tess)

    # --- fascia alta: marchio e nome per esteso, sulla stessa linea di base
    s = 8.4 * mm
    marchio(c, L, T - s, s)
    reg("marchio", L, T - s, L + s, T)

    x_nome = L + s + 3.4 * mm
    y_nome = T - s + 1.4 * mm
    c.setFont("Anton", C_NOME)
    c.setFillColor(CHIARO)
    c.drawString(x_nome, y_nome, NOME)
    reg("nome", x_nome, y_nome, x_nome + larghezza(NOME, "Anton", C_NOME),
        y_nome + C_NOME * CAP)

    # --- il tracciato: un filetto e basta. L'arancio non riempie mai.
    y_linea = T - 13.2 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(0.7)
    c.line(L, y_linea, R, y_linea)

    # --- il mestiere, e sotto in che cosa consiste
    y_ruolo = y_linea - 4.2 * mm
    w = tracking(c, L, y_ruolo, RUOLO, "Barlow-SB", C_RUOLO, ARANCIO, 1.5)
    reg("ruolo", L, y_ruolo, L + w, y_ruolo + C_RUOLO * .73)

    y_lav = y_ruolo - 4.8 * mm
    c.setFont("Barlow", C_LAVORI)
    c.setFillColor(FUMO)
    interlinea = 3.7 * mm
    for i, riga in enumerate(LAVORI):
        c.drawString(L, y_lav - i * interlinea, riga)
    # le righe di uno stesso paragrafo sono un blocco solo: fra loro vale
    # l'interlinea, non lo stacco fra blocchi
    reg("lavori", L, y_lav - (len(LAVORI) - 1) * interlinea - 1.7,
        L + max(larghezza(r, "Barlow", C_LAVORI) for r in LAVORI),
        y_lav + C_LAVORI * .73)

    # --- il numero: l'unica cosa che deve leggersi da lontano
    y_tel = B + 9.6 * mm
    c.setFont("Anton", C_TEL)
    c.setFillColor(CHIARO)
    c.drawString(L, y_tel, TEL)
    reg("telefono", L, y_tel, L + larghezza(TEL, "Anton", C_TEL), y_tel + C_TEL * CAP)

    # --- zona e indirizzo, appoggiati al piede
    y_zona = B + 5.0 * mm
    w = tracking(c, L, y_zona, ZONA, "Barlow-SB", C_ZONA, FUMO, 1.1)
    reg("zona", L, y_zona, L + w, y_zona + C_ZONA * .73)

    y_sito = B + 0.8 * mm
    c.setFont("Barlow", C_SITO)
    c.setFillColor(FUMO)
    c.drawString(L, y_sito, SITO)
    reg("sito", L, y_sito - 1.5, L + larghezza(SITO, "Barlow", C_SITO),
        y_sito + C_SITO * .73)

    crocini(c)
    c.setFont("Barlow", 4.5)
    c.setFillColor(Color(.55, .55, .55))
    c.drawCentredString(PAGE_W / 2, 2.2 * mm,
                        "GABRIEL CALASI  ·  85 x 55 mm  ·  abbondanza 3 mm  ·  lato unico")
    c.showPage()
    return n, modulo


c = rl_canvas.Canvas(OUT, pagesize=(PAGE_W, PAGE_H))
c.setTitle("Gabriel Calasi - biglietto da visita")
c.setAuthor("Gabriel Calasi")
c.setSubject("85x55 mm, lato unico, abbondanza 3 mm")
n, modulo = biglietto(c)

errori = verifica()
for e in errori:
    print("ERRORE:", e)
if errori:
    sys.exit(1)

c.save()
print("scritto: %s" % OUT)
print("  %d elementi | nessuna collisione, nessuno sconfinamento" % len(BOX))
print("  corpo minimo %.1f pt | QR %d x %d moduli da %.2f mm"
      % (min(cp for _, cp in CORPI), n, n, modulo / mm))
