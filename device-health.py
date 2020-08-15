from influxdb import InfluxDBClient
import requests
import sys
import json
import time
import yaml

requests.packages.urllib3.disable_warnings()

from requests.packages.urllib3.exceptions import InsecureRequestWarning

class Authentication:

    @staticmethod
    def get_jsessionid(vmanage_host, vmanage_port, username, password):
        api = "/j_security_check"
        base_url = "https://%s:%s"%(vmanage_host, vmanage_port)
        url = base_url + api
        payload = {'j_username' : username, 'j_password' : password}
        
        response = requests.post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")
            return(jsessionid[0])
        except:
            print("\nNo valid JSESSION ID returned")
            exit()
       
    @staticmethod
    def get_token(vmanage_host, vmanage_port, jsessionid):
        headers = {'Cookie': jsessionid}
        base_url = "https://%s:%s"%(vmanage_host, vmanage_port)
        api = "/dataservice/client/token"
        url = base_url + api      
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            return(response.text)
        else:
            return None

if __name__ == '__main__':

    try:

        with open("vmanage_login.yaml") as f:
            config = yaml.safe_load(f.read())

        vmanage_host = config["vmanage_host"]
        vmanage_port = config["vmanage_port"]
        username = config["vmanage_username"]
        password = config["vmanage_password"]
        routerId = config["hub_routers"]  

        Auth = Authentication()
        jsessionid = Auth.get_jsessionid(vmanage_host,vmanage_port,username,password)
        token = Auth.get_token(vmanage_host,vmanage_port,jsessionid)

        if token is not None:
            headers = {'Content-Type': "application/json",'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
        else:
            headers = {'Content-Type': "application/json",'Cookie': jsessionid}

        base_url = "https://%s:%s/dataservice"%(vmanage_host,vmanage_port)     

        # Get app route statistics for tunnels between Hub routers and Spoke routers.
        status = []
        total_records = 0
        payload = {}

        api_url = "/device/system/status?deviceId=%s"%(routerId[0]['system_ip'])

        url = base_url + api_url

        response = requests.request("GET", url=url, headers=headers, data = payload, verify=False)
        device_stats = response.json()["data"]

        # loop over the API response variable items and create records to be stored in InfluxDB

        if response.status_code == 200:
            device_stats = response.json()["data"]

            for item in device_stats:
                temp = {
                        "measurement": "device_stats",
                        "tags": {
                                    "Device": item['vdevice-name']
                                },
                        "fields": {
                                    "CPU": float(item['cpu_system']),
                                    "Memoria_free": float(item['mem_free']),
                                    "disk_avail": float(item['disk_avail'].replace('M','')),
                                    "lastupdated": float(item['lastupdated'])
                                    }
                        }

                status.append(temp)
                print(status)
                total_records = total_records+1
    
        else:
            print("Failed to retrieve app route statistics\n")

        # login credentials for InfluxDB

        USER = 'MyUser'
        PASSWORD = 'MyPass'
        DBNAME = 'telegraf'
        host='localhost'
        port=8086

        client = InfluxDBClient(host, port, USER, PASSWORD, DBNAME)

        client.write_points(status)
        time.sleep(2)

        print("Stored %s records in influxdb"%total_records)


    except Exception as e:
        print('Exception line number: {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)