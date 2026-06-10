#!/usr/bin/env python3
"""Mini-proxy sniffer entre opencode et Ollama.
Listen :11435 → forward :11434. Log complet du payload entrant et de la réponse.
NE MODIFIE RIEN. Pour debug uniquement.
"""
import http.server
import json
import os
import socketserver
import urllib.request
import urllib.error
import datetime

OLLAMA_URL = "http://127.0.0.1:11434"
LISTEN_PORT = 11435
LOG_DIR = "/tmp/ollama-sniff"
os.makedirs(LOG_DIR, exist_ok=True)

REQ_COUNTER = 0


def now():
    return datetime.datetime.utcnow().strftime("%H%M%S-%f")[:-3]


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a, **k):
        return  # mute default

    def _read_body(self):
        n = int(self.headers.get("content-length", 0) or 0)
        return self.rfile.read(n) if n else b""

    def _forward(self, method):
        global REQ_COUNTER
        REQ_COUNTER += 1
        rid = f"{REQ_COUNTER:04d}-{now()}"
        path = self.path
        body = self._read_body()
        upstream = OLLAMA_URL + path

        # Log la requête entrante
        if path.startswith("/v1/chat/completions") or path.startswith("/api/chat") or path.startswith("/api/generate"):
            with open(f"{LOG_DIR}/req-{rid}.json", "wb") as f:
                f.write(body)
            try:
                payload = json.loads(body)
                model = payload.get("model")
                stream = payload.get("stream")
                ntools = len(payload.get("tools") or [])
                nmsgs = len(payload.get("messages") or [])
                input_chars = len(body)
                with open(f"{LOG_DIR}/_summary.log", "a") as f:
                    f.write(f"[{rid}] {method} {path}  model={model}  stream={stream}  tools={ntools}  msgs={nmsgs}  body={input_chars} chars\n")
            except Exception as e:
                with open(f"{LOG_DIR}/_summary.log", "a") as f:
                    f.write(f"[{rid}] {method} {path} (parse error: {e})\n")

        # Forward exact
        headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length", "accept-encoding")}
        req = urllib.request.Request(upstream, data=body or None, method=method, headers=headers)
        try:
            r = urllib.request.urlopen(req, timeout=600)
            resp_body = r.read()
            status = r.status
            resp_headers = dict(r.headers)
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            status = e.code
            resp_headers = dict(e.headers)
        except Exception as e:
            self.send_error(502, str(e))
            return

        # Log la réponse
        if path.startswith("/v1/chat/completions") or path.startswith("/api/chat") or path.startswith("/api/generate"):
            with open(f"{LOG_DIR}/resp-{rid}.txt", "wb") as f:
                f.write(resp_body)
            with open(f"{LOG_DIR}/_summary.log", "a") as f:
                f.write(f"[{rid}] response status={status}  body={len(resp_body)} bytes\n")

        self.send_response(status)
        for k, v in resp_headers.items():
            if k.lower() in ("content-length", "transfer-encoding", "connection"):
                continue
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(resp_body)

    def do_GET(self):     self._forward("GET")
    def do_POST(self):    self._forward("POST")
    def do_PUT(self):     self._forward("PUT")
    def do_DELETE(self):  self._forward("DELETE")
    def do_PATCH(self):   self._forward("PATCH")
    def do_HEAD(self):    self._forward("HEAD")


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    print(f"Sniffer listening :{LISTEN_PORT} → {OLLAMA_URL}")
    print(f"Logs in {LOG_DIR}")
    with ReusableTCPServer(("127.0.0.1", LISTEN_PORT), Handler) as httpd:
        httpd.serve_forever()
