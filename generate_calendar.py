import time
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

# URLs dels calendaris
URLS = [
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79637",
    "https://www.basquetcatala.cat/partits/calendari_equip_global/53/79640",
]


def fetch_matches(url):
    matches = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"Carregant: {url}")
        page.goto(url, timeout=60000)

        # Esperar que la taula carregui
        page.wait_for_selector("table")

        rows = page.query_selector_all("table tr")

        current_date = None

        for row in rows:
            cols = [c.inner_text().strip() for c in row.query_selector_all("td")]

            if not cols:
                continue

            # Files amb data
            if len(cols) == 1 and "/" in cols[0]:
                current_date = cols[0]
                continue

            # Files amb partits
            if len(cols) >= 5 and current_date:
                try:
                    hora = cols[1]
                    local = cols[2]
                    visitant = cols[3]
                    categoria = cols[4]
                    lloc = cols[5] if len(cols) > 5 else ""

                    matches.append((current_date, hora, local, visitant, categoria, lloc))
                except:
                    continue

        browser.close()

    print(f"Partits trobats: {len(matches)}")
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
        matches = fetch_matches(url)
        all_matches.extend(matches)
        time.sleep(2)

    print(f"TOTAL PARTITS: {len(all_matches)}")

    generate_ics(all_matches, "calendari_basket_almeda.ics")
