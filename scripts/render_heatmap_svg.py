"""data/contributions.json -> contrib-heatmap.svg

53 hafta x 7 gun takvimini koselerinden yuvarlatilmis kutular halinde cizer.
Kutular capraz bir dalga halinde bir kez belirir ve donar (dongu yok).
Tum animasyon SVG'nin icindeki CSS keyframe'lerde: GitHub README'de disaridan
CSS ve JavaScript'e izin vermedigi icin calisan tek yontem bu.
"""
import argparse
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "contributions.json")
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")

# seviye 0 (katki yok) -> seviye 5 (neon tepe)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL, GAP = 13, 3
STEP = CELL + GAP
PAD = 22
LEFT = PAD + 32          # gun etiketleri icin sol bosluk
TOP = 74                 # baslik cubugu + ay etiketleri
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}   # pazar = 0


def plural(n, word):
    """1 icin tekil, digerleri icin cogul - "1 contributions" ozensiz duruyor."""
    return word if n == 1 else word + "s"


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def sunday_index(day):
    """Pazar = 0 ... Cumartesi = 6 (GitHub takvimi pazar ile baslar)."""
    return (day.weekday() + 1) % 7


def build_grid(days, best_count):
    """Gunleri (hafta, satir) izgarasina yerlestir ve seviyeleri belirle."""
    first = date.fromisoformat(days[0]["date"])
    origin = date.fromordinal(first.toordinal() - sunday_index(first))

    cells = []
    max_week = 0
    for day in days:
        current = date.fromisoformat(day["date"])
        week = (current.toordinal() - origin.toordinal()) // 7
        row = sunday_index(current)
        level = int(day["level"])
        # En yogun gunlere ayri bir neon basamak ver; dolu bir takvimde
        # 4. seviye her seyi ayni yesile duzlestiriyor.
        if level >= 4 and best_count and day["count"] >= best_count * 0.8:
            level = 5
        cells.append((week, row, level, day["count"], day["date"]))
        max_week = max(max_week, week)
    return cells, max_week, origin


def month_labels(days, origin):
    """Her ayin ilk gorundugu hafta sutununu isaretle."""
    labels, seen = [], set()
    for day in days:
        current = date.fromisoformat(day["date"])
        key = (current.year, current.month)
        if key in seen:
            continue
        seen.add(key)
        week = (current.toordinal() - origin.toordinal()) // 7
        # Takvim ayin ortasinda basliyorsa ilk etiketi atla, yoksa kayik durur
        if week == 0 and current.day > 7:
            continue
        labels.append((week, MONTHS[current.month - 1]))
    return labels


def main():
    # Veri ve cikti yolu disaridan verilebiliyor: boylece gercek grafigi
    # bozmadan ornek bir veriyle deneme cizimi yapilabiliyor.
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=DATA)
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    with open(args.data, encoding="utf-8") as fh:
        payload = json.load(fh)
    with open(CONFIG, encoding="utf-8") as fh:
        config = json.load(fh)

    theme = config["theme"]
    days = payload["days"]
    stats = payload["stats"]
    username = payload["username"]
    hostname = config.get("hostname", "github")

    cells, max_week, origin = build_grid(days, stats["best_day"]["count"])
    weeks = max_week + 1

    grid_w = weeks * STEP - GAP
    grid_h = 7 * STEP - GAP
    width = LEFT + grid_w + PAD
    height = TOP + grid_h + 76

    # Capraz dalga: gecikme sutun + satir ile artiyor, boylece sol ustten
    # sag alta akan bir doldurma hissi olusuyor.
    step_delay = 0.011
    footer_delay = round((weeks - 1 + 6) * step_delay + 0.65, 2)

    out = []
    add = out.append
    add('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d" role="img" '
        'aria-label="%s GitHub katki takvimi">'
        % (width, height, width, height, esc(username)))

    add("<style>")
    add("  .bg{fill:%s}" % theme["bg"])
    add('  text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,'
        '"Liberation Mono",monospace;-webkit-font-smoothing:antialiased}')
    add("  .lbl{fill:%s;font-size:10px}" % theme["dim"])
    add("  .title{fill:%s;font-size:12px}" % theme["dim"])
    add("  .foot{fill:%s;font-size:11.5px}" % theme["fg"])
    add("  .n{fill:%s}" % theme["accent"])
    add("  .sep{fill:%s}" % theme["border"])
    add("  .d{opacity:0;transform-box:fill-box;transform-origin:50%% 50%%;"
        "animation:pop .5s cubic-bezier(.2,.8,.3,1) forwards}")
    add("  .fade{opacity:0;animation:fade .6s ease-out forwards}")
    add("  @keyframes pop{from{opacity:0;transform:translateY(-7px) scale(.35)}"
        "to{opacity:1;transform:none}}")
    add("  @keyframes fade{from{opacity:0;transform:translateY(4px)}"
        "to{opacity:1;transform:none}}")
    add("  @media (prefers-reduced-motion:reduce){"
        ".d,.fade{opacity:1;animation:none;transform:none}}")
    add("</style>")

    # --- pencere cercevesi ---
    add('<rect class="bg" width="%d" height="%d" rx="12"/>' % (width, height))
    add('<rect x="0.5" y="0.5" width="%d" height="%d" rx="11.5" fill="none" '
        'stroke="%s"/>' % (width - 1, height - 1, theme["border"]))
    add('<line x1="0" y1="36" x2="%d" y2="36" stroke="%s"/>' % (width, theme["border"]))
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        add('<circle cx="%d" cy="18" r="5.5" fill="%s"/>' % (22 + i * 19, color))
    add('<text class="title" x="92" y="22">%s@%s: ~/contributions</text>'
        % (esc(username), esc(hostname)))

    # --- ay etiketleri ---
    for week, name in month_labels(days, origin):
        add('<text class="lbl fade" x="%d" y="%d" style="animation-delay:%.2fs">%s</text>'
            % (LEFT + week * STEP, TOP - 10, 0.1 + week * step_delay, name))

    # --- gun etiketleri ---
    for row, name in DAY_LABELS.items():
        add('<text class="lbl fade" x="%d" y="%d" text-anchor="end" '
            'style="animation-delay:%.2fs">%s</text>'
            % (LEFT - 9, TOP + row * STEP + CELL - 3, 0.1 + row * step_delay, name))

    # --- izgara ---
    add("<g>")
    for week, row, level, count, day in cells:
        delay = round((week + row) * step_delay, 3)
        add('<rect class="d" x="%d" y="%d" width="%d" height="%d" rx="3" '
            'fill="%s" style="animation-delay:%.3fs"><title>%s: %d</title></rect>'
            % (LEFT + week * STEP, TOP + row * STEP, CELL, CELL,
               PALETTE[level], delay, day, count))
    add("</g>")

    # --- alt satir: toplam + lejant ---
    foot_y = TOP + grid_h + 30
    add('<text class="foot fade" x="%d" y="%d" style="animation-delay:%.2fs">'
        '<tspan class="n">%s</tspan> %s in the last year</text>'
        % (LEFT, foot_y, footer_delay, "{:,}".format(stats["total"]),
           plural(stats["total"], "contribution")))

    legend_w = 6 * 15 + 66
    lx = width - PAD - legend_w
    add('<g class="fade" style="animation-delay:%.2fs">' % (footer_delay + 0.1))
    add('<text class="lbl" x="%d" y="%d">Less</text>' % (lx, foot_y))
    for i in range(6):
        add('<rect x="%d" y="%d" width="11" height="11" rx="2.5" fill="%s"/>'
            % (lx + 28 + i * 15, foot_y - 9, PALETTE[i]))
    add('<text class="lbl" x="%d" y="%d">More</text>' % (lx + 28 + 6 * 15 + 3, foot_y))
    add("</g>")

    # --- alt satir: seriler ---
    sub_y = foot_y + 22
    add('<text class="foot fade" x="%d" y="%d" font-size="11" '
        'style="animation-delay:%.2fs">'
        '<tspan class="n">%d</tspan> day streak'   # bilesik sifat: hep tekil
        '<tspan class="sep">  /  </tspan>longest <tspan class="n">%d</tspan>'
        '<tspan class="sep">  /  </tspan>best day <tspan class="n">%d</tspan>'
        '<tspan class="sep">  /  </tspan><tspan class="n">%d</tspan> active %s'
        "</text>"
        % (LEFT, sub_y, footer_delay + 0.2,
           stats["current_streak"],
           stats["longest_streak"], stats["best_day"]["count"],
           stats["active_days"], plural(stats["active_days"], "day")))

    add("</svg>")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
    print("%s yazildi (%d hafta, %dx%d)"
          % (os.path.basename(args.out), weeks, width, height))


if __name__ == "__main__":
    main()
