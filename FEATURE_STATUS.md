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

