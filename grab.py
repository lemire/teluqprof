import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Base URL for the repository
BASE_URL = "https://r-libre.teluq.ca/"
MAIN_URL = BASE_URL + "profs.html"
MAX_CONCURRENT_REQUESTS = 10


def count_journal_articles(html):
    soup = BeautifulSoup(html, "html.parser")

    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        title = " ".join(heading.get_text(" ", strip=True).split())
        if title.lower() != "articles de revues":
            continue

        count = 0
        for sibling in heading.find_next_siblings():
            if sibling.name and re.match(r"^h[1-6]$", sibling.name, re.IGNORECASE):
                break
            if sibling.name in {"p", "li"} and sibling.get_text(" ", strip=True):
                count += 1
        return count

    return 0


def fetch_professor_result(index, total, name, url):
    count = 0
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            count = count_journal_articles(r.text)
    except Exception:
        # Some links may 404, timeout, or fail — that's OK as per the request
        count = 0
    return index, total, name, count

print("Fetching the main professors list page...")
try:
    response = requests.get(MAIN_URL, timeout=15)
    response.raise_for_status()
except Exception as e:
    print(f"Failed to fetch main page: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")

# Extract all professor profile links
# They follow the pattern: view/person/encoded-email.html
professors = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    if href.startswith("view/person/") and href.endswith(".html"):
        name = a.get_text().strip()
        if name and name != "":  # skip empty or header links
            full_url = BASE_URL + href
            professors.append((name, full_url))

print(f"Found {len(professors)} professor profile links.")

# Process each professor page
results = []
with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
    futures = [
        executor.submit(fetch_professor_result, i, len(professors), name, url)
        for i, (name, url) in enumerate(professors, 1)
    ]

    for future in as_completed(futures):
        index, total, name, count = future.result()
        print(f"[{index}/{total}] Processed: {name} ...", end="\r")
        results.append((name, count))

# Sort: by count descending, then by name alphabetically
results.sort(key=lambda x: (-x[1], x[0]))

# Print final results
print("\n" + "=" * 60)
print("Professor | Number of 'Articles de revues'")
print("=" * 60)
for name, count in results:
    print(f"{name:<40} | {count:>3}")
print("=" * 60)
print(f"Total professors processed: {len(results)}")
