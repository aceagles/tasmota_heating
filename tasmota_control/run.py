import requests
import os
from datetime import datetime
import time
import redis

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, charset='utf-8', decode_responses=True)

prometheus = os.environ.get("PROM_HOST", "http://192.168.1.140:9090/")

def switch_toggle(mod, switch_info):
    switch_query = f"{switch_info['url']}/cm?cmnd=Power%20{mod}"
    print(switch_query)
    is_on = requests.get(switch_query).json()['POWER'] == 'ON'
    redis_client.hset(job_name, 'is_on',  int(is_on))

def central_toggle(mod, switch_info):
    switch_query = f"{switch_info['url']}/data?cmd={mod}"
    return_data = requests.get(switch_query).json()

while True:
    for job_name in redis_client.keys():
        query = f'{prometheus}/api/v1/query?query=temperature{{job="{job_name}"}}'
        read_time = value = None
        x = requests.get(query).json()
        # Check if there were any matching results
        if len(x['data']['result']) > 0:
            #If there were then parse the return to get just the first returned series.
            # Should only be one so if there's more then just bin them
            tmp = x['data']['result'][0]["value"]
            # Parse the returned values 
            read_time = datetime.fromtimestamp(tmp[0])
            value = float(tmp[1])
            print(read_time, value)
            switch_info = redis_client.hgetall(job_name)
            print(switch_info)
            mod = ""
            if(int(switch_info['active']) > 0):
                print("Is Actives")
                if (value <= float(switch_info['setpoint']) - float(switch_info['delta'])):
                    mod = "On"
                elif (value >= float(switch_info['setpoint'])):
                    mod = "Off"
            try:
                switch_toggle(mod, switch_info)
            except:
                print("unable to query")
        
        time.sleep(10)