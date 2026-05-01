# PrecioVista 💰

**Collaborative real-time price comparator for supermarkets and convenience stores.**

Built by and for the community. No registration required to browse. Free forever.

![PrecioVista](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-green)
![Countries](https://img.shields.io/badge/countries-8-orange)

---

## What it does

PrecioVista lets anyone compare real prices across supermarkets and kiosks in 8 Latin American and European countries. Prices are reported by real users who physically visited the stores — no deals with chains, no sponsored data.

**Core features:**
- Search any product and see a ranked price list across nearby stores
- Interactive map with store locations, names, and opening hours
- 30-day price history chart per product per store
- Store detail page: logo, location, top products, star ratings
- Report prices in 4 simple steps (account required)
- Admin panel to manage users and ban bad actors

---

## Countries supported

🇦🇷 Argentina · 🇪🇸 Spain · 🇨🇱 Chile · 🇺🇾 Uruguay · 🇵🇾 Paraguay · 🇧🇴 Bolivia · 🇵🇪 Peru · 🇲🇽 Mexico

---

## Quick start (local)

```bash
git clone https://github.com/YOUR_USERNAME/preciovista.git
cd preciovista
npx serve .
# Open http://localhost:3000
```

No build step. No npm install. Pure HTML + CSS + JavaScript.

---

## Setting up Supabase (required for real data)

Without Supabase, the app runs in **demo mode** with simulated prices. To enable real user accounts and live data:

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **Settings → API** and copy:
   - Project URL
   - `anon` public key
4. Open `js/supabase.js` and replace:
```javascript
const SUPABASE_URL  = 'https://YOUR_PROJECT.supabase.co';
const SUPABASE_ANON = 'YOUR_ANON_KEY';
const ADMIN_EMAIL   = 'your@email.com';
```
5. Run the SQL schema (see `SUPABASE_SETUP.md`)
6. Enable Google and Microsoft OAuth in **Authentication → Providers**

---

## Project structure

```
preciovista/
├── index.html              # Homepage
├── manifest.json           # PWA manifest
├── sw.js                   # Service worker (offline)
├── css/
│   └── styles.css          # Full design system
├── js/
│   ├── data.js             # Countries, provinces, store chains
│   ├── supabase.js         # Database client and queries
│   ├── auth.js             # Login, register, session
│   └── app.js              # Main logic and shared utilities
├── pages/
│   ├── buscar.html         # Search results + map
│   ├── comercio.html       # Store detail page
│   ├── reportar.html       # Report a price (4 steps)
│   └── admin.html          # Admin panel (/pages/admin.html)
├── assets/                 # Icons and logos
├── README.md
├── SUPABASE_SETUP.md       # Database schema
├── CONTRIBUTING.md
└── LICENSE
```

---

## Publishing on GitHub Pages

1. Push the repo to GitHub (public)
2. Go to **Settings → Pages**
3. Source: `Deploy from a branch` → `main` → `/ (root)`
4. Your app will be live at `https://YOUR_USERNAME.github.io/preciovista`

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome — new countries, new store chains, UI improvements, bug fixes.

---

## License

**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)**

You can use, modify, and share this project freely **as long as**:
- You credit the original author
- You don't use it for commercial purposes
- You share any modifications under the same license

© 2026 PrecioVista. Original author retains authorship rights.
