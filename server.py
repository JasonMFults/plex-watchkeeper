"""Single-process service: periodic Plex reconciliation + authenticated MCP tools."""
import asyncio,contextlib,json,os,secrets,fcntl
from fastapi import FastAPI,Request,HTTPException
from starlette.responses import JSONResponse
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from mcp.server.transport_security import TransportSecuritySettings
from watchkeeper import Keeper,Config

cfg=Config.env();keeper=Keeper(cfg)
mcp=MCPServer('Jason Plex Watchkeeper',version='1.0.0',instructions='Maintains Jason’s ordered Marvel and Star Trek playlists. Preview before applying changes. Never changes watched state or other users.')
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def playlist_status()->dict:
 """Read last synchronization result, missing items, and items requiring review."""
 return keeper.status()
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def preview_playlists()->dict:
 """Read Plex as Jason and preview full/unwatched playlist changes without editing Plex."""
 return keeper.reconcile(apply=False)
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False,destructiveHint=False,idempotentHint=True))
def sync_playlists()->dict:
 """Apply the pinned Marvel and Star Trek orders to Jason's full and remaining playlists. Does not mark anything watched/unwatched."""
 if cfg.dry_run:return {'state':'dry_run','message':'Set DRY_RUN=false locally after reviewing the preview to enable playlist changes.'}
 return keeper.reconcile(apply=True)

mcp_app=mcp.streamable_http_app(stateless_http=True,json_response=True,transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,allowed_hosts=os.getenv('MCP_ALLOWED_HOSTS','127.0.0.1:*,localhost:*').split(','),allowed_origins=os.getenv('MCP_ALLOWED_ORIGINS','http://127.0.0.1:*,http://localhost:*').split(',')))

@contextlib.asynccontextmanager
async def lifespan(app):
 if len(cfg.api_token)<32 or len(cfg.webhook_secret)<32:raise RuntimeError('Set distinct API and webhook secrets of at least 32 characters')
 if secrets.compare_digest(cfg.api_token,cfg.webhook_secret):raise RuntimeError('API and webhook secrets must differ')
 cfg.data_dir.mkdir(parents=True,exist_ok=True)
 lockfile=open(cfg.data_dir/'instance.lock','a')
 try:fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:raise RuntimeError('Only one service process may manage these playlists')
 async with mcp_app.router.lifespan_context(mcp_app):
  keeper.start()
  try:yield
  finally:await asyncio.to_thread(keeper.close);lockfile.close()
app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
@app.get('/health')
def health():return {'service':'plex-watchkeeper','running':True}
@app.get('/status')
def status():return keeper.status()
@app.post('/preview')
async def preview():return await asyncio.to_thread(keeper.reconcile,False)
@app.post('/sync')
async def sync():
 if cfg.dry_run:raise HTTPException(409,'Dry-run mode; review preview then enable locally')
 return await asyncio.to_thread(keeper.reconcile,True)
@app.post('/webhooks/plex/{secret}')
async def webhook(secret:str,request:Request):
 if not secrets.compare_digest(secret,cfg.webhook_secret):raise HTTPException(401,'Unauthorized')
 if 'multipart/form-data' in request.headers.get('content-type',''):
  form=await request.form(max_files=1,max_fields=8,max_part_size=1024*1024)
  try:payload=json.loads(str(form['payload']))
  except (KeyError,ValueError):raise HTTPException(400,'Invalid payload')
 else:
  try:payload=await request.json()
  except ValueError:raise HTTPException(400,'Invalid JSON')
 if not isinstance(payload,dict):raise HTTPException(400,'Invalid payload')
 return {'accepted':keeper.accept_event(payload)}
app.mount('/',mcp_app)

class Guard:
 """Pure ASGI auth avoids BaseHTTPMiddleware stream lifetime problems."""
 def __init__(self,inner):self.inner=inner
 async def __call__(self,scope,receive,send):
  if scope['type']!='http':return await self.inner(scope,receive,send)
  path=scope.get('path','');headers=dict(scope.get('headers',[]))
  if path!='/health' and not path.startswith('/webhooks/plex/'):
   auth=headers.get(b'authorization',b'').decode('latin-1')
   if not cfg.api_token or not secrets.compare_digest(auth,'Bearer '+cfg.api_token):
    return await JSONResponse({'error':'Unauthorized'},401)(scope,receive,send)
  length=headers.get(b'content-length',b'0')
  try:too_large=int(length)>2*1024*1024
  except ValueError:too_large=True
  if too_large:return await JSONResponse({'error':'Body too large'},413)(scope,receive,send)
  used=0
  async def limited_receive():
   nonlocal used
   message=await receive();used+=len(message.get('body',b''))
   if used>2*1024*1024:raise HTTPException(413,'Body too large')
   return message
  await self.inner(scope,limited_receive,send)
application=Guard(app)
if __name__=='__main__':
 import uvicorn
 uvicorn.run(application,host='0.0.0.0',port=8765,access_log=False)
