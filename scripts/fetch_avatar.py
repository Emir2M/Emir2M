"""GitHub profil fotografini indirir -> source-photo.png

github.com/<kullaniciadi>.png herkese acik ve token istemiyor; ?size=920
ile en buyuk karesini verir. ASCII'ye cevrilmeden once prep_photo.py'den
gecirilmesi gerekiyor.
"""
import json
import os
import sys

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "source-photo.png")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def main():
    username = os.environ.get("GH_USERNAME")
    if not username:
        with open(CONFIG, encoding="utf-8") as fh:
            username = json.load(fh)["username"]
    if not username or username == "KULLANICI_ADIN":
        sys.exit("profile.json icindeki 'username' alanini doldur.")

    url = "https://github.com/%s.png?size=920" % username
    resp = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    if resp.status_code == 404:
        sys.exit("Avatar bulunamadi: %s" % username)
    resp.raise_for_status()

    with open(OUT, "wb") as fh:
        fh.write(resp.content)
    print("Avatar indirildi: source-photo.png (%.0f KB)" % (len(resp.content) / 1024))


if __name__ == "__main__":
    main()
