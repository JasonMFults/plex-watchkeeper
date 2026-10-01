"""Local MCP bridge. It talks to the watcher; it never holds a Plex token."""
import os,httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
client=httpx.Client(base_url=os.getenv('WATCHKEEPER_URL','http://127.0.0.1:8765'),headers={'Authorization':'Bearer '+os.environ['WATCHKEEPER_API_TOKEN']},timeout=300)
mcp=MCPServer('Jason Plex Watchkeeper',version='1.0.0')
def request(method,path):
 response=client.request(method,path);response.raise_for_status();return response.json()
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def playlist_status()->dict:
 """Read Jason's Marvel and Star Trek playlist status."""
 return request('GET','/status')
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
def preview_playlists()->dict:
 """Preview Jason's playlist updates; no writes."""
 return request('POST','/preview')
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False,destructiveHint=False,idempotentHint=True))
def sync_playlists()->dict:
 """Synchronize the configured full and unwatched playlists under Jason."""
 return request('POST','/sync')
if __name__=='__main__':mcp.run(transport='stdio')
