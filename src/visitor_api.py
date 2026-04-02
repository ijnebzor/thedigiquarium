#!/usr/bin/env python3
"""
Visitor Tank API — HTTP endpoint for the bouncer.
Visitors connect via web browser, messages route through the bouncer
to the specimen, responses come back.

Runs on port 8200. NOT exposed to internet — only via Rustunnel.
"""
import json, sys, os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'daemons'))
from security.bouncer import Bouncer

bouncer = Bouncer()

class VisitorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/session/start':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            ip = self.client_address[0]
            password = body.get('password', '')
            ok, msg, session = bouncer.start_session(ip, password)
            self._respond(200 if ok else 403, {'ok': ok, 'message': msg, 
                          'session_id': session.session_id if session else None,
                          'specimen': session.specimen_name if session else None})

        elif self.path == '/api/message':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            session_id = body.get('session_id', '')
            message = body.get('message', '')
            ok, msg, response = bouncer.process_message(session_id, message)
            self._respond(200 if ok else 400, {'ok': ok, 'message': msg, 'response': response})

        elif self.path == '/api/session/end':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            session_id = body.get('session_id', '')
            bouncer.end_session(session_id, 'visitor_ended')
            self._respond(200, {'ok': True, 'message': 'Session ended'})

        else:
            self._respond(404, {'error': 'Not found'})

    def do_GET(self):
        if self.path == '/api/status':
            self._respond(200, bouncer.get_status())
        elif self.path == '/api/health':
            self._respond(200, {'ok': True, 'tanks': bouncer.verify_visitor_containers()})
        else:
            self._respond(404, {'error': 'Not found'})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    port = int(os.getenv('VISITOR_API_PORT', '8200'))
    print(f"Visitor API starting on port {port}")
    HTTPServer(('0.0.0.0', port), VisitorHandler).serve_forever()
