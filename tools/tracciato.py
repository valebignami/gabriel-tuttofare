# -*- coding: utf-8 -*-
"""TRACCIATO — strumenti comuni agli stampati di Gabriel Calasi.

Tavolozza, caratteri, marchio, QR vettoriale e le verifiche che ogni
stampato deve superare prima di essere salvato. Biglietti e volantini
importano da qui: una tavolozza sola, un marchio solo, e le correzioni
valgono per tutti invece di dover essere ricopiate.
"""

import os, tempfile
import qrcode
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ---------------------------------------------------------------- tavolozza
ANTRACITE = HexColor("#16181A")
ARANCIO   = HexColor("#F26522")
CARTA     = HexColor("#F3F0E9")
CHIARO    = HexColor("#FFFFFF")
FUMO      = HexColor("#A7ACB1")   # secondario sul fondo scuro
MATITA    = HexColor("#6B6660")   # secondario sulla carta
FILETTO   = HexColor("#B5AC9D")   # separatore: al 16% di contrasto spariva in stampa

CAP_ANTON, CAP_BARLOW = 0.727, 0.72        # rapporto maiuscola/em

# ---------------------------------------------------------------- contenuto
NOME   = "GABRIEL CALASI"
RUOLO  = "Tuttofare per la casa"
CLAIM  = ("Un solo professionista", "per tutta la casa")
LAVORI = ("Idraulica, caldaie e condizionatori",
          "Bagni, muratura, piastrelle e riparazioni")
ELENCO = ("Idraulica, caldaie e condizionatori",
          "Bagni e ristrutturazioni",
          "Muratura e cartongesso",
          "Piastrelle e pavimenti",
          "Riparazioni e tinteggiatura")
STORIA = ("Vent'anni di cantiere: muratore, capo",
          "squadra, poi idraulico. Chi chiama tre",
          "ditte diverse, di solito, le fa litigare.")
PROMESSA = "Sopralluogo e preventivo gratuiti"
TEL    = "320 417 7267"
ZONA   = "Milano e provincia"
URL    = "https://gabriel-tuttofare.vercel.app"

MINIMO = 7.5           # corpo minimo leggibile su uno stampato da mano
ARIA = 2.0 * mm        # stacco minimo fra due blocchi incolonnati


def carica_font():
    """I caratteri del sito stanno in fonts/ come .woff2. Qui vengono riscritti
    in .ttf, che reportlab sa incorporare nel PDF: nessun font di sistema,
    nessuna sostituzione a sorpresa in tipografia."""
    from fontTools.ttLib import TTFont as FTFont
    tmp = tempfile.mkdtemp(prefix="tracciato-font-")
    for nome, sorgente in (("Anton", "Anton-400.woff2"),
                           ("Barlow", "Barlow-400.woff2"),
                           ("Barlow-SB", "Barlow-600.woff2"),
                           ("Barlow-B", "Barlow-700.woff2")):
        f = FTFont(os.path.join("fonts", sorgente))
        f.flavor = None
        dst = os.path.join(tmp, sorgente.replace(".woff2", ".ttf"))
        f.save(dst)
        pdfmetrics.registerFont(TTFont(nome, dst))


# ------------------------------------------------------------- le verifiche

BOX, CORPI = [], []


def azzera():
    del BOX[:]
    del CORPI[:]


def reg(nome, x0, y0, x1, y1):
    """Ogni elemento dichiara il suo ingombro: si verifica, non si spera."""
    BOX.append((nome, x0, y0, x1, y1))


def larghezza(testo, font, corpo, track=0.0):
    CORPI.append((testo[:26], corpo))
    return pdfmetrics.stringWidth(testo, font, corpo) + track * (len(testo) - 1)


def verifica(L, R, B, T, minimo=MINIMO, aria=ARIA):
    """Si controlla con i numeri, non guardando l'anteprima."""
    err = []
    for testo, corpo in CORPI:
        if corpo < minimo - .01:
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
                    # non basta non toccarsi: sotto i 2 mm lo stampato sembra
                    # affollato anche se tecnicamente e' corretto
                    stacco = max(a[2], b[2]) - min(a[4], b[4])
                    if stacco < aria - .01:
                        err.append("'%s' e '%s' distano %.1f mm, meno dei %.1f minimi"
                                   % (a[0], b[0], stacco / mm, aria / mm))
    return err


# -------------------------------------------------------------- il disegno


def tracking(c, x, y, testo, font, corpo, colore, track, align="left"):
    """Le etichette in maiuscolo reggono solo se respirano."""
    w = larghezza(testo, font, corpo, track)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2.0
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


def qr_vettoriale(c, x, y, lato, dato=URL, scuro=ANTRACITE):
    """Disegnato in vettoriale, non incollato come immagine: resta nitido a
    qualsiasi risoluzione di stampa. Restituisce moduli e lato del modulo,
    perche' sotto i 0,4 mm un codice non si legge piu'."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    q.add_data(dato)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    u = lato / float(n)
    c.setFillColor(scuro)
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


def crocini(c, x0, y0, larg, alt, stacco, lung=4 * mm, spess=0.25):
    """Fuori dall'abbondanza: il taglierino sa dove fermarsi."""
    c.setStrokeColor(Color(0, 0, 0))
    c.setLineWidth(spess)
    for x in (x0, x0 + larg):
        for y in (y0, y0 + alt):
            sx = -1 if x == x0 else 1
            sy = -1 if y == y0 else 1
            c.line(x, y + sy * stacco, x, y + sy * (stacco + lung))
            c.line(x + sx * stacco, y, x + sx * (stacco + lung), y)


def didascalia(c, x, y, testo, corpo=4.5):
    c.setFont("Barlow", corpo)
    c.setFillColor(Color(.55, .55, .55))
    c.drawCentredString(x, y, testo)
