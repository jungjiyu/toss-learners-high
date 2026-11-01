"""Anonymous HTTP content checks and fresh Chrome reading/navigation checks.
Usage: python3 tools/verify_live.py https://OWNER.github.io/REPO/
Requires Playwright and local Chrome; writes only ignored .review/ output.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright
import json,hashlib,sys,time
R=Path(__file__).resolve().parents[1];OUT=R/'.review';OUT.mkdir(exist_ok=True)
BASE=sys.argv[1].rstrip('/')+'/';manifest=json.loads((R/'publication.json').read_text());errors=[]
files=['index.html','publication.json']+[x['published_path'] for x in manifest['files']]
def get(path):
 url=urljoin(BASE,path)
 try:
  with urlopen(Request(url,headers={'User-Agent':'Portfolio-public-access-check/1.0'}),timeout=45) as response:
   body=response.read();actual=hashlib.sha256(body).hexdigest();expected=hashlib.sha256((R/path).read_bytes()).hexdigest()
   return {'path':path,'url':response.url,'status':response.status,'content_type':response.headers.get('Content-Type'),'sha256_matches':actual==expected,'bytes':len(body)}
 except Exception as e:return {'path':path,'error':str(e)}
with ThreadPoolExecutor(max_workers=6) as pool:responses=list(pool.map(get,files))
for row in responses:
 if row.get('status')!=200 or not row.get('sha256_matches'):errors.append(row)
views=[];routes=[];network=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 context=browser.new_context(storage_state={'cookies':[],'origins':[]},device_scale_factor=1)
 page=context.new_page();page.on('pageerror',lambda e:errors.append({'browser_error':str(e)}))
 page.on('response',lambda r:network.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
 for width in [1280,390]:
  page.set_viewport_size({'width':width,'height':1000})
  page.goto(BASE,wait_until='networkidle');assert page.title()=='정지유 | 토스 Learner’s High 서버 3기 지원 포트폴리오'
  page.get_by_role('link',name='모구시장',exact=True).click();page.wait_for_load_state('networkidle')
  for name in ['대표 글 바로 읽기','전체 11편']:
   b=page.get_by_role('link',name=name,exact=True).bounding_box();assert b and b['y']+b['height']<1000
  page.screenshot(path=str(OUT/f'public-mogu-{width}.png'))
  page.get_by_role('link',name='대표 글 바로 읽기',exact=True).click();page.wait_for_load_state('networkidle');assert page.url==urljoin(BASE,'mogu/articles/retries.html')
  routes.append({'width':width,'route':'root → mogu → representative','url':page.url})
  page.get_by_role('link',name='글 목록',exact=True).click();page.wait_for_load_state('networkidle');assert page.url==urljoin(BASE,'mogu/index.html#articles')
  page.goto(urljoin(BASE,'mogu/index.html'));page.add_style_tag(content='html{scroll-behavior:auto!important}');page.get_by_role('link',name='전체 11편',exact=True).click()
  assert page.url.endswith('#articles') and page.locator('.cards .card').count()==11
  assert page.locator('#articles').bounding_box()['y']<1000
  routes.append({'width':width,'route':'root → mogu → article list','url':page.url})
  for path in ['mogu/index.html']+['mogu/articles/'+f.name for f in sorted((R/'mogu/articles').glob('*.html'))]:
   page.goto(urljoin(BASE,path),wait_until='networkidle');page.evaluate('document.fonts.ready');page.add_style_tag(content='html{scroll-behavior:auto!important}')
   r=page.evaluate('''() => ({title:document.title,overflow:document.documentElement.scrollWidth>innerWidth+1,images:[...document.images].map(i=>({src:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})),styles:[...document.styleSheets].map(s=>s.href),toc:[...document.querySelectorAll('.toc a')].map(a=>({text:a.textContent.trim(),target:document.getElementById(new URL(a.href).hash.slice(1))?.textContent.trim()}))})''')
   r.update(path=path,width=width);views.append(r)
   if r['overflow'] or not all(i['loaded'] for i in r['images']) or not r['styles'] or any(a['text']!=a.get('target') for a in r['toc']):errors.append(r)
   if path.endswith('/retries.html'):
    for label,locator in [('sql',page.locator('pre').filter(has_text='ALTER TABLE attempts')),('graph',page.locator('figure').first),('table',page.locator('table[data-source-table="8"]'))]:
     locator.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'public-retries-{label}-{width}.png'))
    region=page.locator('table[data-source-table="8"]').locator('..');scroll=region.evaluate('e=>{e.scrollLeft=e.scrollWidth;return {max:e.scrollWidth-e.clientWidth,actual:e.scrollLeft}}')
    if scroll['actual']<scroll['max']-1:errors.append({'table_scroll':scroll})
    figure_url=page.locator('figure').first.locator('a').first.get_attribute('href')
    page.goto(urljoin(urljoin(BASE,path),figure_url),wait_until='load');assert page.locator('svg').count()==1
    page.goto(urljoin(BASE,path),wait_until='networkidle')
   if '/articles/' in path:
    page.get_by_role('link',name='글 목록',exact=True).click();page.wait_for_load_state('networkidle');assert page.url==urljoin(BASE,'mogu/index.html#articles')
    routes.append({'width':width,'route':path+' → article list','url':page.url})
 browser.close()
errors.extend(network)
result={'base':BASE,'anonymous':True,'http':responses,'views':views,'routes':routes,'errors':errors,'passed':not errors}
(OUT/'live.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'anonymous_files':len(responses),'screen_views':len(views),'routes':len(routes),'errors':errors,'passed':not errors},ensure_ascii=False))
if errors:sys.exit(1)
