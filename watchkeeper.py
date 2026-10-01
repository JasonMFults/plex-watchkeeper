from __future__ import annotations
import json,os,re,threading,time,unicodedata,hashlib
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import dataclass
from typing import Any

ROOT=Path(__file__).resolve().parent
class SafetyError(Exception):pass

def norm(value):
 return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower())
def title_key(value):
 value=str(value).replace('…','...')
 value=re.sub(r'\bPart\s+(III|II|I)\b',lambda m:'Part '+str({'I':1,'II':2,'III':3}[m[1].upper()]),value,flags=re.I)
 # Plex commonly labels two-parters with (1), while the guide says Part 1.
 value=re.sub(r'\((\d+)\)$',r'Part \1',value.strip())
 return norm(value)
def base_title(value):
 return title_key(re.sub(r'(?i)(?:,?\s*parts?\s*[\divand ]+|\s*\(\d+\))$','',value))
def key(obj):return str(obj.ratingKey)
def unique(items):return list({key(x):x for x in items}.values())

def matches_series(spec,item):
 return norm(getattr(item,'grandparentTitle','')) in {norm(s) for s in [spec['series'],*spec.get('series_aliases',[])]}

def resolve(spec,catalog,overrides=None):
 """Return ordered media or an explicit missing/ambiguous result. No fuzzy cross-show matches."""
 override=(overrides or {}).get(spec['id'])
 if override:
  found=[]
  for ident in override:
   candidates=[x for x in catalog if key(x)==str(ident) and x.type==spec['kind']]
   if len(candidates)!=1:raise SafetyError('Invalid override for '+spec['id'])
   found.extend(candidates)
  return found,None
 candidates=[x for x in catalog if x.type==spec['kind']]
 if spec['kind']=='movie':
  candidates=[x for x in candidates if norm(x.title) in {norm(spec['title']),*[norm(t) for t in spec.get('title_aliases',[])]} and int(x.year or 0)==spec['year']]
 else:
  candidates=[x for x in candidates if matches_series(spec,x)]
  if spec.get('series_year'):
   candidates=[x for x in candidates if getattr(x,'grandparentYear',None)==spec['series_year']]
  if spec.get('title_first'):
   exact=[x for x in candidates if title_key(x.title)==title_key(spec['title'])]
   if exact:candidates=exact
   elif spec.get('episode_end'):
    # Guide range can be a single combined file or separate numbered parts.
    candidates=[x for x in candidates if x.parentIndex==spec['season'] and spec['episode']<=x.index<=spec['episode_end'] and base_title(x.title)==base_title(spec['title'])]
    indices={x.index for x in candidates}
    if indices==set(range(spec['episode'],spec['episode_end']+1)) and len(candidates)==len(indices):return sorted(candidates,key=lambda x:x.index),None
    candidates=[]
   else:candidates=[] # Never silently shift TOS numbering by one.
  else:
   candidates=[x for x in candidates if x.parentIndex==spec['season'] and x.index==spec['episode']]
 pinned=spec.get('rating_key')
 if pinned:
  match=[x for x in candidates if key(x)==str(pinned)]
  if len(match)==1:return match,None
 if len(candidates)==1:return candidates,None
 return [],{'id':spec['id'],'status':'ambiguous' if candidates else 'missing','item':spec,'candidates':[{'rating_key':key(x),'title':x.title} for x in candidates]}

@dataclass
class Config:
 plex_url:str=''
 plex_token:str=''
 target_user:str='BobaFett3896'
 target_title:str='Jason'
 machine_identifier:str='8b878955a394dd0833a570758a9e1b42637131c7'
 api_token:str=''
 webhook_secret:str=''
 dry_run:bool=True
 poll_seconds:int=300
 data_dir:Path=Path('/data')
 config_file:Path=ROOT/'config.json'
 @classmethod
 def env(cls):
  c=cls(plex_url=os.getenv('PLEX_URL',''),plex_token=os.getenv('PLEX_TOKEN',''),api_token=os.getenv('WATCHKEEPER_API_TOKEN',''),webhook_secret=os.getenv('WATCHKEEPER_WEBHOOK_SECRET',''),dry_run=os.getenv('DRY_RUN','true').lower()!='false',poll_seconds=max(30,int(os.getenv('POLL_SECONDS','300'))),data_dir=Path(os.getenv('DATA_DIR','/data')),config_file=Path(os.getenv('CONFIG_FILE',str(ROOT/'config.json'))))
  return c

def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp')
 with open(tmp,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)

def patch_playlist(playlist,wanted,full,backup):
 before=playlist.items();expected=[key(x) for x in wanted]
 if [key(x) for x in before]==expected:return
 if playlist.smart:raise SafetyError('Managed playlist must be a regular playlist')
 if len({key(x) for x in before})!=len(before):raise SafetyError('Duplicate existing entries require review')
 if full and any(key(x) not in expected for x in before):raise SafetyError('Full playlist contains unrecognized media; review before changing')
 backup(playlist,before)
 wanted_keys=set(expected)
 removed=[x for x in before if key(x) not in wanted_keys]
 if removed:playlist.removeItems(removed);playlist.reload()
 present={key(x) for x in playlist.items()}
 added=[x for x in wanted if key(x) not in present]
 for start in range(0,len(added),100):playlist.addItems(added[start:start+100]);playlist.reload()
 current=playlist.items()
 for index,ident in enumerate(expected):
  if key(current[index])==ident:continue
  moving=next(x for x in current if key(x)==ident)
  playlist.moveItem(moving,after=current[index-1] if index else None)
  playlist.reload();current=playlist.items()
 if [key(x) for x in playlist.items()]!=expected:raise SafetyError('Playlist write verification failed')

class Keeper:
 def __init__(self,cfg:Config,server_factory=None):
  self.cfg=cfg;self.lock=threading.Lock();self.trigger=threading.Event();self.stop=threading.Event();self.thread=None;self.account_id=None
  self.factory=server_factory;self.last={'state':'not_connected','dry_run':cfg.dry_run,'user':'Jason','playlists':[]}
  self.path=cfg.data_dir/'status.json'
  if self.path.exists():self.last=json.loads(self.path.read_text())
 def connect(self):
  if not self.cfg.plex_url or not self.cfg.plex_token:raise SafetyError('Configure PLEX_URL and PLEX_TOKEN on the server')
  from plexapi.server import PlexServer
  owner=(self.factory or PlexServer)(self.cfg.plex_url,self.cfg.plex_token,timeout=30)
  if owner.machineIdentifier!=self.cfg.machine_identifier:raise SafetyError('Wrong Plex server')
  user=owner.myPlexAccount().user(self.cfg.target_user)
  if norm(user.username)!=norm(self.cfg.target_user) or norm(user.title)!=norm(self.cfg.target_title):raise SafetyError('Jason account identity did not match')
  token=user.get_token(owner.machineIdentifier)
  if not token:raise SafetyError('Jason has no server token; owner fallback is prohibited')
  self.account_id=str(user.id)
  return (self.factory or PlexServer)(self.cfg.plex_url,token,timeout=30)
 def backup(self,playlist,items):
  stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
  atomic_json(self.cfg.data_dir/'backups'/f'{stamp}-{playlist.ratingKey}.json',{'playlist_key':str(playlist.ratingKey),'title':playlist.title,'account_id':self.account_id,'items':[key(x) for x in items]})
 def status(self):return json.loads(json.dumps(self.last))
 def reconcile(self,apply=False):
  if not self.lock.acquire(blocking=False):self.trigger.set();return {'state':'busy'}
  try:
   server=self.connect();configuration=json.loads(self.cfg.config_file.read_text())
   catalog=[]
   # All configured sections must be successfully read before any mutation.
   for section_id in configuration['sections']:
    section=server.library.sectionByID(section_id)
    if section.type=='movie':catalog.extend(section.all())
    elif section.type=='show':
     shows=section.all();years={str(x.ratingKey):x.year for x in shows}
     eps=section.all(libtype='episode')
     for x in eps:x.grandparentYear=years.get(str(x.grandparentRatingKey))
     catalog.extend(eps)
   catalog=unique(catalog);plans=[];playlist_list=server.playlists()
   overrides_path=self.cfg.data_dir/'overrides.json';overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
   for pair in configuration['playlists']:
    manifest=json.loads((ROOT/'manifests'/pair['manifest']).read_text());desired=[];issues=[]
    for entry in manifest['items']:
     media,issue=resolve(entry,catalog,overrides)
     desired.extend(media)
     if issue:issues.append(issue)
    desired=unique(desired);unwatched=[x for x in desired if not int(x.viewCount or 0)]
    pairplans=[]
    for role,wanted in [('full',desired),('remaining',unwatched)]:
     title=pair[role]['title'];ident=pair[role].get('key')
     matches=[p for p in playlist_list if (str(p.ratingKey)==str(ident) if ident else p.title==title)]
     if len(matches)>1:raise SafetyError('Duplicate playlist title: '+title)
     playlist=matches[0] if matches else None
     if ident and not playlist:raise SafetyError('Configured Jason playlist not found: '+title)
     if playlist and (playlist.title!=title or playlist.smart):raise SafetyError('Playlist identity/type changed: '+title)
     before=playlist.items() if playlist else []
     missing_old=[key(x) for x in before if key(x) not in {key(x) for x in desired}]
     blocked=any(x['status']=='ambiguous' for x in issues) or bool(missing_old)
     pairplans.append((playlist,wanted,role))
     plans.append({'title':title,'role':role,'before':len(before),'after':len(wanted),'changed':[key(x) for x in before]!=[key(x) for x in wanted],'blocked':blocked,'unrecognized_existing':missing_old,'issues':issues,'wanted_keys':[key(x) for x in wanted],'_pair':pair,'_objects':(playlist,wanted,role)})
   report={'state':'preview','dry_run':not apply,'user':'Jason','checked_at':datetime.now(timezone.utc).isoformat(),'playlists':[{k:v for k,v in p.items() if not k.startswith('_')} for p in plans]}
   if apply:
    # Preflight every plan: never mutate one pair if the overall plan needs review.
    if any(p['blocked'] for p in plans):report['state']='review_required'
    else:
     atomic_json(self.cfg.data_dir/'pending-plan.json',report)
     for p in plans:
      playlist,wanted,role=p['_objects']
      if not playlist:
       if wanted:
        created=server.createPlaylist(p['title'],items=wanted)
        if [key(x) for x in created.items()]!=[key(x) for x in wanted]:raise SafetyError('New playlist verification failed')
      else:patch_playlist(playlist,wanted,role=='full',self.backup)
     report['state']='synced'
     (self.cfg.data_dir/'pending-plan.json').unlink(missing_ok=True)
   self.last=report;atomic_json(self.path,report);return report
  except Exception as exc:
   # Exceptions from HTTP clients may include tokens/URLs. Store safe category only.
   self.last={'state':'error','error':str(exc) if isinstance(exc,SafetyError) else type(exc).__name__,'user':'Jason','dry_run':not apply,'checked_at':datetime.now(timezone.utc).isoformat()}
   atomic_json(self.path,self.last);return self.status()
  finally:self.lock.release()
 def accept_event(self,payload):
  if payload.get('Server',{}).get('uuid')!=self.cfg.machine_identifier:return False
  event=payload.get('event')
  if event in {'library.new','library.on.deck'}:self.trigger.set();return True
  if event not in {'media.scrobble','media.unscrobble','media.stop'}:return False
  account=payload.get('Account',{})
  # Events merely prompt an authoritative scan of Jason's own watched state.
  if not self.account_id or str(account.get('id'))!=self.account_id:return False
  self.trigger.set();return True
 def start(self):
  def loop():
   while not self.stop.is_set():
    self.trigger.clear();self.reconcile(apply=not self.cfg.dry_run)
    self.trigger.wait(self.cfg.poll_seconds)
  self.thread=threading.Thread(target=loop,daemon=True);self.thread.start()
 def close(self):
  self.stop.set();self.trigger.set()
  if self.thread:self.thread.join(timeout=35)
