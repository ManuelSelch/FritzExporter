from fritzconnection import FritzConnection
import os
from dotenv import load_dotenv

load_dotenv()

FRITZ_HOST = os.getenv('FRITZ_HOST')
FRITZ_USER = os.getenv('FRITZ_USER')
FRITZ_PASS = os.getenv('FRITZ_PASS')

def get_fritzbox_logs():
    fritz = FritzConnection(address=FRITZ_HOST, user=FRITZ_USER, password=FRITZ_PASS)
    logs = fritz.call_action("DeviceInfo1", "X_AVM-DE_GetAnonymousLog")
    return logs

logs = get_fritzbox_logs()
print("logs:")
print(logs)