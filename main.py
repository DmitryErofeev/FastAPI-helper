# from typing import Optional
from fastapi import FastAPI, Request
from colorama import init, Fore
import pynetbox
import datetime
import json
import time
# from celery import Celery

init(autoreset=True)

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
    print('Device update')

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


@app.post("/make_config_eltex")
async def make_conf_mes1124m(request: Request):
    """
Ловит вебхук из нетбокса и создает начальный конфиг для Элтекса.
    """
    config = []
    response_code = "500"
    data = await request.json()
    print(Fore.RED + 'make config eltex webhook', data)
    time.sleep(5)

    device = nb.dcim.devices.get(data['data']['id'])
    site = nb.dcim.sites.get(device.site.id)
    vlan_group = nb.ipam.vlan_groups.get(slug=site.region.slug)
    vlans = nb.ipam.vlans.filter(group_id=vlan_group.id)
    hostname = device.display_name
    location = device.site.name
    ip = device.primary_ip.address.split('/')[0]

    print(Fore.RED + 'IP', ip, vlans, hostname, location, sep=', ')

    device_status = data['data']['status']['value']

    if device_status == 'staged':
        if device.device_type.slug == 'mes1124m':


            with open('misc\MES1.txt', 'r') as f1:
                temp_conf = []

                for line in f1:
                    temp_conf.append(line)

                for command in temp_conf:
                    if command.startswith("hostname"):
                        command = command.rstrip('\n')
                        config.append(f'{command} {hostname}\n')
                    else:
                        config.append(command)
                config.append('!\n')


            config.append('vlan database\n')
            for vlan in vlans:
                vid = vlan['vid']
                name = vlan['name']
                config.append(f' vlan {vid} name {name}\n')
            config.append('exit\n')
            config.append('!\n')

            config.append('interface vlan 1\n')
            config.append(' no ip address dhcp\n')
            config.append('exit\n')

            for vlan in vlans:
                vid = vlan['vid']
                name = vlan['name']
                config.append('!\n')
                config.append(f'interface vlan {vid}\n')
                config.append(f' name {name}\n')
                if 'mgmt' in name:
                    config.append(f' ip address {ip} 255.255.254.0\n')
                    config.append(f' sntp client enable\n')

                config.append(f'exit\n')

            _gateway = ip.split('.')
            _gateway[-1] = '1'
            gateway = '.'.join(_gateway)
            command = command.rstrip('\n')
            config.append('!\n')
            config.append(f'ip default-gateway {gateway}\n')


            with open('misc\mes3.txt') as f2:
                for line in f2:

                    if 'access-node-id' in line:
                        line = line.rstrip('\n')
                        config.append(f'{line} {ip}\n')
                        continue

                    if 'management access-list' in line:
                        mgmt_vlan = [str(element['vid']) for element in vlans if 'mgmt' in element['name']]
                        config.append(line)
                        config.append(f' permit vlan {mgmt_vlan[0]}\n')
                        config.append(' deny\n')
                        continue

                    if 'snmp-server location' in line:
                        line = line.rstrip('\n')
                        config.append(f'{line} {hostname}\n')
                        continue

                    else:
                        config.append(line)


            with open('misc\MES4.txt') as f3:
                for line in f3:
                    if 'switchport access vlan' in line:
                        pppoe_vlan = [str(element['vid']) for element in vlans if 'pppoe' in element['name']]
                        line = line.rstrip('\n')
                        config.append(f'{line} {pppoe_vlan[0]}\n')
                    else:
                        config.append(line)


            with open('misc\config.txt', 'w') as final_conf:
                for line in config:
                    final_conf.write(line)


            print(temp_conf)
            print(config)


    return {'result': 'ignore'}