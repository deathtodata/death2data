#!/usr/bin/env python3
"""
D2D CONTENT REGISTRY
====================

Register content → Get UUID + hash → Prove ownership → License it

Watch ~/Downloads, auto-register files, track licenses.

Run:
    python3 content_registry.py              # Start server
    python3 content_registry.py --watch      # Watch Downloads folder

Server runs on: http://localhost:5051
"""

import sqlite3
import secrets
import hashlib
import json
import os
import sys
import uuid as uuid_lib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from pathlib import Path

DB = "content.db"
PORT = 5051

# ============================================================================
# CONFIG
# ============================================================================

CONFIG = {
    "name": "D2D Content Registry",
    "tagline": "Register content. Prove ownership. License freely.",
    "version": "1.0.0",
    "watch_folder": str(Path.home() / "Downloads"),
    "licenses": {
        "CC0-1.0": "Public Domain (No Rights Reserved)",
        "CC-BY-4.0": "Attribution 4.0 International",
        "MIT": "MIT License",
        "Apache-2.0": "Apache License 2.0",
        "GPL-3.0": "GNU General Public License v3.0",
        "Proprietary": "All Rights Reserved",
    },
    "tiers": {
        "free": {"files_per_month": 10},
        "paid": {"files_per_month": -1},  # unlimited
    }
}

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    conn = sqlite3.connect(DB)

    # Users
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            token_hash TEXT,
            tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Registered content
    conn.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            file_hash TEXT,
            filename TEXT,
            filepath TEXT,
            filesize INTEGER,
            user_id INTEGER,
            license TEXT DEFAULT 'Proprietary',
            tags TEXT,
            notes TEXT,
            auto_registered BOOLEAN DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Export history
    conn.execute("""
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER,
            format TEXT,
            exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES content(id)
        )
    """)

    # Usage tracking (for tier limits)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            user_id INTEGER,
            month TEXT,
            files_registered INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# AUTH
# ============================================================================

def signup(email):
    conn = get_db()
    token = secrets.token_hex(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        conn.execute("INSERT INTO users (email, token_hash) VALUES (?, ?)", (email, token_hash))
        conn.commit()
        conn.close()
        return token, None
    except sqlite3.IntegrityError:
        conn.close()
        return None, "Email already exists"

def get_user(token):
    if not token:
        return None
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE token_hash = ?", (token_hash,)).fetchone()
    conn.close()
    return dict(user) if user else None

# ============================================================================
# CONTENT REGISTRATION
# ============================================================================

def hash_file(filepath):
    """Generate SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def register_content(filepath, user_id, license="Proprietary", tags="", notes="", auto=False):
    """Register a file and return its UUID."""
    path = Path(filepath)

    if not path.exists():
        return None, "File not found"

    # Generate UUID and hash
    content_uuid = str(uuid_lib.uuid4())
    file_hash = hash_file(filepath)
    filesize = path.stat().st_size

    conn = get_db()

    # Check usage limits
    if not auto:  # Don't count auto-registered files against limit
        month = datetime.now().strftime("%Y-%m")
        user = conn.execute("SELECT tier FROM users WHERE id = ?", (user_id,)).fetchone()

        if user:
            tier = user["tier"]
            limit = CONFIG["tiers"][tier]["files_per_month"]

            if limit > 0:  # -1 = unlimited
                usage = conn.execute(
                    "SELECT files_registered FROM usage WHERE user_id = ? AND month = ?",
                    (user_id, month)
                ).fetchone()

                current = usage["files_registered"] if usage else 0

                if current >= limit:
                    conn.close()
                    return None, f"Monthly limit reached ({limit} files)"

    # Insert content
    try:
        conn.execute("""
            INSERT INTO content
            (uuid, file_hash, filename, filepath, filesize, user_id, license, tags, notes, auto_registered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_uuid, file_hash, path.name, str(path), filesize, user_id, license, tags, notes, auto))

        # Update usage
        month = datetime.now().strftime("%Y-%m")
        conn.execute("""
            INSERT INTO usage (user_id, month, files_registered)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, month) DO UPDATE SET files_registered = files_registered + 1
        """, (user_id, month))

        conn.commit()
        conn.close()

        return content_uuid, None

    except Exception as e:
        conn.close()
        return None, str(e)

def get_content(content_uuid):
    """Lookup content by UUID."""
    conn = get_db()
    content = conn.execute("""
        SELECT c.*, u.email as owner_email
        FROM content c
        JOIN users u ON c.user_id = u.id
        WHERE c.uuid = ?
    """, (content_uuid,)).fetchone()
    conn.close()
    return dict(content) if content else None

def get_user_content(user_id, limit=100):
    """Get all content registered by a user."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM content
        WHERE user_id = ?
        ORDER BY registered_at DESC
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def verify_content(content_uuid, filepath):
    """Verify a file matches its registered hash."""
    content = get_content(content_uuid)
    if not content:
        return False, "UUID not found"

    current_hash = hash_file(filepath)

    if current_hash == content["file_hash"]:
        return True, "File matches registered hash"
    else:
        return False, "File has been modified (hash mismatch)"

# ============================================================================
# PROOF CERTIFICATES
# ============================================================================

def generate_certificate(content_uuid):
    """Generate proof certificate for content."""
    content = get_content(content_uuid)
    if not content:
        return None

    cert = f"""
CONTENT REGISTRATION CERTIFICATE
=================================

UUID:         {content['uuid']}
SHA256:       {content['file_hash']}
Filename:     {content['filename']}
Size:         {content['filesize']} bytes
Registered:   {content['registered_at']}
Owner:        {content['owner_email']}
License:      {content['license']}

{content.get('notes', '')}

This certificate proves registration of the above content.
Verify at: http://localhost:5051/verify?uuid={content['uuid']}

Death2Data Content Registry v{CONFIG['version']}
Generated: {datetime.now().isoformat()}
""".strip()

    return cert

def generate_certificate_json(content_uuid):
    """Generate JSON proof certificate."""
    content = get_content(content_uuid)
    if not content:
        return None

    return json.dumps({
        "uuid": content["uuid"],
        "sha256": content["file_hash"],
        "filename": content["filename"],
        "filesize": content["filesize"],
        "registered_at": content["registered_at"],
        "owner": content["owner_email"],
        "license": content["license"],
        "tags": content.get("tags", "").split(",") if content.get("tags") else [],
        "notes": content.get("notes", ""),
        "verify_url": f"http://localhost:5051/verify?uuid={content['uuid']}",
        "registry": "Death2Data Content Registry",
        "version": CONFIG["version"]
    }, indent=2)

# ============================================================================
# FILE WATCHING
# ============================================================================

def watch_downloads(user_id):
    """Watch Downloads folder and auto-register new files."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ Watch mode requires watchdog: pip install watchdog")
        sys.exit(1)

    watch_path = CONFIG["watch_folder"]

    class RegisterHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                filepath = event.src_path
                # Wait for file to finish writing
                import time
                time.sleep(2)

                if Path(filepath).exists() and not Path(filepath).name.startswith("."):
                    print(f"📁 New file detected: {Path(filepath).name}")
                    content_uuid, error = register_content(filepath, user_id, auto=True)

                    if content_uuid:
                        print(f"   ✓ Registered: {content_uuid}")
                    else:
                        print(f"   ✗ Failed: {error}")

    observer = Observer()
    observer.schedule(RegisterHandler(), watch_path, recursive=False)
    observer.start()

    print(f"👁  Watching: {watch_path}")
    print(f"   Auto-registering all new files")
    print(f"   Press Ctrl+C to stop\n")

    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n✓ Stopped watching")

    observer.join()

# ============================================================================
# HTTP SERVER
# ============================================================================

STYLE = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:monospace;background:#000;color:#fff;min-height:100vh;padding:20px}
main{max-width:800px;margin:0 auto}
h1{font-size:24px;margin-bottom:20px;color:#0f0}
h2{font-size:18px;margin:20px 0 10px;color:#0af}
a{color:#0af}
pre{background:#111;padding:15px;overflow-x:auto;border:1px solid #333}
form{margin:20px 0}
input,textarea,select{
  background:#111;border:1px solid #333;color:#fff;
  padding:10px;font-family:monospace;width:100%;margin-bottom:10px;
}
button{
  background:#0f0;color:#000;border:none;padding:12px 24px;
  font-family:monospace;font-weight:bold;cursor:pointer;
}
button:hover{background:#fff}
.cert{background:#0a0a0a;border:2px solid #0f0;padding:20px;margin:20px 0}
.error{color:#f00;background:#1a0000;padding:10px;border:1px solid #f00}
.success{color:#0f0;background:#001a00;padding:10px;border:1px solid #0f0}
table{width:100%;border-collapse:collapse;margin:20px 0}
th,td{border:1px solid #333;padding:8px;text-align:left}
th{background:#111}
""".strip()

class RequestHandler(BaseHTTPRequestHandler):
    def send_html(self, content, code=200):
        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{CONFIG['name']}</title>
<style>{STYLE}</style>
</head><body>
<main>{content}</main>
</body></html>"""

        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html.encode())

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_text(self, text, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(text.encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Home
        if path == "/":
            content = f"""
<h1>{CONFIG['name']}</h1>
<p>{CONFIG['tagline']}</p>

<h2>Quick Actions</h2>
<ul>
  <li><a href="/register">Register Content</a></li>
  <li><a href="/my-content">My Content</a></li>
  <li><a href="/verify">Verify Content</a></li>
</ul>

<h2>API Endpoints</h2>
<pre>
GET  /                    - This page
GET  /register            - Registration form
POST /register            - Register content
GET  /content/:uuid       - Lookup content
GET  /certificate/:uuid   - Download certificate
GET  /verify?uuid=xxx     - Verify content
GET  /my-content          - List my content
</pre>
"""
            self.send_html(content)

        # Register form
        elif path == "/register":
            licenses_html = "".join([
                f'<option value="{k}">{v}</option>'
                for k, v in CONFIG["licenses"].items()
            ])

            content = f"""
<h1>Register Content</h1>
<form method="POST" action="/register">
  <input type="text" name="filepath" placeholder="/path/to/file" required>
  <input type="text" name="token" placeholder="Your access token" required>

  <select name="license">
    {licenses_html}
  </select>

  <input type="text" name="tags" placeholder="Tags (comma-separated)">
  <textarea name="notes" placeholder="Notes" rows="4"></textarea>

  <button type="submit">REGISTER CONTENT</button>
</form>
"""
            self.send_html(content)

        # Content lookup
        elif path.startswith("/content/"):
            content_uuid = path.split("/")[-1]
            content = get_content(content_uuid)

            if content:
                html_content = f"""
<h1>Content Details</h1>
<table>
  <tr><th>UUID</th><td>{content['uuid']}</td></tr>
  <tr><th>SHA256</th><td style="word-break:break-all">{content['file_hash']}</td></tr>
  <tr><th>Filename</th><td>{content['filename']}</td></tr>
  <tr><th>Size</th><td>{content['filesize']} bytes</td></tr>
  <tr><th>Owner</th><td>{content['owner_email']}</td></tr>
  <tr><th>License</th><td>{content['license']}</td></tr>
  <tr><th>Tags</th><td>{content.get('tags', '')}</td></tr>
  <tr><th>Registered</th><td>{content['registered_at']}</td></tr>
</table>

<h2>Download Certificate</h2>
<a href="/certificate/{content['uuid']}?format=txt">Text</a> |
<a href="/certificate/{content['uuid']}?format=json">JSON</a>
"""
                self.send_html(html_content)
            else:
                self.send_html(f"<h1>Not Found</h1><p>UUID not found</p>", 404)

        # Certificate download
        elif path.startswith("/certificate/"):
            content_uuid = path.split("/")[-1]
            fmt = query.get("format", ["txt"])[0]

            if fmt == "json":
                cert = generate_certificate_json(content_uuid)
                if cert:
                    self.send_text(cert)
                else:
                    self.send_json({"error": "UUID not found"}, 404)
            else:
                cert = generate_certificate(content_uuid)
                if cert:
                    self.send_text(cert)
                else:
                    self.send_text("UUID not found", 404)

        # Verify
        elif path == "/verify":
            content_uuid = query.get("uuid", [""])[0]

            if content_uuid:
                content = get_content(content_uuid)
                if content:
                    html_content = f"""
<h1>✓ Content Verified</h1>
<div class="success">
  <p>This UUID is registered in the D2D Content Registry.</p>
</div>

<table>
  <tr><th>UUID</th><td>{content['uuid']}</td></tr>
  <tr><th>Filename</th><td>{content['filename']}</td></tr>
  <tr><th>SHA256</th><td style="word-break:break-all">{content['file_hash']}</td></tr>
  <tr><th>Owner</th><td>{content['owner_email']}</td></tr>
  <tr><th>Registered</th><td>{content['registered_at']}</td></tr>
  <tr><th>License</th><td>{content['license']}</td></tr>
</table>

<p><a href="/content/{content['uuid']}">View full details</a></p>
"""
                    self.send_html(html_content)
                else:
                    html_content = """
<h1>✗ Not Found</h1>
<div class="error">
  <p>This UUID is not registered in the D2D Content Registry.</p>
</div>
"""
                    self.send_html(html_content, 404)
            else:
                html_content = """
<h1>Verify Content</h1>
<form method="GET" action="/verify">
  <input type="text" name="uuid" placeholder="Content UUID" required>
  <button type="submit">VERIFY</button>
</form>
"""
                self.send_html(html_content)

        else:
            self.send_html("<h1>404</h1><p>Not found</p>", 404)

    def do_POST(self):
        if self.path == "/register":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = parse_qs(body)

            filepath = params.get("filepath", [""])[0]
            token = params.get("token", [""])[0]
            license_key = params.get("license", ["Proprietary"])[0]
            tags = params.get("tags", [""])[0]
            notes = params.get("notes", [""])[0]

            user = get_user(token)
            if not user:
                self.send_html('<div class="error">Invalid token</div>', 401)
                return

            content_uuid, error = register_content(
                filepath, user["id"], license_key, tags, notes
            )

            if content_uuid:
                cert = generate_certificate(content_uuid)
                html_content = f"""
<h1>✓ Content Registered</h1>
<div class="success">
  <p>Your content has been registered!</p>
</div>

<div class="cert">
<pre>{cert}</pre>
</div>

<p><a href="/content/{content_uuid}">View details</a> |
   <a href="/certificate/{content_uuid}?format=json">Download JSON</a></p>
"""
                self.send_html(html_content)
            else:
                self.send_html(f'<div class="error">Error: {error}</div>', 400)

    def log_message(self, format, *args):
        # Suppress default logging
        pass

# ============================================================================
# CLI
# ============================================================================

def main():
    init_db()

    if "--watch" in sys.argv:
        # Demo user for watch mode (in production, require signup)
        conn = get_db()
        user = conn.execute("SELECT * FROM users LIMIT 1").fetchone()

        if not user:
            print("No users found. Creating demo user...")
            token, _ = signup("demo@example.com")
            print(f"Demo user created. Token: {token}\n")
            user = conn.execute("SELECT * FROM users WHERE email = 'demo@example.com'").fetchone()

        conn.close()
        watch_downloads(user["id"])
    else:
        print(f"🚀 {CONFIG['name']}")
        print(f"   {CONFIG['tagline']}\n")
        print(f"   Server: http://localhost:{PORT}")
        print(f"   Database: {DB}\n")
        print("   Press Ctrl+C to stop\n")

        server = HTTPServer(("0.0.0.0", PORT), RequestHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n✓ Stopped server")

if __name__ == "__main__":
    main()
