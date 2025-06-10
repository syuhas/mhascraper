import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import os

BASE_URL = "https://www.samhsa.gov"
blocked_extensions = [".pdf", ".csv", ".doc", ".docx", ".zip", ".xls", ".xlsx"]

def is_file_url(url):
    return any(url.lower().endswith(ext) for ext in blocked_extensions)

def normalize_url(url):
    return url.rstrip("/")

def is_valid_nested_url(link, root_path):
    path = urlparse(link).path.rstrip("/")
    return path.startswith(root_path) and path != root_path and not is_file_url(link)

def get_links_from_page(url, root_path):
    try:
        print(f"Visiting: {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        # main = soup.find("div", class_="region-content") or soup.body
        main = soup.find("div", id="main") or soup.find("div", class_="region-content") or soup.body
        anchors = main.find_all("a", href=True)
        links = set()

        for tag in anchors:
            href = tag["href"].split("#")[0].strip()
            full_url = normalize_url(urljoin(BASE_URL, href))
            if full_url.startswith(BASE_URL) and is_valid_nested_url(full_url, root_path):
                links.add(full_url)

        return sorted(links)
    except Exception as e:
        print(f"Error visiting {url}: {e}")
        return []

def crawl_all_nested_links(start_url, root_path):
    visited = set()
    to_visit = [start_url]
    all_links = set()

    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        all_links.add(current)

        children = get_links_from_page(current, root_path)
        to_visit.extend([link for link in children if link not in visited])

    return sorted(all_links)

def insert_path(tree, full_url, root_path):
    rel_path = urlparse(full_url).path[len(root_path):].strip("/").split("/")
    current = tree
    base = BASE_URL + root_path
    running_path = base

    for part in rel_path:
        running_path = f"{running_path}/{part}".rstrip("/")
        if running_path not in current:
            current[running_path] = {}
        current = current[running_path]

def build_tree_from_links(links, root_url):
    root_path = urlparse(root_url).path
    tree = {root_url: {}}

    for link in links:
        if link == root_url:
            continue
        insert_path(tree[root_url], link, root_path)

    return tree

def save_to_json(data, filename):
    os.makedirs("output", exist_ok=True)
    dirs = filename.split("/")
    for i in range(len(dirs) - 1):
        os.makedirs(os.path.join("output", *dirs[:i + 1]), exist_ok=True)
    with open(os.path.join("output", filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved to output/{filename}")

def main():
    section = "find-help"
    print(f"Scraping {section} section...")
    root_url = f"{BASE_URL}/{section}"
    root_path = urlparse(root_url).path

    all_links = crawl_all_nested_links(root_url, root_path)
    tree = build_tree_from_links(all_links, root_url)
    save_to_json(tree, f"structure/{section}_structure.json")

if __name__ == "__main__":
    main()
