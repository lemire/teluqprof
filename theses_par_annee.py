import re
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

URL = "https://r-libre.teluq.ca/view/theses-memoires/phd.html"


def normalize_spaces(text):
    # Replace non-breaking spaces and collapse repeated whitespace.
    text = text.replace("\xa0", " ")
    return " ".join(text.split())


def split_directors(raw_directors):
    # Normalize separators like ';' and ' et ' to get individual names.
    parts = re.split(r"\s*;\s*|\s+et\s+", raw_directors)
    return [p.strip(" .") for p in parts if p.strip(" .")]


def parse_entries(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    for p in soup.find_all("p"):
        text = normalize_spaces(p.get_text(" ", strip=True))

        year_match = re.search(r"\((19|20)\d{2}\)", text)
        if not year_match:
            continue

        direction_match = re.search(r"Direction\s*:\s*(.+)$", text, flags=re.IGNORECASE)
        if not direction_match:
            continue

        year = int(year_match.group(0).strip("()"))

        title_link = p.find("a")
        title = normalize_spaces(title_link.get_text(" ", strip=True)) if title_link else "(sans titre)"

        author = text.split("(", 1)[0].strip(" .")

        directors_raw = direction_match.group(1).strip(" .")
        directors = split_directors(directors_raw)

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
            print(f"- {item['author']}")
            print(f"  Direction: {directors}")

    print(f"\nTotal theses parsed: {len(entries)}")


if __name__ == "__main__":
    main()
