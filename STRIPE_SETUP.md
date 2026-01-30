# Stripe Dashboard Setup (5 Minutes)

Your payment link exists: `https://buy.stripe.com/cNieVd5Vjb6N2ZY6Fq4wM00`

But it's not configured to redirect properly. Here's how to fix it.

---

## 1. Update Success URL

Stripe Dashboard → Products → Click your $1 product → Edit payment link

**Current Success URL:** (probably blank or wrong domain)

**New Success URL:**
```
https://deathtodata.github.io/death2data/welcome.html?success=true
```

**Cancel URL:**
```
https://deathtodata.github.io/death2data/
```

Click **Save**

---

## 2. Enable Customer Portal

Stripe Dashboard → Settings → Customer Portal

**Enable:**
- ✓ Customers can update payment methods
- ✓ Customers can cancel subscriptions
- ✓ Customers can view invoices

**Branding:**
- Company name: Death2Data
- Primary color: #00ff00 (green)
- Icon: Upload logo if you have one

Click **Save**

---

## 3. Enable Email Receipts

Stripe Dashboard → Settings → Emails

**Enable:**
- ✓ Successful payments
- ✓ Invoices
- ✓ Customer portal link

**From address:** receipts@death2data.com (or use Stripe default)

**Include Customer Portal link in emails:** ✓ ON

---

## 4. Test the Flow

1. Go to https://deathtodata.github.io/death2data/
2. Click through 7-step signup
3. Generate identity (save the keys!)
4. Click "PAY $1"
5. Use Stripe test card: `4242 4242 4242 4242`
6. Exp: any future date, CVC: any 3 digits
7. Should redirect to welcome.html

---

## 5. What Happens After Payment

**Current setup (no backend):**
- User pays → Stripe processes payment
- User redirected to welcome.html
- They see "check your email for Stripe customer portal"
- **NO tokens are generated** (that requires backend)

**This means:**
- Users can pay and manage subscription via Stripe
- But they can't actually USE the tools yet
- Tools require either:
  1. Backend to verify Stripe subscription status
  2. Manual delivery (you email them access links)

---

## 6. Options to Actually Deliver Tools

### Option A: Manual Delivery (Works Now)

After someone pays:
1. You get email from Stripe
2. You manually send them:
   - Access links
   - Instructions
   - Their tools

**Pro:** Works with GitHub Pages
**Con:** Not scalable

### Option B: Stripe Customer Portal Only

Users don't get "tools" - they just manage subscription:
1. Pay $1/month
2. Manage billing through Stripe portal
3. You deliver updates manually via email newsletter

**Pro:** Works with GitHub Pages
**Con:** Not really a product, just a subscription

### Option C: Deploy Backend (Requires Server)

Use `/Users/matthewmauer/Downloads/app.py`:
1. Deploy to Cloudflare Workers, Railway, Fly.io
2. Add Stripe webhook endpoint
3. When payment succeeds → create user account + token
4. Email token to user
5. Tools verify token against backend

**Pro:** Fully automated
**Con:** Requires hosting (not free GitHub Pages)

---

## 7. Custom Domain (Optional)

After Stripe is working on `deathtodata.github.io`:

### Add CNAME to GitHub

Create file: `~/Desktop/death2data/CNAME`

Content:
```
death2data.com
```

Push to GitHub.

### Update DNS (Cloudflare)

Delete all existing records, add:

```
Type: A
Name: @
Content: 185.199.108.153

Type: A
Name: @
Content: 185.199.109.153

Type: A
Name: @
Content: 185.199.110.153

Type: A
Name: @
Content: 185.199.111.153

Type: CNAME
Name: www
Content: deathtodata.github.io
```

Wait 5-10 minutes.

GitHub Settings → Pages:
- Custom domain: `death2data.com`
- Enforce HTTPS: ✓

Now: https://death2data.com → your GitHub Pages site

---

## Current Stripe Link

`https://buy.stripe.com/cNieVd5Vjb6N2ZY6Fq4wM00`

After updating success URL in Dashboard, this link will work properly.

---

## Summary

**What works now:**
- Signup flow generates cryptographic identity
- Payment link processes $1
- Welcome page shows "check email for Stripe portal"

**What doesn't work:**
- No backend to verify who paid
- No token generation system
- No way to gate access to tools
- No webhook integration

**Next decision:**
Choose Option A, B, or C above for tool delivery.

---

**Do this now:** https://dashboard.stripe.com/products

Update that success URL so payments redirect properly.
