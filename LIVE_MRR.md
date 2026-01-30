# LIVE MRR DISPLAY SYSTEM
# =======================

## The Goal

Show your real Stripe MRR across ALL your sites.
Make it feel like a live game - everyone sees the score.


## How It Works

```
STRIPE ──→ mrr.py ──→ GitHub (stats.json) ──→ Any Website
           (cron)      (raw.githubusercontent)   (fetch + display)
```

1. mrr.py fetches your real MRR from Stripe API
2. Saves it to a JSON file on GitHub (public)
3. Any site can fetch that JSON and display it


## Files

mrr.py      - Fetches Stripe data, saves to GitHub
widget.js   - Embeddable web component
widget.html - Example embed code
stats.json  - The data file (created by mrr.py)


## Setup

### Step 1: Create stats.json in your repo

In your GitHub repo (Soulfra/d2d or deathtodata/d2d), create:

```json
{
  "mrr_cents": 600,
  "mrr_dollars": 6.00,
  "customers": 6,
  "updated_at": "2026-01-30T15:00:00Z"
}
```

This is the file that will be publicly readable at:
https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/stats.json


### Step 2: Set up environment variables

```bash
export STRIPE_SECRET_KEY="sk_live_xxx"  # From Stripe Dashboard > Developers > API keys
export GITHUB_TOKEN="ghp_xxx"           # From GitHub > Settings > Developer settings > Personal access tokens
```

For the GitHub token:
1. Go to github.com/settings/tokens
2. Generate new token (classic)
3. Select "repo" scope
4. Copy the token


### Step 3: Run mrr.py

```bash
python3 mrr.py
```

This will:
- Fetch your active subscriptions from Stripe
- Calculate MRR
- Update stats.json in your GitHub repo


### Step 4: Automate with cron (optional)

Run every hour:
```bash
crontab -e

# Add this line:
0 * * * * cd /path/to/mrr.py && STRIPE_SECRET_KEY=xxx GITHUB_TOKEN=xxx python3 mrr.py
```

Or use GitHub Actions (see below).


## Embed on Any Site

### Simple (just the numbers)

```html
<span id="mrr">$0</span> MRR

<script>
fetch('https://raw.githubusercontent.com/Soulfra/d2d/main/stats.json')
  .then(r => r.json())
  .then(d => document.getElementById('mrr').textContent = '$' + d.mrr_dollars);
</script>
```


### Widget (styled component)

```html
<script src="https://raw.githubusercontent.com/Soulfra/d2d/main/widget.js"></script>
<d2d-stats></d2d-stats>
```

Options:
```html
<d2d-stats theme="light"></d2d-stats>
<d2d-stats theme="dark"></d2d-stats>
<d2d-stats show="mrr"></d2d-stats>
<d2d-stats show="customers"></d2d-stats>
<d2d-stats show="mrr,customers"></d2d-stats>
```


### Full Scoreboard

```html
<div style="background:#000;color:#0f0;padding:20px;font-family:monospace">
  <div style="font-size:32px">$<span id="mrr">0</span></div>
  <div style="font-size:12px;color:#666">MONTHLY RECURRING REVENUE</div>
  <div style="margin-top:15px">
    <span id="customers">0</span> paying members
  </div>
</div>

<script>
fetch('https://raw.githubusercontent.com/Soulfra/d2d/main/stats.json')
  .then(r => r.json())
  .then(d => {
    document.getElementById('mrr').textContent = d.mrr_dollars;
    document.getElementById('customers').textContent = d.customers;
  });
</script>
```


## GitHub Actions (auto-update every hour)

Create `.github/workflows/update-mrr.yml`:

```yaml
name: Update MRR Stats

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:      # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Fetch and update stats
        env:
          STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python mrr.py
      
      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add stats.json
          git diff --staged --quiet || git commit -m "Update MRR stats"
          git push
```

Add secrets in GitHub:
1. Go to repo > Settings > Secrets > Actions
2. Add STRIPE_SECRET_KEY
3. GITHUB_TOKEN is automatic


## Where to Show It

- death2data.com (main site)
- fortune0.com (equity page)
- finishthisidea.com (footer)
- finishthisrepo.com (footer)
- Your GitHub README
- Your Twitter/X bio (manually update)
- Anywhere else


## The "Live Game" Vibe

This makes your business feel like a multiplayer game:
- Everyone can see the score (MRR)
- Everyone can see the player count (customers)
- Progress is visible and shared
- Joining feels like joining a team

You can extend this to show:
- Total contributions
- Active projects
- Code commits
- Whatever metrics matter


## Manual Update (if automation fails)

Just edit stats.json directly on GitHub:

```json
{
  "mrr_cents": 600,
  "mrr_dollars": 6.00,
  "customers": 6,
  "updated_at": "2026-01-30T15:00:00Z"
}
```

The widgets will show whatever's in this file.


## Troubleshooting

### "Failed to fetch" in browser console
- Check the raw URL is correct
- Make sure stats.json exists in your repo
- Make sure the repo is public (or use a token)

### mrr.py fails with Stripe error
- Check STRIPE_SECRET_KEY is set
- Check it's the live key (sk_live_) not test (sk_test_)
- Check you have active subscriptions

### GitHub update fails
- Check GITHUB_TOKEN has "repo" scope
- Check the repo name in mrr.py is correct
- Check you have push access to the repo


## Stats.json Schema

```json
{
  "mrr_cents": 600,        // Integer, MRR in cents
  "mrr_dollars": 6.00,     // Float, MRR in dollars
  "customers": 6,          // Integer, active subscribers
  "updated_at": "...",     // ISO timestamp
  
  // Optional extras you could add:
  "total_revenue": 50.00,  // All-time revenue
  "churn_rate": 0.05,      // Monthly churn
  "contributors": 3,       // F0 contributors
  "commits_today": 12      // GitHub activity
}
```


## That's It

1. Run mrr.py (or set up cron/GitHub Actions)
2. Embed the widget wherever
3. Everyone sees the live score
