# D2D Content Registry

**Register content. Prove ownership. License freely.**

## What This Is

A simple content tracking system that:
1. Watches your ~/Downloads folder (optional)
2. Generates UUID + SHA256 hash for each file
3. Lets you choose a license (MIT, CC0, proprietary, etc.)
4. Creates proof certificates you can share

## Quick Start

### Run the Registry Server

```bash
cd ~/Desktop/death2data
python3 content_registry.py
```

Server runs on: `http://localhost:5051`

### Watch Downloads Folder (Auto-Register)

```bash
python3 content_registry.py --watch
```

Every new file in ~/Downloads gets auto-registered with a UUID.

### Use the Web UI

1. Go to: `http://localhost:3000/tools/registry.html`
2. Upload a file
3. Choose license, add tags/notes
4. Get UUID + SHA256 hash
5. Download proof certificate

## API Endpoints

```
GET  /                    - Home page
GET  /register            - Registration form
POST /register            - Register content
GET  /content/:uuid       - Lookup content by UUID
GET  /certificate/:uuid   - Download certificate (txt or json)
GET  /verify?uuid=xxx     - Verify content exists
```

## Example Certificate

```
CONTENT REGISTRATION CERTIFICATE
=================================

UUID:         f47ac10b-58cc-4372-a567-0e02b2c3d479
SHA256:       a3b5c8d2e4f6g...
Filename:     my_design.psd
Size:         25600000 bytes
Registered:   2026-01-30T10:00:00Z
Owner:        user@example.com
License:      CC-BY-4.0

This certificate proves registration of the above content.
Verify at: http://localhost:5051/verify?uuid=f47ac10b...
```

## Use Cases

- **Designers:** Register logo files, prove you created them
- **Writers:** Register articles before publishing
- **Developers:** Register code before open sourcing
- **Anyone:** Prove you had a file at a specific time

## Licenses Supported

- CC0-1.0 (Public Domain)
- CC-BY-4.0 (Attribution)
- MIT License
- Apache 2.0
- GPL 3.0
- Proprietary (All Rights Reserved)

## Database

SQLite database: `content.db`

**Schema:**
- `users` - Token-based auth
- `content` - Registered files (UUID, hash, license, tags, notes)
- `exports` - Export history
- `usage` - Monthly limits tracking

## Tier Limits

- **Free:** 10 files/month
- **Paid ($1/mo):** Unlimited files

## Technical Details

- **Hashing:** SHA256 (client-side in browser, server-side in Python)
- **UUID:** UUID v4 (random)
- **Auth:** Token-based (SHA256 hash of token stored)
- **Storage:** SQLite (portable, no external DB needed)
- **File watching:** Python watchdog library

## Integration with Death2Data

The registry is accessible from the main D2D tools page at:
`https://deathtodata.github.io/death2data/tools.html`

Users who paid $1 can access it with their token.

## Local Development

```bash
# Install dependencies
pip install watchdog

# Run server
python3 content_registry.py

# Run in watch mode
python3 content_registry.py --watch

# Check database
sqlite3 content.db "SELECT * FROM content"
```

## Production Deployment

To deploy:
1. Set up ngrok/cloudflare tunnel to expose :5051
2. Point DNS to tunnel
3. Update URLs in HTML to use real domain
4. Add Stripe webhook integration
5. Enable HTTPS

## License

MIT

## Part of Death2Data

https://death2data.com
