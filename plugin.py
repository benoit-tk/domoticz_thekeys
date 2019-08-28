"""
The Keys python plugin for Domoticz
Author: benoit,
Version:    0.0.1: alpha
"""
"""
<plugin key="TheKeys" name="The Keys" author="benoit" version="0.0.1" wikilink="" externallink="https://store.the-keys.fr">
    <description>
        <h2>The Keys</h2><br/>
        Control your locker from Domoticz
    </description>
    <params>
        <param field="Mode1" label="Gateway IP Address" width="200px" required="true" default="192.168.0.100"/>
        <param field="Mode2" label="Locker Identifier" width="200px" required="true" default=""/>
        <param field="Mode3" label="Share Code" width="200px" required="true" default=""/>
    </params>
</plugin>
"""
import Domoticz

#import json
#import urllib.parse as parse
#import urllib.request as request
#from datetime import datetime, timedelta
#import time
#import base64
#import itertools

import threading
import queue

from gateway import Gateway

class deviceparam:

    def __init__(self, unit, nvalue, svalue):
        self.unit = unit
        self.nvalue = nvalue
        self.svalue = svalue


class BasePlugin:

    def __init__(self):
        self.gateway = Gateway()
        self.messageQueue = queue.Queue()
        self.messageThread = threading.Thread(name="QueueThread", target=BasePlugin.handleMessage, args=(self,))
        return

    def handleMessage(self):
        try:
            while True:
                try:
                    Message = self.messageQueue.get(block=True)
                    self.messageQueue.task_done()
                    Domoticz.Debug("handleMessage: %d"%Message["last_log"])
                    if self.checkStatus():
                        self.lastLog = Message["last_log"]
                except Exception as err:
                    Domoticz.Error("checkStatus error: %s"%str(err))
        except Exception as err:
            Domoticz.Error("handleMessage: %s"%str(err))
            self.messageQueue.task_done()

    def onStart(self):
        Domoticz.Log("onStart")

        self.gatewayIP = Parameters["Mode1"]
        self.lockerId = Parameters["Mode2"]
        self.shareCode = Parameters["Mode3"]

        self.gateway.set_host(self.gatewayIP)

        self.lastLog = -1

        # create the child devices if these do not exist yet
        if not 1 in Devices:
            Domoticz.Device(Name="The Keys", Unit=1, TypeName="Switch", Switchtype=19, Used=1).Create()
        self.messageThread.start()



    def onStop(self):
        Domoticz.Debug("onStop")
        Domoticz.Debugging(0)


    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Unit {}: Command '{}', Level: {}".format(Unit, Command, Level))
        Domoticz.Log("locker code: %s"%self.shareCode)
        if Command == "Off":
            self.gateway.open(self.lockerId, self.shareCode.encode("ascii"))
            Devices[Unit].Update(nValue = 1, sValue = 'Locked')
        else:
            self.gateway.close(self.lockerId, self.shareCode.encode("ascii"))
            Devices[Unit].Update(nValue = 0, sValue = 'Unlocked')


    def onHeartbeat(self):
        #Domoticz.Log("onHeartbeat before search")
        resp = self.gateway.search()
        #Domoticz.Log(str(resp))
        for d in resp["devices"]:
            if str(d["identifier"]) == self.lockerId:
                if d["last_log"] != self.lastLog :
                    Domoticz.Log("Last log: %d"%d["last_log"])
                    self.messageQueue.put({"last_log":d["last_log"]})
                    #self.checkStatus()
                    Domoticz.Log("Found locker %s. RSSI: %d, battery: %d"%(d["identifier"], d["rssi"], d["battery"]))
                    #self.lastLog = d["last_log"]
                break;
        if not self.messageThread.isAlive:
            self.messageThread = threading.Thread(name="QueueThread", target=BasePlugin.handleMessage, args=(self,))
            self.messageThread.start()
        Domoticz.Log("onHeartbeat done.")


    def checkStatus(self):
        resp = self.gateway.locker_status(self.lockerId, self.shareCode.encode("ascii"))
        Domoticz.Log("Check status: %d"%resp["code"])
        if resp["code"] == 49:
            Devices[1].Update(nValue = 1, sValue = 'Locked')
            return True
        elif resp["code"] == 50:
            Devices[1].Update(nValue = 0, sValue = 'Unlocked')
            return True
        return False


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onCommand(Unit, Command, Level, Color):
    global _plugin
    try:
        _plugin.onCommand(Unit, Command, Level, Color)
    except Exception as e:
        Domoticz.Log("An error occurs:%s"%str(e))



def onHeartbeat():
    global _plugin
    try:
        _plugin.onHeartbeat()
    except Exception as e:
        Domoticz.Log("An error occurs:%s"%str(e))


# Plugin utility functions ---------------------------------------------------
