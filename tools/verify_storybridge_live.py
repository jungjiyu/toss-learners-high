"""Anonymous content verification and Chrome navigation/rendering for the published site.
Usage: python -X utf8 tools/verify_storybridge_live.py https://OWNER.github.io/REPO/
Also accepts a local HTTP base for pre-deployment review; no performance tests.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlsplit,unquote
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright
import json,hashlib,sys,time,re

R=Path(__file__).resolve().parents[1];OUT=R/'.review';OUT.mkdir(exist_ok=True)
BASE=sys.argv[1].rstrip('/')+'/';live=BASE.startswith('https://')
manifest=json.loads((R/'storybridge-publication.json').read_text(encoding='utf8'))
mogu=json.loads((R/'publication.json').read_text(encoding='utf8'))
paths=['index.html','storybridge-publication.json']+[x['published_path'] for x in manifest['files']]+list(manifest['generated'])+[x['published_path'] for x in mogu['files']]
errors=[];bodies={};responses=[]
def fetch(path):
 url=urljoin(BASE,path)
 for attempt in range(3):
  try:
   with urlopen(Request(url,headers={'User-Agent':'Portfolio-anonymous-verification/1.0'}),timeout=40) as response:
    body=response.read();result={'path':path,'url':response.url,'status':response.status,'content_type':response.headers.get('Content-Type'),'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'sha256_matches':body==(R/path).read_bytes()}
    if path.endswith('.json'):json.loads(body)
    if path.endswith('.jsonl'):
     for line in body.splitlines():
      if line.strip():json.loads(line)
    # HTML permits an omitted <html> element; the preserved Mogu snapshot is a <pre> document.
    if path.endswith('.html') and not re.search(rb'<(?:html|pre|main|table)\b',body,re.I):raise ValueError('not an HTML document or diagnostic fragment')
    return result,body
  except Exception as e:
   if attempt==2:return {'path':path,'error':str(e)},b''
with ThreadPoolExecutor(max_workers=8) as pool:
 for i,(row,body) in enumerate(pool.map(fetch,paths),1):
  responses.append(row);bodies[row['path']]=body
  if row.get('status')!=200 or not row.get('sha256_matches'):errors.append(row)
  if i%100==0:print('Anonymous HTTP files checked:',i,flush=True)

class HTML(HTMLParser):
 def __init__(self,raw):super().__init__();self.ids=set();self.refs=[];self.feed(raw.decode('utf8'))
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.add(a['id'])
  for k in ['href','src','xlink:href']:
   if a.get(k):self.refs.append(a[k])
parsed={p:HTML(b) for p,b in bodies.items() if p.endswith(('.html','.svg')) and b}
references=0
for path,doc in parsed.items():
 for value in doc.refs:
  if value.startswith(('data:','mailto:','javascript:')):continue
  url=urljoin(urljoin(BASE,path),value)
  if not url.startswith(BASE):continue
  target=unquote(urlsplit(url).path[len(urlsplit(BASE).path):]);fragment=unquote(urlsplit(url).fragment)
  if target not in bodies:errors.append({'from':path,'href':value,'error':'HTTP target not checked'})
  elif fragment and target in parsed and fragment not in parsed[target].ids:errors.append({'from':path,'href':value,'error':'missing public anchor'})
  references+=1

(OUT/('storybridge-http.json' if live else 'storybridge-local-http.json')).write_text(json.dumps(
 {'base':BASE,'stage':'HTTP and anchor content checked; browser pending','http':responses,'references':references,'errors':errors},ensure_ascii=False,indent=2)+'\n',encoding='utf8')

views=[];routes=[];captures=[];browser_errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 context=browser.new_context(storage_state={'cookies':[],'origins':[]},device_scale_factor=1)
 assert context.cookies()==[]
 page=context.new_page()
 page.on('pageerror',lambda e:browser_errors.append(str(e)))
 page.on('response',lambda r:browser_errors.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 def go(path):
  page.goto(urljoin(BASE,path),wait_until='networkidle');page.evaluate('document.fonts.ready')
  page.add_style_tag(content='html{scroll-behavior:auto!important}')
 def shot(name):
  f=OUT/(('public-' if live else 'local-')+name+'.png');page.screenshot(path=str(f));captures.append(f.name)
 for width in [1280,390]:
  page.set_viewport_size({'width':width,'height':1100})
  go('index.html');shot(f'root-{width}')
  page.locator('a[href="storybridge/articles/reconnect.html"]').click();page.wait_for_load_state('networkidle')
  assert page.url==urljoin(BASE,'storybridge/articles/reconnect.html')
  routes.append({'width':width,'route':'root → StoryBridge representative','url':page.url})
  page.locator('nav.top a[href="../index.html#all"]').click();page.wait_for_load_state('networkidle')
  page.wait_for_function('Math.abs(document.querySelector("#all").getBoundingClientRect().top)<200')
  assert page.url.endswith('/storybridge/index.html#all')
  routes.append({'width':width,'route':'representative → actual list','top':page.locator('#all').bounding_box()['y']})
  go('index.html');page.locator('a[href="storybridge/index.html#all"]').click();page.wait_for_load_state('networkidle')
  page.wait_for_function('Math.abs(document.querySelector("#all").getBoundingClientRect().top)<200')
  assert page.locator('#all .card').count()==11;shot(f'storybridge-list-{width}')
  routes.append({'width':width,'route':'root → StoryBridge list','cards':11,'top':page.locator('#all').bounding_box()['y']})
  for path in ['storybridge/index.html']+['storybridge/articles/'+f.name for f in sorted((R/'storybridge/articles').glob('*.html'))]:
   go(path)
   info=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+1,images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})),font:document.fonts.check('16px Portfolio'),styles:document.styleSheets.length,anchors:[...document.querySelectorAll('.toc a')].every(a=>document.getElementById(new URL(a.href).hash.slice(1)))})''')
   info.update(path=path,width=width);views.append(info)
   if info['overflow'] or not info['styles'] or not info['font'] or not info['anchors'] or not all(i['loaded'] for i in info['images']):errors.append(info)
   if path=='storybridge/index.html':shot(f'storybridge-guide-{width}')
   if path.endswith('/reconnect.html'):
    shot(f'reconnect-opening-{width}')
    page.locator('.finding').scroll_into_view_if_needed();shot(f'reconnect-summary-{width}')
    page.locator('[data-origin="reconnect:56"] li').nth(2).scroll_into_view_if_needed();shot(f'reconnect-p99-{width}')
    assert 'p99는 매회 250ms 이하였다' in page.locator('[data-origin="reconnect:56"]').inner_text()
    for label,locator in [('graph',page.locator('figure').first),('table',page.locator('.table-wrap.wide').first)]:
     locator.scroll_into_view_if_needed();shot(f'reconnect-{label}-{width}')
     if label=='table':
      scroll=locator.evaluate('e=>{e.scrollLeft=e.scrollWidth;return {max:e.scrollWidth-e.clientWidth,actual:e.scrollLeft}}')
      assert scroll['actual']>=scroll['max']-1
     else:
      region=locator.locator('.figure-scroll')
      if region.count():
       scroll=region.evaluate('e=>{e.scrollLeft=e.scrollWidth;return {max:e.scrollWidth-e.clientWidth,actual:e.scrollLeft}}')
       assert scroll['actual']>=scroll['max']-1
   if path.endswith('/mixed.html'):
    target=page.locator('[data-origin="mixed:58"]');target.scroll_into_view_if_needed();shot(f'mixed-backlog-{width}')
    assert '합계 초당 17,500건씩 늘어난다' in target.inner_text() and '상한 계산' not in target.inner_text()
   if path.endswith('/reconnect-runs.html'):
    page.locator('.finding').scroll_into_view_if_needed();shot(f'reconnect-runs-summary-{width}')
    assert '저장 여부를 확인하지 못해 미확정으로 남겼다' in page.locator('.finding').inner_text()
   if '/articles/' in path:
    page.locator('nav.top a[href="../index.html#all"]').click();page.wait_for_load_state('networkidle')
    page.wait_for_function('Math.abs(document.querySelector("#all").getBoundingClientRect().top)<200')
    routes.append({'width':width,'route':path+' → list','top':page.locator('#all').bounding_box()['y']})
  go('index.html');page.locator('a[href="mogu/articles/retries.html"]').click();page.wait_for_load_state('networkidle')
  assert page.url==urljoin(BASE,'mogu/articles/retries.html');shot(f'mogu-representative-{width}')
  go('index.html');page.locator('a[href="mogu/index.html#articles"]').click();page.wait_for_load_state('networkidle')
  page.wait_for_function('Math.abs(document.querySelector("#articles").getBoundingClientRect().top)<200')
  # Existing Mogu uses an h2 anchor followed by the .cards container.
  assert page.locator('.cards .card').count()==11;shot(f'mogu-list-{width}')
  routes.append({'width':width,'route':'root → existing mogu representative/list','cards':11})
 # Open actual evidence in Chrome, including the linked diagnostic assets and code line.
 examples=[next(x['published_path'] for x in manifest['files'] if x['published_path'].endswith('/report.html')),
           next(x['published_path'] for x in manifest['files'] if x['published_path'].endswith('/plan.json')),
           'storybridge/evidence/code/'+manifest['roles']['최종 단일 서버']+'/src/main/java/dev/storybridge/Store.java.html#L1']
 for path in examples:
  go(path);assert page.locator('body').inner_text().strip();routes.append({'route':'public evidence opened','url':page.url})
 result_cookies=context.cookies();assert not result_cookies
 browser.close()
errors.extend(browser_errors)
result={'base':BASE,'source_commit':manifest['source_commit'],'anonymous':True,'cookies_after':result_cookies,'http':responses,'local_references':references,'views':views,'routes':routes,'captures':captures,'errors':errors,'passed':not errors}
(OUT/('storybridge-live.json' if live else 'storybridge-local.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'http_files':len(responses),'references':references,'views':len(views),'routes':len(routes),'errors':len(errors),'passed':not errors},ensure_ascii=False),flush=True)
if errors:sys.exit(1)
