# Debug Death2Data

**Your site is live. Here's how to fix things when they break.**

---

## Current Status

✅ Running: `https://manor-somewhere-generate-tip.trycloudflare.com`
✅ Laptop: `http://localhost:3000`
✅ Server: Python (PID shows in terminal)

---

## Quick Checks

### Is the server running?

```bash
lsof -i:3000
```

Should show: `Python` on port 3000

### Is the tunnel running?

```bash
ps aux | grep cloudflared
```

Should show: `cloudflared tunnel`

### What's the current URL?

Look at terminal where you ran cloudflared. It shows:
```
https://manor-somewhere-generate-tip.trycloudflare.com
```

---

## Common Problems

### Problem: Site won't load

**Check:**
```bash
curl http://localhost:3000
```

**If fails:** Server died
```bash
cd ~/Desktop/death2data
python3 -m http.server 3000
```

**If works:** Tunnel died
```bash
cloudflared tunnel --url http://localhost:3000
```

### Problem: Tunnel URL changed

This happens when cloudflared restarts. New random URL.

**Fix:** Use `RUN_FOREVER.sh` - keeps same URL longer

**Or:** Point DNS to tunnel (see below)

### Problem: Made changes, not showing

**Browser cache.** Hard refresh:
- Mac: `Cmd+Shift+R`
- Or open in Private/Incognito window

### Problem: Need to see errors

**Server logs:**
```bash
# If running in background
lsof -ti:3000  # Get PID
# Look at terminal where you started it
```

**Browser console:**
- Right click → Inspect → Console tab
- Shows JavaScript errors

---

## Point DNS (Make URL Permanent)

### Option 1: Cloudflare Tunnel Named

Instead of random URL, get permanent tunnel:

```bash
# One-time setup
cloudflared tunnel login
cloudflared tunnel create death2data
cloudflared tunnel route dns death2data death2data.com

# Then run
cloudflared tunnel run death2data
```

Now: `https://death2data.com` always works

### Option 2: CNAME to Random URL

Cloudflare Dashboard:
1. DNS → Add record
2. Type: CNAME
3. Name: `@`
4. Target: `manor-somewhere-generate-tip.trycloudflare.com`
5. Save

Now: death2data.com → loads the tunnel

**Problem:** If tunnel restarts, URL changes, DNS breaks

**Solution:** Use Option 1 (named tunnel)

---

## File Changes

Edit any file in `~/Desktop/death2data/`:

```bash
# index.html, tools.html, whatever
code ~/Desktop/death2data/index.html
```

Save → Refresh browser → Changes appear instantly

**No rebuild. No deploy. Just edit and reload.**

---

## Add Live Reload (Optional)

Install:
```bash
npm install -g live-server
```

Run instead of Python:
```bash
cd ~/Desktop/death2data
live-server --port=3000
```

Now: File changes = auto browser refresh

---

## Logs

### Server access log

Python shows every request:
```
127.0.0.1 - - [30/Jan/2026 08:56:32] "GET / HTTP/1.1" 200 -
```

### Error log

If Python crashes, you see stack trace in terminal

### Browser errors

F12 → Console → See JavaScript errors

---

## Stop Everything

```bash
# Kill server
lsof -ti:3000 | xargs kill -9

# Kill tunnel
pkill -f cloudflared
```

---

## Restart Everything

```bash
cd ~/Desktop/death2data
./RUN_FOREVER.sh
```

Server + tunnel both start, tunnel auto-restarts if it dies

---

## Test Stripe

If $1 signup isn't working:

1. Check Stripe Dashboard → Developers → API Keys
2. Make sure key is in your HTML (if using Stripe)
3. Check browser console for errors

**Current setup:** Just static HTML, no Stripe yet

---

## Check What's Using Credits (Netlify)

You're not using Netlify anymore, so fuck their credits.

But if you were:
- Netlify Dashboard → Usage
- Shows builds, bandwidth, function calls
- All bullshit charges

**You escaped this.** You're on your laptop now. Zero credits needed.

---

## Make It Boot on Startup (Mac)

Create: `~/Library/LaunchAgents/com.death2data.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.death2data</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/matthewmauer/Desktop/death2data/RUN_FOREVER.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.death2data.plist
```

Now: Mac boots → death2data starts automatically

---

## Simple Truth

**Your site works because:**
- Python serves files (port 3000)
- Cloudflared tunnels to internet
- No Netlify, no credits, no bullshit

**To debug:**
- Check if Python running (`lsof -i:3000`)
- Check if tunnel running (`ps aux | grep cloudflared`)
- Check browser console (F12)
- Restart if needed (`./RUN_FOREVER.sh`)

**That's it.** No complex deploy pipeline. Just files on your laptop.

---

**MIT License // Death2Data 2026**

Keep it simple. Keep it local. Keep it real.
