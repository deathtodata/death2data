#!/usr/bin/env python3
"""
MRR DISPLAY SYSTEM
==================

1. Fetches MRR from Stripe
2. Saves to GitHub (public JSON file)
3. Any site can embed it via raw.githubusercontent.com

Run manually or on a cron:
    python3 mrr.py

Requires:
    STRIPE_SECRET_KEY=sk_live_xxx
    GITHUB_TOKEN=ghp_xxx
"""

import os
import json
import base64
from datetime import datetime
import urllib.request

# ============================================================================
# CONFIG
# ============================================================================

STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = "Soulfra/d2d"  # or deathtodata/d2d
GITHUB_FILE = "stats.json"   # Will be at raw.githubusercontent.com/Soulfra/d2d/main/stats.json

# ============================================================================
# STRIPE: GET MRR
# ============================================================================

def get_stripe_mrr():
    """Fetch MRR from Stripe API."""
    if not STRIPE_KEY:
        print("ERROR: Set STRIPE_SECRET_KEY")
        return None
    
    # Get active subscriptions
    url = "https://api.stripe.com/v1/subscriptions?status=active&limit=100"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {STRIPE_KEY}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            
            mrr = 0
            customer_count = 0
            
            for sub in data.get("data", []):
                customer_count += 1
                for item in sub.get("items", {}).get("data", []):
                    price = item.get("price", {})
                    amount = price.get("unit_amount", 0)  # in cents
                    interval = price.get("recurring", {}).get("interval", "month")
                    
                    # Convert to monthly
                    if interval == "year":
                        mrr += amount / 12
                    elif interval == "month":
                        mrr += amount
                    elif interval == "week":
                        mrr += amount * 4.33
                    elif interval == "day":
                        mrr += amount * 30
            
            return {
                "mrr_cents": int(mrr),
                "mrr_dollars": round(mrr / 100, 2),
                "customers": customer_count,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
    
    except Exception as e:
        print(f"Stripe error: {e}")
        return None

def get_stripe_customers():
    """Get customer count."""
    if not STRIPE_KEY:
        return 0
    
    url = "https://api.stripe.com/v1/customers?limit=1"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {STRIPE_KEY}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            # The total_count isn't directly available, but we can get it from subscriptions
            return None
    except:
        return None

# ============================================================================
# GITHUB: SAVE STATS
# ============================================================================

def save_to_github(stats):
    """Save stats.json to GitHub repo."""
    if not GITHUB_TOKEN:
        print("ERROR: Set GITHUB_TOKEN")
        return False
    
    content = json.dumps(stats, indent=2)
    content_b64 = base64.b64encode(content.encode()).decode()
    
    # First, try to get existing file SHA (needed for updates)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    
    sha = None
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            sha = data.get("sha")
    except:
        pass  # File doesn't exist yet
    
    # Create or update file
    payload = {
        "message": f"Update MRR stats - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha
    
    req = urllib.request.Request(url, method="PUT")
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps(payload).encode()
    
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✓ Saved to GitHub: {GITHUB_FILE}")
            return True
    except Exception as e:
        print(f"GitHub error: {e}")
        return False

# ============================================================================
# LOCAL: SAVE STATS (backup)
# ============================================================================

def save_local(stats):
    """Save stats locally as backup."""
    with open("stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved locally: stats.json")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("Fetching MRR from Stripe...")
    stats = get_stripe_mrr()
    
    if not stats:
        print("Failed to fetch stats")
        return
    
    print(f"""
╔════════════════════════════════════════╗
║  MRR: ${stats['mrr_dollars']}
║  Customers: {stats['customers']}
║  Updated: {stats['updated_at']}
╚════════════════════════════════════════╝
""")
    
    # Save locally
    save_local(stats)
    
    # Save to GitHub
    if GITHUB_TOKEN:
        save_to_github(stats)
    else:
        print("Skipping GitHub (no token)")
    
    print(f"""
EMBED ANYWHERE:
  Raw URL: https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FILE}
  
  <script>
    fetch('https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FILE}')
      .then(r => r.json())
      .then(d => document.getElementById('mrr').textContent = '$' + d.mrr_dollars);
  </script>
  <span id="mrr">Loading...</span>
""")

if __name__ == "__main__":
    main()
