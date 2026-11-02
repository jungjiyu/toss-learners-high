"""Read-only anonymous checks for third-party references; distinguish them from hosted evidence."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor
import json
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'storybridge-publication.json').read_text(encoding='utf8'))
def check(url):
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:
   body=r.read();return {'url':url,'status':r.status,'resolved':r.url,'content_type':r.headers.get('Content-Type'),'bytes':len(body)}
 except HTTPError as e:return {'url':url,'status':e.code}
 except Exception as e:return {'url':url,'error':str(e)}
with ThreadPoolExecutor(max_workers=5) as pool:rows=list(pool.map(check,manifest['external_links']))
(R/'.review/external.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'checked':len(rows),'not_200':[r for r in rows if r.get('status')!=200]},ensure_ascii=False))
