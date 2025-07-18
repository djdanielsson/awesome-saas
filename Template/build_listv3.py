import json
import requests
import re

# List of source template URLs
template_urls = [
    'https://raw.githubusercontent.com/pi-hosted/pi-hosted/refs/heads/master/template/portainer-v3-amd64.json',
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

def determine_type(template):
    # type=1 container if "image" key present, else type=2 stack if "repository" key present
    if "image" in template:
        return 1
    elif "repository" in template:
        return 2
    else:
        return 2  # fallback to stack type

def get_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return

    try:
        data = response.json()
        raw_templates = data.get("templates", [])

        for template in raw_templates:
            title = template.get("title", "").strip()
            description = template.get("description", "").strip()
            title_key = sanitize_key(title)

            # Filter conditions
            if not title or not description or "[DEPRECATED]" in description.upper():
                continue

            if title_key in unique_titles:
                continue

            # Base new template
            new_template = {
                "title": title,
                "description": description,
                "type": determine_type(template),
                "platforms": [template.get("platform", "linux")],
                "categories": template.get("categories", []),
                "name": template.get("name", title),
                "note": template.get("note", ""),
            }

            # Add logo if present
            logo = template.get("logo", "").strip()
            if logo:
                new_template["logo"] = logo

            # Add container-specific fields if type=1
            if new_template["type"] == 1:
                if "image" in template:
                    new_template["image"] = template["image"]
                if "env" in template:
                    new_template["env"] = template["env"]
                if "ports" in template:
                    new_template["ports"] = template["ports"]
                if "volumes" in template:
                    new_template["volumes"] = template["volumes"]
                if "restart_policy" in template:
                    new_template["restart_policy"] = template["restart_policy"]

            # Add stack-specific repository if type=2
            elif new_template["type"] == 2:
                repo = template.get("repository", {})
                repo_url = repo.get("url", "").strip()
                stackfile = repo.get("stackfile", "").lstrip("./")

                if not repo_url or not stackfile:
                    # Skip if repo info incomplete
                    continue

                # Ensure stackfile starts with '/'
                if not stackfile.startswith("/"):
                    stackfile = "/" + stackfile

                new_template["repository"] = {
                    "url": repo_url,
                    "stackfile": stackfile
                }

            templates.append(new_template)
            unique_titles.add(title_key)

    except Exception as e:
        print(f"❌ Error parsing {url}: {e}")

# Fetch all templates from URLs
for url in template_urls:
    print(f"📥 Fetching: {url}")
    get_data(url)

# Sort by title, assign incremental integer IDs
templates_sorted = sorted(templates, key=lambda t: t["title"].lower())
for idx, template in enumerate(templates_sorted, start=1):
    template["id"] = idx

final_output = {
    "version": "3",
    "templates": templates_sorted
}

# Write output file
output_file = "portainer-v3-latest.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

print(f"\n✅ Generated {len(templates_sorted)} valid Portainer v3 templates.")
print(f"📁 Output saved to {output_file}")
