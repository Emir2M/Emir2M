"""source-prepped.png -> ascii-portrait.svg

Hazirlanmis goruntuyu bir karakter izgarasina (varsayilan 100 sutun)
kucultur; her pikselin parlakligi yogunluk rampasindan bir glif secer.

Iki tasarim karari goruntuyu "parazit" olmaktan cikariyor:
  * Tek renk. Karakter basina gokkusagi renklendirme, cogu ASCII portreyi
    karincalanan bir ekrana cevirenin ta kendisi.
  * Yuksek kontrast. Arka plan bosluk glifine dusuyor, yani sadece ozne yaziliyor.

Animasyon: her satir kendi yatay kirpma maskesinin icinde soldan saga
aciliyor, kucuk bir blok imlec silme kenarinda geziyor, satirlar yukaridan
asagiya kaydiriliyor. Portre bir kez yaziliyor ve donuyor - dongu yok.
SMIL SVG'nin icinde oldugu icin GitHub oynatiyor.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "ascii-portrait.svg")

# parlak (seyrek) -> koyu (yogun).  Bastaki bosluk arka plani hiclige indirir.
RAMP = " .`:-=+*cs#%@"

FONT = 10.5
CHAR_W = FONT * 0.60      # monospace yatay ilerleme
LINE_H = FONT * 1.06
PAD = 16


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def to_rows(path, cols, aspect, invert, gamma):
    img = Image.open(path).convert("L")
    rows = max(1, round(img.height / img.width * cols * aspect))
    small = img.resize((cols, rows), Image.LANCZOS)

    arr = np.asarray(small).astype(np.float64) / 255.0
    if gamma != 1.0:
        arr = np.power(arr, gamma)
    if invert:
        arr = 1.0 - arr

    # parlak piksel -> rampanin basi (bosluk), koyu piksel -> rampanin sonu
    idx = ((1.0 - arr) * (len(RAMP) - 1)).round().astype(int).clip(0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=None, help="varsayilan: profile.json icindeki ascii.photo")
    parser.add_argument("--cols", type=int, default=None)
    parser.add_argument("--aspect", type=float, default=0.50,
                        help="karakter yukseklik/genislik duzeltmesi")
    parser.add_argument("--gamma", type=float, default=1.0,
                        help="<1 aydinlatir, >1 koyultur")
    parser.add_argument("--invert", action="store_true",
                        help="koyu zeminli fotograflar icin")
    parser.add_argument("--static", action="store_true", help="animasyonsuz kare")
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    theme = config["theme"]
    cols = args.cols or config.get("ascii", {}).get("cols", 100)
    image = args.image or os.path.join(ROOT, config.get("ascii", {}).get("photo",
                                                                        "source-prepped.png"))
    if not os.path.exists(image):
        sys.exit("Goruntu yok: %s\nOnce: python scripts/prep_photo.py <fotograf>" % image)

    rows = to_rows(image, cols, args.aspect, args.invert, args.gamma)

    width = round(PAD * 2 + cols * CHAR_W)
    height = round(PAD * 2 + len(rows) * LINE_H)
    stagger = min(0.05, 2.2 / max(1, len(rows)))
    wipe = 0.34

    out = []
    add = out.append
    add('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" aria-label="ASCII portre">'
        % (width, height, width, height))
    add("<style>")
    add('  text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
        '"Liberation Mono",monospace;font-size:%.2fpx;white-space:pre}' % FONT)
    add("  .a{fill:%s}" % theme["fg"])
    add("</style>")
    add('<rect width="%d" height="%d" rx="12" fill="%s"/>' % (width, height, theme["bg"]))

    defs, texts, cursors = [], [], []
    for i, row in enumerate(rows):
        stripped = row.rstrip()
        if not stripped:
            continue
        y = PAD + (i + 1) * LINE_H
        begin = round(i * stagger, 3)
        row_w = len(stripped) * CHAR_W
        full_w = cols * CHAR_W

        defs.append(
            '<clipPath id="w%d"><rect x="%d" y="%.2f" width="0" height="%.2f">'
            '<animate attributeName="width" from="0" to="%.2f" begin="%.3fs" '
            'dur="%.2fs" fill="freeze"/></rect></clipPath>'
            % (i, PAD, y - LINE_H, LINE_H + 2, full_w, begin, wipe))

        texts.append(
            ('<text class="a" x="%d" y="%.2f" xml:space="preserve" '
             'textLength="%.2f" lengthAdjust="spacingAndGlyphs">%s</text>'
             % (PAD, y, row_w, esc(stripped)), i))

        # Silme kenarinda gezen blok imlec
        cursors.append(
            '<rect x="%d" y="%.2f" width="%.2f" height="%.2f" fill="%s" opacity="0">'
            '<animate attributeName="x" from="%d" to="%.2f" begin="%.3fs" '
            'dur="%.2fs" fill="freeze"/>'
            '<animate attributeName="opacity" values="0;0.85;0.85;0" '
            'keyTimes="0;0.05;0.9;1" begin="%.3fs" dur="%.2fs" fill="freeze"/>'
            '</rect>'
            % (PAD, y - LINE_H + 1.5, CHAR_W, LINE_H - 1, theme["accent"],
               PAD, PAD + full_w - CHAR_W, begin, wipe, begin, wipe))

    if args.static:
        add("".join(text for text, _ in texts))
    else:
        add("<defs>%s</defs>" % "".join(defs))
        for text, i in texts:
            add('<g clip-path="url(#w%d)">%s</g>' % (i, text))
        add("".join(cursors))

    add("</svg>")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("%s yazildi (%d sutun x %d satir, %dx%d px)"
          % (os.path.basename(args.out), cols, len(rows), width, height))


if __name__ == "__main__":
    main()
