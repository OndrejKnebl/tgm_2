# tgm_2.py
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from dateutil import tz
import requests
import time
import pytz
import os

# Read parameters from environment variables
ttn_personal_API_key = os.getenv('TTN_PERSONAL_API_KEY')
ttn_url = os.getenv('TTN_URL')

db_url = os.getenv('DB_URL')
db_token = os.getenv('DB_WRITE_TOKEN')
db_org = os.getenv('DB_ORG')
db_bucket = os.getenv('DB_BUCKET')

sleep_time = int(os.getenv('COLLECTION_INTERVAL'))


def main():
    if db_token == "AAA" or db_org == "BBB" or db_bucket == "CCC":
        print("Add your configuration from InfluxDB to the docker-compose.yml and restart the containers.")
        time.sleep(sleep_time)
        exit()


    with InfluxDBClient(url=db_url, token=db_token, org=db_org) as client:
        while True:
            write_api = client.write_api(write_options=SYNCHRONOUS)

            session = requests.Session()
            header = {'Authorization': 'Bearer ' + ttn_personal_API_key}
            response = session.get(f"{ttn_url}/api/v3/gateways", headers=header)
            gateways_list = [gateway['ids']['gateway_id'] for gateway in response.json()['gateways']]

            int_parameters = ["uplink_count", "downlink_count"]
            time_parameters = ["last_uplink_received_at", "last_downlink_received_at", "last_status_received_at"]

            all_GWs = []

            my_main_time = int(datetime.now().timestamp() * 1000)

            for gateway in gateways_list:
                session = requests.Session()
                header = {'Authorization': 'Bearer ' + ttn_personal_API_key}
                response = session.get(f"{ttn_url}/api/v3/gs/gateways/{gateway}/connection/stats", headers=header)
                responseJSON = response.json()

                one_GW = {}
                one_GW["measurement"] = db_bucket
                one_GW["tags"] = {"host": str(gateway)}
                one_GW["time"] = my_main_time
                fields = {}


                for param in int_parameters:
                    if responseJSON.get(param) != None:
                        fields[str(param)] = int(responseJSON.get(param))
                    else:
                        fields[str(param)] = 0


                for param in time_parameters:
                    if responseJSON.get(param) != None:
                        myTime = responseJSON.get(param)
                        myTime = myTime.split(".")
                        myTime = datetime.strptime(myTime[0],'%Y-%m-%dT%H:%M:%S')

                        # Convert timezone of datetime from UTC to local
                        myTime = myTime.replace(tzinfo=pytz.UTC)
                        local_zone = tz.tzlocal()
                        myTime = myTime.astimezone(local_zone).timestamp() * 1000

                        fields[str(param)] = int(myTime)
                    else:
                        fields[str(param)] = 0
                        

                one_GW["fields"] = fields
                all_GWs.append(one_GW)


            write_api.write(db_bucket, db_org, all_GWs, "ms")
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
