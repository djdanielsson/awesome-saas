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

templates = []
unique_titles = set()

def sanitize_key(text):
    return re.sub(r'[\s\-]+', '', text.lower().strip())

def convert_v2_to_v3(template_v2):
    title = str(template_v2.get("title", "")).strip()
    description = str(template_v2.get("description", "")).strip()

    if not title or not description or "[DEPRECATED]" in description.upper():
        return None

    title_key = sanitize_key(title)
    if title_key in unique_titles:
        return None

    # Guess repo URL and default stackfile path
    repo_url = ""
    stackfile = "/docker-compose.yml"

    maintainer = str(template_v2.get("maintainer", "")).strip()
    repo_match = re.search(r'https://github\.com/[\w\-]+/[\w\-\.]+', maintainer)
    if repo_match:
        repo_url = repo_match.group(0)

    if not repo_url:
        # Skip if no image AND no repo
        if not template_v2.get("image"):
            return None

    template_v3 = {
        "title": title,
        "description": description,
        "type": "stack",
        "platforms": [template_v2.get("platform", "linux")],
        "categories": template_v2.get("categories", []),
    }

    logo = template_v2.get("logo", "").strip()
    if logo:
        template_v3["logo"] = logo

    if template_v2.get("image"):
        template_v3["image"] = template_v2["image"]

    if template_v2.get("env"):
        template_v3["env"] = template_v2["env"]

    if template_v2.get("volumes"):
        template_v3["volumes"] = template_v2["volumes"]

    if template_v2.get("ports"):
        template_v3["ports"] = template_v2["ports"]

    if template_v2.get("restart_policy"):
        template_v3["restart_policy"] = template_v2["restart_policy"]
    else:
        template_v3["restart_policy"] = "unless-stopped"

    if repo_url:
        template_v3["repository"] = {
            "url": repo_url,
            "stackfile": stackfile
        }

    unique_titles.add(title_key)
    return template_v3

def process_templates_from_data(data):
    """
    Accepts loaded JSON data dict and process its templates (v2 or v3).
    Returns list of converted templates.
    """
    version = str(data.get("version", "3")).strip()
    raw_templates = data.get("templates", [])

    processed = []
    if version == "2":
        # v2: convert each template
        for t in raw_templates:
            conv = convert_v2_to_v3(t)
            if conv:
                processed.append(conv)
    else:
        # Assume v3 or unknown: minimal normalization + filter duplicates later
        for t in raw_templates:
            # Basic checks:
            title = t.get("title", "").strip()
            description = t.get("description", "").strip()
            if not title or not description:
                continue
            if "[DEPRECATED]" in description.upper():
                continue

            # Accept platforms list or convert platform string to list
            platforms = t.get("platforms")
            if not platforms:
                platform = t.get("platform")
                platforms = [platform] if platform else ["linux"]

            # Normalize type to string if int
            ttype = t.get("type", "stack")
            if isinstance(ttype, int):
                ttype = {1: "stack", 2: "app"}.get(ttype, "stack")

            # Build normalized template dict
            normalized = {
                "title": title,
                "description": description,
                "type": ttype,
                "platforms": platforms,
                "categories": t.get("categories", []),
            }

            # Copy repository if valid dict
            repo = t.get("repository")
            if isinstance(repo, dict):
                url = repo.get("url")
                stackfile = repo.get("stackfile")
                if url and stackfile:
                    if not stackfile.startswith("/"):
                        stackfile = "/" + stackfile
                    normalized["repository"] = {
                        "url": url,
                        "stackfile": stackfile
                    }

            # Copy image and logo if present
            image = t.get("image")
            if image:
                normalized["image"] = image
            logo = t.get("logo", "").strip()
            if logo:
                normalized["logo"] = logo

            # Copy env, ports, volumes, restart_policy if present
            for key in ["env", "ports", "volumes", "restart_policy"]:
                if key in t:
                    normalized[key] = t[key]

            processed.append(normalized)

    return processed


def get_data(url):
    try:
        data = json.loads(response.text)

        raw_templates = data.get("templates", [])
        if isinstance(raw_templates, list):
            for template in raw_templates:
                v3_template = convert_v2_to_v3(template)
                if v3_template:
                    templates.append(v3_template)
        else:
            print(f"❌ Unexpected structure at {url}")

# Process all source URLs
for url in template_urls:
    print(f"📥 Fetching: {url}")
    new_templates = get_data(url)
    for t in new_templates:
        title_key = sanitize_key(t["title"])
        if title_key not in unique_titles:
            templates.append(t)
            unique_titles.add(title_key)

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
