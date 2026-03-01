# Three Feature Implementation Status

## ✅ Feature 1: 5-Minute Email Delay - COMPLETE

### What Was Done:
1. **Database Changes:**
   - Added `send_after` column to `notifications` table
   - Created migration `004_add_send_after_to_notifications.py`

2. **Email Service Updates:**
   - Modified `process_pending_notifications()` to only send notifications where `send_after` is NULL or in the past
   - Now respects the delay before sending

3. **Webhook Updates:**
   - **Sonarr webhook:** Sets `send_after = now() + 5 minutes` when creating episode notifications
   - **Radarr webhook:** Sets `send_after = now() + 5 minutes` when creating movie notifications
   - Both log the delayed send time

4. **Background Task:**
   - Added `process_notifications_periodically()` function that runs every 60 seconds
   - Checks for notifications ready to send and processes them
   - Started automatically on application startup

### How It Works:
```
1. Content downloads → Webhook fires
2. Notification created with send_after = now() + 5 minutes
3. Notification marked as "pending" (sent=False)
4. Background task checks every minute
5. When current time > send_after, email is sent
6. Gives Plex 5 minutes to index before users get notified
```

### Files Modified:
- `app/database.py` - Added send_after field
- `alembic/versions/004_add_send_after_to_notifications.py` - Migration
- `app/services/email_service.py` - Updated processing logic
- `app/routers/webhooks.py` - Set delays in both Sonarr and Radarr
- `app/main.py` - Added background notification processor

---

## ⏳ Feature 2: Light/Dark Mode - TODO

### What Needs to Be Done:
1. **CSS Variables:**
   - Add CSS custom properties for colors
   - Create light and dark themes
   - Use `prefers-color-scheme` media query for system detection

2. **Theme Toggle:**
   - Add toggle button in dashboard header
   - Store preference in localStorage
   - Apply theme on page load

3. **Implementation:**
   ```css
   :root {
     --bg-primary: #1a1a2e;
     --bg-secondary: #16213e;
     --text-primary: #e4e4e4;
     /* ... */
   }
   
   [data-theme="light"] {
     --bg-primary: #ffffff;
     --bg-secondary: #f5f5f5;
     --text-primary: #333333;
     /* ... */
   }
   ```

4. **JavaScript:**
   ```javascript
   // Detect system theme
   const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
   // Load saved theme or use system
   const savedTheme = localStorage.getItem('theme') || systemTheme;
   document.documentElement.setAttribute('data-theme', savedTheme);
   ```

### Files to Modify:
- `app/static/admin.html` - Add CSS variables, theme toggle button, theme switcher JS

---

## ⏳ Feature 3: Config Page - TODO

### What Needs to Be Done:
1. **Backend API Endpoints:**
   - `GET /admin/config` - Get current configuration
   - `POST /admin/config` - Update configuration
   - Read from and write to `.env` file
   - Reload settings after save

2. **Frontend Config Page:**
   - New tab in dashboard: "⚙️ Settings"
   - Form with fields for:
     - SMTP Host, Port, From, User, Password
     - Jellyseerr URL, API Key
     - Sonarr URL, API Key
     - Radarr URL, API Key  
     - Plex URL, Token
   - Save button with confirmation
   - Warning: "Changing these may break integrations"

3. **Security Considerations:**
   - Mask passwords/API keys (show as ••••••••)
   - Require confirmation before saving
   - Validate inputs before saving
   - Optional: Add basic auth to config page

4. **Implementation:**
   ```python
   @router.get("/config")
   async def get_config():
       return {
           "smtp_host": os.getenv("SMTP_HOST"),
           "smtp_port": os.getenv("SMTP_PORT"),
           # ... etc
       }
   
   @router.post("/config")
   async def update_config(config: ConfigUpdate):
       # Write to .env file
       # Reload settings
       # Restart app components if needed
   ```

### Files to Create/Modify:
- `app/routers/admin.py` - Add config endpoints
- `app/static/admin.html` - Add Settings tab with form
- Need to handle `.env` file updates carefully

---

## 🚀 Deployment Instructions

### For Feature 1 (5-Minute Delay):
```bash
docker compose down
docker compose up -d --build
```

The migration will automatically run and add the `send_after` column.

### Testing Feature 1:
1. Request content in Jellyseerr
2. Wait for Sonarr/Radarr to download
3. Check logs: `docker compose logs -f api | grep "will send after"`
4. Wait 5 minutes
5. Email should arrive after the delay

---

## ⚠️ Important Notes

- Feature 1 is ready to deploy
- Features 2 and 3 need additional work
- All three can be deployed independently
- No breaking changes to existing functionality

---

## ✅ Feature 4: Maintenance Windows - COMPLETE (v1.5.0)

### What Was Done:
1. **Database Changes:**
   - Added `maintenance_windows` table with status lifecycle tracking
   - Created migration `007_add_maintenance_windows.py`

2. **Email Templates (4 types):**
   - 🔧 **Announcement** — yellow/warning theme, sent when window is scheduled
   - ⏰ **Reminder** — orange theme, sent ~1 hour before start
   - ✅ **Completion** — green theme, sent when maintenance ends
   - ℹ️ **Cancellation** — blue theme, sent if window is cancelled

3. **Background Worker:**
   - `maintenance_worker.py` runs every 60 seconds
   - Auto-sends reminder when within 60 minutes of start time
   - Auto-transitions status to "active" when start time is reached
   - Auto-sends completion email and marks "completed" when end time is reached

4. **Maintenance-Aware Workers:**
   - All 5 existing background workers check for active maintenance before each cycle
   - Shared `is_maintenance_active()` utility in `background/utils.py`
   - Workers skip their cycle during active maintenance (avoids noisy API errors)
   - Workers affected: notification processor, reconciliation, quality monitor, stuck download monitor, weekly summary

5. **API Endpoints (7 new):**
   - `GET /admin/maintenance` — list all windows
   - `POST /admin/maintenance` — create + send announcement
   - `PUT /admin/maintenance/{id}` — update/reschedule
   - `POST /admin/maintenance/{id}/complete` — early completion
   - `POST /admin/maintenance/{id}/cancel` — cancel + notify
   - `DELETE /admin/maintenance/{id}` — delete (no email)
   - `POST /admin/maintenance/{id}/send-reminder` — manual reminder

6. **Admin UI:**
   - New 🔧 Maintenance tab in dashboard
   - Schedule form with title, description, start/end datetime
   - Toggle to send/skip announcement email
   - Window list with status badges and email tracking icons
   - Action buttons: Remind, Complete, Cancel, Delete

7. **Security Dependencies:**
   - python-multipart 0.0.6 → 0.0.20 (fixes 3 High CVEs)
   - jinja2 3.1.3 → 3.1.6 (fixes 4 Moderate CVEs)

### How It Works:
```
Admin schedules maintenance window
        │
        ├─ Announcement email sent to all users (immediate)
        │
        ├─ ~60 min before start → Reminder email sent automatically
        │
        ├─ Start time reached → Status changes to "active"
        │   └─ All background workers pause (skip cycles)
        │
        ├─ End time reached → Completion email sent automatically
        │   └─ Status changes to "completed"
        │   └─ Background workers resume
        │
        └─ (Alternative) Admin clicks Complete early or Cancel
            └─ Appropriate email sent, workers resume
```

### Files Created:
- `app/background/maintenance_worker.py` — Background lifecycle worker
- `app/background/utils.py` — Shared `is_maintenance_active()` utility
- `alembic/versions/007_add_maintenance_windows.py` — Migration

### Files Modified:
- `app/database.py` — Added `MaintenanceWindow` model
- `app/services/email_service.py` — 4 email templates + `send_maintenance_email_to_all_users()`
- `app/routers/admin.py` — 7 maintenance API endpoints
- `app/main.py` — Registered maintenance worker + maintenance check in notification processor
- `app/static/admin.html` — New Maintenance tab with schedule form + window list
- `app/background/reconciliation.py` — Added maintenance check
- `app/background/quality_monitor.py` — Added maintenance check
- `app/background/stuck_monitor.py` — Added maintenance check
- `app/background/weekly_summary.py` — Added maintenance check
- `requirements.txt` — Updated python-multipart and jinja2

