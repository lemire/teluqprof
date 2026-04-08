import re
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

URL = "https://r-libre.teluq.ca/view/theses-memoires/masters.html"
SECTION_TITLE = "Technologie de l'information"


def normalize_spaces(text):
    text = text.replace("\xa0", " ")
    return " ".join(text.split())


def split_directors(raw_directors):
    # Handles both separator styles used on the page.
    parts = re.split(r"\s*;\s*|\s+et\s+", raw_directors)
    return [p.strip(" .") for p in parts if p.strip(" .")]


def get_ti_section_paragraphs(soup):
    start_heading = None
    for h2 in soup.find_all("h2"):
        heading_text = normalize_spaces(h2.get_text(" ", strip=True))
        if heading_text == SECTION_TITLE:
            start_heading = h2
            break

    if start_heading is None:
        return []

    paragraphs = []
    for sibling in start_heading.find_next_siblings():
        if sibling.name == "h2":
            break
        if sibling.name == "p":
            paragraphs.append(sibling)

    return paragraphs


def parse_entries(html):
    soup = BeautifulSoup(html, "html.parser")
    paragraphs = get_ti_section_paragraphs(soup)
    entries = []

    for p in paragraphs:
        text = normalize_spaces(p.get_text(" ", strip=True))

        year_match = re.search(r"\((19|20)\d{2}\)", text)
        if not year_match:
            continue
        year = int(year_match.group(0).strip("()"))

        author = text.split("(", 1)[0].strip(" .")

        title_link = p.find("a")
        title = normalize_spaces(title_link.get_text(" ", strip=True)) if title_link else "(sans titre)"

        direction_match = re.search(r"Direction\s*:\s*(.+)$", text, flags=re.IGNORECASE)
        if direction_match:
            directors = split_directors(direction_match.group(1))
        else:
            directors = []

        entries.append(
            {
                "year": year,
                "author": author,
                "title": title,
                "directors": directors,
            }
        )

    return entries


def main():
    response = requests.get(URL, timeout=20)
    response.raise_for_status()

    entries = parse_entries(response.text)

    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry["year"]].append(entry)

    for year in sorted(grouped.keys(), reverse=True):
        print(f"\n{year}")
        print("-" * 4)
        for item in grouped[year]:
            directors = ", ".join(item["directors"]) if item["directors"] else "(direction inconnue)"
            print(f"- {item['author']})")
            print(f"  Direction: {directors}")

    print(f"\nTotal master theses (TI) parsed: {len(entries)}")


if __name__ == "__main__":
    main()
