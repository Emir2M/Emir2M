# Kurulum ve bakım

## 1. Repoyu yayına al

Profil README'si için repo adının **tam olarak kullanıcı adınla aynı** olması şart: `Emir2M/Emir2M`.

GitHub'da yeni repo aç (public, README ekleme — burada zaten var), sonra:

```bash
git init
git branch -M main
git add .
git commit -m "feat: animated terminal profile README"
git remote add origin https://github.com/Emir2M/Emir2M.git
git push -u origin main
```

Push'tan sonra `github.com/Emir2M` adresine bak — README profilinin en üstünde görünür.

Son adım: Actions sekmesine gir, **Update profile art** iş akışını bir kez elle çalıştır (`Run workflow`). Her gün 06:17 UTC'de (TR 09:17) ısı haritasını tazeleyip commit'ler.

---

## 2. Katkı grafiği neden boş — ve nasıl düzelir

Şu an takvim son bir yılda **1 katkı** gösteriyor. Sebebi tembellik değil, ayar:

`42-Libft` reposundaki 11 commit'in tamamı şu adresle yazılmış:

```
emirhyil@k1m04s05.42istanbul.com.tr
emirhyil@k1m05s01.42istanbul.com.tr
```

Bunlar 42 laboratuvarındaki makinelerin yerel hostname'inden türeyen sahte adresler. GitHub bir commit'i ancak yazar e-postası hesabına kayıtlıysa sana sayar — bu adresler kayıtlı olmadığı için 11 commit'in hiçbiri grafiğe düşmüyor.

### Bundan sonrası için (şart)

42'deki makinede ve kendi bilgisayarında bir kez çalıştır:

```bash
git config --global user.name  "Emir2M"
git config --global user.email "198243462+Emir2M@users.noreply.github.com"
```

Bu, GitHub'ın sana verdiği `noreply` adresi — gerçek e-postanı commit geçmişinde açığa çıkarmadan katkıların sayılmasını sağlar.

> 42 laboratuvarında home dizini her oturumda sıfırlanıyorsa bu komut da sıfırlanır. Her oturum başında tekrar çalıştır ya da `~/.gitconfig` dosyanı kalıcı bir yere yedekle.

Doğru ayarlandığını kontrol et:

```bash
git config --global user.email    # noreply adresini yazmalı
git log -1 --format='%ae'         # son commit'in yazar adresi
```

### Geçmiş commit'ler için (isteğe bağlı)

Eski 11 commit'i de geri kazanmak istersen yazar adreslerini yeniden yazman gerekir. **Bu geçmişi değiştirir ve `--force` push gerektirir** — repo tek başına senin ve kimse fork'lamadıysa güvenli:

```bash
cd 42-Libft
git filter-branch --env-filter '
  if [ "$GIT_AUTHOR_EMAIL" != "198243462+Emir2M@users.noreply.github.com" ]; then
    export GIT_AUTHOR_EMAIL="198243462+Emir2M@users.noreply.github.com"
    export GIT_COMMITTER_EMAIL="198243462+Emir2M@users.noreply.github.com"
  fi
' --tag-name-filter cat -- --branches --tags
git push --force origin main
```

GitHub'ın grafiği yeniden hesaplaması birkaç saat sürebilir.

### Private repolar

4 reponun 3'ü private. Bunlardaki commit'lerin de grafikte görünmesi için:

**Settings → Public profile → Contributions & Activity** altında
**"Include private contributions on my profile"** kutusunu işaretle.

Sayılar değil sadece yoğunluk görünür, repo adları gizli kalır.

---

## 3. Yeniden üretme

Her şey:

```bash
python build.py
```

Sadece bilgi kartı — metin denerken hızlı tur, ağa çıkmaz:

```bash
python build.py --only-card
```

Sadece ısı haritası (fotoğraf/kart değişmediyse):

```bash
python build.py --only-heatmap
```

Kendi fotoğrafınla:

```bash
python build.py --photo fotograf.jpg
```

`preview.html` dosyasını tarayıcıda açarak GitHub'a göndermeden kontrol et. Sayfadaki butona basmak animasyonları baştan oynatır.

### Ayar noktaları

| Ne | Nerede |
|---|---|
| Kart içeriği, renkler, kullanıcı adı | `profile.json` |
| Portre kırpma sıkılığı | `prep_photo.py --crop-ratio 0.38` (küçült = yüze yaklaş) |
| Portre kontrastı | `prep_photo.py --gain 1.35` |
| ASCII çözünürlüğü | `profile.json` → `ascii.cols` (şu an 86) |
| Portre koyu/açık dengesi | `make_ascii_svg.py --gamma 1.0` |
| Toplam README genişliği | `make_readme.py` → `TOTAL_W = 860` |

Portre veya kart değişince `make_readme.py` sütun genişliklerini yeniden hesaplar — elle hizalama gerekmiyor.

### Neyin ne zaman güncellenmesi gerekiyor

| Parça | Kim günceller | Ne zaman |
|---|---|---|
| Isı haritası | **Kendi kendine** — GitHub Actions, her gün 09:17 | Elle bir şey yapmana gerek yok |
| Bilgi kartı | Sen | Bilgi değişince: yeni proje, yeni stack, yeni rol |
| ASCII portre | Sen | Profil fotoğrafını değiştirince |

Kartı veya portreyi güncelledikten sonra commit'leyip push'laman gerekir — ısı haritasının aksine bunlar statik dosyalar:

```bash
python build.py --only-card          # profile.json'u düzenledikten sonra
git add -A && git commit -m "chore: update info card" && git push
```

### Isı haritasını dolu haliyle test etme

Takvim henüz boşken animasyonun dolu halini görmek için örnek veriyle çizim yapabilirsin — gerçek grafiğe dokunmaz:

```bash
python scripts/render_heatmap_svg.py --data _demo-data.json --out _demo-heatmap.svg
```

`_` ile başlayan dosyalar `.gitignore` içinde, repoya girmezler.

---

## 4. Bağımlılıklar

Günlük otomasyon (GitHub Actions) sadece şunları kuruyor:

```
requests, beautifulsoup4
```

Portre üretimi yerelde ek olarak `pillow`, `numpy`, `opencv-python` ve `rembg` istiyor. `rembg` ilk çalıştırmada ~1 GB model indiriyor, sonraki çalıştırmalar hızlı. Yoksa da script çalışır, sadece arka planı silmez ve kırpmayı atlar.
