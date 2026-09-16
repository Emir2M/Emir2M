"""Tum profil sanatini sirayla uretir.

    python build.py            # her seyi uret (avatar + portre + kart + isi haritasi + README)
    python build.py --no-photo # portreyi atla (fotograf/avatar degismediyse)
    python build.py --only-heatmap

Gunluk GitHub Actions isi sadece son iki adimi calistiriyor; portre ve kart
statik, onlari yalnizca fotografin ya da profile.json degistiginde uretmen
yeterli.
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(script, *extra):
    label = os.path.basename(script)
    print("\n>>> %s %s" % (label, " ".join(extra)))
    result = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", script)] + list(extra),
                            cwd=ROOT)
    if result.returncode != 0:
        sys.exit("%s basarisiz oldu (kod %d)" % (label, result.returncode))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-photo", action="store_true",
                        help="avatar indirme + portre adimlarini atla")
    parser.add_argument("--only-heatmap", action="store_true",
                        help="sadece katki verisini tazele ve isi haritasini ciz")
    parser.add_argument("--only-card", action="store_true",
                        help="sadece bilgi kartini yeniden ciz (aga cikmaz - "
                             "metin denerken hizli tur)")
    parser.add_argument("--photo", default=None,
                        help="avatar yerine kendi fotografini kullan")
    args = parser.parse_args()

    # Kart metnini deneme turu: ne fotograf isliyor ne de GitHub'a gidiyor.
    # README yine de uretiliyor, cunku kart boyu degisince sutun genislikleri
    # yeniden hesaplanmali.
    if args.only_card:
        run("make_info_card.py")
        run("make_readme.py")
        print("\nHazir. preview.html dosyasini tarayicida yenile.")
        return

    if not args.only_heatmap and not args.no_photo:
        if args.photo:
            run("prep_photo.py", args.photo)
        else:
            run("fetch_avatar.py")
            run("prep_photo.py", "source-photo.png")
        run("make_ascii_svg.py")

    if not args.only_heatmap:
        run("make_info_card.py")

    run("fetch_contributions.py")
    run("render_heatmap_svg.py")
    run("make_readme.py")

    print("\nHazir. Yerelde kontrol icin preview.html dosyasini tarayicida ac.")


if __name__ == "__main__":
    main()
