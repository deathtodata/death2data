---
name: death2data
description: Design system, branding, and infrastructure management for Death2Data privacy-first search engine. Use when building any Death2Data page, component, subdomain site, email template, or marketing material. Triggers on mentions of death2data, d2d branding, privacy search UI, or requests to create/modify Death2Data web properties. Includes design tokens, component patterns, Netlify deployment guides, and brand voice guidelines.
---

# Death2Data Design System & Infrastructure

Build and maintain all Death2Data web properties with consistent branding, high-quality UI, and proper infrastructure.

## Brand Identity

**Mission**: Privacy-first search. No tracking. No profiling. No bullshit.

**Voice**: Direct, technical, slightly rebellious. Speaks to developers who value privacy. Never corporate-speak. Uses phrases like "kill the trackers" and "refuse to be the product."

**Aesthetic**: Dark brutalist-tech. High contrast. Monospace accents. Scan lines and noise textures. Red for destruction/warning, green for action/success.

## Design Tokens

```css
:root {
  /* Colors */
  --black: #0a0a0a;
  --white: #f5f5f5;
  --gray: #888;
  --gray-dark: #555;
  --gray-darker: #333;
  --gray-darkest: #222;
  --red: #ff3333;
  --red-dim: #cc0000;
  --green: #00ff66;
  --green-dim: #00cc52;
  
  /* Typography */
  --font-mono: 'Space Mono', monospace;
  --font-sans: 'Instrument Sans', sans-serif;
  
  /* Spacing */
  --space-xs: 8px;
  --space-sm: 16px;
  --space-md: 24px;
  --space-lg: 32px;
  --space-xl: 48px;
  --space-2xl: 80px;
  
  /* Effects */
  --border-subtle: 1px solid #222;
  --border-input: 2px solid #333;
  --shadow-glow-green: 0 0 0 4px rgba(0, 255, 102, 0.1);
  --shadow-glow-red: 0 0 0 4px rgba(255, 51, 51, 0.1);
}
```

**Required Google Fonts import**:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
```

## Visual Effects

**Always include noise texture overlay**:
```css
body::before {
  content: '';
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
  z-index: 1000;
}
```

**Scan lines (use sparingly, mainly on landing pages)**:
```css
body::after {
  content: '';
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 2px,
    rgba(0, 0, 0, 0.1) 2px, rgba(0, 0, 0, 0.1) 4px
  );
  pointer-events: none;
  z-index: 999;
}
```

## Component Patterns

### Logo
```html
<div class="logo">Death2Data</div>

<style>
.logo {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--red);
}
.logo::before {
  content: '█';
  margin-right: 8px;
  animation: blink 1s steps(1) infinite;
}
@keyframes blink { 50% { opacity: 0; } }
</style>
```

### Buttons
```css
/* Primary (light on dark) */
.btn-primary {
  padding: 16px 32px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: var(--white);
  color: var(--black);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: var(--green);
  transform: translateY(-2px);
}

/* Secondary (outline) */
.btn-secondary {
  /* same as primary but: */
  background: transparent;
  color: var(--white);
  border: 2px solid var(--gray-darker);
}
.btn-secondary:hover {
  border-color: var(--green);
  color: var(--green);
}
```

### Form Inputs
```css
input[type="email"],
input[type="text"],
textarea {
  padding: 16px 20px;
  font-family: var(--font-mono);
  font-size: 16px;
  background: var(--black);
  border: 2px solid var(--gray-darker);
  color: var(--white);
  outline: none;
  transition: border-color 0.2s;
}
input:focus, textarea:focus {
  border-color: var(--green);
}
input::placeholder {
  color: var(--gray-dark);
}
```

### Feature Cards
```css
.feature {
  background: var(--black);
  padding: 32px 24px;
  transition: background 0.2s;
}
.feature:hover { background: #111; }
.feature-icon {
  font-family: var(--font-mono);
  font-size: 24px;
  color: var(--green);
  margin-bottom: 16px;
}
.feature h3 {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}
```

### Section Headers
- Use `Space Mono` for all headers
- H1: `clamp(48px, 10vw, 96px)`, letter-spacing `-0.03em`
- H2: `24px`, can use green accent color
- H3: `14-16px`, uppercase, letter-spacing `0.1em`

## Page Templates

### Landing Page Structure
1. Header with logo
2. Hero with headline + tagline
3. Features grid (2x2 or 4-column)
4. Signup/CTA section
5. Manifesto/about section (red left border)
6. Footer with links

### Documentation Structure
1. Sidebar navigation (260px, sticky)
2. Main content area (max-width 800px)
3. Code blocks with dark background (#111)
4. Callout boxes (green border = info, red border = warning)

### App/Dashboard Structure
1. Minimal header
2. Full-width or centered content
3. Cards for data display
4. Status indicators (green = good, red = warning/error)

## Infrastructure

### Domain Structure
| Subdomain | Purpose | Netlify Site |
|-----------|---------|--------------|
| death2data.com | Landing page, waitlist | main site |
| docs.death2data.com | Documentation | separate site |
| app.death2data.com | Search application | separate site |
| status.death2data.com | Uptime/status page | separate site |
| api.death2data.com | API (future) | different host |

### Netlify Deployment
Each subdomain = separate Netlify site. To add a new subdomain:
1. Create new site in Netlify (manual deploy or connect repo)
2. Go to Domain management → Add domain alias
3. Enter subdomain (e.g., `status.death2data.com`)
4. Netlify auto-configures DNS (nameservers already pointed)
5. SSL auto-provisions

### Forms (Netlify Forms)
Always use Netlify Forms for any form submission:
```html
<form name="form-name" method="POST" data-netlify="true" data-netlify-honeypot="bot-field">
  <p class="honey-field"><input name="bot-field"></p>
  <!-- form fields -->
</form>

<style>.honey-field { position: absolute; left: -9999px; }</style>
```

### Email Automation
Connect Netlify Forms to Zapier for auto-responses:
1. Zapier trigger: Netlify → New Form Submission
2. Zapier action: Email by Zapier → Send Outbound Email
3. Use `{{email}}` variable for recipient

## File Naming
- All lowercase, hyphens for spaces
- `index.html` for main page of each site
- `style.css` if separating CSS (optional, inline is fine)
- `assets/` folder for images, fonts if needed

## Responsive Breakpoints
```css
/* Mobile-first, then: */
@media (min-width: 600px) { /* Tablet */ }
@media (min-width: 900px) { /* Desktop */ }
@media (min-width: 1200px) { /* Large desktop */ }
```

## Checklist for New Pages
- [ ] Correct meta charset and viewport
- [ ] Title follows pattern: "Page — Death2Data"
- [ ] Meta description included
- [ ] Google Fonts preconnect + import
- [ ] CSS variables defined
- [ ] Noise texture overlay
- [ ] Logo with blink animation
- [ ] Mobile responsive
- [ ] Links to other D2D properties where relevant
- [ ] Footer with copyright + links
