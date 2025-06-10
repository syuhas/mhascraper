import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os

BASE_URL = "https://www.samhsa.gov"

def is_valid_internal_link(href, root_path):
    return href.startswith(root_path)

def is_crawlable_page(url):
    blocked_exts = [".pdf", ".csv", ".doc", ".docx", ".zip", ".xls", ".xlsx"]
    parsed = urlparse(url)
    path = parsed.path.lower()
    if any(path.endswith(ext) for ext in blocked_exts):
        return False
    if "?" in url and "resource_type" in url:
        return False
    return True

def normalize_url(url):
    return url.rstrip("/")

def get_links(url, root_path):
    try:
        print(f"Visiting: {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return [], [], []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = []

        main_content = soup.find("div", class_="region-content") or soup.body
        for a in main_content.find_all("a", href=True):
            href = a["href"].split("#")[0].strip()
            full_url = urljoin(BASE_URL, href)
            parsed_url = urlparse(full_url)

            if parsed_url.netloc != "www.samhsa.gov":
                continue

            path = parsed_url.path
            links.append(normalize_url(full_url))

        links = list(set(link for link in links if normalize_url(link) != normalize_url(url)))
        links.sort()

        nested = []
        stop_here = []
        resources = []

        for link in links:
            path = urlparse(link).path
            if is_valid_internal_link(path, root_path):
                if is_crawlable_page(link):
                    nested.append(link)
                else:
                    resources.append(link)
            else:
                stop_here.append(link)

        return nested, stop_here, resources

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return [], [], []

def crawl_tree(url, root_path, visited, node):
    url = normalize_url(url)
    if url in visited:
        return
    visited.add(url)

    nested_links, stop_here, resources = get_links(url, root_path)

    node[url] = {
        "_stop_here": [],
        "_resources": resources
    }

    current = node[url]

    for link in nested_links:
        if is_valid_internal_link(urlparse(link).path, root_path) and is_crawlable_page(link):
            crawl_tree(link, root_path, visited, current)

    for link in stop_here:
        if is_valid_internal_link(urlparse(link).path, root_path) and is_crawlable_page(link):
            crawl_tree(link, root_path, visited, current)
        else:
            current["_stop_here"].append(link)





def print_structure_tree(structure, indent=0):
    for key, value in structure.items():
        if key in ["_stop_here", "_resources"]:
            if value:
                print("  " * indent + f"{key} ({len(value)})")
        else:
            print("  " * indent + f"{key}")
            if isinstance(value, dict):
                print_structure_tree(value, indent + 1)

def save_structure_to_json(structure, section_name):
    safe_name = section_name.replace("/", "_")
    os.makedirs("output", exist_ok=True)
    filename = f"output/{safe_name}_structure.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(structure, f, indent=2)
    print(f"Saved structure to {filename}")

if __name__ == "__main__":
    section = "substance-use/learn"
    start_url = f"{BASE_URL}/{section}"
    root_path = f"/{section}"

    visited = set()
    structure = {}
    crawl_tree(start_url, root_path, visited, structure)

    print_structure_tree(structure)
    save_structure_to_json(structure, section)

