import os
from dotenv import load_dotenv

import xml.etree.ElementTree as ET
import hashlib
import requests
import json

import logging
import logging_loki

load_dotenv()

FRITZ_HOST = os.getenv('FRITZ_HOST')
FRITZ_USER = os.getenv('FRITZ_USER')
FRITZ_PASS = os.getenv('FRITZ_PASS')
LOKI_HOST = os.getenv('LOKI_HOST')
LOG_FILE = os.getenv('LOG_FILE')

logging_loki.emitter.LokiEmitter.level_tag = "level"
handler = logging_loki.LokiHandler(
   url=LOKI_HOST+"/loki/api/v1/push",
   version="1",
)
logger = logging.getLogger("fritzbox_logs")
logger.addHandler(handler)

def get_md5_hash(challenge, password):
    hash_me = (challenge + "-" + password).encode("UTF-16LE")
    hashed = hashlib.md5(hash_me).hexdigest()
    return challenge + "-" + hashed

def get_session_id():
    doc = ET.fromstring(
        requests.get(FRITZ_HOST+"/login_sid.lua").text
    )

    sid = doc.findtext("SID")

    # cached sid
    if(sid != "0000000000000000"):
        return sid
    
    challenge = doc.findtext("Challenge")    
    return login(challenge)    

def login(challenge):
    params = {
         "username": FRITZ_USER,
        "response": get_md5_hash(challenge, FRITZ_PASS)
    }
    doc = ET.fromstring(
        requests.get(FRITZ_HOST+"/login_sid.lua", params=params).text
    )

    sid = doc.findtext("SID")
    if(sid == "0000000000000000"):
        print("Error getting SID")
        exit()

    return sid

def get_logs(sid):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "xhr": 1,
        "sid": sid, 
        "lang": "de",
        "page": "log",
        "xhrId": "log",
        "filter": "all"
    }
    ret = requests.post(FRITZ_HOST+"/data.lua", data=data, headers=headers)
    json = ret.json()
    return json["data"]["log"]

def load_last_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_last_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f)

def get_new_logs(sid):
    logs = get_logs(sid)
    last_logs = load_last_logs()

    print("current logs: " + str(len(logs)))
    print("last logs: " + str(len(last_logs)))

    new_logs = []
    for log in logs:
        if log not in last_logs:  
            new_logs.append(log)

    save_last_logs(logs) 

    print("new logs: " + str(len(new_logs)))
    return new_logs

def send_logs(json):
    for log in json:
        logger.warning(
            log["msg"],
            extra={"tags": {"service": "fritzbox_logs"}},
        )

sid = get_session_id()
print("sid: " + sid)

logs = get_new_logs(sid)

send_logs(logs)