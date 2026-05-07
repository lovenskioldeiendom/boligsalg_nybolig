"""
Minimal test: henter 3 Finn-prosjektsider og rapporterer hva som faktisk
ligger i HTML-en. Formålet er å avgjøre om scraping av Finn er
gjennomførbart fra GitHub Actions før vi bygger noe stort.

Kjøring: python test_finn.py
"""

import re
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup

# Tre kjente, aktive prosjektannonser i Akershus.
# Disse må være "project" (med enhetsliste), ikke "projectsingle" eller "planned".
TEST_URLS = [
    ("Helgerudkvartalet (Bærum)", "https://www.finn.no/realestate/project/ad.html?finnkode=397833531"),
    ("Storøykilen Kvartal 4 trinn 3 (Bærum)", "https://www.finn.no/realestate/project/ad.html?finnkode=368269668"),
    ("Ballerud Hageby trinn 1 (Bærum)", "https://www.finn.no/realestate/project/ad.html?finnkode=319934863"),
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str) -> tuple[int, str]:
    """Returnerer (HTTP-status, body)."""
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "nb-NO,nb;q=0.9",
    })
    try:
        with urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        return e.code, body
    except URLError as e:
        return -1, str(e)


def analyze(html: str) -> dict:
    """Sjekker om HTML-en inneholder data vi trenger."""
    if not html:
        return {"error": "tom respons"}

    result = {
        "size_kb": round(len(html) / 1024, 1),
        "has_finn_brand": "FINN" in html or "finn.no" in html,
    }

    # Identifiser bot-vegger
    lower = html.lower()
    if "captcha" in lower or "are you human" in lower:
        result["bot_wall"] = "CAPTCHA detected"
    elif "access denied" in lower or "forbidden" in lower:
        result["bot_wall"] = "Access denied"
    elif "cloudflare" in lower and len(html) < 50000:
        result["bot_wall"] = "Cloudflare challenge (mistenkt)"

    soup = BeautifulSoup(html, "html.parser")

    # Tittel
    title = soup.find("title")
    result["title"] = title.get_text(strip=True)[:120] if title else None

    # Lete etter enhetstabell
    units = []
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        if "enhet" in headers and "totalpris" in headers:
            tbody = table.find("tbody")
            rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
            for row in rows:
                cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if cells and cells[0]:
                    units.append(cells[:5])
            break  # Tar bare første matchende tabell

    result["units_found"] = len(units)
    result["sample_units"] = units[:3]

    # Sjekk om vi finner pris-info i andre former
    if not units:
        # Kanskje grid med <div>-er istedenfor table?
        price_mentions = len(re.findall(r"\d{1,3}(?:\s\d{3}){1,2}\s*kr", html))
        result["price_mentions_in_html"] = price_mentions

    return result


def main() -> int:
    print(f"Tester Finn-scraping fra denne maskinen...")
    print(f"User-Agent: {USER_AGENT[:50]}...\n")

    successes = 0
    for name, url in TEST_URLS:
        print(f"━━━ {name} ━━━")
        print(f"URL: {url}")
        status, body = fetch(url)
        print(f"HTTP-status: {status}")

        if status != 200:
            print(f"FEILET. Første 500 tegn av respons:")
            print(body[:500])
            print()
            continue

        result = analyze(body)
        print(f"Størrelse: {result.get('size_kb')} KB")
        print(f"Tittel: {result.get('title')}")
        if result.get("bot_wall"):
            print(f"⚠ BOT-VEGG: {result['bot_wall']}")
        else:
            print(f"Enheter funnet: {result.get('units_found', 0)}")
            for u in result.get("sample_units", []):
                print(f"  → {u}")
            if result.get("units_found", 0) > 0:
                successes += 1
        print()

    print(f"━━━ OPPSUMMERING ━━━")
    print(f"Vellykkede oppslag: {successes} / {len(TEST_URLS)}")
    if successes == len(TEST_URLS):
        print("✓ Finn-scraping ser ut til å virke. Trygt å bygge resten.")
        return 0
    elif successes > 0:
        print("⚠ Delvis suksess. Mulig at Finn varierer struktur eller rate-limiterer.")
        return 1
    else:
        print("✗ Ingen oppslag virket. Finn blokkerer eller har endret struktur.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
