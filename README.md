### About
This repository contains two files: `lol.py` and `lol_tg.py` which are:
 1. `lol.py` - op.gg parser that shows most common runes for select champion
 2. `lol_tg.py` - telegram bot wrapper around the said parser
 
### Installation
Requirements: python3, venv
Inside virtualenviromentenv run
```sh
pip install -r requirements.txt
```
for telegram bot you'll need a telegram bot token and .env file
```sh
touch .env
```
in `.env` write the token
```sh
TOKEN="<your_token>"
```
### Running
```sh
python lol.py <champion>
```
use `python lol.py -h` to get detailed desription
To run telegram bot:
```sh
python lol_tg.py
```

Idk how to deploy since i havent done telegram bot deployments just yet but i guess wsgi and gunicorn would work.
