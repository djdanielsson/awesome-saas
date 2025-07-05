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
    """
    Convert a single v2 template dict to v3 format.
    """
    # Basic required fields
    title = template_v2.get("title", "").strip()
    description = template_v2.get("description", "").strip()
    if not title or not description:
        return None

    # Skip deprecated
    if "[DEPRECATED]" in description.upper():
        return None

    # Convert type: v2 uses int, map 1 -> "stack" (you can adjust mapping)
    type_map = {1: "stack", 2: "app"}
    v2_type = template_v2.get("type", 1)
    ttype = type_map.get(v2_type, "stack")

    # Platform
    platform = template_v2.get("platform", "linux")
    platforms = [platform]

    # Categories fallback
    categories = template_v2.get("categories", [])

    # Repository: v2 often doesn't have repository info.
    # We'll build minimal repository only if stackfile info is found.
    # Otherwise, fallback to using image key (which is accepted by v3)

    repo_url = None
    stackfile = None
    repository = template_v2.get("repository")
    if isinstance(repository, dict):
        repo_url = repository.get("url")
        stackfile = repository.get("stackfile")

    # Try to build repository if missing, from image or maintainer info (best effort)
    # Most v2 templates do NOT have this info, so we fallback to just image.
    if not repo_url or not stackfile:
        repo_url = None
        stackfile = None

    # Build v3 template dict
    template_v3 = {
        "title": title,
        "description": description,
        "type": ttype,
        "platforms": platforms,
        "categories": categories,
    }

    # Repository block if valid
    if repo_url and stackfile:
        # Normalize stackfile to start with /
        if not stackfile.startswith("/"):
            stackfile = "/" + stackfile
        template_v3["repository"] = {
            "url": repo_url,
            "stackfile": stackfile
        }

    # For v2 templates without repository, fallback to v3 with image
    # If "image" key present, add it
    image = template_v2.get("image")
    if image:
        template_v3["image"] = image

    # Add logo if exists
    logo = template_v2.get("logo", "").strip()
    if logo:
        template_v3["logo"] = logo

    # Optionally copy env, ports, volumes etc for completeness (v3 supports these)
    # For brevity, just copy if present:
    for key in ["env", "ports", "volumes", "restart_policy"]:
        if key in template_v2:
            template_v3[key] = template_v2[key]

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
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

    try:
        data = json.loads(response.text)
        return process_templates_from_data(data)
    except Exception as e:
        print(f"❌ Error parsing {url}: {e}")
        return []

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
