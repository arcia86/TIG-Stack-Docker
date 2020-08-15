# TIG-Stack-Docker
TIG stack on Docker for network monitoring of Cisco SDWAN controller

## Getting Started

I ran this code using a Mac-OS. with docker already installed. the main goal of this is running a monitoring completed system to collect information from the vManager using 
RESTAPIService and save those values into a InfluxDB database then you can use Grafana dashboard to monitoring.

### Prerequisites

Docker, Cisco Sandbox vManager reserved.  

## Create your docker enviroment

Firts create your network environment and volume for the Grafana and influxdb container.

```
docker network create monitoring
docker volume create grafana-volume
docker volume create influxdb-volume
docker network ls
docker volume ls
```
You can also need to prepare the influxdb environment.

```
docker run --rm \
  -e INFLUXDB_DB=telegraf -e INFLUXDB_ADMIN_ENABLED=true \
  -e INFLUXDB_ADMIN_USER='MyUser' \
  -e INFLUXDB_ADMIN_PASSWORD='Mypass' \
  -e INFLUXDB_USER=telegraf -e INFLUXDB_USER_PASSWORD='Mypass' \
  -v influxdb-volume:/var/lib/influxdb \
  influxdb /init-influxdb.sh
```
just start your containers.
```
docker-compose up -d
```
### verifying container is running

Once is running you can verify the container is running:
```
docker ps
```
Open browser to verify Grafana is running localhost:3000

### Collect data from the vManager

Create your virtual environment and install your requirements

```
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements.txt
```
Edit the vmanage_login.yaml file with your credentials
```
vim vmanage_login.yaml

# vManage Connectivity Info
vmanage_host: 'YOUR_IP'
vmanage_port: 8443
vmanage_username: admin
vmanage_password: admin
hub_routers:
  - system_ip: 'YOUR_system_ip'
```
Run python scripts.
```
./approute_statistics_api.py
./device-health.py
```
![Imagen of localhost:3000](/imagen/Capt1.png)

