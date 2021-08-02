from typing import Optional
from fastapi import FastAPI, Request
import pynetbox
import datetime
import json
# from celery import Celery


with open('config.json', 'r') as cf_file:
    config = json.load(cf_file)


NB_URL = config['netbox']['url']
NB_TOKEN =config['netbox']['token']
NB_USER = config['netbox']['nb_user']

app = FastAPI()
nb = pynetbox.api(NB_URL, NB_TOKEN)
now = datetime.datetime.now()


@app.post("/device_update")
async def device_update(request: Request):
    """
Ловит вебхук из нетбокса и переименовывает коммутатор.
    """
    response_code = "500"
    data = await request.json()

    current_date = now.strftime('%Y%m%d')
    date_remove = now.strftime('%Y-%m-%d')

    device_status = data['data']['status']['value']

    if data['username'] != NB_USER:

        if device_status == 'offline':

            device = nb.dcim.devices.get(data['data']['id'])

            new_device_name = device['name'] + '-' + current_date
            new_status = 'offline'
            interfaces = nb.dcim.interfaces.filter(device_id=device.id, cabled=True)
            ids_cable_links = [id.cable_peer.cable for id in interfaces]


            try:
                for cable_link in ids_cable_links:
                    link = nb.dcim.cables.get(cable_link)
                    link.delete()
                print('Линки коммутатора удалены')

            except Exception:
                print('Линки коммутатора не удалены')

            try:
                device = nb.dcim.devices.get(device.id)

                device.name = new_device_name
                device.status = new_status
                device.custom_fields['dateRemove'] = date_remove
                device.save()
                print('Коммутатор переименован')

            except Exception as ex:
                print(ex)
                print('Коммутатор не переименован')
                return {'result': 'failure'}

            return {"result":'ok'}

    return {'result': 'ignore'}