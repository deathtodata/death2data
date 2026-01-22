# Email Templates

## Welcome Email (Waitlist Signup)

**Subject**: You're on the list

**Body**:
```
Hey,

You're on the Death2Data waitlist. We'll let you know when we launch.

In the meantime:
- Follow development: github.com/deathtodata
- Questions? Reply to this email.

No tracking. No profiling. No bullshit.

— Death2Data
```

## Launch Announcement

**Subject**: Death2Data is live

**Body**:
```
It's here.

Death2Data is now live at app.death2data.com

What you get:
- Privacy-first search aggregating 70+ engines
- Zero tracking, zero logging
- Self-host option available

Get started: [app.death2data.com]

Questions? Reply to this email.

— Death2Data
```

## Weekly/Monthly Update Template

**Subject**: Death2Data Update — [Month Year]

**Body**:
```
Quick update on Death2Data:

**What's new**:
- [Feature/update 1]
- [Feature/update 2]

**Coming soon**:
- [Upcoming feature]

**Numbers** (if relevant):
- [X] users on waitlist
- [X] searches served

Thanks for being here.

— Death2Data
```

## Zapier Setup for Auto-Welcome

1. Create Zapier account (free tier)
2. New Zap → Trigger: Netlify (New Form Submission)
3. Select site → Select "waitlist" form
4. Action: Email by Zapier (Send Outbound Email)
5. Configure:
   - To: `{{email}}`
   - From Name: `Death2Data`
   - Subject: `You're on the list`
   - Body: Use welcome email template above
6. Test and enable
