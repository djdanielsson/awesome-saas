import json
jsonFile = open('tmp.json', 'r')
data = json.load(jsonFile)

size=len(data["templates"])
print(size)
values = [];
uniqueNames = [];
for i in data["templates"]:
  if((str(i["title"])).lower() not in uniqueNames):
    uniqueNames.append((str(i["title"])).lower());
    values.append(i)
jsonFile.close()

jsonFile2 = open('tmp2.json', 'r')
data2 = json.load(jsonFile2)

size=len(data2["templates"])
print(size)
for i in data2["templates"]:
  if((str(i["title"])).lower() not in uniqueNames):
    uniqueNames.append((str(i["title"])).lower());
    values.append(i)
jsonFile.close()
#print(values)
sortedValues = sorted(values, key=lambda d: d['title'])
with open("test.json", "w") as json_file:
  json_file.write(str(sortedValues))

with open('test.json', 'w', encoding='utf-8') as f:
    json.dump(sortedValues, f, ensure_ascii=False, indent=2)