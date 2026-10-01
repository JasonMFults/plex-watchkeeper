import unittest,json,tempfile,os,sys
from pathlib import Path
from types import SimpleNamespace as N
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from watchkeeper import *
def media(ident,title='Film',kind='movie',**kw):return N(ratingKey=str(ident),title=title,type=kind,year=2000,viewCount=0,**kw)
class Playlist:
 def __init__(self,items):self._items=items;self.smart=False;self.title='Test';self.ratingKey='55'
 def items(self):return list(self._items)
 def reload(self):pass
 def removeItems(self,items):self._items=[x for x in self._items if x not in items]
 def addItems(self,items):self._items.extend(items)
 def moveItem(self,item,after=None):
  self._items.remove(item);self._items.insert(self._items.index(after)+1 if after else 0,item)
class Tests(unittest.TestCase):
 def test_watched_removal_and_new_item_position(self):
  a,b,c=media(1),media(2),media(3);p=Playlist([a,c]);patch_playlist(p,[b,c],False,lambda *a:None);self.assertEqual([key(x) for x in p.items()],['2','3'])
 def test_mark_unwatched_restores_original_position(self):
  a,b,c=media(1),media(2),media(3);p=Playlist([a,c]);patch_playlist(p,[a,b,c],False,lambda *a:None);self.assertEqual([key(x) for x in p.items()],['1','2','3'])
 def test_noop_does_not_backup(self):
  a=media(1);patch_playlist(Playlist([a]),[a],True,lambda *a:self.fail('No-op mutated'))
 def test_full_playlist_never_drops_unknown(self):
  with self.assertRaises(SafetyError):patch_playlist(Playlist([media(1)]),[],True,lambda *a:None)
 def test_movie_year_prevents_wrong_remake(self):
  a,b=media(1),media(2);b.year=2015
  resolved,issue=resolve({'id':'m','kind':'movie','title':'Film','year':2015},[a,b]);self.assertIs(resolved[0],b)
 def test_ambiguity_is_reported(self):
  resolved,issue=resolve({'id':'m','kind':'movie','title':'Film','year':2000},[media(1),media(2)]);self.assertFalse(resolved);self.assertEqual(issue['status'],'ambiguous')
 def test_echo_never_matches_smallville_episode(self):
  wrong=media(1,'Echo','episode',grandparentTitle='Smallville',parentIndex=1,index=1)
  resolved,issue=resolve({'id':'e','kind':'episode','series':'Echo','season':1,'episode':1},[wrong]);self.assertFalse(resolved)
 def test_cage_title_overrides_wrong_guide_number(self):
  cage=media(1,'The Cage','episode',grandparentTitle='Star Trek',parentIndex=0,index=1)
  trap=media(2,'The Man Trap','episode',grandparentTitle='Star Trek',parentIndex=1,index=1)
  resolved,_=resolve({'id':'t','kind':'episode','series':'Star Trek','season':1,'episode':1,'title':'The Cage','title_first':True},[trap,cage]);self.assertIs(resolved[0],cage)
 def test_combined_guide_range_split_files(self):
  a=media(1,'Emissary (1)','episode',grandparentTitle='Star Trek: Deep Space Nine',parentIndex=1,index=1)
  b=media(2,'Emissary (2)','episode',grandparentTitle='Star Trek: Deep Space Nine',parentIndex=1,index=2)
  resolved,issue=resolve({'id':'t','kind':'episode','series':'Star Trek: Deep Space Nine','season':1,'episode':1,'episode_end':2,'title':'Emissary','title_first':True},[b,a]);self.assertEqual(resolved,[a,b])
 def test_wrong_account_and_wrong_server_events_ignored(self):
  k=Keeper(Config(data_dir=Path(tempfile.mkdtemp())));k.account_id='77'
  payload={'event':'media.scrobble','Server':{'uuid':k.cfg.machine_identifier},'Account':{'id':88}}
  self.assertFalse(k.accept_event(payload));self.assertFalse(k.trigger.is_set())
  payload['Account']['id']=77;self.assertTrue(k.accept_event(payload));k.trigger.clear();payload['Server']['uuid']='other';self.assertFalse(k.accept_event(payload))
 def test_marvel_projection_and_manifest_exclusions(self):
  manifest=json.loads((ROOT/'manifests/marvel.json').read_text());pinned=[x['rating_key'] for x in manifest['items'] if 'rating_key' in x];self.assertEqual(len(pinned),323);self.assertEqual(len(set(pinned)),323)
  self.assertFalse(any('Slingshot' in x.get('series','') for x in manifest['items']))
  self.assertFalse(any(x.get('series')=='Your Friendly Neighborhood Spider-Man' and x['season']==2 for x in manifest['items']))
 def test_star_trek_guide_delays_and_movie_count(self):
  items=json.loads((ROOT/'manifests/star-trek.json').read_text())['items'];self.assertEqual(len(items),960)
  self.assertEqual(sum(x['kind']=='movie' for x in items),14)
  ent=[x for x in items if x.get('series')=='Star Trek: Enterprise'];self.assertLess(ent.index(next(x for x in ent if x['season']==1 and x['episode']==12)),ent.index(next(x for x in ent if x['season']==1 and x['episode']==11)))
 def test_reconcile_preview_apply_and_rewatch(self):
  temp=Path(tempfile.mkdtemp());(temp/'manifests').mkdir()
  entries=[{'id':str(i),'kind':'movie','title':t,'year':2000} for i,t in [(1,'A'),(2,'B'),(3,'C')]]
  (temp/'manifests/test.json').write_text(json.dumps({'items':entries}))
  conf=temp/'config.json';conf.write_text(json.dumps({'sections':[6],'playlists':[{'manifest':'test.json','full':{'title':'Full','key':'55'},'remaining':{'title':'Remaining','key':'56'}}]}))
  a,b,c=media(1,'A'),media(2,'B'),media(3,'C');b.viewCount=1
  full=Playlist([a,c]);full.title='Full'
  remaining=Playlist([a,c]);remaining.title='Remaining';remaining.ratingKey='56'
  section=N(type='movie',all=lambda:[a,b,c]);server=N(library=N(sectionByID=lambda _:section),playlists=lambda:[full,remaining])
  k=Keeper(Config(data_dir=temp/'data',config_file=conf))
  with patch('watchkeeper.ROOT',temp),patch.object(k,'connect',return_value=server):
   self.assertEqual(k.reconcile(False)['state'],'preview');self.assertEqual([key(x) for x in full.items()],['1','3'])
   self.assertEqual(k.reconcile(True)['state'],'synced');self.assertEqual([key(x) for x in full.items()],['1','2','3']);self.assertEqual([key(x) for x in remaining.items()],['1','3'])
   b.viewCount=0;a.viewCount=1
   self.assertEqual(k.reconcile(True)['state'],'synced');self.assertEqual([key(x) for x in remaining.items()],['2','3']);self.assertEqual([key(x) for x in full.items()],['1','2','3'])
   self.assertTrue(list((temp/'data/backups').glob('*.json')))
   section.all=lambda: (_ for _ in ()).throw(RuntimeError('secret token error'))
   report=k.reconcile(True);self.assertEqual(report['state'],'error');self.assertNotIn('secret',json.dumps(report));self.assertEqual([key(x) for x in full.items()],['1','2','3'])
 def test_owner_token_never_used_if_jason_token_missing(self):
  user=N(username='BobaFett3896',title='Jason',id=77,get_token=lambda _:None)
  owner=N(machineIdentifier=Config().machine_identifier,myPlexAccount=lambda:N(user=lambda _:user))
  k=Keeper(Config(plex_url='http://plex.local:32400',plex_token='OWNER_SECRET',data_dir=Path(tempfile.mkdtemp())),server_factory=lambda *a,**kw:owner)
  with self.assertRaisesRegex(SafetyError,'owner fallback is prohibited'):k.connect()
 def test_http_auth_and_mcp_discovery(self):
  os.environ.update(WATCHKEEPER_API_TOKEN='a'*40,WATCHKEEPER_WEBHOOK_SECRET='b'*40,DATA_DIR=tempfile.mkdtemp())
  import server
  from fastapi.testclient import TestClient
  with patch.object(server.keeper,'start'),patch.object(server.keeper,'close'),TestClient(server.application,base_url="http://127.0.0.1:8765") as client:
   self.assertEqual(client.get('/status').status_code,401)
   h={'Authorization':'Bearer '+'a'*40,'Accept':'application/json, text/event-stream'}
   response=client.post('/mcp',headers=h,json={'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'test','version':'1'}}});self.assertEqual(response.status_code,200,response.text)
   response=client.post('/mcp',headers={**h,'MCP-Protocol-Version':'2025-03-26'},json={'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}});self.assertEqual(response.status_code,200,response.text);self.assertEqual(len(response.json()['result']['tools']),3)
   response=client.post('/mcp',headers=h,json={'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'playlist_status','arguments':{}}});self.assertEqual(response.status_code,200,response.text)
   self.assertEqual(client.post('/webhooks/plex/wrong',json={}).status_code,401)
   self.assertEqual(client.post('/sync',headers=h).status_code,409)
if __name__=='__main__':unittest.main()
