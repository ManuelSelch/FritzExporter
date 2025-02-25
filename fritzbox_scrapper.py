import xml.etree.ElementTree as ET
import hashlib
from requests import Session
import logging
import logging_loki
import os
from dotenv import load_dotenv

load_dotenv()

FRITZ_HOST = os.getenv('FRITZ_HOST')
FRITZ_USER = os.getenv('FRITZ_USER')
FRITZ_PASS = os.getenv('FRITZ_PASS')
LOKI_HOST = os.getenv('LOKI_HOST')

session = Session() 

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
        session.get(FRITZ_HOST+"/login_sid.lua").text
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
        session.get(FRITZ_HOST+"/login_sid.lua", params=params).text
    )

    sid = doc.findtext("SID")
    if(sid == "0000000000000000"):
        print("Error getting SID")

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
    ret = session.post(FRITZ_HOST+"/data.lua", data=data, headers=headers)
    json = ret.json()
    return json["data"]["log"]

def send_logs(json):
    for log in json:
        logger.warning(
            log["msg"],
            extra={"tags": {"service": "fritzbox_logs"}},
        )

sid = get_session_id()
print("sid: " + sid)

logs = get_logs(sid)
print(logs)

send_logs(logs)

