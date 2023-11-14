import requests
import os
from datetime import datetime
import time
import redis

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

prometheus = os.environ.get("PROM_HOST", "http://192.168.1.140:9090/")



while True:
    for job_name in redis_client.keys():
        job_name = job_name.decode('utf-8')
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
        switch_info = redis_client.json().get(job_name)
        print(switch_info)
        mod = ""
        if(switch_info['active']):
            if (value <= switch_info['setpoint'] - switch_info['delta']):
                mod = "On"
            elif (value >= switch_info['setpoint']):
                mod = "Off"
        try:
            switch_query = f"{switch_info['url']}/cm?cmnd=Power%20{mod}"
            print(switch_query)
            is_on = requests.get(switch_query).json()['POWER'] == 'ON'
            redis_client.json().set(job_name, '$.is_on', is_on)
        except:
            print("unable to query")
        
        time.sleep(10)