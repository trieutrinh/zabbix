from asyncio.windows_events import NULL
import logging
from pprint import pformat
from pyzabbix import ZabbixAPI, ZabbixAPIException
import os
import sys
import csv
import argparse

def connection(zbx_url, zbx_user, zbx_password):

    ## pyzabbix library 
    logging.debug("Try connect to Zabbix by pyzabbix...")
    try:
        zbx_pyzabbix = ZabbixAPI(zbx_url)
        zbx_pyzabbix.session.verify=False
        zbx_pyzabbix.login(zbx_user,zbx_password)
        print("Connect Zabbix API success!")
        return zbx_pyzabbix
    except Exception as e:
        logging.exception(e)
    
    ## py-zabbix library
    logging.debug("Try connect to Zabbix by py-zabbix")
    try:
        zbx_py_zabbix = ZabbixAPI(zbx_url, user=zbx_user, password=zbx_password)
        zbx_py_zabbix.session.verify=False
        print("Connect Zabbix API success!")
        return zbx_py_zabbix
    except Exception as e:
        logging.exception(e)

    raise Exception("Some error in pyzabbix or py_zabbix module, see logs")

def environ_or_required(key):
    if os.environ.get(key):
        return {"default": os.environ.get(key)}
    else:
        return {"required": True}

def parse_args():
    "Return parsed CLI args"
    parser = argparse.ArgumentParser("Import Zabbix object")
    parser.add_argument("--debug", action="store_true", help="Show debug output")
    parser.add_argument(
        "--zabbix-url",
        action="store",
        help="REQUIRED. May be in ZABBIX_URL env var, Example: http://192.168.0.1",
        **environ_or_required("ZABBIX_URL")
    )
    parser.add_argument(
        "--zabbix-username",
        action="store",
        help="REQUIRED. May be in ZABBIX_USERNAME env var",
        **environ_or_required("ZABBIX_USERNAME")
    )
    parser.add_argument(
        "--zabbix-password",
        action="store",
        help="REQUIRED. May be in ZABBIX_PASSWORD env var",
        **environ_or_required("ZABBIX_PASSWORD")
    )
    parser.add_argument(
        "--type",
        choices=[
            "autoguess"
            "import-host",
            "import-group",
            "delete-host",
            "delete-group"
        ],
        default="autoguess",
        help="Zabbix object type, default is %(default)s",
    )
    parser.add_argument(
        "--directory",
        action="store",
        default=".",
        help="Directory, default is %(default)s"
    )
    parser.add_argument(
        "--call",
        action="store",
        default="",
        help="Hostname or groupname"
    )
    args = parser.parse_args()
    return args

def init_logging(level):
    logger_format_string = "%(asctime)s %(levelname)s-8s %(message)s"
    logging.basicConfig(level=level,format=logger_format_string,stream=sys.stdout)

def get_hostgroups_cache(zabbix):
    "Returns dict groupname => groupid"
    result = zabbix.hostgroup.get(output=["groupid", "name"])
    group2groupid = {} # key: groupid, value: group name
    for group in result:
        group2groupid[group["groupid"]] = group["name"]
    return group2groupid

def get_hosts_cache(zabbix):
    "Returns dict host => hostid"
    result = zabbix.host.get(output=["hostid","host"])
    host2hostid ={}
    for host in result:
        host2hostid[host["hostid"]] = host["host"]
    return host2hostid

def get_hosts(zabbix):
    "Returns files"
    ghg = zabbix_.hostgroup.get(
        output=["groupid", "name"]
    )
    for group in ghg:
        groupid = group["groupid"]
        groupname = group["name"]
        gh = zabbix_.host.get(
            output=["hostid", "host"],
            groupids=[groupid]
        )
        for host in gh:
            hostid = host["hostid"]
            hostname = host["host"]
            ghi = zabbix_.hostinterface.get(
                output=["hostid","ip"],
                hostids=[hostid]
            )
            for interfaces in ghi:
                ip = interfaces["ip"]
                if ip == '127.0.0.1':
                    continue
                export_host = []
                export_host.append(hostname)
                export_host.append(ip)
                filename = "./host-export/{}.csv".format(groupname)
                with open(filename, mode='a') as f:
                    for item in export_host:
                        f.writelines("%s," %item)
                    f.write("\n")


def import_group(zabbix, groupname, group2groupid):
    "Import group"
    if groupname in group2groupid:
        return True # Skip existing objects
    result = None
    try:
        result = zabbix.hostgroup.create(name=groupname)
        logging.debug(pformat(result))
    except ZabbixAPIException as e:
        if "Hostgroup already exist" in str(e):
            result = True
        else:
            logging.error(e)
            result = False
    return result

def import_host(zabbix,hostname,ipaddress,description,groupname,host2hostid,group2groupid):
    "Import host"
    result = None
    try:
        if hostname in host2hostid:
            return True #skip existing objects
        
        for groupids, name in group2groupid.items():
            if groupname == name:
                groupid = groupids
                break        
        groups = [
            {
                "groupid": groupid
            }
        ]
        interfaces = [
            {
                "ip": ipaddress,
                "type": 1,
                "main": 1,
                "useip": 1,
                "dns": "",
                "port": "10050"
            }
        ]
        templates =[
            {
                "templateid": "10186" 
            }
        ]
        try:
            result = zabbix.host.create(
                {
                    "host": hostname,
                    "description": description,
                    "interfaces": interfaces,
                    "groups": groups,
                    "templates": templates
                }
            )
        except ZabbixAPIException as e:
            print(e)
            logging.exception(e)
        logging.debug(pformat(result))
        rew_hostid = result["hostids"][0]
        print("Do")

        

    except Exception as e:
        logging.debug(pformat(result))

def delete_host(zabbix,groupid=""):
    "Delete host"
    if groupid != "":
        host2hostid = zabbix.hostgroup.get(
            selectHosts = ["hostid", "name"],
            filter = {"groupid": "19"},
            output=["hosts"]
        )
        print(host2hostid)
        print("Done")
        return
    for key,value in host2hostid.items():
        result = None
        try:
            # result = zabbix.host.delete(key)
            # if isinstance(result, dict):
            #     print("Deleted "+value)
            print("ABC")
        except ZabbixAPIException as e:
            logging.debug(pformat(result))

def delete_group(zabbix,group2groupid,groupname=""):
    "Delete group"
    for key,value in group2groupid.items():
        result = None
        try:
            result = zabbix.hostgroup.delete(key)
            if isinstance(result, dict):
                print("Deleted "+value) 
        except ZabbixAPIException as e:
            logging.debug(pformat(result))

def main(zabbix_,directory,file_type,call_type,group_cache,host_cache):
    "Main function"
    op_result = None
    if file_type == "import-group":
        try:
            filename = "{}/groups/groups.csv".format(directory)
            filename = os.path.abspath(filename)
            print(filename)
            with open(filename, mode='r', newline="") as csv_file:
                csv_reader = csv.reader(csv_file)
                for row in csv_reader:
                    groupname = "".join(row)
                    ig_result = import_group(zabbix_, groupname,group_cache)
        except Exception as e:
            logging.exception(e)
    
    elif file_type == "import-host":
        try:
            listdir = os.listdir("{}/hosts/".format(directory))
            for filename in listdir:
                fileopen = "{}/hosts/{}".format(directory,filename)
                fileopen = os.path.abspath(fileopen)
                groupname = os.path.splitext(filename)[0]
                # ig_result = import_group(zabbix_,groupname,group_cache)
                with open(fileopen, mode='r', newline="") as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    line_count=1
                    for row in csv_reader:
                        ih_result = import_host(
                            zabbix_,
                            row["hostname"],
                            row["ipaddress"],
                            row["description"],
                            groupname,
                            host_cache,
                            group_cache,
                        )
                        line_count+=1

        except Exception as e:
            logging.exception(e)
    elif file_type == "delete-host":
        try:
            dh = delete_host(zabbix_,call_type)
            print(call_type)
        except Exception as e:
            logging.exception(e)

    elif file_type == "delete-group":
        try:
            dg = delete_group(zabbix_,group2groupid)
        except Exception as e:
            logging.exception(e)
    elif file_type == "get-hosts":
        try:
            gh = get_hosts(zabbix_,group2groupid)
        except Exception as e:
            logging.exception(e)
# For Test
# if __name__ == "__main__":
#     zabbix_url = 'http://10.100.1.19'
#     zabbix_username = 'sa.trieutm'
#     zabbix_password = 'Maiiunguoi2##'
#     directory = '.'
#     type = 'import-host'
    
#     zabbix_ = connection(zabbix_url, zabbix_username, zabbix_password)
#     group2groupid={}
#     host2hostid={}

#     group2groupid = get_hostgroups_cache(zabbix_)
#     host2hostid = get_hosts_cache(zabbix_)
#     main(
#         zabbix_=zabbix_,
#         directory=directory,
#         file_type=type,
#         group_cache=group2groupid,
#         host_cache=host2hostid,
#     )

## For running
if __name__ == "__main__":
    args = parse_args()
    
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    init_logging(level=level)
    zabbix_ = connection(
        args.zabbix_url,
        args.zabbix_username,
        args.zabbix_password
    )
    try:
        group2groupid={}
        host2hostid={}
        if args.type == "import-group":
            group2groupid = get_hostgroups_cache(zabbix_)
        if args.type == "import-host":
            host2hostid = get_hosts_cache(zabbix_)
        if args.type == "delete-host":
            host2hostid = get_hosts_cache(zabbix_)
        main(
            zabbix_=zabbix_,
            directory=args.directory,
            file_type=args.type,
            call_type=args.call,
            group_cache=group2groupid,
            host_cache=host2hostid,
        )

    except Exception as e:
        logging.exception(pformat(e))
    

