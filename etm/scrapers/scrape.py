import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin

# Load structure
with open("output/structure/equaltreatment_structure.json", "r") as f:
    page_segments = json.load(f)

base_url = "https://www.equaltreatmentmd.org"
output_dir = "markdown_output"
os.makedirs(output_dir, exist_ok=True)

# Pages to visit (include homepage)
urls = [base_url] + list(page_segments.keys())

def clean_and_format_text(soup, page_url):
    blacklist = ['script', 'style', 'nav', 'footer', 'header']
    seen = set()
    lines = []

    # Main content wrapper
    main = soup.find("div", {"id": "siteWrapper"}) or soup.body

    if not main:
        return ""

    for tag in main.find_all(True):
        if tag.name in blacklist:
            continue

        text = tag.get_text(strip=True, separator=' ')
        if not text or text in seen or len(text) < 3:
            continue
        seen.add(text)

        if tag.name == 'a' and tag.has_attr('href'):
            href = tag['href']
            if not href.startswith('#'):
                full_url = urljoin(page_url, href)
                text = f"[{text}]({full_url})"
        lines.append(text)

    return "\n\n".join(lines)

# Scrape each page
for url in urls:
    print(f"Scraping: {url}")
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        content = clean_and_format_text(soup, url)

        file_slug = url.rstrip('/').split("/")[-1] or "home"
        output_path = os.path.join(output_dir, f"{file_slug}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
