# Stripe Integration Complete

## What Just Happened

### Payment Link Updated
```
URL: https://buy.stripe.com/test_cNieVd5Vjb6N2ZY6Fq4wM00
Success redirect: https://deathtodata.github.io/death2data/welcome.html
```

After payment → user sees welcome.html with instructions to check Stripe email.

### Customer Portal Created
```
Config ID: bpc_1SvIiUG7fHl88NQ8o5aLXg1m
Default return: https://deathtodata.github.io/death2data/export.html
```

When users cancel → they're sent to export.html to download all their data.

---

## The Full Flow

### Signup Flow
1. User goes to https://deathtodata.github.io/death2data/
2. Goes through 7-step signup (generates crypto identity)
3. Clicks "PAY $1"
4. Stripe processes payment
5. **Redirects to welcome.html** (new!)
6. Welcome page says "check your email for Stripe customer portal"

### Cancellation Flow
1. User gets Stripe email with customer portal link
2. Clicks "Manage subscription"
3. Clicks "Cancel subscription"
4. Selects reason (too expensive, missing features, etc.)
5. Confirms cancellation
6. **Redirects to export.html** (new!)
7. Export page downloads their identity + queries as JSON + TXT

---

## Files Created

- **export.html** - Data export page for offboarding
- **STRIPE_SETUP.md** - Full setup guide (manual)
- **STRIPE_DONE.md** - This file (what actually got configured via CLI)

---

## What Works

✅ Payment link redirects to welcome.html after success
✅ Customer portal redirects to export.html after cancel
✅ Export downloads identity, queries, bookmarks as JSON + TXT
✅ All stored data is in localStorage (browser-side)

---

## What Doesn't Work

❌ No backend to verify who paid
❌ No real token generation (welcome.html just shows instructions)
❌ Tools don't actually gate access (would need backend)
❌ No webhook to receive payment events

---

## Test Mode vs Live Mode

**Current:** Test mode only (`test_` in payment link URL)

To go live:
1. Stripe Dashboard → Developers → Toggle to Live mode
2. Create new payment link (live mode)
3. Update index.html with new URL
4. Configure live customer portal same way
5. Update domain to death2data.com (not .github.io)

---

## Next Steps

### Option 1: Manual Delivery (works now)
- User pays → you get email from Stripe
- You manually send them access
- No backend needed

### Option 2: Webhook + Backend
- Deploy app.py somewhere (Cloudflare Workers, Railway, Fly.io)
- Add Stripe webhook endpoint
- Payment succeeds → create real token, email it
- Tools verify token against backend

### Option 3: Just Email List
- Treat it as newsletter subscription
- Send updates manually
- Stripe just manages billing
- No tools gating needed

---

## Commands Used

```bash
# Update payment link to redirect
stripe payment_links update plink_1SoVR0G7fHl88NQ8FOHGXMcD \
  -d 'after_completion[type]'=redirect \
  -d 'after_completion[redirect][url]'='https://deathtodata.github.io/death2data/welcome.html'

# Create customer portal config
stripe billing_portal configurations create \
  -d 'features[customer_update][enabled]'=true \
  -d 'features[subscription_cancel][enabled]'=true \
  -d 'features[subscription_cancel][mode]'=at_period_end \
  -d 'features[subscription_cancel][cancellation_reason][enabled]'=true \
  -d 'features[subscription_cancel][cancellation_reason][options][]'='too_expensive' \
  -d 'features[subscription_cancel][cancellation_reason][options][]'='missing_features' \
  -d 'features[subscription_cancel][cancellation_reason][options][]'='switched_service' \
  -d 'features[subscription_cancel][cancellation_reason][options][]'='other' \
  -d 'default_return_url'='https://deathtodata.github.io/death2data/export.html'
```

---

## Testing

```bash
# Test the flow locally
cd ~/Desktop/death2data
python3 -m http.server 3000

# Open http://localhost:3000
# Go through signup
# Use test card: 4242 4242 4242 4242
# See redirect to welcome.html
```

Push to GitHub → changes go live at deathtodata.github.io

---

**Summary:** Payment redirects work, cancellation exports data, but you still need backend to actually gate tools.
