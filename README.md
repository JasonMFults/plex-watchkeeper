# Jason Plex Watchkeeper

Written for Jason / BobaFett3896 on Thea-ter. This is a standalone Plex companion service with MCP plugin tools, not a legacy Plex `.bundle`. Run it on an always-on machine that can reach your Plex server. It keeps working when ChatGPT is closed.

**Current delivery state: code and manifests are complete and locally tested. Not installed on your Plex host, connected to live Plex, or enabled.** No account password or token is included.

## Playlists

| Full playlist | Unwatched playlist | Order |
|---|---|---|
| Marvel Multiverse Marathon (existing ID 245419) | Marvel Multiverse Marathon (Remaining) | Established Marvel order, 854 individual planned items; all 323 previously verified available items preserve their exact relative order |
| Star Trek (Full Guide Order) | Star Trek (Progress) (existing ID 231363) | Your linked viewing guide, 960 entries including 14 movies; five guide entries cover two episodes |

The new Star Trek guide replaces the older Progress playlist's chronology and includes the Kelvin movies. Jason's watched state is preserved. Missing content is skipped and inserted into its correct position when it appears. No media files, watched flags, or other users' playlists are changed. Slingshot and Endgame: Encore are excluded. Your Friendly Neighborhood Spider-Man season 2 is excluded. Black Widow's post-credits scene remains a viewing note after Endgame because Plex has no separate scene file.

## Start on your Plex machine

1. Extract this folder on the computer running Plex, or another always-on computer with access to it. Docker Compose must be installed.
2. Run `python3 scripts/setup.py`. It creates a private `.env` with generated service secrets.
3. Edit `.env` **locally** and fill in `PLEX_URL` and `PLEX_TOKEN`. Use the owner's Plex token so the service can switch to Jason; it never falls back to the owner. Do not send the token or password in chat. [Plex's token instructions](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).
4. Run `docker compose up -d --build`.
5. Run `docker compose exec watchkeeper python scripts/control.py preview`. Review the counts, missing items, and any ambiguity. Dry-run mode prevents writes.
6. Resolve any `review_required` cases as described below. When the preview is correct, change `DRY_RUN=false` in `.env` and run `docker compose up -d --force-recreate`.
7. Check `docker compose exec watchkeeper python scripts/control.py status`. `synced` confirms a completed reconciliation. `error` or `review_required` requires attention.

The service polls every five minutes by default. This catches watched/unwatched changes and newly added content even without webhooks. It creates a new playlist when its first matching item is available; Plex cannot create a regular empty playlist through this API. An existing Remaining playlist can become empty.

## Faster watch-event updates

Optional: configure Plex to send webhooks to `https://YOUR_PRIVATE_SERVICE_HOST/webhooks/plex/YOUR_WEBHOOK_SECRET`. Use the secret generated in your local `.env`. The receiver must be reachable from Plex. The default Docker port binds only to loopback, so use an authenticated TLS reverse proxy or private networking for access from another machine. Disable proxy access logs for the webhook path because it contains the secret.

Plex webhooks require Plex Pass and are tied to the user configuring them. Verify that Jason's events actually arrive; an owner's hook is not assumed to receive Jason's scrobbles. Polling remains the reliable fallback. The event only triggers a read of Jason's real watched state; the service never trusts an event to mark media watched. A stop event can trigger an earlier check; it does not count as completed viewing.

## MCP plugin connection

Three tools are included: `playlist_status` (read-only), `preview_playlists` (read-only), and `sync_playlists` (writes the configured playlists when enabled).

For a desktop MCP client supporting stdio, adapt `mcp-client.example.json` with the absolute extracted folder path. The stdio bridge executes inside the existing container and talks to the service locally. It does not copy your Plex token to the client.

The same tools are available at `/mcp` through Streamable HTTP with a required Bearer service token. If exposing this remotely, use TLS, configure exact `MCP_ALLOWED_HOSTS` and `MCP_ALLOWED_ORIGINS`, and keep it private. This package does not implement an OAuth authorization server. ChatGPT remote connectors that require OAuth need an OAuth gateway before they can connect; this is not an already installed ChatGPT plugin. Do not disable authentication to connect it.

## Ambiguity and catalog differences

Star Trek resolves titles within the correct series before episode numbers. This avoids The Cage shifting TOS season-one numbering. Split two-part episodes are kept as individual items; an actual combined file appears once. Unmatched combined premieres or alternate titles require an explicit mapping. Marvel uses exact series, season, and episode coordinates, plus verified Plex IDs where available. A movie must match its title and year. Duplicate versions without a verified ID require review.

Create `/data/overrides.json` in the container's persistent volume for reviewed mappings, for example:

```json
{"trek-0001": ["ACTUAL_PLEX_RATING_KEY"]}
```

Mapping values may contain multiple IDs when one guide entry maps to separate episode files. Map adjacent guide entries to the same combined-file ID when appropriate; duplicate media IDs are emitted once, at their first position. Verify the episode's identity before mapping it. Overrides deliberately take precedence over the matcher, so only trusted local administrators should edit them. Any unknown old playlist item blocks the entire synchronization until resolved, rather than silently removing it.

The guide is pinned to the page retrieved October 1, 2026 (page label “Last Updated 2/03/2026”). Its episode/movies sequence is included without its commentary. New Plex arrivals sync automatically using that sequence. Future revisions to the website need a reviewed manifest update; they are not silently adopted.

## Recovery and verification

Ordered playlist ID backups are written under `/data/backups` before changes. `/data/pending-plan.json` records an in-progress write; a crash is repaired by the next idempotent reconciliation. Plex cannot atomically update multiple playlists, so a connection failure can temporarily leave a partial update. Watched state and files are never modified. To restore a playlist order, use its backup IDs as a temporary manifest and preview it before enabling a write.

To pause automatic edits, set `DRY_RUN=true` and recreate the container. Stop with `docker compose stop`. Keep the data volume to retain backups. Do not run multiple replicas or multiple installations against the same playlists.

Run the meaningful local checks with `python -m unittest discover -s tests -v`. These verify watched removal, unwatched restoration, insertion order, safe matching, guide exceptions, profile event isolation, API authentication, and actual MCP discovery/calls. They use synthetic Plex objects and do not constitute a live Plex integration test.

Sources: [Star Trek viewing guide](https://startrekviewingguide.com/lo-fi-print-ready-listing.html), [Plex webhooks](https://support.plex.tv/articles/115002267687-webhooks/), [Python PlexAPI playlists](https://python-plexapi.readthedocs.io/en/stable/modules/playlist.html), [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
