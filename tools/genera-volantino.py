# -*- coding: utf-8 -*-
"""TRACCIATO — volantino A6 di Gabriel Calasi.

A6 e' 105 x 148,5 mm: quattro A6 riempiono esattamente un A4, senza sfrido
e con due soli tagli dritti. Escono due file:

  volantino-a6-stampa.pdf        il singolo, con crocini, per la tipografia
  volantino-a4-4-per-foglio.pdf  il foglio A4 gia' impaginato con quattro

Le fotografie sono quelle del sito, ritagliate qui al formato che serve:
una fascia larga in alto con le mani al lavoro, e tre miniature che fanno
vedere i mestieri invece di limitarsi a elencarli.

Il fondo resta bianco e niente arriva al bordo del foglio, fotografie
comprese. Una stampante da casa non copre gli ultimi millimetri: un'immagine
al vivo uscirebbe con una cornice bianca storta e un taglio da indovinare.
Cosi' invece il margine non stampabile e' carta bianca comunque, e il taglio
puo' sbagliare di due millimetri senza che si veda.
"""

import os, sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from PIL import Image

from tracciato import (ANTRACITE, ARANCIO, CHIARO, MATITA, CAP_BARLOW,
                       NOME, RUOLO, CLAIM, ELENCO, STORIA, PROMESSA, TEL, ZONA,
                       carica_font, azzera, reg, larghezza, verifica, BOX, CORPI,
                       tracking, marchio, qr_vettoriale, crocini, didascalia)

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "biglietto"
carica_font()

A6_W, A6_H = 105 * mm, 148.5 * mm
A4_W, A4_H = 210 * mm, 297 * mm
MARGINE = 9 * mm
STACCO = 4 * mm            # spazio per i crocini attorno al singolo A6
MIN_VOLANTINO = 8.0        # su un volantino si sta piu' larghi che su un biglietto
DPI_STAMPA = 300

FASCIA = "img/cta.jpg"
MINIATURE = ("img/serv-idraulica.jpg", "img/serv-bagno.jpg", "img/serv-piastrelle.jpg")

_cache = {}


def foto(c, percorso, x, y, w, h):
    """Ritaglia al centro sul formato richiesto e disegna a 300 dpi.

    Il ritaglio si fa qui e non nel PDF: chiedere a reportlab di adattare
    l'immagine la schiaccerebbe, e le persone storte si notano subito.
    """
    chiave = (percorso, round(w, 2), round(h, 2))
    if chiave not in _cache:
        im = Image.open(percorso)
        iw, ih = im.size
        voluto = w / float(h)
        if iw / float(ih) > voluto:                 # troppo larga: taglio i fianchi
            nuova = int(round(ih * voluto))
            im = im.crop(((iw - nuova) // 2, 0, (iw - nuova) // 2 + nuova, ih))
        else:                                       # troppo alta: taglio sopra e sotto
            nuova = int(round(iw / voluto))
            im = im.crop((0, (ih - nuova) // 2, iw, (ih - nuova) // 2 + nuova))
        px = int(round(w / mm / 25.4 * DPI_STAMPA))
        _cache[chiave] = ImageReader(im.resize((px, int(round(px / voluto))), Image.LANCZOS))
    c.drawImage(_cache[chiave], x, y, w, h)


def disegna(c, ox, oy, registra=False):
    """Il volantino, con l'angolo in basso a sinistra in (ox, oy).

    Registra gli ingombri una volta sola: le quattro copie sul foglio A4
    sono lo stesso disegno, verificarlo quattro volte non aggiunge niente.
    """
    def R_(nome, x0, y0, x1, y1):
        if registra:
            reg(nome, x0, y0, x1, y1)

    L, R = ox + MARGINE, ox + A6_W - MARGINE
    B, T = oy + MARGINE, oy + A6_H - MARGINE
    larg = R - L

    # --- la fascia fotografica: le mani al lavoro, non un fondo colorato.
    # E' la prima cosa che si vede e dice il mestiere senza una parola.
    h_foto = 28 * mm
    foto(c, FASCIA, L, T - h_foto, larg, h_foto)

    # --- sotto, la fascia scura con il marchio: aggancia la foto al marchio
    h_bar = 16 * mm
    by = T - h_foto - h_bar
    c.setFillColor(ANTRACITE)
    c.rect(L, by, larg, h_bar, stroke=0, fill=1)
    # foto e fascia sono attaccate di proposito: sono una testata sola, non
    # due blocchi da distanziare
    R_("testata", L, by, R, T)

    s = 10.0 * mm
    marchio(c, L + 4.5 * mm, by + (h_bar - s) / 2, s)
    x_id = L + 4.5 * mm + s + 4.2 * mm
    tracking(c, x_id, by + h_bar / 2 + 0.5 * mm, NOME, "Barlow-B", 13.5, CHIARO, 0.9)
    c.setFont("Barlow", 9.0)
    c.setFillColor(ARANCIO)
    c.drawString(x_id, by + h_bar / 2 - 4.4 * mm, RUOLO)
    larghezza(RUOLO, "Barlow", 9.0)

    # --- il titolo: la promessa, non il nome. E' la riga che ferma la mano
    # di chi sta buttando la posta.
    c_claim, passo_claim = 17.0, 7.2 * mm
    y_claim = by - 5.0 * mm - c_claim * CAP_BARLOW
    c.setFont("Barlow-B", c_claim)
    c.setFillColor(ANTRACITE)
    for i, riga in enumerate(CLAIM):
        c.drawString(L, y_claim - i * passo_claim, riga)
    R_("titolo", L, y_claim - (len(CLAIM) - 1) * passo_claim - 2.2,
       L + max(larghezza(r, "Barlow-B", c_claim) for r in CLAIM),
       y_claim + c_claim * CAP_BARLOW)

    y_sotto = y_claim - (len(CLAIM) - 1) * passo_claim
    y_storia = y_sotto - 5.2 * mm
    c.setFont("Barlow", 8.6)
    c.setFillColor(MATITA)
    c.drawString(L, y_storia, STORIA)
    R_("mestiere", L, y_storia - 2.0, L + larghezza(STORIA, "Barlow", 8.6),
       y_storia + 8.6 * CAP_BARLOW)

    y_filo = y_storia - 4.8 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(1.1)
    c.line(L, y_filo, L + 22 * mm, y_filo)

    y_prom = y_filo - 4.6 * mm
    c.setFont("Barlow-SB", 9.5)
    c.setFillColor(ARANCIO)
    c.drawString(L, y_prom, PROMESSA)
    R_("promessa", L, y_prom - 2.2, L + larghezza(PROMESSA, "Barlow-SB", 9.5),
       y_prom + 9.5 * CAP_BARLOW)

    # --- che cosa fa: elenco puntato, perche' un volantino si scorre
    c_voce, passo = 9.5, 5.0 * mm
    y_voce = y_prom - 7.0 * mm
    for i, voce in enumerate(ELENCO):
        y = y_voce - i * passo
        c.setFillColor(ARANCIO)
        c.rect(L, y + 0.7 * mm, 1.8 * mm, 1.8 * mm, stroke=0, fill=1)
        c.setFont("Barlow", c_voce)
        c.setFillColor(ANTRACITE)
        c.drawString(L + 4.8 * mm, y, voce)
    R_("elenco", L, y_voce - (len(ELENCO) - 1) * passo - 2.1,
       L + 4.8 * mm + max(larghezza(v, "Barlow", c_voce) for v in ELENCO),
       y_voce + c_voce * CAP_BARLOW)

    # --- il codice parte dalla stessa quota della prima voce: due blocchi
    # affiancati che cominciano allineati si leggono come una cosa voluta
    lato = 20.0 * mm
    qx, qy = R - lato, y_voce + c_voce * CAP_BARLOW - lato
    n, modulo = qr_vettoriale(c, qx, qy, lato)
    y_did = qy - 3.2 * mm
    c.setFont("Barlow-SB", 8.0)
    c.setFillColor(MATITA)
    c.drawCentredString(qx + lato / 2, y_did, "Il sito")
    larghezza("Il sito", "Barlow-SB", 8.0)
    R_("QR", qx, y_did - 2.0, qx + lato, qy + lato)

    # --- tre miniature: i mestieri si fanno vedere, non solo elencare
    h_min, gap = 15 * mm, 3 * mm
    w_min = (larg - 2 * gap) / 3.0
    y_min = B + 9.0 * mm
    for i, img in enumerate(MINIATURE):
        foto(c, img, L + i * (w_min + gap), y_min, w_min, h_min)
    R_("miniature", L, y_min, R, y_min + h_min)

    # --- come chiamarlo. Il numero e' la cosa piu' grande della pagina
    # dopo il titolo: e' l'unica azione che si chiede a chi legge.
    c_tel = 22.0
    y_tel = B + 0.8 * mm
    c.setFont("Barlow-B", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    R_("telefono", L, y_tel, L + larghezza(TEL, "Barlow-B", c_tel),
       y_tel + c_tel * CAP_BARLOW)

    c.setFont("Barlow-SB", 9.0)
    c.setFillColor(MATITA)
    c.drawRightString(R, y_tel + 1.2 * mm, ZONA)
    R_("zona", R - larghezza(ZONA, "Barlow-SB", 9.0), y_tel + 1.2 * mm - 2.0, R,
       y_tel + 1.2 * mm + 9.0 * CAP_BARLOW)

    return n, modulo


# ------------------------------------------------------------------ stampa


def singolo(percorso):
    """Il volantino da solo, con i crocini attorno: quello per la tipografia."""
    azzera()
    pw, ph = A6_W + 2 * STACCO, A6_H + 2 * STACCO
    c = rl_canvas.Canvas(percorso, pagesize=(pw, ph))
    c.setTitle("Gabriel Calasi - volantino")
    c.setAuthor("Gabriel Calasi")
    c.setSubject("A6, 105x148,5 mm, lato unico")
    n, modulo = disegna(c, STACCO, STACCO, registra=True)
    crocini(c, STACCO, STACCO, A6_W, A6_H, 0)
    didascalia(c, pw / 2, 1.6 * mm, "GABRIEL CALASI  ·  volantino A6  ·  105 x 148,5 mm")
    errori = verifica(STACCO + MARGINE, STACCO + A6_W - MARGINE,
                      STACCO + MARGINE, STACCO + A6_H - MARGINE, minimo=MIN_VOLANTINO)
    for e in errori:
        print("ERRORE:", e)
    if errori:
        sys.exit(1)
    c.save()
    return n, modulo


def quattro_su_a4(percorso):
    """Quattro copie che riempiono l'A4. Le linee di taglio cadono nel bianco
    fra un volantino e l'altro, quindi si puo' tagliare anche con le forbici
    senza intaccare la stampa."""
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
print("  %d elementi | corpo min %.1f pt | QR %dx%d da %.2f mm | %d fotografie"
      % (len(BOX), min(cp for _, cp in CORPI), n, n, modulo / mm, 1 + len(MINIATURE)))
