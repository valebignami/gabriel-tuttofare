# -*- coding: utf-8 -*-
"""TRACCIATO — biglietto da visita, Gabriel Calasi.
Due pagine (fronte/retro), 85x55 mm, abbondanza 3 mm, crocini di taglio.
QR disegnato in vettoriale: nitido a qualsiasi risoluzione."""

import os, sys, tempfile
import qrcode
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "biglietto"   # cartella di uscita


def carica_font():
    """I caratteri del biglietto sono gli stessi del sito, presi da fonts/.
    Sul web sono .woff2: qui vengono riscritti in .ttf, che reportlab sa
    incorporare nel PDF. Nessun font di sistema, nessuna sostituzione."""
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
# grigi ricavati dai due estremi: nessun terzo colore entra nella tavolozza
FUMO      = HexColor("#8A8F94")   # testo secondario sul fondo scuro
MATITA    = HexColor("#6E6A64")   # testo secondario sulla carta

# ---------------------------------------------------------------- geometria
TRIM_W, TRIM_H = 85 * mm, 55 * mm
BLEED, MARK_ROOM = 3 * mm, 5 * mm
OFF = BLEED + MARK_ROOM                       # origine del taglio nella pagina
PAGE_W, PAGE_H = TRIM_W + 2 * OFF, TRIM_H + 2 * OFF
SAFE = 6 * mm                                 # margine di sicurezza dal taglio

URL   = "https://gabriel-tuttofare.vercel.app"
SITO  = "gabriel-tuttofare.vercel.app"
TEL   = "320 417 7267"

# ---------------------------------------------------------------- strumenti

BOX = []            # ogni elemento dichiara il suo ingombro: si verifica, non si spera


def reg(pagina, nome, x0, y0, x1, y1):
    BOX.append((pagina, nome, x0, y0, x1, y1))


def verifica():
    """Nessun elemento esce dall'area di sicurezza, nessuno tocca un altro.
    Non e' negoziabile: si controlla con i numeri, non guardando l'anteprima."""
    errori = []
    sx, sy = OFF + SAFE, OFF + SAFE
    dx, dy = OFF + TRIM_W - SAFE, OFF + TRIM_H - SAFE
    for pag, nome, x0, y0, x1, y1 in BOX:
        if x0 < sx - .01 or x1 > dx + .01 or y0 < sy - .01 or y1 > dy + .01:
            errori.append("%s/%s esce dall'area di sicurezza" % (pag, nome))
    for i in range(len(BOX)):
        for j in range(i + 1, len(BOX)):
            a, b = BOX[i], BOX[j]
            if a[0] != b[0]:
                continue
            if a[2] < b[4] - .01 and b[2] < a[4] - .01 and a[3] < b[5] - .01 and b[3] < a[5] - .01:
                errori.append("%s: '%s' e '%s' si sovrappongono" % (a[0], a[1], b[1]))
    return errori


def tracking(c, x, y, text, font, size, color, track, align="left"):
    """Testo spaziato a mano: le etichette minute reggono solo se respirano."""
    c.setFont(font, size)
    widths = [c.stringWidth(ch, font, size) for ch in text]
    total = sum(widths) + track * (len(text) - 1)
    if align == "right":
        x -= total
    elif align == "center":
        x -= total / 2
    c.setFillColor(color)
    for ch, w in zip(text, widths):
        c.drawString(x, y, ch)
        x += w + track
    return total


def fit_font(c, text, font, target_w, lo=6, hi=200):
    """Corpo massimo che tiene il testo entro target_w. Binaria, non a occhio."""
    for _ in range(60):
        mid = (lo + hi) / 2
        if c.stringWidth(text, font, mid) <= target_w:
            lo = mid
        else:
            hi = mid
    return lo


def marchio(c, x, y, s, fondo=ARANCIO, segno=ANTRACITE):
    """Il marchio del sito: quadrato arrotondato, triangolo pieno. Stesse
    proporzioni dell'SVG (viewBox 32), asse Y ribaltato per il PDF."""
    c.saveState()
    c.setFillColor(fondo)
    c.roundRect(x, y, s, s, s * 7 / 32.0, stroke=0, fill=1)
    u = s / 32.0
    p = c.beginPath()
    p.moveTo(x + 8.5 * u, y + 9.4 * u)
    p.lineTo(x + 16.0 * u, y + 22.9 * u)
    p.lineTo(x + 23.5 * u, y + 9.4 * u)
    p.close()
    c.setFillColor(segno)
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def tacche(c, x0, y0, x1, y1, colore, lung=2.2 * mm, spess=0.25):
    """Tacche di registro agli angoli dell'area utile: il tracciato che il
    muratore non cancella, perche e' la prova che la parete e' a piombo."""
    c.saveState()
    c.setStrokeColor(colore)
    c.setLineWidth(spess)
    c.setLineCap(0)
    for x, y, dx, dy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        c.line(x, y, x + dx * lung, y)
        c.line(x, y, x, y + dy * lung)
    c.restoreState()


def qr_vettoriale(c, x, y, lato, dato, scuro=ANTRACITE):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    q.add_data(dato)
    q.make(fit=True)
    m = q.get_matrix()
    n = len(m)
    u = lato / float(n)
    c.saveState()
    c.setFillColor(scuro)
    for r, riga in enumerate(m):
        cc = 0
        while cc < n:
            if riga[cc]:
                run = cc
                while run < n and riga[run]:
                    run += 1
                # moduli contigui fusi in un unico rettangolo: niente fessure
                # bianche fra i pixel quando la stampante interpola
                c.rect(x + cc * u, y + lato - (r + 1) * u, (run - cc) * u, u, stroke=0, fill=1)
                cc = run
            else:
                cc += 1
    c.restoreState()
    return n


def fondo(c, colore):
    """Il colore arriva fino all'abbondanza e non oltre: cosi' i crocini
    restano leggibili sulla carta bianca, come vuole la prestampa."""
    c.setFillColor(colore)
    c.rect(OFF - BLEED, OFF - BLEED, TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED, stroke=0, fill=1)


def crocini(c):
    """Fuori dall'abbondanza: il taglierino sa dove fermarsi."""
    c.saveState()
    c.setStrokeColor(Color(0, 0, 0))
    c.setLineWidth(0.25)
    lung, stacco = 4 * mm, BLEED
    for x in (OFF, OFF + TRIM_W):
        for y in (OFF, OFF + TRIM_H):
            sx = -1 if x == OFF else 1
            sy = -1 if y == OFF else 1
            c.line(x, y + sy * stacco, x, y + sy * (stacco + lung))
            c.line(x + sx * stacco, y, x + sx * (stacco + lung), y)
    c.setFont("Barlow", 4)
    c.setFillColor(Color(.45, .45, .45))
    c.restoreState()


def slug(c, testo):
    c.saveState()
    c.setFont("Barlow", 4)
    c.setFillColor(Color(.55, .55, .55))
    c.drawCentredString(PAGE_W / 2, 2.2 * mm, testo)
    c.restoreState()


# ---------------------------------------------------------------- il fronte


def fronte(c):
    fondo(c, ANTRACITE)

    L = OFF + SAFE                     # colonna sinistra
    R = OFF + TRIM_W - SAFE            # colonna destra
    B = OFF + SAFE                     # piede dell'area utile
    T = OFF + TRIM_H - SAFE            # cielo dell'area utile
    larg = R - L

    tacche(c, L, B, R, T, HexColor("#2C2F33"))

    # --- fascia alta: marchio a sinistra, territorio a destra, stessa linea ottica
    s = 7.4 * mm
    y_mark = T - s
    marchio(c, L, y_mark, s)
    y_terr = y_mark + s / 2 - 1.0 * mm
    w_terr = tracking(c, R, y_terr, "MILANO E PROVINCIA",
                      "Barlow-SB", 5.0, FUMO, 1.15, align="right")
    reg("fronte", "territorio", R - w_terr, y_terr, R, y_terr + 5.0 * .73)

    # --- la voce alta: una parola sola. Il corpo nasce dall'altezza voluta,
    # non dalla larghezza disponibile: e' l'altezza a governare il respiro.
    CAP = 0.727                                   # rapporto maiuscola/em di Anton
    alt_voluta = 10.4 * mm
    corpo = min(alt_voluta / CAP, fit_font(c, "GABRIEL", "Anton", larg))
    alt = corpo * CAP
    base = B + 17.4 * mm
    c.setFont("Anton", corpo)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(L, base, "GABRIEL")
    reg("fronte", "marchio", L, y_mark, L + s, y_mark + s)
    reg("fronte", "wordmark", L, base, L + c.stringWidth("GABRIEL", "Anton", corpo), base + alt)

    # --- il tracciato: un filetto e basta. L'arancio non riempie mai.
    y_linea = base - 4.0 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(0.6)
    c.line(L, y_linea, R, y_linea)

    y_claim = y_linea - 3.5 * mm
    w_claim = tracking(c, L, y_claim, "TUTTOFARE PER LA CASA", "Barlow-SB", 5.4, ARANCIO, 1.45)
    reg("fronte", "claim", L, y_claim, L + w_claim, y_claim + 5.4 * .73)

    # --- il numero: chi trova il biglietto sul bancone non deve girarlo
    c_tel = 14.0
    c.setFont("Anton", c_tel)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(L, B + 0.4 * mm, TEL)
    reg("fronte", "telefono", L, B + 0.4 * mm, L + c.stringWidth(TEL, "Anton", c_tel),
        B + 0.4 * mm + c_tel * CAP)

    # --- etichetta WhatsApp, appesa al filetto che la sottolinea
    et = "ANCHE WHATSAPP"
    y_et = B + 2.0 * mm
    w = tracking(c, R, y_et, et, "Barlow-SB", 5.0, FUMO, 1.15, align="right")
    c.setStrokeColor(HexColor("#3A3E42"))
    c.setLineWidth(0.4)
    c.line(R - w, y_et - 1.6 * mm, R, y_et - 1.6 * mm)
    reg("fronte", "whatsapp", R - w, y_et - 1.6 * mm, R, y_et + 1.4 * mm)

    crocini(c)
    slug(c, "GABRIEL CALASI  ·  fronte  ·  85 x 55 mm  ·  abbondanza 3 mm")
    c.showPage()


# ----------------------------------------------------------------- il retro


def retro(c):
    fondo(c, CARTA)

    L = OFF + SAFE
    R = OFF + TRIM_W - SAFE
    T = OFF + TRIM_H - SAFE

    tacche(c, L, OFF + SAFE, R, T, HexColor("#D8D3C9"))

    B = OFF + SAFE

    # QR in alto a destra: scuro su chiaro, il solo verso che legge sempre
    lato = 18.6 * mm
    qx, qy = R - lato, T - lato
    n = qr_vettoriale(c, qx, qy, lato, URL)
    reg("retro", "qr", qx, qy, qx + lato, qy + lato)

    # colonna sinistra: chi e', e cosa fa. Larghezza chiusa dal QR.
    col = qx - L - 5 * mm
    c.setFont("Anton", 10.6)
    c.setFillColor(ANTRACITE)
    y_nome = T - 3.4 * mm
    c.drawString(L, y_nome, "GABRIEL CALASI")
    reg("retro", "nome", L, y_nome, L + c.stringWidth("GABRIEL CALASI", "Anton", 10.6),
        y_nome + 10.6 * .727)

    y_mest = T - 7.3 * mm
    w_mest = tracking(c, L, y_mest, "IDRAULICO  ·  MURATORE", "Barlow-SB", 5.3, ARANCIO, 1.35)
    reg("retro", "mestiere", L, y_mest, L + w_mest, y_mest + 5.3 * .73)

    voci = ["Idraulica, caldaie e condizionatori",
            "Bagni e ristrutturazioni",
            "Muratura e cartongesso",
            "Piastrelle e pavimenti",
            "Riparazioni e tinteggiatura"]
    c.setFont("Barlow", 6.4)
    c.setFillColor(MATITA)
    y = T - 12.4 * mm
    w_voci = max(c.stringWidth(v, "Barlow", 6.4) for v in voci)
    for v in voci:
        c.drawString(L, y, v)
        y -= 3.15 * mm
    reg("retro", "servizi", L, y + 3.15 * mm - 1.4, L + w_voci, T - 12.4 * mm + 6.4 * .73)

    # sotto il QR, l'indirizzo in chiaro: il codice non e' l'unica via d'accesso
    y_sito = qy - 3.1 * mm
    tracking(c, qx + lato, y_sito, "IL SITO", "Barlow-SB", 4.7, ARANCIO, 1.2, align="right")
    c.setFont("Barlow", 5.0)
    c.setFillColor(MATITA)
    c.drawRightString(qx + lato, qy - 6.1 * mm, SITO)
    reg("retro", "indirizzo", qx + lato - c.stringWidth(SITO, "Barlow", 5.0),
        qy - 6.1 * mm - 1.2, qx + lato, y_sito + 4.7 * .73)

    # la fascia centrale non e' un avanzo: ci sta la frase che regge il sito
    y_frase = B + 11.0 * mm
    c.setFont("Barlow", 7.4)
    c.setFillColor(ANTRACITE)
    frase = "Un solo professionista per tutta la casa."
    c.drawString(L, y_frase, frase)
    reg("retro", "frase", L, y_frase - 1.3, L + c.stringWidth(frase, "Barlow", 7.4),
        y_frase + 7.4 * .73)

    # piede: il filetto regge la promessa commerciale
    y_linea = B + 5.6 * mm
    c.setStrokeColor(HexColor("#D8D3C9"))
    c.setLineWidth(0.5)
    c.line(L, y_linea, R, y_linea)

    c.setFont("Barlow-SB", 7.6)
    c.setFillColor(ANTRACITE)
    c.drawString(L, B + 1.0 * mm, TEL)
    reg("retro", "telefono", L, B + 1.0 * mm - 1.2,
        L + c.stringWidth(TEL, "Barlow-SB", 7.6), B + 1.0 * mm + 7.6 * .73)

    y_prom = B + 1.35 * mm
    w_prom = tracking(c, R, y_prom, "SOPRALLUOGO E PREVENTIVO GRATUITI",
                      "Barlow", 4.9, MATITA, 0.85, align="right")
    reg("retro", "promessa", R - w_prom, y_prom, R, y_prom + 4.9 * .73)

    crocini(c)
    slug(c, "GABRIEL CALASI  ·  retro  ·  85 x 55 mm  ·  abbondanza 3 mm")
    c.showPage()


# ------------------------------------------------------------ il lato unico


def lato_unico(c):
    """Un solo lato non e' il fronte col retro buttato via: e' una terza
    composizione, dove QR e contatti devono rientrare davanti senza che
    la voce alta perda il suo respiro."""
    fondo(c, ANTRACITE)

    L, R = OFF + SAFE, OFF + TRIM_W - SAFE
    B, T = OFF + SAFE, OFF + TRIM_H - SAFE
    CAP = 0.727

    tacche(c, L, B, R, T, HexColor("#2C2F33"))

    # --- il QR vuole il suo chiaro: su fondo scuro si apre una tessera di carta.
    # Invertirlo costerebbe meno spazio ma non tutti i lettori lo reggono, e un
    # codice che non legge manda al macero l'intera tiratura.
    lap = 22.0 * mm
    px, py = R - lap, T - lap
    c.setFillColor(CARTA)
    c.roundRect(px, py, lap, lap, 1.2 * mm, stroke=0, fill=1)
    pad = 2.0 * mm
    qr_vettoriale(c, px + pad, py + pad, lap - 2 * pad, URL)
    reg("solo", "tessera-qr", px, py, px + lap, py + lap)

    # --- fascia alta: il marchio, e accanto il territorio. La destra e' occupata.
    s = 7.2 * mm
    y_mark = T - s
    marchio(c, L, y_mark, s)
    reg("solo", "marchio", L, y_mark, L + s, y_mark + s)
    x_terr = L + s + 3.0 * mm
    y_terr = y_mark + s / 2 - 1.0 * mm
    w_terr = tracking(c, x_terr, y_terr, "MILANO E PROVINCIA", "Barlow-SB", 5.0, FUMO, 1.15)
    reg("solo", "territorio", x_terr, y_terr, x_terr + w_terr, y_terr + 5.0 * .73)

    # --- la voce alta, contenuta dalla tessera: l'altezza governa, la
    # larghezza disponibile fa solo da tetto
    corpo = min(8.8 * mm / CAP, fit_font(c, "GABRIEL", "Anton", px - L - 5.0 * mm))
    base = B + 24.0 * mm
    c.setFont("Anton", corpo)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(L, base, "GABRIEL")
    reg("solo", "wordmark", L, base, L + c.stringWidth("GABRIEL", "Anton", corpo),
        base + corpo * CAP)

    # --- il tracciato passa sotto la tessera e tiene insieme i due blocchi
    y_linea = B + 20.0 * mm
    c.setStrokeColor(ARANCIO)
    c.setLineWidth(0.6)
    c.line(L, y_linea, R, y_linea)

    y_claim = y_linea - 3.6 * mm
    w_claim = tracking(c, L, y_claim, "TUTTOFARE PER LA CASA", "Barlow-SB", 5.3, ARANCIO, 1.45)
    reg("solo", "claim", L, y_claim, L + w_claim, y_claim + 5.3 * .73)

    # --- l'indirizzo in chiaro sotto la tessera: il codice non e' l'unica via
    tracking(c, R, y_claim, "IL SITO", "Barlow-SB", 4.7, ARANCIO, 1.2, align="right")
    y_sito = y_claim - 3.1 * mm
    c.setFont("Barlow", 5.1)
    c.setFillColor(FUMO)
    c.drawRightString(R, y_sito, SITO)
    reg("solo", "indirizzo", R - c.stringWidth(SITO, "Barlow", 5.1), y_sito - 1.2,
        R, y_claim + 4.7 * .73)

    # --- i mestieri, in due righe: l'elenco lungo del retro qui non ci sta
    voci = ["Idraulica, caldaie e condizionatori",
            "Bagni, muratura, piastrelle, riparazioni"]
    c.setFont("Barlow", 5.9)
    c.setFillColor(FUMO)
    y = B + 10.2 * mm
    for v in voci:
        c.drawString(L, y, v)
        y -= 3.2 * mm
    reg("solo", "servizi", L, y + 3.2 * mm - 1.2,
        L + max(c.stringWidth(v, "Barlow", 5.9) for v in voci), B + 10.2 * mm + 5.9 * .73)

    # --- il numero, l'unica cosa che deve leggersi da un metro
    c_tel = 14.0
    c.setFont("Anton", c_tel)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(L, B + 0.4 * mm, TEL)
    reg("solo", "telefono", L, B + 0.4 * mm, L + c.stringWidth(TEL, "Anton", c_tel),
        B + 0.4 * mm + c_tel * CAP)

    et, y_et = "ANCHE WHATSAPP", B + 2.0 * mm
    w = tracking(c, R, y_et, et, "Barlow-SB", 5.0, FUMO, 1.15, align="right")
    c.setStrokeColor(HexColor("#3A3E42"))
    c.setLineWidth(0.4)
    c.line(R - w, y_et - 1.6 * mm, R, y_et - 1.6 * mm)
    reg("solo", "whatsapp", R - w, y_et - 1.6 * mm, R, y_et + 1.4 * mm)

    crocini(c)
    slug(c, "GABRIEL CALASI  ·  lato unico  ·  85 x 55 mm  ·  abbondanza 3 mm")
    c.showPage()


# ------------------------------------------------------------------ stampa


def documento(percorso, pagine, sottotitolo):
    del BOX[:]
    c = rl_canvas.Canvas(percorso, pagesize=(PAGE_W, PAGE_H))
    c.setTitle("Gabriel Calasi - biglietto da visita")
    c.setAuthor("Gabriel Calasi")
    c.setSubject("85x55 mm, %s, abbondanza 3 mm" % sottotitolo)
    for p in pagine:
        p(c)
    errori = verifica()
    for e in errori:
        print("ERRORE:", e)
    if errori:
        sys.exit(1)
    c.save()
    print("scritto: %-46s %2d elementi, nessuna collisione" % (percorso, len(BOX)))


documento(os.path.join(OUT, "gabriel-biglietto-stampa.pdf"), [fronte, retro], "fronte/retro")
documento(os.path.join(OUT, "gabriel-biglietto-1lato-stampa.pdf"), [lato_unico], "lato unico")
