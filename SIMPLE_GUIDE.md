# Death2Data - Simple Guide

**Your site is on your laptop. No paid hosting.**

---

## Run It (30 seconds)

```bash
cd ~/Desktop/death2data
./START.sh
```

Opens at: `http://localhost:3000`

---

## Expose to Internet (2 minutes)

### Install cloudflared (one time)

```bash
brew install cloudflare/cloudflare/cloudflared
```

### Run tunnel

```bash
cloudflared tunnel --url http://localhost:3000
```

You get: `https://random-words.trycloudflare.com`

**That URL is live. Share it. It's death2data.com until you point DNS.**

---

## Point Your Domain (optional)

When you want death2data.com to point here:

1. Cloudflare Dashboard → DNS
2. Add CNAME record:
   - Name: `@`
   - Target: `random-words.trycloudflare.com`
3. Wait 5 minutes
4. death2data.com works

---

## Stop It

```bash
lsof -ti:3000 | xargs kill -9
```

---

## What This Is

**No Netlify. No paid hosting. No complexity.**

Just:
- Python (built into Mac)
- Your laptop
- Cloudflare tunnel (free)

---

## The Files

```
death2data/
├── index.html      ← Main site
├── tools.html      ← Tools page
├── welcome.html    ← Welcome page
├── START.sh        ← Run this
└── sites/          ← Other pages
```

---

## Why This Works

**Netlify was:**
- Paid service
- Credit limits
- Blocked you

**This is:**
- Your laptop = you control it
- Python = already installed
- Cloudflare = free forever
- Works right now

---

## Make It Permanent (Later)

When you want it always on:

**Option 1: Keep laptop running**
```bash
# Run on startup
./START.sh
```

**Option 2: $5/mo VPS**
```bash
# On Hetzner/DigitalOcean
git clone <your-repo>
cd death2data
python3 -m http.server 3000
```

**Option 3: Make GitHub repo public**
- Free GitHub Pages
- Works instantly
- No server needed

---

## Current Status

✅ Site exists (index.html, tools.html, etc.)
✅ Runs on laptop (localhost:3000)
✅ Can expose to internet (cloudflared)
❌ Not pointed to death2data.com yet (DNS)

**But it works. Share the cloudflare URL for now.**

---

## No Database Needed

death2data.com is static HTML. No backend. No database.

**SQLite? Postgres?** Not for this site.

Those are for:
- User accounts (later)
- Fortune 0 (if you add that)
- API stuff (future)

**Right now:** Just HTML files. That's it.

---

## Sanitize (Delete Confusion)

Too many folders? Delete these:

```bash
# Keep
~/Desktop/death2data/         ← The real site
~/Desktop/D2D-ACTIVE/fortune0/ ← F0 templates

# Delete (noise)
~/Desktop/D2D-ACTIVE/tools/
~/Desktop/D2D-ACTIVE/infrastructure/
~/Desktop/D2D-ACTIVE/ship/
~/Downloads/*.zip (all the old versions)
```

**Only keep:**
1. death2data (the actual site)
2. fortune0 (templates for later)

Everything else is just files we generated trying stuff.

---

## The Truth

**What's real:**
- death2data.com site (~/Desktop/death2data/)
- Your laptop
- Python
- This works

**What's noise:**
- D2D-ACTIVE complexity
- SQLite/Postgres confusion
- Matrix/other systems
- Downloads folder chaos

**What to do:**
```bash
./START.sh
```

Share the cloudflare URL. Done.

---

**MIT License // Death2Data 2026**

No paid hosting. No complexity. Just ship it.
