import requests
import os
from datetime import datetime, timedelta
import time
import redis

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, charset='utf-8', decode_responses=True)

prometheus = os.environ.get("PROM_HOST", "http://192.168.1.140:9090/")

def is_within_5_minutes(time_string):
    # Parse the current time
    current_time = datetime.now().time()

    # Parse the specified time string
    specified_time = datetime.strptime(time_string, "%H:%M").time()

    # Calculate the time difference
    time_difference = datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(), specified_time)

    # Check if the absolute difference is within 5 minutes
    return abs(time_difference) <= timedelta(minutes=1)



while True:
    for job_name in redis_client.smembers("heating_controllers"):
        switch_info = redis_client.hgetall(job_name)

        if "start_time" in switch_info:
            if is_within_5_minutes(switch_info["start_time"]):
                switch_info["active"] = 1
                redis_client.hset(job_name, "active", 1)
        if "end_time" in switch_info:
            if is_within_5_minutes(switch_info["end_time"]):
                switch_info["active"] = 0
                redis_client.hset(job_name, "active", 0)
        sensor_name = ""
        if 'job' in switch_info:
            sensor = switch_info['job']
            if 'sensor_name' in switch_info:
                sensor_name = f',name="{switch_info["sensor_name"]}"'
        else:
            sensor = job_name

        query = f'{prometheus}/api/v1/query?query=temperature{{job="{sensor}"{sensor_name}}}'
        read_time = value = None
        x = requests.get(query).json()
        # Check if there were any matching results
        if len(x['data']['result']) > 0:
            #If there were then parse the return to get just the first returned series.
            # Should only be one so if there's more then just bin them
            tmp = x['data']['result'][0]["value"]
            # Parse the returned values 
            read_time = datetime.fromtimestamp(tmp[0])
            # TODO - deactivate if sensor data is too old
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