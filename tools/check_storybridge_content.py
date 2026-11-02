"""Check published tables/code, immutable diagrams and numeric evidence against source blobs."""
from pathlib import Path
from html.parser import HTMLParser
import sys,subprocess,json,hashlib,re
R=Path(__file__).resolve().parents[1];SRC=Path(sys.argv[1]).resolve()
m=json.loads((R/'storybridge-publication.json').read_text(encoding='utf8'))
class Parts(HTMLParser):
 def __init__(self,text):super().__init__();self.stack=[];self.values=[];self.current=None;self.feed(text)
 def handle_starttag(self,t,a):
  if t in ['table','pre'] and self.current is None:self.current=[t,[]];self.stack=[t]
  elif self.current:self.stack.append(t)
 def handle_endtag(self,t):
  if self.current and t==self.current[0]:self.values.append((t,''.join(self.current[1])));self.current=None;self.stack=[]
 def handle_data(self,s):
  if self.current:self.current[1].append(s)
def numeric(v):
 h=hashlib.sha256()
 def visit(x,path):
  if isinstance(x,dict):
   for k,v in sorted(x.items()):visit(v,path+'/'+k)
  elif isinstance(x,list):
   for i,v in enumerate(x):visit(v,path+'/'+str(i))
  elif isinstance(x,(int,float,bool)) or x is None:h.update((path+'='+json.dumps(x)+'\n').encode())
 visit(v,'');return h.hexdigest()
checks=[]
for x in m['files']:
 source=x['source_path'];published=R/x['published_path']
 if source.startswith('docs/portfolio/articles/') or source.endswith('.json') or source in ['docs/portfolio/architecture/before.svg','docs/portfolio/architecture/after.svg','docs/portfolio/architecture/captions.txt']:
  raw=subprocess.check_output(['git','show',x['source_commit']+':'+source],cwd=SRC)
  assert hashlib.sha256(raw).hexdigest()==x['source_sha256'],source
  if source.startswith('docs/portfolio/articles/'):
   ok=Parts(raw.decode('utf8')).values==Parts(published.read_text(encoding='utf8')).values;kind='tables and code text'
  elif source.endswith('.json'):
   ok=numeric(json.loads(raw))==numeric(json.loads(published.read_bytes()));kind='numeric values and their JSON paths'
  else:ok=raw==published.read_bytes();kind='approved architecture bytes'
  checks.append({'path':x['published_path'],'check':kind,'passed':ok})
# A concurrent, independently published Mogu prose revision was merged intact.
# Compare its exact tree and manifest, rather than rejecting that user's update.
MOGU_BASE='2cf6eec65776727ca4419e7bdaa00b4fb72b27b0'
assert not subprocess.check_output(['git','diff',MOGU_BASE,'--','mogu','publication.json'],cwd=R),'Latest published Mogu changed'
result={'source_commit':m['source_commit'],'checks':checks,'passed':all(c['passed'] for c in checks),'existing_mogu_content_unchanged':True,'mogu_preserved_commit':MOGU_BASE}
(R/'.review/content.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
assert result['passed'],[c for c in checks if not c['passed']]
print('Published content checks:',len(checks),'PASS; latest published Mogu and manifest unchanged')
