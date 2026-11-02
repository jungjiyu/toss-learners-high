"""Repeat cold, cookie-free list navigation without programmatic scrolling."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json,sys
BASE=sys.argv[1].rstrip('/')+'/';R=Path(__file__).resolve().parents[1];rows=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True)
 for width in [1280,390]:
  for repeat in range(1,4):
   c=b.new_context(storage_state={'cookies':[],'origins':[]},viewport={'width':width,'height':1100})
   page=c.new_page();page.goto(BASE,wait_until='networkidle')
   page.locator('a[href="storybridge/articles/reconnect.html"]').click();page.wait_for_load_state('networkidle')
   page.locator('nav.top a[href="../index.html#all"]').click();page.wait_for_load_state('networkidle')
   page.wait_for_function('Math.abs(document.querySelector("#all").getBoundingClientRect().top)<200')
   row=page.evaluate('''() => ({url:location.href,top:document.querySelector('#all').getBoundingClientRect().top,cards:document.querySelectorAll('#all .card').length,images:[...document.images].map(i=>({complete:i.complete,width:i.getAttribute('width'),height:i.getAttribute('height')}))})''')
   assert row['cards']==11 and all(i['complete'] and i['width'] and i['height'] for i in row['images'])
   assert not c.cookies();row.update(width=width,repeat=repeat);rows.append(row);c.close()
 b.close()
out=R/'.review/anchor-cold.json';out.write_text(json.dumps({'base':BASE,'runs':rows,'passed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Cold contexts:',len(rows),'PASS; maximum absolute list top:',max(abs(r['top']) for r in rows))
