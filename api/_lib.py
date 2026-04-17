import re, urllib.request as _req
from html.parser import HTMLParser

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

def fetch_text(url):
    req=_req.Request(url,headers={'User-Agent':'Mozilla/5.0 TankerTracker/1.0'})
    with _req.urlopen(req,timeout=20) as r: return r.read().decode('utf-8','replace')
    
def _main_text(html):
    p=_TextEx(); p.feed(html); return ' '.join(p.texts)

def fetch_page(url): return _main_text(fetch_text(url))

def parse_darkfleet(text):
    m=re.search(r'(\d[\d,]+) active vessels',text)
    total=int(m.group(1).replace(',','')) if m else None
    flags=[{'flag':x.strip(),'count':int(c)} for x,c in re.findall(r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\.]+?) : (\d+) vessels',text) if 2<=len(x.strip())<=40]
    routes=[{'route':r.strip(),'bpd':int(b.replace(',',''))} for r,b in re.findall(r'([A-Za-z][\w\s]+? to [A-Za-z][\w\s]+?) : ([\d,]+) barrels per day',text)]
    sizes=[{'cls':s.strip(),'count':int(c)} for s,c in re.findall(r'(Handysize[^:]*|Aframax[^:]*|VLCC[^:]*|Suezmax[^:]*|Panamax[^:]*) : (\d+) vessels',text)]
    return {'total':total,'flags':flags[:20],'routes':routes[:10],'sizes':sizes}

def parse_lostandfound(text):
    entries=re.findall(r'([A-Z][A-Z0-9 \-\.]+) \((\d{7,9})\) (?:Taken since: (\d{4}-\d{2}-\d{2}) \(\d+ days\) )?Last seen: (\d{4}-\d{2}-\d{2}) Coordinates: ([\d\.\-]+), ([\d\.\-]+)',text)
    return [{'name':n.strip(),'imo':i,'taken':t or None,'last_seen':ls,'lat':float(la),'lon':float(lo),'type':'taken' if t else 'navy'} for n,i,t,ls,la,lo in entries]

def parse_sanctioned_count(text):
    m=re.search(r'(\d[\d,]+)\s+(?:sanctioned|vessel)',text,re.I)
    return int(m.group(1).replace(',','')) if m else None
