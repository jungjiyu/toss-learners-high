"""Reserve the existing Mogu guide's image space without changing its content."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET

def reserve(root):
 page=root/'mogu/index.html';original=page.read_bytes();text=original.decode('utf8')
 for name in ['before','after']:
  image=root/f'mogu/architecture/{name}.svg'
  box=ET.fromstring(image.read_bytes()).get('viewBox').split()
  w,h=map(float,box[2:]);pattern=rf'<img\b[^>]*src="architecture/{name}\.svg"[^>]*>'
  def replace(m):
   tag=re.sub(r'\s+(?:width|height)="[^"]*"','',m[0])
   return tag[:-1]+f' width="{round(w)}" height="{round(h)}">'
  text,n=re.subn(pattern,replace,text);assert n==1,(name,n)
 raw=text.encode('utf8');page.write_bytes(raw)
 manifest=root/'publication.json';m=json.loads(manifest.read_bytes())
 row=next(x for x in m['files'] if x['published_path']=='mogu/index.html')
 row['published_sha256']=hashlib.sha256(raw).hexdigest()
 row['publication_layout']='Intrinsic SVG dimensions reserve space for cold #articles navigation; text and image bytes unchanged.'
 manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

if __name__=='__main__':reserve(Path(__file__).resolve().parents[1])
