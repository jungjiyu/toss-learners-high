"""Check the published dependency closure and local anchors, without a server."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import re,json,hashlib,sys
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
class P(HTMLParser):
 def __init__(self,s):super().__init__();self.refs=[];self.ids=set();self.feed(s)
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  for k in ['href','src','xlink:href']:
   if k in a:self.refs.append(a[k])
manifest=json.loads((R/'publication.json').read_text());errors=[];links=[];cache={}
paths=[R/'index.html']+[R/x['published_path'] for x in manifest['files']]
for row in manifest['files']:
 p=R/row['published_path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['published_sha256']:errors.append([row['published_path'],'content hash mismatch'])
for p in paths:
 if p.suffix not in ['.html','.css','.svg']:continue
 if p.suffix=='.svg':
  try:ET.parse(p)
  except ET.ParseError as e:errors.append([str(p.relative_to(R)),'invalid SVG XML',str(e)])
 s=p.read_text();parsed=P(s);refs=parsed.refs+re.findall(r'url\(\s*["\']?([^)"\']+)',s)
 for ref in refs:
  u=urlsplit(ref)
  if u.scheme or u.netloc:continue
  if u.path.startswith('/'):errors.append([str(p.relative_to(R)),ref,'domain-root path']);continue
  q=(p.parent/unquote(u.path)).resolve() if u.path else p
  if not q.is_relative_to(R) or not q.is_file():errors.append([str(p.relative_to(R)),ref,'missing or outside site']);continue
  if u.fragment and q.suffix in ['.html','.svg']:
   if q not in cache:cache[q]=P(q.read_text())
   if unquote(u.fragment) not in cache[q].ids:errors.append([str(p.relative_to(R)),ref,'missing anchor'])
  links.append({'from':str(p.relative_to(R)),'href':ref,'target':str(q.relative_to(R))})
assert len(list((R/'mogu/articles').glob('*.html')))==11
for p in paths:
 if p.suffix not in ['.html','.svg','.css','.json','.txt']:continue
 s=p.read_text()
 for name,pat in {'credential':r'(?i)(?:test|live)_(?:sk|gsk|ck|gck)_[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9_]{15,}|github_pat_[A-Za-z0-9_]+','private_key':r'-----BEGIN [^-]*PRIVATE KEY-----','local_username':r'/Users/(?!REDACTED)[^/\s"\'<>]+'}.items():
  if re.search(pat,s):errors.append([str(p.relative_to(R)),name])
result={'files':len(paths),'local_references':len(links),'links':links,'errors':errors,'passed':not errors}
out=R/'.review';out.mkdir(exist_ok=True);(out/'static.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(paths),'local_references':len(links),'errors':errors},ensure_ascii=False))
if errors:sys.exit(1)
