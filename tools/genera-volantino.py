# -*- coding: utf-8 -*-
"""TRACCIATO — volantino A6 di Gabriel Calasi.

A6 e' 105 x 148,5 mm: quattro A6 riempiono esattamente un A4, senza sfrido
e con due soli tagli dritti. Escono due file:

  volantino-a6-stampa.pdf        il singolo, con crocini, per la tipografia
  volantino-a4-4-per-foglio.pdf  il foglio A4 gia' impaginato con quattro

Scelta che decide tutto il resto: il fondo e' bianco e nessun colore arriva
al bordo. Non e' pigrizia, e' quello che rende il volantino stampabile
davvero. Una stampante da casa non arriva agli ultimi millimetri del foglio:
un fondo pieno uscirebbe con una cornice bianca storta e un taglio da
indovinare. Cosi' invece il margine che la stampante non copre e' carta
bianca comunque, il taglio puo' sbagliare di un paio di millimetri senza
che si veda, e l'inchiostro costa un quarto. Il colore sta dove serve:
la fascia scura del titolo e l'arancio, tutti e due dentro i margini.
"""

import os, sys
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color

from tracciato import (ANTRACITE, ARANCIO, CHIARO, MATITA, FILETTO, CAP_BARLOW,
                       NOME, RUOLO, CLAIM, ELENCO, STORIA, PROMESSA, TEL, ZONA,
                       carica_font, azzera, reg, larghezza, verifica, BOX, CORPI,
                       tracking, marchio, qr_vettoriale, crocini, didascalia)

CARTELLA = sys.argv[1] if len(sys.argv) > 1 else "biglietto"
carica_font()

# ---------------------------------------------------------------- geometria
A6_W, A6_H = 105 * mm, 148.5 * mm
A4_W, A4_H = 210 * mm, 297 * mm
MARGINE = 9 * mm
STACCO = 4 * mm            # spazio per i crocini attorno al singolo A6
MIN_VOLANTINO = 8.0        # su un volantino si puo' stare piu' larghi che su un biglietto


def disegna(c, ox, oy, registra=False):
    """Il volantino, con l'angolo in basso a sinistra in (ox, oy).

    Registra gli ingombri una volta sola: le quattro copie del foglio A4
    sono lo stesso disegno, verificarlo quattro volte non aggiunge niente.
    """
    def R_(nome, x0, y0, x1, y1):
        if registra:
            reg(nome, x0, y0, x1, y1)

    L, R = ox + MARGINE, ox + A6_W - MARGINE
    B, T = oy + MARGINE, oy + A6_H - MARGINE

    # --- la fascia del titolo: scura, ma dentro i margini. Da' il colpo
    # d'occhio senza chiedere alla stampante di arrivare al bordo.
    fascia = 26.0 * mm
    fy = T - fascia
    c.setFillColor(ANTRACITE)
    c.rect(L, fy, R - L, fascia, stroke=0, fill=1)
    R_("fascia", L, fy, R, T)

    s = 12.0 * mm
    marchio(c, L + 6 * mm, fy + (fascia - s) / 2, s)

    x_id = L + 6 * mm + s + 5 * mm
    c_nome = 15.0
    y_nome = fy + fascia / 2 + 0.6 * mm
    tracking(c, x_id, y_nome, NOME, "Barlow-B", c_nome, CHIARO, 1.0)
    c.setFont("Barlow", 10.0)
    c.setFillColor(ARANCIO)
    c.drawString(x_id, fy + fascia / 2 - 5.4 * mm, RUOLO)
    larghezza(RUOLO, "Barlow", 10.0)

    # --- il titolo: la promessa, non il nome. E' la riga che ferma la mano
    # di chi sta buttando la posta.
    c_claim = 19.0
    y_claim = fy - 8.0 * mm - c_claim * CAP_BARLOW
    c.setFont("Barlow-B", c_claim)
    c.setFillColor(ANTRACITE)
    for i, riga in enumerate(CLAIM):
        c.drawString(L, y_claim - i * 8.4 * mm, riga)
    R_("titolo", L, y_claim - (len(CLAIM) - 1) * 8.4 * mm - 2.2,
       L + max(larghezza(r, "Barlow-B", c_claim) for r in CLAIM),
       y_claim + c_claim * CAP_BARLOW)

    y_sotto = y_claim - (len(CLAIM) - 1) * 8.4 * mm
    y_filo = y_sotto - 6.4 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(1.1)
    c.line(L, y_filo, L + 22 * mm, y_filo)

    # --- che cosa fa: elenco puntato, perche' un volantino si scorre
    c_voce, passo = 10.0, 5.8 * mm
    y_voce = y_filo - 7.6 * mm
    for i, voce in enumerate(ELENCO):
        y = y_voce - i * passo
        c.setFillColor(ARANCIO)
        c.rect(L, y + 0.8 * mm, 1.9 * mm, 1.9 * mm, stroke=0, fill=1)
        c.setFont("Barlow", c_voce)
        c.setFillColor(ANTRACITE)
        c.drawString(L + 5.2 * mm, y, voce)
    R_("elenco", L, y_voce - (len(ELENCO) - 1) * passo - 2.2,
       L + 5.2 * mm + max(larghezza(v, "Barlow", c_voce) for v in ELENCO),
       y_voce + c_voce * CAP_BARLOW)

    # --- il QR sta di fianco all'elenco, non in fondo: laggiu' rubava la
    # larghezza al numero, che e' la cosa che deve restare piu' grande
    lato = 21.0 * mm
    # il codice parte dalla stessa quota della prima voce: due blocchi
    # affiancati che cominciano allineati si leggono come una cosa voluta
    qx, qy = R - lato, y_voce + c_voce * CAP_BARLOW - lato
    n, modulo = qr_vettoriale(c, qx, qy, lato)
    y_did = qy - 3.5 * mm
    c.setFont("Barlow-SB", 8.5)
    c.setFillColor(MATITA)
    c.drawCentredString(qx + lato / 2, y_did, "Il sito")
    larghezza("Il sito", "Barlow-SB", 8.5)
    R_("QR", qx, y_did - 2.0, qx + lato, qy + lato)

    # --- perche' lui: il pezzo che rende credibile l'elenco qui sopra
    c_storia, passo_s = 9.0, 4.4 * mm
    y_storia = y_voce - (len(ELENCO) - 1) * passo - 9.9 * mm
    c.setFont("Barlow", c_storia)
    c.setFillColor(MATITA)
    for i, riga in enumerate(STORIA):
        c.drawString(L, y_storia - i * passo_s, riga)
    R_("storia", L, y_storia - (len(STORIA) - 1) * passo_s - 2.0,
       L + max(larghezza(r, "Barlow", c_storia) for r in STORIA),
       y_storia + c_storia * CAP_BARLOW)

    # --- il filetto, da margine a margine: sotto c'e' solo come chiamarlo
    y_taglio = B + 21.5 * mm
    c.setStrokeColor(FILETTO)
    c.setLineWidth(0.6)
    c.line(L, y_taglio, R, y_taglio)

    # --- il numero e' la cosa piu' grande della pagina dopo il titolo:
    # e' l'unica azione che si chiede a chi legge
    y_prom = B + 16.0 * mm
    c.setFont("Barlow-SB", 10.0)
    c.setFillColor(ARANCIO)
    c.drawString(L, y_prom, PROMESSA)
    R_("promessa", L, y_prom - 2.2, L + larghezza(PROMESSA, "Barlow-SB", 10.0),
       y_prom + 10.0 * CAP_BARLOW)

    c_tel = 26.0
    y_tel = B + 5.4 * mm
    c.setFont("Barlow-B", c_tel)
    c.setFillColor(ANTRACITE)
    c.drawString(L, y_tel, TEL)
    R_("telefono", L, y_tel, L + larghezza(TEL, "Barlow-B", c_tel),
       y_tel + c_tel * CAP_BARLOW)

    c.setFont("Barlow-SB", 9.0)
    c.setFillColor(MATITA)
    y_zona = B + 0.9 * mm
    c.drawString(L, y_zona, ZONA)
    R_("zona", L, y_zona - 2.0, L + larghezza(ZONA, "Barlow-SB", 9.0),
       y_zona + 9.0 * CAP_BARLOW)

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
    L, R, B, T = STACCO + MARGINE, STACCO + A6_W - MARGINE, STACCO + MARGINE, STACCO + A6_H - MARGINE
    errori = verifica(L, R, B, T, minimo=MIN_VOLANTINO)
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
print("  %d elementi | corpo min %.1f pt | QR %dx%d da %.2f mm"
      % (len(BOX), min(cp for _, cp in CORPI), n, n, modulo / mm))
