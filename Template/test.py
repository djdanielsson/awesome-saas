import json
jsonFile = open('tmp.json', 'r')
data = json.load(jsonFile)

size=len(data["templates"])
print(size)
values = [];
uniqueNames = [];
for i in data["templates"]:
    if(i["title"] not in uniqueNames):
         uniqueNames.append(i["title"]);
         values.append(i)
jsonFile.close()
#print(values)
with open("test.json", "w") as json_file:
    json_file.write(str(values))
