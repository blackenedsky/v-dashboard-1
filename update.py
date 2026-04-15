import urllib.request
import json
import time
from datetime import datetime

BASE = "https://transparenz.vorarlberg.at/api/data/vtr.view_foerderungen_pers"
OUTPUT = "data.json"
PAGE_SIZE = 100

def fetch_page(page, extra=""):
    url = f"{BASE}?page={page}&size={PAGE_SIZE}&sort[0][field]=auszahlungsdatum&sort[0][dir]=desc{extra}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

# Bestehende Daten laden
with open(OUTPUT, "r", encoding="utf-8") as f:
    existing = json.load(f)

existing_data = existing.get("data", [])
last_downloaded = existing.get("downloaded", "2020-01-01")[:10]
print(f"Bestehende Einträge: {len(existing_data)}")
print(f"Letzter Download: {last_downloaded}")

# Bestehende IDs als Set für schnellen Duplikat-Check
# Da es keine ID gibt, nutzen wir empfänger+datum+betrag als Key
def key(r):
    return f"{r.get('empfänger','')}-{r.get('auszahlungsdatum','')}-{r.get('auszahlungsbetrag','')}"

existing_keys = set(key(r) for r in existing_data)

# Neue Einträge holen (nur erste Seiten bis wir auf bekannte stoßen)
new_entries = []
page = 1
done = False

while not done:
    try:
        d = fetch_page(page)
        for r in d["data"]:
            k = key(r)
            if k in existing_keys:
                done = True
                break
            new_entries.append(r)
        if page >= d["last_page"]:
            done = True
        page += 1
        time.sleep(0.3)
    except Exception as e:
        print(f"Fehler auf Seite {page}: {e}")
        break

print(f"Neue Einträge gefunden: {len(new_entries)}")

# Neue Einträge vorne einfügen
all_data = new_entries + existing_data

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "downloaded": datetime.now().isoformat(),
        "total": len(all_data),
        "data": all_data
    }, f, ensure_ascii=False, indent=2)

print(f"Fertig! Gesamt: {len(all_data)} Einträge")
