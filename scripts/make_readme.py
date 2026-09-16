"""Uc SVG'yi terminal duzeninde yerlestiren README.md'yi uretir.

Genislikleri elle yazmak yerine SVG'lerin gercek olculerinden hesapliyor:
portre + kart toplami tam olarak isi haritasinin genisligine esitleniyor,
boylece kenarlar hizali duruyor.

GitHub markdown tuzaklari (bu dosyanin sekli bunlara gore):
  * Satir ici style tamamen siliniyor. GitHub'in kabul ettigi tek dikey
    bosluk <br> etiketi.
  * <h1> ve <h2> tam genislikte bir alt cizgi ciziyor. Ayrac olarak iyi,
    baslik olarak dikkat dagitici - cizgi istemiyorsan <h3> kullan.
  * JavaScript yok, disaridan CSS engelli. Animasyon her SVG'nin icinde yasamali.
  * Iki gorseli yan yana koymanin guvenilir tek yolu <table>.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "README.md")

TOTAL_W = 860        # portre + kart genisligi; isi haritasi da bu genislikte


def svg_size(name):
    """SVG'nin kok width/height degerlerini oku."""
    path = os.path.join(ROOT, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        head = fh.read(600)
    w = re.search(r'\bwidth="([\d.]+)"', head)
    h = re.search(r'\bheight="([\d.]+)"', head)
    if not (w and h):
        return None
    return float(w.group(1)), float(h.group(1))


def main():
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)
    username = config["username"]
    host = config.get("hostname", "github")
    prompt = "%s@%s ~ $" % (username, host)

    portrait = svg_size("ascii-portrait.svg")
    card = svg_size("info-card.svg")

    lines = ['<div align="center">', ""]

    if svg_size("contrib-heatmap.svg"):
        lines += [
            "<h3><code>%s ./contributions.sh</code></h3>" % prompt,
            '<img src="./contrib-heatmap.svg" width="%d" alt="Katki grafigi" />' % TOTAL_W,
            "",
            "<br>",
            "",
        ]

    if portrait and card:
        # Iki sutunu ayni EKRAN YUKSEKLIGINE getir, sonra genislikleri
        # TOTAL_W'yi dolduracak sekilde dagit. Ikisine ayni olcek katsayisini
        # uygulamak yanlis oluyor: portre kare, kart genis ve kisa; ayni
        # katsayi devasa bir portrenin yanina minicik bir kart koyuyor.
        # Ortak yukseklikte cozunce sutunlar alt kenarda da hizalaniyor.
        gap = 16
        height = (TOTAL_W - gap) / (portrait[0] / portrait[1] + card[0] / card[1])
        pw = round(height * portrait[0] / portrait[1])
        cw = TOTAL_W - gap - pw

        lines += [
            "<h3><code>%s whoami</code></h3>" % prompt,
            "<table>",
            "  <tr>",
            '    <td valign="top"><img src="./ascii-portrait.svg" width="%d" alt="ASCII portre" /></td>' % pw,
            '    <td valign="top"><img src="./info-card.svg" width="%d" alt="Bilgi karti" /></td>' % cw,
            "  </tr>",
            "</table>",
            "",
        ]
    elif card:
        lines += [
            "<h3><code>%s whoami</code></h3>" % prompt,
            '<img src="./info-card.svg" width="%d" alt="Bilgi karti" />' % min(int(card[0]), TOTAL_W),
            "",
        ]

    lines += [
        "<br>",
        "",
        "<sub><code>%s exit</code></sub>" % prompt,
        "",
        "</div>",
        "",
    ]

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print("README.md yazildi")

    write_preview(prompt, portrait, card)


def write_preview(prompt, portrait, card):
    """Yerel onizleme sayfasi - README ile ayni genislikleri kullanir.

    Genislikleri iki dosyaya elle yazmak ikisinin birbirinden kaymasina yol
    aciyordu; ayni hesaptan uretince onizleme gercekten GitHub'da gorecegin
    sey oluyor.
    """
    heat = svg_size("contrib-heatmap.svg")
    gap = 16
    if portrait and card:
        h = (TOTAL_W - gap) / (portrait[0] / portrait[1] + card[0] / card[1])
        pw = round(h * portrait[0] / portrait[1])
        cw = TOTAL_W - gap - pw
        row = ('<div class="row">\n'
               '  <img src="./ascii-portrait.svg" width="%d">\n'
               '  <img src="./info-card.svg" width="%d">\n'
               "</div>" % (pw, cw))
    elif card:
        row = '<img src="./info-card.svg" width="%d">' % min(int(card[0]), TOTAL_W)
    else:
        row = ""

    heat_block = ('<h3>%s ./contributions.sh</h3>\n<img src="./contrib-heatmap.svg" width="%d">'
                  % (prompt, TOTAL_W)) if heat else ""

    html = """<!doctype html>
<meta charset="utf-8">
<title>Profil onizleme</title>
<style>
  body{background:#0d1117;color:#8b949e;font:14px ui-monospace,Consolas,monospace;
       margin:0;padding:40px;display:flex;flex-direction:column;align-items:center}
  .row{display:flex;gap:%dpx;align-items:flex-start}
  h3{color:#c9d1d9;font-weight:400;margin:28px 0 10px}
  img{display:block}
  button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;
         padding:8px 16px;font:inherit;cursor:pointer;margin-top:32px}
</style>
<!-- GitHub README'nin birebir aynisi degil, ama SVG animasyonlarini ayni
     sekilde oynatir ve genislikler README ile ayni hesaptan geliyor. -->
%s
<h3>%s whoami</h3>
%s
<button onclick="location.reload()">animasyonlari tekrar oynat</button>
""" % (gap, heat_block, prompt, row)

    with open(os.path.join(ROOT, "preview.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    print("preview.html yazildi")


if __name__ == "__main__":
    main()
