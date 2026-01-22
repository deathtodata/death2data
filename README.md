# Death2Data

**Privacy-first search. No tracking. No profiling. No bullshit.**

Death2Data is an open-source, self-hosted metasearch engine that aggregates results from 70+ search engines without tracking you.

🔗 **Website**: [death2data.com](https://death2data.com)  
📚 **Documentation**: [docs.death2data.com](https://docs.death2data.com)  
🔍 **Search App**: [app.death2data.com](https://app.death2data.com)  
📊 **Status**: [status.death2data.com](https://status.death2data.com)

---

## What's in this repo

This repository contains the public web properties for Death2Data:

```
death2data/
├── sites/
│   ├── www/          → Landing page (death2data.com)
│   ├── docs/         → Documentation (docs.death2data.com)
│   ├── app/          → Search interface (app.death2data.com)
│   └── status/       → Status page (status.death2data.com)
├── shared/           → Shared styles and assets
├── skills/           → Claude AI skill for design system
└── netlify.toml      → Deployment configuration
```

## Quick Start

### Prerequisites

- Git
- A [Netlify](https://netlify.com) account (free tier works)

### Local Development

```bash
# Clone the repo
git clone https://github.com/deathtodata/death2data.git
cd death2data

# Open any site in your browser
open sites/www/index.html
```

No build step required — these are static HTML files.

### Deployment

Each subdomain is deployed as a separate Netlify site:

| Subdomain | Folder | Netlify Site |
|-----------|--------|--------------|
| death2data.com | `sites/www` | Main site |
| docs.death2data.com | `sites/docs` | Docs site |
| app.death2data.com | `sites/app` | App site |
| status.death2data.com | `sites/status` | Status site |

**To deploy a new site:**

1. Create a new site on Netlify
2. Connect this GitHub repo
3. Set the **Base directory** to the appropriate folder (e.g., `sites/docs`)
4. Set **Publish directory** to the same folder
5. Add your subdomain in Domain Management

## Design System

The Death2Data design system is documented in `skills/death2data-skill/SKILL.md`. It includes:

- Color tokens
- Typography
- Component patterns
- Visual effects (noise texture, scan lines)
- Copy guidelines

If you use Claude AI, you can install the `.skill` file to automatically apply the design system when building Death2Data pages.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick version:**
1. Fork the repo
2. Create a branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Submit a PR

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

SPDX-License-Identifier: MIT

---

## Links

- **GitHub**: [github.com/deathtodata](https://github.com/deathtodata)
- **Email**: hello@death2data.com

---

*Built for developers who refuse to be the product.*
