---
name: x-analytics
description: "Scrape any X/Twitter account's posts and generate an interactive analytics dashboard HTML. Use when: (1) user provides an X/Twitter profile URL or username and wants data scraped, (2) user asks to analyze someone's Twitter/X account growth or content, (3) user wants a social media analytics dashboard or visualization, (4) user mentions 'X analytics', 'Twitter analysis', 'scrape tweets', or 'account analysis'. Accepts profile URLs (x.com/username, twitter.com/username), post URLs, or @handles. Outputs a self-contained dark-themed HTML dashboard with Chart.js growth charts, top posts ranking, content analysis, audience voice analysis from real comments, and AI-generated tweet drafts."
---

# X Analytics Dashboard Generator

Scrape an X/Twitter account and generate a comprehensive interactive HTML analytics dashboard.

## Workflow

1. **Parse input** -- Extract username from URL or handle
2. **Scrape data** -- Multi-source collection (see [references/scraping-guide.md](references/scraping-guide.md))
3. **Save raw data** -- Compile to JSON with `scripts/compile_data.py`
4. **Generate dashboard** -- Populate `assets/dashboard-template.html` with real data
5. **QA check** -- Open in browser, verify rendering

## Step 1: Parse Input

Extract username from any format:
- `https://x.com/username/status/123` -> `username`
- `https://twitter.com/username` -> `username`
- `@username` -> `username`

```bash
mkdir -p /tmp/x_scrape/{posts_detail,comments}
```

## Step 2: Scrape Data

Read [references/scraping-guide.md](references/scraping-guide.md) for the full multi-source scraping procedure. Summary:

1. **Browser scraping** -- Navigate to profile, inject `scripts/extract_tweets.js`, scroll 15-25 times to collect timeline posts
2. **Web search** -- Query `"username" site:x.com` to find viral/recent posts missing from algorithmic timeline
3. **API** (if key provided) -- TikHub endpoints: `fetch_user_post_tweet`, `fetch_tweet_detail`, `fetch_post_comments`
4. **Direct post visits** -- Visit each URL for full text + metrics
5. **Comment collection** -- Search Substack, GitHub, Reddit, media for real audience reactions

Save each post as `/tmp/x_scrape/posts_detail/{post_id}.json`.

## Step 3: Compile Raw Data

```bash
python3 scripts/compile_data.py --username USERNAME --data-dir /tmp/x_scrape --output outputs/USERNAME_raw_data.json
```

## Step 4: Generate Dashboard

Read `assets/dashboard-template.html`. Copy it to `outputs/{username}-dashboard.html`. Replace all `{{PLACEHOLDER}}` values:

| Placeholder | Source |
|---|---|
| `{{USERNAME}}`, `{{DISPLAY_NAME}}`, `{{INITIAL}}` | Profile data |
| `{{DATE_RANGE}}`, `{{SCRAPE_DATE}}` | Scrape metadata |
| `{{TOTAL_GROWTH}}`, `{{AVG_DAILY}}`, `{{BEST_DAY}}`, `{{TOP_VIEWS}}` | Calculated from metrics |
| `{{START_DATE}}`, `{{END_DATE}}`, `{{START_FOLLOWERS}}`, `{{END_FOLLOWERS}}` | For growth chart |
| `{{BASE_DAILY_GAIN}}` | `(end_followers - start_followers) / days` |

Populate JavaScript data arrays:

**TOP_POSTS** -- Rank top 10 by views (or likes). Format:
```js
{rank:1, views:"3.2M", likes:"6.8K", retweets:"1K", date:"Oct 14, 2025", text:"...", url:"..."}
```

**GROWTH_DATA** -- Use real CSV if provided, otherwise estimate between known follower snapshots. Add `viralDays` for high-engagement posts.

**Content Analysis cards** -- Analyze patterns across posts:
- Why They Went Viral (hooks, format, identity)
- Content-Market Fit (audience, gap, advantage)
- Thought Patterns (recurring themes)
- Future Topics (double down / expand / experiment)

**DRAFTS** (12 tweets) -- 3 categories: `Double Down` (green), `Expand Into` (amber), `Experiment` (rose)

**VOICES** -- Real scraped comments from any platform:
```js
{quote:"...", author:"Name", source:"substack|media|github|reddit|x", featured:true}
```

**SENTIMENT_DATA** -- Categorize audience reactions with percentages.

### Critical: Chart.js Canvas Fix

The `.chart-inner` wrapper MUST have `position:relative;height:320px` and canvas MUST have `position:absolute`. Without this, Chart.js canvas expands to 19,000+ px tall.

## Step 5: QA

Open dashboard in browser before delivering:
```bash
python3 -m http.server 8090 &
browser navigate "http://localhost:8090/outputs/{username}-dashboard.html"
browser console view error  # Must show 0 errors
```

Verify: chart correct height, all sections populated, scrolling works, mobile responsive.

## Output

- `outputs/{username}-dashboard.html` -- Interactive dashboard (single HTML file)
- `outputs/{username}_raw_data.json` -- Structured raw data for reuse
