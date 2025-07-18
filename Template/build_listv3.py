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
template_counts = {}

def sanitize_key(text):
    """Normalize title text to ensure uniqueness."""
    return re.sub(r'[\s\-]+', '', text.lower().strip())

def determine_type(template):
    """Determine template type based on available keys."""
    if "image" in template:
        return 1  # container
    elif "repository" in template:
        return 2  # stack
    return 2  # default to stack

def fetch_templates_from_url(url):
    """Fetch, parse, and collect templates from a single URL."""
    added = 0
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return added

    raw_templates = data.get("templates", [])
    for template in raw_templates:
        if not template:
            continue
    
        title = str(template.get("title") or "").strip()
        description = str(template.get("description") or "").strip()
        title_key = sanitize_key(title)

        if not title or not description or "[DEPRECATED]" in description.upper():
            continue
        if title_key in unique_titles:
            continue

        new_template = {
            "title": title,
            "description": description,
            "type": determine_type(template),
            "platforms": [template.get("platform", "linux")],
            "categories": template.get("categories", []),
            "name": template.get("name", title),
            "note": template.get("note", "")
        }

        logo = template.get("logo", "").strip()
        if logo:
            new_template["logo"] = logo

        if new_template["type"] == 1:
            # Container-specific fields
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
        else:
            # Stack-specific fields
            repo = template.get("repository", {})
            repo_url = repo.get("url", "").strip()
            stackfile = repo.get("stackfile", "").lstrip("./")

            if not repo_url or not stackfile:
                continue
            if not stackfile.startswith("/"):
                stackfile = "/" + stackfile

            new_template["repository"] = {
                "url": repo_url,
                "stackfile": stackfile
            }

        templates.append(new_template)
        unique_titles.add(title_key)
        added += 1

    return added

# Fetch templates from each source
for url in template_urls:
    print(f"📥 Fetching: {url}")
    count = fetch_templates_from_url(url)
    template_counts[url] = count

# Sort and assign IDs
templates_sorted = sorted(templates, key=lambda t: t["title"].lower())
for idx, template in enumerate(templates_sorted, start=1):
    template["id"] = idx

# Write to file
output_file = "portainer-v3-latest.json"
final_output = {
    "version": "3",
    "templates": templates_sorted
}
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

# Summary
print(f"\n✅ Generated {len(templates_sorted)} valid Portainer v3 templates.")
print(f"📁 Output saved to {output_file}\n")

print("📊 Template counts by source:")
for url, count in template_counts.items():
    print(f"- {url}: {count} template(s)")
