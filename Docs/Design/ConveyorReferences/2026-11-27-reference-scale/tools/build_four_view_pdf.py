"""PDF page layout with exact source image excerpts. No source PNG edits."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json,hashlib
P=Path(__file__).resolve().parents[1]
out=P/'presentation'
out.mkdir(exist_ok=True)
r8=P/'attempts/06-conveyor-views-r8.png'
r9=P/'attempts/06-conveyor-left-panel-r9.png'
pdf=out/'06-conveyor-four-view-reference.pdf'
pdfmetrics.registerFont(TTFont('HavenlineSans','/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('HavenlineSansBold','/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
c=canvas.Canvas(str(pdf),pagesize=(1536,1200),pageCompression=1,invariant=1)
c.setTitle('Havenline - Conveyor Four-View Reference')
c.setAuthor('Havenline art continuation')
c.setFillColor(HexColor('#101e32'));c.rect(0,0,1536,1200,fill=1,stroke=0)
c.setFillColor(HexColor('#f4f7fb'));c.setFont('HavenlineSansBold',25)
c.drawString(22,1150,'HAVENLINE / CONVEYOR - FOUR VIEWS')
c.setFillColor(HexColor('#b8c9dd'));c.setFont('HavenlineSans',16)
c.drawRightString(1514,1153,'Selected proportions | Static reference study')
# Draw the same full source behind each scoped page viewport. The wrong
# superseded left source panel is never part of the selected page viewport.
for box in [(0,588,768,536),(768,588,768,536),(768,100,768,488)]:
 c.saveState();p=c.beginPath();p.rect(*box);c.clipPath(p,stroke=0,fill=0)
 c.drawImage(str(r8),0,100,width=1536,height=1024,mask='auto')
 c.restoreState()
c.setFillColor(HexColor('#f8b89a'));c.rect(0,100,768,488,fill=1,stroke=0)
height=998*768/1576
c.drawImage(str(r9),0,100+(488-height)/2,width=768,height=height,mask='auto')
c.setFillColor(HexColor('#c9d4e2'));c.setFont('HavenlineSans',14)
c.drawString(22,72,'Source preservation: front, rear and right are unaltered panel excerpts from R8. The corrected left view is the separately generated R9 panel.')
c.drawString(22,48,'R8\'s superseded left panel and the failed R10 composite remain archived. Thirteen rollers are the authored cross-view consistency target.')
c.drawString(22,24,'This static reference sheet does not establish native geometry, movement, collision or in-game inventory behavior.')
c.showPage();c.save()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta={'schema_version':1,'format':'PDF document layout','source_raster_edits':False,'pdf':{'path':str(pdf.relative_to(P)),'sha256':sha(pdf),'bytes':pdf.stat().st_size},'page_size_points':[1536,1200],'source_images':[{'path':str(r8.relative_to(P)),'sha256':sha(r8),'included_views':['front_three_quarter','rear_three_quarter','right_side'],'excluded_view':'superseded_left_side'},{'path':str(r9.relative_to(P)),'sha256':sha(r9),'included_view':'whole corrected left panel'}],'runtime_approved':False}
(out/'06-conveyor-four-view-pdf-source-map.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
