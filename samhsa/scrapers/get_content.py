import os
import json
import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urlparse, urljoin

BASE_URL = "https://www.samhsa.gov"
CONTENT_SELECTOR = 'div#main[role=main]'
HTML_DIR = 'output/html'
TEXT_DIR = 'output/text'

def download_pdf(pdf_url, output_folder):
    try:

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            # 'Referer': url,  # Optional but can help when the site checks origin
        }
        filename = pdf_url.split('/')[-1]
        response = requests.get(pdf_url, headers=headers, timeout=10)
        response.raise_for_status()
        pdf_path = os.path.join(output_folder, filename)
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        print(f"📥 Downloaded PDF: {pdf_url}")
    except Exception as e:
        print(f"❌ Failed to download {pdf_url}: {e}")

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

def save_text(url, text, pdfs):
    rel_path = sanitize_path(url)
    parts = rel_path.split('/')
    folder_path = os.path.join(TEXT_DIR, *parts)
    os.makedirs(folder_path, exist_ok=True)
    out_path = os.path.join(folder_path, f"{parts[-1] or 'index'}.txt")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"📄 Saved Text: {out_path}")
    # if pdfs:
    #     for pdf_url in pdfs:
    #         download_pdf(pdf_url, folder_path)

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
            return None, None, None

        soup = BeautifulSoup(resp.text, 'html.parser')
        main = soup.select_one(CONTENT_SELECTOR)

        # Remove script and style tags
        for tag in main.find_all(['script', 'style']):
            tag.decompose()

        text, pdfs = format_text(main)
        print(pdfs)
        return str(main), text, pdfs

    except Exception as e:
        print(f"❌ Error: {e} at {url}")
        return None, None, None

def format_text(element):
    lines = []
    pdf_links = []
    filter_text = {'body', 
                   'intro', 
                   'hero', 
                   'expand all', 
                   'collapse all', 
                   'skip to main content', 
                   'title', 'last updated', 
                   'last updated:', 
                   'spanish language toggle', 
                   'español', 'breadcrumbs', 
                   'your browser is not supported',
                   'switch to chrome, edge, firefox or safari',
                   'main page content',
                   'source'
    }

    def recurse(node, indent=""):
        if isinstance(node, NavigableString):
            text = node.strip()
            if text and text.lower() not in filter_text and not (text.startswith(f) for f in filter_text):
                lines.append(indent + text)

        elif isinstance(node, Tag):
            name = node.name.lower()

            if name in ['script', 'style', 'nav', 'footer']:
                return  # skip

            if name.startswith('h') and name[1:].isdigit():
                heading = get_text_with_links(node).strip()
                lines.append('\n' + heading)
                lines.append('-' * len(heading))
            elif name in ['button']:
                lines.append('')
                lines.append(f'(button) {indent + get_text_with_links(node)} (button)')
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
        seen_strings = set()
        for child in tag.descendants:
            if isinstance(child, NavigableString):
                text = child.strip()
                if text:
                    parent = child.find_parent('a', href=True)
                    if parent:
                        full_url = urljoin(BASE_URL, parent['href'])
                        combined = f"{text} ({full_url})"
                        if combined not in seen_strings:
                            seen_strings.add(combined)
                            parts.append(combined)
                            # parts.append(f"{text} ({full_url})")
                    elif not parent:
                        parts.append(text)
                        seen_strings.add(text)
            # if isinstance(child, NavigableString):
            #     parts.append(child.strip())
            elif isinstance(child, Tag) and child.name == 'a' and child.get('href'):
                anchor = child.get_text(strip=True)
                href = child['href']
                full_url = urljoin(BASE_URL, href)
                combined = f"{anchor} ({full_url})"
                if combined not in seen_strings:
                    seen_strings.add(combined)
                    parts.append(f"{anchor} ({full_url})")
                    if href.lower().endswith('pdf'):
                        pdf_links.append(full_url)

        return ' '.join(filter(None, parts))

    recurse(element)
    return "\n\n".join(line for line in lines if line.strip()), pdf_links


def process_structure(structure):
    for url, children in structure.items():
        html, text, pdfs = extract_main_content(url)
        if html:
            save_html(url, html)
        if text:
            save_text(url, text, pdfs)
        if isinstance(children, dict):
            process_structure(children)

def main():
    with open("output/structure/communities_structure.json", "r", encoding="utf-8") as f:
        structure = json.load(f)

    process_structure(structure)

if __name__ == "__main__":
    main()
