import json

champs_json = {}
champs_json_out = []
with open('champions.json', 'r+') as champs:
    champs_json = json.load(champs)

for champ in champs_json:
    champs_json_out.append({
        'id': champ['id'],
        'name': champ['name'],
        'icon': champ['icon'],
    })

# any(d['id'] == 'warwick' for d in champs_json_out))

with open("champions_out.json", 'w+') as ch_out:
    ch_out.write(json.dumps(champs_json_out))