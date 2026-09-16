"""GitHub katki takvimini token'siz cek ve data/contributions.json yaz.

GitHub, profil sayfasinin kendi kullandigi HTML parcasini herkese acik
sunar: https://github.com/users/<username>/contributions
Ne GraphQL API'sine ne de personal access token'a ihtiyac var.
"""
import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "profile.json")
OUT = os.path.join(ROOT, "data", "contributions.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def load_username():
    username = os.environ.get("GH_USERNAME")
    if username:
        return username
    with open(CONFIG, encoding="utf-8") as fh:
        username = json.load(fh)["username"]
    if not username or username == "KULLANICI_ADIN":
        sys.exit("profile.json icindeki 'username' alanini doldur (veya GH_USERNAME ver).")
    return username


def fetch_html(username):
    url = "https://github.com/users/%s/contributions" % username
    resp = requests.get(url, headers={"User-Agent": UA, "Accept": "text/html"}, timeout=30)
    if resp.status_code == 404:
        sys.exit("GitHub kullanicisi bulunamadi: %s" % username)
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    """HTML parcasindan (tarih, sayi, seviye) uclulerini cikar.

    GitHub markup'i zaman zaman degisiyor: gun sayisi bazen td'nin kendi
    data-count'unda, bazen de eslesen <tool-tip> metninde duruyor. Ikisini de
    dene, ayrica metinden sayi ayiklamaya geri dus.
    """
    soup = BeautifulSoup(html, "html.parser")

    tips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tips[target] = tip.get_text(" ", strip=True)

    days = []
    cells = soup.find_all("td", class_="ContributionCalendar-day")
    for cell in cells:
        day = cell.get("data-date")
        if not day:
            continue
        level = int(cell.get("data-level") or 0)

        count = cell.get("data-count")
        if count is None:
            text = tips.get(cell.get("id", ""), "") or cell.get("aria-label", "")
            match = re.search(r"(\d[\d,\.]*)\s+contribution", text)
            if match:
                count = match.group(1).replace(",", "").replace(".", "")
            elif re.search(r"\bNo contributions\b", text, re.I):
                count = 0
            else:
                count = 0
        days.append({"date": day, "count": int(count), "level": level})

    if not days:
        sys.exit("Katki hucresi bulunamadi - GitHub markup'i degismis olabilir.")

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    by_date = {d["date"]: d["count"] for d in days}
    total = sum(by_date.values())

    # En uzun seri
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)

    # Guncel seri: bugunden geriye say. Bugun henuz bos olabilir, o yuzden
    # sifirsa dunden baslamak seriyi haksiz yere kirmiyor.
    today = date.fromisoformat(days[-1]["date"])
    cursor = today
    if by_date.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    current = 0
    while by_date.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)

    best = max(days, key=lambda d: d["count"])

    monthly = OrderedDict()
    for day in days:
        key = day["date"][:7]
        monthly[key] = monthly.get(key, 0) + day["count"]

    active = sum(1 for d in days if d["count"] > 0)
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active,
        "monthly": monthly,
        "average": round(total / len(days), 2) if days else 0,
    }


def main():
    username = load_username()
    days = parse_days(fetch_html(username))
    payload = {
        "username": username,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"from": days[0]["date"], "to": days[-1]["date"]},
        "days": days,
        "stats": derive_stats(days),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    stats = payload["stats"]
    print("%s -> %d gun, %d katki (seri: %d, en uzun: %d)"
          % (username, len(days), stats["total"], stats["current_streak"], stats["longest_streak"]))


if __name__ == "__main__":
    main()
