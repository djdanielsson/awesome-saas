# not working yet
import json
import requests
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

# Output list and title deduplication set
templates = []
unique_titles = set()

def sanitize_key(text):
    """Normalize a title for deduplication"""
    return re.sub(r'[\s\-]+', '', text.lower().strip())

def convert_v2_to_v3(template):
    """Convert a v2 Portainer template to v3 format"""
    title = str(template.get("title", "")).strip()
    description = str(template.get("description", "")).strip()

    if not title or not description or "[DEPRECATED]" in description.upper():
        return None

    title_key = sanitize_key(title)
    if title_key in unique_titles:
        return None

    maintainer = str(template.get("maintainer", "")).strip()
    repo_match = re.search(r'https://github\.com/[\w\-]+/[\w\-\.]+', maintainer)
    repo_url = repo_match.group(0) if repo_match else ""
    stackfile = "/docker-compose.yml"

    # Skip template if no repo or image
    if not repo_url and not template.get("image"):
        return None

    result = {
        "title": title,
        "description": description,
        "type": "stack",
        "platforms": [template.get("platform", "linux")],
        "categories": template.get("categories", []),
        "restart_policy": template.get("restart_policy", "unless-stopped"),
    }

    if "logo" in template:
        result["logo"] = template["logo"].strip()
    if "image" in template:
        result["image"] = template["image"]
    if "env" in template:
        result["env"] = template["env"]
    if "ports" in template:
        result["ports"] = template["ports"]
    if "volumes" in template:
        result["volumes"] = template["volumes"]
    if repo_url:
        result["repository"] = {
            "url": repo_url,
            "stackfile": stackfile
        }

    unique_titles.add(title_key)
    return result

def normalize_v3_template(template):
    """Normalize and filter a v3 Portainer template"""
    title = str(template.get("title", "")).strip()
    description = str(template.get("description", "")).strip()

    if not title or not description or "[DEPRECATED]" in description.upper():
        return None

    title_key = sanitize_key(title)
    if title_key in unique_titles:
        return None

    platforms = template.get("platforms")
    if not platforms:
        platform = template.get("platform")
        platforms = [platform] if platform else ["linux"]

    ttype = template.get("type", "stack")
    if isinstance(ttype, int):
        ttype = {1: "stack", 2: "app"}.get(ttype, "stack")

    normalized = {
        "title": title,
        "description": description,
        "type": ttype,
        "platforms": platforms,
        "categories": template.get("categories", []),
        "restart_policy": template.get("restart_policy", "unless-stopped")
    }

    if "logo" in template:
        normalized["logo"] = template["logo"].strip()
    if "image" in template:
        normalized["image"] = template["image"]
    if "env" in template:
        normalized["env"] = template["env"]
    if "ports" in template:
        normalized["ports"] = template["ports"]
    if "volumes" in template:
        normalized["volumes"] = template["volumes"]

    repo = template.get("repository")
    if isinstance(repo, dict) and "url" in repo and "stackfile" in repo:
        stackfile = repo["stackfile"]
        if not stackfile.startswith("/"):
            stackfile = "/" + stackfile
        normalized["repository"] = {
            "url": repo["url"],
            "stackfile": stackfile
        }

    unique_titles.add(title_key)
    return normalized

def process_templates(data):
    """Convert templates from raw JSON to unified v3 format"""
    version = str(data.get("version", "3")).strip()
    raw_templates = data.get("templates", [])
    output = []

    if version == "2":
        for template in raw_templates:
            v3 = convert_v2_to_v3(template)
            if v3:
                output.append(v3)
    else:
        for template in raw_templates:
            v3 = normalize_v3_template(template)
            if v3:
                output.append(v3)
    return output

def fetch_templates(url):
    """Fetch and parse a template file from URL"""
    try:
        print(f"📥 Fetching: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = json.loads(response.text)
        return process_templates(data)
    except Exception as e:
        print(f"❌ Failed to load {url}: {e}")
        return []

# Main processing loop
for url in template_urls:
    templates.extend(fetch_templates(url))

# Sort templates alphabetically
templates_sorted = sorted(templates, key=lambda t: t["title"].lower())

# Assign unique numeric IDs
for i, t in enumerate(templates_sorted, start=1):
    t["id"] = str(i)

# Final JSON output
final_output = {
    "version": "3",
    "templates": templates_sorted
}

# Save to file
output_path = "portainer-v2-v3-latest.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(final_output, f, indent=2, ensure_ascii=False)

print(f"\n✅ {len(templates_sorted)} valid Portainer templates written to: {output_path}")
