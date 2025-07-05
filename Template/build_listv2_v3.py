import json
import requests
import re

# List of source template URLs
template_urls = [
    'https://raw.githubusercontent.com/pi-hosted/pi-hosted/master/template/portainer-v2-amd64.json',
    # Replaced the dead 'donspablo' link with a working, popular alternative
    'https://raw.githubusercontent.com/dnburgess/portainer-templates/master/template.json',
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
    if not title or not description or "[DEPRECATED]" in description.upper():
        return None

    title_key = sanitize_key(title)
    if title_key in unique_titles:
        return None

    # --- Determine Template Type (Stack vs. Container) ---
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
    if is_stack:
        repo = template.get("repository", {})
        if not repo.get("url"):
            return None # A stack template MUST have a repository URL.

        stackfile = repo.get("stackfile", "docker-compose.yml")
        if not stackfile.startswith('/'):
            stackfile = f"/{stackfile}"

        v3_template = {
            "type": "stack", "title": title, "description": description,
            "repository": {"url": repo["url"], "stackfile": stackfile}
        }
    elif is_container:
        if not template.get("image"):
            return None # A container template MUST have an image.
            
        v3_template = {
            "type": "container", "title": title, "description": description,
            "image": template["image"]
        }
        if "ports" in template: v3_template["ports"] = template["ports"]
        if "volumes" in template: v3_template["volumes"] = template["volumes"]
        if "env" in template: v3_template["env"] = template["env"]
    else:
        return None

    # --- Add Common Optional Fields ---
    if "logo" in template and template["logo"]: v3_template["logo"] = template["logo"].strip()
    if "categories" in template and template["categories"]: v3_template["categories"] = template["categories"]
    
    platforms = template.get("platforms", [template.get("platform", "linux")])
    if not isinstance(platforms, list): platforms = [str(platforms)]
    v3_template["platforms"] = platforms
    
    v3_template["restart_policy"] = template.get("restart_policy", "unless-stopped")

    # --- Final V3 Schema Enforcement ---
    if v3_template["type"] == "stack":
        for key in ["image", "ports", "volumes", "env"]: v3_template.pop(key, None)
    elif v3_template["type"] == "container":
        v3_template.pop("repository", None)

    unique_titles.add(title_key)
    return v3_template

def parse_json_stream(text):
    """
    Parses a string that contains multiple, concatenated JSON objects
    by finding the boundaries of each object.
    """
    templates = []
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(text):
        text = text[pos:]
        # Skip whitespace and other non-JSON characters at the beginning
        obj_start = text.find('{')
        if obj_start == -1:
            break
        text = text[obj_start:]
        try:
            obj, pos = decoder.raw_decode(text)
            templates.append(obj)
        except json.JSONDecodeError:
            # Could not decode, move past this point to find the next object
            pos = 1
    return templates

def fetch_and_process_url(url):
    """Fetches a template file from a URL and processes its contents."""
    try:
        print(f"📥 Fetching: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        content = response.text.strip()
        if not content:
            print(f"⚠️ Empty content from {url}")
            return []

        raw_templates = []
        try:
            # First, try to parse as a single, valid JSON object
            data = json.loads(content)
            if isinstance(data, dict):
                # Standard format: {"version": "x", "templates": [...]}
                raw_templates = data.get("templates", [])
            elif isinstance(data, list):
                # Some files have the root as a list of templates
                raw_templates = data
        except json.JSONDecodeError:
            # If standard parsing fails, it might be a stream of JSON objects
            print(f"ℹ️ Standard JSON parse failed for {url}. Attempting to parse as a stream.")
            raw_templates = parse_json_stream(content)

        if not raw_templates:
            print(f"⚠️ No templates found in {url}")
            return []
            
        processed_templates = []
        for raw_template in raw_templates:
            if not isinstance(raw_template, dict): continue
            v3_template = normalize_and_validate_template(raw_template)
            if v3_template:
                processed_templates.append(v3_template)
        print(f"👍 Processed {len(processed_templates)} templates from {url}")
        return processed_templates
        
    except requests.Timeout:
        print(f"❌ Timeout while fetching {url}")
    except requests.RequestException as e:
        print(f"❌ Request failed for {url}: {e}")
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
