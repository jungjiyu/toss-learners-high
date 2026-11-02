"""Publish StoryBridge's reviewed edition and reachable evidence from immutable Git blobs.
Usage: python tools/publish_storybridge.py /path/to/toss_storybridge SOURCE_COMMIT
Only storybridge/ and storybridge-publication.json are written. No experiments run.
"""
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,urlunsplit,unquote
from html import escape,unescape
from html.parser import HTMLParser
import subprocess,sys,re,json,hashlib,posixpath,collections

SRC=Path(sys.argv[1]).resolve();OUT=Path(__file__).resolve().parents[1]
SHA=subprocess.check_output(['git','rev-parse',sys.argv[2]+'^{commit}'],cwd=SRC,text=True).strip()
SITE='https://jungjiyu.github.io/toss-learners-high/'
PAGES=['storage','recovery','comparison','shared-fanout','connections','distributed','scale','mixed','mixed-runs','reconnect','reconnect-runs']
ROLES={'기준 구현':'91ce2a72a9635a60d8171db5ab5840ade3692926','최종 단일 서버':'d1ab45300a25fc763381899466752482bf6e0921','RabbitMQ 다중 gateway':'c85d5345e1effcc73cf4816341217ad1ad1e7868'}
OFFICIAL_LINKS={
 'https://jakarta.ee/specifications/websocket/2.1/apidocs/server/jakarta/websocket/remoteendpoint':'https://jakarta.ee/specifications/websocket/2.1/apidocs/server/jakarta/websocket/RemoteEndpoint.html',
 'https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html':'https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/innodb-consistent-read.html',
 'https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html':'https://docs.oracle.com/cd/E17952_01/mysql-8.4-en/innodb-locking-reads.html',
}
cache={};todo=collections.deque();queued=set();done={};external=set();redactions=collections.Counter();generated={};rewrites=[]
def blob(path,ref=SHA):
 key=(ref,path)
 if key not in cache:cache[key]=subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=SRC)
 return cache[key]
def iscode(path):return path.startswith(('src/','docs/scripts/','scripts/')) or PurePosixPath(path).suffix in ['.java','.py','.js','.sql','.properties']
def dest(path,ref=SHA):
 if path.startswith('docs/articles/'):return 'storybridge/evidence/articles/'+PurePosixPath(path).name
 if iscode(path):return 'storybridge/evidence/code/'+ref+'/'+path+'.html'
 if path.startswith('docs/portfolio/'):return 'storybridge/'+path[len('docs/portfolio/'):]
 if path.startswith('docs/assets/'):return 'storybridge/assets/shared/'+path[len('docs/assets/'):]
 if path.startswith('docs/evidence/'):return 'storybridge/evidence/'+path[len('docs/evidence/'):]
 if path.startswith('docs/') and PurePosixPath(path).suffix in ['.json','.txt','.html']:return 'storybridge/evidence/records/'+path[len('docs/'):]
 raise ValueError('Unexpected dependency: '+path)
def include(path,ref=SHA):
 if path=='docs/index.html':path='docs/portfolio/sources.html';ref=SHA
 if path.startswith('../') or '/.scratch/' in path or path.startswith('reference/'):raise ValueError('Out of scope: '+path)
 key=(ref,path)
 if key not in queued:queued.add(key);todo.append(key)
 return dest(path,ref)
def rewrite(value,path,ref):
 value=unescape(value)
 if value in OFFICIAL_LINKS:
  rewrites.append({'source':path,'kind':'official_reference_url','from':value,'to':OFFICIAL_LINKS[value]})
  value=OFFICIAL_LINKS[value]
 u=urlsplit(value)
 if not value or value.startswith(('#','data:','mailto:','tel:','javascript:')):return value
 if u.netloc=='github.com' and u.path.startswith('/jungjiyu/toss_storybridge/blob/'):
  _,owner,repo,kind,commit,code=u.path.split('/',5)
  assert re.fullmatch('[0-9a-f]{40}',commit),value
  target=include(unquote(code),commit)
 elif u.scheme or u.netloc:external.add(value);return value
 else:
  if u.path.startswith('/'):raise ValueError('Domain-root dependency: '+value)
  target_path=posixpath.normpath(posixpath.join(posixpath.dirname(path),unquote(u.path)))
  target=include(target_path,ref)
 fragment=re.sub(r'^(L\d+)-L\d+$',r'\1',u.fragment)
 return urlunsplit(('', '',posixpath.relpath(target,posixpath.dirname(dest(path,ref))),u.query,fragment))

def scrub(text,path):
 rules=[
  ('windows_user',r'(?i)([a-z]:[\\/]+Users[\\/]+)(?!REDACTED)([^\\/\s"<>]+)',lambda m:m[1]+'REDACTED'),
  ('unix_user',r'/Users/(?!REDACTED)[^/\s"\'<>]+',lambda m:'/Users/REDACTED'),
  ('email',r'[A-Za-z0-9_.+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,24}',lambda m:'REDACTED@example.invalid'),
  ('credential',r'(?i)gh[pousr]_[A-Za-z0-9_]{15,}|github_pat_[A-Za-z0-9_]+|(?:Bearer|Basic)\s+[A-Za-z0-9+/=._-]{15,}|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',lambda m:'REDACTED_CREDENTIAL'),
  ('credential_assignment',r'(?i)(\b(?:SB_[A-Z_]*(?:PASSWORD|SECRET)|MYSQL_ROOT_PASSWORD|MYSQL_PASSWORD|SPRING_DATASOURCE_PASSWORD)\s*[=:]\s*)[^\s"\',}]+',lambda m:m[1]+'REDACTED'),
 ]
 for kind,pattern,replace in rules:
  def sub(m):redactions[path,kind]+=1;return replace(m)
  text=re.sub(pattern,sub,text)
 if re.search(r'-----BEGIN [^-]*PRIVATE KEY-----',text):raise ValueError('Private key requires review: '+path)
 return text

class Links(HTMLParser):
 def __init__(self,text):super().__init__();self.refs=[];self.ids=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if tag=='a' and a.get('href'):self.refs.append(a['href'])

def page(title,content):
 return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+'</title><style>body{font:16px/1.8 system-ui,"Malgun Gothic",sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#253343}a{color:#166854}pre{font:13px/1.7 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7f8;padding:20px}.line{display:block;scroll-margin-top:20px}.line:target{background:#fff0ad}.ln{color:#85909b;text-decoration:none;margin-right:20px;user-select:none}li{margin:10px 0}h2{margin-top:36px}</style></head><body>'+content+'</body></html>'

for name in ['index','sources']+[f'articles/{n}' for n in PAGES]:include('docs/portfolio/'+name+'.html')
code_map=json.loads(blob('docs/portfolio/architecture/code-map.json'))
for context in code_map.values():
 if isinstance(context,dict) and 'commit' in context:
  for f in context['files']:include(f['path'],context['commit'])
for commit in ROLES.values():
 files=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'src'],cwd=SRC,text=True).splitlines()
 for f in files:
  if not f.endswith(('.css',)):include(f,commit)

while todo:
 ref,path=todo.popleft();key=(ref,path)
 if key in done:continue
 raw=blob(path,ref);target=dest(path,ref);suffix=PurePosixPath(path).suffix
 done[key]={'source_path':path,'source_commit':ref,'published_path':target,'source_sha256':hashlib.sha256(raw).hexdigest()}
 if suffix in ['.html','.css','.svg','.json','.jsonl','.csv','.txt','.mmd','.java','.py','.js','.sql','.properties','.xml','.log']:
  text=raw.decode('utf8');text=scrub(text,path)
  if iscode(path):
   lines=''.join(f'<span class="line" id="L{i}"><a class="ln" href="#L{i}">{i}</a>{escape(line)}</span>' for i,line in enumerate(text.splitlines(),1))
   role=next((k for k,v in ROLES.items() if v==ref),'중간 비교 구현/검증 코드')
   text=page(PurePosixPath(path).name+' · '+role,'<p><a href="'+posixpath.relpath('storybridge/evidence/code/index.html',posixpath.dirname(target))+'">구현 근거 목록</a></p><h1>'+escape(PurePosixPath(path).name)+'</h1><p>'+role+' · 원본 커밋 <code>'+ref+'</code></p><p>'+escape(path)+'</p><p>원본 코드의 공개용 사본이다. 자격정보는 필요한 경우 REDACTED로 대체했다.</p><pre><code>'+lines+'</code></pre>')
  elif path.startswith('docs/articles/'):
   parsed=Links(text);name=PurePosixPath(path).stem
   references=[]
   for href in dict.fromkeys(parsed.refs):
    if href.startswith('#'):continue
    result=rewrite(href,path,ref)
    references.append('<li><a href="'+escape(result,quote=True)+'">'+escape(unquote(urlsplit(href).path).split('/')[-1] or href)+'</a></li>')
   anchors=''.join('<span id="'+escape(i,quote=True)+'"></span>' for i in parsed.ids)
   text=page('측정·구현 근거: '+name,anchors+'<p><a href="../../articles/'+name+'.html">아티클로 돌아가기</a></p><h1>측정·구현 근거</h1><p>내부 작업 기록 대신 해당 글에서 참조한 공개 측정 자료와 구현 코드를 제공한다. 원본 문서 커밋: <code>'+SHA+'</code></p><ul>'+''.join(references)+'</ul>')
   rewrites.append({'source':path,'kind':'internal_article_to_evidence_catalog'})
  else:
   if suffix=='.json':
    data=json.loads(text)
    def walk(v,key=''):
     if isinstance(v,dict):return {k:walk(x,k) for k,x in v.items()}
     if isinstance(v,list):return [walk(x,key) for x in v]
     if key.lower() in ['password','root_password','api_key','access_token','refresh_token','authorization','jwt_secret'] and v:
      redactions[path,'json_credential']+=1;return 'REDACTED'
     if isinstance(v,str) and v.startswith('https://github.com/jungjiyu/toss_storybridge/blob/'):
      rewritten=rewrite(v,path,ref)
      return SITE+posixpath.normpath(posixpath.join(posixpath.dirname(target),rewritten))
     return v
    updated=walk(data)
    if updated!=data:text=json.dumps(updated,ensure_ascii=False,indent=2)+'\n'
   if suffix in ['.html','.svg']:
    text=re.sub(r'\b(href|src|xlink:href)=("|\')([^"\']*)\2',lambda m:m[1]+'='+m[2]+escape(rewrite(m[3],path,ref),quote=True)+m[2],text)
   if suffix in ['.css','.svg','.html']:
    text=re.sub(r'url\(\s*(["\']?)([^)"\']+)\1\s*\)',lambda m:'url('+m[1]+rewrite(m[2].strip(),path,ref)+m[1]+')',text)
   if path=='docs/portfolio/sources.html':
    text=text.replace('내부 원문과 외부 글의 1:1 대응','아티클별 공개 근거').replace('보존한 원문','측정·구현 근거')
    text=text.replace('<h2>구현 기준</h2>','<h2>구현 기준</h2><p><a href="evidence/code/index.html">기준 구현 · 최종 단일 서버 · RabbitMQ의 고정 커밋별 코드</a></p>')
   if path.startswith('docs/portfolio/') and suffix=='.html':
    text=text.replace('내부 실험 기록','측정·구현 근거').replace('내부 원문','원문 근거')
  raw=text.encode('utf8')
 p=OUT/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 done[key]['published_sha256']=hashlib.sha256(raw).hexdigest()

code_rows=[]
for label,ref in [*ROLES.items(),('중간 비교 및 검증 코드',None)]:
 rows=[v for (r,p),v in done.items() if iscode(p) and (r==ref if ref else r not in ROLES.values())]
 code_rows.append('<h2>'+label+'</h2><ul>'+''.join('<li><a href="'+posixpath.relpath(v['published_path'],'storybridge/evidence/code')+'">'+escape(v['source_path'])+'</a> · <code>'+v['source_commit'][:12]+'</code></li>' for v in sorted(rows,key=lambda v:(v['source_commit'],v['source_path'])))+'</ul>')
target='storybridge/evidence/code/index.html';content=page('StoryBridge 구현 근거','<p><a href="../../sources.html">소스·측정 근거</a></p><h1>검증 커밋별 구현 코드</h1><p>기준과 최종 구현은 단일 서버이며 RabbitMQ는 별도의 두 gateway 구현이다. 각 파일은 표시한 커밋에서 추출했다.</p>'+''.join(code_rows)).encode('utf8')
(OUT/target).write_bytes(content);generated[target]=hashlib.sha256(content).hexdigest()
records=sorted(done.values(),key=lambda v:v['published_path'])
manifest={'source_repository':'https://github.com/jungjiyu/toss_storybridge','source_commit':SHA,'source_repository_visibility':'private','roles':ROLES,'scope':'External edition, reachable assets and evidence, exact-commit code copies. Internal articles replaced with evidence catalogs. No new measurements.','files':records,'generated':generated,'external_links':sorted(external),'redactions':[{'source':p,'kind':k,'occurrences':n} for (p,k),n in sorted(redactions.items())],'rewrites':rewrites}
(OUT/'storybridge-publication.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({'source_commit':SHA,'files':len(records),'generated':len(generated),'bytes':sum((OUT/v['published_path']).stat().st_size for v in records),'redaction_files':len({p for p,k in redactions})},ensure_ascii=False))
