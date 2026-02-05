# Smart Episode Batching (Option C) 🚀

## 🎯 How It Works

**The Problem:**
- Sonarr sends separate webhooks for each episode
- Users got 4 separate emails for 4 episodes
- Annoying spam instead of one clean notification

**The Solution:**
Smart hybrid batching that checks Sonarr's queue to intelligently group episodes!

## ⚙️ Implementation Details

### Step 1: Episode Downloads
When an episode downloads:
1. Webhook received from Sonarr
2. Notification created with:
   - `send_after` = now + 7 minutes (initial delay)
   - `series_id` = Sonarr series ID (for batching)
   - Status: `sent = False`

### Step 2: Smart Processing (Every 60 seconds)
Background task checks for notifications ready to send:

**For TV Episodes:**
1. Check if notification is ready (`send_after <= now`)
2. **Query Sonarr queue** - are more episodes downloading?
3. **Decision logic:**
   - ✅ **Queue has more episodes** → Extend delay by 3 minutes (max 15 min total)
   - ✅ **Queue is empty** → Batch and send now!
   - ✅ **Hit 15-min max wait** → Send anyway (don't wait forever)

**For Movies:**
- Send immediately when ready (no batching needed)

### Step 3: Batching
When ready to send:
1. Find ALL notifications for same user + same series that are ready
2. Combine into one email with all episodes listed
3. Mark all as sent
4. One clean email! 📧

## 📊 Example Timeline

**Scenario: 4 episodes of The Waterfront download**

```
Time    Event
00:00   Episode 5 downloads → Notification created (send_after: 00:07)
00:02   Episode 6 downloads → Notification created (send_after: 00:09)
00:03   Episode 7 downloads → Notification created (send_after: 00:10)
00:05   Episode 8 downloads → Notification created (send_after: 00:12)

00:07   Processor checks Episode 5 notification
        → Checks Sonarr queue
        → Finds Episodes 6,7,8 still downloading
        → Extends delay to 00:10

00:10   Processor checks again
        → Queue empty (all downloaded)
        → Batches Episodes 5,6,7,8
        → Sends ONE email with all 4 episodes! 🎉
```

**Total wait:** ~10 minutes  
**Emails sent:** 1 (instead of 4)

## 🎚️ Tunable Parameters

**Initial Delay:** 7 minutes (420 seconds)
- Gives 2 min batch window + 5 min Plex indexing
- Adjustable in `webhooks.py` line 154

**Extension Interval:** 3 minutes
- How much longer to wait when more episodes found
- Adjustable in `email_service.py` line 208

**Max Wait Time:** 15 minutes
- Absolute maximum to prevent infinite waiting
- Adjustable in `email_service.py` line 207

**Check Frequency:** 60 seconds
- How often the processor runs
- Adjustable in `main.py` line 39

## 🔍 What Gets Checked

**Sonarr Queue Statuses:**
- `downloading` - Episode actively downloading
- `queued` - Waiting to download
- `importPending` - Downloaded, waiting to import

**Ignored Statuses:**
- `completed` - Already done
- `failed` - Failed download
- `warning` - Has issues

## 📝 Logging

Watch it work in real-time:

```bash
docker compose logs -f api | grep -i "batch\|queue\|episode"
```

You'll see:
```
Found 4 notifications ready to process
Found 2 episodes in queue for series 123
Extended delay for New Episode: The Waterfront S01E05 - 2 episodes still in queue (waiting 3 more minutes)
...
Batching 4 episode notifications for user marlintodd@me.com
Processed 4 TV notifications, 0 movie notifications
```

## 🚀 Benefits

✅ **Smart** - Checks actual queue, not just guessing  
✅ **Fast** - Single episodes still ~7 minutes  
✅ **Clean** - Bulk downloads = one email  
✅ **Safe** - Max 15 min prevents infinite waiting  
✅ **Flexible** - All parameters tunable

## 🧪 Testing

Test with different scenarios:

**Single Episode:**
```
Episode downloads → Wait 7 min → Email sent
```

**Bulk Download (4 episodes):**
```
All 4 download quickly → Wait ~10 min → One email with all 4
```

**Slow Downloads:**
```
Episode 1 → Wait 7 min → Check queue → More coming → Wait
Episode 2-4 download → Queue empty → Send batched email
```

**Max Wait Scenario:**
```
Episodes keep downloading over 15 min → Send after 15 min regardless
```

## 🛠️ Database Changes

**New Migration:** `005_add_series_id_to_notifications.py`
- Adds `series_id` column to `notifications` table
- Stores Sonarr series ID for batching
- Nullable (movies don't have series_id)

**Auto-runs on startup!**

## 📈 Performance

- **API calls:** One Sonarr queue check per series per minute (lightweight)
- **Database queries:** Efficient - uses indexes on user_id + series_id
- **Email sending:** Drastically reduced (1 email instead of N emails)

## 🎉 Result

Instead of:
```
📧 New Episode: The Waterfront S01E05
📧 New Episode: The Waterfront S01E06  
📧 New Episode: The Waterfront S01E07
📧 New Episode: The Waterfront S01E08
```

Users get:
```
📧 New Episodes: The Waterfront (4 episodes)
   - S01E05
   - S01E06
   - S01E07
   - S01E08
```

Much better! 🎊
