# X Analytics Skill

Turn any X/Twitter profile into a polished, interactive analytics dashboard.

This skill collects post data from multiple sources, compiles structured JSON, and outputs a dark-themed single-file HTML report with:

- follower growth analysis
- top posts leaderboard
- content pattern insights
- audience voice + sentiment blocks
- AI tweet draft ideas

---

## What this skill does

Given a profile URL, handle, or post URL, the skill workflow is:

1. Parse target username
2. Scrape data from browser timeline + web search (+ optional API)
3. Normalize data into one raw JSON file
4. Fill dashboard template with real metrics and analysis
5. QA in browser and deliver ready-to-share HTML

Output files:

- `outputs/{username}-dashboard.html`
- `outputs/{username}_raw_data.json`

---

## Repository structure

```text
x-analytics/
├── SKILL.md                         # Skill instruction + end-to-end workflow
├── assets/
│   └── dashboard-template.html      # Dashboard HTML template (Chart.js)
├── references/
│   └── scraping-guide.md            # Multi-source scraping playbook
├── scripts/
│   └── compile_data.py              # Merge/clean scraped raw data -> unified JSON
└── outputs/                         # Generated dashboard + raw data
```

---

## Input formats supported

- `https://x.com/username`
- `https://x.com/username/status/123456...`
- `https://twitter.com/username`
- `@username`

All resolve to `username`.

---

## Data collection strategy (high level)

Because X timelines are algorithmic (not purely chronological), this skill combines sources:

1. **Browser scraping** from profile timeline
2. **Web search supplementation** (`site:x.com`) for missing viral/recent posts
3. **Optional API enrichment** (TikHub) for post detail/comments
4. **Direct post-page extraction** for full text + metrics
5. **Off-platform audience signals** (Substack/GitHub/Reddit/media comments)

See full details: `references/scraping-guide.md`

---

## Compile raw data

After scraping into `/tmp/x_scrape`, run:

```bash
python3 scripts/compile_data.py \
  --username USERNAME \
  --data-dir /tmp/x_scrape \
  --output outputs/USERNAME_raw_data.json
```

`compile_data.py` merges:

- `profile.json`
- `timeline_posts.json`
- `posts_detail/*.json`
- `comments/*.json`
- `web_search.json`

and outputs a normalized file with `meta`, `posts_detail`, and `timeline_all_posts`.

---

## Generate dashboard

1. Copy `assets/dashboard-template.html` to:
   `outputs/{username}-dashboard.html`
2. Replace all `{{PLACEHOLDER}}` values
3. Populate JS arrays:
   - `TOP_POSTS`
   - `GROWTH_DATA`
   - `DRAFTS`
   - `VOICES`
   - `SENTIMENT_DATA`

### Important Chart.js layout fix

Keep these CSS rules exactly (already in template):

- `.chart-inner { position: relative; height: 320px; }`
- `.chart-inner canvas { position: absolute; ... }`

Without this, canvas can expand to extreme height.

---

## QA checklist

- dashboard opens with no console errors
- chart height/render is correct
- top posts links work
- all analysis blocks populated
- mobile layout is usable

Quick local preview:

```bash
python3 -m http.server 8090
# open http://localhost:8090/outputs/{username}-dashboard.html
```

---

## Requirements

- Python 3.8+
- Browser automation environment for scraping
- Optional: TikHub API key (for richer API-based enrichment)

---

## Notes

- This project is focused on **analytics and content intelligence**, not just scraping.
- If X blocks comment visibility, use alternative public discussion sources as documented.
- Respect platform terms and local regulations when collecting data.

---

## License

Add your preferred license (MIT/Apache-2.0/etc.) to this repo.
