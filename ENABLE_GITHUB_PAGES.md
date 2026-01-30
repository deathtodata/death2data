# Enable GitHub Pages (2 Minutes)

Your repo is PUBLIC. You can use GitHub Pages for FREE.

---

## Steps

### 1. Go to Repo Settings

https://github.com/deathtodata/death2data/settings/pages

### 2. Enable Pages

- Source: Deploy from a branch
- Branch: `main`
- Folder: `/ (root)`
- Click **Save**

### 3. Wait 30 Seconds

GitHub builds your site automatically.

### 4. Visit Your Site

https://deathtodata.github.io/death2data/

Should show your death2data signup page.

---

## Point Your Domain

After GitHub Pages is working:

### 5. Add Custom Domain

Still in Settings → Pages:
- Custom domain: `death2data.com`
- Click **Save**

### 6. Update DNS (Cloudflare)

Cloudflare Dashboard → DNS:

**Delete old records, add these:**

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

### 7. Enable HTTPS

Back in GitHub Settings → Pages:
- Check "Enforce HTTPS"

### 8. Done

- https://death2data.com → Your site
- Free forever
- No laptop needed
- Stripe links work

---

## Fix Stripe Redirect

After domain is live:

Stripe Dashboard → Products → Click your $1 product:
- Success URL: `https://death2data.com/welcome.html`
- Cancel URL: `https://death2data.com/`

---

## Current Stripe Link

`https://buy.stripe.com/cNieVd5Vjb6N2ZY6Fq4wM00`

This works, but redirects to wrong URL after payment.

Fix it by updating success URL in Stripe Dashboard.

---

## Summary

**Before:** Ugly tunnel URL, laptop required
**After:** death2data.com, free GitHub hosting

No credits. No Netlify. Just works.

---

**Do this now:** https://github.com/deathtodata/death2data/settings/pages
