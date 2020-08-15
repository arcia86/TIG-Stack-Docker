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

        Auth = Authentication()
        jsessionid = Auth.get_jsessionid(vmanage_host,vmanage_port,username,password)
        token = Auth.get_token(vmanage_host,vmanage_port,jsessionid)

        if token is not None:
            headers = {'Content-Type': "application/json",'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
        else:
            headers = {'Content-Type': "application/json",'Cookie': jsessionid}

        base_url = "https://%s:%s/dataservice"%(vmanage_host,vmanage_port)     

        # Get app route statistics for tunnels between Hub routers and Spoke routers.
        series = []
        total_records = 0

        for hub in config["hub_routers"]:

            api_url = "/statistics/approute/fec/aggregation"

            payload = {
                            "query": {
                                "condition": "AND",
                                "rules": [
                                {
                                    "value": [
                                                "24"
                                             ],
                                    "field": "entry_time",
                                    "type": "date",
                                    "operator": "last_n_hours"
                                },
                                {
                                    "value": [
                                            hub["system_ip"]
                                            ],
                                    "field": "local_system_ip",
                                    "type": "string",
                                    "operator": "in"
                                }
                                ]
                            },
                            "aggregation": {
                                "field": [
                                {
                                    "property": "name",
                                    "sequence": 1,
                                    "size": 6000
                                },
                                {
                                    "property": "proto",
                                    "sequence": 2
                                }
                                ],
                                "histogram": {
                                                "property": "entry_time",
                                                "type": "minute",
                                                "interval": 30,
                                                "order": "asc"
                                             },
                                "metrics": [
                                {
                                    "property": "latency",
                                    "type": "avg"
                                },
                                {
                                    "property": "jitter",
                                    "type": "avg"
                                },
                                {
                                    "property": "loss_percentage",
                                    "type": "avg"
                                }
                                ]
                            }
                            }

            url = base_url + api_url

            response = requests.post(url=url, headers=headers, data=json.dumps(payload), verify=False)

            # loop over the API response variable items and create records to be stored in InfluxDB

            if response.status_code == 200:
                app_route_stats = response.json()["data"]

                for item in app_route_stats:
                    temp = {
                                "measurement": "approute_stats",
                                "tags": {
                                            "Tunnel": item['name'] + "(" + item['proto'] + ")",
                                        },
                                "time": time.strftime('%m/%d/%Y %H:%M:%S',  time.gmtime(item['entry_time']/1000.)),
                                "fields": {
                                            "latency": float(item['latency']),
                                            "loss": float(item['loss_percentage']),
                                            "jitter": float(item['jitter'])
                                }
                                }
                    series.append(temp)
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

        client.write_points(series)
        time.sleep(2)

        print("Stored %s records in influxdb"%total_records)


    except Exception as e:
        print('Exception line number: {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)