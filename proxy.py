#!/usr/bin/env python3
"""
AISStream.io WebSocket Proxy
----------------------------
Bridges your browser to aisstream.io, keeping your API key server-side.

Usage:
  1. pip3 install websockets
  2. python3 proxy.py --key YOUR_AISSTREAM_API_KEY
  3. Open tanker-tracker.html, enter ws://localhost:8765 as the proxy URL

The browser connects here → this proxy connects to aisstream.io
"""

import asyncio
import json
import argparse
import websockets
import logging
import re
import time
import urllib.request as _urllib
from html.parser import HTMLParser
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"
DEFAULT_PORT = 8765
api_key = None



_DATA_CACHE = {}
_CACHE_TTL  = 3600
_REPORT_URLS = {
    'darkfleet': 'https://tankertrackers.com/report/darkfleetinfo',
    'lostandfound': 'https://tankertrackers.com/report/lostandfound',
    'sanctioned': 'https://tankertrackers.com/report/sanctioned',
}

class _TextEx(HTMLParser):
    def __init__(self):
        super().__init__(); self.texts=[]; self._in=False
    def handle_starttag(self,t,a):
        if t=='main': self._in=True
    def handle_endtag(self,t):
        if t=='main': self._in=False
    def handle_data(self,d):
        if self._in:
            s=d.strip()
            if s: self.texts.append(s)

def _fetch(url):
    req=_urllib.Request(url,headers={'User-Agent':'Mozilla/5.0 TankerTracker/1.0'})
    with _urllib.urlopen(req,timeout=20) as r: return r.read().decode('utf-8','replace')

def _text(html):
    p=_TextEx(); p.feed(html); return ' '.join(p.texts)

def _parse_df(text):
    m=re.search(r'(\d[\d,]+) active vessels',text)
    total=int(m.group(1).replace(',','')) if m else None
    flags=[{'flag':x.strip(),'count':int(c)} for x,c in re.findall(r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\.]+?) : (\d+) vessels',text) if 2<=len(x.strip())<=40]
    routes=[{'route':r.strip(),'bpd':int(b.replace(',',''))} for r,b in re.findall(r'([A-Za-z][\w\s]+? to [A-Za-z][\w\s]+?) : ([\d,]+) barrels per day',text)]
    sizes=[{'cls':s.strip(),'count':int(c)} for s,c in re.findall(r'(Handysize[^:]*|Aframax[^:]*|VLCC[^:]*|Suezmax[^:]*|Panamax[^:]*) : (\d+) vessels',text)]
    return {'total':total,'flags':flags[:20],'routes':routes[:10],'sizes':sizes}

def _parse_lf(text):
    entries=re.findall(r'([A-Z][A-Z0-9 \-\.]+) \((\d{7,9})\) (?:Taken since: (\d{4}-\d{2}-\d{2}) \(\d+ days\) )?Last seen: (\d{4}-\d{2}-\d{2}) Coordinates: ([\d\.\-]+), ([\d\.\-]+)',text)
    return [{'name':n.strip(),'imo':i,'taken':t or None,'last_seen':ls,'lat':float(la),'lon':float(lo),'type':'taken' if t else 'navy'} for n,i,t,ls,la,lo in entries]

async def _get_report(rtype):
    now=time.time()
    cached=_DATA_CACHE.get(rtype)
    if cached and now-cached['ts']<_CACHE_TTL: return cached['payload']
    url=_REPORT_URLS.get(rtype)
    if not url: return None
    loop=asyncio.get_event_loop()
    try:
        html=await loop.run_in_executor(None,_fetch,url)
        text=_text(html)
        if rtype=='darkfleet': parsed=_parse_df(text)
        elif rtype=='lostandfound': parsed={'vessels':_parse_lf(text)}
        else:
            m=re.search(r'(\d[\d,]+)\s+(?:sanctioned|vessel)',text,re.I)
            parsed={'count':int(m.group(1).replace(',','')) if m else None}
        payload={'type':rtype,'data':parsed,'updated':datetime.utcnow().isoformat()+'Z'}
        _DATA_CACHE[rtype]={'ts':now,'payload':payload}
        log.info(f"Fetched {rtype}")
        return payload
    except Exception as e:
        log.error(f"Fetch {rtype} failed: {e}"); return None

async def _handle_http(reader, writer):
    try:
        raw=await asyncio.wait_for(reader.read(4096),timeout=5)
        line=raw.split(b'\n')[0].decode('utf-8','ignore').strip()
        parts=line.split()
        path=parts[1] if len(parts)>=2 else '/'
        if len(parts)>0 and parts[0]=='OPTIONS':
            writer.write(b'HTTP/1.1 204 No Content\r\nAccess-Control-Allow-Origin: *\r\n\r\n')
            await writer.drain(); writer.close(); return
        if path.startswith('/data/'):
            rtype=path.split('/')[2].split('?')[0]
            payload=await _get_report(rtype)
            if payload:
                body=json.dumps(payload).encode()
                writer.write(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n'+f'Content-Length: {len(body)}\r\n\r\n'.encode()+body)
            else:
                writer.write(b'HTTP/1.1 503 Service Unavailable\r\nAccess-Control-Allow-Origin: *\r\n\r\n')
        else:
            writer.write(b'HTTP/1.1 404 Not Found\r\n\r\n')
        await writer.drain()
    except: pass
    finally:
        try: writer.close()
        except: pass

async def handle_browser(browser_ws):
    """One browser client ↔ one aisstream connection."""
    client_ip = browser_ws.remote_address[0]
    log.info(f"Browser connected from {client_ip}")

    try:
        async with websockets.connect(AISSTREAM_URL) as ais_ws:
            log.info("Connected to aisstream.io")

            async def browser_to_ais():
                """Forward subscription messages from browser, injecting the API key."""
                async for raw in browser_ws:
                    try:
                        msg = json.loads(raw)
                        msg["APIKey"] = api_key          # always inject the real key
                        msg.pop("APIKeyPlaceholder", None)
                        await ais_ws.send(json.dumps(msg))
                        log.info(f"Subscription sent: boxes={len(msg.get('BoundingBoxes', []))}")
                    except json.JSONDecodeError:
                        log.warning("Invalid JSON from browser, skipping")

            async def ais_to_browser():
                """Forward AIS messages back to the browser."""
                count = 0
                async for raw in ais_ws:
                    if isinstance(raw, bytes):
                        raw = raw.decode('utf-8')
                    await browser_ws.send(raw)
                    count += 1
                    if count <= 5 or count % 50 == 0:
                        log.info(f"Forwarded {count} AIS messages to browser")

            # Run both directions concurrently
            await asyncio.gather(browser_to_ais(), ais_to_browser())

    except websockets.exceptions.ConnectionClosedError as e:
        log.info(f"Connection closed: {e}")
    except Exception as e:
        log.error(f"Error: {e}")
    finally:
        log.info(f"Client {client_ip} disconnected")


async def main(port):
    log.info(f"Proxy starting on ws://localhost:{port}")
    log.info("Open tanker-tracker.html → Live AIS tab → enter ws://localhost:{port}")
    http_port = port + 1
    http_srv = await asyncio.start_server(_handle_http, "localhost", http_port)
    log.info(f"Data API: http://localhost:{http_port}/data/darkfleet")
    async with websockets.serve(
        handle_browser,
        "localhost",
        port,
        origins=None,           # allow all origins (local only)
        ping_interval=20,
        ping_timeout=60,
    ), http_srv:
        log.info(f"Proxy ready — waiting for browser connections...")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AISStream.io WebSocket Proxy")
    parser.add_argument("--key", default="YOUR_API_KEY_HERE", help="Your aisstream.io API key")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Local port (default {DEFAULT_PORT})")
    args = parser.parse_args()

    api_key = args.key
    log.info(f"API key loaded ({api_key[:4]}...{api_key[-4:]})")

    try:
        asyncio.run(main(args.port))
    except KeyboardInterrupt:
        log.info("Proxy stopped")
