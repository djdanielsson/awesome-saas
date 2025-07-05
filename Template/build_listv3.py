import json
import requests
import os
import random
import string
import re

# List of source template URLs
template_urls = [
    'https://raw.githubusercontent.com/pi-hosted/pi-hosted/master/template/portainer-v2-amd64.json',
    'https://raw.githubusercontent.com/donspablo/awesome-saas/master/Template/portainer-v2.json',
    'https://raw.githubusercontent.com/SelfhostedPro/selfhosted_templates/master/Template/template.json',
    'https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json',
    'https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates.json',
    'https://raw.githubusercontent.com/technorabilia/portainer-templates/refs/heads/main/lsio/templates/templates.json'
]

templates = []
unique_titles = set()

def sanitize_key(text):
    return re.sub(r'[\s\-]+', '', text.lower().strip())

def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return

    try:
        data = json.loads(response.text)
        raw_templates = data.get("templates", [])

        for template in raw_templates:
            title = template.get("title", "").strip()
            description = template.get("description", "").strip()
            title_key = sanitize_key(title)

            if not title or not description or "[DEPRECATED]" in description.upper():
                continue

            if title_key in unique_titles:
                continue

            repo = template.get("repository", {})
            repo_url = repo.get("url", "").strip()
            stackfile = repo.get("stackfile", "").lstrip("./")

            if not repo_url or not stackfile:
                continue

            # Ensure stackfile starts with "/"
            if not stackfile.startswith("/"):
                stackfile = "/" + stackfile

            # Build Portainer v3 template structure
            new_template = {
                "title": title,
                "description": description,
                "type": "stack",  # default type
                "platforms": [template.get("platform", "linux")],
                "categories": template.get("categories", []),
                "repository": {
                    "url": repo_url,
                    "stackfile": stackfile
                }
            }

            # Optional: add logo if present and not empty
            logo = template.get("logo", "").strip()
            if logo:
                new_template["logo"] = logo

            templates.append(new_template)
            unique_titles.add(title_key)

    except Exception as e:
        print(f"❌ Error parsing {url}: {e}")

# Process all source URLs
for url in template_urls:
    print(f"📥 Fetching: {url}")
    get_data(url)

# Sort and assign IDs
templates_sorted = sorted(templates, key=lambda t: t["title"].lower())
for i, t in enumerate(templates_sorted, start=1):
    t["id"] = str(i)

final_output = {
    "version": "3",
    "templates": templates_sorted
}

# Write to file
output_file = "portainer-v3-latest.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Generated {len(templates_sorted)} valid Portainer v3 templates.")
print(f"📁 Output saved to {output_file}")
