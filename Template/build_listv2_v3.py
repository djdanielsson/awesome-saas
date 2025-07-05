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

# --- Globals for processing ---
# Final list of processed templates
templates = []
# Set to track unique titles to prevent duplicates
unique_titles = set()

def sanitize_key(text):
    """Normalize a title for deduplication by making it lowercase and removing spaces/hyphens."""
    return re.sub(r'[\s\-]+', '', text.lower().strip())

def normalize_and_validate_template(template):
    """
    Processes a single template object (from any version), validates it,
    and converts it to a strict Portainer v3 format.

    Returns a valid v3 template dict or None if the template is invalid/skipped.
    """
    title = str(template.get("title", "")).strip()
    description = str(template.get("description", "")).strip()

    # --- Basic Filtering ---
    # Skip if essential fields are missing or it's marked as deprecated
    if not title or not description or "[DEPRECATED]" in description.upper():
        return None

    # Skip if the title is already in our list (deduplication)
    title_key = sanitize_key(title)
    if title_key in unique_titles:
        return None

    # --- Determine Template Type (Stack vs. Container) ---
    # A template is a "stack" if it has a repository defined.
    # A template is a "container" if it has an image defined.
    # The v2 'type' field (1=stack, 2=container) is also a strong indicator.
    
    v2_type = template.get("type")
    is_stack = (
        v2_type == 1 or
        template.get("type") == "stack" or
        ("repository" in template and isinstance(template.get("repository"), dict) and "url" in template.get("repository"))
    )
    is_container = (
        v2_type == 2 or
        template.get("type") in ["container", "app"] or
        "image" in template
    )

    # --- Build the V3 Template Object ---
    
    # A. Process as a Stack Template
    if is_stack:
        repo = template.get("repository", {})
        if not repo.get("url"):
            return None # A stack template MUST have a repository URL.

        # Ensure stackfile path is correctly formatted
        stackfile = repo.get("stackfile", "docker-compose.yml")
        if not stackfile.startswith('/'):
            stackfile = f"/{stackfile}"

        # Construct the valid v3 stack object
        v3_template = {
            "type": "stack",
            "title": title,
            "description": description,
            "repository": {
                "url": repo["url"],
                "stackfile": stackfile
            }
        }
        # Note: A stack template should NOT have top-level 'image', 'ports', 'volumes'.
        # These are defined within the stackfile (e.g., docker-compose.yml).

    # B. Process as a Container Template
    elif is_container:
        if not template.get("image"):
            return None # A container template MUST have an image.
            
        # Construct the valid v3 container object
        v3_template = {
            "type": "container",
            "title": title,
            "description": description,
            "image": template["image"]
        }
        # A container template can have optional runtime details
        if "ports" in template:
            v3_template["ports"] = template["ports"]
        if "volumes" in template:
            v3_template["volumes"] = template["volumes"]
        if "env" in template:
            v3_template["env"] = template["env"]
        # Note: A container template should NOT have a 'repository' key.
    
    # C. If it's neither a valid stack nor container, skip it
    else:
        return None

    # --- Add Common Optional Fields ---
    if "logo" in template and template["logo"]:
        v3_template["logo"] = template["logo"].strip()
    if "categories" in template and template["categories"]:
        v3_template["categories"] = template["categories"]
    
    # For platforms, default to linux if not specified
    platforms = template.get("platforms", [template.get("platform", "linux")])
    if not isinstance(platforms, list):
        platforms = [str(platforms)]
    v3_template["platforms"] = platforms
    
    v3_template["restart_policy"] = template.get("restart_policy", "unless-stopped")

    # If we got here, the template is valid and processed.
    unique_titles.add(title_key)
    return v3_template


def fetch_and_process_url(url):
    """Fetches a template file from a URL and processes its contents."""
    try:
        print(f"📥 Fetching: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # Some files might have leading/trailing whitespace or comments
        # A more robust way to load JSON is to find the first '{'
        content = response.text
        json_start = content.find('{')
        if json_start == -1:
            print(f"⚠️ No JSON object found in {url}")
            return []
        
        data = json.loads(content[json_start:])
        
        processed_templates = []
        for raw_template in data.get("templates", []):
            v3_template = normalize_and_validate_template(raw_template)
            if v3_template:
                processed_templates.append(v3_template)
        return processed_templates
        
    except requests.Timeout:
        print(f"❌ Timeout while fetching {url}")
        return []
    except requests.RequestException as e:
        print(f"❌ Request failed for {url}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON from {url}: {e}")
        return []
    except Exception as e:
        print(f"❌ An unexpected error occurred for {url}: {e}")
        return []

# --- Main Processing Loop ---
for url in template_urls:
    templates.extend(fetch_and_process_url(url))

# Sort the final list of templates alphabetically by title
templates_sorted = sorted(templates, key=lambda t: t["title"].lower())

# Final JSON output structure required by Portainer
final_output = {
    "version": "3",
    "templates": templates_sorted
}

# --- Save to File ---
output_path = "portainer-templates-v3.json"
try:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Success! {len(templates_sorted)} valid Portainer v3 templates written to: {output_path}")
except IOError as e:
    print(f"\n❌ Error writing to file {output_path}: {e}")

