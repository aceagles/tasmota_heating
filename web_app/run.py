from flask import Flask, abort, request, jsonify
import redis
import os
from flask_cors import CORS, cross_origin
from datetime import datetime

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, charset='utf-8', decode_responses=True)

@app.get('/<string:job>/data')
def data(job):
    try:
        status = redis_client.hgetall(job)
    except:
        abort(404)
    # TODO - return all values that aren't strings and change booleans to numeric
    return_string = ""
    print(status)
    for key in list(status.keys()):
        
        try:
            return_string += f"{key} {float(status[key])}\n"
        except ValueError:
            pass
    return return_string
@cross_origin
@app.post("/<string:job>/set")
def setpoint(job):
    sp = request.json
    for key in  list(sp.keys()):
        redis_client.hset(job, key, sp[key])
    return jsonify(sp)

@app.post("/<string:job>/init")
def init(job):
    json_data = request.json
    url = json_data['url']
    metadata = {
        "url": url,
        "active": 0,
        "is_on": 0,
        "setpoint": 15,
        "delta": 2
    }
    for key in list(json_data):
        metadata[key] = json_data[key]
    redis_client.hmset(job, metadata)
    # This registers the controller to be evaluated by the setpoint process
    redis_client.sadd("heating_controllers", job)
    return jsonify(metadata)

@app.get("/<string:job>/json")
def json_endpoint(job):
    metadata = redis_client.hgetall(job)
    return jsonify(metadata)

@app.get("/<string:job>/active")
def toggle_active(job):
    new_val = 1- int(redis_client.hget(job, "active"))
    
    redis_client.hset(job, "active", new_val)
    val_dict = {"status": "ON" if new_val == 1  else "OFF"}
    return jsonify(val_dict)

@app.get("/blesensors")
def blesensors():
    sensors = redis_client.smembers("bluetooth_sensors")
    return_string = ""
    now_stamp = datetime.now().timestamp()
    for sensor in sensors:
        data = redis_client.hgetall(sensor)
        # If sensor has been named and the latest reading was within 2 minutes
        if "name" in data and now_stamp - float(data['time']) <= 120:
            for key in list(data.keys()):
        
                try:
                    return_string += f"""{key}{{name="{data['name']}"}} {float(data[key])}\n"""
                except ValueError:
                    pass
    return return_string

@app.get("/")
def index():
    return "here!"
    

if __name__ == '__main__':
    app.run(host="0.0.0.0")