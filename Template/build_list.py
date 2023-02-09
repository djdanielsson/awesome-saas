import json
import requests
import os
import random, string
import re

files = ['https://raw.githubusercontent.com/pi-hosted/pi-hosted/master/template/portainer-v2-amd64.json', 'https://raw.githubusercontent.com/donspablo/awesome-saas/master/Template/portainer-v2.json', 'https://raw.githubusercontent.com/SelfhostedPro/selfhosted_templates/master/Template/portainer-v2.json', 'https://raw.githubusercontent.com/Qballjos/portainer_templates/master/Template/template.json']
values = [];
uniqueNames = [];

def getData(url):
  myfile = requests.get(url)
  randoms = string.ascii_lowercase
  fileName = os.path.basename(url)
  open("/tmp/" + randoms + fileName, 'wb').write(myfile.content)
  jsonFile = open("/tmp/" + randoms + fileName, 'r')
  data = json.load(jsonFile)

  size=len(data["templates"])
  print(size)
  for i in data["templates"]:
    if(((str(i["title"])).replace(" ", "").replace("-", "")).lower() not in uniqueNames):
      uniqueNames.append(((str(i["title"])).replace(" ", "").replace("-", "")).lower());
      values.append(i)
  jsonFile.close()

# Call function
for urlz in files:
  getData(urlz)

valueSize = values
totalSize = len(valueSize)
print(totalSize)
# Sort based on title
sortedValues = sorted(values, key=lambda d: (d['title']).lower())
# Write json file
with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(sortedValues, f, ensure_ascii=False, indent=2)

# Now re-open new file so it can be just a string and replace all timzeones to correct one
jsonFile2 = open('test.json', 'r')
newData = re.sub(r'Europe\/\w*|America\/\w*', 'America/Chicago', str(jsonFile2.read()))
with open("test.json", "w") as text_file:
  text_file.write(newData)
