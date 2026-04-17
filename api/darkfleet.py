from http.server import BaseHTTPRequestHandler
import json, sys, os, datetime
sys.path.insert(0, os.path.dirname(__file__))
from _lib import fetch_page, parse_darkfleet, parse_lostandfound, parse_sanctioned_count

URLS = {
    'darkfleet': 'https://tankertrackers.com/report/darkfleetinfo',
    'lostandfound': 'https://tankertrackers.com/report/lostandfound',
    'sanctioned': 'https://tankertrackers.com/report/sanctioned',
}
PARSERS = {
    'darkfleet': parse_darkfleet,
    'lostandfound': lambda t: {'vessels': parse_lostandfound(t)},
    'sanctioned': lambda t: {'count': parse_sanctioned_count(t)},
}
RTYPE = 'darkfleet'

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            text = fetch_page(URLS[RTYPE])
            data = PARSERS[RTYPE](text)
            body = json.dumps({'type':RTYPE,'data':data,'updated':datetime.datetime.utcnow().isoformat()+'Z'}).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Cache-Control','public, max-age=3600, s-maxage=3600')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers(); self.wfile.write(body)
        except Exception as e:
            self.send_response(500); self.end_headers()
            self.wfile.write(json.dumps({'error':str(e)}).encode())
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
    def log_message(self,*a): pass
