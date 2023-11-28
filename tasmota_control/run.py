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
  

while True:
    for job_name in redis_client.keys():
        switch_info = redis_client.hgetall(job_name)
        if 'sensor' in switch_info:
            sensor = switch_info['sensor']
        else:
            sensor = job_name
        query = f'{prometheus}/api/v1/query?query=temperature{{job="{sensor}"}}'
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
            
            mod = ""
            if(int(switch_info['active']) > 0):
                print("Is Active")
                if (value <= float(switch_info['setpoint']) - float(switch_info['delta'])):
                    mod = "On"
                elif (value >= float(switch_info['setpoint'])):
                    mod = "Off"
            else:
                mod = "Off"
            try:
                if 'type' in switch_info and switch_info['type'] == "central":
                    switch_query = f"{switch_info['url']}/data?cmd={mod}"
                    return_data = requests.get(switch_query, timeout=5).json()
                    for key in list(return_data.keys()):
                        if type(return_data[key]) :
                            return_data[key] = 1 if return_data[key] else 0
                        redis_client.hset(job_name, key, return_data[key])
                else:
                    switch_query = f"{switch_info['url']}/cm?cmnd=Power%20{mod}"
                    is_on = requests.get(switch_query, timeout=5).json()['POWER'] == 'ON'
                    redis_client.hset(job_name, 'is_on',  int(is_on))
            except requests.exceptions.ConnectionError:
                print("Unable to Query")
        
        time.sleep(10)