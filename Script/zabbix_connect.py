import logging
from pyzabbix import ZabbixAPI, ZabbixAPIException

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
        zbx_py_zabbix = ZabbixAPI(zbx_user, user=zbx_user, password=zbx_password)
        zbx_py_zabbix.session.verify=False
        print("Connect Zabbix API success!")
        return zbx_py_zabbix
    except Exception as e:
        logging.exception(e)

    raise Exception("Some error in pyzabbix or py_zabbix module, see logs")
