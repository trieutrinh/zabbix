from pyzabbix import ZabbixAPIException
import zabbix_connect
import os
import sys
import csv
import random
def icons_get(zabbix_,iconname):
    icons = {}
    iconData = zabbix_.image.get(output=["imageid","name"])
    for icon in iconData:
        icons[icon["name"]] = icon["imangeid"]
    return icons

def host_lookup(zabbix_,hostname):
    hostid = zabbix_.host.get(filter={"host": hostname})
    if hostid:
        return str(hostid[0]['hostid'])

def map_lookup(zabbix_,mapname):
    mapid = zabbix_.map.get(filter={"name":mapname})
    if mapid:
        return str(mapid[0]['sysmapid'])
def trigger_lookup(zabbix_,hostid):
    triggerid = zabbix_.trigger.get(
        filter={
            "description": "Unavailable by ICMP ping",
            "hostid": hostid
        },
    )
    if triggerid:
        return str(triggerid[0]['triggerid'])
    print(triggerid)

def create_maps(zabbix_):

    selements= []
    links=[]
    fileopen = "{}".format("maps_bni.csv")
    fileopen = os.path.abspath(fileopen)
    with open(fileopen, mode='r', newline="") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        selementid=1
        Flag= True
        for row in csv_reader:
            seletemp1 =0
            seletemp2=0
            host1id = host_lookup(zabbix_,row['hostname1'])
            host2id = host_lookup(zabbix_,row['hostname2'])

            trigger1 = trigger_lookup(zabbix_,host1id)
            trigger2 = trigger_lookup(zabbix_,host2id)
            elements = [
                {"hostid": host1id}
            ]
            temp1 = (next((x for x in selements if x["elements"] == elements), None))
            if bool(selements) and (temp1 == None) or Flag:
                seletemp1=selementid
                map_element ={}
                map_element.update(
                    {
                        "selementid": selementid,
                        "elements": elements,
                        "x": random.randrange(1,600),
                        "y": random.randrange(1,600),
                        "elementtype": 0,
                        "iconid_off": "155"
                    }
                )
                selements.append(map_element)
                selementid+=1
            else:
                    seletemp1 = temp1["selementid"]

            elements2 = [
                {"hostid": host2id}
            ]
            temp2 = (next((x for x in selements if x["elements"] == elements2), None))

            if bool(selements) and (temp2 == None) or Flag:
                seletemp2=selementid
                map_element ={}
                map_element.update(
                    {
                        "selementid": selementid,
                        "elements": elements2,
                        "x": random.randrange(1,600),
                        "y": random.randrange(1,600),
                        "elementtype": 0,
                        "iconid_off": "155"
                    }
                )
                selements.append(map_element)
                selementid+=1
            else:
                    seletemp2 = temp2["selementid"]
            link_element = {}
            link_element.update(
                {
                    "selementid1": seletemp1,
                    "selementid2": seletemp2,
                    "drawtype": "0",
                    "color": "00CC00",
                    "linktriggers": [
                        {
                            "triggerid": trigger1,
                            "drawtype": 4,
                            "color": "DD0000"
                        },
                        {
                            "triggerid": trigger2,
                            "drawtype": 4,
                            "color": "DD0000"                            
                        }
                    ]
                }
            )
            links.append(link_element)
            Flag = False

    result = None

    try:
        result = zabbix_.map.create(
            {
                "name": "Network maps BNI",
                "width": "1000",
                "height": "1000",
                "selements": selements,
                "links": links
            }
        )
        print("done")
    except ZabbixAPIException as e:
        print(e)

def main(zabbix_):
    #Main

    im = create_maps(zabbix_)


if __name__ == '__main__':
    zabbix_url = 'http://10.100.1.19'
    zabbix_username = 'sa.trieutm'
    zabbix_password = 'Maiiunguoi2##'

    zabbix_ = zabbix_connect.connection(zabbix_url,zabbix_username,zabbix_password)
    main(zabbix_)