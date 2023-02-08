import json
import requests
import os
import random
import string
import re

template_urls = [
    'https://raw.githubusercontent.com/pi-hosted/pi-hosted/master/template/portainer-v2-amd64.json',
    'https://raw.githubusercontent.com/donspablo/awesome-saas/master/Template/portainer-v2.json',
    'https://raw.githubusercontent.com/SelfhostedPro/selfhosted_templates/master/Template/template.json',
    'https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json',
    'https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates.json'
]

templates = []
unique_names = set()

def sanitize_string(text):
    return re.sub(r'\s+|-', '', text.lower())

def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=5))
    filename = f"/tmp/{random_suffix}_{os.path.basename(url)}"

    with open(filename, 'wb') as file:
        file.write(response.content)

    with open(filename, 'r', encoding='utf-8') as json_file:
        try:
            data = json.load(json_file)
            for template in data.get("templates", []):
                title_key = sanitize_string(template.get("title", ""))
                description = template.get("description", "")
                if title_key in unique_names or not description or "[DEPRECATED]" in description:
                    continue

                # Skip if no valid repository (v3 requires URL and stackfile)
                repo = template.get("repository")
                if not repo or "url" not in repo or not repo.get("stackfile"):
                    continue

                unique_names.add(title_key)

                v3_template = {
                    "title": template.get("title", "Untitled"),
                    "description": description,
                    "categories": template.get("categories", []),
                    "logo": template.get("logo", ""),
                    "platforms": [template.get("platform", "linux")],
                    "repository": {
                        "url": repo["url"],
                        "stackfile": repo["stackfile"]
                    }
                }

                # Remove empty logo fields
                if not v3_template["logo"]:
                    del v3_template["logo"]

                templates.append(v3_template)
        except Exception as e:
            print(f"Error parsing {url}: {e}")

# Process URLs
for url in template_urls:
    get_data(url)

# Sort templates by title
sorted_templates = sorted(templates, key=lambda d: d["title"].lower())

# Assign sequential numeric IDs
for idx, template in enumerate(sorted_templates, start=1):
    template["id"] = str(idx)

# Final JSON structure
final_data = {
    "version": "3",
    "templates": sorted_templates
}

# Write output
output_file = "portainer-v3-latest.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

print(f"✔ Generated {len(sorted_templates)} valid Portainer v3 templates.")
print(f"📁 Output saved to {output_file}")
