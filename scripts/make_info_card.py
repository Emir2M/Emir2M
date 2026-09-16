"""profile.json -> info-card.svg

neofetch ciktisina benzeyen bir panel: baslik cubugu, user@host satiri,
altinda renkli anahtar/deger satirlari. Her satir kisa bir gecikmeyle
kayarak beliriyor, boylece portrenin yanina "yaziliyormus" gibi duruyor.

STATIC=1 ile calistirirsan animasyonsuz, donmus bir kare uretir
(yerelde onizleme icin).
"""
import json
import os
import textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "info-card.svg")

FONT = 13           # piksel
CHAR_W = 7.82       # monospace 13px icin yaklasik karakter genisligi
LINE_H = 22
PAD = 24
TOP = 36 + 20       # pencere cubugu + ic bosluk
KEY_COL = 13        # anahtar sutunu kac karakter genisliginde
WRAP = 42           # deger metni kac karakterde sarilsin
STATIC = os.environ.get("STATIC") == "1"


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def anim(delay):
    """Satir animasyonu icin stil parcasi (STATIC modda bos)."""
    if STATIC:
        return ""
    return ' style="animation-delay:%.2fs"' % delay


def cls(*names):
    """class niteligi kurar; animasyon acikken 'ln' sinifini da ekler.

    Animasyon sinifini ayri bir nitelik olarak basmak, class'i iki kez yazip
    gecersiz XML uretmeye yol aciyordu - tek yerden kurmak o riski kapatiyor.
    """
    parts = [n for n in names if n]
    if not STATIC:
        parts.append("ln")
    return ' class="%s"' % " ".join(parts) if parts else ""


def main():
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)

    theme = config["theme"]
    card = config["card"]
    username = config["username"]
    hostname = config.get("hostname", "github")
    rows = card["rows"]

    # Satirlari once duz bir listeye ac: uzun degerler birden fazla satira sariliyor
    lines = []          # (anahtar, deger) - anahtar "" ise devam satiri
    header = "%s@%s" % (username, hostname)
    lines.append(("@", header))
    lines.append(("-", "-" * len(header)))
    for key, value in rows:
        chunks = textwrap.wrap(str(value), WRAP) or [""]
        for i, chunk in enumerate(chunks):
            lines.append((key if i == 0 else "", chunk))

    longest = max(KEY_COL + len(v) for _, v in lines)
    width = int(PAD * 2 + longest * CHAR_W) + 8
    width = max(width, 460)
    height = TOP + len(lines) * LINE_H + PAD + 6

    out = []
    add = out.append
    add('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="%s hakkinda bilgi karti">'
        % (width, height, width, height, esc(username)))

    add("<style>")
    add('  text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
        '"Liberation Mono",monospace;font-size:%dpx;'
        "-webkit-font-smoothing:antialiased}" % FONT)
    add("  .k{fill:%s;font-weight:700}" % theme["accent"])
    add("  .v{fill:%s}" % theme["fg"])
    add("  .u{fill:%s;font-weight:700}" % theme["accent2"])
    add("  .dim{fill:%s}" % theme["dim"])
    add("  .title{fill:%s;font-size:12px}" % theme["dim"])
    if not STATIC:
        add("  .ln{opacity:0;animation:in .45s ease-out forwards}")
        add("  @keyframes in{from{opacity:0;transform:translateX(-10px)}"
            "to{opacity:1;transform:none}}")
        add("  .cur{animation:blink 1.1s step-end infinite}")
        add("  @keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}")
        add("  @media (prefers-reduced-motion:reduce){"
            ".ln{opacity:1;animation:none;transform:none}.cur{animation:none}}")
    add("</style>")

    # --- pencere cercevesi ---
    add('<rect width="%d" height="%d" rx="12" fill="%s"/>' % (width, height, theme["bg"]))
    add('<rect x="0.5" y="0.5" width="%d" height="%d" rx="11.5" fill="none" '
        'stroke="%s"/>' % (width - 1, height - 1, theme["border"]))
    add('<line x1="0" y1="36" x2="%d" y2="36" stroke="%s"/>' % (width, theme["border"]))
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        add('<circle cx="%d" cy="18" r="5.5" fill="%s"/>' % (22 + i * 19, color))
    add('<text class="title" x="92" y="22">%s@%s: ~/%s</text>'
        % (esc(username), esc(hostname), esc(card.get("title", "whoami"))))

    # --- satirlar ---
    key_x = PAD
    val_x = PAD + KEY_COL * CHAR_W
    for i, (key, value) in enumerate(lines):
        y = TOP + i * LINE_H
        delay = 0.25 + i * 0.09
        if key == "@":
            add('<text%s x="%d" y="%.1f"%s><tspan class="u">%s</tspan>'
                '<tspan class="dim">@</tspan><tspan class="u">%s</tspan></text>'
                % (cls(), key_x, y, anim(delay), esc(username), esc(hostname)))
        elif key == "-":
            add('<text%s x="%d" y="%.1f"%s>%s</text>'
                % (cls("dim"), key_x, y, anim(delay), esc(value)))
        else:
            add("<text%s%s>" % (cls(), anim(delay)))
            if key:
                add('<tspan class="k" x="%d" y="%.1f">%s</tspan>' % (key_x, y, esc(key)))
            add('<tspan class="v" x="%.1f" y="%.1f">%s</tspan>'
                % (val_x, y, esc(value)))
            add("</text>")

    # --- yanip sonen imlec ---
    # Imlec iki katman: disdaki <g> iceri kayarak giriyor, icteki <text>
    # yanip sonuyor. Ayni ogeye iki animasyon vermek ikisinin de 'opacity'
    # uzerinde carpismasina yol aciyor, bu yuzden ayirdim.
    cursor_y = TOP + len(lines) * LINE_H
    add("<g%s%s>" % (cls(), anim(0.25 + len(lines) * 0.09)))
    add('<text class="%s" x="%d" y="%.1f">&#9608;</text>'
        % ("v" if STATIC else "v cur", key_x, cursor_y))
    add("</g>")

    add("</svg>")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("info-card.svg yazildi (%dx%d%s)"
          % (width, height, ", STATIC" if STATIC else ""))


if __name__ == "__main__":
    main()
