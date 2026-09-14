# -*- coding: utf-8 -*-
"""MANO FERMA — volantino A6 di Gabriel Calasi.

A6 e' 105 x 148,5 mm: quattro riempiono esattamente un A4, senza sfrido e con
due soli tagli dritti. Escono due file, il singolo con i crocini e il foglio
gia' impaginato.

L'IMPIANTO. La versione precedente impilava nove fasce orizzontali tutte
larghe uguale: ordinata, e per questo invisibile. Qui comanda un gesto solo.
Una fotografia grande occupa la parte alta. Un blocco antracite le appoggia
sopra l'angolo in basso a sinistra e scende oltre il suo bordo, cucendo la
zona dell'immagine a quella del testo: e' lo scavalco che toglie alla pagina
il ritmo dell'elenco. Il blocco non arriva al margine destro, dove una
seconda immagine piu' piccola continua la colonna e tiene la composizione
fuori asse. Sotto, campo bianco: elenco a sinistra, codice a destra, e il
numero di telefono come seconda voce alta.

Il titolo sta dentro il blocco scuro in Anton, il carattere da insegna del
sito, montato su tre righe con interlinea stretta perche' diventi una forma
prima ancora che una frase. E' l'unico punto in cui questo carattere serve
davvero: un volantino e' un manifesto in miniatura.

LA STAMPA. Niente arriva al bordo del foglio, fotografie comprese. Una
stampante da casa non copre gli ultimi millimetri: un'immagine al vivo
uscirebbe con una cornice bianca storta e un taglio da indovinare. Cosi'
invece il margine non stampabile e' carta bianca comunque, e il taglio puo'
sbagliare di due millimetri senza che si veda. I margini non sono pero'
uguali su tutti i lati: quello inferiore e' piu' largo, come vuole l'occhio.
"""

import os, sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from PIL import Image

from tracciato import (ANTRACITE, ARANCIO, CHIARO, MATITA, CAP_ANTON, CAP_BARLOW,
                       NOME, ELENCO, STORIA, PROMESSA, TEL, ZONA,
                       carica_font, azzera, reg, larghezza, verifica, BOX, CORPI,
                       tracking, marchio, qr_vettoriale, crocini, didascalia)

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "biglietto"
carica_font()

A6_W, A6_H = 105 * mm, 148.5 * mm
A4_W, A4_H = 210 * mm, 297 * mm
STACCO = 4 * mm            # spazio per i crocini attorno al singolo A6
DPI_STAMPA = 300
MIN_VOLANTINO = 8.0

# I margini non sono uguali: quello basso e' piu' largo perche' un margine
# inferiore uguale agli altri, otticamente, sembra piu' stretto.
M_SX, M_DX, M_ALTO, M_BASSO = 8 * mm, 8 * mm, 8 * mm, 10 * mm

TITOLO = ("UN SOLO", "PROFESSIONISTA", "PER TUTTA LA CASA")

# I lavori come righe puntate invece che come elenco a cinque voci: un elenco
# verticale rifa' la pila che si voleva togliere, e su un volantino le voci si
# scorrono, non si leggono una per una.
SERVIZI = ("Idraulica · Caldaie · Condizionatori",
           "Bagni · Muratura · Piastrelle",
           "Riparazioni · Tinteggiatura")
# Il ritratto vero al posto di uno scorcio di lavoro: su un volantino
# una faccia vale piu' di un dettaglio, e il formato e' gia' il suo.
FOTO = "img/cta.jpg"

_cache = {}


def foto(c, percorso, x, y, w, h, riquadro=None):
    """Ritaglia sul formato richiesto e disegna a 300 dpi.

    Il ritaglio si fa qui e non lo si lascia al PDF: adattare l'immagine al
    riquadro la schiaccerebbe, e una cosa storta si nota subito.

    `riquadro` e' la porzione da usare, in frazioni di lato (sinistra, alto,
    destra, basso). Serve quando il centro geometrico non e' il soggetto:
    in un ritratto a figura intera il volto sta in alto, e prendere il centro
    significa consegnare una faccia grande tre millimetri."""
    chiave = (percorso, round(w, 2), round(h, 2), riquadro)
    if chiave not in _cache:
        im = Image.open(percorso)
        if riquadro:
            iw, ih = im.size
            a, b, cc, d = riquadro
            im = im.crop((int(a * iw), int(b * ih), int(cc * iw), int(d * ih)))
        iw, ih = im.size
        voluto = w / float(h)
        if iw / float(ih) > voluto:
            nuova = int(round(ih * voluto))
            im = im.crop(((iw - nuova) // 2, 0, (iw - nuova) // 2 + nuova, ih))
        else:
            nuova = int(round(iw / voluto))
            im = im.crop((0, (ih - nuova) // 2, iw, (ih - nuova) // 2 + nuova))
        px = int(round(w / mm / 25.4 * DPI_STAMPA))
        _cache[chiave] = ImageReader(im.resize((px, int(round(px / voluto))), Image.LANCZOS))
    c.drawImage(_cache[chiave], x, y, w, h)


def riga_puntata(c, x, y, testo, corpo):
    """Una riga di voci separate dal punto medio, con i punti in arancio.

    I separatori colorati danno ritmo alla riga senza aggiungere un solo
    elemento alla composizione: e' il colore a fare il lavoro dello spazio."""
    from reportlab.pdfbase import pdfmetrics
    inizio = x
    for i, pezzo in enumerate(testo.split(" · ")):
        if i:
            c.setFont("Barlow-SB", corpo)
            c.setFillColor(ARANCIO)
            c.drawString(x, y, "·")
            x += pdfmetrics.stringWidth("·", "Barlow-SB", corpo) + 1.6 * mm
        c.setFont("Barlow", corpo)
        c.setFillColor(ANTRACITE)
        c.drawString(x, y, pezzo)
        x += pdfmetrics.stringWidth(pezzo, "Barlow", corpo) + 1.6 * mm
    larghezza(testo, "Barlow", corpo)
    return x - inizio - 1.6 * mm


def corpo_che_entra(testi, font, largh, lo=6.0, hi=90.0):
    """Il corpo massimo che tiene la riga piu' lunga dentro la larghezza.
    Binaria, non a occhio."""
    from reportlab.pdfbase import pdfmetrics
    for _ in range(60):
        mid = (lo + hi) / 2
        if max(pdfmetrics.stringWidth(t, font, mid) for t in testi) <= largh:
            lo = mid
        else:
            hi = mid
    return lo


def disegna(c, ox, oy, registra=False):
    """Il volantino, con l'angolo in basso a sinistra in (ox, oy)."""
    def R_(nome, x0, y0, x1, y1):
        if registra:
            reg(nome, x0, y0, x1, y1)

    L, R = ox + M_SX, ox + A6_W - M_DX
    B, T = oy + M_BASSO, oy + A6_H - M_ALTO

    # ---------------------------------------------------- il gesto: la foto
    # Occupa la parte alta e non la divide a meta': prende piu' della meta',
    # perche' una superficie divisa in due parti uguali non sceglie niente.
    y_foto = oy + 70 * mm
    foto(c, FOTO, L, y_foto, R - L, T - y_foto)

    R_("fotografia", L, y_foto, R, T)

    # ------------------------------------------- lo scavalco: blocco scuro
    # Appoggia sull'angolo della fotografia e scende oltre il suo bordo:
    # cuce la zona dell'immagine a quella del testo e rompe il ritmo a fasce.
    bx0, bx1 = L, ox + 67 * mm
    by0, by1 = oy + 56 * mm, oy + 92 * mm
    c.setFillColor(ANTRACITE)
    c.rect(bx0, by0, bx1 - bx0, by1 - by0, stroke=0, fill=1)
    R_("blocco", bx0, by0, bx1, by1)

    pad = 5.5 * mm
    ix0, ix1 = bx0 + pad, bx1 - pad

    s = 6.6 * mm
    y_m = by1 - 3.2 * mm - s
    marchio(c, ix0, y_m, s)
    tracking(c, ix0 + s + 3.0 * mm, y_m + (s - 8.0 * .72) / 2 + 0.3 * mm,
             NOME, "Barlow-SB", 8.0, ARANCIO, 1.2)

    # il titolo: tre righe strette, che si leggono come una forma
    c_tit = min(28.0, corpo_che_entra(TITOLO, "Anton", ix1 - ix0))
    passo = c_tit * CAP_ANTON + 2.0 * mm
    y_tit = by0 + pad + (len(TITOLO) - 1) * passo
    c.setFont("Anton", c_tit)
    c.setFillColor(CHIARO)
    for i, riga in enumerate(TITOLO):
        c.drawString(ix0, y_tit - i * passo, riga)
        larghezza(riga, "Anton", c_tit)

    # ------------------------------------------------- il campo bianco
    # Tre gruppi separati, non una pila sola: che cosa fa, poi il filetto,
    # poi come si chiama. Il raggruppamento e' la gerarchia.
    c_serv, passo_s = 8.6, 4.6 * mm
    y_serv = by0 - 3.6 * mm - c_serv * CAP_BARLOW
    largo = 0
    for i, riga in enumerate(SERVIZI):
        largo = max(largo, riga_puntata(c, L, y_serv - i * passo_s, riga, c_serv))
    R_("servizi", L, y_serv - (len(SERVIZI) - 1) * passo_s - 2.0, L + largo,
       y_serv + c_serv * CAP_BARLOW)

    # il codice sta in basso a destra e fa da contrappeso al numero, che pesa
    # in basso a sinistra: sotto il filetto la pagina ha due appoggi, non uno
    lato = 19.0 * mm
    y_did = oy + 11.0 * mm                     # stessa linea di base della zona
    qx, qy = R - lato, y_did + 3.0 * mm
    n, modulo = qr_vettoriale(c, qx, qy, lato)
    c.setFont("Barlow-SB", 8.0)
    c.setFillColor(MATITA)
    c.drawCentredString(qx + lato / 2, y_did, "Il sito")
    larghezza("Il sito", "Barlow-SB", 8.0)
    R_("QR", qx, y_did - 2.0, qx + lato, qy + lato)

    # il filetto divide che cosa fa da come si chiama, e si ferma prima della
    # colonna del codice
    y_filo = 34.5 * mm + oy
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(0.8)
    c.line(L, y_filo, ox + 68 * mm, y_filo)

    y_prom = y_filo - 5.4 * mm
    c.setFont("Barlow-SB", 9.0)
    c.setFillColor(ARANCIO)
    c.drawString(L, y_prom, PROMESSA)
    R_("promessa", L, y_prom - 2.1, L + larghezza(PROMESSA, "Barlow-SB", 9.0),
       y_prom + 9.0 * CAP_BARLOW)

    c_tel = 30.0
    y_tel = oy + 16.5 * mm
    c.setFont("Anton", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    R_("telefono", L, y_tel, L + larghezza(TEL, "Anton", c_tel), y_tel + c_tel * CAP_ANTON)

    c.setFont("Barlow-SB", 8.6)
    c.setFillColor(MATITA)
    y_zona = oy + 11.0 * mm
    c.drawString(L, y_zona, ZONA)
    R_("zona", L, y_zona - 2.0, L + larghezza(ZONA, "Barlow-SB", 8.6),
       y_zona + 8.6 * CAP_BARLOW)

    return n, modulo


# ------------------------------------------------------------------ stampa


def singolo(percorso):
    azzera()
    pw, ph = A6_W + 2 * STACCO, A6_H + 2 * STACCO
    c = rl_canvas.Canvas(percorso, pagesize=(pw, ph))
    c.setTitle("Gabriel Calasi - volantino")
    c.setAuthor("Gabriel Calasi")
    c.setSubject("A6, 105x148,5 mm, lato unico")
    n, modulo = disegna(c, STACCO, STACCO, registra=True)
    crocini(c, STACCO, STACCO, A6_W, A6_H, 0)
    didascalia(c, pw / 2, 1.6 * mm, "GABRIEL CALASI  ·  volantino A6  ·  105 x 148,5 mm")
    errori = verifica(STACCO + M_SX, STACCO + A6_W - M_DX,
                      STACCO + M_BASSO, STACCO + A6_H - M_ALTO, minimo=MIN_VOLANTINO,
                      ammesse=(("blocco", "fotografia"),))    # lo scavalco e' il progetto
    for e in errori:
        print("ERRORE:", e)
    if errori:
        sys.exit(1)
    c.save()
    return n, modulo


def quattro_su_a4(percorso):
    """Le linee di taglio cadono nel bianco fra un volantino e l'altro: si
    puo' tagliare con le forbici senza intaccare la stampa."""
    c = rl_canvas.Canvas(percorso, pagesize=(A4_W, A4_H))
    c.setTitle("Gabriel Calasi - volantini, 4 per foglio A4")
    c.setAuthor("Gabriel Calasi")
    c.setSubject("A4 con quattro volantini A6 da ritagliare")
    for ox in (0, A6_W):
        for oy in (0, A6_H):
            disegna(c, ox, oy)
    c.setStrokeColor(Color(.72, .72, .72))
    c.setLineWidth(0.3)
    c.line(A6_W, 0, A6_W, A4_H)
    c.line(0, A6_H, A4_W, A6_H)
    c.save()


n, modulo = singolo(os.path.join(CARTELLA, "volantino-a6-stampa.pdf"))
quattro_su_a4(os.path.join(CARTELLA, "volantino-a4-4-per-foglio.pdf"))
print("volantino A6 + foglio A4 con quattro copie")
print("  %d blocchi | corpo min %.1f pt | QR %dx%d da %.2f mm"
      % (len(BOX), min(cp for _, cp in CORPI), n, n, modulo / mm))
