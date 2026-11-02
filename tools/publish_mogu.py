"""Export only reachable portfolio pages/assets/evidence from an immutable source commit.
Usage: python3 tools/publish_mogu.py /path/to/toss_mogu COMMIT
No experiment execution. Preserve other projects in this publishing repository.
"""
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,urlunsplit,unquote
from html import escape,unescape
from html.parser import HTMLParser
import subprocess,sys,re,json,hashlib,posixpath,collections
SRC=Path(sys.argv[1]).resolve();SHA=sys.argv[2];OUT=Path(__file__).resolve().parents[1]
SHA=subprocess.check_output(['git','rev-parse',SHA],cwd=SRC,text=True).strip()
cache={};todo=[];done={};external=set();redactions=[]
def blob(path,ref=SHA):
 key=(ref,path)
 if key not in cache:cache[key]=subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=SRC)
 return cache[key]
def dest(path,ref=SHA):
 if ref!=SHA:return 'mogu/evidence/code/'+ref+'/'+path+'.html'
 if path.startswith('docs/portfolio/'):return 'mogu/'+path[len('docs/portfolio/'):]
 if path.startswith('docs/assets/'):return 'mogu/assets/shared/'+path[len('docs/assets/'):]
 if path.startswith('docs/evidence/'):return 'mogu/evidence/'+path[len('docs/evidence/'):]+('.html' if path.endswith('.py') else '')
 if path=='docs/scripts/correct_occupancy.py':return 'mogu/evidence/tools/correct_occupancy.py.html'
 raise ValueError('Unexpected publication dependency: '+path)
def include(path,ref=SHA):
 if '/.work/' in path or '/review/' in path or path.startswith('docs/articles/'):raise ValueError('Internal material: '+path)
 key=(ref,path)
 if key not in done and key not in todo:todo.append(key)
 return dest(path,ref)
def rewrite(ref,path,commit):
 ref=unescape(ref);u=urlsplit(ref)
 if not ref or ref.startswith(('#','data:','mailto:','tel:')):return ref
 if u.netloc=='github.com' and u.path.startswith('/jungjiyu/toss_mogu/blob/'):
  _,owner,repo,kind,sha,code=u.path.split('/',5);target=include(code,sha)
 elif u.scheme or u.netloc:
  external.add(ref);return ref
 else:
  if u.path.startswith('/'):raise ValueError('Domain-root path: '+ref)
  target_path=posixpath.normpath(posixpath.join(posixpath.dirname(path),unquote(u.path)))
  target=include(target_path,commit)
 relative=posixpath.relpath(target,posixpath.dirname(dest(path,commit)))
 return urlunsplit(('', '',relative,u.query,u.fragment))
def scrub(s,path):
 # Referenced PG artifacts contain hashes, not raw actual-PG payment objects.
 # Simulator identities are synthetic and retained for joining ledgers.
 rules={'local_user_path':r'/Users/[^/\s"\'<>]+','email':r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
 'credential':r'(?i)(?:test|live)_(?:sk|gsk|ck|gck)_[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9_]{15,}|github_pat_[A-Za-z0-9_]+|(?:Bearer|Basic)\s+[A-Za-z0-9+/=._-]{8,}'}
 for kind,pattern in rules.items():
  def replace(m):
   redactions.append({'source':path,'kind':kind})
   return '/Users/REDACTED' if kind=='local_user_path' else '[REDACTED_'+kind.upper()+']'
  s=re.sub(pattern,replace,s)
 if re.search(r'-----BEGIN [^-]*PRIVATE KEY-----',s):raise ValueError('Private key requires manual review: '+path)
 return s
for path in ['docs/portfolio/index.html',*[f'docs/portfolio/articles/{n}.html' for n in ['recovery','inventory','execution','reconciliation','overload','transactions','purchases','retries','terminal','verification','final']]]:include(path)
while todo:
 ref,path=todo.pop(0);key=(ref,path)
 if key in done:continue
 raw=blob(path,ref);target=dest(path,ref);suffix=PurePosixPath(path).suffix
 done[key]={'source_path':path,'source_commit':ref,'published_path':target,'source_sha256':hashlib.sha256(raw).hexdigest()}
 if suffix in ['.html','.css','.svg','.json','.txt','.py','.java']:
  text=raw.decode('utf-8');text=scrub(text,path)
  if suffix in ['.html','.svg']:
   text=re.sub(r'\b(href|src|xlink:href)=("|\')([^"\']*)\2',lambda m:m[1]+'='+m[2]+escape(rewrite(m[3],path,ref),quote=True)+m[2],text)
  if suffix in ['.css','.svg','.html']:
   # Preserve CSS quoting: adding double quotes inside SVG attributes breaks XML.
   text=re.sub(r'url\(\s*(["\']?)([^)"\']+)\1\s*\)',lambda m:'url('+m[1]+rewrite(m[2].strip(),path,ref)+m[1]+')',text)
  if suffix in ['.py','.java']:
   code=text;text='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(PurePosixPath(path).name)+' · 구현 근거</title><style>body{font:16px/1.7 sans-serif;max-width:1100px;margin:30px auto;padding:0 20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f7;padding:20px;font:14px/1.6 monospace}</style><h1>'+escape(PurePosixPath(path).name)+'</h1><p>원본 커밋: '+ref+'</p><p>'+escape(path)+'</p><pre><code>'+escape(code)+'</code></pre></html>'
  raw=text.encode()
 p=OUT/target;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 done[key]['published_sha256']=hashlib.sha256(raw).hexdigest()
(OUT/'.nojekyll').touch()
records=sorted(done.values(),key=lambda x:x['published_path'])
manifest={'source_repository':'https://github.com/jungjiyu/toss_mogu','source_commit':SHA,'source_repository_visibility':'private','scope':'12 external pages and only their reachable assets/evidence. Original internal articles and full experiment directories excluded.','files':records,'external_links':sorted(external),'redactions':[{'source':p,'kind':k,'occurrences':n} for (p,k),n in collections.Counter((r['source'],r['kind']) for r in redactions).items()]}
(OUT/'publication.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_commit':SHA,'files':len(records),'bytes':sum((OUT/x['published_path']).stat().st_size for x in records),'redactions':manifest['redactions']},ensure_ascii=False))
from reserve_mogu_image_space import reserve
reserve(OUT)
