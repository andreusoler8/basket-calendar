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
    # Extreure ID final de la URL
    team_id = url.split("/")[-1]

    api_url = f"https://www.basquetcatala.cat/api/partits/calendari_equip_global/{team_id}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    resp = requests.get(api_url, headers=headers)
    resp.raise_for_status()

    data = resp.json()

    matches = []

    for item in data.get("data", []):
        try:
            date_str = item.get("data")  # format: "06/09/2025"
            time_str = item.get("hora")  # "16:45"

            home = item.get("equip_local")
            away = item.get("equip_visitant")
            categoria = item.get("competicio")
            location = item.get("camp")

            if date_str and time_str:
                matches.append((date_str, time_str, home, away, categoria, location))
        except Exception as e:
            print("Error parsejant:", item)

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
