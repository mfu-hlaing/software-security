"""Host-only authenticated API for fixed personal lab actions and a tool-free tutor."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import time
import guide
from manager import Manager

ROOT = Path(os.environ.get('CAMPUS_ROOT', '/opt/software-security'))
STATE = Path(os.environ.get('CAMPUS_STATE', '/var/lib/outsiders'))
CONFIG_PATH = Path(os.environ.get('CAMPUS_CONFIG', '/etc/outsiders/config.json'))


def serve():
    config = json.loads(CONFIG_PATH.read_text())
    token = Path(config['token_file']).read_text().strip()
    if len(token) < 32:
        raise ValueError('broker token missing')
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    manager = Manager(config, STATE / 'labs.json')
    budget = guide.Budget(STATE / 'guide-budget.db')
    guide_gate = threading.BoundedSemaphore(1)
    request_gate = threading.BoundedSemaphore(5)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Questions, tokens and student activity never enter access logs.

        def reply(self, code, result):
            body = json.dumps(result).encode()
            self.send_response(code)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != '/v1/action' or not hmac.compare_digest(
                    self.headers.get('Authorization','').encode(), ('Bearer '+token).encode()):
                return self.reply(403, {'error':'denied'})
            if not request_gate.acquire(blocking=False):
                return self.reply(429, {'error':'busy'})
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 8000:
                    return self.reply(413, {'error':'body limit'})
                self.connection.settimeout(10)
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict) or not manager.valid_slot(data.get('slot')):
                    return self.reply(403, {'error':'unknown learner slot'})
                slot, action = data['slot'], data.get('action')
                if action == 'start':
                    result = manager.start(slot, data.get('lab'))
                elif action == 'stop':
                    result = manager.stop(slot)
                elif action == 'status':
                    result = manager.status(slot)
                elif action == 'guide':
                    week, question = data.get('week'), data.get('question')
                    if type(week) is not int or not 1 <= week <= 19 or not isinstance(question,str) or not 3 <= len(question) <= 1500:
                        return self.reply(400, {'error':'invalid question'})
                    if not guide_gate.acquire(blocking=False):
                        return self.reply(200, {'error':'Scout is answering another learner. Try again in a moment.'})
                    try:
                        result = guide.answer(ROOT, config['deepseek_key_file'], budget, slot, week, question)
                    finally:
                        guide_gate.release()
                else:
                    return self.reply(400, {'error':'unsupported action'})
                self.reply(200, result)
            except Exception as error:
                print('Broker operation failed: '+type(error).__name__,flush=True)
                self.reply(503, {'error':'The service could not complete this operation. Course documents remain available.'})
            finally:
                request_gate.release()

    def reaper():
        while True:
            try:
                manager.reap()
            except Exception:
                pass
            time.sleep(30)

    threading.Thread(target=reaper, daemon=True).start()
    server = ThreadingHTTPServer((config.get('bind', '172.30.1.1'),8787), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == '__main__':
    serve()
