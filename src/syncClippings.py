#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys
import json
import struct
import configparser

DEBUG = True

gAppName = "Sync Clippings"
gAppInternalName = "syncClippings"
gAppVer = "1.0a0+"
gConfFilename = "syncClippings.ini"
gSyncFilename = "clippings-sync.json"
gDefaultClippingsData = {
    "version": "6.0",
    "createdBy": "Sync Clippings",
    "userClippingsRoot": []
}

def getAppName():
    return gAppName

def getAppVer():
    return gAppVer

def getSyncFilePath():
    conf = configparser.ConfigParser()
    conf.read(gConfFilename)
    rv = conf["Sync File"]["Path"]
    return rv

def setSyncFilePath(aPath):
    conf = configparser.ConfigParser()
    conf["Sync File"] = { "Path": aPath }
    with open(gConfFilename, "w") as configFile:
        conf.write(configFile)
    
def log(aMsg):
    if DEBUG:
        with open("debug.txt", "a") as file:
            file.write(aMsg)
            file.write("\n")

def getResponseOK():
    rv = { "status": "ok" }
    return rv

def getResponseErr(aErr):
    template = "Exception {0} (arguments: {1!r})"
    rv = {
        "status": "failure",
        "details": template.format(type(aErr).__name__, aErr.args)
    }
    return rv

def getMessage():
    rawLength = sys.stdin.buffer.read(4)
    if len(rawLength) == 0:
        sys.exit(0)
    messageLength = struct.unpack('@I', rawLength)[0]
    message = sys.stdin.buffer.read(messageLength).decode('utf-8')
    rv = json.loads(message)   
    return rv

def encodeMessage(aMsgContent):
    encodedContent = json.dumps(aMsgContent).encode('utf-8')
    encodedLength = struct.pack('@I', len(encodedContent))
    return {'length': encodedLength, 'content': encodedContent}

def sendMessage(aEncodedMsg):
    sys.stdout.buffer.write(aEncodedMsg['length'])
    sys.stdout.buffer.write(aEncodedMsg['content'])
    sys.stdout.buffer.flush()

    
while True:
    msg = getMessage()
    resp = None

    if "msgID" not in msg:
        err = "Error: expected key 'msgID' does not exist!"
        log(err)
        sys.stderr.buffer.write("%s: %s" % (gAppInternalName, err))
        sys.stderr.buffer.flush()
        sys.exit(1)

    log("Value of key 'msgID' from 'msg' dictionary: %s" % msg["msgID"])
    
    if msg["msgID"] == "get-app-version":
        resp = {
            "appName": getAppName(),
            "appVersion": getAppVer()
        }
    elif msg["msgID"] == "get-sync-file-path":
        resp = {
            "syncFilePath": getSyncFilePath()
        }
    elif msg["msgID"] == "set-sync-file-path":
        path = msg["filePath"]
        log("Message 'set-sync-file-path': filePath = {0}".format(msg['filePath']))
        try:
            setSyncFilePath(path)
            resp = getResponseOK()
        except Exception as e:
            resp = getResponseErr(e)

    if resp is not None:
        sendMessage(encodeMessage(resp))
