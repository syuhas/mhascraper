import os

BASE_S3_URL = "http://samhsa-website.s3-website-us-east-1.amazonaws.com"
OUTPUT_DIR = "output"
WEBSITE_INDEX = "website/index.html"

accordion_id_counter = 0

def generate_index():
    sections = []

    for content_type in ["text", "html"]:
        path = os.path.join(OUTPUT_DIR, content_type)
        if not os.path.exists(path):
            continue

        global accordion_id_counter
        accordion_id = f"accordion-{accordion_id_counter}"
        accordion_id_counter += 1

        body = generate_nested_accordion(path, content_type)
        section = f"""
        <div class="accordion-item">
          <h2 class="accordion-header" id="heading-{content_type}">
            <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-{content_type}" aria-expanded="false" aria-controls="collapse-{content_type}">
              {content_type}
            </button>
          </h2>
          <div id="collapse-{content_type}" class="accordion-collapse collapse" aria-labelledby="heading-{content_type}" data-bs-parent="#rootAccordion">
            <div class="accordion-body">
              {body}
            </div>
          </div>
        </div>
        """
        sections.append(section)

    html = build_html("\n".join(sections))
    os.makedirs("website", exist_ok=True)
    with open(WEBSITE_INDEX, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Wrote index to {WEBSITE_INDEX}")


def generate_nested_accordion(current_path, content_type, rel_path=""):
    global accordion_id_counter

    entries = sorted(os.listdir(current_path))
    html = ['<ul class="list-unstyled">']

    for entry in entries:
        full_path = os.path.join(current_path, entry)
        rel_entry_path = os.path.join(rel_path, entry).replace("\\", "/")

        if os.path.isdir(full_path):
            acc_id = f"accordion-{accordion_id_counter}"
            accordion_id_counter += 1
            html.append(f'''
            <li>
              <div class="accordion" id="{acc_id}">
                <div class="accordion-item">
                  <h2 class="accordion-header" id="heading-{acc_id}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-{acc_id}" aria-expanded="false" aria-controls="collapse-{acc_id}">
                      {entry}
                    </button>
                  </h2>
                  <div id="collapse-{acc_id}" class="accordion-collapse collapse" aria-labelledby="heading-{acc_id}" data-bs-parent="#{acc_id}">
                    <div class="accordion-body">
                      {generate_nested_accordion(full_path, content_type, rel_entry_path)}
                    </div>
                  </div>
                </div>
              </div>
            </li>
            ''')
        elif entry.endswith(".txt") or entry.endswith(".html"):
            s3_url = f"{BASE_S3_URL}/{content_type}/{rel_entry_path}"
            html.append(f'''
            <li class="ms-3 mb-2">
              <strong>{entry}</strong><br/>
              <a href="{s3_url}" class="btn btn-sm btn-primary me-2" target="_blank">View</a>
              <a href="{s3_url}" download class="btn btn-sm btn-secondary">Download</a>
            </li>
            ''')

    html.append("</ul>")
    return "\n".join(html)


def build_html(body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>SAMHSA Scraper Index</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <style>
    body {{ padding: 2rem; }}
    ul {{ padding-left: 1rem; }}
    .btn {{ font-size: 0.8rem; }}
  </style>
</head>
<body>
  <div class="container">
    <h1 class="mb-3">SAMHSA Scraper Index</h1>
    <p class="text-muted">Directory of all structured text and HTML content, hosted on S3.</p>
    <div class="accordion" id="rootAccordion">
      {body}
    </div>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    generate_index()
