"""Build factual ordered manifests; no guide commentary is redistributed."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'manifests'
def norm(t):return re.sub(r'[^a-z0-9]','',t.lower())
observed=json.loads((source/'verified-marvel-identities.json').read_text())
items=[]
def movie(title,year):items.append(dict(kind='movie',title=title,year=year))
def episodes(series,season,count,start=1):
 for e in range(start,count+1):items.append(dict(kind='episode',series=series,season=season,episode=e))
def seasons(series,counts):
 for s,c in enumerate(counts,1):episodes(series,s,c)
A="Marvel's Agents of S.H.I.E.L.D."
C="Marvel's Agent Carter"
D="Marvel's Daredevil"
J="Marvel's Jessica Jones"
L="Marvel's Luke Cage"
I="Marvel's Iron Fist"
P="Marvel's The Punisher"
X='X-Men: The Animated Series'
S='Spider-Man'
# Every range expands to individual episodes before Plex operations.
episodes('Eyes of Wakanda',1,4)
movie('Captain America: The First Avenger',2011);movie('Marvel One-Shot: Agent Carter',2013);seasons(C,[8,10])
for t,y in [('Captain Marvel',2019),('Iron Man',2008),('Iron Man 2',2010),('The Incredible Hulk',2008),('Marvel One-Shot: A Funny Thing Happened on the Way to Thor’s Hammer',2011),('Thor',2011),('Marvel One-Shot: The Consultant',2011),('The Avengers',2012),('Marvel One-Shot: Item 47',2012),('Iron Man 3',2013),('Marvel One-Shot: All Hail the King',2014)]:movie(t,y)
episodes(A,1,7);movie('Thor: The Dark World',2013);episodes(A,1,16,8);movie('Captain America: The Winter Soldier',2014);episodes(A,1,22,17)
movie('Guardians of the Galaxy',2014);episodes('I Am Groot',1,1);movie('Guardians of the Galaxy: Vol. 2',2017);episodes('I Am Groot',1,5,2);episodes('I Am Groot',2,5)
episodes(D,1,13);episodes(J,1,13);episodes(A,2,19);movie('Avengers: Age of Ultron',2015);episodes(A,2,22,20)
episodes('WHIH Newsfront',1,5);movie('Ant-Man',2015);episodes(D,2,13);episodes(L,1,13);episodes(A,3,19);episodes('WHIH Newsfront',2,5);movie('Captain America: Civil War',2016);episodes(A,3,22,20);episodes(A,4,22)
episodes(I,1,13);episodes('Marvel’s The Defenders',1,8);movie('Spider-Man: Homecoming',2017);episodes(P,1,13);movie('Black Widow',2021);movie('Doctor Strange',2016);episodes(A,5,19);movie('Black Panther',2018)
episodes(J,2,13);episodes('Marvel’s Inhumans',1,8);episodes(L,2,13);episodes(I,2,10);episodes(D,3,13);episodes(P,2,13);episodes(J,3,13)
episodes('Marvel’s Runaways',1,10);episodes('Marvel’s Runaways',2,13);seasons('Marvel’s Cloak & Dagger',[10,10]);episodes('Marvel’s Runaways',3,10)
movie('Thor: Ragnarok',2017);episodes(A,5,22,20);movie('Ant-Man and the Wasp',2018);movie('Avengers: Infinity War',2018);episodes(A,6,13);episodes(A,7,13);episodes('Helstrom',1,10);movie('Avengers: Endgame',2019)
episodes('WandaVision',1,9);seasons('Loki',[6,6]);episodes('What If...?',1,9);episodes('Marvel Zombies',1,4);episodes('What If...?',2,9);episodes('What If...?',3,8)
episodes(X,1,13);episodes(X,2,13)
x3=[(3,1),(3,2),(3,3),(3,4),(3,5),(3,6),(3,7),(5,4),(3,10),(5,5),(3,15),(3,8),(3,9),(3,11),(3,12),(3,13),(3,14),(3,16),(4,14)]
x4=[(3,17),(5,3),(4,6),(4,7),(4,16),(4,3),(4,15),(3,18),(4,1),(4,2),(4,4),(4,5),(4,17),(5,6),(4,13),(3,19),(4,12),(4,8),(4,9),(4,10),(4,11)]
x5=[(5,1),(5,2),(5,7),(5,8),(5,10),(5,9),(5,11),(5,12),(5,13),(5,14)]
for s,e in x3:episodes(X,s,e,e)
episodes(S,1,13)
for s,e in x4:episodes(X,s,e,e)
episodes(S,2,14)
for s,e in x5:episodes(X,s,e,e)
for s,c in [(3,14),(4,11),(5,13)]:episodes(S,s,c)
seasons('X-Men ’97',[10,9])
for t,y in [('X-Men: First Class',2011),('X-Men Origins: Wolverine',2009),('X-Men',2000),('X2: X-Men United',2003),('X-Men: The Last Stand',2006),('The Wolverine',2013),('X-Men: Days of Future Past',2014),('X-Men: Apocalypse',2016),('X-Men: Dark Phoenix',2019),('Deadpool',2016),('Deadpool: No Good Deed',2017),('The New Mutants',2020),('Deadpool 2',2018),('Logan',2017),('Blade',1998),('Blade II',2002),('Blade: Trinity',2004)]:movie(t,y)
episodes('Blade: The Series',1,12)
for t,y in [('Daredevil',2003),('Elektra',2005),('Fantastic Four',2005),('Fantastic Four: Rise of the Silver Surfer',2007),('Fantastic Four',2015),('The Fantastic Four: First Steps',2025),('Shang-Chi and the Legend of the Ten Rings',2021),('Deadpool & Wolverine',2024)]:movie(t,y)
episodes('The Falcon and the Winter Soldier',1,6);episodes('Spider-Noir',1,8);movie('Spider-Man: Into the Spider-Verse',2018);movie('Spider-Man: Across the Spider-Verse',2023);episodes('Your Friendly Neighborhood Spider-Man',1,10)
for t,y in [('Spider-Man',2002),('Spider-Man 2',2004),('Spider-Man 3',2007),('The Amazing Spider-Man',2012),('The Amazing Spider-Man 2',2014),('Madame Web',2024),('Kraven the Hunter',2024),('Venom',2018),('Venom: Let There Be Carnage',2021),('Peter’s To-Do List',2019),('Spider-Man: Far from Home',2019)]:movie(t,y)
episodes('The Daily Bugle',1,6);episodes('The Daily Bugle',2,13);movie('Spider-Man: No Way Home',2021);episodes('The Daily Bugle',4,6);movie('Venom: The Last Dance',2024);movie('Morbius',2022);episodes('The Daily Bugle',3,4)
movie('Eternals',2021);episodes('Hawkeye',1,6);movie('Doctor Strange in the Multiverse of Madness',2022);episodes('Moon Knight',1,6);movie('Thor: Love and Thunder',2022);movie('Black Panther: Wakanda Forever',2022);episodes('Echo',1,5);episodes('She-Hulk: Attorney at Law',1,9);episodes('Ms. Marvel',1,6);episodes('Ironheart',1,6)
for t,y in [('Werewolf by Night',2022),('The Guardians of the Galaxy Holiday Special',2022),('Ant-Man and the Wasp: Quantumania',2023),('Guardians of the Galaxy Vol. 3',2023)]:movie(t,y)
episodes('Secret Invasion',1,6);movie('The Marvels',2023);episodes('Agatha All Along',1,9);episodes('Daredevil: Born Again',1,9);movie('Captain America: Brave New World',2025);movie('Thunderbolts*',2025);episodes('Daredevil: Born Again',2,8);movie('The Punisher: One Last Kill',2026);episodes('Wonder Man',1,8);movie('Spider-Man: Brand New Day',2026);episodes('VisionQuest',1,8)
def identity(x):
 if x['kind']=='movie':return ('movie',norm(x['title']),x['year'])
 return ('episode',norm(x['series']),x['season'],x['episode'])
# Normalize the verified Plex series aliases for matching, never episode title alone.
alias={'xmen97':['X-Men ’97',"X-Men '97"],'spiderman':['Spider-Man: The Animated Series'],'marvelsthedefenders':['The Defenders'],'marvelsdaredevil':['Daredevil'],'marvelsjessicajones':['Jessica Jones'],'marvelslukecage':['Luke Cage'],'marvelsironfist':['Iron Fist'],'marvelsthepunisher':['The Punisher'],'marvelsinhumans':['Inhumans'],'marvelsrunaways':['Runaways'],'marvelscloakdagger':['Cloak & Dagger']}
lookup={identity(x):x for x in observed}
for i,x in enumerate(items):
 x['id']=f'marvel-{i+1:04}'
 if x['kind']=='episode':
  x['series_aliases']=alias.get(norm(x['series']),[])
  if x['series']=='Spider-Man':x['series_year']=1994
 o=lookup.get(identity(x))
 if o:x.update(rating_key=o['rating_key'],title=o['title'])
# Existing available content MUST project to the exact verified order.
projection=[x['rating_key'] for x in items if 'rating_key' in x]
expected=[x['rating_key'] for x in observed]
if projection!=expected:
 print('Unmatched verified:',[x for x in observed if x['rating_key'] not in projection]);raise SystemExit('Available order mismatch; do not publish.')
manifest={'name':'Marvel Multiverse Marathon','source':'Jason’s established order','machine_identifier':'8b878955a394dd0833a570758a9e1b42637131c7','notes':['Slingshot and Endgame: Encore excluded.','Black Widow: skip post-credits here; view the scene after Avengers: Endgame. No duplicate full movie is added.','Blade pilot may be combined. Resolve catalog numbering by title before approving it.'],'items':items}
(ROOT/'manifests/marvel.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
series={'ENT':'Star Trek: Enterprise','SHO':'Star Trek: Short Treks','TOS':'Star Trek','DIS':'Star Trek: Discovery','SNW':'Star Trek: Strange New Worlds','TAS':'Star Trek: The Animated Series','TNG':'Star Trek: The Next Generation','DS9':'Star Trek: Deep Space Nine','VOY':'Star Trek: Voyager','LDS':'Star Trek: Lower Decks','PRO':'Star Trek: Prodigy','PIC':'Star Trek: Picard'}
years=[1979,1982,1984,1986,1989,1991,1994,1996,1998,2002,2009,2013,2016,2025]
movie_years=dict(zip([r[4:] for r in json.loads((source/'trek-source-entries.json').read_text()) if r.startswith('MOV ')],years))
trek=[]
for i,r in enumerate(json.loads((source/'trek-source-entries.json').read_text())):
 m=re.fullmatch(r'(\w+) Season (\d+), episodes? (\d+)(?:[-–](\d+))? - (.+)',r)
 if m:
  code,s,e,end,t=m.groups();x={'kind':'episode','series':series[code],'season':int(s),'episode':int(e),'title':t,'title_first':True}
  if end:x['episode_end']=int(end)
  if code=='TOS':x.update(series_year=1966,series_aliases=['Star Trek: The Original Series'])
 else:
  assert r.startswith('MOV '),r
  title=r[4:];x={'kind':'movie','title':title,'year':movie_years[title]}
  if title=='Star Trek (2009)':x.update(title='Star Trek')
 x['id']=f'trek-{i+1:04}';trek.append(x)
assert len(trek)==960
(ROOT/'manifests/star-trek.json').write_text(json.dumps({'name':'Star Trek (Full Guide Order)','source':'https://startrekviewingguide.com/lo-fi-print-ready-listing.html','source_updated':'2026-02-03','source_sha256':'7fcf5b7d6012ce5da41faa9af2fa315a39edf8406b546602a6a352542e59890d','notes':['Guide includes Kelvin movies; the newer user-specified guide replaces the old playlist chronology.','Title matching takes priority over guide numbers, especially The Cage and combined premieres.','Guide revisions are reviewed explicitly; new library arrivals use the pinned order automatically.'],'items':trek},ensure_ascii=False,indent=2))
print(f'Marvel {len(items)} planned items / {len(projection)} verified available; Star Trek {len(trek)} guide entries')
