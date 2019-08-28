#!/usr/bin/python3

#import requests
import json
import time
import sys
import logging
import hashlib
import base64
import hmac
import urllib.parse
import urllib.request
import traceback

import Domoticz

try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
#http_client.HTTPConnection.debuglevel = 1
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

DEFAULT_HOST = "thekeys.local"

class Gateway:

    def __init__(self, debug = False):
        self.debug = debug
        logging.getLogger().setLevel(logging.INFO)
        if debug:
            # You must initialize logging, otherwise you'll not see debug output.
            #http_client.HTTPConnection.debuglevel = 1

            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            #requests_log.propagate = True
        self.host = DEFAULT_HOST

    def set_host(self, host):
        self.host = host

    def synchro_auto(self, enable):
        r = urllib.request.urlopen(urllib.request.Request("http://%s/auto"%(self.host), urllib.parse.urlencode({"enable": enable}).encode("ascii")), timeout = 10)
        logging.debug("synchro auto enable: %s - %s"%(enable, r.read()))

    def open(self, identifier, code):
        return self.action("open", identifier, code)

    def close(self, identifier, code):
        return self.action("close", identifier, code)

    def calibrate(self, identifier, code):
        return self.action("calibrate", identifier, code)

    def locker_status(self, identifier, code, type='json'):
        return self.action("locker_status", identifier, code, type)

    def action(self, type, identifier, code, res_type = 'json'):
        start = time.time()
        ts = str(int(time.time()) - 10)
        hm = hmac.new(code, ts.encode("ascii"), "sha256")
        hash = hm.digest()
        if self.debug:
            logging.debug("hash: " + hm.hexdigest())
        hash = base64.b64encode(hash)
        url = "http://%s/%s"%(self.host, type);
        Domoticz.Log("url: %s"%url)
        r = urllib.request.urlopen(urllib.request.Request(url, urllib.parse.urlencode({"hash": hash, "identifier":identifier, "ts":ts}).encode("ascii")), timeout = 10)
        if res_type == 'json':
            res = r.read()
            Domoticz.Log("res: %s"%res)
            #logging.debug(r.text)
            resp = json.loads(res.decode('utf-8'))
            logging.debug("result: %s. Code: %d"%(resp, resp["code"]))
            logging.debug("duration: %f"%(time.time() - start))
            return resp
        else:
            return r

    def search(self):
        url = "http://%s/lockers"%self.host
        req = urllib.request.Request(url)
        r = urllib.request.urlopen(req, timeout = 10)
        try:
            resp = json.loads(r.read().decode('utf-8'))
        except:
            Domoticz.Log("Fail to parse response: ");
            traceback.print_exc()
        #logging.debug("Found %d lockers:"%len(resp["devices"]))
        #for d in resp["devices"]:
        #    logging.debug("Found locker %s. RSSI: %d, battery: %d"%(d["identifier"], d["rssi"], d["battery"]))
        return resp

    def status(self):
        r = requests.get("http://%s/status"%self.host)
        resp = json.loads(r.text.decode('utf-8'))
        logging.debug("Version: %s\nCurrentAction: %s\n"%(resp["version"], resp["current_status"]))

    def synchronize(self):
        r = requests.get("http://%s/synchronize"%self.host)
        logging.debug("resp: %s"% r.text)
        resp = json.loads(r.text.decode('utf-8'))
        return resp

    def update(self):
        r = requests.post("http://%s/update"%self.host)
        logging.debug(r.text)
        resp = json.loads(r.text.decode('utf-8'))
        return resp

    def synchronize_locker(self, identifier):
        r = requests.post("http://%s/locker/synchronize"%self.host, data={"identifier": identifier})
        logging.debug(r.text)

    def update_locker(self, identifier):
        r = requests.post("http://%s/locker/update"%self.host, data={"identifier": identifier})
        logging.debug(r.text)
        resp = json.loads(r.text.decode('utf-8'))
        return resp
