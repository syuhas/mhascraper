# get_nested_structure_eqtmd.py
import json, os
from urllib.parse import urlparse
from collections import OrderedDict

BASE_URL = "https://www.equaltreatmentmd.org"
PAGES = [
    "/about-the-coalition",
    "/newsletter",
    "/contact-us",
    "/platform",
    "/maryland-resources",
    "/maryland-voices"
]

def build_structure():
    tree = OrderedDict()
    for page in PAGES:
        full_url = f"{BASE_URL}{page}"
        tree[full_url] = {}
    return tree

def save_to_json(data, filename):
    os.makedirs("./output/structure", exist_ok=True)
    with open(f"./output/structure/{filename}", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Structure saved to output/structure/{filename}")

def main():
    structure = build_structure()
    save_to_json(structure, "equaltreatment_structure.json")

if __name__ == "__main__":
    main()
