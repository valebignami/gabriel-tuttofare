# -*- coding: utf-8 -*-
"""MANO FERMA — volantino A6 di Gabriel Calasi.

A6 e' 105 x 148,5 mm: quattro riempiono esattamente un A4, con due tagli
dritti. Escono il singolo con i crocini e il foglio gia' impaginato.

L'IMPIANTO. Quattro masse, dall'alto in basso, e nient'altro:

  1. una riga d'intestazione sottile, marchio e nome;
  2. la fotografia, larga il doppio della sua altezza;
  3. un campo antracite che occupa un terzo della pagina e porta il titolo
     in Anton piu' i mestieri in maiuscoletto spaziato;
  4. la zona bianca dell'azione: la promessa, il numero, la zona, il codice.

Le versioni precedenti avevano due difetti che tornavano a ogni giro. Il
primo: righe di testo piccole lasciate galleggiare da sole su fondo bianco,
senza un campo che le contenesse — sembravano avanzi. Ora ogni testo sta
dentro una massa. Il secondo: vuoti sparsi in piu' punti, che leggono come
buchi. Ora il vuoto e' concentrato nelle due fasce d'aria fra le masse, dove
si legge come respiro.

I CORPI, per la stampa a dimensione reale:
  titolo Anton 28 pt · numero Anton 30 pt · mestieri 9 pt maiuscoletto
  promessa 9,5 pt · nome 8,5 pt · zona e didascalia 8,6 pt
Nessun testo sotto gli 8 pt: su un volantino A6, letto a mezzo braccio,
sotto quella soglia le parole si chiudono.

LA STAMPA. Niente arriva al bordo del foglio, fotografia e campo scuro
compresi: una stampante da casa non copre gli ultimi millimetri, e un
elemento al vivo uscirebbe con una cornice bianca storta. Il margine non
stampabile resta carta bianca comunque, e il taglio puo' sbagliare di due
millimetri senza che si veda.
"""

import os, sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from PIL import Image

from tracciato import (ANTRACITE, ARANCIO, CHIARO, FUMO, MATITA, CAP_ANTON, CAP_BARLOW,
                       NOME, RUOLO, PROMESSA, TEL, ZONA,
                       carica_font, azzera, reg, larghezza, verifica, BOX, CORPI,
                       tracking, marchio, qr_vettoriale, crocini, didascalia)

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "stampati"
carica_font()

A6_W, A6_H = 105 * mm, 148.5 * mm
A4_W, A4_H = 210 * mm, 297 * mm
STACCO = 4 * mm
DPI_STAMPA = 300
MIN_VOLANTINO = 8.0

M_SX, M_DX, M_ALTO, M_BASSO = 8 * mm, 8 * mm, 8 * mm, 10 * mm

TITOLO = ("UN SOLO", "PROFESSIONISTA", "PER TUTTA LA CASA")
# Due righe, non sette voci: su un volantino la lista lunga non si legge e
# costringe a un corpo che in stampa si chiude.
MESTIERI = ("IDRAULICA · CALDAIE · CONDIZIONATORI",
            "BAGNI · MURATURA · PIASTRELLE")
FOTO = "img/cta.jpg"

_cache = {}


def foto(c, percorso, x, y, w, h):
    """Ritaglia al centro sul formato richiesto e disegna a 300 dpi. Il
    ritaglio si fa qui: adattare l'immagine al riquadro la schiaccerebbe."""
    chiave = (percorso, round(w, 2), round(h, 2))
    if chiave not in _cache:
        im = Image.open(percorso)
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


def corpo_che_entra(testi, font, largh, track=0.0, tetto=90.0):
    """Il corpo massimo che tiene la riga piu' lunga dentro la larghezza.
    Binaria, non a occhio: e' l'unico modo perche' un titolo composto da
    parole diverse non esca dal campo che lo contiene."""
    lo, hi = 6.0, tetto
    for _ in range(60):
        mid = (lo + hi) / 2
        peggio = max(pdfmetrics.stringWidth(t, font, mid) + track * (len(t) - 1) for t in testi)
        if peggio <= largh:
            lo = mid
        else:
            hi = mid
    return lo


def riga_mestieri(c, x, y, testo, corpo, track):
    """Maiuscoletto spaziato con i punti di separazione in arancio: il ritmo
    della riga lo fa il colore, senza aggiungere elementi alla pagina."""
    for ch in testo:
        c.setFont("Barlow-SB", corpo)
        c.setFillColor(ARANCIO if ch == "·" else CHIARO)
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, "Barlow-SB", corpo) + track
    larghezza(testo, "Barlow-SB", corpo)


def disegna(c, ox, oy, registra=False):
    def R_(nome, x0, y0, x1, y1):
        if registra:
            reg(nome, x0, y0, x1, y1)

    L, R = ox + M_SX, ox + A6_W - M_DX
    B, T = oy + M_BASSO, oy + A6_H - M_ALTO
    larg = R - L

    # ------------------------------------------- 1. l'intestazione sottile
    s = 7.0 * mm
    marchio(c, L, T - s, s)
    tracking(c, L + s + 3.2 * mm, T - s + (s - 8.5 * CAP_BARLOW) / 2 + 0.2 * mm,
             NOME, "Barlow-SB", 8.5, ANTRACITE, 1.1)
    c.setFont("Barlow", 8.5)
    c.setFillColor(MATITA)
    c.drawRightString(R, T - s + (s - 8.5 * CAP_BARLOW) / 2 + 0.2 * mm, RUOLO)
    larghezza(RUOLO, "Barlow", 8.5)
    R_("intestazione", L, T - s, R, T)

    # ------------------------------------------------- 2. la fotografia
    # Larga il doppio dell'altezza: un rapporto deciso si legge come una
    # scelta, uno qualunque si legge come un ritaglio capitato.
    y_foto, h_foto = oy + 89 * mm, 40 * mm
    foto(c, FOTO, L, y_foto, larg, h_foto)
    R_("fotografia", L, y_foto, R, y_foto + h_foto)

    # -------------------------------------------------- 3. il campo scuro
    # Un terzo della pagina. Il testo non galleggia sul bianco: sta dentro
    # una massa, ed e' la massa a dargli peso.
    cy0, cy1 = oy + 34 * mm, oy + 83 * mm
    c.setFillColor(ANTRACITE)
    c.rect(L, cy0, larg, cy1 - cy0, stroke=0, fill=1)
    R_("campo", L, cy0, R, cy1)

    pad = 5.5 * mm
    ix0, ix1 = L + pad, R - pad

    c_tit = min(28.0, corpo_che_entra(TITOLO, "Anton", ix1 - ix0))
    passo_tit = c_tit * CAP_ANTON + 2.2 * mm
    y_tit = cy1 - pad - c_tit * CAP_ANTON
    c.setFont("Anton", c_tit)
    c.setFillColor(CHIARO)
    for i, riga in enumerate(TITOLO):
        c.drawString(ix0, y_tit - i * passo_tit, riga)
        larghezza(riga, "Anton", c_tit)
    R_("titolo", ix0, y_tit - (len(TITOLO) - 1) * passo_tit,
       ix0 + max(larghezza(r, "Anton", c_tit) for r in TITOLO),
       y_tit + c_tit * CAP_ANTON)

    c_mest, passo_m = min(9.0, corpo_che_entra(MESTIERI, "Barlow-SB", ix1 - ix0, track=0.55)), 4.6 * mm
    y_mest = cy0 + pad + (len(MESTIERI) - 1) * passo_m + 0.2 * mm
    for i, riga in enumerate(MESTIERI):
        riga_mestieri(c, ix0, y_mest - i * passo_m, riga, c_mest, 0.55)
    R_("mestieri", ix0, y_mest - (len(MESTIERI) - 1) * passo_m - 2.0,
       ix0 + max(larghezza(r, "Barlow-SB", c_mest, 0.55) for r in MESTIERI),
       y_mest + c_mest * CAP_BARLOW)

    # ---------------------------------------------- 4. la zona dell'azione
    y_prom = oy + 28.0 * mm
    c.setFont("Barlow-SB", 9.5)
    c.setFillColor(ARANCIO)
    c.drawString(L, y_prom, PROMESSA)
    R_("promessa", L, y_prom - 2.1, L + larghezza(PROMESSA, "Barlow-SB", 9.5),
       y_prom + 9.5 * CAP_BARLOW)

    c_tel = 30.0
    y_tel = oy + 15.8 * mm
    c.setFont("Anton", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    R_("telefono", L, y_tel, L + larghezza(TEL, "Anton", c_tel), y_tel + c_tel * CAP_ANTON)

    y_base = oy + 10.9 * mm            # l'ultima riga corre da un margine all'altro
    c.setFont("Barlow-SB", 8.6)
    c.setFillColor(MATITA)
    c.drawString(L, y_base, ZONA)
    R_("zona", L, y_base - 2.0, L + larghezza(ZONA, "Barlow-SB", 8.6),
       y_base + 8.6 * CAP_BARLOW)

    lato = 18.0 * mm
    qx, qy = R - lato, y_base + 3.1 * mm
    n, modulo = qr_vettoriale(c, qx, qy, lato)
    c.setFont("Barlow-SB", 8.6)
    c.setFillColor(MATITA)
    c.drawCentredString(qx + lato / 2, y_base, "Il sito")
    larghezza("Il sito", "Barlow-SB", 8.6)
    R_("QR", qx, y_base - 2.0, qx + lato, qy + lato)

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
                      # il testo dentro il campo e' il progetto; fra titolo e
                      # mestieri invece lo stacco va rispettato, ed e' li' che
                      # la versione precedente sovrapponeva senza accorgersene
                      ammesse=(("campo", "titolo"), ("campo", "mestieri")))
    for e in errori:
        print("ERRORE:", e)
    if errori:
        sys.exit(1)
    c.save()
    return n, modulo


def quattro_su_a4(percorso):
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
print("  %d masse | corpo min %.1f pt | QR %dx%d da %.2f mm"
      % (len(BOX), min(cp for _, cp in CORPI), n, n, modulo / mm))
