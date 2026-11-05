#!/usr/bin/env python3
"""Minimal client for the Alcatel HH40V stock web API.

Usage: hh40v_webapi.py USER PASS info | backup FILE | restore FILE
The request keys and login obfuscation come from the stock web UI (dist/build.js).
"""
import json
import sys
import urllib.request

BASE = "http://192.168.1.1"
VKEY = "KSDHSDFOGQ5WERYTUIQWERTYUISDFG1HJZXCVCXBN2GDSMNDHKVKFsVBNf"
KEY = "e5dl12XYVggihggafXWf0f2YSf2Xngd1"


def encrypt(s):
    out = []
    for i, ch in enumerate(s):
        c, k = ord(ch), ord(KEY[i % len(KEY)])
        out.append(chr((k & 0xF0) | ((c & 0xF) ^ (k & 0xF))))
        out.append(chr((k & 0xF0) | ((c >> 4) ^ (k & 0xF))))
    return "".join(out)


class Client:
    def __init__(self):
        self.token = ""

    def headers(self):
        h = {"_TclRequestVerificationKey": VKEY, "Referer": BASE + "/index.html",
             "Content-Type": "application/json"}
        if self.token:
            h["_TclRequestVerificationToken"] = self.token
        return h

    def call(self, method, params=None):
        body = json.dumps({"id": "12", "jsonrpc": "2.0", "method": method,
                           "params": params or {}}).encode()
        req = urllib.request.Request(BASE + "/jrd/webapi", body, self.headers())
        return json.load(urllib.request.urlopen(req, timeout=20))

    def login(self, user, pw):
        for params in ({"UserName": encrypt(user), "Password": encrypt(pw)},
                       {"UserName": user, "Password": pw}):
            r = self.call("Login", params)
            if "result" in r and "token" in r["result"]:
                self.token = encrypt(str(r["result"]["token"]))
                return r
        return r

    def download(self, path, dest):
        req = urllib.request.Request(BASE + path, headers=self.headers())
        data = urllib.request.urlopen(req, timeout=30).read()
        open(dest, "wb").write(data)
        return len(data)

    def upload_restore(self, path):
        import uuid
        b = uuid.uuid4().hex
        data = open(path, "rb").read()
        parts = [
            f"--{b}\r\nContent-Disposition: form-data; name=\"_TclRequestVerificationToken\"\r\n\r\n{self.token}\r\n".encode(),
            f"--{b}\r\nContent-Disposition: form-data; name=\"fileUpload\"; filename=\"configure.bin\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode(),
            data, f"\r\n--{b}--\r\n".encode()]
        h = self.headers()
        h["Content-Type"] = f"multipart/form-data; boundary={b}"
        req = urllib.request.Request(BASE + "/goform/uploadBackupSettings", b"".join(parts), h)
        return urllib.request.urlopen(req, timeout=60).read().decode(errors="replace")


if __name__ == "__main__":
    import time
    c = Client()
    user, pw, action = sys.argv[1], sys.argv[2], sys.argv[3]
    print("login:", c.login(user, pw))
    if action == "info":
        print(c.call("GetSystemInfo"))
    elif action == "backup":
        print("SetDeviceBackup:", c.call("SetDeviceBackup", {}))
        time.sleep(3)
        print("bytes:", c.download("/cfgbak/configure.bin", sys.argv[4]))
    elif action == "restore":
        print("upload:", c.upload_restore(sys.argv[4]))
