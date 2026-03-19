import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
import time

# URLs dels calendaris
URLS = [
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79637",
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79640",
]

def fetch_matches(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept-Language": "ca-ES,ca;q=0.9,en;q=0.8",
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    matches = []
    rows = soup.find_all("tr")

    current_date = None

    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        if not cols:
            continue

        # Detectar files amb només la data
        if len(cols) == 1 and "/" in cols[0]:
            current_date = cols[0]
            continue

        # Files amb dades de partit
        if len(cols) >= 5 and current_date:
            try:
                hora = cols[1]
                local = cols[2]
                visitant = cols[3]
                categoria = cols[4]
                lloc = cols[5] if len(cols) > 5 else ""

                matches.append((current_date, hora, local, visitant, categoria, lloc))
            except Exception as e:
                print("Error processant fila:", cols)
                continue

    return matches


def generate_ics(matches, output_path):
    def format_dt(dt):
        return dt.strftime("%Y%m%dT%H%M%S")

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Basket Almeda//Calendari//CA"
    ]

    for date_str, time_str, home, away, category, location in matches:
        try:
            start_dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        except ValueError:
            print("Error amb data:", date_str, time_str)
            continue

        end_dt = start_dt + timedelta(hours=1, minutes=30)
        uid = f"{home}-{away}-{start_dt.strftime('%Y%m%d%H%M')}@basketalmeda"

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{format_dt(datetime.utcnow())}Z",
            f"DTSTART;TZID=Europe/Madrid:{format_dt(start_dt)}",
            f"DTEND;TZID=Europe/Madrid:{format_dt(end_dt)}",
            f"SUMMARY:{home} vs {away}",
            f"DESCRIPTION:{category}",
            f"LOCATION:{location}",
            "END:VEVENT"
        ])

    ics_lines.append("END:VCALENDAR")
    Path(output_path).write_text("\n".join(ics_lines), encoding="utf-8")
    print(f"ICS creat a {output_path}")


if __name__ == "__main__":
    all_matches = []

    for url in URLS:
        print(f"Carregant: {url}")
        matches = fetch_matches(url)
        print(f"Partits trobats: {len(matches)}")
        all_matches.extend(matches)

        time.sleep(2)  # Evitar bloquejos

    print(f"TOTAL PARTITS: {len(all_matches)}")

    generate_ics(all_matches, "calendari_basket_almeda.ics")
