import os
import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urlparse, urljoin

BASE_URL = "https://www.equaltreatmentmd.org"
CONTENT_SELECTOR = 'main[data-content-field="main-content"]'
HTML_DIR = 'output/html'
TEXT_DIR = 'output/text'

def sanitize_path(url):
    path = urlparse(url).path.strip('/')
    return path if path else 'index'

def save_html(url, html):
    rel_path = sanitize_path(url)
    parts = rel_path.split('/')
    folder_path = os.path.join(HTML_DIR, *parts)
    os.makedirs(folder_path, exist_ok=True)
    out_path = os.path.join(folder_path, f"{parts[-1] or 'index'}.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"📝 Saved HTML: {out_path}")

def save_text(url, text):
    rel_path = sanitize_path(url)
    parts = rel_path.split('/')
    folder_path = os.path.join(TEXT_DIR, *parts)
    os.makedirs(folder_path, exist_ok=True)
    out_path = os.path.join(folder_path, f"{parts[-1] or 'index'}.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"📄 Saved Text: {out_path}")

# def extract_main_content(url):
#     try:
#         print(f"Visiting: {url}")
#         resp = requests.get(url, timeout=10)
#         if resp.status_code != 200:
#             print(f"⚠️ Skipped (HTTP {resp.status_code}): {url}")
#             return None, None
#         soup = BeautifulSoup(resp.text, 'html.parser')
#         main = soup.select_one(CONTENT_SELECTOR)
#         if not main:
#             print(f"⚠️ No main content for: {url}")
#             return None, None
#         return str(main), format_text(main)
#     except Exception as e:
#         print(f"❌ Error: {e} at {url}")
#         return None, None

def extract_main_content(url):
    try:
        print(f"Visiting: {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️  Skipped (HTTP {resp.status_code}): {url}")
            return None, None

        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.select_one("main") or soup.select_one("div.site-wrapper") or soup.body

        # Remove script and style tags
        for tag in main.find_all(['script', 'style']):
            tag.decompose()

        # Use format_text for structured, deduplicated output
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
                heading = get_text_with_links(node).strip()
                lines.append('\n' + heading)
                lines.append('-' * len(heading))
            elif name in ['p']:
                lines.append('')
                lines.append(indent + get_text_with_links(node).strip())
            elif name in ['ul', 'ol']:
                for li in node.find_all('li', recursive=False):
                    recurse(li, indent + "  ")
            elif name == 'li':
                lines.append(indent + "- " + get_text_with_links(node).strip())
            else:
                for child in node.children:
                    recurse(child, indent)

    def get_text_with_links(tag):
        parts = []
        for child in tag.descendants:
            if isinstance(child, NavigableString):
                parts.append(child.strip())
            elif isinstance(child, Tag) and child.name == 'a' and child.get('href'):
                anchor = child.get_text(strip=True)
                href = child['href']
                full_url = urljoin(BASE_URL, href)
                parts.append(f"{anchor} ({full_url})")
        return ' '.join(filter(None, parts))

    recurse(element)
    return "\n\n".join(line for line in lines if line.strip())


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
    with open("output/structure/equaltreatment_structure.json", "r", encoding="utf-8") as f:
        structure = json.load(f)

    process_structure(structure)

if __name__ == "__main__":
    main()
