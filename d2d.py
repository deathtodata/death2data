#!/usr/bin/env python3
"""
D2D - ONE APP THAT ACTUALLY WORKS
=================================

ONE file. ONE database. Everything connected.

Features:
- Auth (signup, login)
- Search (SearXNG)
- Save results
- Register content (DMCA protection)
- Export (JSON/Markdown/CSV)
- Delete account (GDPR)

Run:
    python3 d2d.py

Open:
    http://localhost:8000
"""

import sqlite3, secrets, hashlib, json, os, uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, urlencode
import urllib.request

DB = "d2d.db"
PORT = int(os.environ.get("PORT", 5052))  # Changed to 5052 to avoid conflict
SEARXNG = ["https://searx.be", "https://search.sapti.me"]
VERSION = "v1.3.0"

# Stripe config
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.environ.get("STRIPE_PRICE_ID", "")
DOMAIN = os.environ.get("DOMAIN", f"http://localhost:{PORT}")

# Tier limits (searches/day, saves/month)
TIERS = {
    'free': {'searches': 20, 'saves': 50, 'registrations': 10},
    'member': {'searches': 1000, 'saves': 10000, 'registrations': 1000}
}

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            token_hash TEXT NOT NULL,
            stripe_customer_id TEXT,
            tier TEXT DEFAULT 'free',
            cohort TEXT DEFAULT 'A',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS saved (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT, url TEXT, snippet TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT DEFAULT 'other',
            content_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            date TEXT NOT NULL,
            count INTEGER DEFAULT 1,
            UNIQUE(user_id, action, date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT UNIQUE NOT NULL,
            features TEXT NOT NULL,
            value_impact TEXT,
            released_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feature_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature_name TEXT NOT NULL,
            cohort TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            UNIQUE(feature_name, cohort)
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            category TEXT DEFAULT 'other',
            score INTEGER DEFAULT 50,
            stars INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS project_stars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, project_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# USAGE TRACKING
# ============================================================================

def log_usage(user_id, action):
    """Track usage for tier limits"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = db()
    try:
        conn.execute("INSERT INTO usage (user_id, action, date, count) VALUES (?, ?, ?, 1)",
                    (user_id, action, today))
    except sqlite3.IntegrityError:
        conn.execute("UPDATE usage SET count = count + 1 WHERE user_id = ? AND action = ? AND date = ?",
                    (user_id, action, today))
    conn.commit()
    conn.close()

def check_limit(user_id, action, user_tier):
    """Check if user has hit tier limit"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = db()
    row = conn.execute("SELECT count FROM usage WHERE user_id = ? AND action = ? AND date = ?",
                      (user_id, action, today)).fetchone()
    conn.close()

    count = row['count'] if row else 0
    limit = TIERS[user_tier][action]

    if count >= limit:
        return False, f"Limit reached ({count}/{limit}). <a href='/upgrade'>Upgrade</a> for more."
    return True, None

def get_usage_stats(user_id):
    """Get usage stats for current user"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = db()
    rows = conn.execute("SELECT action, count FROM usage WHERE user_id = ? AND date = ?",
                       (user_id, today)).fetchall()
    conn.close()
    stats = {row['action']: row['count'] for row in rows}
    return stats

# ============================================================================
# VERSIONING & CHANGELOG
# ============================================================================

def get_versions():
    """Get all versions for changelog"""
    conn = db()
    rows = conn.execute("SELECT * FROM versions ORDER BY released_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_version(version, features, value_impact):
    """Add a new version to changelog"""
    conn = db()
    try:
        conn.execute("INSERT INTO versions (version, features, value_impact) VALUES (?, ?, ?)",
                    (version, features, value_impact))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Version already exists
    conn.close()

# ============================================================================
# A/B TESTING
# ============================================================================

def is_feature_enabled(feature_name, cohort):
    """Check if feature is enabled for user's cohort"""
    conn = db()
    row = conn.execute("SELECT enabled FROM feature_flags WHERE feature_name = ? AND cohort = ?",
                      (feature_name, cohort)).fetchone()
    conn.close()
    return bool(row['enabled']) if row else True  # Default enabled

def set_feature_flag(feature_name, cohort, enabled):
    """Enable/disable feature for specific cohort"""
    conn = db()
    try:
        conn.execute("INSERT INTO feature_flags (feature_name, cohort, enabled) VALUES (?, ?, ?)",
                    (feature_name, cohort, enabled))
    except sqlite3.IntegrityError:
        conn.execute("UPDATE feature_flags SET enabled = ? WHERE feature_name = ? AND cohort = ?",
                    (enabled, feature_name, cohort))
    conn.commit()
    conn.close()

# ============================================================================
# GOLDEN TICKET (PROJECT DISCOVERY)
# ============================================================================

def get_projects():
    """Get all active projects"""
    conn = db()
    rows = conn.execute("SELECT * FROM projects WHERE status='active' ORDER BY score DESC, stars DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_project(name, url, description, category, score=50):
    """Add a new project"""
    conn = db()
    conn.execute("INSERT INTO projects (name, url, description, category, score) VALUES (?, ?, ?, ?, ?)",
                (name, url, description, category, score))
    conn.commit()
    conn.close()

def star_project(user_id, project_id):
    """User stars a project"""
    conn = db()
    try:
        conn.execute("INSERT INTO project_stars (user_id, project_id) VALUES (?, ?)",
                    (user_id, project_id))
        conn.execute("UPDATE projects SET stars = stars + 1 WHERE id = ?", (project_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already starred
    conn.close()

def get_user_stars(user_id):
    """Get project IDs user has starred"""
    conn = db()
    rows = conn.execute("SELECT project_id FROM project_stars WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return {r['project_id'] for r in rows}

# ============================================================================
# AUTH
# ============================================================================

def signup(email, stripe_customer_id=None):
    """Create user with email and optional Stripe customer ID"""
    conn = db()
    token = secrets.token_hex(32)
    try:
        conn.execute("INSERT INTO users (email, token_hash, stripe_customer_id) VALUES (?, ?, ?)",
                    (email, hashlib.sha256(token.encode()).hexdigest(), stripe_customer_id))
        conn.commit()
        conn.close()
        return token, None
    except sqlite3.IntegrityError:
        # User exists, update token and customer ID
        conn.execute("UPDATE users SET token_hash = ?, stripe_customer_id = ? WHERE email = ?",
                    (hashlib.sha256(token.encode()).hexdigest(), stripe_customer_id, email))
        conn.commit()
        conn.close()
        return token, None

def login(token):
    if not token: return None
    conn = db()
    user = conn.execute("SELECT * FROM users WHERE token_hash = ?",
                       (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    conn.close()
    return dict(user) if user else None

# ============================================================================
# STRIPE
# ============================================================================

def create_checkout_session():
    """Create Stripe Checkout Session for $1/month"""
    if not STRIPE_KEY or not STRIPE_PRICE_ID:
        return None, "Stripe not configured"

    data = {
        "mode": "subscription",
        "payment_method_types[]": "card",
        "line_items[0][price]": STRIPE_PRICE_ID,
        "line_items[0][quantity]": "1",
        "success_url": f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{DOMAIN}/",
    }

    body = "&".join(f"{k}={v}" for k, v in data.items())

    req = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=body.encode(),
        headers={
            "Authorization": f"Bearer {STRIPE_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    )

    try:
        with urllib.request.urlopen(req) as resp:
            session = json.loads(resp.read().decode())
            return session.get("url"), None
    except urllib.error.HTTPError as e:
        error = json.loads(e.read().decode())
        return None, error.get("error", {}).get("message", "Stripe error")

def get_checkout_session(session_id):
    """Get details of a completed checkout"""
    if not STRIPE_KEY:
        return None

    req = urllib.request.Request(
        f"https://api.stripe.com/v1/checkout/sessions/{session_id}",
        headers={"Authorization": f"Bearer {STRIPE_KEY}"}
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except:
        return None

# ============================================================================
# SEARCH
# ============================================================================

def search(query, user_id=None, user_tier='free'):
    if not query: return []

    # Check usage limit
    if user_id:
        ok, err = check_limit(user_id, 'searches', user_tier)
        if not ok:
            return {'error': err}

    for instance in SEARXNG:
        try:
            url = f"{instance}/search?{urlencode({'q': query, 'format': 'json'})}"
            req = urllib.request.Request(url, headers={"User-Agent": "D2D/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                results = json.loads(r.read()).get("results", [])[:15]

                # Log successful search
                if user_id:
                    log_usage(user_id, 'searches')

                return results
        except: continue
    return []

# ============================================================================
# SAVED
# ============================================================================

def save(user_id, title, url, snippet, user_tier='free'):
    # Check limit
    ok, err = check_limit(user_id, 'saves', user_tier)
    if not ok:
        return err

    conn = db()
    conn.execute("INSERT INTO saved (user_id, title, url, snippet) VALUES (?, ?, ?, ?)",
                (user_id, title, url, snippet))
    conn.commit()
    conn.close()

    log_usage(user_id, 'saves')
    return None

def get_saved(user_id):
    conn = db()
    rows = conn.execute("SELECT * FROM saved WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_saved(user_id, sid):
    conn = db()
    conn.execute("DELETE FROM saved WHERE id = ? AND user_id = ?", (sid, user_id))
    conn.commit()
    conn.close()

# ============================================================================
# CONTENT REGISTRY
# ============================================================================

def register(user_id, title, description, ctype, user_tier='free'):
    # Check limit
    ok, err = check_limit(user_id, 'registrations', user_tier)
    if not ok:
        return None, err

    conn = db()
    uid = str(uuid.uuid4())
    chash = hashlib.sha256(f"{title}{description}{datetime.utcnow()}".encode()).hexdigest()
    conn.execute("INSERT INTO content (uuid, user_id, title, description, content_type, content_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (uid, user_id, title, description, ctype, chash))
    conn.commit()
    conn.close()

    log_usage(user_id, 'registrations')
    return uid, None

def get_content(user_id):
    conn = db()
    rows = conn.execute("SELECT * FROM content WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_by_uuid(uid):
    conn = db()
    row = conn.execute("SELECT * FROM content WHERE uuid = ?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None

# ============================================================================
# EXPORT
# ============================================================================

def export_json(user_id):
    return json.dumps({"saved": get_saved(user_id), "content": get_content(user_id)}, indent=2, default=str)

def export_md(user_id):
    md = "# Export\n\n## Saved\n\n"
    for s in get_saved(user_id):
        md += f"- [{s['title']}]({s['url']})\n"
    md += "\n## Content\n\n"
    for c in get_content(user_id):
        md += f"- {c['title']} ({c['uuid']})\n"
    return md

def delete_all(user_id):
    conn = db()
    conn.execute("DELETE FROM saved WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM content WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# ============================================================================
# HTML
# ============================================================================

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,sans-serif;background:#0a0a0a;color:#ddd;max-width:800px;margin:0 auto;padding:20px}
header{display:flex;justify-content:space-between;align-items:center;padding:15px 0;border-bottom:1px solid #222;margin-bottom:20px}
header h1{font-size:18px;color:#0f0}
nav a{color:#666;margin-left:15px;text-decoration:none;font-size:14px}
nav a:hover{color:#fff}
h2{font-size:14px;color:#888;margin:25px 0 15px;border-bottom:1px solid #222;padding-bottom:10px}
.search{display:flex;gap:10px;margin-bottom:20px}
.search input{flex:1;background:#111;border:1px solid #333;color:#fff;padding:12px;font-size:15px}
.search button{background:#0f0;color:#000;border:none;padding:12px 25px;font-weight:bold;cursor:pointer}
.card{background:#111;border:1px solid #222;padding:15px;margin-bottom:10px}
.card:hover{border-color:#333}
.card h3{font-size:14px;color:#8ab4f8;margin-bottom:5px}
.card p{font-size:13px;color:#888}
.card small{font-size:11px;color:#555}
.card a{color:#0f0;font-size:12px;margin-right:15px}
form.box{background:#111;border:1px solid #222;padding:20px;margin-bottom:20px}
form.box input,form.box textarea,form.box select{width:100%;background:#000;border:1px solid #333;color:#fff;padding:10px;margin-bottom:10px;font-family:inherit}
form.box button{background:#0f0;color:#000;border:none;padding:12px 20px;font-weight:bold;cursor:pointer}
form.box button.red{background:#f00;color:#fff}
.uuid{font-family:monospace;font-size:11px;color:#0f0;background:#001100;padding:2px 6px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:20px}
.stat{background:#111;padding:20px;text-align:center;border:1px solid #222}
.stat b{display:block;font-size:24px;color:#0f0}
.stat span{font-size:11px;color:#666}
.empty{color:#555;text-align:center;padding:30px}
footer{margin-top:40px;padding:20px 0;border-top:1px solid #222;text-align:center;font-size:12px;color:#444}
.result{padding:15px 0;border-bottom:1px solid #1a1a1a}
.result h3 a{color:#8ab4f8;text-decoration:none}
.result .url{color:#666;font-size:12px}
.result .snippet{color:#999;font-size:13px;margin:5px 0}
.result button{background:#222;color:#888;border:none;padding:4px 10px;font-size:11px;cursor:pointer}
"""

def html(title, body, user=None):
    nav = '<a href="/search">Search</a><a href="/saved">Saved</a><a href="/content">Content</a><a href="/discover">Discover</a><a href="/changelog">Changelog</a><a href="/export">Export</a><a href="/logout">Logout</a>' if user else '<a href="/">Login</a><a href="/stats">Stats</a><a href="/changelog">Changelog</a>'
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><style>{CSS}</style></head><body>
<header><h1>D2D <span style="color:#666;font-size:12px">{VERSION}</span></h1><nav>{nav}</nav></header>
{body}
<footer>Death2Data · Port {PORT} · {VERSION}</footer>
</body></html>"""

# ============================================================================
# PAGES
# ============================================================================

def page_changelog():
    """Show changelog with version history"""
    versions = get_versions()
    h = "<h2>Changelog</h2>"

    if not versions:
        h += '<div class="empty">No versions yet</div>'
    else:
        for v in versions:
            h += f"""<div class="card" style="border-color:#0f0">
                <h3>{v['version']}</h3>
                <p><b>Features:</b> {v['features']}</p>
                <p><b>Value:</b> {v['value_impact'] or 'N/A'}</p>
                <small>{v['released_at'][:10]}</small>
            </div>"""

    return h

def page_analytics(user):
    """Analytics dashboard for admins"""
    # Get all users stats
    conn = db()
    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()['c']
    free_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE tier='free'").fetchone()['c']
    member_users = conn.execute("SELECT COUNT(*) as c FROM users WHERE tier='member'").fetchone()['c']

    # Get today's usage
    today = datetime.now().strftime('%Y-%m-%d')
    today_searches = conn.execute("SELECT SUM(count) as c FROM usage WHERE action='searches' AND date=?", (today,)).fetchone()['c'] or 0
    today_saves = conn.execute("SELECT SUM(count) as c FROM usage WHERE action='saves' AND date=?", (today,)).fetchone()['c'] or 0
    today_regs = conn.execute("SELECT SUM(count) as c FROM usage WHERE action='registrations' AND date=?", (today,)).fetchone()['c'] or 0

    # Cohort breakdown
    cohort_a = conn.execute("SELECT COUNT(*) as c FROM users WHERE cohort='A'").fetchone()['c']
    cohort_b = conn.execute("SELECT COUNT(*) as c FROM users WHERE cohort='B'").fetchone()['c']

    conn.close()

    return f"""
    <h2>Analytics Dashboard</h2>
    <div class="stats">
        <div class="stat"><b>{total_users}</b><span>Total Users</span></div>
        <div class="stat"><b>{free_users}</b><span>Free Tier</span></div>
        <div class="stat"><b>{member_users}</b><span>Members ($1/mo)</span></div>
    </div>
    <h2>Today's Usage</h2>
    <div class="stats">
        <div class="stat"><b>{today_searches}</b><span>Searches</span></div>
        <div class="stat"><b>{today_saves}</b><span>Saves</span></div>
        <div class="stat"><b>{today_regs}</b><span>Registrations</span></div>
    </div>
    <h2>A/B Testing</h2>
    <div class="stats">
        <div class="stat"><b>{cohort_a}</b><span>Cohort A</span></div>
        <div class="stat"><b>{cohort_b}</b><span>Cohort B</span></div>
    </div>
    """

def page_discover(user):
    """Golden Ticket - Project Discovery"""
    projects = get_projects()
    user_stars = get_user_stars(user['id']) if user else set()

    h = "<h2>Golden Ticket: Project Discovery</h2>"
    h += '<p style="color:#888;margin-bottom:20px">Star projects you think will succeed. Early stars = bragging rights.</p>'

    if not projects:
        h += '<div class="empty">No projects yet. Check back soon!</div>'
    else:
        for p in projects:
            starred = p['id'] in user_stars
            star_btn = f'<span style="color:#666">★ {p["stars"]}</span>' if starred else f'<form method="POST" action="/star" style="display:inline"><input type="hidden" name="project_id" value="{p["id"]}"><button style="background:none;border:none;color:#0f0;cursor:pointer;font-size:14px">☆ Star ({p["stars"]})</button></form>'

            h += f"""<div class="card">
                <h3>{p['name']}</h3>
                <p>{p['description']}</p>
                <small style="color:#666">Score: {p['score']}/100 · {p['category']}</small><br>
                <a href="{p['url']}" target="_blank" style="color:#0f0;margin-right:15px">Visit</a>
                {star_btn}
            </div>"""

    return h

def page_public_stats():
    """Public stats page - no login required"""
    try:
        with open("stats.json") as f:
            stats = json.load(f)
    except:
        stats = {"mrr_dollars": 0, "customers": 0, "searches_today": 0, "projects_tracked": 0}

    return f"""
    <h2>Live Stats</h2>
    <p style="color:#888;margin-bottom:20px">Open startup transparency. Updated hourly.</p>

    <div class="stats">
        <div class="stat"><b>${stats.get('mrr_dollars', 0)}</b><span>MRR</span></div>
        <div class="stat"><b>{stats.get('customers', 0)}</b><span>Paying Members</span></div>
        <div class="stat"><b>{stats.get('searches_today', 0)}</b><span>Searches Today</span></div>
    </div>

    <div class="stats">
        <div class="stat"><b>{stats.get('registrations_total', 0)}</b><span>Content Registered</span></div>
        <div class="stat"><b>{stats.get('projects_tracked', 0)}</b><span>Projects Tracked</span></div>
    </div>

    <p style="margin-top:30px;color:#666;font-size:13px">
        Want to contribute? <a href="/" style="color:#0f0">Join for $1/month</a>
    </p>
    """

def page_home(user):
    if user:
        s, c = len(get_saved(user['id'])), len(get_content(user['id']))
        usage = get_usage_stats(user['id'])
        tier = user['tier']
        limits = TIERS[tier]

        searches_used = usage.get('searches', 0)
        saves_used = usage.get('saves', 0)
        regs_used = usage.get('registrations', 0)

        return f"""
        <div class="stats">
            <div class="stat"><b>{s}</b><span>Saved</span></div>
            <div class="stat"><b>{c}</b><span>Content</span></div>
            <div class="stat"><b>{user['tier']}</b><span>Tier</span></div>
        </div>
        <div class="stats">
            <div class="stat"><b>{searches_used}/{limits['searches']}</b><span>Searches Today</span></div>
            <div class="stat"><b>{saves_used}/{limits['saves']}</b><span>Saves This Month</span></div>
            <div class="stat"><b>{regs_used}/{limits['registrations']}</b><span>Registrations</span></div>
        </div>
        <form action="/search" method="GET" class="search">
            <input type="text" name="q" placeholder="Search..." autofocus>
            <button>Search</button>
        </form>
        """
    stripe_btn = '<div class="card" style="text-align:center;background:#001100;border-color:#0f0"><p style="margin-bottom:15px;font-size:24px;color:#0f0">$1<span style="font-size:14px;color:#666">/month</span></p><a href="/checkout" style="background:#0f0;color:#000;padding:12px 30px;text-decoration:none;font-weight:bold;display:inline-block">GET ACCESS</a></div>' if STRIPE_KEY and STRIPE_PRICE_ID else ''

    return f"""
    <h2>Death2Data</h2>
    <p style="color:#888;margin-bottom:20px">Search privately. Save what matters. Own your data.</p>

    {stripe_btn}

    <h2 style="margin-top:30px">Free Sign Up</h2>
    <form class="box" method="POST" action="/signup">
        <input type="email" name="email" placeholder="Email" required>
        <button>Sign Up Free</button>
    </form>
    <p style="color:#555;font-size:13px">Have a token? <a href="/login" style="color:#0f0">Login</a></p>
    """

def page_search(user, q, results):
    r_html = ""

    # Check if results is an error dict
    if isinstance(results, dict) and 'error' in results:
        r_html = f'<div class="empty" style="color:#f66">{results["error"]}</div>'
    elif results:
        for r in results:
            t, u, s = r.get('title',''), r.get('url',''), r.get('content','')[:200]
            r_html += f"""<div class="result">
                <h3><a href="{u}" target="_blank">{t}</a></h3>
                <div class="url">{u[:60]}</div>
                <div class="snippet">{s}</div>
                <form method="POST" action="/save" style="display:inline">
                    <input type="hidden" name="title" value="{t.replace('"','&quot;')}">
                    <input type="hidden" name="url" value="{u}">
                    <input type="hidden" name="snippet" value="{s.replace('"','&quot;')}">
                    <input type="hidden" name="q" value="{q}">
                    <button>+ Save</button>
                </form>
            </div>"""
    elif q:
        r_html = '<div class="empty">No results</div>'

    return f"""
    <form action="/search" method="GET" class="search">
        <input type="text" name="q" value="{q}" placeholder="Search..." autofocus>
        <button>Search</button>
    </form>
    {r_html}
    """

def page_saved(user):
    items = get_saved(user['id'])
    h = ""
    for s in items:
        h += f"""<div class="card">
            <h3>{s['title']}</h3>
            <p>{s['snippet'][:100] if s['snippet'] else ''}...</p>
            <small>{s['created_at'][:10]}</small><br>
            <a href="{s['url']}" target="_blank">Open</a>
            <form method="POST" action="/saved/delete" style="display:inline">
                <input type="hidden" name="id" value="{s['id']}">
                <button style="background:none;border:none;color:#f66;cursor:pointer;font-size:12px">Delete</button>
            </form>
        </div>"""
    return f"<h2>Saved ({len(items)})</h2>{h or '<div class=\"empty\">Nothing saved</div>'}"

def page_content(user):
    items = get_content(user['id'])
    h = ""
    for c in items:
        h += f"""<div class="card">
            <h3>{c['title']}</h3>
            <span class="uuid">{c['uuid']}</span>
            <br><small>{c['content_type']} · {c['created_at'][:10]}</small>
            <br><a href="/verify/{c['uuid']}">Verify</a>
        </div>"""
    return f"""
    <h2>Registered Content ({len(items)})</h2>
    <form class="box" method="POST" action="/register">
        <input type="text" name="title" placeholder="Title" required>
        <textarea name="description" placeholder="Description" rows="2"></textarea>
        <select name="type">
            <option value="article">Article</option>
            <option value="image">Image</option>
            <option value="video">Video</option>
            <option value="code">Code</option>
            <option value="other">Other</option>
        </select>
        <button>Register</button>
    </form>
    {h or '<div class=\"empty\">Nothing registered</div>'}
    """

def page_verify(uid):
    c = get_by_uuid(uid)
    if not c: return '<div class="empty">Not found</div>'
    return f"""
    <div class="card" style="border-color:#0f0;background:#001100">
        <h3 style="color:#0f0">✓ VERIFIED</h3>
        <p><b>{c['title']}</b></p>
        <p>{c['description'] or ''}</p>
        <br><span class="uuid">{c['uuid']}</span>
        <br><small>Hash: {c['content_hash']}</small>
        <br><small>Registered: {c['created_at']}</small>
    </div>
    """

def page_export(user):
    return """
    <h2>Export</h2>
    <div class="card"><a href="/export?f=json">Download JSON</a></div>
    <div class="card"><a href="/export?f=md">Download Markdown</a></div>
    <h2>Delete Account</h2>
    <form class="box" method="POST" action="/delete" onsubmit="return confirm('Delete everything?')">
        <button class="red">Delete All My Data</button>
    </form>
    """

# ============================================================================
# SERVER
# ============================================================================

class H(BaseHTTPRequestHandler):
    def token(self):
        for p in self.headers.get("Cookie","").split(";"):
            if "token=" in p: return p.split("=")[1].strip()
        return None
    
    def send(self, body, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", "text/html")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers()
        self.wfile.write(body.encode())
    
    def file(self, data, mime, name):
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Disposition", f"attachment; filename={name}")
        self.end_headers()
        self.wfile.write(data.encode())
    
    def redir(self, url, cookie=None):
        self.send_response(303)
        self.send_header("Location", url)
        if cookie: self.send_header("Set-Cookie", cookie)
        self.end_headers()
    
    def do_GET(self):
        p = urlparse(self.path)
        path, params = p.path, parse_qs(p.query)
        user = login(self.token())

        if path == "/": return self.send(html("Home", page_home(user), user))
        if path == "/login": return self.send(html("Login", '<h2>Login</h2><form class="box" method="POST" action="/login"><input name="token" placeholder="Token" required><button>Login</button></form>'))
        if path == "/logout": return self.redir("/", "token=; Path=/; Max-Age=0")
        if path == "/changelog": return self.send(html("Changelog", page_changelog(), user))
        if path == "/stats": return self.send(html("Stats", page_public_stats(), user))
        if path.startswith("/verify/"): return self.send(html("Verify", page_verify(path.split("/")[-1]), user))

        # Stripe checkout
        if path == "/checkout":
            url, error = create_checkout_session()
            if error:
                return self.send(html("Error", f'<div class="empty" style="color:#f66">{error}</div><a href="/" style="color:#0f0">Back</a>', user))
            return self.redir(url)

        # Stripe success
        if path == "/success":
            session_id = params.get("session_id", [None])[0]
            if not session_id:
                return self.redir("/")

            session = get_checkout_session(session_id)
            if not session:
                return self.send(html("Error", '<div class="empty" style="color:#f66">Invalid session</div><a href="/" style="color:#0f0">Back</a>', user))

            email = session.get("customer_details", {}).get("email")
            customer_id = session.get("customer")
            token, _ = signup(email, customer_id)

            return self.send(html("Success", f'<h2>You\'re In!</h2><p>Save this token:</p><pre style="color:#0f0;background:#000;padding:15px;font-family:monospace">{token}</pre><p><a href="/" style="color:#0f0">Continue</a></p>'), headers={"Set-Cookie": f"token={token}; Path=/; HttpOnly"})

        if not user: return self.redir("/")

        if path == "/search":
            q = params.get("q",[""])[0]
            results = search(q, user['id'], user['tier'])
            return self.send(html("Search", page_search(user, q, results), user))
        if path == "/saved": return self.send(html("Saved", page_saved(user), user))
        if path == "/content": return self.send(html("Content", page_content(user), user))
        if path == "/discover": return self.send(html("Discover", page_discover(user), user))
        if path == "/analytics": return self.send(html("Analytics", page_analytics(user), user))
        if path == "/export":
            f = params.get("f",[None])[0]
            if f == "json": return self.file(export_json(user['id']), "application/json", "export.json")
            if f == "md": return self.file(export_md(user['id']), "text/markdown", "export.md")
            return self.send(html("Export", page_export(user), user))

        self.send(html("404", "<h2>Not Found</h2>", user), 404)
    
    def do_POST(self):
        data = parse_qs(self.rfile.read(int(self.headers.get("Content-Length",0))).decode())
        user = login(self.token())

        if self.path == "/signup":
            token, err = signup(data.get("email",[""])[0])
            if err: return self.send(html("Error", f'<p style="color:red">{err}</p><a href="/">Back</a>'))
            return self.send(html("Welcome", f'<h2>Done!</h2><p>Your token:</p><pre style="color:#0f0">{token}</pre><p><a href="/">Continue</a></p>'), headers={"Set-Cookie": f"token={token}; Path=/; HttpOnly"})

        if self.path == "/login":
            t = data.get("token",[""])[0]
            if login(t): return self.redir("/", f"token={t}; Path=/; HttpOnly")
            return self.send(html("Error", '<p style="color:red">Invalid</p><a href="/">Back</a>'))

        if not user: return self.redir("/")

        if self.path == "/save":
            err = save(user['id'], data.get("title",[""])[0], data.get("url",[""])[0], data.get("snippet",[""])[0], user['tier'])
            if err:
                return self.send(html("Error", f'<p style="color:#f66">{err}</p><a href="/search">Back</a>', user))
            return self.redir(f"/search?q={data.get('q',[''])[0]}")

        if self.path == "/saved/delete":
            delete_saved(user['id'], data.get("id",[""])[0])
            return self.redir("/saved")

        if self.path == "/register":
            uid, err = register(user['id'], data.get("title",[""])[0], data.get("description",[""])[0], data.get("type",["other"])[0], user['tier'])
            if err:
                return self.send(html("Error", f'<p style="color:#f66">{err}</p><a href="/content">Back</a>', user))
            return self.redir(f"/verify/{uid}")

        if self.path == "/star":
            project_id = data.get("project_id", [""])[0]
            if project_id:
                star_project(user['id'], int(project_id))
            return self.redir("/discover")

        if self.path == "/delete":
            delete_all(user['id'])
            return self.redir("/", "token=; Path=/; Max-Age=0")

        self.send(html("404", "<h2>Not Found</h2>", user), 404)
    
    def log_message(self, *a): pass

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    init_db()

    # Add initial changelog entries
    add_version("v1.0.0", "Auth, Search, Save, Content Registry, Export", "Privacy-first search with ownership tracking")
    add_version("v1.1.0", "Added CSV export, improved UI", "Save 5-10 min/week with faster exports")
    add_version("v1.2.0", "Usage tracking, tier limits, changelog, A/B testing", "Track value delivered: X searches, Y saves per day. Data-driven pricing.")
    add_version("v1.3.0", "Stripe payment integration + Golden Ticket discovery", "One-click payment → instant access. Members get 1000 searches/day. Discover projects early.")

    # Add seed projects
    conn = db()
    if conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()['c'] == 0:
        projects = [
            ("Death2Data", "https://github.com/deathtodata/death2data", "Privacy-first search engine with content ownership tracking", "search", 85),
            ("Fortune 0", "https://fortune0.com", "Contribution tracking and equity distribution for open source", "tools", 75),
            ("Ollama", "https://ollama.com", "Run LLMs locally with zero cloud dependency", "ai", 95),
            ("SearXNG", "https://github.com/searxng/searxng", "Privacy-respecting metasearch engine", "search", 90),
        ]
        for name, url, desc, cat, score in projects:
            conn.execute("INSERT INTO projects (name, url, description, category, score) VALUES (?, ?, ?, ?, ?)",
                        (name, url, desc, cat, score))
        conn.commit()
    conn.close()

    print(f"""
╔═════════════════════════════════════════════╗
║  D2D {VERSION} - http://localhost:{PORT}
╠═════════════════════════════════════════════╣
║  ✓ Auth     ✓ Search    ✓ Save
║  ✓ Content  ✓ Export    ✓ Delete
║  ✓ Usage    ✓ Analytics ✓ Changelog
║
║  Database: {DB}
║  Ctrl+C to stop
╚═════════════════════════════════════════════╝
""")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
