# Traced Chrome Extension

See who really owns what you buy — directly on grocery sites.

## What It Does

- Works on **Instacart, Amazon Fresh, Whole Foods, Safeway, Walmart, Target, Kroger**
- Detects product brand names on the page
- Hits the Traced API to get ownership and contradiction data
- Shows a **color-coded dot badge** on each product card:
  - 🟢 Green = independent or low contradiction
  - 🟡 Amber = acquired, moderate concern
  - 🔴 Red = high contradiction score (70+)
- Click any badge to expand a card with parent company, score, and key findings
- Toolbar popup lets you search any brand and shows brands detected on the current page

## Install (Developer Mode)

1. Open Chrome → go to `chrome://extensions`
2. Toggle **Developer mode** on (top right)
3. Click **Load unpacked**
4. Select the `chrome-extension/` folder from this repo
5. The Traced icon appears in your toolbar

## Switch to Local API

For development, edit the `API_BASE` constant in both `content.js` and `popup.js`:

```js
const API_BASE = 'http://127.0.0.1:5001';  // local Flask dev server
```

To use production:
```js
const API_BASE = 'https://tracedhealth.com';
```

## Files

| File | Purpose |
|---|---|
| `manifest.json` | Extension config, permissions, content script registration |
| `content.js` | Injected into grocery sites — detects products, fetches API, adds badges |
| `styles.css` | Injected styles for badges and cards |
| `popup.html` / `popup.js` | Toolbar popup UI |
| `background.js` | Service worker for cross-tab cache coordination |
| `icons/` | Extension icons (16px, 48px, 128px) |

## Supported Sites

| Site | Notes |
|---|---|
| instacart.com | Full product grid support |
| amazon.com | Search results + Fresh/Whole Foods sections |
| wholefoodsmarket.com | Product tiles |
| safeway.com | Product cards |
| walmart.com | Search grid |
| target.com | Product grid |
| kroger.com | Product cards |
