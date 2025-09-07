# sanctra-api
# Sanctra IR - PeMFHealing.app

Mobile-first SPA for exploring sacred site impulse responses and synthesizing binaural IR audio from the Sanctra API.

> Copyright © 2025 PeMFHealing.app. All rights reserved.  
> Website: https://www.pemfhealing.app  
> Contact: info@epemf.app

## Overview

- React single page app that calls your Flask API
- Realtime stereo IR synthesis in the browser using Web Audio
- Mobile-first UI aligned with the PeMFHealing.app gold on black design system
- Optional offline caching via Service Worker and IndexedDB

### Live preview

GitHub Pages  
`https://pemfhealingapp.github.io/sanctra-api/`

Append an API override if needed  
`?api=https://sanctra-api.onrender.com`

## Quick start

```text
docs/
  index.html
  style.css
  sw.js                 # optional - offline
  manifest.webmanifest  # optional - PWA
  faviconV2.jpeg
