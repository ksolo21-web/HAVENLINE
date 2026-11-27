from pathlib import Path
from html import escape
import json, hashlib, subprocess, math
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'design'
OUT.mkdir(parents=True, exist_ok=True)
C = {'ink':'#183447','muted':'#536b78','food':'#008b83','utility':'#ad7425','manual':'#6f7d8a','ref':'#3769a3','bg':'#f5f8f8','line':'#ccd9de','white':'#ffffff'}

class Board:
    def __init__(self, w, h, title, subtitle):
        self.w,self.h=w,h
        self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(title)}</title>',f'<desc id="desc">{escape(subtitle)}</desc>', '<defs>']
        for k in ['food','utility','manual','ref','ink']:
            self.s.append(f'<marker id="arrow-{k}" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto-start-reverse" markerUnits="userSpaceOnUse"><path d="M1,1 L13,7 L1,13 Z" fill="{C[k]}"/></marker>')
        self.s += ['<pattern id="reserve" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="12" stroke="#d7e1e6" stroke-width="3"/></pattern></defs>', '<style>text{font-family:Inter,"DejaVu Sans",Arial,sans-serif} .title{font-weight:700} .smallcap{font-weight:700;letter-spacing:2px}</style>', f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>']
        self.text(60,58,'HAVENLINE / LOGISTICS',19,'muted',weight=700,spacing=2)
        self.text(60,118,title,44,weight=700)
        self.text(60,157,subtitle,20,'muted')
    def text(self,x,y,t,size=20,color='ink',weight=400,anchor='start',spacing=None):
        fill=C.get(color,color)
        self.s.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"'+(f' letter-spacing="{spacing}"' if spacing else '')+f'>{escape(str(t))}</text>')
    def lines(self,x,y,lines,size=18,color='muted',gap=25,weight=400):
        for i,t in enumerate(lines):self.text(x,y+i*gap,t,size,color,weight)
    def rect(self,x,y,w,h,fill='white',stroke='line',r=14,dash=None,sw=2):
        self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{C.get(fill,fill)}" stroke="{C.get(stroke,stroke)}" stroke-width="{sw}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def path(self,pts,color='food',width=5,dash=None,arrow=True,startarrow=False):
        d='M '+' L '.join(f'{x},{y}' for x,y in pts)
        self.s.append(f'<path d="{d}" fill="none" stroke="{C.get(color,color)}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'+(f' stroke-dasharray="{dash}"' if dash else '')+(f' marker-end="url(#arrow-{color})"' if arrow else '')+(f' marker-start="url(#arrow-{color})"' if startarrow else '')+'/>')
    def badge(self,x,y,t,color='ref'):
        w=16+len(t)*9
        self.rect(x,y,w,26,fill='#ecf2f8' if color=='ref' else '#edf2f3',stroke='none',r=6,sw=0)
        self.text(x+8,y+18,t,13,color,700)
    def node(self,x,y,w,h,title,lines=(),family='food',provisional=False,badge=None):
        self.rect(x,y,w,h,stroke=family,dash='8 6' if provisional else None)
        self.s.append(f'<rect x="{x}" y="{y+16}" width="5" height="{h-32}" rx="2" fill="{C[family]}"/>')
        available=w-36
        title_size=21
        while title_size>14 and ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',title_size).getlength(title)>available:
            title_size-=1
        self.text(x+18,y+32,title,title_size,weight=700)
        # Wrap to measured card width and fit the available vertical space without truncation.
        for body_size in range(17,13,-1):
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',body_size)
            wrapped=[]
            for line in lines:
                cur=''
                for word in line.split():
                    trial=(cur+' '+word).strip()
                    if cur and font.getlength(trial)>available:wrapped.append(cur);cur=word
                    else:cur=trial
                if cur:wrapped.append(cur)
            gap=body_size+6
            if not wrapped or 60+(len(wrapped)-1)*gap <= h-10:break
        assert not wrapped or 60+(len(wrapped)-1)*gap <= h-8, (title,wrapped,h)
        self.lines(x+18,y+60,wrapped,body_size,gap=gap)
        if badge:self.badge(x+w-16-len(badge)*9-16,y+14,badge)
    def label(self,x,y,t,color='muted',size=16,anchor='middle'):
        w=len(t)*size*.55+14
        rx=x-w/2 if anchor=='middle' else x-5
        self.rect(rx,y-size,w,size+8,fill='bg',stroke='none',r=4,sw=0)
        self.text(x,y,t,size,color,anchor=anchor)
    def circle(self,x,y,r,fill='white',stroke='line',sw=2):
        self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{C.get(fill,fill)}" stroke="{C.get(stroke,stroke)}" stroke-width="{sw}"/>')
    def write(self,name):
        p=OUT/name;p.write_text('\n'.join(self.s+['</svg>'])+'\n');return p

def flow():
    b=Board(2200,1850,'Connections that have a reason','D07.1 · Directed route specification · New hardware and control rules are proposals; recipe quantities remain unfrozen.')
    b.badge(60,190,'Source forms observed; ports proposed')
    b.badge(435,190,'Dashed card = provisional recipe or equipment','manual')
    b.text(1120,210,'FOOD',16,'food',700);b.text(1265,210,'UTILITY',16,'utility',700);b.text(1450,210,'MANUAL SERVICE',16,'manual',700)
    b.text(60,267,'01  FOOD · a destination owns every release',23,weight=700)
    b.node(60,300,250,120,'Shore intake',['Whole fish output','Source form observed'],'food')
    b.node(380,300,260,120,'Cooker / processor',['Raw input → cooked form','New side adapter proposed'],'food')
    b.node(710,300,230,120,'Finite output buffer',['Reserve a free slot','before processing'],'food')
    b.node(1010,300,230,120,'Demand router',['Allowed SKU + request','One destination per item'],'food')
    b.node(1510,300,230,120,'Gated merge',['Fresh OR stored stock','One owner / stock slot'],'food')
    b.node(1810,300,330,120,'Allowed food counter',['Belt ends at staff-side buffer','Staff lifts stock onto timber table','Cash / frontage stay separate'],'food')
    for a,z in [(310,380),(640,710),(940,1010),(1240,1510),(1740,1810)]:b.path([(a,360),(z,360)])
    b.label(345,445,'supported adapter',size=15)
    b.label(1375,337,'fresh, allowed SKU','food')
    b.label(1775,445,'restock','food',15)
    b.text(60,485,'Reference fish path is observed; the port geometry, buffers and reservation logic are new design.',18,'muted')

    # Surplus receiving and independently requested dispatch. The stock node is not a through-belt.
    b.rect(1240,585,900,315,fill='#eaf5f2',stroke='#bfded7',r=20)
    b.text(1270,625,'PREPARED-FOOD STORAGE · REAR CASSETTE',20,'food',700)
    b.node(1270,665,200,120,'Reserved IN',['Admit only when a','typed slot is available'],'food')
    b.node(1510,665,245,120,'Local food inventory',['Tray / shuttle serves bay','Stock remains here'],'food')
    b.node(1800,665,310,120,'Request-controlled OUT',['Dispatch chosen, compatible SKU','Only against an open reservation'],'food')
    b.path([(1170,420),(1170,520),(1210,520),(1210,725),(1270,725)])
    b.label(1210,554,'surplus only','food',15)
    b.path([(1470,725),(1510,725)])
    b.path([(1755,725),(1800,725)])
    b.path([(1955,665),(1955,525),(1625,525),(1625,420)])
    b.label(1790,505,'counter request + reserved stock','food',16)
    b.lines(1270,832,['Independent IN and OUT trays; no belt through the central storage aisle.','There is no automatic OUT → IN return route.'],18,'food',gap=28)

    # Optional multi-input branch is topology-supported, while recipe eligibility stays provisional.
    b.text(60,620,'OPTIONAL ASSEMBLY · separate ingredient ports',21,weight=700)
    b.node(60,700,270,130,'Wheat processing chain',['Harvest + processor observed','No flour stage inferred'],'food')
    b.node(390,700,180,130,'Bread-like form',['Output appearance','Recipe unfrozen'],'food',True)
    b.node(650,700,280,130,'Optional assembler *',['A: bread-like input','B: compatible cooked input'],'food',True)
    b.node(990,700,200,130,'Own menu counter *',['Accepts the assembled','item only if allowed'],'food',True)
    b.path([(330,765),(390,765)])
    b.path([(570,765),(650,765)])
    b.path([(930,765),(990,765)])
    b.path([(1070,420),(1070,560),(800,560),(800,700)],dash='9 6')
    b.label(902,541,'optional recipe mode *','food',16)
    b.badge(616,746,'A');b.badge(810,664,'B')
    b.lines(60,885,['* A56.5–59s supports the dual-feeder topology and a direct service output.','Ingredient eligibility, exact product identity, ratios, fuel and timing are not frozen.','Cycle start: reserve both accepted ingredients and output space together; otherwise WAIT.'],18,'muted',gap=27)

    b.path([(60,1000),(2140,1000)],color='manual',width=1,arrow=False)
    b.text(60,1047,'02  UTILITY · typed local storage, no food or fuel on this lane',23,weight=700)
    b.node(60,1100,280,120,'Timber / saw variant *',['Logs unchanged; planks provisional','Machines are alternatives'],'utility',True)
    b.node(60,1270,280,100,'Quarry / extraction',['Raw stone / ore; form preserved'],'utility')
    b.node(420,1100,250,170,'Typed feeder buffer',['Separate held source queues','One class / selected batch','Wrong item stays at source'],'utility')
    b.node(750,1125,250,120,'Utility cassette IN',['Select timber OR minerals','Reserved local receiving tray'],'utility')
    b.node(1075,1125,285,120,'Indexed local inventory',['Bounded timber / mineral slots','No mixed pile or hidden sorting'],'utility')
    b.node(1440,1125,245,120,'Utility cassette OUT',['Chosen item + request','Independent dispatch tray'],'utility')
    b.node(1770,1125,370,155,'Permitted endpoint *',['Compatible workstation socket, or','explicitly allowed log / material counter','Unknown recipes remain disabled'],'utility',True)
    b.path([(340,1160),(420,1160)],color='utility')
    b.path([(340,1320),(380,1320),(380,1230),(420,1230)],color='utility')
    b.path([(670,1185),(750,1185)],color='utility')
    b.path([(1000,1185),(1075,1185)],color='utility')
    b.path([(1360,1185),(1440,1185)],color='utility')
    b.path([(1685,1185),(1770,1185)],color='utility')
    b.lines(750,1325,['No ore → ingot claim. No workshop parts, greenhouse yields or new recipe quantities are inferred.','A disabled future socket is a reserved interface, not an operating production line.'],18,'muted',gap=28)

    b.rect(60,1450,1110,235,fill='#edf1f5',stroke='#ced7df',r=18)
    b.text(85,1490,'03  MANUAL FUEL / WARMTH',21,'manual',700)
    b.node(85,1520,365,115,'Original fuel-service handoff',['Dedicated right-side hatch','Fuel route remains manual'],'manual')
    b.node(600,1520,525,115,'Central warming furnace',['Warmth / upgrade state, not a processed item','Not a smelter; receives no food conveyor'],'manual')
    b.path([(450,1575),(600,1575)],color='manual',dash='6 7')
    b.label(525,1550,'staff carry','manual',16)
    b.rect(1210,1450,930,235,fill='#edf1f5',stroke='#ced7df',r=18)
    b.text(1235,1490,'MANUAL / NOT YET ELIGIBLE FOR BELTS',21,'manual',700)
    b.lines(1235,1535,['Raw-food storage / raw sales: manual + explicit catalogue','Hides / fur · cargo / cash · butcher tables · drying racks','Cookfire / cookhouse · chopping fixtures · crates / sled handoffs','Workshop / greenhouse outputs unspecified; no active recipe route.'],19,'manual',gap=31)
    b.rect(60,1730,2080,72,fill='ink',stroke='none',r=14)
    b.text(85,1775,'FULL / WRONG ITEM: hold → stop upstream release. No deletion, duplication, mixed universal loop or unbounded queue.',22,'white',700)
    return b.write('D07-01-directed-routing.svg')

def camp():
    b=Board(2200,1450,'A compact camp that stays walkable','D07.2 · Conceptual top-down allocation · No world-scale, collision, structural clearance or runtime-fit approval is implied.')
    # Spatial plan has deliberately clear perimeter working areas and a continuous two-gate corridor.
    b.rect(70,220,1540,1020,fill='#eef4f2',stroke='none',r=18)
    b.circle(840,730,105,fill='#f2e3ca',stroke='#dec5a0',sw=2)
    # Continuous fence with explicit gate and service-counter openings.
    for pts in [[(70,900),(70,220),(1610,220),(1610,580)],[(1610,800),(1610,900)],[(1610,1010),(1610,1240),(70,1240),(70,1010)]]:
        b.path(pts,color='manual',width=11,arrow=False)
    b.text(95,253,'CAMP FENCE · no exterior painted road',17,'manual',700)
    b.rect(80,900,1520,110,fill='#dce8ef',stroke='none',r=10)
    b.text(840,942,'CONTINUOUS CLEAR WALK ZONE',21,'ref',700,anchor='middle')
    b.text(840,975,'both directions · belts stay outside this corridor',18,'ref',anchor='middle')
    b.path([(15,955),(300,955)],color='ref',width=4,startarrow=True)
    b.path([(1390,955),(1695,955)],color='ref',width=4,startarrow=True)
    b.label(180,1045,'GATE A · open both ways','ref',18)
    b.label(1485,1045,'GATE B · open both ways','ref',18)

    # Perimeter storage service zones. These are reserved empty areas, not belt lanes.
    b.rect(100,278,65,622,fill='#e1ebf0',stroke='none',r=7)
    b.rect(165,278,290,65,fill='#e1ebf0',stroke='none',r=7)
    b.rect(165,545,120,65,fill='#e1ebf0',stroke='none',r=7)
    b.s.append('<text x="138" y="720" transform="rotate(-90 138 720)" font-family="Inter,DejaVu Sans" font-size="15" font-weight="700" fill="#3769a3" text-anchor="middle">CONTINUOUS SERVICE ACCESS</text>')
    b.rect(455,278,360,65,fill='#e1ebf0',stroke='#bed0db',r=8,dash='6 5')
    b.text(635,306,'REAR SERVICE AISLE',17,'ref',700,anchor='middle')
    b.text(635,330,'clear above the paired food cassette',15,'ref',anchor='middle')
    b.rect(285,485,50,170,fill='#e1ebf0',stroke='#bed0db',r=7,dash='6 5')
    b.s.append('<text x="313" y="570" transform="rotate(-90 313 570)" font-family="Inter,DejaVu Sans" font-size="15" font-weight="700" fill="#3769a3" text-anchor="middle">LEFT SERVICE AISLE</text>')
    b.rect(460,720,290,125,fill='#e1ebf0',stroke='#bed0db',r=10,dash='6 5')
    b.text(605,768,'FRONT APRON',21,'ref',700,anchor='middle')
    b.text(605,797,'doors / access stay clear',17,'ref',anchor='middle')
    b.rect(570,845,75,55,fill='#e1ebf0',stroke='none',r=5)

    # Storage floorplate and original service areas.
    b.rect(420,410,350,300,fill='#fcf6ec',stroke='#9a7856',r=12,sw=4)
    b.text(635,265,'STORAGE HOUSE',22,'ink',700,anchor='middle')
    b.rect(470,515,75,62,fill='#f0e2c7',stroke='utility',r=6)
    b.text(507,540,'TIMBER',12,'utility',700,anchor='middle');b.text(507,561,'local tray',11,'utility',anchor='middle')
    b.rect(470,590,75,62,fill='#e7e0d4',stroke='utility',r=6)
    b.text(507,615,'MINERAL',11,'utility',700,anchor='middle');b.text(507,636,'local tray',11,'utility',anchor='middle')
    b.rect(530,465,210,43,fill='#d7eee6',stroke='food',r=6)
    b.text(635,493,'PREPARED-FOOD BAY',14,'food',700,anchor='middle')
    b.rect(575,525,50,174,fill='#ffffff',stroke='#d9d1c3',r=3)
    b.text(600,564,'CLEAR',10,'muted',700,anchor='middle');b.text(600,585,'AISLE',10,'muted',700,anchor='middle')
    b.rect(640,535,100,115,fill='#f0ebe4',stroke='#ad9d88',r=6)
    b.lines(650,558,['MANUAL','raw food','hides / cargo'],12,'manual',gap=23)
    # Paired cassettes occupy real illustrated footprint outside two different walls.
    b.rect(350,460,70,180,fill='#ecd8b2',stroke='utility',r=8,sw=3)
    b.text(385,485,'UTILITY',12,'utility',700,anchor='middle')
    b.text(385,531,'IN →',15,'utility',700,anchor='middle')
    b.text(385,603,'← OUT',14,'utility',700,anchor='middle')
    # Separate local selector networks. Either tray can receive and either can dispatch.
    b.path([(385,460),(385,500),(440,500)],color='utility',width=3,arrow=False)
    b.path([(440,500),(440,530),(470,530)],color='utility',width=3)
    b.path([(440,530),(440,605),(470,605)],color='utility',width=3)
    b.circle(440,500,5,fill='utility',stroke='utility',sw=1)
    b.path([(545,560),(560,560),(560,675)],color='utility',width=3,arrow=False)
    b.path([(545,635),(560,635)],color='utility',width=3,arrow=False)
    b.path([(560,675),(430,675),(430,630),(385,630)],color='utility',width=3)
    b.path([(385,630),(385,640)],color='utility',width=3,arrow=False)
    b.circle(560,635,5,fill='utility',stroke='utility',sw=1)
    b.text(480,697,'indexed class selection',10,'utility',700,anchor='middle')
    b.rect(490,350,260,60,fill='#cce8de',stroke='food',r=8,sw=3)
    b.text(505,374,'FOOD IN',14,'food',700);b.text(505,399,'FOOD OUT',14,'food',700)
    b.path([(620,410),(620,465)],color='food',width=3)
    b.path([(680,465),(680,410)],color='food',width=3)
    # Existing window / vent / hatch are named as retained; no feeder replaces them.
    b.path([(420,432),(420,450)],color='ref',width=7,arrow=False)
    b.rect(770,578,24,55,fill='#e3ccb1',stroke='#9a7856',r=3)
    b.text(780,662,'fuel hatch',14,'manual',anchor='middle')
    b.path([(550,710),(625,710)],color='ref',width=9,arrow=False)
    b.text(588,737,'original front doors',12,'ref',anchor='middle')

    # Utility service remains on the left perimeter, with one typed feeding batch.
    b.node(195,345,125,125,'Utility feed',['Crates','One class','Saw option'],'utility',True)
    b.path([(320,395),(385,395),(385,460)],color='utility')
    b.node(185,735,135,100,'Endpoint *',['Allowed input','or catalogue'],'utility',True)
    b.path([(385,640),(385,690),(252,690),(252,735)],color='utility')
    b.label(280,863,'* typed input / catalogue required','utility',13)

    # Food chain and storage branch. The only junction between fresh/stored output is explicitly gated.
    b.node(1410,330,140,100,'Intake',['Whole fish'],'food')
    b.node(1170,330,200,100,'Cooker',['Side IN / cooked OUT'],'food')
    b.path([(1410,380),(1370,380)])
    b.rect(1040,350,80,70,fill='white',stroke='food',r=10)
    b.text(1080,378,'ROUTE',14,'food',700,anchor='middle');b.text(1080,400,'GATE',14,'food',700,anchor='middle')
    b.path([(1170,380),(1120,380)])
    b.path([(1040,385),(880,385),(880,370),(750,370)])
    b.label(880,349,'surplus → reserved IN','food',15)
    b.path([(750,395),(900,395),(900,550),(1040,550)])
    b.label(900,476,'request-only OUT','food',15)
    b.rect(1040,525,80,55,fill='white',stroke='food',r=8)
    b.text(1080,549,'GATED',13,'food',700,anchor='middle');b.text(1080,568,'MERGE',13,'food',700,anchor='middle')
    b.path([(1080,420),(1080,525)])
    b.label(1155,480,'fresh stock','food',15)
    b.path([(1120,550),(1400,550),(1400,610),(1440,610)])
    b.node(1130,650,230,110,'Optional assembly *',['Separate A / B feeders','Reserved future pad'],'food',True)
    b.text(1130,788,'Full multi-input route: D07.1',15,'muted')
    # Canonical counter remains a distinct table footprint; stock and cash are separate.
    b.rect(1530,580,80,220,fill='#a77d54',stroke='#755431',r=8,sw=3)
    b.rect(1440,580,90,60,fill='#d5ebe3',stroke='food',r=8,sw=3)
    b.text(1485,605,'STOCK',13,'food',700,anchor='middle');b.text(1485,625,'BUFFER',12,'food',700,anchor='middle')
    b.path([(1530,610),(1565,610)],color='manual',width=3,dash='4 5')
    b.label(1530,565,'staff lift','manual',14)
    b.rect(1545,728,40,42,fill='#e9dca6',stroke='#8f7d46',r=5)
    b.text(1558,699,'REGISTER',12,'ink',700,anchor='middle')
    b.path([(1545,748),(1502,748)],color='manual',width=3)
    b.rect(1410,674,90,106,fill='#e1ebf0',stroke='#bed0db',r=8,dash='6 5')
    b.text(1455,712,'STAFF',14,'ref',700,anchor='middle');b.text(1455,736,'+ cash',14,'manual',anchor='middle')
    b.rect(1410,780,90,120,fill='#e1ebf0',stroke='none',r=8)
    b.text(1570,832,'customer face →',16,'muted',anchor='middle')
    for cy in [615,680,745]:
        b.circle(1660,cy,18,fill='#d4e2ee',stroke='ref');b.path([(1645,cy+28),(1675,cy+28)],color='ref',width=3,arrow=False)
    b.text(1660,575,'QUEUE',15,'ref',700,anchor='middle')
    b.text(1660,806,'outside fence',14,'muted',anchor='middle')

    # Warmth remains at geometric camp centre; fuel delivery is a manual path.
    b.circle(840,730,70,fill='#bc6b33',stroke='#89451f',sw=4)
    b.text(840,720,'CENTRAL',20,'white',700,anchor='middle');b.text(840,750,'HEATER',20,'white',700,anchor='middle')
    b.text(840,887,'warmth access stays open',17,'manual',anchor='middle')
    b.path([(794,605),(840,605),(840,660)],color='manual',width=4,dash='6 7')
    b.label(865,590,'manual fuel','manual',15)
    # Manual work zones sit south of the gate corridor and have no invented active conveyor line.
    b.node(140,1090,380,100,'Manual preparation',['Racks / butcher / cookfire fixtures'],'manual')
    b.node(620,1090,350,100,'Manual logistics',['Cargo / hides / crates / sled handoff'],'manual')
    b.node(1080,1090,400,100,'Reserved future work area',['Workshop / greenhouse: output undefined'],'manual',True)

    # Side key: concise, reviewable spatial constraints, not a third flow network.
    b.rect(1760,220,370,1020,fill='white',stroke='line',r=18)
    b.text(1785,265,'HOW TO READ',22,weight=700)
    b.lines(1785,305,['Teal: prepared-food routing','Ochre: utility material routing','Gray dashed: manual staff handoff','Blue areas: reserved walk / service'],16,'muted',gap=29)
    b.text(1785,460,'FIXED DESIGN INTENT',20,weight=700)
    b.lines(1785,500,['01  Rear food tray / shuttle','      original high vent retained','02  Left utility cassette / lift','      select timber OR mineral','      original high window retained','03  Original front doors clear','04  Original right fuel hatch','      manual handoff retained','05  Heater at camp centre','06  Two bidirectional gates'],16,'muted',gap=29)
    b.text(1785,810,'NO UNIVERSAL LOOP',20,'food',700)
    b.lines(1785,850,['Stored stock leaves only against','a compatible destination request.','Fresh and stored items join at','one gated merge before the buffer.'],16,'muted',gap=29)
    b.text(1785,1020,'PROVISIONAL',20,weight=700)
    b.lines(1785,1060,['Exact dimensions and capacity','are not assigned by this drawing.','Dashed machine pads remain','disabled until their typed recipe','or endpoint catalogue is defined.'],16,'muted',gap=29)
    b.text(60,1320,'Source topology: original A / equipment coverage. New dispatch and buffer logic: proposed, informed by first-party references.',18,'muted')
    b.text(60,1352,'This plan reserves space; final footprints, movement and collision require a later runtime layout check.',18,'muted')
    b.text(60,1400,'D07 · Editable SVG + typed routing catalogue · Root requirements R03–R11',17,'muted')
    return b.write('D07-02-camp-allocation.svg')

def port(id,direction,family,forms,method='belt'):
    return {'id':id,'direction':direction,'carrier_family':family,'accepted_item_forms':forms,'transfer_method':method}

def catalogue():
    coverage=json.loads((ROOT/'sources/docs/source-equipment-coverage.json').read_text())
    stations=[]
    def st(id,name,group,disp,ports=(),note='',sources=()):
        stations.append({'id':id,'name':name,'equipment_families':group,'disposition':disp,'ports':list(ports),'boundary':note,'evidence_refs':list(sources)})
    st('fishing-rack','Fishing rods / rack',['fish-line'],'manual_acquisition',[port('handoff','out','raw_food',['whole fish'],'staff_carry')],'Manual acquisition is an earlier/alternate phase, replaced by mechanized intake in the reference; no demonstrated serial rod-to-intake feed or species conversion',['locked-video-chain','station-kit'])
    st('shore-intake','Shore intake machinery',['fish-line'],'proposed_conveyor_connection',[port('load','in','raw_food',['whole fish'],'staff_or_intake'),port('out','out','raw_food',['whole fish'])],'Front discharge and new cooker side adapter; raw fish form observed. A manual loading port is a new proposal, not an observed serial fishing-rack input.',['locked-video-chain','video-A-016'])
    st('cooker','Cooker / processor',['fish-line','meat-processor'],'typed_recipe_variant_required',[port('raw-in','in','raw_food',['whole fish','raw meat portions (separate selected variant)']),port('cooked-out','out','prepared_food',['cooked whole-fish-shaped item','processed meat portion (separate selected variant)'])],'Observed visual associations; exact recipes, species, fuel and rates unfrozen',['locked-video-chain','cooker-visible-crops','board-18567'])
    st('food-output-buffer','Finite cooked-output buffer',['fish-line'],'new_proposal',[port('in','in','prepared_food',['selected compatible prepared-food form']),port('out','out','prepared_food',['same selected form'])],'Reserve output slot before processing starts',['DESIGN_CHECKPOINT','NEW-V01','NEW-V02'])
    st('food-router','Demand router / release gate',['fish-line'],'new_proposal',[port('in','in','prepared_food',['selected compatible prepared-food form']),port('fresh-out','out','prepared_food',['active counter allowed form']),port('surplus-out','out','prepared_food',['storage allowed prepared-food form']),port('assembly-out','out','prepared_food',['assembler accepted cooked form; unfrozen'])],'Every item has one destination; optional assembly mode does not copy the stream',['DESIGN_CHECKPOINT','NEW-D01'])
    st('food-storage-in','Rear prepared-food receiving cassette',['logistics'],'new_proposal',[port('in','in','prepared_food',['selected allowed prepared-food form']),port('local-deposit','out','prepared_food',['same form'],'local_horizontal_tray_shuttle')],'Separate finite receiving tray at prepared-food shelf height; short horizontal shuttle serves this bay; compatible inventory slot reserved',['DESIGN_CHECKPOINT'])
    st('food-inventory','Local prepared-food inventory bay',['logistics'],'new_proposal',[port('receive','in','prepared_food',['allowed prepared-food form'],'local_horizontal_tray_shuttle'),port('release','out','prepared_food',['requested allowed prepared-food form'],'local_horizontal_tray_shuttle')],'Prepared-food shelf is above closed raw-food cabinets; stock is retained until requested; no automatic recirculation',['DESIGN_CHECKPOINT'])
    st('food-storage-out','Rear prepared-food dispatch cassette',['logistics'],'new_proposal',[port('load','in','prepared_food',['requested allowed prepared-food form'],'local_horizontal_tray_shuttle'),port('out','out','prepared_food',['same requested form'])],'Independent dispatch tray/shuttle serves this shelf-height local bay; no crossing central aisle',['DESIGN_CHECKPOINT','NEW-V04'])
    st('food-merge','Gated fresh / stored merge',['logistics'],'new_proposal',[port('fresh-in','in','prepared_food',['counter allowed form']),port('stored-in','in','prepared_food',['counter allowed form']),port('out','out','prepared_food',['same form'])],'One source owns each reserved counter slot; one item released at a time',['DESIGN_CHECKPOINT'])
    st('food-counter','Canonical customer counter + new stock-end buffer',['fish-line','logistics'],'allowed_catalogue_required',[port('stock-in','in','prepared_food',['explicit active menu catalogue']),port('service','out','prepared_food',['same stocked form'],'staff_lift_then_customer_handoff'),port('cash','out','cash',['credits / cash representation'],'staff_collection')],'Belt ends at separate dead-end staff buffer; staff lift stock onto original timber table. Goods/cash routes separate; register, shelf, legs and customer frontage preserved',['locked-video-chain','runtime-customers','DESIGN_CHECKPOINT'])
    st('wheat-harvester','Wheat patch / mechanized harvester',['wheat-food-line'],'reference_topology_recipe_unfrozen',[port('out','out','plant_food',['wheat'],'unspecified_reference_transfer')],'T19 freeze required; no flour intermediate inferred',['locked-video-chain','resource-registry'])
    st('wheat-processor','Blue / orange food processor',['wheat-food-line'],'reference_topology_recipe_unfrozen',[port('in','in','plant_food',['wheat'],'unspecified_reference_transfer'),port('out','out','prepared_food',['bread-like cooked-food stack'])],'Input/output visual chain observed; hidden stages and recipe undefined',['locked-video-chain'])
    st('optional-assembler','Proposed dual-input assembly station',[],'disabled_until_recipe_catalogue_defined',[port('ingredient-a','in','prepared_food',['bread-like form if recipe accepts it']),port('ingredient-b','in','prepared_food',['compatible cooked form if recipe accepts it']),port('out','out','prepared_food',['assembled menu item; identity unfrozen'])],'Topology observed A56.5–59s; separate magazines; no fixed ratios or hidden ingredients. Joint input/output reservation is a cycle-start condition; completed stock dispatch is independent of consumed input availability.',['A56.5-59s','critic-reference-amendment-v1'])
    st('assembly-counter','Future allowed-menu assembly counter',[],'disabled_until_menu_catalogue_defined',[port('stock-in','in','prepared_food',['assembled menu item explicitly allowed']),port('service','out','prepared_food',['same form'],'customer_handoff')],'Direct output to service topology observed; Havenline geometry proposed',['A57-58.25s'])
    st('saw-variant','Saw station / lumber mill / steam saw',['saw-lumber'],'alternative_variants_recipe_unfrozen',[port('manual-load','in','utility_timber',['timber / logs'],'staff_load'),port('proposed-out','out','utility_timber',['planks only if pairing approved'])],'Alternatives, not serial mandatory machines; PLANK noun does not establish a recipe',['board-18607','board-18609','world-atlas'])
    st('quarry','Mining nodes / quarry drill',['stone-slate-quarry'],'typed_crate_feeder_proposed',[port('acquired','out','utility_mineral',['raw stone','raw metal ore'],'crate_handoff')],'Extraction preserves identity; no cut stone, bricks or smelting inferred',['runtime-kinds','resource-registry','board-18609'])
    st('utility-feeder','Typed utility buffer / feeder',['logistics'],'new_proposal',[port('timber-in','in','utility_timber',['logs','approved plank form'],'source_held_queue'),port('mineral-in','in','utility_mineral',['raw stone','raw metal ore'],'source_held_queue'),port('out','out','selected_utility_class',['one selected timber or mineral form'])],'One class/batch at a time; wrong item held at source; no mixed pile',['DESIGN_CHECKPOINT'])
    st('utility-storage-in','Left utility receiving cassette',['logistics'],'new_proposal',[port('in','in','selected_utility_class',['selected timber / mineral form']),port('local-deposit','out','selected_utility_class',['same selected form'],'indexed_local_tray')],'Timber and mineral compartments separately indexed by the low utility cassette tray/lift',['DESIGN_CHECKPOINT'])
    st('utility-inventory','Local indexed utility inventory',['logistics'],'new_proposal',[port('receive','in','selected_utility_class',['selected timber / mineral form'],'indexed_local_tray'),port('release','out','selected_utility_class',['requested timber / mineral form'],'indexed_local_tray')],'Bounded per-class local slots. No food, hides, raw meat, fuel or cash',['DESIGN_CHECKPOINT'])
    st('utility-storage-out','Left utility dispatch cassette',['logistics'],'new_proposal',[port('load','in','selected_utility_class',['requested timber / mineral form'],'indexed_local_tray'),port('out','out','selected_utility_class',['same requested form'])],'Dispatch consumes an explicit request and stock reservation',['DESIGN_CHECKPOINT'])
    st('reserved-workstation','Reserved compatible workstation socket',['workshop'],'disabled_until_input_catalogue_defined',[port('reserved-in','in','selected_utility_class',[])],'No active conversion shown; outputs unspecified',['board-18600','board-18607','DESIGN_CHECKPOINT'])
    st('material-counter','Explicitly permitted log / material counter',['logistics'],'allowed_catalogue_required',[port('stock-in','in','selected_utility_class',['logs or material specifically listed in active catalogue']),port('service','out','selected_utility_class',['same form'],'customer_handoff')],'Raw resources can be sold if listed; not automatically every raw or prepared form',['runtime-customers','DESIGN_CHECKPOINT'])
    st('fuel-hatch','Original right fuel-service hatch',['furnace-hearth','logistics'],'manual_only',[port('handoff','out','fuel',['approved fuel resource'],'staff_carry')],'Fuel excluded from first conveyor upgrade',['DESIGN_CHECKPOINT'])
    st('heater','Central furnace / hearth vessel',['furnace-hearth'],'manual_warmth_service',[port('service','in','fuel',['approved fuel resource'],'staff_carry')],'Produces warmth/state changes, not smelted inventory. Wood/stone/metal upgrade debits are not transformation recipes',['runtime-kinds','runtime-transfers'])
    st('processing-counter','Processing counter',['fish-line'],'manual_fixture_until_adapter_defined',[],'Stock/preparation surface; no independent conversion inferred',['station-kit','station-scope'])
    st('cookfire-house','Cookfire / cookhouse',['cookfire-cookhouse'],'manual_only_recipe_unfrozen',[],'Depicted cooking equipment; generic species eligibility/fuel/recipes undefined',['board-18607','board-18609'])
    st('drying-racks','Meat / fish drying racks',['drying-racks'],'manual_only_recipe_unfrozen',[],'Hung contents observed; duration/yield/inventory transition not established',['board-18600','board-18603'])
    st('chopping','Chopping stump / station',['chopping'],'manual_only',[],'Split-firewood visual state does not establish separate inventory kind',['board-18607','board-18600'])
    st('butcher-prep','Butcher table / animal harvest preparation',['animal-harvest-prep'],'manual_only_recipe_unfrozen',[],'No species drop/edibility/tanning list; companions excluded from harvest assumptions',['board-18607','world-atlas'])
    st('greenhouse','Greenhouse',['greenhouse'],'manual_or_future_unspecified',[],'No established crop/output catalogue; no active belt endpoint',['board-18609'])
    st('workshop','Workshop / equipment supply',['workshop'],'manual_or_future_unspecified',[],'No nails, rods, gears, ammunition or weapon crafting recipe is inferred',['board-18600','board-18607'])
    st('storage-crates','Stockpile / storage crates',['logistics'],'manual_handoff',[port('timber-handoff','out','utility_timber',['raw logs'],'staff_carry'),port('raw-food-handoff','out','raw_food',['raw meat only if explicit sales catalogue permits'],'staff_carry')],'Stores same goods; no conversion. Raw-food, hides, fuel, cargo and cash remain dedicated manual zones',['board-18607','DESIGN_CHECKPOINT'])
    st('manual-raw-sales','Catalogue-gated raw-sales counter mode',['logistics'],'manual_only_explicit_catalogue',[port('manual-stock','in','raw_food',['raw meat only if explicitly listed'],'staff_carry')],'Separate allowed stock area / active menu mode; no raw food on prepared-food storage belts',['DESIGN_CHECKPOINT','runtime-customers'])
    st('cash-collection','Staff cash collection area',['logistics'],'manual_only',[port('collect','in','cash',['credits / cash representation'],'staff_collection')],'Separate from product conveyor and customer queue',['A58.5-59s','DESIGN_CHECKPOINT'])
    st('fishing-winch','Fishing winch',['logistics'],'manual_or_mechanical_acquisition',[],'Transport/acquisition aid; no output transformation inferred',['board-18607'])
    st('sled-hauler','Sled hauler',['logistics'],'manual_or_helper_transport',[],'Moves same resource form; no conveyor or processing recipe inferred',['board-18607'])
    st('steel-oil-unassigned','Unassigned steel / oil conversion equipment',['steel-oil'],'no_supported_machine_or_recipe',[],'No smelter, refinery or charcoal line inferred from requested material concepts',['prior-user-request','world-atlas'])
    next(s for s in stations if s['id']=='optional-assembler')['cycle_rules']={'start':'Both accepted ingredients are present/reserved and one compatible completed-output buffer slot is reserved. Consume the accepted pair once when the recipe cycle commits.','complete':'Create the configured recipe output in the already reserved finite output buffer; quantities remain undefined until recipe freeze.','dispatch':'Release the completed item only against its own compatible counter reservation. Do not require already consumed ingredient stock to remain available.'}
    routes=[]
    def rt(id,src,sp,dst,dp,form,kind='belt',status='proposed_connection',when='compatible destination slot reserved',evidence=()):
        routes.append({'id':id,'source':{'station':src,'port':sp},'destination':{'station':dst,'port':dp},'direction':'source_to_destination','item_form':form,'transport':kind,'status':status,'release_condition':when,'on_full':'hold at source / finite queue; stop upstream release','on_wrong_item':'source-held reject; never reroute into an incompatible destination','evidence_refs':list(evidence)})
    rt('R-F01','fishing-rack','handoff','shore-intake','load','whole fish','staff_or_intake','new_manual_loading_proposal',when='optional manual loading task selected; intake slot available; not a required serial acquisition phase',evidence=['DESIGN_CHECKPOINT'])
    rt('R-F02','shore-intake','out','cooker','raw-in','whole fish',evidence=['locked-video-chain','DESIGN_CHECKPOINT'])
    rt('R-F03','cooker','cooked-out','food-output-buffer','in','selected compatible cooked item',evidence=['locked-video-chain','DESIGN_CHECKPOINT'])
    rt('R-F04','food-output-buffer','out','food-router','in','same cooked item')
    rt('R-F05','food-router','fresh-out','food-merge','fresh-in','active counter allowed prepared item',when='fresh lane selected; active menu match; merge owns counter stock reservation')
    rt('R-F06','food-router','surplus-out','food-storage-in','in','storage allowed prepared item',when='surplus mode selected; specific prepared-food inventory slot reserved')
    rt('R-F07','food-storage-in','local-deposit','food-inventory','receive','same prepared item','local_horizontal_tray_shuttle')
    rt('R-F08','food-inventory','release','food-storage-out','load','requested prepared item','local_horizontal_tray_shuttle',when='explicit counter request AND stock reservation AND merge reservation')
    rt('R-F09','food-storage-out','out','food-merge','stored-in','same requested prepared item',when='stored source selected; exclusive ownership of counter slot')
    rt('R-F10','food-merge','out','food-counter','stock-in','active counter allowed prepared item',when='one source gate open; source and destination agree on item ownership')
    rt('R-A01','wheat-harvester','out','wheat-processor','in','wheat','unspecified_reference_transfer','reference_topology_recipe_unfrozen',evidence=['locked-video-chain'])
    rt('R-A02','wheat-processor','out','optional-assembler','ingredient-a','bread-like form','separate_belt','disabled_until_recipe_defined','recipe A accepts exact form; ingredient B and output also reserved',['A56.5-59s'])
    rt('R-A03','food-router','assembly-out','optional-assembler','ingredient-b','compatible cooked form; exact SKU unfrozen','separate_belt','disabled_until_recipe_defined','optional assembly mode; recipe B accepts exact form; ingredient A and output also reserved',['A56.5-59s'])
    rt('R-A04','optional-assembler','out','assembly-counter','stock-in','assembled menu item; identity unfrozen','belt','disabled_until_recipe_and_menu_defined','completed output exists; active menu accepts it; this item owns the counter destination reservation',['A57-58.25s'])
    rt('R-U00','storage-crates','timber-handoff','utility-feeder','timber-in','raw logs; form unchanged','staff_handoff','proposed_connection',evidence=['runtime-kinds','DESIGN_CHECKPOINT'])
    rt('R-U01','saw-variant','proposed-out','utility-feeder','timber-in','approved plank form; pairing provisional','source_queue','disabled_until_pairing_defined',evidence=['board-18607','world-atlas'])
    rt('R-U02','quarry','acquired','utility-feeder','mineral-in','raw stone / metal ore (identity retained)','typed_crate_handoff',evidence=['resource-registry','board-18609'])
    rt('R-U03','utility-feeder','out','utility-storage-in','in','one selected utility form',when='selected class and indexed receiving tray agree')
    rt('R-U04','utility-storage-in','local-deposit','utility-inventory','receive','same utility form','indexed_local_tray')
    rt('R-U05','utility-inventory','release','utility-storage-out','load','requested utility form','indexed_local_tray',when='explicit destination request; chosen class stock reserved')
    rt('R-U06','utility-storage-out','out','reserved-workstation','reserved-in','exact requested form not yet defined','belt','disabled_until_input_catalogue_defined','no release until compatible input catalogue is frozen')
    rt('R-U07','utility-storage-out','out','material-counter','stock-in','explicitly permitted log / material form','belt','catalogue_gated_proposal','counter explicitly allows this exact raw/material form and reserves stock space')
    rt('R-M01','fuel-hatch','handoff','heater','service','approved fuel resource','staff_carry','manual_only','manual fuel/service task valid; no food or utility conveyor connection',['runtime-transfers','DESIGN_CHECKPOINT'])
    rt('R-M02','storage-crates','raw-food-handoff','manual-raw-sales','manual-stock','raw meat only if explicitly listed','staff_carry','manual_only_catalogue_gated','exact raw item is in active sales catalogue; separate allowed stock area',['DESIGN_CHECKPOINT'])
    rt('R-M03','food-counter','cash','cash-collection','collect','credits / cash representation','staff_collection','manual_only','sale completed; collect separately from products',['A58.5-59s'])
    fam=[]
    for c in coverage['equipment_chains']:
        ids=[s['id'] for s in stations if c['id'] in s['equipment_families']]
        assert ids,c['id']
        fam.append({'source_family':c['id'],'source_equipment':c['equipment'],'source_status':c['status'],'station_ids':ids,'recipe_boundary':c['recipe_boundary'],'evidence_refs':c['sources']})
    # Structural acceptance check. This is a spec validation, not a simulation test.
    idx={s['id']:s for s in stations}
    for r in routes:
        for side,direction in [('source','out'),('destination','in')]:
            p=next(p for p in idx[r[side]['station']]['ports'] if p['id']==r[side]['port'])
            assert p['direction']==direction,(r['id'],side)
    graph={s['id']:[] for s in stations}
    for r in routes:graph[r['source']['station']].append(r['destination']['station'])
    def reaches(start,target):
        seen=set();todo=[start]
        while todo:
            x=todo.pop()
            if x==target:return True
            if x in seen:continue
            seen.add(x);todo.extend(graph[x])
        return False
    assert not reaches('food-storage-out','food-storage-in')
    assert not reaches('utility-storage-out','utility-storage-in')
    data={'schema':'havenline-typed-routing-proposal-v1','scope':'D07 exact concept specification only; no runtime implementation or frozen recipes','source_equipment_file':'sources/docs/source-equipment-coverage.json','source_family_count':len(fam),'runtime_kinds_from_source':['wood','stone','metal','fuel'],'proposal_item_forms_are_not_runtime_ids':True,'capacities_speeds_costs_recipe_quantities_world_dimensions':None,'stations':stations,'routes':routes,'source_family_coverage':fam,'global_rules':['Carrier family and allowed form checked before release.','Reserve destination slot, stock and exclusive transfer owner before dispatch.','Reserve machine output before consuming inputs; a multi-input recipe reserves both ingredients together.','Wrong item remains source-held; a bounded reject area being full stops intake.','Full destination propagates wait upstream; no deletion, duplication or unbounded queue.','Storage OUT requires a request and never automatically returns to storage IN.','Food and utility cassettes serve local bays; original front aisle and right fuel hatch remain separate.','Fuel, raw-food storage, hides, cargo and cash remain manual in this upgrade.','No unlisted future recipe or production conversion is active.'],'validation':{'source_families_covered':len(fam),'station_count':len(stations),'route_count':len(routes),'all_route_ports_resolve':True,'direction_consistency':True,'automatic_storage_return_path_exists':False,'runtime_tested':False}}
    (OUT/'routing-catalogue.json').write_text(json.dumps(data,indent=2)+'\n')
    return data

if __name__=='__main__':
    svgs=[flow(),camp()]
    data=catalogue()
    for svg in svgs:
        png=svg.with_suffix('.png')
        subprocess.run(['inkscape',str(svg),'--export-type=png','--export-filename='+str(png),'--export-width=2200'],check=True,capture_output=True,text=True)
    metadata={'deliverable':'D07','generated_files':[p.name for p in svgs]+[p.with_suffix('.png').name for p in svgs]+['routing-catalogue.json'],'source_families_covered':data['source_family_count'],'station_count':len(data['stations']),'route_count':len(data['routes']),'independent_review':'pending','runtime_fit':'not tested; no scale claim'}
    (OUT/'D07-build-checkpoint.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata))
