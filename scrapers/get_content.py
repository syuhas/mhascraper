import os
import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urlparse, urljoin

BASE_URL = "https://www.samhsa.gov"
CONTENT_SELECTOR = 'div#main.content-inner-regions[role=main]'
HTML_DIR = 'output/html'
TEXT_DIR = 'output/text'

def sanitize_path(url):
    path = urlparse(url).path.strip('/')
    return path if path else 'index'

def save_html(url, html):
    rel_path = sanitize_path(url)
    out_path = os.path.join(HTML_DIR, rel_path, "index.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"📝 Saved HTML: {out_path}")

def save_text(url, text):
    rel_path = sanitize_path(url)
    out_path = os.path.join(TEXT_DIR, rel_path, "index.txt")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"📄 Saved Text: {out_path}")

def extract_main_content(url):
    try:
        print(f"Visiting: {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Skipped (HTTP {resp.status_code}): {url}")
            return None, None
        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.select_one(CONTENT_SELECTOR)
        if not main:
            print(f"⚠️ No main content for: {url}")
            return None, None
        return str(main), format_text(main)
    except Exception as e:
        print(f"❌ Error: {e} at {url}")
        return None, None

def format_text(element):
    lines = []

    def recurse(node, indent=""):
        if isinstance(node, NavigableString):
            text = node.strip()
            if text:
                lines.append(indent + text)

        elif isinstance(node, Tag):
            name = node.name.lower()

            if name in ['script', 'style', 'nav', 'footer']:
                return  # skip

            if name.startswith('h') and name[1:].isdigit():
                heading = node.get_text(strip=True)
                link = extract_link_if_any(node)
                if link:
                    heading += f" (link: {link})"
                lines.append('\n' + heading)
                lines.append('-' * len(heading))
            elif name in ['p']:
                lines.append('')
                recurse_children(node)
            elif name in ['ul', 'ol']:
                recurse_children(node, indent + "  ")
            elif name == 'li':
                lines.append(indent + "- " + node.get_text(strip=True))
            else:
                recurse_children(node)

    def recurse_children(parent, indent=""):
        for child in parent.children:
            recurse(child, indent)

    def extract_link_if_any(tag):
        """Extract a valid internal link path, if any, from the tag"""
        a = tag.find('a', href=True)
        if not a:
            return None
        href = a['href']
        full_url = urljoin(BASE_URL, href)
        if full_url.startswith(BASE_URL):
            return urlparse(full_url).path
        return None

    recurse(element)
    return "\n".join(lines).strip()


def process_structure(structure):
    for url, children in structure.items():
        html, text = extract_main_content(url)
        if html:
            save_html(url, html)
        if text:
            save_text(url, text)
        if isinstance(children, dict):
            process_structure(children)

def main():
    with open("output/structure/find-help_structure.json", "r", encoding="utf-8") as f:
        structure = json.load(f)

    process_structure(structure)

if __name__ == "__main__":
    main()
