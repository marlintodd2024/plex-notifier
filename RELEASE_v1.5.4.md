## BingeAlert v1.5.4 — User Lifecycle, Sonarr Anime & Smart Anime Routing

### ✨ Automatic User Deactivation & Reactivation

BingeAlert now tracks when users are removed from Jellyseerr/Plex and automatically stops sending them notifications.

- **Sync Users** compares Jellyseerr's user list against BingeAlert's local database
- Users no longer in Jellyseerr are **soft-deactivated** — data preserved, notifications stop
- Deactivated users who reappear are **automatically reactivated**
- Empty API responses from Jellyseerr are safely ignored to prevent false mass-deactivations
- Users tab shows **Active/Inactive** badges with **⏸️ Deactivate / ✅ Activate** toggle
- Dashboard stat card shows active count with "+N inactive" note
- User dropdowns (Shared Users, Request on Behalf) only show active users
- Pending notifications for inactive users are marked as skipped

---

### 🎌 Sonarr Anime Support (Multi-Instance)

All background workers and admin features now support a second Sonarr instance for anime.

**Setup:** Add to `.env`:
```env
SONARR_ANIME_URL=http://your-anime-sonarr:8990
SONARR_ANIME_API_KEY=your_anime_api_key
```

Or configure in Settings → **🎌 Sonarr Anime**. If not set, everything works as before.

**Covered:** Stuck download monitor, quality monitor, reconciliation, upcoming episodes, episode imports, issue auto-fix — all check both instances. Same `/webhooks/sonarr` endpoint works for both.

---

### 🎌 Smart Anime Request Routing

**Request on Behalf** now auto-detects anime and routes it to your anime Sonarr in Seerr.

- Auto-detection: **Animation** genre + **Japanese** origin country (or **anime** keyword) from TMDB data
- Sends `serverId`, `profileId`, and `rootFolder` overrides to Seerr's request API
- New **🎌 Seerr Anime Routing** section in Settings with server/profile/root folder fields
- **🔍 Discover Seerr Sonarr Servers** button fetches configured servers from Seerr — click to auto-fill
- Success message confirms routing: "🎌 Routed to anime Sonarr"

---

### 🔧 Settings Page Fixes

- **Live config reload** — saving settings now updates the running process immediately, no restart needed to see changes
- **Tab bleed fix** — Settings tab content no longer appends below other tabs

### 📝 Footer

All pages (admin, setup, login) now include a footer with links to GitHub, Report a Bug, Request a Feature, and Discussions.

### 📦 Files Changed

| File | Change |
|------|--------|
| `app/config.py` | Sonarr Anime + Seerr anime override settings |
| `app/database.py` | `is_active` and `deactivated_at` on User model |
| `alembic/versions/008_add_user_is_active.py` | Database migration |
| `app/services/sonarr_service.py` | Multi-instance support, `get_all_sonarr_instances()` |
| `app/services/jellyseerr_sync.py` | Soft-delete/reactivation, paginated fetch, multi-Sonarr imports |
| `app/services/email_service.py` | Skip inactive users, check all Sonarr queues |
| `app/routers/admin.py` | User toggle, Seerr discovery, anime routing, live config reload |
| `app/routers/webhooks.py` | Filter inactive users, multi-Sonarr issue auto-fix |
| `app/routers/health.py` | Sonarr Anime health status |
| `app/background/stuck_monitor.py` | Check all Sonarr instance queues |
| `app/background/quality_monitor.py` | Search all instances for series |
| `app/background/reconciliation.py` | Scan all instances for reconciliation |
| `app/static/admin.html` | User status UI, Sonarr Anime settings, Seerr routing, tab fix, footer |
| `app/static/setup.html` | Footer |
| `app/static/login.html` | Footer |

### 🔄 Upgrade
```bash
# Docker Pull users:
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d

# Build from Source users:
git pull
docker compose up -d --build
```

Database migration runs automatically on startup. All existing users default to **active**.

### ⚙️ Post-Upgrade Setup for Anime
1. Add `SONARR_ANIME_URL` and `SONARR_ANIME_API_KEY` to `.env` (or configure in Settings)
2. Point your anime Sonarr's webhook at `http://your-server:8000/webhooks/sonarr`
3. Go to Settings → 🎌 Seerr Anime Routing → click **Discover** to find your anime server ID
4. Click your anime server to auto-fill, then **Save Settings**
