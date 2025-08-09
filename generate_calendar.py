import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path

# URLs dels calendaris
URLS = [
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79637",  # Júnior
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79640",  # Infantil
]

def fetch_matches(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    matches = []
    rows = soup.select("table tr")  # Files de la taula

    current_date = None
    for row in rows:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if not cols:
            continue
        # Si la fila comença amb una data, actualitza la data actual
        if cols[0]:
            current_date = cols[0]

        # Comprovem que hi ha almenys 6 columnes per ser un partit
        if len(cols) >= 6 and current_date:
            hora = cols[1]
            local = cols[2]
            visitant = cols[3]
            categoria = cols[4]
            lloc = cols[5]
            matches.append((current_date, hora, local, visitant, categoria, lloc))
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
            continue  # Salta entrades amb format erroni

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
        all_matches.extend(fetch_matches(url))
    generate_ics(all_matches, "calendari_basket_almeda.ics")
