"""Fotografi ASCII'ye donusturulmeye hazir hale getirir.

Duz isikla cekilmis bir yuz, dogrudan cevrildiginde koyu ve okunaksiz bir
lekeye donusuyor. Uc adim bunu duzeltiyor:

  1. Arka plani kaldir (rembg varsa) - ozne izole olsun.
  2. Yerel kontrasti yukselt (OpenCV CLAHE varsa, yoksa numpy ile ayni isi
     yapan sade bir uyarlama) - duz bir yuze gercek isik/golge kazandirir.
  3. Saf beyaza yerlestir - arka plan ASCII rampasinin bos ucuna dussun.

Kullanim:
    python scripts/prep_photo.py source-photo.jpg
    python scripts/prep_photo.py source-photo.jpg --no-rembg --gain 2.5

Cikti: source-prepped.png (gri tonlamali)
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "source-prepped.png")


def remove_background(img):
    """rembg kuruluysa arka plani sil; degilse fotografi oldugu gibi birak."""
    try:
        from rembg import remove
    except Exception:
        print("  ! rembg yok - arka plan silinmiyor "
              "(sade bir arka planla cekilmis fotograf kullan ya da "
              "--white-point degerini dusur)")
        return img
    print("  - arka plan siliniyor (rembg)")
    return remove(img)


def crop_to_subject(img, mode, ratio=0.52, aspect=0.85, margin=0.04):
    """Alfa kanalindaki ozneye gore kirpar.

    'subject'  : oznenin sinir kutusu (tam boy silueti).
    'portrait' : kutunun ust kismi - bas ve omuzlar. Tam boy bir kare
                 README'de kartin yanina koyunca cok uzun duruyor ve yuz
                 birkac karaktere dusuyor; bu mod yuzu cerceveye oturtuyor.
    """
    if mode == "none":
        return img
    alpha = np.asarray(img)[:, :, 3]
    ys, xs = np.where(alpha > 40)
    if len(xs) == 0:
        print("  ! alfa bos - kirpma atlandi")
        return img

    x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
    box_h = y1 - y0

    if mode == "portrait":
        y1 = y0 + max(1, int(box_h * ratio))
        # Basin yatay merkezini bul: ust seritteki piksellerin ortalamasi.
        band = alpha[y0:y0 + max(1, box_h // 6)]
        band_xs = np.where(band > 40)[1]
        cx = int(band_xs.mean()) + 0 if len(band_xs) else (x0 + x1) // 2
        half = int((y1 - y0) * aspect / 2)
        x0, x1 = cx - half, cx + half

    pad_x = int((x1 - x0) * margin)
    pad_y = int((y1 - y0) * margin)
    box = (max(0, x0 - pad_x), max(0, y0 - pad_y),
           min(img.width, x1 + pad_x), min(img.height, y1 + pad_y))
    print("  - kirpildi (%s): %dx%d" % (mode, box[2] - box[0], box[3] - box[1]))
    return img.crop(box)


def clahe(gray, clip=2.5, grid=8):
    """Kontrast sinirli yerel histogram esitleme.

    OpenCV varsa onun CLAHE'sini kullanir. Yoksa ayni fikri numpy ile
    uygular: goruntuyu kareler halinde esitle, kareler arasinda bilineer
    gecis yap. Amac tek bir global egri yerine yuzun her bolgesine kendi
    kontrastini vermek.
    """
    try:
        import cv2
        print("  - yerel kontrast (OpenCV CLAHE)")
        return cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid)).apply(gray)
    except Exception:
        pass

    print("  - yerel kontrast (numpy CLAHE)")
    h, w = gray.shape
    ty, tx = max(1, h // grid), max(1, w // grid)
    # Her kare icin kendi arama tablosunu cikar
    luts = np.zeros((grid, grid, 256), dtype=np.uint8)
    for gy in range(grid):
        for gx in range(grid):
            tile = gray[gy * ty:(gy + 1) * ty if gy < grid - 1 else h,
                        gx * tx:(gx + 1) * tx if gx < grid - 1 else w]
            hist = np.bincount(tile.ravel(), minlength=256).astype(np.float64)
            limit = clip * tile.size / 256.0
            excess = np.maximum(hist - limit, 0).sum()
            hist = np.minimum(hist, limit) + excess / 256.0
            cdf = hist.cumsum()
            cdf = (cdf - cdf[0]) / max(cdf[-1] - cdf[0], 1e-6) * 255.0
            luts[gy, gx] = cdf.clip(0, 255).astype(np.uint8)

    # Kare merkezleri arasinda bilineer harmanla - kare sinirlarinda iz kalmasin
    yy = (np.arange(h) / ty - 0.5).clip(0, grid - 1)
    xx = (np.arange(w) / tx - 0.5).clip(0, grid - 1)
    y0, x0 = np.floor(yy).astype(int), np.floor(xx).astype(int)
    y1, x1 = np.minimum(y0 + 1, grid - 1), np.minimum(x0 + 1, grid - 1)
    fy, fx = (yy - y0)[:, None], (xx - x0)[None, :]

    def mapped(gy, gx):
        return luts[gy[:, None], gx[None, :], gray].astype(np.float64)

    top = mapped(y0, x0) * (1 - fx) + mapped(y0, x1) * fx
    bot = mapped(y1, x0) * (1 - fx) + mapped(y1, x1) * fx
    return (top * (1 - fy) + bot * fy).clip(0, 255).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("photo")
    parser.add_argument("--no-rembg", action="store_true",
                        help="arka plan silmeyi atla")
    parser.add_argument("--white-point", type=int, default=238,
                        help="bu parlakligin ustundeki pikseller saf beyaza cekilir (0-255)")
    parser.add_argument("--gain", type=float, default=1.0,
                        help="son kontrast carpani (1.0 = degistirme)")
    parser.add_argument("--clip", type=float, default=2.5,
                        help="CLAHE kontrast siniri")
    parser.add_argument("--crop", choices=("portrait", "subject", "none"),
                        default="portrait",
                        help="portrait = bas ve omuzlar, subject = tum siluet")
    parser.add_argument("--crop-ratio", type=float, default=0.52,
                        help="portrait modunda oznenin ust yuzde kaci alinsin")
    parser.add_argument("--out", default=OUT)
    args = parser.parse_args()

    if not os.path.exists(args.photo):
        sys.exit("Fotograf bulunamadi: %s" % args.photo)

    print("Hazirlaniyor: %s" % args.photo)
    img = Image.open(args.photo).convert("RGBA")

    # Cok buyuk fotograflar sadece islemi yavaslatiyor; ASCII izgarasi zaten kucuk
    if img.width > 1400:
        img = img.resize((1400, round(img.height * 1400 / img.width)), Image.LANCZOS)

    if not args.no_rembg:
        img = remove_background(img)
        img = crop_to_subject(img, args.crop, ratio=args.crop_ratio)
    elif args.crop != "none":
        print("  ! kirpma alfa kanaline dayaniyor, rembg olmadan atlaniyor")

    # Saf beyaz zemine yapistir: seffaf alanlar rampanin bos ucuna dussun
    canvas = Image.new("RGBA", img.size, (255, 255, 255, 255))
    canvas.alpha_composite(img.convert("RGBA"))
    gray = canvas.convert("L")

    arr = clahe(np.asarray(gray), clip=args.clip)
    out = Image.fromarray(arr)

    if args.gain != 1.0:
        out = ImageOps.autocontrast(out, cutoff=1)
        arr = np.asarray(out).astype(np.float64)
        arr = ((arr - 128.0) * args.gain + 128.0).clip(0, 255)
        out = Image.fromarray(arr.astype(np.uint8))

    # Hafif keskinlestirme: kucultuldugunde hatlar dagilmasin
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=3))

    # Beyaz noktasi: acik gri arka plani tamamen beyaza cek (-> ASCII'de bosluk)
    arr = np.asarray(out).copy()
    arr[arr >= args.white_point] = 255
    out = Image.fromarray(arr)

    out.save(args.out)
    print("Yazildi: %s (%dx%d)" % (args.out, out.width, out.height))
    print("Kontrol et; koyu cikmissa --gain 1.6, arka plan kirliyse "
          "--white-point 220 dene.")


if __name__ == "__main__":
    main()
