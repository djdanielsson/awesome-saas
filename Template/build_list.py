import json
import requests
import os
import random
import string
import re

template_urls = [
  'https://raw.githubusercontent.com/pi-hosted/pi-hosted/master/template/portainer-v2-amd64.json',
  'https://raw.githubusercontent.com/donspablo/awesome-saas/master/Template/portainer-v2.json',
  'https://raw.githubusercontent.com/SelfhostedPro/selfhosted_templates/master/Template/portainer-v2.json',
  'https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json'
]

templates = []
unique_names = []

def get_data(url):
  myfile = requests.get(url)
  randoms = ''.join(random.choices(string.ascii_lowercase, k=5))
  filename = os.path.basename(url)
  with open(f"/tmp/{randoms}{filename}", 'wb') as file:
    file.write(myfile.content)
  with open(f"/tmp/{randoms}{filename}", 'r') as json_file:
    data = json.load(json_file)
    size = len(data["templates"])
    print(size)
    for template in data["templates"]:
      title = template["title"].replace(" ", "").replace("-", "").lower()
      if title not in unique_names:
        unique_names.append(title)
        templates.append(template)

# Call function
for url in template_urls:
  get_data(url)

total_size = len(templates)
print(total_size)

# Sort based on title
sorted_templates = sorted(templates, key=lambda d: d['title'].lower())

# Create a new dictionary with the required structure
final_data = {
  "version": "2",
  "templates": sorted_templates
}

# Write json file
with open('portainer-v2-latest.json', 'w', encoding='utf-8') as file:
    json.dump(final_data, file, ensure_ascii=False, indent=2)

# Replace timezones in the new file
with open("portainer-v2-latest.json", "r") as file:
  new_data = re.sub(r'Europe\/\w*|America\/\w*', 'America/Chicago', file.read())
  with open("portainer-v2-latest.json", "w") as text_file:
    text_file.write(new_data)

