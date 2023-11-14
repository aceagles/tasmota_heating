from flask import Flask, abort, request, jsonify
import redis
import os

app = Flask(__name__)

redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_port = 6379
redis_db = 0

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db)

@app.get('/<string:job>/data')
def index(job):
    try:
        status = redis_client.json().get(job)
    except:
        abort(404)
    return f"is_on {1 if status['is_on'] else 0} \nsetpoint {status['setpoint']}"

@app.post("/<string:job>/set")
def setpoint(job):
    sp = request.json
    key = list(sp.keys())[0]
    redis_client.json().set(job, f"$.{key}", sp[key])
    return jsonify(sp)

@app.post("/<string:job>/init")
def init(job):
    url = request.json['url']
    metadata = {
        "url": url,
        "active": False,
        "is_on": False,
        "setpoint": 15,
        "delta": 2
    }
    redis_client.json().set(job, "$", metadata)
    return jsonify(metadata)

if __name__ == '__main__':
    app.run()