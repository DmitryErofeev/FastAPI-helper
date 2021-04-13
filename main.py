from typing import Optional
from fastapi import FastAPI
import pynetbox
import datetime
import json
from celery import Celery


with open('config.json', 'r') as cf_file:
    config = json.load(cf_file)

nb_url = config['netbox']['url']
nb_token =config['netbox']['token']

app = FastAPI()
nb = pynetbox.api(nb_url, nb_token)

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# @app.post("/items/{item_id}")
# def read_item(item_id: int, q: Optional[str] = None, a: Optional[str] = None):
#     """

#     """
#     return {"item_id": item_id, "q": q, "a": a}



@app.post("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None, a: Optional[str] = None):
    """
Ловит вебхук из нетбокса и переименовывает коммутатор.
    """

    return {"item_id": item_id, "q": q, "a": a}
