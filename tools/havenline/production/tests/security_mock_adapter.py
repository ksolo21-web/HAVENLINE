#!/usr/bin/env python3
import argparse,hashlib,json,os,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools/havenline/production'))
from lib import DOCS,load_json
ap=argparse.ArgumentParser();ap.add_argument('--attack',required=True);ap.add_argument('--candidate',required=True);ap.add_argument('--vulnerable',action='store_true');a=ap.parse_args()
cfg=load_json(DOCS/'SECURITY_ATTACK_MATRIX.json');attack=next(x for x in cfg['attacks'] if x['id']==a.attack)
assertions={k:True for k in attack['required_assertions']};passed=True
if a.vulnerable and a.attack=='fake_purchase':
    assertions[attack['required_assertions'][0]]=False;passed=False
seed=(a.candidate+'|'+a.attack).encode();before=hashlib.sha256(seed+b'|before').hexdigest();after=hashlib.sha256(seed+(b'|safe' if passed else b'|compromised')).hexdigest()
print(json.dumps({'attack_id':a.attack,'candidate_commit':a.candidate,'passed':passed,'assertions':assertions,'before_state_hash':before,'after_state_hash':after,'notes':'deterministic test fixture only'}))
raise SystemExit(0 if passed else 2)
